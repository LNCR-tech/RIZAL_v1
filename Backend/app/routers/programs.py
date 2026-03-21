"""Use: Handles program management API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs program management features.
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
from app.schemas.program import Program as ProgramSchema, ProgramCreate, ProgramUpdate
from app.services import program_service

router = APIRouter(prefix="/programs", tags=["programs"])

@router.post("/", response_model=ProgramSchema, status_code=status.HTTP_201_CREATED)
def create_program(
    program: ProgramCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_school_it),
):
    return program_service.create_program(
        db,
        program,
        school_id=get_school_id_or_403(current_user),
    )

@router.get("/", response_model=list[ProgramSchema])
def read_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserModel = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    return program_service.list_programs(
        db,
        school_id=get_school_id_or_403(current_user),
        skip=skip,
        limit=limit,
    )

@router.get("/{program_id}", response_model=ProgramSchema)
def read_program(
    program_id: int,
    current_user: UserModel = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    return program_service.get_program_or_404(
        db,
        program_id,
        school_id=get_school_id_or_403(current_user),
    )

@router.patch("/{program_id}", response_model=ProgramSchema)
def update_program(
    program_id: int,
    program_update: ProgramUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_school_it),
):
    return program_service.update_program(
        db,
        program_id=program_id,
        school_id=get_school_id_or_403(current_user),
        payload=program_update,
    )


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_school_it),
):
    program_service.delete_program(
        db,
        program_id,
        school_id=get_school_id_or_403(current_user),
    )
    return None
