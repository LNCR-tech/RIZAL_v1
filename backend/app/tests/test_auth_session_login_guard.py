"""Use: Tests login account-state guard rules.
Where to use: Use this when running `pytest` to check that this backend behavior still works.
Role: Test layer. It protects the app from regressions.
"""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.auth_session import validate_login_account_state


def _role_assignment(role_name: str):
    return SimpleNamespace(role=SimpleNamespace(name=role_name))


class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class _FakeDb:
    def __init__(self, school):
        self._school = school

    def query(self, model):
        return _FakeQuery(self._school)


def test_platform_admin_without_school_is_allowed() -> None:
    user = SimpleNamespace(
        is_active=True,
        school_id=None,
        roles=[_role_assignment("admin")],
    )

    validate_login_account_state(_FakeDb(None), user)


def test_inactive_account_is_rejected() -> None:
    user = SimpleNamespace(
        is_active=False,
        school_id=1,
        roles=[_role_assignment("school_IT")],
    )

    with pytest.raises(HTTPException, match="inactive"):
        validate_login_account_state(_FakeDb(SimpleNamespace(active_status=True)), user)


def test_account_without_roles_is_rejected() -> None:
    user = SimpleNamespace(
        is_active=True,
        school_id=1,
        roles=[],
    )

    with pytest.raises(HTTPException, match="no assigned role"):
        validate_login_account_state(_FakeDb(SimpleNamespace(active_status=True)), user)


def test_school_scoped_account_without_school_is_rejected() -> None:
    user = SimpleNamespace(
        is_active=True,
        school_id=None,
        roles=[_role_assignment("school_IT")],
    )

    with pytest.raises(HTTPException, match="not assigned to a school"):
        validate_login_account_state(_FakeDb(None), user)


def test_account_with_missing_school_is_rejected() -> None:
    user = SimpleNamespace(
        is_active=True,
        school_id=99,
        roles=[_role_assignment("school_IT")],
    )

    with pytest.raises(HTTPException, match="does not exist"):
        validate_login_account_state(_FakeDb(None), user)


def test_account_with_inactive_school_is_rejected() -> None:
    user = SimpleNamespace(
        is_active=True,
        school_id=2,
        roles=[_role_assignment("school_IT")],
    )

    with pytest.raises(HTTPException, match="school is inactive"):
        validate_login_account_state(_FakeDb(SimpleNamespace(active_status=False)), user)
