from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException, status

from app.models.platform_features import UserSession
from app.services.security_service import assert_session_valid


def test_assert_session_valid_accepts_naive_expires_at(test_db, test_user):
    expires_at_naive = datetime.utcnow() + timedelta(minutes=30)
    session = UserSession(
        id="sess-1",
        user_id=test_user.id,
        token_jti="jti-1",
        expires_at=expires_at_naive,
    )
    test_db.add(session)
    test_db.commit()

    loaded = assert_session_valid(test_db, token_jti="jti-1")
    assert loaded is not None
    assert loaded.id == "sess-1"


def test_assert_session_valid_rejects_expired_naive_expires_at(test_db, test_user):
    expires_at_naive = datetime.utcnow() - timedelta(minutes=1)
    session = UserSession(
        id="sess-2",
        user_id=test_user.id,
        token_jti="jti-2",
        expires_at=expires_at_naive,
    )
    test_db.add(session)
    test_db.commit()

    with pytest.raises(HTTPException) as exc:
        assert_session_valid(test_db, token_jti="jti-2")
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

