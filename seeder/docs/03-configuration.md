# Chapter 3 â€” Configuration System

<!--nav-->
[Previous](02-architecture.md) | [Next](04-rng.md) | [Home](/README.md)

---
<!--/nav-->

---

## 3.1 Overview

All seeder configuration lives in `seeder/variables.py`. Edit it directly before running. There are no environment variables, no `.env` files, and no CLI flags required for basic use â€” though CLI flags can override `variables.py` values for a single run.

`config.py` validates `variables.py` on startup and exits with a clear error message if anything is wrong, before touching the database.

---

## 3.2 Full Variable Reference

### Safety Gate

| Variable | Type | Default | Description |
|---|---|---|---|
| `SEED_DATABASE` | `bool` | `False` | Must be `True` to run. The primary safety gate against accidental execution. |
| `SEED_WIPE_EXISTING` | `bool` | `True` | If `True`, truncates all seeded tables before inserting. Safe to re-run. If `False`, the seeder is additive â€” it will skip records that already exist (get-or-create pattern). |

### Platform Admin

| Variable | Type | Default | Description |
|---|---|---|---|
| `SEED_ADMIN_EMAIL` | `str` | `admin@aura.com` | Email for the platform admin account. Created if missing, preserved on wipe. |
| `SEED_ADMIN_PASSWORD` | `str` | `AdminPass123!` | Password set on the platform admin. Hashed with bcrypt at rounds=12. |

### Determinism

| Variable | Type | Default | Description |
|---|---|---|---|
| `SEED_RANDOMIZER_KEY` | `int` | `42` | Seeds `random.Random`. Same key + same config = identical dataset every run. Change to generate a different universe. |
| `SEED_UNIQUE_PASSWORDS` | `bool` | `False` | `False` gives all students the password `Student123!`. `True` generates a unique 12-character alphanumeric password per student (significantly slower due to bcrypt). |
| `SEED_USER_SUFFIX_PROBABILITY` | `float` | `0.3` | Probability (0.0â€“1.0) that a generated name gets a generational suffix (Jr., Sr., II, III, IV). |

### Scale

| Variable | Type | Default | Description |
|---|---|---|---|
| `SEED_N_SCHOOLS` | `int` | `5` | Number of schools to generate. Hard-capped at 21 (the size of the school name pool in `data.py`). |
| `SEED_MIN_COLLEGES` / `SEED_MAX_COLLEGES` | `int` | `3` / `8` | Range for how many colleges (departments) each school gets. Actual count is `rng.randint(min, max)`. |
| `SEED_MIN_PROGRAMS` | `int` | `1` | Minimum programs per college. The maximum is the full program list for that college in `data.py`. |
| `SEED_MIN_STUDENTS` / `SEED_MAX_STUDENTS` | `int` | `1000` / `2000` | Range for student count per school. |
| `SEED_MIN_EVENTS` / `SEED_MAX_EVENTS` | `int` | `30` / `100` | Range for event count per school. |

Min/max pairs are swap-protected in `seed.py` â€” if you accidentally set `min > max`, they are silently corrected before being passed to `run_demo()`.

### Temporal Window

| Variable | Type | Default | Description |
|---|---|---|---|
| `SEED_START_MMDDYY` | `tuple` | `(1, 1, 2024)` | Earliest date for generated events, as `(month, day, year)`. |
| `SEED_END_MMDDYY` | `tuple` | `(12, 31, 2026)` | Latest date for generated events. |

`config.py` validates that `SEED_START_MMDDYY` is not later than `SEED_END_MMDDYY` and rejects the configuration if it is.

### Output Format

| Variable | Type | Default | Description |
|---|---|---|---|
| `SEED_CREDENTIALS_FORMAT` | `str` | `"csv"` | Format for credential output files. Options: `"csv"`, `"tsv"`, `"psv"`. |

---

## 3.3 Validation Rules

`config.py` enforces the following before the seeder starts:

- `variables.py` must exist at `seeder/variables.py`
- `variables.py` must be syntactically valid Python
- Every variable must be present and of the correct type
- `SEED_N_SCHOOLS` â‰¥ 1
- `SEED_MIN_COLLEGES`, `SEED_MAX_COLLEGES`, `SEED_MIN_PROGRAMS` â‰¥ 1
- `SEED_MIN_STUDENTS`, `SEED_MAX_STUDENTS`, `SEED_MIN_EVENTS`, `SEED_MAX_EVENTS` â‰¥ 0
- `SEED_USER_SUFFIX_PROBABILITY` âˆˆ [0.0, 1.0]
- `SEED_CREDENTIALS_FORMAT` âˆˆ `{"csv", "tsv", "psv"}`
- `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD` must not be empty strings
- Each date tuple must be `(month, day, year)` with valid calendar ranges
- Start date must not be later than end date

All errors are collected and printed together in a single message, so you can fix everything in one edit.

---

## 3.4 CLI Overrides

All scale and temporal parameters can be overridden per-run via CLI flags without editing `variables.py`:

```bash
python seed.py demo --schools 3 --min-students 100 --max-students 500
python seed.py demo --start-mmddyy 1,1,2025 --end-mmddyy 6,30,2025
python seed.py demo --credentials-format tsv
```

CLI flags take precedence over `variables.py` for that run only. `SEED_DATABASE`, `SEED_WIPE_EXISTING`, `SEED_RANDOMIZER_KEY`, `SEED_UNIQUE_PASSWORDS`, and `SEED_USER_SUFFIX_PROBABILITY` cannot be overridden via CLI â€” edit `variables.py` for those.

