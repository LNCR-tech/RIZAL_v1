# Seeder Architecture

Internal reference for the seeder's structure, module responsibilities, and data dependency order.

For usage instructions, configuration, and output details see [SEEDER_GUIDE.md](../docs/backend/SEEDER_GUIDE.md).

---

## Directory Structure

```
seeder/
├── seed.py          Entry point and CLI
├── config.py        Loads and validates variables.py — fails fast before touching the DB
├── variables.py     All configuration — edit this before running
├── ARCHITECTURE.md  This file
└── modules/
    ├── __init__.py
    ├── data.py      Static datasets (name pools, school names, colleges, programs, event data)
    ├── helpers.py   Pure utilities — no DB, no app.* imports
    ├── core.py      DB lifecycle + all factory functions
    └── demo.py      Demo orchestration — full generation sequence per school
```

`seed.py` injects `../backend` into `sys.path` so `app.*` imports resolve correctly without installing the backend as a package.

---

## Module Responsibilities

### `config.py`
Loads `variables.py` via `importlib` (not a direct import) so it can catch `SyntaxError` and missing-file errors cleanly. Validates every field — type, range, and cross-field constraints (start date must not be later than end date). Returns a frozen `SeederConfig` dataclass. Calls `sys.exit(1)` with a human-readable message on any failure.

### `variables.py`
Plain Python file with typed variable assignments. No imports, no logic. The only file a user needs to edit before running.

### `modules/data.py`
Static data only. No DB, no `app.*` imports. Contains:
- Name pools: first names, last names, middle names, suffixes
- School name pool (21 entries — caps `SEED_N_SCHOOLS`)
- College → programs dataset (15 colleges, used by `pick_colleges`)
- Event themes, event types, locations
- Announcement templates, student note templates, compliance note templates
- `DEFAULT_ROLE_NAMES` — must stay in sync with the `roles` table

### `modules/helpers.py`
Pure Python utilities. No SQLAlchemy, no `app.*`.
- `get_random_date_in_range(rng, ...)` — uniform random datetime within a bounded window, with swap protection and Feb-29 fallback
- `chunked(items, size)` — splits a list into fixed-size chunks for batch DB inserts
- `hash_passwords_parallel(passwords, *, rounds, workers)` — concurrent bcrypt via `ThreadPoolExecutor`; uses rounds=6 for students (speed), rounds=12 for the platform admin (security)
- `pick_colleges(rng, dataset, n, min_programs)` — samples N colleges and a random subset of their programs
- `is_absent(rng, base_prob)` — single Bernoulli trial for absence
- `apply_suffix(rng, name, suffixes, probability)` — appends a generational suffix with given probability

### `modules/core.py`
All SQLAlchemy operations. Imports from `data.py`, `helpers.py`, and `app.*`.

Lifecycle functions:
- `ensure_tables()` — `Base.metadata.create_all(engine)`
- `wipe_records(db, preserve_platform_admin)` — bulk `TRUNCATE ... CASCADE` across all seeded tables; surgically deletes non-admin users via `DELETE WHERE email !=`
- `seed_roles(db)` — idempotent insert of all role names from `data.DEFAULT_ROLE_NAMES`
- `seed_permission_catalog(db)` — idempotent insert of all `GovernancePermission` rows from `PERMISSION_DEFINITIONS`
- `seed_platform_admin(db, email, password_hash)` — creates or repairs the platform admin user and ensures the `admin` role is assigned
- `resolve_event_type_id(db, name)` — looks up a global `EventType` by name (falls back to any school-scoped match); used to populate `event_type_id` FK

Factory functions (all use `db.flush()`, not `db.commit()`, so the caller controls transaction boundaries):
- `get_or_create_school` / `get_or_create_department` / `get_or_create_program`
- `link_program_to_department`
- `create_user` / `assign_role` / `create_student_profile`
- `create_governance_unit` / `assign_unit_permissions`
- `create_governance_member` / `set_member_permissions`
- `create_event` / `create_sanction_config` / `create_sanction_delegation`
- `create_announcement` / `create_student_note` / `create_compliance_history`

### `modules/demo.py`
Orchestrates the full generation sequence. All parameters are passed in — nothing is read from config or env directly. Commits are issued per-school and per attendance chunk (2000 rows) to bound memory usage.

---

## Data Dependency Order

```
roles
permissions catalog
  └── school + school_settings
        └── departments + programs (many-to-many via association table)
              └── campus_admin user + user_role
                    └── governance_units (SSG → SG per dept → ORG per SG)
                          └── governance_unit_permissions
                                └── governance_announcements
                                      └── students (users + user_roles + student_profiles)
                                            └── governance_members + member_permissions
                                                  └── student_notes
                                                        └── events (+ event_type_id FK)
                                                              └── event_sanction_configs
                                                                    └── sanction_delegations
                                                                          └── attendances (batched)
                                                                                └── sanction_records
                                                                                      └── sanction_items
                                                                                            └── sanction_compliance_history
```

---

## Stochastic Design Notes

**Single RNG instance** — `random.Random(SEED_RANDOMIZER_KEY)` is created once in `seed.py` and passed through to every function that needs randomness. This guarantees full reproducibility: same key + same config = identical dataset, regardless of execution environment.

**Chaos engine** — two probabilities are rolled once per run (not per school): `cancellation_prob_base` (2–7%) and `emergency_cutoff_prob` (10–25%). These govern event status and attendance gate probabilities across the entire dataset, giving each seeded universe a consistent "climate".

**Program weight distribution** — each program in a school is assigned a random weight (10–100) before students are distributed. This produces realistic enrollment skew rather than uniform distribution across programs.

**Leader pool** — the top ~15% of students (min 5) are sampled as the governance leader pool. Officers are drawn from this pool with overlap allowed, so a student can simultaneously be an SSG officer, an SG officer, and an ORG officer — matching real-world hybrid governance roles.

**Attendance batching** — attendance rows are accumulated in memory and flushed in chunks of 2000 to avoid holding large transactions open. Sanction records are created inline within the same chunk loop so `attendance_id` FKs are available immediately after flush.

**Sanction config ID** — stored as `ev._seeder_sanction_config_id` (a transient Python attribute on the ORM object) after creation, then read back during the attendance loop. The `Event` model has no `sanction_config_id` column — this is purely a seeder-internal handoff.
