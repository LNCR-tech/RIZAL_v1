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
    from app.core.security import SECRET_KEY, ALGORITHM
    from app.models.platform_features import UserSession
    from app.models.user import User
    student = db_session.query(User).filter_by(email="student@test.com").first()
    # Identify the active session JTI so we don't revoke it
    token = student_headers["Authorization"].split(" ", 1)[1]
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    active_jti = payload.get("jti")
    # Find a session that is NOT the active one
    session = (
        db_session.query(UserSession)
        .filter(UserSession.user_id == student.id, UserSession.token_jti != active_jti)
        .first()
    )
    if session is None:
        import pytest; pytest.skip("No non-active sessions for student in test DB")
    r = client.post(f"/api/auth/security/sessions/{session.id}/revoke", headers=student_headers)
    assert r.status_code in (200, 403, 404)
