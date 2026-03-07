"""drop_global_student_id_uniqueness

Revision ID: a9d1f5c7b882
Revises: f2c6d8a9e1b3
Create Date: 2026-03-04 09:08:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a9d1f5c7b882"
down_revision: Union[str, None] = "f2c6d8a9e1b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_student_profiles_student_id", table_name="student_profiles")
    op.create_index("ix_student_profiles_student_id", "student_profiles", ["student_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_student_profiles_student_id", table_name="student_profiles")
    op.create_index("ix_student_profiles_student_id", "student_profiles", ["student_id"], unique=True)
