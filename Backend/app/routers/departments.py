"""Use: Handles department management API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs department management features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.security import (
    get_current_application_user,
    get_current_school_it,
    get_school_id_or_403,
)
from app.models.user import User as UserModel
from app.schemas.department import (
    Department as DepartmentSchema,
    DepartmentCreate,
    DepartmentUpdate,
)
from app.services import department_service

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post(
    "/",
    response_model=DepartmentSchema,
    status_code=status.HTTP_201_CREATED
)
def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_school_it),
):
    """
    Create a new department.
    
    - **name**: Department name (must be unique, 2-100 characters)
    """
    return department_service.create_department(
        db,
        department,
        school_id=get_school_id_or_403(current_user),
    )

@router.get("/", response_model=list[DepartmentSchema])
def read_departments(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    current_user: UserModel = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve list of departments with pagination.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return (1-1000)
    """
    return department_service.list_departments(
        db,
        school_id=get_school_id_or_403(current_user),
        skip=skip,
        limit=limit,
    )

@router.get("/{department_id}", response_model=DepartmentSchema)
def read_department(
    department_id: int,
    current_user: UserModel = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    """
    Get a single department by ID.
    
    - **department_id**: ID of the department to retrieve
    """
    return department_service.get_department_or_404(
        db,
        department_id,
        school_id=get_school_id_or_403(current_user),
    )

@router.patch("/{department_id}", response_model=DepartmentSchema)
def update_department(
    department_id: int,
    department_update: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_school_it),
):
    """
    Update department information.
    
    - **department_id**: ID of the department to update
    - **name**: New department name (optional)
    """
    return department_service.update_department(
        db,
        department_id=department_id,
        school_id=get_school_id_or_403(current_user),
        payload=department_update,
    )

@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_school_it),
):
    """
    Delete a department.
    
    - **department_id**: ID of the department to delete
    """
    department_service.delete_department(
        db,
        department_id,
        school_id=get_school_id_or_403(current_user),
    )
    return None
