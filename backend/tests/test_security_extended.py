def test_revoke_other_sessions(client, student_headers):
    r = client.post("/api/auth/security/sessions/revoke-others", headers=student_headers)
    assert r.status_code in (200, 204)


def test_login_history(client, campus_admin_headers):
    r = client.get("/api/auth/security/login-history", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_login_history_requires_auth(client):
    r = client.get("/api/auth/security/login-history")
    assert r.status_code == 401


def test_face_reference_requires_auth(client):
    r = client.post("/api/auth/security/face-reference", json={"image_base64": "fake"})
    assert r.status_code == 401


def test_delete_face_reference_requires_auth(client):
    r = client.delete("/api/auth/security/face-reference")
    assert r.status_code == 401


def test_face_verify_requires_auth(client):
    r = client.post("/api/auth/security/face-verify", json={"image_base64": "fake"})
    assert r.status_code == 401


def test_revoke_session(client, student_headers, db_session):
    from jose import jwt
    import uuid
    from app.core.security import SECRET_KEY, ALGORITHM
    from app.models.platform_features import UserSession
    from app.models.user import User
    from app.core.timezones import utc_now
    from datetime import timedelta
    student = db_session.query(User).filter_by(email="student@test.com").first()
    token = student_headers["Authorization"].split(" ", 1)[1]
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    active_jti = payload.get("jti")
    # Use a unique JTI so re-runs on a persistent DB don't collide
    dummy_jti = f"test-revoke-dummy-{uuid.uuid4().hex}"
    now = utc_now()
    dummy = UserSession(
        id=uuid.uuid4(),
        user_id=student.id,
        token_jti=dummy_jti,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(minutes=30),
    )
    try:
        db_session.add(dummy)
        db_session.flush()
    except Exception:
        db_session.rollback()
        raise
    r = client.post(f"/api/auth/security/sessions/{dummy.id}/revoke", headers=student_headers)
    assert r.status_code == 200
