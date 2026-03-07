"""normalize attendance status enum labels to lowercase

Revision ID: d4f6a8b0c2e4
Revises: c3d4e5f6a7b8
Create Date: 2026-03-06 20:25:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4f6a8b0c2e4"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rename_enum_value(type_name: str, old_value: str, new_value: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_enum e ON e.enumtypid = t.oid
                WHERE t.typname = '{type_name}'
                  AND e.enumlabel = '{old_value}'
            ) THEN
                ALTER TYPE {type_name} RENAME VALUE '{old_value}' TO '{new_value}';
            END IF;
        END
        $$;
        """
    )


def upgrade() -> None:
    _rename_enum_value("attendancestatus", "PRESENT", "present")
    _rename_enum_value("attendancestatus", "ABSENT", "absent")
    _rename_enum_value("attendancestatus", "EXCUSED", "excused")


def downgrade() -> None:
    _rename_enum_value("attendancestatus", "present", "PRESENT")
    _rename_enum_value("attendancestatus", "absent", "ABSENT")
    _rename_enum_value("attendancestatus", "excused", "EXCUSED")
