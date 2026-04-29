# Chapter 2 â€” Architecture and File Layout

<!--nav-->
[Previous](01-purpose.md) | [Next](03-configuration.md) | [Home](/README.md)

---
<!--/nav-->

---

## 2.1 Directory Structure

```
seeder/
â”œâ”€â”€ seed.py              Entry point and CLI
â”œâ”€â”€ config.py            Loads and validates variables.py before anything runs
â”œâ”€â”€ variables.py         All configuration â€” edit this before running
â”œâ”€â”€ pyrightconfig.json   Tells Pylance where to find app.* imports
â”œâ”€â”€ ARCHITECTURE.md      Internal architecture reference
â”œâ”€â”€ docs/                This documentation
â””â”€â”€ modules/
    â”œâ”€â”€ data.py          Static data pools (names, schools, colleges, events)
    â”œâ”€â”€ core.py          DB factory functions and lifecycle helpers
    â”œâ”€â”€ demo.py          Main orchestration â€” full generation sequence per school
    â””â”€â”€ helpers.py       Pure utilities: date generation, chunking, bcrypt, etc.
```

---

## 2.2 Module Responsibilities

### `seed.py` â€” Entry Point

The CLI entry point. Responsibilities:

1. Injects `../backend` into `sys.path` so `app.*` imports resolve at runtime
2. Calls `load_config()` to validate `variables.py` before anything else runs
3. Parses CLI arguments, which override `variables.py` defaults for that run
4. Opens a SQLAlchemy session
5. Runs the pre-generation pipeline: `ensure_tables` â†’ `wipe_records` (if enabled) â†’ `seed_roles` â†’ `seed_permission_catalog` â†’ `seed_platform_admin`
6. Dispatches to `run_demo()` with all parameters
7. Handles `KeyboardInterrupt` and exceptions with rollback

### `config.py` â€” Validator

Loads `variables.py` via `importlib` (not a direct import) so it can catch `SyntaxError` and missing-file errors before they become cryptic tracebacks. Validates every field for type, range, and cross-field constraints. Returns a frozen `SeederConfig` dataclass. Calls `sys.exit(1)` with a human-readable message on any failure.

### `variables.py` â€” Configuration

Plain Python file with typed variable assignments. No imports, no logic. The only file a user needs to edit before running. See [Chapter 3](./03-configuration.md) for the full reference.

### `modules/data.py` â€” Static Data Pools

Pure data. No DB, no `app.*` imports. Contains all the name pools, school names, college/program datasets, event themes, locations, announcement templates, note templates, and compliance note templates used during generation.

### `modules/helpers.py` â€” Pure Utilities

No SQLAlchemy, no `app.*`. Contains:

- `get_random_date_in_range` â€” uniform random datetime within a bounded window
- `chunked` â€” splits a list into fixed-size chunks for batch DB inserts
- `hash_passwords_parallel` â€” concurrent bcrypt via `ThreadPoolExecutor`
- `pick_colleges` â€” samples N colleges and a random subset of their programs
- `is_absent` â€” single Bernoulli trial for absence
- `apply_suffix` â€” appends a generational suffix with given probability

### `modules/core.py` â€” DB Layer

All SQLAlchemy operations. Every function either creates or retrieves a single record type. Uses `db.flush()` rather than `db.commit()` so the caller controls transaction boundaries. Commits are issued at the school level and per attendance chunk in `demo.py`.

### `modules/demo.py` â€” Orchestration

The main generation loop. Iterates over schools and runs the full generation sequence for each. All parameters are passed in â€” nothing is read from config or env directly inside this module.

---

## 2.3 Execution Flow

```
seed.py
  â”‚
  â”œâ”€â”€ config.load_config()          Validate variables.py
  â”‚
  â”œâ”€â”€ ensure_tables()               CREATE TABLE IF NOT EXISTS
  â”œâ”€â”€ wipe_records()                TRUNCATE ... CASCADE (if enabled)
  â”œâ”€â”€ seed_roles()                  INSERT roles
  â”œâ”€â”€ seed_attendance_methods()     INSERT attendance method lookup rows
  â”œâ”€â”€ seed_attendance_statuses()    INSERT attendance status lookup rows
  â”œâ”€â”€ seed_event_types()            INSERT global event types
  â”œâ”€â”€ seed_permission_catalog()     INSERT governance permissions
  â”œâ”€â”€ seed_platform_admin()         INSERT/repair platform admin user
  â”‚
  â””â”€â”€ run_demo()
        â”‚
        â””â”€â”€ for each school:
              â”œâ”€â”€ get_or_create_school()
              â”œâ”€â”€ academic_periods (1st/2nd/Summer for each year in date range)
              â”œâ”€â”€ departments + programs
              â”œâ”€â”€ campus admin user
              â”œâ”€â”€ SSG â†’ SG â†’ ORG governance units + permissions + announcements
              â”œâ”€â”€ students (bulk bcrypt â†’ bulk insert)
              â”œâ”€â”€ governance officers (drawn from leader pool)
              â”œâ”€â”€ student notes
              â”œâ”€â”€ events (with stochastic status + sanction configs)
              â””â”€â”€ attendances + sanctions (batched in chunks of 2000)
                    â””â”€â”€ db.commit() per chunk
```

---

## 2.4 Dependency on Bootstrap

The seeder is self-contained for all lookup data. It seeds roles, attendance methods, attendance statuses, event types, and governance permissions directly â€” it does not require `bootstrap.py` to have run first.

Running the seeder on a completely empty database will produce a fully populated, consistent dataset.

