[← Back to Main README](../../README.md)

# Backend Large Data Seed Guide

## Purpose

This guide documents the dedicated Misamis University large-data seed script for generating one school with a heavy attendance and sanctions dataset for local or staging validation.

## Seed Entry Points

- `Backend/seed_misamis_university.py`
- `Backend/app/misamis_university_seeder.py`

## Default Dataset

Running the script with defaults creates:

- `1` school named `Misamis University`
- `1` `campus_admin` account for that school
- `15,000` student users with:
  - randomized names
  - randomized student IDs
  - randomized passwords
  - generated emails under `@misamisu.seed.edu.ph`
- `33` completed school events
- `1,000,000` total attendance rows
  - all seeded attendance rows use API-compatible `method='manual'`
- sanctions for every core absent attendance row
- pre-created governance structure with memberships and permissions:
  - `1` SSG unit
  - `5` SG units
  - `15` ORG units

## Important Attendance Volume Note

`1,000,000` attendance rows is implemented as:

- one core attendance row per seeded student per event
- additional duplicate history rows to reach the requested total volume exactly

This keeps:

- every student represented on every seeded event
- sanctions tied to the core absent record for each event
- enough attendance history volume for performance testing

## Governance and Sanctions Seeded

The seed script also prepares governance and sanctions data:

- one seeded SSG student member with full SSG member permissions
- one seeded SG member per department with SG member permissions
- one seeded ORG member per program with ORG member permissions
- matching `governance_unit_permissions` and `governance_member_permissions`
- `EventSanctionConfig` rows for every seeded event
- `SanctionRecord` rows for every core absent attendance row
- `SanctionItem` rows for each sanction record
- SG delegations on a subset of school-wide events so SG members have delegated sanction coverage immediately

## Password Hashing

The script accepts a configurable bcrypt cost for bulk seed speed:

- default: `--password-hash-rounds 6`
- helper updated: `app.utils.passwords.hash_password_bcrypt(password, *, rounds=...)`

This lower default is intended for large non-production seed runs where insertion time matters more than password hash cost.

## Credentials Artifacts

By default the script writes:

- `storage/seed_outputs/misamis_university_credentials.csv`
- `storage/seed_outputs/misamis_university_privileged_credentials.csv`
- `storage/seed_outputs/misamis_university_seed_summary.json`

The privileged CSV contains the campus admin plus the seeded SSG, SG, and ORG member accounts.

## Prerequisites

Before running the seed:

1. Apply backend migrations so the schema and enum types already exist.
2. Point `DATABASE_URL` at the target database.
3. Make sure the target database can handle a large write workload.

The script checks for required tables and fails fast if the migrated schema is missing.

## How To Run

Dry run:

- `python Backend/seed_misamis_university.py --dry-run`

Default full seed:

- `python Backend/seed_misamis_university.py`

Recreate the Misamis University dataset if it already exists:

- `python Backend/seed_misamis_university.py --replace-existing`

Override counts or hashing:

- `python Backend/seed_misamis_university.py --student-count 15000 --event-count 33 --attendance-target 1000000 --password-hash-rounds 6`

## How To Test

1. Run a dry run first:
   - `python Backend/seed_misamis_university.py --dry-run`
2. Run the seed against a migrated database:
   - `python Backend/seed_misamis_university.py`
3. Verify generated counts in SQL:
   - `SELECT COUNT(*) FROM schools WHERE school_name = 'Misamis University';`
   - `SELECT COUNT(*) FROM student_profiles WHERE school_id = <school_id>;`
   - `SELECT COUNT(*) FROM events WHERE school_id = <school_id>;`
   - `SELECT COUNT(*) FROM attendances a JOIN events e ON e.id = a.event_id WHERE e.school_id = <school_id>;`
   - `SELECT COUNT(*) FROM sanction_records WHERE school_id = <school_id>;`
4. Check the generated credential files under `storage/seed_outputs/`.
5. Login with the campus admin or one of the privileged governance users from the privileged CSV and verify the reports, governance, and sanctions screens load against the seeded dataset.
