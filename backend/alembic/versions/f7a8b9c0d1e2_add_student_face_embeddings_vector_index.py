"""Add pgvector index table for student face embeddings.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-04-25 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgresql():
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "student_face_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("student_profile_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("program_id", sa.Integer(), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="arcface"),
        sa.Column("embedding_dtype", sa.String(length=16), nullable=False, server_default="float32"),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False, server_default="512"),
        sa.Column("embedding_normalized", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("student_profile_id", name="uq_student_face_embeddings_student_profile_id"),
    )
    op.execute("ALTER TABLE student_face_embeddings ALTER COLUMN embedding TYPE vector(512) USING embedding::vector")
    op.create_index(
        "ix_student_face_embeddings_school_active",
        "student_face_embeddings",
        ["school_id"],
        unique=False,
        postgresql_where=sa.text("is_active IS TRUE"),
    )
    op.create_index(
        "ix_student_face_embeddings_scope_active",
        "student_face_embeddings",
        ["school_id", "department_id", "program_id"],
        unique=False,
        postgresql_where=sa.text("is_active IS TRUE"),
    )
    # Runtime registration syncs new/updated faces. Existing rows can be indexed
    # with the dedicated operational backfill script documented with this change.
    op.execute(
        """
        DO $$
        BEGIN
            BEGIN
                EXECUTE '
                    CREATE INDEX IF NOT EXISTS ix_student_face_embeddings_vector_hnsw
                    ON student_face_embeddings
                    USING hnsw (embedding vector_cosine_ops)
                ';
            EXCEPTION WHEN OTHERS THEN
                EXECUTE '
                    CREATE INDEX IF NOT EXISTS ix_student_face_embeddings_vector_hnsw
                    ON student_face_embeddings
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                ';
            END;
        END $$;
        """
    )


def downgrade() -> None:
    if not _is_postgresql():
        return

    op.execute("DROP INDEX IF EXISTS ix_student_face_embeddings_vector_hnsw")
    op.drop_index("ix_student_face_embeddings_scope_active", table_name="student_face_embeddings")
    op.drop_index("ix_student_face_embeddings_school_active", table_name="student_face_embeddings")
    op.drop_table("student_face_embeddings")
