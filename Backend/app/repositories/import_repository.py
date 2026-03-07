from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Sequence, Tuple

from sqlalchemy import delete, func, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.import_job import BulkImportError, BulkImportJob, EmailDeliveryLog
from app.models.role import Role
from app.models.user import StudentProfile, User, UserRole


class ImportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, job: BulkImportJob) -> BulkImportJob:
        self.db.add(job)
        self.db.flush()
        return job

    def get_job(self, job_id: str) -> BulkImportJob | None:
        return self.db.query(BulkImportJob).filter(BulkImportJob.id == job_id).first()

    def mark_processing(self, job_id: str) -> None:
        self.db.execute(
            update(BulkImportJob)
            .where(BulkImportJob.id == job_id)
            .values(status="processing", started_at=datetime.utcnow(), last_heartbeat=datetime.utcnow())
        )

    def update_progress(
        self,
        job_id: str,
        *,
        total_rows: int,
        processed_rows: int,
        success_count: int,
        failed_count: int,
        eta_seconds: int | None,
    ) -> None:
        self.db.execute(
            update(BulkImportJob)
            .where(BulkImportJob.id == job_id)
            .values(
                total_rows=total_rows,
                processed_rows=processed_rows,
                success_count=success_count,
                failed_count=failed_count,
                eta_seconds=eta_seconds,
                last_heartbeat=datetime.utcnow(),
            )
        )

    def mark_completed(self, job_id: str, failed_report_path: str | None = None) -> None:
        self.db.execute(
            update(BulkImportJob)
            .where(BulkImportJob.id == job_id)
            .values(
                status="completed",
                completed_at=datetime.utcnow(),
                failed_report_path=failed_report_path,
                eta_seconds=0,
                last_heartbeat=datetime.utcnow(),
            )
        )

    def mark_failed(self, job_id: str, error_summary: str) -> None:
        self.db.execute(
            update(BulkImportJob)
            .where(BulkImportJob.id == job_id)
            .values(
                status="failed",
                completed_at=datetime.utcnow(),
                error_summary=error_summary[:2000],
                last_heartbeat=datetime.utcnow(),
            )
        )

    def add_errors(self, job_id: str, errors: Sequence[dict]) -> None:
        if not errors:
            return
        values = [
            {
                "job_id": job_id,
                "row_number": item["row"],
                "error_message": item["error"],
                "row_data": item.get("row_data"),
            }
            for item in errors
        ]
        self.db.execute(pg_insert(BulkImportError), values)

    def fetch_errors(self, job_id: str, limit: int = 1000) -> List[BulkImportError]:
        return (
            self.db.query(BulkImportError)
            .filter(BulkImportError.job_id == job_id)
            .order_by(BulkImportError.row_number.asc(), BulkImportError.id.asc())
            .limit(max(1, min(limit, 10000)))
            .all()
        )

    def count_recent_jobs(self, created_by_user_id: int, window_seconds: int) -> int:
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        return (
            self.db.query(func.count(BulkImportJob.id))
            .filter(
                BulkImportJob.created_by_user_id == created_by_user_id,
                BulkImportJob.created_at >= cutoff,
            )
            .scalar()
            or 0
        )

    def get_student_role_id(self) -> int:
        role = self.db.query(Role).filter(Role.name == "student").first()
        if not role:
            raise RuntimeError("Role 'student' is missing")
        return role.id

    def lock_import_processing(self) -> None:
        # Global advisory lock to avoid concurrent import race conditions.
        self.db.execute(select(func.pg_advisory_lock(883_501_221)))

    def unlock_import_processing(self) -> None:
        self.db.execute(select(func.pg_advisory_unlock(883_501_221)))

    def existing_emails(self, emails: Iterable[str]) -> set[str]:
        email_list = list({email for email in emails if email})
        if not email_list:
            return set()
        rows = self.db.execute(select(User.email).where(User.email.in_(email_list))).scalars().all()
        return {email.lower() for email in rows}

    def existing_school_student_pairs(self, pairs: Iterable[Tuple[int, str]]) -> set[Tuple[int, str]]:
        pair_list = list({(int(school_id), student_id) for school_id, student_id in pairs if student_id})
        if not pair_list:
            return set()
        rows = self.db.execute(
            select(StudentProfile.school_id, StudentProfile.student_id).where(
                tuple_(StudentProfile.school_id, StudentProfile.student_id).in_(pair_list)
            )
        ).all()
        return {(int(school_id), student_id) for school_id, student_id in rows}

    def bulk_insert_students(self, rows: Sequence[dict], student_role_id: int) -> tuple[List[dict], List[dict]]:
        if not rows:
            return [], []

        existing_emails = self.existing_emails(row["email"] for row in rows)
        existing_pairs = self.existing_school_student_pairs(
            (row["school_id"], row["student_id"]) for row in rows
        )

        candidate_rows: List[dict] = []
        errors: List[dict] = []

        for row in rows:
            row_errors = []
            if row["email"] in existing_emails:
                row_errors.append("Email already exists")
            if (row["school_id"], row["student_id"]) in existing_pairs:
                row_errors.append("Duplicate Student_ID within School_ID")

            if row_errors:
                errors.append(
                    {
                        "row": row["row_number"],
                        "error": "; ".join(row_errors),
                        "row_data": row["raw_row_data"],
                    }
                )
            else:
                candidate_rows.append(row)

        if not candidate_rows:
            return [], errors

        user_values = [
            {
                "email": row["email"],
                "school_id": row["school_id"],
                "password_hash": row["password_hash"],
                "first_name": row["first_name"],
                "middle_name": row["middle_name"],
                "last_name": row["last_name"],
                "is_active": True,
                "must_change_password": True,
            }
            for row in candidate_rows
        ]

        inserted_user_rows = self.db.execute(
            pg_insert(User)
            .values(user_values)
            .on_conflict_do_nothing(index_elements=[User.email])
            .returning(User.id, User.email)
        ).all()

        inserted_user_map: Dict[str, int] = {email.lower(): user_id for user_id, email in inserted_user_rows}

        inserted_candidates: List[dict] = []
        skipped_candidates: List[dict] = []
        for row in candidate_rows:
            user_id = inserted_user_map.get(row["email"])
            if user_id is None:
                skipped_candidates.append(row)
            else:
                row["user_id"] = user_id
                inserted_candidates.append(row)

        for row in skipped_candidates:
            errors.append(
                {
                    "row": row["row_number"],
                    "error": "Email already exists",
                    "row_data": row["raw_row_data"],
                }
            )

        if not inserted_candidates:
            return [], errors

        self.db.execute(
            pg_insert(UserRole),
            [{"user_id": row["user_id"], "role_id": student_role_id} for row in inserted_candidates],
        )

        profile_values = [
            {
                "user_id": row["user_id"],
                "school_id": row["school_id"],
                "student_id": row["student_id"],
                "department_id": row["department_id"],
                "program_id": row["program_id"],
                "year_level": 1,
            }
            for row in inserted_candidates
        ]

        inserted_profiles = self.db.execute(
            pg_insert(StudentProfile)
            .values(profile_values)
            .on_conflict_do_nothing(index_elements=["school_id", "student_id"])
            .returning(StudentProfile.user_id)
        ).scalars().all()

        inserted_profile_user_ids = set(inserted_profiles)
        orphan_rows = [row for row in inserted_candidates if row["user_id"] not in inserted_profile_user_ids]

        if orphan_rows:
            orphan_user_ids = [row["user_id"] for row in orphan_rows]
            self.db.execute(delete(UserRole).where(UserRole.user_id.in_(orphan_user_ids)))
            self.db.execute(delete(User).where(User.id.in_(orphan_user_ids)))
            for row in orphan_rows:
                errors.append(
                    {
                        "row": row["row_number"],
                        "error": "Duplicate Student_ID within School_ID",
                        "row_data": row["raw_row_data"],
                    }
                )

        successful_rows = [row for row in inserted_candidates if row["user_id"] in inserted_profile_user_ids]
        return successful_rows, errors

    def log_email_delivery(
        self,
        *,
        job_id: str | None,
        user_id: int | None,
        email: str,
        status: str,
        error_message: str | None = None,
        retry_count: int = 0,
    ) -> None:
        self.db.add(
            EmailDeliveryLog(
                job_id=job_id,
                user_id=user_id,
                email=email,
                status=status,
                error_message=error_message,
                retry_count=retry_count,
            )
        )
