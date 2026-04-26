"""Use: Shares student face candidate scoping and public attendance persistence helpers.
Where to use: Use this from attendance-related routers that need event-scoped face matching.
Role: Service layer. It keeps scope and persistence rules out of router files.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

import numpy as np
from sqlalchemy import bindparam, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event as EventModel
from app.models.user import StudentProfile, User as UserModel
from app.schemas.event import EventLocationVerificationResponse
from app.services.attendance_status import finalize_completed_attendance_status
from app.services.event_attendance_service import get_event_participant_student_ids
from app.services.event_time_status import get_attendance_decision, get_event_status, get_sign_out_decision
from app.services.face_recognition import FaceCandidate, FaceMatchResult, LivenessResult
from app.services.notification_center_service import send_attendance_notification

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScopedStudentFaceCandidate:
    student: StudentProfile
    candidate: FaceCandidate


@dataclass(frozen=True)
class PublicAttendancePersistenceResult:
    action: str
    message: str
    reason_code: str | None = None
    attendance_id: int | None = None
    time_in: datetime | None = None
    time_out: datetime | None = None
    duration_minutes: int | None = None


@dataclass(frozen=True)
class PgvectorFaceSearchRow:
    student_profile_id: int
    distance: float
    confidence: float
    threshold: float


def student_display_name(student: StudentProfile) -> str:
    """Build a friendly student name for face-match results and logs."""
    user = student.user
    if user is None:
        return student.student_id or f"Student {student.id}"
    full_name = " ".join(
        part.strip()
        for part in [user.first_name or "", user.middle_name or "", user.last_name or ""]
        if part and part.strip()
    ).strip()
    return full_name or student.student_id or f"Student {student.id}"


def _build_scoped_candidates(students: list[StudentProfile]) -> list[ScopedStudentFaceCandidate]:
    """Convert student rows into matchable face candidates for recognition."""
    candidates: list[ScopedStudentFaceCandidate] = []
    for student in students:
        if not student.face_encoding:
            continue
        candidates.append(
            ScopedStudentFaceCandidate(
                student=student,
                candidate=FaceCandidate(
                    identifier=student.id,
                    label=student_display_name(student),
                    encoding_bytes=bytes(student.face_encoding),
                    embedding_provider=student.embedding_provider,
                    embedding_dtype=student.embedding_dtype,
                    embedding_dimension=student.embedding_dimension,
                    embedding_normalized=student.embedding_normalized,
                ),
            )
        )
    return candidates


def _session_uses_postgresql(db: Session) -> bool:
    bind = db.get_bind()
    return bool(bind is not None and bind.dialect.name == "postgresql")


def _pgvector_face_index_ready(db: Session) -> bool:
    """Return True when the optional pgvector attendance index is available."""
    if not _session_uses_postgresql(db):
        return False
    cached = db.info.get("pgvector_face_index_ready")
    if cached is not None:
        return bool(cached)

    try:
        row = db.execute(
            text(
                """
                SELECT
                    to_regtype('vector') IS NOT NULL AS has_vector,
                    to_regclass('public.student_face_embeddings') IS NOT NULL AS has_table
                """
            )
        ).mappings().first()
    except SQLAlchemyError:
        logger.exception("Unable to inspect pgvector face index availability.")
        db.info["pgvector_face_index_ready"] = False
        return False

    ready = bool(row and row["has_vector"] and row["has_table"])
    db.info["pgvector_face_index_ready"] = ready
    return ready


def _pgvector_school_index_complete(db: Session, school_id: int) -> bool:
    """Return True when active vector rows cover all registered faces in a school."""
    cache_key = f"pgvector_school_index_complete:{school_id}"
    cached = db.info.get(cache_key)
    if cached is not None:
        return bool(cached)
    if not _pgvector_face_index_ready(db):
        db.info[cache_key] = False
        return False

    try:
        row = db.execute(
            text(
                """
                SELECT
                    (
                        SELECT count(*)
                        FROM student_profiles AS sp
                        WHERE sp.school_id = :school_id
                          AND sp.face_encoding IS NOT NULL
                          AND sp.is_face_registered IS TRUE
                          AND COALESCE(sp.embedding_provider, 'arcface') IN ('arcface', 'buffalo_l')
                          AND COALESCE(sp.embedding_dtype, 'float32') = 'float32'
                          AND COALESCE(sp.embedding_dimension, 512) = 512
                          AND COALESCE(sp.embedding_normalized, TRUE) IS TRUE
                    ) AS registered_count,
                    (
                        SELECT count(*)
                        FROM student_face_embeddings AS sfe
                        WHERE sfe.school_id = :school_id
                          AND sfe.is_active IS TRUE
                          AND sfe.embedding IS NOT NULL
                          AND sfe.provider IN ('arcface', 'buffalo_l')
                          AND sfe.embedding_dtype = 'float32'
                          AND sfe.embedding_dimension = 512
                          AND sfe.embedding_normalized IS TRUE
                    ) AS indexed_count
                """
            ),
            {"school_id": school_id},
        ).mappings().first()
    except SQLAlchemyError:
        logger.exception("Unable to inspect pgvector face index completeness.")
        db.info[cache_key] = False
        return False

    complete = bool(
        row
        and int(row["registered_count"] or 0) > 0
        and int(row["registered_count"] or 0) == int(row["indexed_count"] or 0)
    )
    db.info[cache_key] = complete
    return complete


def _embedding_to_vector_literal(embedding) -> str:
    """Serialize one normalized embedding as a pgvector text literal."""
    vector = np.asarray(embedding, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(vector))
    if norm <= 0:
        raise ValueError("Embedding norm must be greater than zero.")
    normalized = vector / norm
    return "[" + ",".join(f"{float(value):.8g}" for value in normalized) + "]"


def sync_student_face_embedding_index(db: Session, student: StudentProfile) -> bool:
    """Upsert one registered student face into the optional pgvector index table."""
    if not _pgvector_face_index_ready(db):
        return False
    db.info.pop(f"pgvector_school_index_complete:{student.school_id}", None)

    if not student.face_encoding or not student.is_face_registered:
        try:
            db.execute(
                text(
                    """
                    UPDATE student_face_embeddings
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE student_profile_id = :student_profile_id
                    """
                ),
                {"student_profile_id": student.id},
            )
            return True
        except SQLAlchemyError:
            logger.exception("Failed to deactivate student face embedding index row.")
            db.rollback()
            return False

    dtype_name = (student.embedding_dtype or "float32").strip().lower()
    dimension = int(student.embedding_dimension or 0)
    if dtype_name != "float32" or dimension <= 0:
        return False

    try:
        vector = np.frombuffer(bytes(student.face_encoding), dtype=np.dtype(dtype_name))
        if vector.size != dimension:
            return False
        vector_literal = _embedding_to_vector_literal(vector)
        db.execute(
            text(
                """
                INSERT INTO student_face_embeddings (
                    school_id,
                    student_profile_id,
                    department_id,
                    program_id,
                    embedding,
                    provider,
                    embedding_dtype,
                    embedding_dimension,
                    embedding_normalized,
                    is_active,
                    updated_at
                )
                VALUES (
                    :school_id,
                    :student_profile_id,
                    :department_id,
                    :program_id,
                    CAST(:embedding AS vector),
                    :provider,
                    :embedding_dtype,
                    :embedding_dimension,
                    :embedding_normalized,
                    TRUE,
                    NOW()
                )
                ON CONFLICT (student_profile_id) DO UPDATE SET
                    school_id = EXCLUDED.school_id,
                    department_id = EXCLUDED.department_id,
                    program_id = EXCLUDED.program_id,
                    embedding = EXCLUDED.embedding,
                    provider = EXCLUDED.provider,
                    embedding_dtype = EXCLUDED.embedding_dtype,
                    embedding_dimension = EXCLUDED.embedding_dimension,
                    embedding_normalized = EXCLUDED.embedding_normalized,
                    is_active = TRUE,
                    updated_at = NOW()
                """
            ),
            {
                "school_id": student.school_id,
                "student_profile_id": student.id,
                "department_id": student.department_id,
                "program_id": student.program_id,
                "embedding": vector_literal,
                "provider": student.embedding_provider or "arcface",
                "embedding_dtype": dtype_name,
                "embedding_dimension": dimension,
                "embedding_normalized": bool(student.embedding_normalized),
            },
        )
        return True
    except (SQLAlchemyError, ValueError):
        logger.exception(
            "Failed to sync student face embedding index row for student_profile_id=%s.",
            student.id,
        )
        db.rollback()
        return False


def get_registered_face_candidates_for_school(
    db: Session,
    school_id: int,
) -> list[ScopedStudentFaceCandidate]:
    """Load every registered face candidate that belongs to one school."""
    students = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.user))
        .join(UserModel, StudentProfile.user_id == UserModel.id)
        .filter(
            UserModel.school_id == school_id,
            StudentProfile.face_encoding.isnot(None),
            StudentProfile.is_face_registered.is_(True),
        )
        .all()
    )
    return _build_scoped_candidates(students)


def _event_scope_ids(event: EventModel) -> tuple[list[int], list[int]]:
    program_ids = [program.id for program in event.programs]
    department_ids = [department.id for department in event.departments]
    return program_ids, department_ids


def _search_pgvector_face_index(
    db: Session,
    *,
    face_service,
    encoding,
    school_id: int,
    program_ids: list[int] | None = None,
    department_ids: list[int] | None = None,
    threshold: float | None = None,
    mode: str = "group",
) -> PgvectorFaceSearchRow | None:
    if not _pgvector_face_index_ready(db):
        return None

    effective_threshold = float(
        threshold if threshold is not None else face_service.default_threshold_for_mode(mode)
    )
    try:
        vector_literal = _embedding_to_vector_literal(encoding)
    except ValueError:
        return None

    where_clauses = [
        "sfe.school_id = :school_id",
        "sfe.is_active IS TRUE",
        "sfe.embedding IS NOT NULL",
        "sfe.embedding_dtype = :embedding_dtype",
        "sfe.embedding_dimension = :embedding_dimension",
        "sfe.embedding_normalized IS TRUE",
        "sfe.provider IN ('arcface', 'buffalo_l')",
    ]
    params: dict[str, object] = {
        "school_id": school_id,
        "embedding": vector_literal,
        "embedding_dtype": face_service.settings.face_embedding_dtype,
        "embedding_dimension": face_service.settings.face_embedding_dim,
    }
    bind_params = []

    if program_ids:
        where_clauses.append("sfe.program_id IN :program_ids")
        params["program_ids"] = program_ids
        bind_params.append(bindparam("program_ids", expanding=True))
    if department_ids:
        where_clauses.append("sfe.department_id IN :department_ids")
        params["department_ids"] = department_ids
        bind_params.append(bindparam("department_ids", expanding=True))

    distance_expression = "sfe.embedding <=> CAST(:embedding AS vector)"
    statement = text(
        f"""
        SELECT
            sfe.student_profile_id,
            ({distance_expression}) AS distance
        FROM student_face_embeddings AS sfe
        WHERE {" AND ".join(where_clauses)}
        ORDER BY {distance_expression}, sfe.student_profile_id ASC
        LIMIT 1
        """
    )
    if bind_params:
        statement = statement.bindparams(*bind_params)

    try:
        row = db.execute(statement, params).mappings().first()
    except SQLAlchemyError:
        logger.exception("pgvector face search failed; falling back to ORM candidate matching.")
        return None

    if row is None:
        return None

    distance = float(row["distance"])
    return PgvectorFaceSearchRow(
        student_profile_id=int(row["student_profile_id"]),
        distance=distance,
        confidence=float(max(-1.0, min(1.0, 1.0 - distance))),
        threshold=effective_threshold,
    )


def _load_student_for_face_search_row(db: Session, row: PgvectorFaceSearchRow) -> StudentProfile | None:
    return (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.user))
        .filter(StudentProfile.id == row.student_profile_id)
        .first()
    )


def _face_match_from_pgvector_row(
    row: PgvectorFaceSearchRow | None,
    *,
    student: StudentProfile | None = None,
    default_threshold: float = 0.0,
) -> FaceMatchResult:
    if row is None:
        return FaceMatchResult(
            matched=False,
            threshold=float(default_threshold),
            distance=float("inf"),
            confidence=0.0,
            candidate=None,
        )

    candidate = None
    if student is not None:
        candidate = FaceCandidate(
            identifier=student.id,
            label=student_display_name(student),
            encoding_bytes=bytes(student.face_encoding or b""),
            embedding_provider=student.embedding_provider,
            embedding_dtype=student.embedding_dtype,
            embedding_dimension=student.embedding_dimension,
            embedding_normalized=student.embedding_normalized,
        )
    return FaceMatchResult(
        matched=row.distance <= row.threshold,
        threshold=row.threshold,
        distance=row.distance,
        confidence=row.confidence,
        candidate=candidate,
    )


def resolve_face_match_scope_with_pgvector(
    db: Session,
    *,
    face_service,
    encoding,
    event: EventModel,
    threshold: float | None = None,
    mode: str = "group",
) -> tuple[str, StudentProfile | None, FaceMatchResult] | None:
    """Resolve a face match through pgvector without loading every embedding."""
    if not _pgvector_school_index_complete(db, event.school_id):
        return None

    program_ids, department_ids = _event_scope_ids(event)
    event_row = _search_pgvector_face_index(
        db,
        face_service=face_service,
        encoding=encoding,
        school_id=event.school_id,
        program_ids=program_ids,
        department_ids=department_ids,
        threshold=threshold,
        mode=mode,
    )
    if event_row is not None and event_row.distance <= event_row.threshold:
        student = _load_student_for_face_search_row(db, event_row)
        if student is not None:
            return "in_scope", student, _face_match_from_pgvector_row(event_row, student=student)

    default_threshold = float(
        threshold if threshold is not None else face_service.default_threshold_for_mode(mode)
    )
    event_match = _face_match_from_pgvector_row(event_row, default_threshold=default_threshold)
    if not program_ids and not department_ids:
        return "no_match", None, event_match

    school_row = _search_pgvector_face_index(
        db,
        face_service=face_service,
        encoding=encoding,
        school_id=event.school_id,
        threshold=threshold,
        mode=mode,
    )
    if school_row is not None and school_row.distance <= school_row.threshold:
        student = _load_student_for_face_search_row(db, school_row)
        if student is not None:
            return "out_of_scope", student, _face_match_from_pgvector_row(school_row, student=student)

    return "no_match", None, _face_match_from_pgvector_row(
        school_row or event_row,
        default_threshold=default_threshold,
    )


def resolve_school_face_match_with_pgvector(
    db: Session,
    *,
    face_service,
    encoding,
    school_id: int,
    threshold: float | None = None,
    mode: str = "single",
) -> tuple[StudentProfile | None, FaceMatchResult] | None:
    """Resolve the best school-wide face match through pgvector when available."""
    if not _pgvector_school_index_complete(db, school_id):
        return None

    default_threshold = float(
        threshold if threshold is not None else face_service.default_threshold_for_mode(mode)
    )
    row = _search_pgvector_face_index(
        db,
        face_service=face_service,
        encoding=encoding,
        school_id=school_id,
        threshold=threshold,
        mode=mode,
    )
    if row is None or row.distance > row.threshold:
        return None, _face_match_from_pgvector_row(row, default_threshold=default_threshold)

    student = _load_student_for_face_search_row(db, row)
    if student is None:
        return None, _face_match_from_pgvector_row(row, default_threshold=default_threshold)
    return student, _face_match_from_pgvector_row(row, student=student)


def get_registered_face_candidates_for_event(
    db: Session,
    event: EventModel,
) -> list[ScopedStudentFaceCandidate]:
    """Load only the registered face candidates that are valid for one event."""
    participant_ids = get_event_participant_student_ids(db, event)
    if not participant_ids:
        return []

    students = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.user))
        .filter(
            StudentProfile.id.in_(participant_ids),
            StudentProfile.face_encoding.isnot(None),
            StudentProfile.is_face_registered.is_(True),
        )
        .all()
    )
    return _build_scoped_candidates(students)


def resolve_face_match_scope(
    *,
    face_service,
    encoding,
    event_candidates: list[ScopedStudentFaceCandidate],
    school_candidates: list[ScopedStudentFaceCandidate],
    threshold: float | None = None,
    mode: str = "group",
) -> tuple[str, StudentProfile | None, FaceMatchResult]:
    """Tell whether a matched face is inside event scope, outside it, or unmatched."""
    empty_match = FaceMatchResult(
        matched=False,
        threshold=float(
            threshold if threshold is not None else face_service.default_threshold_for_mode(mode)
        ),
        distance=float("inf"),
        confidence=0.0,
        candidate=None,
    )

    if event_candidates:
        event_match = face_service.find_best_match(
            encoding,
            [candidate.candidate for candidate in event_candidates],
            threshold=threshold,
            mode=mode,
        )
        if event_match.matched and event_match.candidate is not None:
            event_lookup = {
                candidate.candidate.identifier: candidate.student
                for candidate in event_candidates
            }
            return "in_scope", event_lookup.get(event_match.candidate.identifier), event_match
    else:
        event_match = empty_match

    if school_candidates:
        school_match = face_service.find_best_match(
            encoding,
            [candidate.candidate for candidate in school_candidates],
            threshold=threshold,
            mode=mode,
        )
        if school_match.matched and school_match.candidate is not None:
            school_lookup = {
                candidate.candidate.identifier: candidate.student
                for candidate in school_candidates
            }
            return "out_of_scope", school_lookup.get(school_match.candidate.identifier), school_match
        return "no_match", None, school_match

    return "no_match", None, event_match


def resolve_public_attendance_phase(event: EventModel) -> str | None:
    """Map the current event time window into the public face-scan phase."""
    time_status = get_event_status(
        start_time=event.start_datetime,
        end_time=event.end_datetime,
        early_check_in_minutes=getattr(event, "early_check_in_minutes", 0),
        late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
        sign_out_grace_minutes=getattr(event, "sign_out_grace_minutes", 0),
        sign_out_open_delay_minutes=getattr(event, "sign_out_open_delay_minutes", 0),
        sign_out_override_until=getattr(event, "sign_out_override_until", None),
        present_until_override_at=getattr(event, "present_until_override_at", None),
        late_until_override_at=getattr(event, "late_until_override_at", None),
    )
    if time_status.event_status in {"early_check_in", "late_check_in", "absent_check_in"}:
        return "sign_in"
    if time_status.event_status == "sign_out_open":
        return "sign_out"
    return None


def persist_public_attendance_scan(
    db: Session,
    *,
    event: EventModel,
    student: StudentProfile,
    phase: str,
    scanned_at: datetime,
    geo_response: EventLocationVerificationResponse | None,
    latitude: float | None,
    longitude: float | None,
    accuracy_m: float | None,
    liveness: LivenessResult | None = None,
) -> PublicAttendancePersistenceResult:
    """Create or complete attendance after a successful public face scan."""
    active_attendance = (
        db.query(AttendanceModel)
        .filter(
            AttendanceModel.student_id == student.id,
            AttendanceModel.event_id == event.id,
            AttendanceModel.time_out.is_(None),
        )
        .order_by(AttendanceModel.time_in.desc(), AttendanceModel.id.desc())
        .first()
    )
    latest_attendance = (
        db.query(AttendanceModel)
        .filter(
            AttendanceModel.student_id == student.id,
            AttendanceModel.event_id == event.id,
        )
        .order_by(AttendanceModel.time_in.desc(), AttendanceModel.id.desc())
        .first()
    )

    if phase == "sign_in":
        if active_attendance is not None:
            return PublicAttendancePersistenceResult(
                action="already_signed_in",
                reason_code="attendance_already_in_progress",
                attendance_id=active_attendance.id,
                time_in=active_attendance.time_in,
                message="Attendance is already active for this student in this event.",
            )
        if latest_attendance is not None and latest_attendance.time_out is not None:
            return PublicAttendancePersistenceResult(
                action="already_signed_out",
                reason_code="attendance_already_completed",
                attendance_id=latest_attendance.id,
                time_in=latest_attendance.time_in,
                time_out=latest_attendance.time_out,
                duration_minutes=(
                    int(max(0, (latest_attendance.time_out - latest_attendance.time_in).total_seconds() / 60))
                    if latest_attendance.time_in and latest_attendance.time_out
                    else None
                ),
                message="Attendance has already been completed for this student and event.",
            )

        attendance_decision = get_attendance_decision(
            start_time=event.start_datetime,
            end_time=event.end_datetime,
            early_check_in_minutes=getattr(event, "early_check_in_minutes", 0),
            late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
            sign_out_grace_minutes=getattr(event, "sign_out_grace_minutes", 0),
            sign_out_open_delay_minutes=getattr(event, "sign_out_open_delay_minutes", 0),
            sign_out_override_until=getattr(event, "sign_out_override_until", None),
            present_until_override_at=getattr(event, "present_until_override_at", None),
            late_until_override_at=getattr(event, "late_until_override_at", None),
        )
        if not attendance_decision.attendance_allowed:
            return PublicAttendancePersistenceResult(
                action="rejected",
                reason_code=attendance_decision.reason_code or "attendance_not_allowed",
                message=attendance_decision.message,
            )

        attendance = AttendanceModel(
            student_id=student.id,
            event_id=event.id,
            time_in=scanned_at,
            method="face_scan",
            status=attendance_decision.attendance_status or "absent",
            check_in_status=attendance_decision.attendance_status,
            check_out_status=None,
            verified_by=None,
            notes="Pending sign-out.",
            geo_distance_m=geo_response.distance_m if geo_response else None,
            geo_effective_distance_m=geo_response.effective_distance_m if geo_response else None,
            geo_latitude=latitude,
            geo_longitude=longitude,
            geo_accuracy_m=accuracy_m,
            liveness_label=str(liveness.label) if liveness is not None else None,
            liveness_score=float(liveness.score) if liveness is not None else None,
        )
        db.add(attendance)
        db.flush()
        if student.user is not None:
            notification_category = (
                "late_attendance"
                if attendance_decision.attendance_status == "late"
                else "attendance_sign_in"
            )
            send_attendance_notification(
                db,
                user=student.user,
                school_id=event.school_id,
                category=notification_category,
                subject=(
                    f"Late attendance recorded for {event.name}"
                    if notification_category == "late_attendance"
                    else f"Sign-in recorded for {event.name}"
                ),
                message=(
                    f"Your sign-in for {event.name} was recorded and marked {attendance_decision.attendance_status}."
                    " Complete sign-out during the allowed window to validate attendance."
                ),
                metadata_json={
                    "event_id": event.id,
                    "attendance_id": attendance.id,
                    "action": "sign_in",
                    "source": "public_attendance",
                    "display_status": attendance_decision.attendance_status,
                },
            )
        db.commit()
        db.refresh(attendance)
        return PublicAttendancePersistenceResult(
            action="time_in",
            attendance_id=attendance.id,
            time_in=attendance.time_in,
            message="Check-in recorded successfully.",
        )

    if active_attendance is None:
        if latest_attendance is not None and latest_attendance.time_out is not None:
            return PublicAttendancePersistenceResult(
                action="already_signed_out",
                reason_code="attendance_already_completed",
                attendance_id=latest_attendance.id,
                time_in=latest_attendance.time_in,
                time_out=latest_attendance.time_out,
                duration_minutes=(
                    int(max(0, (latest_attendance.time_out - latest_attendance.time_in).total_seconds() / 60))
                    if latest_attendance.time_in and latest_attendance.time_out
                    else None
                ),
                message="Attendance has already been completed for this student and event.",
            )
        return PublicAttendancePersistenceResult(
            action="rejected",
            reason_code="no_active_attendance_for_sign_out",
            message="This student does not have an active sign-in for this event.",
        )

    sign_out_decision = get_sign_out_decision(
        start_time=event.start_datetime,
        end_time=event.end_datetime,
        early_check_in_minutes=getattr(event, "early_check_in_minutes", 0),
        late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
        sign_out_grace_minutes=getattr(event, "sign_out_grace_minutes", 0),
        sign_out_open_delay_minutes=getattr(event, "sign_out_open_delay_minutes", 0),
        sign_out_override_until=getattr(event, "sign_out_override_until", None),
        present_until_override_at=getattr(event, "present_until_override_at", None),
        late_until_override_at=getattr(event, "late_until_override_at", None),
    )
    if not sign_out_decision.attendance_allowed:
        return PublicAttendancePersistenceResult(
            action="rejected",
            reason_code=sign_out_decision.reason_code or "attendance_not_allowed",
            message=sign_out_decision.message,
        )

    active_attendance.time_out = scanned_at
    active_attendance.check_out_status = "present"
    finalized_status, finalized_note = finalize_completed_attendance_status(
        check_in_status=active_attendance.check_in_status or active_attendance.status,
        check_out_status=active_attendance.check_out_status,
    )
    active_attendance.status = finalized_status
    active_attendance.notes = finalized_note
    if student.user is not None:
        send_attendance_notification(
            db,
            user=student.user,
            school_id=event.school_id,
            category="attendance_sign_out",
            subject=f"Sign-out recorded for {event.name}",
            message=(
                f"Your sign-out for {event.name} was recorded successfully."
                if finalized_status in {"present", "late"}
                else f"Your sign-out for {event.name} was recorded, but the attendance is not valid."
            ),
            metadata_json={
                "event_id": event.id,
                "attendance_id": active_attendance.id,
                "action": "sign_out",
                "source": "public_attendance",
                "display_status": finalized_status,
            },
        )
    db.commit()
    db.refresh(active_attendance)

    return PublicAttendancePersistenceResult(
        action="time_out",
        attendance_id=active_attendance.id,
        time_in=active_attendance.time_in,
        time_out=active_attendance.time_out,
        duration_minutes=int(
            max(0, (active_attendance.time_out - active_attendance.time_in).total_seconds() / 60)
        ),
        message="Check-out recorded successfully.",
    )


def build_outcome_liveness_payload(result: LivenessResult | None) -> dict[str, object] | None:
    """Convert optional liveness output into a response-safe dictionary."""
    if result is None:
        return None
    return result.to_dict()
