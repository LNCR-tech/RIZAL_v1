"""Add missing face feature flag columns to school_event_policies.

Migration 0004 was inserted into the chain after this DB was already past
that point, so ALTER TABLE never executed. This migration repairs the gap.

Revision ID: 0012_school_event_policy_face_flags
Revises: 0011_user_sessions_runtime
Create Date: 2026-05-27
"""

from alembic import op

revision = "0012_school_event_policy_face_flags"
down_revision = "0011_user_sessions_runtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE school_event_policies
        ADD COLUMN IF NOT EXISTS privileged_face_verification_enabled BOOLEAN NOT NULL DEFAULT TRUE,
        ADD COLUMN IF NOT EXISTS attendance_face_recognition_enabled BOOLEAN NOT NULL DEFAULT TRUE,
        ADD COLUMN IF NOT EXISTS first_time_face_registration_required BOOLEAN NOT NULL DEFAULT TRUE
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
