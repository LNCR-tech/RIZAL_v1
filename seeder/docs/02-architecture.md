# Chapter 2 — Architecture and File Layout

<!--nav-->
[← Ch.1 Purpose](01-purpose.md) | [🏠 Home](/README.md) | [Ch.3 Configuration →](03-configuration.md)

---
<!--/nav-->

---

## 2.1 Directory Structure

```
seeder/
├── seed.py              Entry point and CLI
├── config.py            Loads and validates variables.py before anything runs
├── variables.py         All configuration — edit this before running
├── pyrightconfig.json   Tells Pylance where to find app.* imports
├── ARCHITECTURE.md      Internal architecture reference
├── docs/                This documentation
└── modules/
    ├── data.py          Static data pools (names, schools, colleges, events)
    ├── core.py          DB factory functions and lifecycle helpers
    ├── demo.py          Main orchestration — full generation sequence per school
    └── helpers.py       Pure utilities: date generation, chunking, bcrypt, etc.
```

---

## 2.2 Module Responsibilities

### `seed.py` — Entry Point

The CLI entry point. Responsibilities:

1. Injects `../backend` into `sys.path` so `app.*` imports resolve at runtime
2. Calls `load_config()` to validate `variables.py` before anything else runs
3. Parses CLI arguments, which override `variables.py` defaults for that run
4. Opens a SQLAlchemy session
5. Runs the pre-generation pipeline: `ensure_tables` → `wipe_records` (if enabled) → `seed_roles` → `seed_permission_catalog` → `seed_platform_admin`
6. Dispatches to `run_demo()` with all parameters
7. Handles `KeyboardInterrupt` and exceptions with rollback

### `config.py` — Validator

Loads `variables.py` via `importlib` (not a direct import) so it can catch `SyntaxError` and missing-file errors before they become cryptic tracebacks. Validates every field for type, range, and cross-field constraints. Returns a frozen `SeederConfig` dataclass. Calls `sys.exit(1)` with a human-readable message on any failure.

### `variables.py` — Configuration

Plain Python file with typed variable assignments. No imports, no logic. The only file a user needs to edit before running. See [Chapter 3](./03-configuration.md) for the full reference.

### `modules/data.py` — Static Data Pools

Pure data. No DB, no `app.*` imports. Contains all the name pools, school names, college/program datasets, event themes, locations, announcement templates, note templates, and compliance note templates used during generation.

### `modules/helpers.py` — Pure Utilities

No SQLAlchemy, no `app.*`. Contains:

- `get_random_date_in_range` — uniform random datetime within a bounded window
- `chunked` — splits a list into fixed-size chunks for batch DB inserts
- `hash_passwords_parallel` — concurrent bcrypt via `ThreadPoolExecutor`
- `pick_colleges` — samples N colleges and a random subset of their programs
- `is_absent` — single Bernoulli trial for absence
- `apply_suffix` — appends a generational suffix with given probability

### `modules/core.py` — DB Layer

All SQLAlchemy operations. Every function either creates or retrieves a single record type. Uses `db.flush()` rather than `db.commit()` so the caller controls transaction boundaries. Commits are issued at the school level and per attendance chunk in `demo.py`.

### `modules/demo.py` — Orchestration

The main generation loop. Iterates over schools and runs the full generation sequence for each. All parameters are passed in — nothing is read from config or env directly inside this module.

---

## 2.3 Execution Flow

```
seed.py
  │
  ├── config.load_config()          Validate variables.py
  │
  ├── ensure_tables()               CREATE TABLE IF NOT EXISTS
  ├── wipe_records()                TRUNCATE ... CASCADE (if enabled)
  ├── seed_roles()                  INSERT roles
  ├── seed_permission_catalog()     INSERT governance permissions
  ├── seed_platform_admin()         INSERT/repair platform admin user
  │
  └── run_demo()
        │
        └── for each school:
              ├── get_or_create_school()
              ├── departments + programs
              ├── campus admin user
              ├── SSG → SG → ORG governance units + permissions + announcements
              ├── students (bulk bcrypt → bulk insert)
              ├── governance officers (drawn from leader pool)
              ├── student notes
              ├── events (with stochastic status + sanction configs)
              └── attendances + sanctions (batched in chunks of 2000)
                    └── db.commit() per chunk
```

---

## 2.4 Dependency on Bootstrap

The seeder depends on `bootstrap.py` having been run first. Specifically:

- `seed_roles()` in the seeder is additive — it adds governance roles (`ssg`, `sg`, `org`, `faculty`, `school_it`) that bootstrap does not seed. But it does not re-seed `admin`, `campus_admin`, `student` — those are already there from bootstrap.
- `resolve_event_type_id()` in `core.py` looks up global `EventType` records by name. These are seeded by `bootstrap.py`. If bootstrap has not run, every event will have `event_type_id = NULL`.

Running the seeder on a completely empty database (no bootstrap) will not crash, but the data will be incomplete.
