from pathlib import Path

from app.models.role import Role
from app.models.school import School, SchoolSetting
from app.models.user import User
from app.seeder import (
    DEFAULT_ROLE_NAMES,
    BootstrapSeedOptions,
    bootstrap_database,
    seed_demo_data,
    wipe_database_records,
)


def test_bootstrap_database_is_idempotent(test_db):
    options = BootstrapSeedOptions(
        admin_email="owner@example.com",
        admin_password="StrongPass123!",
    )

    bootstrap_database(test_db, options=options)
    bootstrap_database(test_db, options=options)

    assert test_db.query(Role).count() == len(DEFAULT_ROLE_NAMES)
    assert test_db.query(School).count() == 0
    assert test_db.query(SchoolSetting).count() == 0

    admin = test_db.query(User).filter(User.email == "owner@example.com").one()
    assert admin.school_id is None
    assert admin.check_password("StrongPass123!")
    assert [assignment.role.name for assignment in admin.roles] == ["admin"]


def test_seed_demo_data_uses_explicit_email_domain_and_credentials_path(test_db, tmp_path):
    bootstrap_database(
        test_db,
        options=BootstrapSeedOptions(
            admin_email="owner@example.com",
            admin_password="StrongPass123!",
        ),
    )
    credentials_path = tmp_path / "seed_credentials.csv"

    seed_demo_data(
        test_db,
        schools_target=1,
        users_target=8,
        email_domain="demo.example.test",
        credentials_path=credentials_path,
    )

    contents = credentials_path.read_text(encoding="utf-8")
    assert "demo.example.test" in contents
    assert "owner@example.com" not in contents


def test_wipe_database_records_preserves_requested_admin_email(test_db):
    options = BootstrapSeedOptions(
        admin_email="owner@example.com",
        admin_password="StrongPass123!",
    )
    bootstrap_database(test_db, options=options)
    extra_user = User(
        email="student@example.com",
        first_name="Student",
        last_name="Example",
    )
    extra_user.set_password("StudentPass123!")
    test_db.add(extra_user)
    test_db.commit()

    wipe_database_records(test_db, preserve_admin_email=options.admin_email)

    remaining_users = test_db.query(User).all()
    assert [user.email for user in remaining_users] == ["owner@example.com"]
