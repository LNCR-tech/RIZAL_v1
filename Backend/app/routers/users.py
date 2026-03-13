from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import logging
import os
from app.core.security import (
    get_current_user_with_roles,
    get_school_id_or_403,
    has_any_role,
    normalize_role_name,
)
from app.models.department import Department
from app.models.program import Program
from app.models.school import School
from sqlalchemy import select

from app.schemas.user import (
    UserCreate,
    User,
    UserWithRelations,
    StudentProfileCreate,
    SSGProfileCreate,
    SSGPositionEnum,
    UserUpdate,          # New import
    PasswordUpdate,      # New import
    UserRoleUpdate,      # New import
    StudentProfileBase,          # New import (if you're using it)
    SSGProfileBase           # New import (if you're using it)
)
from app.models.event import Event  # SQLAlchemy model ✅
from app.schemas.event import Event as EventSchema  # Pydantic schema for response ✅
from app.models.user import User as UserModel, UserRole, StudentProfile, SSGProfile
from app.models.role import Role
from app.models.attendance import Attendance
from app.services.email_service import EmailDeliveryError, send_welcome_email
from app.utils.passwords import generate_secure_password
from app.database import get_db
from app.core.security import create_access_token
from sqlalchemy.orm import joinedload
from app.models.associations import program_department_association
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Body

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

# Helper function to check if user has any of the required roles
def has_required_roles(user: UserModel, required_roles: List[str]) -> bool:
    """Check if user has any of the required roles"""
    return has_any_role(user, required_roles)


def _is_admin(user: UserModel) -> bool:
    return has_required_roles(user, ["admin"])


def _is_school_it(user: UserModel) -> bool:
    return has_required_roles(user, ["school_IT", "school_it", "school-it"])


def _target_has_admin_or_school_it(user: UserModel) -> bool:
    target_roles = {
        normalize_role_name(role.role.name)
        for role in user.roles
        if getattr(role, "role", None) and getattr(role.role, "name", None)
    }
    return "admin" in target_roles or "school-it" in target_roles


def _assert_school_it_assignable_roles(current_user: UserModel, role_names: List[str]) -> None:
    if not _is_school_it(current_user) or _is_admin(current_user):
        return

    allowed_roles = {"student", "ssg", "event-organizer"}
    normalized_requested = {normalize_role_name(name) for name in role_names}
    disallowed = sorted(normalized_requested - allowed_roles)
    if disallowed:
        raise HTTPException(
            status_code=403,
            detail=(
                "SCHOOL_IT can only assign student, ssg, and event-organizer roles. "
                f"Disallowed roles: {', '.join(disallowed)}"
            ),
        )


def _query_user_in_school(db: Session, user_id: int, school_id: int) -> UserModel | None:
    return (
        db.query(UserModel)
        .filter(UserModel.id == user_id, UserModel.school_id == school_id)
        .first()
    )


def _is_platform_admin(user: UserModel) -> bool:
    return _is_admin(user) and getattr(user, "school_id", None) is None


def _actor_school_scope_id(actor: UserModel) -> int | None:
    if _is_platform_admin(actor):
        return None
    return get_school_id_or_403(actor)


def _apply_user_scope(query, actor: UserModel):
    actor_school_id = _actor_school_scope_id(actor)
    if actor_school_id is None:
        return query
    return query.filter(UserModel.school_id == actor_school_id)


def _query_user_for_actor(db: Session, user_id: int, actor: UserModel) -> UserModel | None:
    actor_school_id = _actor_school_scope_id(actor)
    if actor_school_id is None:
        return db.query(UserModel).filter(UserModel.id == user_id).first()
    return _query_user_in_school(db, user_id, actor_school_id)


@router.post("", response_model=User, include_in_schema=False)
@router.post("/", response_model=User)
def create_user(
    user: UserCreate,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    required_roles = ["admin", "school_IT"]
    if not has_required_roles(current_user, required_roles):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Requires admin or School IT role",
        )

    school_id = _actor_school_scope_id(current_user)
    if school_id is None:
        raise HTTPException(
            status_code=403,
            detail="Platform admin cannot create school-scoped users via /users. Use school admin flows instead.",
        )

    # Check if email exists
    existing_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing_user:
        detail = "Email already registered in this school"
        if existing_user.school_id != school_id:
            detail = "Email already registered in another school"
        raise HTTPException(status_code=400, detail=detail)

    role_names = [role.value for role in user.roles]
    _assert_school_it_assignable_roles(current_user, role_names)

    existing_roles = db.query(Role).filter(Role.name.in_(role_names)).all()
    role_map = {role.name: role for role in existing_roles}
    missing_roles = [role_name for role_name in role_names if role_name not in role_map]

    if missing_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Role(s) not found: {', '.join(missing_roles)}"
        )

    try:
        temporary_password = generate_secure_password(min_length=10, max_length=14)

        # Create user and role links in one transaction.
        db_user = UserModel(
            email=user.email,
            school_id=school_id,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            must_change_password=True,
        )
        db_user.set_password(temporary_password)
        db.add(db_user)
        db.flush()

        for role_name in role_names:
            db.add(UserRole(user_id=db_user.id, role_id=role_map[role_name].id))

        db.commit()
        db.refresh(db_user)

        school = db.query(School).filter(School.id == school_id).first()
        system_name = None
        if school is not None:
            system_name = school.school_name or school.name

        try:
            send_welcome_email(
                recipient_email=db_user.email,
                temporary_password=temporary_password,
                first_name=db_user.first_name,
                system_name=system_name,
            )
        except EmailDeliveryError as exc:
            logger.warning(
                "Welcome email delivery failed for user_id=%s email=%s error=%s",
                db_user.id,
                db_user.email,
                str(exc),
            )

        return User.from_orm(db_user)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {exc}")

@router.post("/admin/students/", response_model=UserWithRelations)
def create_student_profile(
    profile: StudentProfileCreate,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    # Check if user has admin, school_IT, ssg, or event-organizer role
    required_roles = ["admin", "school_IT", "ssg", "event-organizer", "event_organizer"]
    if not has_required_roles(current_user, required_roles):
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions. Requires admin, SCHOOL_IT, SSG or event-organizer role"
        )
    # 1. Verify target user exists
    target_user = _query_user_for_actor(db, profile.user_id, current_user)
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    target_school_id = getattr(target_user, "school_id", None)
    if target_school_id is None:
        raise HTTPException(status_code=400, detail="Target user is not assigned to a school")
    
    # 2. Verify student ID doesn't exist
    if (
        db.query(StudentProfile)
        .join(UserModel, StudentProfile.user_id == UserModel.id)
        .filter(StudentProfile.student_id == profile.student_id, UserModel.school_id == target_school_id)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Student ID already in use")
    
    # 3. Verify department and program exist
    department = db.get(Department, profile.department_id)
    program = db.get(Program, profile.program_id)
    
    if not department or not program:
        raise HTTPException(status_code=400, detail="Invalid department or program ID")
    
    # 4. Verify program belongs to department (many-to-many check)
    association_exists = db.execute(
        select(program_department_association)
        .where(
            (program_department_association.c.department_id == department.id) &
            (program_department_association.c.program_id == program.id)
        )
    ).first()

    if not association_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Program '{program.name}' is not offered by department '{department.name}'"
        )
    
    # 5. Create profile
    try:
        student_profile = StudentProfile(
            user_id=profile.user_id,
            school_id=target_school_id,
            student_id=profile.student_id,
            department_id=profile.department_id,
            program_id=profile.program_id,
            year_level=profile.year_level
        )
        
        db.add(student_profile)
        db.commit()
        db.refresh(target_user)
        
        return UserWithRelations.from_orm(target_user)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create student profile: {str(e)}"
        )


@router.get("", response_model=List[UserWithRelations], include_in_schema=False)
@router.get("/", response_model=List[UserWithRelations])
def get_all_users(
    skip: int = 0, 
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Get all users with pagination, including their profiles and roles.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (for pagination)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of users with all related data
    """
    # Allow admin, SCHOOL_IT, SSG, or event-organizer to access school-scoped users
    required_roles = ["admin", "school_IT", "ssg", "event-organizer", "event_organizer"]
    if not has_required_roles(current_user, required_roles):
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions. Requires admin, SCHOOL_IT, SSG or event-organizer role"
        )
    # Get users with eager loading of relationships
    query = db.query(UserModel)
    query = _apply_user_scope(query, current_user)
    users = query.offset(skip).limit(limit).all()
    return [UserWithRelations.from_orm(user) for user in users]


@router.get("/by-role/{role_name}", response_model=List[UserWithRelations])
def get_users_by_role(
    role_name: str,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Get users filtered by role.
    
    Args:
        role_name: Role name to filter by (student, ssg, admin, etc.)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (for pagination)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of users with the specified role
    """
    # Allow admin, SCHOOL_IT, SSG, or event-organizer to filter users by role
    required_roles = ["admin", "school_IT", "ssg", "event-organizer", "event_organizer"]
    if not has_required_roles(current_user, required_roles):
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions. Requires admin, SCHOOL_IT, SSG or event-organizer role"
        )
    # Find all users with the specified role
    query = (
        db.query(UserModel)
        .join(UserRole)
        .join(Role)
        .filter(Role.name == role_name)
    )
    query = _apply_user_scope(query, current_user)
    users = query.offset(skip).limit(limit).all()
    
    return [UserWithRelations.from_orm(user) for user in users]

@router.get("/ssg-positions/", response_model=List[dict])
def get_ssg_position_types():
    """Get all valid SSG position types for dropdowns"""
    return [{"value": e.value, "label": e.value} for e in SSGPositionEnum]


@router.post("/ssg-profiles/", response_model=UserWithRelations)
def create_ssg_profile(
    profile: SSGProfileCreate,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """Create SSG profile endpoint with validated position"""
    required_roles = ["admin", "school_IT", "ssg", "event-organizer", "event_organizer"]
    if not has_required_roles(current_user, required_roles):
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions"
        )
    # Get the target user
    user = _query_user_for_actor(db, profile.user_id, current_user)
    if not user:
        raise HTTPException(404, "User not found")
    
    # Verify SSG role exists
    if not any(role.role.name == "ssg" for role in user.roles):
        raise HTTPException(400, "User does not have SSG role")
    
    # Check for existing profile
    if user.ssg_profile:
        raise HTTPException(400, "User already has an SSG profile")
    
    # Create the profile (position is automatically validated by Pydantic)
    ssg_profile = SSGProfile(
        user_id=user.id,
        position=profile.position  # This is now an SSGPositionEnum value
    )
    
    db.add(ssg_profile)
    db.commit()
    db.refresh(user)
    return UserWithRelations.from_orm(user)


@router.get("/me/", response_model=UserWithRelations)
def get_current_user_profile(
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Get current user with all profile information
    """
    # Accessible to any authenticated user
    # Refresh to ensure we have the latest data
    db.refresh(current_user)
    return UserWithRelations.from_orm(current_user)


@router.get("/ssg-members/", response_model=List[UserWithRelations])
def get_ssg_members(
    skip: int = 0,
    limit: int = 100,
    include_profiles: bool = True,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """Get all SSG members with their positions"""
    query = (
        db.query(UserModel)
        .join(UserRole)
        .join(Role)
        .filter(Role.name == "ssg")
        .order_by(UserModel.last_name)
    )
    query = _apply_user_scope(query, current_user)
    
    if include_profiles:
        query = query.options(
            joinedload(UserModel.roles).joinedload(UserRole.role),
            joinedload(UserModel.ssg_profile)
        )
    
    ssg_members = query.offset(skip).limit(limit).all()
    
    return [UserWithRelations.from_orm(user) for user in ssg_members]

# Add these endpoints to your existing router
@router.patch("/{user_id}", response_model=UserWithRelations)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Partially update a user's basic information.
    
    Args:
        user_id: ID of the user to update
        user_update: Updated user data (only fields that need to be changed)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user with all related data
    """
    # Allow admin or SCHOOL_IT to update other users in the same school, or users can update themselves.
    if current_user.id != user_id and not has_required_roles(current_user, ["admin", "school_IT"]):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to update this user"
        )
    
    # Get the user to update
    db_user = _query_user_for_actor(db, user_id, current_user)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # SCHOOL_IT cannot modify admin/school_IT accounts.
    if _is_school_it(current_user) and not _is_admin(current_user):
        if current_user.id != db_user.id and _target_has_admin_or_school_it(db_user):
            raise HTTPException(
                status_code=403,
                detail="SCHOOL_IT cannot modify admin or SCHOOL_IT accounts.",
            )
    
    # Only update fields that are provided in the request
    if user_update.email is not None:
        # Check if email is being changed and if it already exists
        if db_user.email != user_update.email:
            existing_email_user = (
                db.query(UserModel)
                .filter(UserModel.email == user_update.email, UserModel.id != db_user.id)
                .first()
            )
            if existing_email_user:
                detail = "Email already registered in this school"
                actor_school_id = _actor_school_scope_id(current_user)
                if actor_school_id is None:
                    detail = "Email already registered"
                elif existing_email_user.school_id != actor_school_id:
                    detail = "Email already registered in another school"
                raise HTTPException(status_code=400, detail=detail)
        db_user.email = user_update.email
    
    if user_update.first_name is not None:
        db_user.first_name = user_update.first_name
        
    if user_update.middle_name is not None:
        db_user.middle_name = user_update.middle_name
        
    if user_update.last_name is not None:
        db_user.last_name = user_update.last_name
    
    db.commit()
    db.refresh(db_user)
    
    return UserWithRelations.from_orm(db_user)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Delete a user.
    
    Args:
        user_id: ID of the user to delete
        current_user: Current authenticated user
        db: Database session
    """
    # Admin and SCHOOL_IT can delete users in their own school scope.
    if not has_required_roles(current_user, ["admin", "school_IT"]):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Admin or SCHOOL_IT role required."
        )
    # Get the user to delete
    db_user = _query_user_for_actor(db, user_id, current_user)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if _is_school_it(current_user) and not _is_admin(current_user):
        if current_user.id == db_user.id:
            raise HTTPException(status_code=403, detail="SCHOOL_IT cannot delete their own account.")
        if _target_has_admin_or_school_it(db_user):
            raise HTTPException(
                status_code=403,
                detail="SCHOOL_IT cannot delete admin or SCHOOL_IT accounts.",
            )
    
    # Delete the user
    db.delete(db_user)
    db.commit()
    
    return None


@router.patch("/student-profiles/{profile_id}", response_model=UserWithRelations)
def update_student_profile(
    profile_id: int,
    profile_update: StudentProfileBase,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Partially update a student profile.
    
    Args:
        profile_id: ID of the student profile to update
        profile_update: Updated profile data (only fields that need to be changed)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User with updated student profile
    """
    # Allow admin, SCHOOL_IT, SSG, or event-organizer to update student profiles
    required_roles = ["admin", "school_IT", "ssg", "event-organizer", "event_organizer"]
    if not has_required_roles(current_user, required_roles):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Requires admin, SCHOOL_IT, SSG or event-organizer role"
        )
    # Get the profile to update
    profile_query = (
        db.query(StudentProfile)
        .join(UserModel, StudentProfile.user_id == UserModel.id)
        .filter(StudentProfile.id == profile_id)
    )
    actor_school_id = _actor_school_scope_id(current_user)
    if actor_school_id is not None:
        profile_query = profile_query.filter(UserModel.school_id == actor_school_id)
    profile = profile_query.first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    target_user = db.query(UserModel).filter(UserModel.id == profile.user_id).first()
    target_school_id = getattr(target_user, "school_id", None)
    if target_school_id is None:
        raise HTTPException(status_code=400, detail="Target user is not assigned to a school")
    
    # Only update fields that are provided in the request
    if profile_update.student_id is not None:
        # Check if student ID is being changed and if it already exists
        if profile.student_id != profile_update.student_id:
            if (
                db.query(StudentProfile)
                .join(UserModel, StudentProfile.user_id == UserModel.id)
                .filter(
                    StudentProfile.student_id == profile_update.student_id,
                    UserModel.school_id == target_school_id,
                )
                .first()
            ):
                raise HTTPException(status_code=400, detail="Student ID already in use")
        profile.student_id = profile_update.student_id
    
    if profile_update.department_id is not None or profile_update.program_id is not None:
        # If either department or program is being updated, we need to validate both
        department_id = profile_update.department_id if profile_update.department_id is not None else profile.department_id
        program_id = profile_update.program_id if profile_update.program_id is not None else profile.program_id
        
        department = db.get(Department, department_id)
        program = db.get(Program, program_id)
        
        if not department or not program:
            raise HTTPException(status_code=400, detail="Invalid department or program ID")
        
        # Verify program belongs to department (many-to-many check)
        association_exists = db.execute(
            select(program_department_association)
            .where(
                (program_department_association.c.department_id == department.id) &
                (program_department_association.c.program_id == program.id)
            )
        ).first()

        if not association_exists:
            raise HTTPException(
                status_code=400,
                detail=f"Program '{program.name}' is not offered by department '{department.name}'"
            )
        
        if profile_update.department_id is not None:
            profile.department_id = profile_update.department_id
        if profile_update.program_id is not None:
            profile.program_id = profile_update.program_id
    
    if profile_update.year_level is not None:
        profile.year_level = profile_update.year_level
    
    db.commit()
    db.refresh(profile)
    
    # Return the full user with updated profile
    user = _query_user_for_actor(db, profile.user_id, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserWithRelations.from_orm(user)


@router.delete("/student-profiles/{profile_id}", status_code=204)
def delete_student_profile(
    profile_id: int,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Delete a student profile.
    
    Args:
        profile_id: ID of the student profile to delete
        current_user: Current authenticated user
        db: Database session
    """
    # Admin and SCHOOL_IT can delete student profiles in their school.
    if not has_required_roles(current_user, ["admin", "school_IT"]):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Admin or SCHOOL_IT role required."
        )
    # Get the profile to delete
    profile_query = (
        db.query(StudentProfile)
        .join(UserModel, StudentProfile.user_id == UserModel.id)
        .filter(StudentProfile.id == profile_id)
    )
    actor_school_id = _actor_school_scope_id(current_user)
    if actor_school_id is not None:
        profile_query = profile_query.filter(UserModel.school_id == actor_school_id)
    profile = profile_query.first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    # Delete the profile
    db.delete(profile)
    db.commit()
    
    return None


@router.put("/ssg-profiles/{profile_id}", response_model=UserWithRelations)
def update_ssg_profile(
    profile_id: int,
    profile_update: SSGProfileBase,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Update an SSG profile.
    
    Args:
        profile_id: ID of the SSG profile to update
        profile_update: Updated profile data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User with updated SSG profile
    """
    # Allow admin, SCHOOL_IT, or SSG to update SSG profiles
    required_roles = ["admin", "school_IT", "ssg"]
    if not has_required_roles(current_user, required_roles):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Requires admin, SCHOOL_IT or SSG role"
        )
    # Get the profile to update
    profile_query = (
        db.query(SSGProfile)
        .join(UserModel, SSGProfile.user_id == UserModel.id)
        .filter(SSGProfile.id == profile_id)
    )
    actor_school_id = _actor_school_scope_id(current_user)
    if actor_school_id is not None:
        profile_query = profile_query.filter(UserModel.school_id == actor_school_id)
    profile = profile_query.first()
    if not profile:
        raise HTTPException(status_code=404, detail="SSG profile not found")
    
    # Update profile fields (position is validated by Pydantic)
    profile.position = profile_update.position
    
    db.commit()
    db.refresh(profile)
    
    # Return the full user with updated profile
    user = _query_user_for_actor(db, profile.user_id, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserWithRelations.from_orm(user)


@router.delete("/ssg-profiles/{profile_id}", status_code=204)
def delete_ssg_profile(
    profile_id: int,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Delete an SSG profile.
    
    Args:
        profile_id: ID of the SSG profile to delete
        current_user: Current authenticated user
        db: Database session
    """
    # Admin and SCHOOL_IT can delete SSG profiles in their school.
    if not has_required_roles(current_user, ["admin", "school_IT"]):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Admin or SCHOOL_IT role required."
        )
    # Get the profile to delete
    profile_query = (
        db.query(SSGProfile)
        .join(UserModel, SSGProfile.user_id == UserModel.id)
        .filter(SSGProfile.id == profile_id)
    )
    actor_school_id = _actor_school_scope_id(current_user)
    if actor_school_id is not None:
        profile_query = profile_query.filter(UserModel.school_id == actor_school_id)
    profile = profile_query.first()
    if not profile:
        raise HTTPException(status_code=404, detail="SSG profile not found")
    
    # Delete the profile
    db.delete(profile)
    db.commit()
    
    return None


@router.put("/{user_id}/roles", response_model=UserWithRelations)
def update_user_roles(
    user_id: int,
    role_update: UserRoleUpdate,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Update a user's roles.
    
    Args:
        user_id: ID of the user to update roles for
        roles: List of role names to assign
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User with updated roles
    """
    # Admin and SCHOOL_IT can update roles inside their school scope.
    if not has_required_roles(current_user, ["admin", "school_IT"]):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Admin or SCHOOL_IT role required."
        )
    # Get the user to update
    user = _query_user_for_actor(db, user_id, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    requested_role_values = [role_name.value for role_name in role_update.roles]
    _assert_school_it_assignable_roles(current_user, requested_role_values)
    if _is_school_it(current_user) and not _is_admin(current_user) and _target_has_admin_or_school_it(user):
        raise HTTPException(
            status_code=403,
            detail="SCHOOL_IT cannot update roles for admin or SCHOOL_IT accounts.",
        )
    
    # Delete existing roles
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    
    # Add new roles
    for role_name in role_update.roles:
        role = db.query(Role).filter(Role.name == role_name.value).first()
        if not role:
            raise HTTPException(
                status_code=400,
                detail=f"Role '{role_name.value}' does not exist in database"
            )
        db.add(UserRole(user_id=user.id, role_id=role.id))
    
    db.commit()
    db.refresh(user)
    
    return UserWithRelations.from_orm(user)


@router.get("/{user_id}", response_model=UserWithRelations)
def get_user_by_id(
    user_id: int,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Get a user by ID with all profile information.
    
    Args:
        user_id: ID of the user to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User with all related data
    """
    # Allow users to get their own profile or admin/SCHOOL_IT/SSG/event-organizer to get any profile in-school.
    if current_user.id != user_id and not has_required_roles(
        current_user, ["admin", "school_IT", "ssg", "event-organizer", "event_organizer"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to view this user"
        )
    
    # Get the user
    user = _query_user_for_actor(db, user_id, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserWithRelations.from_orm(user)


@router.post("/{user_id}/reset-password", status_code=204)
def reset_user_password(
    user_id: int,
    password_update: PasswordUpdate,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db)
):
    """
    Reset a user's password.
    
    Args:
        user_id: ID of the user to reset password for
        password: New password
        current_user: Current authenticated user
        db: Database session
    """
    # Admin and SCHOOL_IT can reset passwords in school scope, or users can reset their own.
    if current_user.id != user_id and not has_required_roles(current_user, ["admin", "school_IT"]):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to reset this user's password"
        )
    
    # Get the user
    user = _query_user_for_actor(db, user_id, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if _is_school_it(current_user) and not _is_admin(current_user):
        if current_user.id != user.id and _target_has_admin_or_school_it(user):
            raise HTTPException(
                status_code=403,
                detail="SCHOOL_IT cannot reset password for admin or SCHOOL_IT accounts.",
            )
    
    # Update password
    user.set_password(password_update.password)
    user.must_change_password = True
    db.commit()
    
    return None    

@router.post("/events/{event_id}/ssg-members", response_model=EventSchema)
def assign_ssg_members_to_event(
    event_id: int,
    ssg_member_ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_roles)
):
    """Assign SSG members to an event"""
    try:
        # Check permissions
        required_roles = ["admin", "event-organizer"]
        if not has_required_roles(current_user, required_roles):
            raise HTTPException(403, "Insufficient permissions")
        actor_school_id = _actor_school_scope_id(current_user)

        # Get the event - using MODEL class
        event_query = db.query(Event).options(
            joinedload(Event.ssg_members)
        ).filter(Event.id == event_id)
        if actor_school_id is not None:
            event_query = event_query.filter(Event.school_id == actor_school_id)
        event = event_query.first()
        
        if not event:
            raise HTTPException(404, "Event not found")
        event_school_id = getattr(event, "school_id", None)
        if event_school_id is None:
            raise HTTPException(400, "Event is not linked to a school")

        # Verify all SSG members exist
        existing_members = db.query(SSGProfile.id).join(
            UserModel, SSGProfile.user_id == UserModel.id
        ).filter(
            SSGProfile.id.in_(ssg_member_ids),
            UserModel.school_id == event_school_id,
        ).all()
        
        existing_ids = {m[0] for m in existing_members}
        missing_ids = set(ssg_member_ids) - existing_ids
        
        if missing_ids:
            raise HTTPException(400, f"Invalid SSG member IDs: {missing_ids}")

        # Clear existing and assign new members
        event.ssg_members = []
        for member_id in ssg_member_ids:
            member = db.query(SSGProfile).join(
                UserModel, SSGProfile.user_id == UserModel.id
            ).filter(
                SSGProfile.id == member_id,
                UserModel.school_id == event_school_id,
            ).first()
            if member:
                event.ssg_members.append(member)

        db.commit()
        db.refresh(event)
        return event
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(500, "Database error") from e
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e)) from e
