from app.models.role import Role
from app.models.event_type import EventType
from app.models.user import User
from app.seeder import (
    DEFAULT_ROLE_NAMES,
    BootstrapSeedOptions,
    bootstrap_database,
)


def test_bootstrap_database_is_idempotent(test_db):
    options = BootstrapSeedOptions(
        admin_email="owner@example.com",
        admin_password="StrongPass123!",
    )

    bootstrap_database(test_db, options=options)
    bootstrap_database(test_db, options=options)

    assert test_db.query(Role).count() == len(DEFAULT_ROLE_NAMES)
    assert test_db.query(EventType).filter(EventType.school_id.is_(None)).count() >= 1

    admin = test_db.query(User).filter(User.email == "owner@example.com").one()
    assert admin.school_id is None
    assert admin.check_password("StrongPass123!")
    assert [assignment.role.name for assignment in admin.roles] == ["admin"]
