[<- Back to docs index](../../README.md)

# Backend Demo Seeding Guide

The backend now uses two explicit data-entry commands:

- `Backend/bootstrap.py` for the minimum production baseline
- `Backend/seed.py` for demo and local-development data

`SEED_*` env toggles are no longer the supported way to control seeding.

## Production Bootstrap

Create only:

- the first platform admin
- the default school
- the default school settings record
- core roles

Example:

```powershell
python Backend/bootstrap.py `
  --admin-email admin@example.com `
  --admin-password ChangeMe123! `
  --school-name "Aura University" `
  --school-code VU-001 `
  --school-address "1 Demo Way"
```

The command is idempotent:

- existing roles are reused
- the default school is reused
- the admin account is repaired if it already exists under the requested email

## Demo Seed

The demo seeder always bootstraps the baseline first, then adds demo schools, users, departments, programs, governance units, and credentials CSV output.

Example:

```powershell
python Backend/seed.py `
  --wipe-existing `
  --schools 5 `
  --users 100 `
  --email-domain demo.aura.dev
```

Large dataset example:

```powershell
python Backend/seed.py `
  --wipe-existing `
  --massive-attendance `
  --massive-students 5000 `
  --massive-records 1000000
```

## Credentials Output

By default the demo seed writes generated credentials to:

- `Backend/storage/seed_credentials.csv`

Override the output path when needed:

```powershell
python Backend/seed.py --credentials-path .\tmp\seed_credentials.csv
```

## Default Values

Default bootstrap and demo seed values now come from:

- `Backend/app/core/app_settings.py`

That file controls defaults such as:

- default school name/code/address
- default admin email/password
- demo school and user counts
- demo email domain
- large-dataset student and attendance counts

## How to Test

1. Run migrations:
   - `python -m alembic upgrade head`
2. Run production bootstrap:
   - `python Backend/bootstrap.py --admin-email admin@example.com --admin-password ChangeMe123!`
3. Run demo seed:
   - `python Backend/seed.py --schools 2 --users 20 --email-domain demo.example.test`
4. Verify `Backend/storage/seed_credentials.csv` was created.
5. Run:
   - `pytest Backend/app/tests/test_seeder.py`
