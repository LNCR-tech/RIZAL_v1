"""Use: Handles user and account management API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs user and account management features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
from app.core.security import (
    canonicalize_role_name_for_storage,
    get_current_admin_or_campus_admin,
    get_current_application_user,
    get_school_id_or_403,
    get_role_lookup_names,
    has_any_role,
    normalize_role_name,
)
from app.models.department import Department
from app.models.program import Program
from app.models.school import School
from sqlalchemy import select

from app.schemas.user import (
    UserCreate,
    UserCreateResponse,
    UserWithRelations,
    StudentProfileCreate,
    UserUpdate,
    PasswordUpdate,
    UserRoleUpdate,
    StudentProfileBase,
)
from app.models.user import User as UserModel, UserRole, StudentProfile
from app.models.role import Role
from app.models.governance_hierarchy import PermissionCode
from app.services.email_service import EmailDeliveryError, send_welcome_email
from app.services.password_change_policy import (
    must_change_password_for_new_account,
    must_change_password_for_temporary_reset,
    should_prompt_password_change_for_new_account,
    should_prompt_password_change_for_temporary_reset,
)
from app.utils.passwords import generate_secure_password
from app.core.dependencies import get_db
from sqlalchemy.orm import joinedload
from app.models.associations import program_department_association
from app.services import governance_hierarchy_service

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


def _serialize_user(user: UserModel) -> UserWithRelations:
    return UserWithRelations.model_validate(user, from_attributes=True)


def _serialize_users(users: list[UserModel]) -> list[UserWithRelations]:
    return [_serialize_user(user) for user in users]


# Helper function to check if user has any of the required roles
def has_required_roles(user: UserModel, required_roles: List[str]) -> bool:
    """Check if user has any of the required roles"""
    return has_any_role(user, required_roles)


def _is_admin(user: UserModel) -> bool:
    return has_required_roles(user, ["admin"])


def _is_school_it(user: UserModel) -> bool:
    return has_required_roles(user, ["campus_admin"])


def _can_manage_student_profiles(db: Session, current_user: UserModel) -> bool:
    if has_required_roles(current_user, ["admin", "campus_admin"]):
        return True

    return governance_hierarchy_service.user_has_governance_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.MANAGE_STUDENTS,
    )


def _target_has_admin_or_school_it(user: UserModel) -> bool:
    target_roles = {
        normalize_role_name(role.role.name)
        for role in user.roles
        if getattr(role, "role", None) and getattr(role.role, "name", None)
    }
    return "admin" in target_roles or "campus-admin" in target_roles


def _assert_school_it_assignable_roles(current_user: UserModel, role_names: List[str]) -> None:
    if not _is_school_it(current_user) or _is_admin(current_user):
        return

    allowed_roles = {"student"}
    normalized_requested = {normalize_role_name(name) for name in role_names}
    disallowed = sorted(normalized_requested - allowed_roles)
    if disallowed:
        raise HTTPException(
            status_code=403,
            detail=(
                "Campus Admin can only assign the student role from user management. "
                "Use Manage SSG for officer assignments. "
                f"Disallowed roles: {', '.join(disallowed)}"
            ),
        )


def _query_user_in_school(db: Session, user_id: int, school_id: int) -> UserModel | None:
    return (
        db.query(UserModel)
        .filter(UserModel.id == user_id, UserModel.school_id == school_id)
        .first()
    )


def _get_role_by_name_or_alias(db: Session, role_name: str) -> Role | None:
    for candidate in get_role_lookup_names(role_name):
        role = db.query(Role).filter(Role.name == candidate).first()
        if role is not None:
            return role
    return None


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


def _get_department_and_program_for_school_or_400(
    db: Session,
    *,
    school_id: int,
    department_id: int,
    program_id: int,
) -> tuple[Department, Program]:
    department = (
        db.query(Department)
        .filter(
            Department.id == department_id,
            Department.school_id == school_id,
        )
        .first()
    )
    program = (
        db.query(Program)
        .filter(
            Program.id == program_id,
            Program.school_id == school_id,
        )
        .first()
    )

    if not department or not program:
        raise HTTPException(
            status_code=400,
            detail="Invalid department or program ID for this school",
        )

    association_exists = db.execute(
        select(program_department_association).where(
            (program_department_association.c.department_id == department.id)
            & (program_department_association.c.program_id == program.id)
        )
    ).first()

    if not association_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Program '{program.name}' is not offered by department '{department.name}'",
        )

    return department, program


@router.post("", response_model=UserCreateResponse, include_in_schema=False)
@router.post("/", response_model=UserCreateResponse)
def create_user(
    user: UserCreate,
    current_user: UserModel = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
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

    role_names = [canonicalize_role_name_for_storage(role.value) for role in user.roles]
    _assert_school_it_assignable_roles(current_user, role_names)

    role_map = {
        role_name: _get_role_by_name_or_alias(db, role_name)
        for role_name in role_names
    }
    missing_roles = [role_name for role_name, role in role_map.items() if role is None]

    if missing_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Role(s) not found: {', '.join(missing_roles)}"
        )

    try:
        generated_temporary_password = None
        issued_password = user.password
        if not issued_password:
            generated_temporary_password = generate_secure_password(min_length=10, max_length=14)
            issued_password = generated_temporary_password

        # Create user and role links in one transaction.
        db_user = UserModel(
            email=user.email,
            school_id=school_id,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            must_change_password=must_change_password_for_new_account(),
            should_prompt_password_change=should_prompt_password_change_for_new_account(),
        )
        db_user.set_password(issued_password)
        db.add(db_user)
        db.flush()

        for role_name in role_names:
            db.add(UserRole(user_id=db_user.id, role_id=role_map[role_name].id))

        db.commit()
        db.refresh(db_user)
        db_user = (
            db.query(UserModel)
            .options(joinedload(UserModel.roles).joinedload(UserRole.role))
            .filter(UserModel.id == db_user.id)
            .first()
        )

        school = db.query(School).filter(School.id == school_id).first()
        system_name = None
        if school is not None:
            system_name = school.school_name or school.name

        try:
            send_welcome_email(
                recipient_email=db_user.email,
                temporary_password=issued_password,
                first_name=db_user.first_name,
                system_name=system_name,
                password_is_temporary=generated_temporary_password is not None,
            )
        except EmailDeliveryError as exc:
            logger.warning(
                "Welcome email delivery failed for user_id=%s email=%s error=%s",
                db_user.id,
                db_user.email,
                str(exc),
            )

        return UserCreateResponse.model_validate(
            db_user,
            from_attributes=True,
        ).model_copy(
            update={"generated_temporary_password": generated_temporary_password},
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {exc}")

@router.post("/admin/students/", response_model=UserWithRelations)
def create_student_profile(
    profile: StudentProfileCreate,
    current_user: UserModel = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db)
):
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
    
    # 3. Verify department and program belong to the same school and academic pairing.
    _get_department_and_program_for_school_or_400(
        db,
        school_id=target_school_id,
        department_id=profile.department_id,
        program_id=profile.program_id,
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
        
        return _serialize_user(target_user)
        
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
    current_user: UserModel = Depends(get_current_admin_or_campus_admin),
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
    # Get users with eager loading of relationships
    query = db.query(UserModel)
    query = _apply_user_scope(query, current_user)
    users = query.offset(skip).limit(limit).all()
    return _serialize_users(users)


@router.get("/by-role/{role_name}", response_model=List[UserWithRelations])
def get_users_by_role(
    role_name: str,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_admin_or_campus_admin),
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
    # Find all users with the specified role
    query = (
        db.query(UserModel)
        .join(UserRole)
        .join(Role)
        .filter(Role.name.in_(get_role_lookup_names(role_name)))
    )
    query = _apply_user_scope(query, current_user)
    users = query.offset(skip).limit(limit).all()
    
    return _serialize_users(users)

@router.get("/me/", response_model=UserWithRelations)
def get_current_user_profile(
    current_user: UserModel = Depends(get_current_application_user),
    db: Session = Depends(get_db)
):
    """
    Get current user with all profile information
    """
    # Accessible to any authenticated user
    # Refresh to ensure we have the latest data
    db.refresh(current_user)
    return _serialize_user(current_user)


# Add these endpoints to your existing router
@router.patch("/{user_id}", response_model=UserWithRelations)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_application_user),
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
    # Allow admin or Campus Admin to update other users in the same school, or users can update themselves.
    if current_user.id != user_id and not has_required_roles(current_user, ["admin", "campus_admin"]):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to update this user"
        )
    
    # Get the user to update
    db_user = _query_user_for_actor(db, user_id, current_user)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Campus Admin cannot modify admin or campus-admin accounts.
    if _is_school_it(current_user) and not _is_admin(current_user):
        if current_user.id != db_user.id and _target_has_admin_or_school_it(db_user):
            raise HTTPException(
                status_code=403,
                detail="Campus Admin cannot modify admin or Campus Admin accounts.",
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
    
    return _serialize_user(db_user)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a user.
    
    Args:
        user_id: ID of the user to delete
        current_user: Current authenticated user
        db: Database session
    """
    # Get the user to delete
    db_user = _query_user_for_actor(db, user_id, current_user)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if _is_school_it(current_user) and not _is_admin(current_user):
        if current_user.id == db_user.id:
            raise HTTPException(status_code=403, detail="Campus Admin cannot delete their own account.")
        if _target_has_admin_or_school_it(db_user):
            raise HTTPException(
                status_code=403,
                detail="Campus Admin cannot delete admin or Campus Admin accounts.",
            )
    
    # Delete the user
    db.delete(db_user)
    db.commit()
    
    return None


@router.patch("/student-profiles/{profile_id}", response_model=UserWithRelations)
def update_student_profile(
    profile_id: int,
    profile_update: StudentProfileBase,
    current_user: UserModel = Depends(get_current_application_user),
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
    if not _can_manage_student_profiles(db, current_user):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to manage student profiles"
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
        
        _get_department_and_program_for_school_or_400(
            db,
            school_id=profile.school_id,
            department_id=department_id,
            program_id=program_id,
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
    return _serialize_user(user)


@router.delete("/student-profiles/{profile_id}", status_code=204)
def delete_student_profile(
    profile_id: int,
    current_user: UserModel = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a student profile.
    
    Args:
        profile_id: ID of the student profile to delete
        current_user: Current authenticated user
        db: Database session
    """
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


@router.put("/{user_id}/roles", response_model=UserWithRelations)
def update_user_roles(
    user_id: int,
    role_update: UserRoleUpdate,
    current_user: UserModel = Depends(get_current_admin_or_campus_admin),
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
    # Get the user to update
    user = _query_user_for_actor(db, user_id, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    requested_role_values = [canonicalize_role_name_for_storage(role_name.value) for role_name in role_update.roles]
    if _is_school_it(current_user) and not _is_admin(current_user):
        raise HTTPException(
            status_code=403,
            detail=(
                "Campus Admin cannot change user roles from Manage Users. "
                "Imported users stay students, and SSG access is managed from Manage SSG."
            ),
        )
    _assert_school_it_assignable_roles(current_user, requested_role_values)
    if _is_school_it(current_user) and not _is_admin(current_user) and _target_has_admin_or_school_it(user):
        raise HTTPException(
            status_code=403,
            detail="Campus Admin cannot update roles for admin or Campus Admin accounts.",
        )
    
    # Delete existing roles
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    
    # Add new roles
    for role_name in requested_role_values:
        role = _get_role_by_name_or_alias(db, role_name)
        if not role:
            raise HTTPException(
                status_code=400,
                detail=f"Role '{role_name}' does not exist in database"
            )
        db.add(UserRole(user_id=user.id, role_id=role.id))
    
    db.commit()
    db.refresh(user)
    
    return _serialize_user(user)


@router.get("/{user_id}", response_model=UserWithRelations)
def get_user_by_id(
    user_id: int,
    current_user: UserModel = Depends(get_current_application_user),
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
    # Allow users to get their own profile or admin/Campus Admin to get any profile in-school.
    if current_user.id != user_id and not has_required_roles(
        current_user, ["admin", "campus_admin"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to view this user"
        )
    
    # Get the user
    user = _query_user_for_actor(db, user_id, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return _serialize_user(user)


@router.post("/{user_id}/reset-password", status_code=204)
def reset_user_password(
    user_id: int,
    password_update: PasswordUpdate,
    current_user: UserModel = Depends(get_current_application_user),
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
    # Admin and Campus Admin can reset passwords in school scope, or users can reset their own.
    if current_user.id != user_id and not has_required_roles(current_user, ["admin", "campus_admin"]):
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
                detail="Campus Admin cannot reset password for admin or Campus Admin accounts.",
            )
    
    # Update password
    user.set_password(password_update.password)
    user.must_change_password = must_change_password_for_temporary_reset()
    user.should_prompt_password_change = should_prompt_password_change_for_temporary_reset()
    db.commit()
    
    return None    


