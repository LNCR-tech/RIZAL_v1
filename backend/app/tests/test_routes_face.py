from __future__ import annotations

import base64
import time
from datetime import datetime, timedelta
from types import SimpleNamespace

import numpy as np
from fastapi import Depends, HTTPException
from sqlalchemy.orm import joinedload

from app.core.dependencies import get_db
from app.core.security import (
    get_current_admin_or_campus_admin,
    get_current_application_user,
    get_current_student_user,
)
from app.models.attendance import Attendance as AttendanceModel
from app.models.department import Department
from app.main import app
from app.models.event import Event, EventStatus
from app.models.face_recognition import UserFaceRecognitionProfile
from app.models.role import Role
from app.models.school import School
from app.models.user import StudentProfile, User, UserRole
from app.routers import face_recognition, security_center
from app.services.event_time_status import get_event_timezone
from app.services.face_recognition import LivenessResult


def _frame_payload() -> str:
    return "data:image/jpeg;base64," + base64.b64encode(b"route-face-frame").decode("ascii")


def _embedding(seed: int) -> np.ndarray:
    vector = np.zeros(512, dtype=np.float32)
    vector[seed % 512] = 0.8
    vector[(seed + 71) % 512] = 0.6
    return vector / np.linalg.norm(vector)


def _runtime_status(
    *,
    state: str = "ready",
    ready: bool = True,
    reason: str | None = None,
    mode: str = "mfa",
) -> dict[str, object]:
    effective_reason = reason or ("ready" if ready else "insightface_warming_up")
    return {
        "state": state,
        "ready": ready,
        "reason": effective_reason,
        "last_error": None,
        "provider_target": "CPUExecutionProvider",
        "mode": mode,
        "initialized_at": None,
        "warmup_started_at": None,
        "warmup_finished_at": None,
    }


def _create_school(test_db, *, code: str, name: str) -> School:
    school = School(
        name=name,
        school_name=name,
        school_code=code,
        address=f"{name} Address",
        active_status=True,
    )
    test_db.add(school)
    test_db.commit()
    test_db.refresh(school)
    return school


def _create_user_with_role(test_db, *, school: School, email: str, role_name: str) -> User:
    role = test_db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name)
        test_db.add(role)
        test_db.commit()
        test_db.refresh(role)

    user = User(
        email=email,
        school_id=school.id,
        first_name="Face",
        last_name="Tester",
        must_change_password=False,
    )
    user.set_password("password123")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    user_role = UserRole(user_id=user.id, role_id=role.id)
    test_db.add(user_role)
    test_db.commit()
    return user


def _add_role_to_user(test_db, *, user: User, role_name: str) -> None:
    role = test_db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name)
        test_db.add(role)
        test_db.commit()
        test_db.refresh(role)

    already_assigned = (
        test_db.query(UserRole)
        .filter(UserRole.user_id == user.id, UserRole.role_id == role.id)
        .first()
    )
    if already_assigned is not None:
        return

    test_db.add(UserRole(user_id=user.id, role_id=role.id))
    test_db.commit()


def _load_user_for_override(test_db, user_id: int) -> User:
    return (
        test_db.query(User)
        .options(
            joinedload(User.roles).joinedload(UserRole.role),
            joinedload(User.student_profile),
            joinedload(User.face_profile),
        )
        .filter(User.id == user_id)
        .first()
    )


def _create_student_profile(
    test_db,
    *,
    user: User,
    seed: int,
    canonical: bool = True,
    department_id: int | None = None,
    program_id: int | None = None,
) -> StudentProfile:
    profile = StudentProfile(
        user_id=user.id,
        school_id=user.school_id,
        student_id=f"STU-{seed:03d}",
        department_id=department_id,
        program_id=program_id,
        year_level=1,
        face_encoding=_embedding(seed).tobytes() if canonical else None,
        embedding_provider="arcface" if canonical else None,
        embedding_dtype="float32" if canonical else None,
        embedding_dimension=512 if canonical else None,
        embedding_normalized=True if canonical else True,
        is_face_registered=canonical,
        registration_complete=canonical,
    )
    test_db.add(profile)
    test_db.commit()
    test_db.refresh(profile)
    return profile


def _create_active_event(test_db, *, school: School) -> Event:
    now = datetime.now(get_event_timezone()).replace(tzinfo=None, microsecond=0)
    event = Event(
        school_id=school.id,
        name="Face Event",
        location="Main Hall",
        geo_latitude=8.1575,
        geo_longitude=123.8431,
        geo_radius_m=60,
        geo_required=True,
        geo_max_accuracy_m=25,
        start_datetime=now - timedelta(minutes=5),
        end_datetime=now + timedelta(minutes=30),
        status=EventStatus.ONGOING,
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    return event


def _create_department(test_db, *, school: School, name: str) -> Department:
    department = Department(
        school_id=school.id,
        name=name,
    )
    test_db.add(department)
    test_db.commit()
    test_db.refresh(department)
    return department


def test_student_registration_upload_stores_canonical_metadata(client, test_db, monkeypatch) -> None:
    school = _create_school(test_db, code="REG", name="Registration Campus")
    user = _create_user_with_role(
        test_db,
        school=school,
        email="student.register@example.com",
        role_name="student",
    )
    profile = _create_student_profile(test_db, user=user, seed=17, canonical=False)

    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_student_user,
        lambda db=Depends(get_db): _load_user_for_override(db, user.id),
    )
    monkeypatch.setattr(
        face_recognition.face_service,
        "extract_encoding_from_bytes",
        lambda *_args, **_kwargs: (_embedding(17), LivenessResult(label="Real", score=0.99)),
    )
    monkeypatch.setattr(
        face_recognition.face_service,
        "ensure_face_runtime_ready",
        lambda **_kwargs: _runtime_status(mode="single"),
    )

    response = client.post(
        "/api/face/register-upload",
        files={"file": ("face.jpg", b"image-bytes", "image/jpeg")},
    )

    test_db.refresh(profile)
    assert response.status_code == 200
    assert profile.face_encoding is not None
    assert profile.embedding_provider == "arcface"
    assert profile.embedding_dtype == "float32"
    assert profile.embedding_dimension == 512
    assert profile.embedding_normalized is True


def test_face_scan_with_recognition_records_student_attendance(client, test_db, monkeypatch) -> None:
    school = _create_school(test_db, code="SCAN", name="Scan Campus")
    user = _create_user_with_role(
        test_db,
        school=school,
        email="student.scan@example.com",
        role_name="student",
    )
    profile = _create_student_profile(test_db, user=user, seed=23, canonical=True)
    event = _create_active_event(test_db, school=school)

    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_application_user,
        lambda db=Depends(get_db): _load_user_for_override(db, user.id),
    )
    monkeypatch.setattr(
        face_recognition.face_service,
        "extract_encoding_from_bytes",
        lambda *_args, **_kwargs: (_embedding(23), LivenessResult(label="Real", score=0.98)),
    )
    monkeypatch.setattr(
        face_recognition.face_service,
        "ensure_face_runtime_ready",
        lambda **_kwargs: _runtime_status(mode="single"),
    )
    monkeypatch.setattr(face_recognition, "verify_event_geolocation_for_attendance", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(face_recognition, "find_attendance_geolocation_travel_risk", lambda *_args, **_kwargs: None)

    response = client.post(
        "/api/face/face-scan-with-recognition",
        json={
            "event_id": event.id,
            "image_base64": _frame_payload(),
            "latitude": 8.1575,
            "longitude": 123.8431,
            "accuracy_m": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["action"] == "time_in"
    test_db.refresh(profile)
    attendance = profile.attendances[0]
    assert attendance.event_id == event.id
    assert attendance.method == "face_scan"


def test_face_scan_with_recognition_rejects_student_outside_event_scope(
    client,
    test_db,
    monkeypatch,
) -> None:
    school = _create_school(test_db, code="SCOPE", name="Scope Campus")
    user = _create_user_with_role(
        test_db,
        school=school,
        email="student.scope@example.com",
        role_name="student",
    )
    _create_student_profile(test_db, user=user, seed=24, canonical=True)
    event = _create_active_event(test_db, school=school)
    out_of_scope_department = _create_department(
        test_db,
        school=school,
        name="Out of Scope Department",
    )
    event.departments = [out_of_scope_department]
    test_db.commit()
    test_db.refresh(event)

    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_application_user,
        lambda db=Depends(get_db): _load_user_for_override(db, user.id),
    )
    monkeypatch.setattr(
        face_recognition.face_service,
        "ensure_face_runtime_ready",
        lambda **_kwargs: _runtime_status(mode="single"),
    )

    response = client.post(
        "/api/face/face-scan-with-recognition",
        json={
            "event_id": event.id,
            "image_base64": _frame_payload(),
            "latitude": 8.1575,
            "longitude": 123.8431,
            "accuracy_m": 5,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "The signed-in student is outside this event scope."


def test_face_scan_with_recognition_rejects_non_student_operator_accounts(
    client,
    test_db,
    monkeypatch,
) -> None:
    school = _create_school(test_db, code="OPR", name="Operator Campus")
    user = _create_user_with_role(
        test_db,
        school=school,
        email="governance.operator@example.com",
        role_name="ssg",
    )
    _add_role_to_user(test_db, user=user, role_name="admin")
    event = _create_active_event(test_db, school=school)

    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_application_user,
        lambda db=Depends(get_db): _load_user_for_override(db, user.id),
    )

    response = client.post(
        "/api/face/face-scan-with-recognition",
        json={
            "event_id": event.id,
            "image_base64": _frame_payload(),
            "latitude": 8.1575,
            "longitude": 123.8431,
            "accuracy_m": 5,
        },
    )

    assert response.status_code == 403
    assert "Student self-scan access is required" in response.json()["detail"]


def test_face_scan_with_recognition_never_records_other_student_for_self_scan(
    client,
    test_db,
    monkeypatch,
) -> None:
    school = _create_school(test_db, code="LOCK", name="Account Lock Campus")
    account_owner = _create_user_with_role(
        test_db,
        school=school,
        email="owner.student@example.com",
        role_name="student",
    )
    _add_role_to_user(test_db, user=account_owner, role_name="ssg")
    owner_profile = _create_student_profile(test_db, user=account_owner, seed=61, canonical=True)

    friend_user = _create_user_with_role(
        test_db,
        school=school,
        email="friend.student@example.com",
        role_name="student",
    )
    friend_profile = _create_student_profile(test_db, user=friend_user, seed=77, canonical=True)

    event = _create_active_event(test_db, school=school)

    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_application_user,
        lambda db=Depends(get_db): _load_user_for_override(db, account_owner.id),
    )
    monkeypatch.setattr(
        face_recognition.face_service,
        "extract_encoding_from_bytes",
        lambda *_args, **_kwargs: (_embedding(77), LivenessResult(label="Real", score=0.98)),
    )
    monkeypatch.setattr(
        face_recognition.face_service,
        "ensure_face_runtime_ready",
        lambda **_kwargs: _runtime_status(mode="single"),
    )
    monkeypatch.setattr(face_recognition, "verify_event_geolocation_for_attendance", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(face_recognition, "find_attendance_geolocation_travel_risk", lambda *_args, **_kwargs: None)

    response = client.post(
        "/api/face/face-scan-with-recognition",
        json={
            "event_id": event.id,
            "image_base64": _frame_payload(),
            "latitude": 8.1575,
            "longitude": 123.8431,
            "accuracy_m": 5,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Face not match."
    owner_attendance_count = (
        test_db.query(AttendanceModel)
        .filter(
            AttendanceModel.event_id == event.id,
            AttendanceModel.student_id == owner_profile.id,
        )
        .count()
    )
    friend_attendance_count = (
        test_db.query(AttendanceModel)
        .filter(
            AttendanceModel.event_id == event.id,
            AttendanceModel.student_id == friend_profile.id,
        )
        .count()
    )
    assert owner_attendance_count == 0
    assert friend_attendance_count == 0


def test_face_scan_with_recognition_rejects_multiple_faces_with_face_not_found(
    client,
    test_db,
    monkeypatch,
) -> None:
    school = _create_school(test_db, code="MULTI", name="Multi Face Campus")
    user = _create_user_with_role(
        test_db,
        school=school,
        email="student.multiface@example.com",
        role_name="student",
    )
    profile = _create_student_profile(test_db, user=user, seed=31, canonical=True)
    event = _create_active_event(test_db, school=school)

    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_application_user,
        lambda db=Depends(get_db): _load_user_for_override(db, user.id),
    )
    monkeypatch.setattr(
        face_recognition.face_service,
        "ensure_face_runtime_ready",
        lambda **_kwargs: _runtime_status(mode="single"),
    )
    monkeypatch.setattr(
        face_recognition.face_service,
        "extract_encoding_from_bytes",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            HTTPException(status_code=400, detail="Image must contain exactly one face.")
        ),
    )

    response = client.post(
        "/api/face/face-scan-with-recognition",
        json={
            "event_id": event.id,
            "image_base64": _frame_payload(),
            "latitude": 8.1575,
            "longitude": 123.8431,
            "accuracy_m": 5,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Face not found."
    attendance_count = (
        test_db.query(AttendanceModel)
        .filter(
            AttendanceModel.event_id == event.id,
            AttendanceModel.student_id == profile.id,
        )
        .count()
    )
    assert attendance_count == 0


def test_admin_face_verify_route_accepts_canonical_reference(client, test_db, monkeypatch) -> None:
    school = _create_school(test_db, code="MFA", name="MFA Campus")
    admin_user = _create_user_with_role(
        test_db,
        school=school,
        email="admin.face@example.com",
        role_name="admin",
    )
    test_db.add(
        UserFaceRecognitionProfile(
            user_id=admin_user.id,
            face_encoding=_embedding(41).tobytes(),
            provider="arcface",
            reference_image_sha256="abc123",
        )
    )
    test_db.commit()

    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_admin_or_campus_admin,
        lambda db=Depends(get_db): _load_user_for_override(db, admin_user.id),
    )
    monkeypatch.setattr(
        security_center.face_service,
        "extract_encoding_from_bytes",
        lambda *_args, **_kwargs: (_embedding(41), LivenessResult(label="Real", score=0.99)),
    )
    monkeypatch.setattr(
        security_center.face_service,
        "ensure_face_runtime_ready",
        lambda **_kwargs: _runtime_status(mode="mfa"),
    )
    monkeypatch.setattr(
        security_center,
        "decode_token_to_token_data",
        lambda _token: SimpleNamespace(face_pending=False),
    )

    response = client.post(
        "/api/auth/security/face-verify",
        json={"image_base64": _frame_payload()},
        headers={"Authorization": "Bearer route-test-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is True
    assert body["distance"] == 0.0


def test_admin_face_verify_route_rejects_multiple_faces_with_face_not_found(
    client,
    test_db,
    monkeypatch,
) -> None:
    school = _create_school(test_db, code="MFV", name="Multi Verify Campus")
    admin_user = _create_user_with_role(
        test_db,
        school=school,
        email="admin.multiverify@example.com",
        role_name="admin",
    )
    test_db.add(
        UserFaceRecognitionProfile(
            user_id=admin_user.id,
            face_encoding=_embedding(51).tobytes(),
            provider="arcface",
            reference_image_sha256="mfv123",
        )
    )
    test_db.commit()

    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_admin_or_campus_admin,
        lambda db=Depends(get_db): _load_user_for_override(db, admin_user.id),
    )
    monkeypatch.setattr(
        security_center.face_service,
        "ensure_face_runtime_ready",
        lambda **_kwargs: _runtime_status(mode="mfa"),
    )
    monkeypatch.setattr(
        security_center.face_service,
        "extract_encoding_from_bytes",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            HTTPException(status_code=400, detail="Image must contain exactly one face.")
        ),
    )

    response = client.post(
        "/api/auth/security/face-verify",
        json={"image_base64": _frame_payload()},
        headers={"Authorization": "Bearer route-test-token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Face not found."


def test_face_status_separates_face_runtime_and_anti_spoof_readiness(
    client,
    test_db,
    monkeypatch,
) -> None:
    school = _create_school(test_db, code="STS", name="Status Campus")
    admin_user = _create_user_with_role(
        test_db,
        school=school,
        email="admin.status@example.com",
        role_name="admin",
    )

    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_admin_or_campus_admin,
        lambda db=Depends(get_db): _load_user_for_override(db, admin_user.id),
    )
    monkeypatch.setattr(
        security_center.face_service,
        "face_runtime_status",
        lambda mode="mfa": _runtime_status(
            state="failed",
            ready=False,
            reason="insightface_unavailable",
            mode=mode,
        ),
    )
    monkeypatch.setattr(
        security_center.face_service,
        "anti_spoof_status",
        lambda: (True, None),
    )

    response = client.get(
        "/api/auth/security/face-status",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["face_runtime_ready"] is False
    assert body["face_runtime_reason"] == "insightface_unavailable"
    assert body["face_runtime_state"] == "failed"
    assert body["anti_spoof_ready"] is True
    assert body["anti_spoof_reason"] is None


def test_face_status_times_out_runtime_probe_without_hanging_route(
    client,
    test_db,
    monkeypatch,
) -> None:
    school = _create_school(test_db, code="STT", name="Status Timeout Campus")
    admin_user = _create_user_with_role(
        test_db,
        school=school,
        email="admin.timeout@example.com",
        role_name="admin",
    )

    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_admin_or_campus_admin,
        lambda db=Depends(get_db): _load_user_for_override(db, admin_user.id),
    )
    monkeypatch.setattr(security_center, "FACE_STATUS_TIMEOUT_SECONDS", 0.05)

    def _slow_face_runtime(mode: str = "mfa") -> dict[str, object]:
        time.sleep(0.2)
        return _runtime_status(mode=mode)

    monkeypatch.setattr(
        security_center.face_service,
        "face_runtime_status",
        _slow_face_runtime,
    )
    monkeypatch.setattr(
        security_center.face_service,
        "anti_spoof_status",
        lambda: (True, None),
    )

    response = client.get("/api/auth/security/face-status")

    assert response.status_code == 200
    body = response.json()
    assert body["face_runtime_ready"] is False
    assert body["face_runtime_reason"] == "insightface_warming_up"
    assert body["face_runtime_state"] == "initializing"
    assert body["anti_spoof_ready"] is True
    assert body["anti_spoof_reason"] is None
