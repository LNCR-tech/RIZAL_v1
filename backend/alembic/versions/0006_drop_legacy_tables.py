"""drop legacy tables no longer referenced by the application

Revision ID: 0006_drop_legacy_tables
Revises: 0005_rename_event_time_cols
Create Date: 2026-05-25 00:00:00.000000

Tables dropped:
  - attendances                  (replaced by attendance_records)
  - event_department_association (replaced by event_departments)
  - event_program_association    (replaced by event_programs)
  - program_department_association (replaced by program_departments)
  - school_settings              (replaced by school_branding + school_event_policies)
  - school_subscription_settings (replaced by school_subscriptions)
  - sanction_items               (replaced by sanction_record_items)

Orphaned FK columns also dropped:
  - sanction_records.attendance_id      (referenced legacy attendances table)
  - sanction_compliance_history.sanction_item_id (referenced legacy sanction_items table)
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_drop_legacy_tables"
down_revision = "0005_rename_event_time_cols"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All operations are guarded with IF EXISTS so the migration is safe on both
    # the legacy deployed DB (where these tables/columns existed) and a fresh DB
    # built from schema.sql (where they were never created).
    op.execute(sa.text("""
        DO $$
        BEGIN
            -- Drop sanction_records.attendance_id ONLY if it FK-references the legacy
            -- attendances table. The column was re-pointed to attendance_records in the
            -- current schema and must not be dropped on a fresh DB.
            IF EXISTS (
                SELECT 1 FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                JOIN pg_class f ON f.oid = c.confrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(c.conkey)
                WHERE t.relname = 'sanction_records'
                  AND c.contype = 'f'
                  AND f.relname = 'attendances'
                  AND a.attname = 'attendance_id'
            ) THEN
                ALTER TABLE sanction_records
                    DROP CONSTRAINT IF EXISTS sanction_records_attendance_id_fkey,
                    DROP COLUMN attendance_id;
            END IF;

            -- Drop orphaned FK column: sanction_compliance_history.sanction_item_id
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'sanction_compliance_history' AND column_name = 'sanction_item_id'
            ) THEN
                ALTER TABLE sanction_compliance_history
                    DROP CONSTRAINT IF EXISTS sanction_compliance_history_sanction_item_id_fkey,
                    DROP COLUMN sanction_item_id;
            END IF;

            -- Drop legacy table: attendances
            IF EXISTS (
                SELECT 1 FROM information_schema.tables WHERE table_name = 'attendances'
            ) THEN
                ALTER TABLE attendances DROP CONSTRAINT IF EXISTS attendances_event_id_fkey;
                ALTER TABLE attendances DROP CONSTRAINT IF EXISTS attendances_student_id_fkey;
                ALTER TABLE attendances DROP CONSTRAINT IF EXISTS attendances_verified_by_fkey;
                DROP TABLE attendances;
            END IF;

            -- Drop legacy table: sanction_items
            IF EXISTS (
                SELECT 1 FROM information_schema.tables WHERE table_name = 'sanction_items'
            ) THEN
                ALTER TABLE sanction_items
                    DROP CONSTRAINT IF EXISTS sanction_items_sanction_record_id_fkey;
                DROP TABLE sanction_items;
            END IF;

            -- Drop remaining legacy tables (outgoing FKs only)
            DROP TABLE IF EXISTS event_department_association;
            DROP TABLE IF EXISTS event_program_association;
            DROP TABLE IF EXISTS program_department_association;
            DROP TABLE IF EXISTS school_settings;
            DROP TABLE IF EXISTS school_subscription_settings;
        END $$;
    """))


def downgrade() -> None:
    # Recreate school_subscription_settings
    op.create_table(
        "school_subscription_settings",
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("plan_name", sa.String(), nullable=False, server_default="free"),
        sa.Column("user_limit", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("event_limit_monthly", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("import_limit_monthly", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reminder_days_before", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("school_id"),
    )

    # Recreate school_settings
    op.create_table(
        "school_settings",
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("primary_color", sa.String(), nullable=False, server_default="#162F65"),
        sa.Column("secondary_color", sa.String(), nullable=False, server_default="#2C5F9E"),
        sa.Column("accent_color", sa.String(), nullable=False, server_default="#4A90E2"),
        sa.Column("event_default_early_check_in_minutes", sa.Integer(), nullable=False),
        sa.Column("event_default_late_threshold_minutes", sa.Integer(), nullable=False),
        sa.Column("event_default_sign_out_grace_minutes", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("school_id"),
    )

    # Recreate junction tables
    op.create_table(
        "program_department_association",
        sa.Column("program_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"]),
        sa.PrimaryKeyConstraint("program_id", "department_id"),
    )
    op.create_table(
        "event_program_association",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("program_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"]),
        sa.PrimaryKeyConstraint("event_id", "program_id"),
    )
    op.create_table(
        "event_department_association",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("event_id", "department_id"),
    )

    # Recreate sanction_items
    op.create_table(
        "sanction_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sanction_record_id", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(), nullable=True),
        sa.Column("item_name", sa.String(), nullable=False),
        sa.Column("item_description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("complied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("compliance_notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sanction_record_id"], ["sanction_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Recreate attendances
    op.create_table(
        "attendances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("time_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("method", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="present"),
        sa.Column("check_in_status", sa.String(), nullable=True),
        sa.Column("check_out_status", sa.String(), nullable=True),
        sa.Column("verified_by", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("geo_distance_m", sa.Float(), nullable=True),
        sa.Column("geo_effective_distance_m", sa.Float(), nullable=True),
        sa.Column("geo_latitude", sa.Float(), nullable=True),
        sa.Column("geo_longitude", sa.Float(), nullable=True),
        sa.Column("geo_accuracy_m", sa.Float(), nullable=True),
        sa.Column("liveness_label", sa.String(), nullable=True),
        sa.Column("liveness_score", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name="attendances_event_id_fkey"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], name="attendances_student_id_fkey"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], name="attendances_verified_by_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Restore orphaned FK columns
    op.add_column(
        "sanction_compliance_history",
        sa.Column("sanction_item_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "sanction_compliance_history_sanction_item_id_fkey",
        "sanction_compliance_history", "sanction_items",
        ["sanction_item_id"], ["id"], ondelete="SET NULL",
    )

    op.add_column(
        "sanction_records",
        sa.Column("attendance_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "sanction_records_attendance_id_fkey",
        "sanction_records", "attendances",
        ["attendance_id"], ["id"], ondelete="SET NULL",
    )
