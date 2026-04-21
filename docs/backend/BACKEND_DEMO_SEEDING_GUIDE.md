# Backend Demo Seeding Guide (Manual UI + Assistant Testing)

This repo includes a demo seeder that creates multiple schools and users so you can test:
- UI role behavior (admin vs campus admin vs student)
- AI assistant behavior per JWT `roles` + `permissions`

## What It Seeds

When you run `python Backend/seed.py`, the seeder will (by default):
- ensure core auth roles exist (`admin`, `campus_admin`, `student`)
- create a default school + admin (existing behavior)
- create demo data:
  - 5 sample schools
  - 100 sample users (platform admins, campus admins, students)
  - departments/programs per school
  - governance units (SSG/SG/ORG) + governance member permissions for a subset of users

## Environment Toggles

All toggles are read from your normal env loading (`.env` is used by `seed.py`).

- `SEED_DEMO_DATA` (default: `true`)
  - set to `false` to disable demo seed.
- `SEED_DEMO_SCHOOLS` (default: `5`)
- `SEED_DEMO_USERS` (default: `100`)
- `SEED_DEMO_EMAIL_DOMAIN` (default: `demo.valid8.dev`)
  - used for all generated demo emails (avoid special-use domains like `.local` which may fail strict validation).

## Where Credentials Go

The seeder writes a local CSV file (gitignored) containing demo login credentials:

- `Backend/storage/seed_credentials.csv`

Re-running the seeder will reset passwords for the `@demo.local` accounts so the CSV stays accurate.

Columns:
- `email`
- `password`
- `school_code`, `school_id`
- `roles` (includes derived governance roles: `ssg`, `sg`, `org` when applicable)
- `permissions` (governance permission codes like `manage_students`, `manage_attendance`, etc)

## How To Use For Assistant Testing

1. Run migrations, then seed:
   - `python -m alembic upgrade head`
   - `python Backend/seed.py`
2. Start backend + assistant + frontend.
3. Pick a user from `Backend/storage/seed_credentials.csv`, log into the UI.
4. Open the in-app Aura AI chat.

The assistant reads `roles` and `permissions` from the backend JWT, so different demo users will get different MCP access policies.
