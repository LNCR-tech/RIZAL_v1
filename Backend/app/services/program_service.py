"""Use: Contains the main backend rules for program creation and update rules.
Where to use: Use this from routers, workers, or other services when program creation and update rules logic is needed.
Role: Service layer. It keeps business logic out of the route files.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.department import Department as DepartmentModel
from app.models.program import Program as ProgramModel
from app.schemas.program import ProgramCreate, ProgramUpdate

logger = logging.getLogger(__name__)


def _programs_query(db: Session):
    return db.query(ProgramModel).options(selectinload(ProgramModel.departments))


def _normalize_department_ids(department_ids: list[int] | None) -> list[int]:
    return list(dict.fromkeys(department_ids or []))


def _load_departments_or_404(
    db: Session,
    *,
    school_id: int,
    department_ids: list[int] | None,
) -> list[DepartmentModel]:
    normalized_ids = _normalize_department_ids(department_ids)
    if not normalized_ids:
        return []

    departments = (
        db.query(DepartmentModel)
        .filter(
            DepartmentModel.school_id == school_id,
            DepartmentModel.id.in_(normalized_ids),
        )
        .order_by(DepartmentModel.name.asc())
        .all()
    )
    if len(departments) != len(normalized_ids):
        found_ids = {department.id for department in departments}
        missing = sorted(set(normalized_ids) - found_ids)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Departments not found: {missing}",
        )
    return departments


def list_programs(
    db: Session,
    *,
    school_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[ProgramModel]:
    try:
        return (
            _programs_query(db)
            .filter(ProgramModel.school_id == school_id)
            .order_by(ProgramModel.name.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    except Exception as exc:
        logger.error("Error fetching programs", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch programs",
        ) from exc


def get_program_or_404(db: Session, program_id: int, *, school_id: int) -> ProgramModel:
    program = (
        _programs_query(db)
        .filter(
            ProgramModel.id == program_id,
            ProgramModel.school_id == school_id,
        )
        .first()
    )
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )
    return program


def create_program(db: Session, payload: ProgramCreate, *, school_id: int) -> ProgramModel:
    program_name = payload.name.strip()
    departments = _load_departments_or_404(db, school_id=school_id, department_ids=payload.department_ids)

    existing = (
        db.query(ProgramModel)
        .filter(
            ProgramModel.school_id == school_id,
            func.lower(ProgramModel.name) == func.lower(program_name),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Program '{program_name}' already exists",
        )

    try:
        program = ProgramModel(name=program_name, school_id=school_id)
        program.departments = departments
        db.add(program)
        db.commit()
        return get_program_or_404(db, program.id, school_id=school_id)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Integrity error creating program", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Program '{program_name}' already exists",
        ) from exc
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Error creating program", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create program",
        ) from exc


def update_program(
    db: Session,
    *,
    program_id: int,
    school_id: int,
    payload: ProgramUpdate,
) -> ProgramModel:
    program = get_program_or_404(db, program_id, school_id=school_id)

    if payload.name is not None:
        program_name = payload.name.strip()
        existing = (
            db.query(ProgramModel)
            .filter(
                ProgramModel.school_id == school_id,
                func.lower(ProgramModel.name) == func.lower(program_name),
                ProgramModel.id != program_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Program '{program_name}' already exists",
            )
        program.name = program_name

    if payload.department_ids is not None:
        program.departments = _load_departments_or_404(
            db,
            school_id=school_id,
            department_ids=payload.department_ids,
        )

    try:
        db.commit()
        return get_program_or_404(db, program_id, school_id=school_id)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Error updating program", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update program",
        ) from exc


def delete_program(db: Session, program_id: int, *, school_id: int) -> None:
    program = get_program_or_404(db, program_id, school_id=school_id)

    try:
        db.delete(program)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.error("Integrity error deleting program", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete program - it's referenced by other records",
        ) from exc
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Error deleting program", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete program",
        ) from exc
