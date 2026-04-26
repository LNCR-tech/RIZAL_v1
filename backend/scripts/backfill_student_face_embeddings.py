"""Backfill the pgvector student face embedding index from registered profiles.

Run after applying the pgvector migration when a database already contains
registered student faces:

    python scripts/backfill_student_face_embeddings.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.user import StudentProfile  # noqa: E402
from app.services.attendance_face_scan import sync_student_face_embedding_index  # noqa: E402


def iter_registered_students(db: Session, *, batch_size: int = 500):
    offset = 0
    while True:
        students = (
            db.query(StudentProfile)
            .filter(
                StudentProfile.face_encoding.isnot(None),
                StudentProfile.is_face_registered.is_(True),
            )
            .order_by(StudentProfile.id.asc())
            .offset(offset)
            .limit(batch_size)
            .all()
        )
        if not students:
            break
        yield from students
        offset += batch_size


def main() -> int:
    batch_size = int(os.getenv("FACE_EMBEDDING_BACKFILL_BATCH_SIZE", "500"))
    processed = 0
    indexed = 0
    failed = 0

    db = SessionLocal()
    try:
        for student in iter_registered_students(db, batch_size=batch_size):
            processed += 1
            if sync_student_face_embedding_index(db, student):
                indexed += 1
                db.commit()
            else:
                failed += 1
            if processed % batch_size == 0:
                print(f"processed={processed} indexed={indexed} failed={failed}")

        print(f"done processed={processed} indexed={indexed} failed={failed}")
    finally:
        db.close()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
