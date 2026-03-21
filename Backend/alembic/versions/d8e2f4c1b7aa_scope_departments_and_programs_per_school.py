"""Use: Implements the database change for scope departments and programs per school.
Where to use: Use this only when Alembic runs backend database upgrades or downgrades.
Role: Migration layer. It records one step in the database schema history.

scope departments and programs per school

Revision ID: d8e2f4c1b7aa
Revises: c3d91e4ab2f6
Create Date: 2026-03-16 10:15:00.000000
"""

from __future__ import annotations

from collections import defaultdict
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d8e2f4c1b7aa"
down_revision: Union[str, None] = "c3d91e4ab2f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


departments_table = sa.table(
    "departments",
    sa.column("id", sa.Integer()),
    sa.column("name", sa.String()),
    sa.column("school_id", sa.Integer()),
)

programs_table = sa.table(
    "programs",
    sa.column("id", sa.Integer()),
    sa.column("name", sa.String()),
    sa.column("school_id", sa.Integer()),
)

schools_table = sa.table(
    "schools",
    sa.column("id", sa.Integer()),
)

student_profiles_table = sa.table(
    "student_profiles",
    sa.column("id", sa.Integer()),
    sa.column("school_id", sa.Integer()),
    sa.column("department_id", sa.Integer()),
    sa.column("program_id", sa.Integer()),
)

governance_units_table = sa.table(
    "governance_units",
    sa.column("id", sa.Integer()),
    sa.column("school_id", sa.Integer()),
    sa.column("department_id", sa.Integer()),
    sa.column("program_id", sa.Integer()),
)

events_table = sa.table(
    "events",
    sa.column("id", sa.Integer()),
    sa.column("school_id", sa.Integer()),
)

event_department_association_table = sa.table(
    "event_department_association",
    sa.column("event_id", sa.Integer()),
    sa.column("department_id", sa.Integer()),
)

event_program_association_table = sa.table(
    "event_program_association",
    sa.column("event_id", sa.Integer()),
    sa.column("program_id", sa.Integer()),
)

program_department_association_table = sa.table(
    "program_department_association",
    sa.column("program_id", sa.Integer()),
    sa.column("department_id", sa.Integer()),
)


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_exists(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _index_exists(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _unique_constraint_exists(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return any(
        constraint.get("name") == constraint_name
        for constraint in inspector.get_unique_constraints(table_name)
    )


def _drop_global_name_unique_constraints(inspector: sa.Inspector, table_name: str) -> None:
    if not _table_exists(inspector, table_name):
        return
    for constraint in inspector.get_unique_constraints(table_name):
        if constraint.get("column_names") == ["name"] and constraint.get("name"):
            op.drop_constraint(constraint["name"], table_name, type_="unique")


def _ensure_school_scope_columns(inspector: sa.Inspector) -> None:
    if not _column_exists(inspector, "departments", "school_id"):
        with op.batch_alter_table("departments") as batch_op:
            batch_op.add_column(sa.Column("school_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_departments_school_id_schools",
                "schools",
                ["school_id"],
                ["id"],
                ondelete="CASCADE",
            )

    inspector = sa.inspect(op.get_bind())
    if not _index_exists(inspector, "departments", "ix_departments_school_id"):
        op.create_index("ix_departments_school_id", "departments", ["school_id"], unique=False)

    if not _column_exists(inspector, "programs", "school_id"):
        with op.batch_alter_table("programs") as batch_op:
            batch_op.add_column(sa.Column("school_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_programs_school_id_schools",
                "schools",
                ["school_id"],
                ["id"],
                ondelete="CASCADE",
            )

    inspector = sa.inspect(op.get_bind())
    if not _index_exists(inspector, "programs", "ix_programs_school_id"):
        op.create_index("ix_programs_school_id", "programs", ["school_id"], unique=False)


def _collect_school_usage_pairs(connection):
    department_school_ids: dict[int, set[int]] = defaultdict(set)
    program_school_ids: dict[int, set[int]] = defaultdict(set)

    for department_id, school_id in connection.execute(
        sa.select(student_profiles_table.c.department_id, student_profiles_table.c.school_id).where(
            student_profiles_table.c.department_id.is_not(None),
            student_profiles_table.c.school_id.is_not(None),
        )
    ):
        department_school_ids[int(department_id)].add(int(school_id))

    for program_id, school_id in connection.execute(
        sa.select(student_profiles_table.c.program_id, student_profiles_table.c.school_id).where(
            student_profiles_table.c.program_id.is_not(None),
            student_profiles_table.c.school_id.is_not(None),
        )
    ):
        program_school_ids[int(program_id)].add(int(school_id))

    if _table_exists(sa.inspect(connection), "governance_units"):
        for department_id, school_id in connection.execute(
            sa.select(governance_units_table.c.department_id, governance_units_table.c.school_id).where(
                governance_units_table.c.department_id.is_not(None),
                governance_units_table.c.school_id.is_not(None),
            )
        ):
            department_school_ids[int(department_id)].add(int(school_id))

        for program_id, school_id in connection.execute(
            sa.select(governance_units_table.c.program_id, governance_units_table.c.school_id).where(
                governance_units_table.c.program_id.is_not(None),
                governance_units_table.c.school_id.is_not(None),
            )
        ):
            program_school_ids[int(program_id)].add(int(school_id))

    event_school_ids = {
        int(row.id): int(row.school_id)
        for row in connection.execute(
            sa.select(events_table.c.id, events_table.c.school_id)
        )
        if row.school_id is not None
    }

    for event_id, department_id in connection.execute(
        sa.select(
            event_department_association_table.c.event_id,
            event_department_association_table.c.department_id,
        )
    ):
        school_id = event_school_ids.get(event_id)
        if department_id is not None and school_id is not None:
            department_school_ids[int(department_id)].add(int(school_id))

    for event_id, program_id in connection.execute(
        sa.select(
            event_program_association_table.c.event_id,
            event_program_association_table.c.program_id,
        )
    ):
        school_id = event_school_ids.get(event_id)
        if program_id is not None and school_id is not None:
            program_school_ids[int(program_id)].add(int(school_id))

    for department_id, school_id in connection.execute(
        sa.select(departments_table.c.id, departments_table.c.school_id).where(
            departments_table.c.school_id.is_not(None)
        )
    ):
        department_school_ids[int(department_id)].add(int(school_id))

    for program_id, school_id in connection.execute(
        sa.select(programs_table.c.id, programs_table.c.school_id).where(
            programs_table.c.school_id.is_not(None)
        )
    ):
        program_school_ids[int(program_id)].add(int(school_id))

    program_department_rows = list(
        connection.execute(
            sa.select(
                program_department_association_table.c.program_id,
                program_department_association_table.c.department_id,
            )
        )
    )

    changed = True
    while changed:
        changed = False
        for program_id, department_id in program_department_rows:
            if program_id is None or department_id is None:
                continue

            for school_id in tuple(department_school_ids.get(int(department_id), set())):
                if school_id not in program_school_ids[int(program_id)]:
                    program_school_ids[int(program_id)].add(int(school_id))
                    changed = True

            for school_id in tuple(program_school_ids.get(int(program_id), set())):
                if school_id not in department_school_ids[int(department_id)]:
                    department_school_ids[int(department_id)].add(int(school_id))
                    changed = True

    return department_school_ids, program_school_ids, program_department_rows, event_school_ids


def _duplicate_rows_per_school(
    connection,
    *,
    source_table,
    school_usage: dict[int, set[int]],
    school_ids: list[int],
):
    single_school_id = school_ids[0] if len(school_ids) == 1 else None
    id_map: dict[tuple[int, int], int] = {}

    rows = list(
        connection.execute(
            sa.select(source_table.c.id, source_table.c.name, source_table.c.school_id).order_by(source_table.c.id.asc())
        )
    )
    for row in rows:
        source_id = int(row.id)
        resolved_school_ids = sorted(int(value) for value in school_usage.get(source_id, set()))

        if row.school_id is not None:
            stored_school_id = int(row.school_id)
            if stored_school_id not in resolved_school_ids:
                resolved_school_ids.insert(0, stored_school_id)

        if not resolved_school_ids and single_school_id is not None:
            resolved_school_ids = [single_school_id]

        if not resolved_school_ids:
            continue

        primary_school_id = resolved_school_ids[0]
        connection.execute(
            source_table.update()
            .where(source_table.c.id == source_id)
            .values(school_id=primary_school_id)
        )
        id_map[(source_id, primary_school_id)] = source_id

        for school_id in resolved_school_ids[1:]:
            new_id = connection.execute(
                source_table.insert()
                .values(name=row.name, school_id=school_id)
                .returning(source_table.c.id)
            ).scalar_one()
            id_map[(source_id, int(school_id))] = int(new_id)

    return id_map


def _repoint_profile_and_governance_references(
    connection,
    *,
    department_id_map: dict[tuple[int, int], int],
    program_id_map: dict[tuple[int, int], int],
) -> None:
    for row in connection.execute(
        sa.select(
            student_profiles_table.c.id,
            student_profiles_table.c.school_id,
            student_profiles_table.c.department_id,
            student_profiles_table.c.program_id,
        )
    ):
        school_id = int(row.school_id)
        updates: dict[str, int] = {}

        if row.department_id is not None:
            mapped_department_id = department_id_map.get((int(row.department_id), school_id))
            if mapped_department_id is not None and mapped_department_id != row.department_id:
                updates["department_id"] = mapped_department_id

        if row.program_id is not None:
            mapped_program_id = program_id_map.get((int(row.program_id), school_id))
            if mapped_program_id is not None and mapped_program_id != row.program_id:
                updates["program_id"] = mapped_program_id

        if updates:
            connection.execute(
                student_profiles_table.update()
                .where(student_profiles_table.c.id == row.id)
                .values(**updates)
            )

    if not _table_exists(sa.inspect(connection), "governance_units"):
        return

    for row in connection.execute(
        sa.select(
            governance_units_table.c.id,
            governance_units_table.c.school_id,
            governance_units_table.c.department_id,
            governance_units_table.c.program_id,
        )
    ):
        school_id = int(row.school_id)
        updates: dict[str, int] = {}

        if row.department_id is not None:
            mapped_department_id = department_id_map.get((int(row.department_id), school_id))
            if mapped_department_id is not None and mapped_department_id != row.department_id:
                updates["department_id"] = mapped_department_id

        if row.program_id is not None:
            mapped_program_id = program_id_map.get((int(row.program_id), school_id))
            if mapped_program_id is not None and mapped_program_id != row.program_id:
                updates["program_id"] = mapped_program_id

        if updates:
            connection.execute(
                governance_units_table.update()
                .where(governance_units_table.c.id == row.id)
                .values(**updates)
            )


def _rebuild_associations(
    connection,
    *,
    department_school_ids: dict[int, set[int]],
    program_school_ids: dict[int, set[int]],
    department_id_map: dict[tuple[int, int], int],
    program_id_map: dict[tuple[int, int], int],
    program_department_rows,
    event_school_ids: dict[int, int],
    school_ids: list[int],
) -> None:
    single_school_id = school_ids[0] if len(school_ids) == 1 else None

    original_event_departments = list(
        connection.execute(
            sa.select(
                event_department_association_table.c.event_id,
                event_department_association_table.c.department_id,
            )
        )
    )
    connection.execute(event_department_association_table.delete())
    desired_event_departments = set()
    for event_id, old_department_id in original_event_departments:
        school_id = event_school_ids.get(event_id)
        if school_id is None or old_department_id is None:
            continue
        mapped_department_id = department_id_map.get((int(old_department_id), int(school_id)))
        if mapped_department_id is not None:
            desired_event_departments.add((int(event_id), int(mapped_department_id)))
    if desired_event_departments:
        connection.execute(
            event_department_association_table.insert(),
            [
                {"event_id": event_id, "department_id": department_id}
                for event_id, department_id in sorted(desired_event_departments)
            ],
        )

    original_event_programs = list(
        connection.execute(
            sa.select(
                event_program_association_table.c.event_id,
                event_program_association_table.c.program_id,
            )
        )
    )
    connection.execute(event_program_association_table.delete())
    desired_event_programs = set()
    for event_id, old_program_id in original_event_programs:
        school_id = event_school_ids.get(event_id)
        if school_id is None or old_program_id is None:
            continue
        mapped_program_id = program_id_map.get((int(old_program_id), int(school_id)))
        if mapped_program_id is not None:
            desired_event_programs.add((int(event_id), int(mapped_program_id)))
    if desired_event_programs:
        connection.execute(
            event_program_association_table.insert(),
            [
                {"event_id": event_id, "program_id": program_id}
                for event_id, program_id in sorted(desired_event_programs)
            ],
        )

    connection.execute(program_department_association_table.delete())
    desired_program_department_links = set()
    for old_program_id, old_department_id in program_department_rows:
        if old_program_id is None or old_department_id is None:
            continue

        school_scope_ids = sorted(
            program_school_ids.get(int(old_program_id), set())
            & department_school_ids.get(int(old_department_id), set())
        )
        if not school_scope_ids and single_school_id is not None:
            school_scope_ids = [single_school_id]

        for school_id in school_scope_ids:
            mapped_program_id = program_id_map.get((int(old_program_id), int(school_id)))
            mapped_department_id = department_id_map.get((int(old_department_id), int(school_id)))
            if mapped_program_id is None or mapped_department_id is None:
                continue
            desired_program_department_links.add((int(mapped_program_id), int(mapped_department_id)))

    if desired_program_department_links:
        connection.execute(
            program_department_association_table.insert(),
            [
                {"program_id": program_id, "department_id": department_id}
                for program_id, department_id in sorted(desired_program_department_links)
            ],
        )


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    _ensure_school_scope_columns(inspector)
    inspector = sa.inspect(connection)
    _drop_global_name_unique_constraints(inspector, "departments")
    inspector = sa.inspect(connection)
    _drop_global_name_unique_constraints(inspector, "programs")

    school_ids = [int(row.id) for row in connection.execute(sa.select(schools_table.c.id).order_by(schools_table.c.id.asc()))]

    (
        department_school_ids,
        program_school_ids,
        program_department_rows,
        event_school_ids,
    ) = _collect_school_usage_pairs(connection)

    department_id_map = _duplicate_rows_per_school(
        connection,
        source_table=departments_table,
        school_usage=department_school_ids,
        school_ids=school_ids,
    )
    program_id_map = _duplicate_rows_per_school(
        connection,
        source_table=programs_table,
        school_usage=program_school_ids,
        school_ids=school_ids,
    )

    _repoint_profile_and_governance_references(
        connection,
        department_id_map=department_id_map,
        program_id_map=program_id_map,
    )
    _rebuild_associations(
        connection,
        department_school_ids=department_school_ids,
        program_school_ids=program_school_ids,
        department_id_map=department_id_map,
        program_id_map=program_id_map,
        program_department_rows=program_department_rows,
        event_school_ids=event_school_ids,
        school_ids=school_ids,
    )

    inspector = sa.inspect(connection)
    if not _unique_constraint_exists(inspector, "departments", "uq_departments_school_name"):
        op.create_unique_constraint(
            "uq_departments_school_name",
            "departments",
            ["school_id", "name"],
        )

    inspector = sa.inspect(connection)
    if not _unique_constraint_exists(inspector, "programs", "uq_programs_school_name"):
        op.create_unique_constraint(
            "uq_programs_school_name",
            "programs",
            ["school_id", "name"],
        )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade is not supported for d8e2f4c1b7aa because school-scoped academic rows "
        "may have been duplicated and repointed across multiple campuses."
    )
