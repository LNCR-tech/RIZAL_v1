# Chapter 11 â€” Running the Seeder

<!--nav-->
[Previous](10-sanctions.md) | [Next](12-output.md) | [Home](/README.md)

---
<!--/nav-->

---

## 11.1 Prerequisites

Before running the seeder:

1. Alembic migrations must be applied: `cd backend && python -m alembic upgrade head`
2. Bootstrap must have run: `cd backend && python bootstrap.py`
3. `DATABASE_URL` must be set in the root `.env`
4. Backend dependencies must be installed: `pip install -r backend/requirements.txt`

The seeder must be run from inside the `seeder/` directory so its relative module imports resolve correctly.

---

## 11.2 Enable the Seeder

Open `seeder/variables.py` and set:

```python
SEED_DATABASE: bool = True
```

The seeder will not run if this is `False`.

---

## 11.3 Manual Run

```powershell
cd seeder
python seed.py demo
```

With CLI overrides:

```powershell
python seed.py demo --schools 3 --min-students 500 --max-students 1000
python seed.py demo --start-mmddyy 1,1,2025 --end-mmddyy 12,31,2025
python seed.py demo --credentials-format tsv
```

---

## 11.4 Docker Run

The `seed` service in `docker-compose.yml` runs automatically when `SEED_DATABASE = True` in `variables.py`. It runs after `bootstrap` completes and before `backend` starts.

To trigger it:

1. Set `SEED_DATABASE = True` in `seeder/variables.py`
2. Run `docker compose up --build`

The seeder service mounts the entire repo root at `/repo` so both `backend/` and `seeder/` are accessible inside the container.

---

## 11.5 Re-Running

The seeder is safe to re-run. With `SEED_WIPE_EXISTING = True` (default), it truncates all seeded tables before inserting, producing a clean dataset every time.

With `SEED_WIPE_EXISTING = False`, the seeder is additive â€” it skips records that already exist (get-or-create pattern). This is useful for adding more schools to an existing dataset without wiping what's already there.

---

## 11.6 Interruption

If the seeder is interrupted with `Ctrl+C`, it rolls back the current transaction and exits cleanly:

```python
except KeyboardInterrupt:
    logger.warning("\nSeeding interrupted by user.")
    db.rollback()
    sys.exit(1)
```

Because commits are issued per school and per attendance chunk, an interruption mid-school will leave the database in a partially seeded state for that school. Re-running with `SEED_WIPE_EXISTING = True` will clean this up.

---

## 11.7 Performance Expectations

With default settings (5 schools, 1,000â€“2,000 students, 30â€“100 events):

| Phase | Approximate time |
|---|---|
| Config validation | < 1 second |
| Table wipe | 1â€“3 seconds |
| Roles + permissions | < 1 second |
| Per school: academic structure | 1â€“2 seconds |
| Per school: students (bcrypt, rounds=6) | 5â€“15 seconds |
| Per school: events | 1â€“3 seconds |
| Per school: attendance + sanctions | 10â€“30 seconds |
| **Total (5 schools)** | **~3â€“5 minutes** |

The dominant cost is bcrypt hashing for student passwords. With `SEED_UNIQUE_PASSWORDS = False` (default), all students share one hash, so this cost is negligible. With `SEED_UNIQUE_PASSWORDS = True`, hashing 10,000 students at `rounds=6` with 10 workers takes approximately 30â€“60 seconds.

The second dominant cost is the attendance + sanctions phase, which involves large batch inserts. The chunk size of 2,000 is tuned to balance memory and throughput.

