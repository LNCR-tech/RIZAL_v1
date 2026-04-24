# Aura Demo Seeder

[<- Back to backend docs](./README.md)

The seeder generates a full production-scale demo dataset for Aura — multiple schools, complete academic hierarchies, governance structures, students, events, attendance records, sanctions, and compliance history. It is designed for QA, demos, and AI assistant stress-testing, not for bootstrapping a real deployment.

For production bootstrapping (admin account + roles + event types only), use `bootstrap.py` instead.

## Prerequisites

- The backend's `DATABASE_URL` must be set in the root `.env` — the seeder connects through `app.core.database`, so it inherits the same connection the backend uses.
- Run Alembic migrations first so all tables exist.
- Run the backend bootstrap first (`python bootstrap.py`) so global event types and base roles are present — the seeder depends on them.
- Install backend dependencies: `pip install -r backend/requirements.txt` from the repo root, or run inside the backend Docker container.

## Running the Seeder

The seeder must be run from inside the `seeder/` directory so its module imports resolve correctly.

```powershell
cd seeder

# Enable seeding first — it is off by default
# Edit variables.py: set SEED_DATABASE = True

python seed.py demo
```

CLI flags override `variables.py` defaults for that run only:

```powershell
python seed.py demo --schools 3 --min-students 100 --max-students 300
python seed.py demo --schools 1 --min-events 10 --max-events 20 --credentials-format tsv
python seed.py demo --help
```

## Configuration — `variables.py`

All seeder configuration lives in `seeder/variables.py`. Edit it directly before running. No `.env` variables, no CLI required for basic use.

`config.py` validates `variables.py` on startup and exits with a clear error message if anything is missing, the wrong type, or out of range — before touching the database.

### Safety gate

| Variable | Type | Default | Purpose |
|---|---|---|---|
| `SEED_DATABASE` | `bool` | `False` | Must be `True` to run. Prevents accidental execution. |
| `SEED_WIPE_EXISTING` | `bool` | `True` | Truncates all seeded tables before inserting. Safe to re-run. |

### Platform admin

| Variable | Type | Default | Purpose |
|---|---|---|---|
| `SEED_ADMIN_EMAIL` | `str` | `admin@aura.com` | Email for the platform admin account. Created if missing, preserved on wipe. |
| `SEED_ADMIN_PASSWORD` | `str` | `AdminPass123!` | Password set on the platform admin. |

### Determinism

| Variable | Type | Default | Purpose |
|---|---|---|---|
| `SEED_RANDOMIZER_KEY` | `int` | `42` | Seeds `random.Random`. Same key + same config = identical dataset every run. Change it to generate a different universe. |
| `SEED_UNIQUE_PASSWORDS` | `bool` | `False` | `False` gives all students the password `Student123!`. `True` generates a unique 12-character password per student (slower due to bcrypt). |
| `SEED_USER_SUFFIX_PROBABILITY` | `float` | `0.3` | Probability (0.0–1.0) that a generated name gets a generational suffix (Jr., Sr., II, III, IV). |

### Scale

| Variable | Type | Default | Purpose |
|---|---|---|---|
| `SEED_N_SCHOOLS` | `int` | `5` | Number of schools to generate. Capped at 21 (the size of the school name pool). |
| `SEED_MIN_COLLEGES` / `SEED_MAX_COLLEGES` | `int` | `3` / `8` | Range for how many colleges (departments) each school gets. |
| `SEED_MIN_PROGRAMS` | `int` | `1` | Minimum programs per college. |
| `SEED_MIN_STUDENTS` / `SEED_MAX_STUDENTS` | `int` | `50` / `250` | Range for student count per school. |
| `SEED_MIN_EVENTS` / `SEED_MAX_EVENTS` | `int` | `30` / `100` | Range for event count per school. |

Min/max pairs are swap-protected — passing `min > max` is silently corrected.

### Temporal window

| Variable | Type | Default | Purpose |
|---|---|---|---|
| `SEED_START_MMDDYY` | `tuple` | `(1, 1, 2024)` | Earliest date for generated events, as `(month, day, year)`. |
| `SEED_END_MMDDYY` | `tuple` | `(12, 31, 2026)` | Latest date for generated events. |

Events are distributed uniformly at random across this window. Whether an event ends up `COMPLETED`, `ONGOING`, `UPCOMING`, or `CANCELLED` is determined by comparing its generated datetime against the real wall-clock time at the moment the seeder runs.

### Output format

| Variable | Type | Default | Purpose |
|---|---|---|---|
| `SEED_CREDENTIALS_FORMAT` | `str` | `"csv"` | Format for credential output files. Options: `"csv"`, `"tsv"`, `"psv"`. |

## What Gets Generated

For each school, in dependency order:

1. **School + SchoolSetting** — name, code, branding colors
2. **Departments + Programs** — N colleges picked from a pool of 15, each with a random subset of their programs, linked via the many-to-many association table
3. **Campus admin** — one `campus_admin` user per school, credentials written to `campus_admin_credentials.{ext}`
4. **Governance hierarchy**
   - One SSG unit with full permissions
   - One SG unit per department, parented to the SSG, with department-scoped permissions
   - 0–2 ORG units per SG, with view/event/attendance permissions
   - 2–4 SSG announcements, 0–1 SG announcements per department (70% probability)
5. **Students** — weighted random program assignment (some programs get more students than others), unique student IDs in `{year}-{5-digit}` format, credentials written to `student_credentials.{ext}`
6. **Governance officers** — top ~15% of students become the leader pool; 3–5 are assigned as SSG officers, 1–3 per SG, 1–2 per ORG, with randomized per-member permission subsets. Officers can hold multiple roles simultaneously (hybrid overlay). Credentials written to `student_governance_credentials.{ext}`
7. **Student notes** — ~10% of students get a governance note from a random leader, with 1–2 tags from the tag pool
8. **Events** — random name, location, type, and duration (1–4 hours). Scope is weighted: 60% program-scoped, 25% department-scoped, 15% school-wide. Each event gets a sanction config with two items (apology letter + community fine)
9. **Event status (chaos engine)** — a per-run cancellation probability (2–7%) and emergency cutoff probability (10–25%) are rolled once at the start. Past events are mostly `COMPLETED`, some `CANCELLED`. Active events are `ONGOING`. Future events are `UPCOMING`. ~50% of events get a sanction delegation to a random SG unit
10. **Attendance** — generated only for events that have passed or are active. Gate probabilities: `COMPLETED` = 100%, `ONGOING` = 20–70%, emergency `CANCELLED` = 1–15%, pre-emptive `CANCELLED` / `UPCOMING` = 0%. Per student per event: 25% absent, 75% present/late (80/20 split)
11. **Sanctions** — created for every absent attendance record. ~30% are auto-resolved with `COMPLIED` status, compliance history, and a random compliance note. The remaining 70% stay `PENDING`

## Output Files

Written to `seeder/storage/seeder_outputs/` (gitignored):

| File | Contents |
|---|---|
| `campus_admin_credentials.{ext}` | School, role, email, password, name for each campus admin |
| `student_governance_credentials.{ext}` | Same for all SSG/SG/ORG officers |
| `student_credentials.{ext}` | Same for all regular students |

These files are the primary way to get login credentials after a seed run.

## Determinism and Reproducibility

The seeder uses a single `random.Random` instance seeded by `SEED_RANDOMIZER_KEY`. Every random decision — school selection, student names, program weights, event dates, attendance outcomes, sanction resolution — flows through this one RNG. Running with the same key and the same config produces byte-for-byte identical data, except for the event status classification which depends on wall-clock time.

To generate a completely different dataset, change `SEED_RANDOMIZER_KEY` to any other integer.

## File Layout

```
seeder/
├── seed.py              Entry point and CLI
├── config.py            Loads and validates variables.py before anything runs
├── variables.py         All configuration — edit this before running
└── modules/
    ├── config.py        Static data pools (names, schools, colleges, programs, events)
    ├── core.py          DB factory functions and lifecycle helpers (wipe, seed roles, etc.)
    ├── demo.py          Main orchestration — runs the full generation sequence per school
    └── helpers.py       Pure utilities: date generation, chunking, parallel bcrypt, etc.
```

## Relationship to `backend/app/seeder.py`

`backend/app/seeder.py` is the production bootstrap — it seeds only the minimum required for a live deployment: roles, global event types, and the platform admin account. It has no demo data, no randomization, and no wipe capability.

The `seeder/` directory here is entirely separate and additive. It calls the same database but builds on top of what the bootstrap already created. Running the demo seeder on a fresh database without running the bootstrap first will fail because the global `EventType` records won't exist.

## Docker

The seeder is not wired into any Docker service. Run it locally against a running database:

```powershell
# With the stack running
cd seeder
python seed.py demo
```

Or exec into the backend container if you prefer:

```powershell
docker compose exec backend bash
cd /app  # backend root is mounted here
# then adjust sys.path manually or run from repo root
```

Running directly from the host with the stack up is simpler.
