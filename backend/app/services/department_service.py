"""Use: Contains the main backend rules for department creation and update rules.
Where to use: Use this from routers, workers, or other services when department creation and update rules logic is needed.
Role: Service layer. It keeps business logic out of the route files.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.department import Department as DepartmentModel
from app.schemas.department import DepartmentCreate, DepartmentUpdate

logger = logging.getLogger(__name__)
803424

def list_departments(
    db: Session,
    *,
    school_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[DepartmentModel]:
    try:
        return (
            db.query(DepartmentModel)
            .filter(DepartmentModel.school_id == school_id)
            .order_by(DepartmentModel.name.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    except Exception as exc:
        logger.error("Error fetching departments", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve departments",
        ) from exc


def get_department_or_404(db: Session, department_id: int, *, school_id: int) -> DepartmentModel:
    department = (
        db.query(DepartmentModel)
        .filter(
            DepartmentModel.id == department_id,
            DepartmentModel.school_id == school_id,
        )
        .first()
    )
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    return department


def create_department(db: Session, payload: DepartmentCreate, *, school_id: int) -> DepartmentModel:
    department_name = payload.name.strip()

    existing = (
        db.query(DepartmentModel)
        .filter(
            DepartmentModel.school_id == school_id,
            func.lower(DepartmentModel.name) == func.lower(department_name),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department with this name already exists",
        )

    department = DepartmentModel(name=department_name, school_id=school_id)
    try:
        db.add(department)
        db.commit()
        db.refresh(department)
        return department
    except IntegrityError as exc:
        db.rollback()
        logger.error("Integrity error creating department", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department creation failed - possible duplicate name",
        ) from exc
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Unexpected error creating department", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create department",
        ) from exc


def update_department(
    db: Session,
    *,
    department_id: int,
    school_id: int,
    payload: DepartmentUpdate,
) -> DepartmentModel:
    department = get_department_or_404(db, department_id, school_id=school_id)

    if payload.name is None:
        return department

    department_name = payload.name.strip()
    existing = (
        db.query(DepartmentModel)
        .filter(
            DepartmentModel.school_id == school_id,
            func.lower(DepartmentModel.name) == func.lower(department_name),
            DepartmentModel.id != department_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department with this name already exists",
        )

    try:
        department.name = department_name
        db.commit()
        db.refresh(department)
        return department
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Error updating department", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update department",
        ) from exc


def delete_department(db: Session, department_id: int, *, school_id: int) -> None:
    department = get_department_or_404(db, department_id, school_id=school_id)

    try:
        db.delete(department)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.error("Integrity error deleting department", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete department - it may be referenced by programs",
        ) from exc
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Error deleting department", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete department",
        ) from exc
