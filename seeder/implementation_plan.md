# Seeder — Implementation Plan

---

## Directory Structure

```
aurav3/
└── Seeder/
    ├── seed.py          ← Unified CLI entry point
    └── modules/
        ├── __init__.py
        ├── config.py    ← Static datasets (names, academic data, role names)
        ├── helpers.py   ← Pure utility functions (no DB)
        ├── core.py      ← DB lifecycle + factory functions
        └── demo.py      ← Demo seeder orchestration
```

`seed.py` adds `Backend/` to `sys.path` so `app.*` imports resolve correctly.

---

## Seeding Dependency Order

```
roles
  └── school + school_settings
        └── departments + programs (many-to-many via association)
              └── users (admin, campus_admin, students)
                    └── user_roles
                          └── student_profiles
                                └── governance_units (SSG → SG → ORG)
                                      └── governance_permissions (catalog)
                                            └── governance_unit_permissions
                                                  └── governance_members
                                                        └── governance_member_permissions
                                                              └── events
                                                                    └── attendances
                                                                          └── event_sanction_configs
                                                                                └── sanction_delegations
                                                                                      └── sanction_records
                                                                                            └── sanction_items
```

---

## Module Specs

### `modules/config.py`
Static data only. No DB, no imports from `app.*`.

- Name pools: first names, last names, middle names, suffixes
- Academic dataset: colleges mapped to their programs (generic)
- School name pool: fictional names for generating demo schools
- Role names list (mirrors the `Role` table)

---

### `modules/helpers.py`
Pure Python utilities. No SQLAlchemy, no `app.*`.

- `random_date(rng, start, end)` — random datetime within a range
- `chunked(items, size)` — split a list into fixed-size chunks
- `hash_passwords_parallel(passwords, *, rounds, workers)` — concurrent bcrypt hashing
- `pick_colleges(rng, n)` — randomly pick N colleges + a subset of their programs

---

### `modules/core.py`
All DB-level operations. Imports from `config.py`, `helpers.py`, `app.*`.

**Lifecycle:**
- `ensure_tables()` — `Base.metadata.create_all(engine)`
- `wipe_records(db)` — delete all records in FK-safe reverse order
- `seed_roles(db)` — insert missing `Role` rows
- `seed_permission_catalog(db)` — insert missing `GovernancePermission` rows
- `seed_platform_admin(db, *, email, password)` — create/repair the global admin user

**Factories** (idempotent, get-or-create):
- `get_or_create_school(db, ...)` → `School`
- `get_or_create_department(db, ...)` → `Department`
- `get_or_create_program(db, ...)` → `Program`
- `link_program_to_department(db, ...)` → via association table
- `create_campus_admin(db, ...)` → `User`
- `create_student_user(db, ...)` → `User`
- `assign_role(db, ...)` → `UserRole`
- `create_student_profile(db, ...)` → `StudentProfile`
- `create_governance_unit(db, ...)` → `GovernanceUnit`
- `assign_unit_permissions(db, ...)` → `GovernanceUnitPermission`
- `create_governance_member(db, ...)` → `GovernanceMember`
- `assign_member_permissions(db, ...)` → `GovernanceMemberPermission`
- `create_event(db, ...)` → `Event`
- `create_sanction_config(db, ...)` → `EventSanctionConfig`
- `create_sanction_delegation(db, ...)` → `SanctionDelegation`
- `create_sanction_record(db, ...)` → `SanctionRecord`
- `create_sanction_items(db, ...)` → `SanctionItem`

---

### `modules/demo.py`
Orchestrates a full demo seed. All parameters passed in — nothing hardcoded.

**Sequence per school:**
1. Create school + `SchoolSetting`
2. Pick colleges → create departments + programs + link associations
3. Create campus admin
4. Create SSG → SG (one per dept) → ORG (one per prog) with unit permissions
5. Create students → `student` role → `StudentProfile`
6. Assign governance officers from students → `GovernanceMember` + member permissions
7. Create events (`COMPLETED`, past dates)
8. Generate attendance per student per event (`present` / `late` / `absent`)
9. For absent records → `EventSanctionConfig` + `SanctionRecord` (linked via `attendance_id`) + `SanctionItem`
10. Create `SanctionDelegation` from campus admin to SG units
11. Write credentials CSV to `Backend/storage/seed_credentials.csv`

**Entry point:**
```python
def run(db: Session, *, n_schools: int, rng: random.Random) -> None
```

**Credentials output:** `Seeder/storage/user_credentials.csv`
All generated accounts (platform admin, campus admins, students with governance roles,
regular students) are written here after each seed run. Used for manual QA and
browser testing across different account types and permission levels.

---

## `.env` Variables

The seeder reads from the root `.env`. Variables below are seeder-specific.
All others (DB URL, JWT, etc.) are owned by the backend and left untouched.

### Master Toggles

| Variable | Default | Purpose |
|---|---|---|
| `SEED_DATABASE` | `false` | Run the seeder on startup |
| `SEED_WIPE_EXISTING` | `false` | Delete all records before seeding |

### Randomization

| Variable | Default | Purpose |
|---|---|---|
| `SEED_RANDOMIZER_KEY` | `42` | Global RNG seed — same key = same output every time |
| `SEED_UNIQUE_PASSWORDS` | `false` | Give every user a unique password; `false` = shared demo password |
| `SEED_USER_SUFFIX_PROBABILITY` | `0.3` | Probability a student name gets a suffix (Jr., Sr., III, etc.) |

### School & Academic Structure

| Variable | Default | Purpose |
|---|---|---|
| `SEED_N_SCHOOLS` | `5` | Number of schools to generate |
| `SEED_MIN_COLLEGES` | `3` | Min number of colleges per school |
| `SEED_MAX_COLLEGES` | `8` | Max number of colleges per school |
| `SEED_MIN_PROGRAMS` | `1` | Min programs per college |

### Students, Events & Attendance Volumes

| Variable | Default | Purpose |
|---|---|---|
| `SEED_MIN_STUDENTS` | `50` | Min students per school |
| `SEED_MAX_STUDENTS` | `250` | Max students per school |
| `SEED_MIN_EVENTS` | `30` | Min events per school |
| `SEED_MAX_EVENTS` | `100` | Max events per school |
| `SEED_MIN_RECORDS` | `0` | Min target for total attendance records (drives sanction volume) |
| `SEED_MAX_RECORDS` | `0` | Max target for total attendance records |

> [!TIP]
> If `SEED_MAX_RECORDS` exceeds the natural core metric (`student_count × event_count`), 
> the seeder will inject extra duplicate attendance records to hit the target volume for stress-testing.

### Date Window

| Variable | Default | Purpose |
|---|---|---|
| `SEED_START_YEAR` | `2024` | Earliest year for generated records |
| `SEED_END_YEAR` | `2026` | Latest year for generated records |
| `SEED_START_MONTH_DATE` | `1,1` | Start month + day within start year (format: `M,D`) |
| `SEED_END_MONTH_DATE` | `12,31` | End month + day within end year (format: `M,D`) |

> [!NOTE]
> These variables produce a **deterministic** date window. Combined with `SEED_RANDOMIZER_KEY`,
> every run with the same config generates identical data — useful for reproducible testing.

---

## `seed.py` — CLI

```
python Seeder/seed.py demo
python Seeder/seed.py --help
```

- Injects `Backend/` into `sys.path`
- Loads `.env`
- Opens `SessionLocal()`, passes to `demo.run()`
- Handles `KeyboardInterrupt` and exceptions

> [!NOTE]
> CLI flags and `.env` parameters will be defined in a follow-up discussion.

---

## Files to Delete (Cj handles manually)

| File |
|---|
| `Backend/app/seeder.py` |
| `Backend/app/misamis_university_seeder.py` |
| `Backend/seed.py` |
| `Backend/seed_misamis_university.py` |
