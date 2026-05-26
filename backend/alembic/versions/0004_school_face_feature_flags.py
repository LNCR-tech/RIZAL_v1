"""add school face feature flags

Revision ID: 0004_school_face_feature_flags
Revises: b033a6f7e275
Create Date: 2026-05-09 04:54:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0004_school_face_feature_flags"
down_revision: Union[str, None] = "b033a6f7e275"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE school_event_policies
        ADD COLUMN IF NOT EXISTS privileged_face_verification_enabled BOOLEAN NOT NULL DEFAULT TRUE
        """
    )
    op.execute(
        """
        ALTER TABLE school_event_policies
        ADD COLUMN IF NOT EXISTS attendance_face_recognition_enabled BOOLEAN NOT NULL DEFAULT TRUE
        """
    )
    op.execute(
        """
        ALTER TABLE school_event_policies
        ADD COLUMN IF NOT EXISTS first_time_face_registration_required BOOLEAN NOT NULL DEFAULT TRUE
        """
    )
    op.execute(
        """
        ALTER TABLE school_event_policies
        ALTER COLUMN privileged_face_verification_enabled DROP DEFAULT,
        ALTER COLUMN attendance_face_recognition_enabled DROP DEFAULT,
        ALTER COLUMN first_time_face_registration_required DROP DEFAULT
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE school_event_policies
        DROP COLUMN IF EXISTS first_time_face_registration_required,
        DROP COLUMN IF EXISTS attendance_face_recognition_enabled,
        DROP COLUMN IF EXISTS privileged_face_verification_enabled
        """
    )
