"""drop legacy unused tables

Revision ID: 9b3e1f2c4d5a
Revises: b45c67d89e01
Create Date: 2026-03-12 14:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b3e1f2c4d5a"
down_revision: Union[str, None] = "b45c67d89e01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LEGACY_TABLES = (
    "security_alerts",
    "anomaly_logs",
    "attendance_predictions",
    "event_predictions",
    "event_flags",
    "event_consumption_logs",
    "recommendation_cache",
    "student_risk_scores",
    "notifications",
    "outbox_events",
    "model_metadata",
    "ai_logs",
)


def upgrade() -> None:
    for table_name in LEGACY_TABLES:
        op.execute(sa.text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))


def downgrade() -> None:
    raise NotImplementedError("Downgrade is not supported for legacy table cleanup.")
