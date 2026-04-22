[<- Back to docs index](../../README.md)

# Backend Large Data Seed Guide

The Aura Seeder supports high-performance data generation designed for stress-testing the report engine and database performance. It can generate tens of thousands of records naturally via stochastic density controls.

## Execution Entry Point

All seeding operations now run through the unified CLI:

```powershell
python seeder/seed.py demo
```

Seeding volume is driven by the density of students and events configured in your `.env`.

## Massive Environment Configuration

### Target Populations
- `SEED_MIN_STUDENTS` / `SEED_MAX_STUDENTS`: Student population per school.
- `SEED_MIN_EVENTS` / `SEED_MAX_EVENTS`: Range for randomized event generation.
- `SEED_N_SCHOOLS`: Total number of schools to generate.

### Temporal Engine (The New Format)
Legacy year/month toggles have been replaced by a unified "MM,DD,YYYY" window:

- `SEED_START_MMDDYY`: The beginning of the attendance window (e.g., `1,1,2024`).
- `SEED_END_MMDDYY`: The end of the attendance window (e.g., `12,31,2026`).

The seeder will stochastically distribute events and attendances proportionally within this specific window.

## Sanction Universe

Massive mode automatically generates a linked "Sanction Universe" derived from the attendance data:
- **Major Events**: Approx 10% of generated events are flagged as major assemblies.
- **Auto-Sanctions**: Students with `ABSENT` statuses for these events receive a `SanctionRecord`.
- **Integrity**: Every `SanctionRecord` is explicitly linked to its triggering `Attendance` record via `attendance_id`.

## High-Performance Features

### 1. Bulk Insertion Logic
The seeder utilizes `db.bulk_insert_mappings` for attendance and sanction records, bypassing SQLAlchemy ORM overhead to handle hundreds of thousands of rows in seconds.

### 2. Multi-Threaded Hashing
When `SEED_UNIQUE_PASSWORDS=true`, the seeder utilizes available CPU cores (`ProcessPoolExecutor`) to pre-hash thousands of passwords in parallel.

### 3. Deterministic RNG
The `SEED_RANDOMIZER_KEY` controls the entire universe. Changing this key will change the IDs, names, and event distributions while maintaining the requested volumes.

## massive Stress Test Example (.env)

```env
SEED_DATABASE=true
SEED_WIPE_EXISTING=true
SEED_MIN_STUDENTS=500
SEED_MAX_STUDENTS=1000
SEED_MIN_EVENTS=100
SEED_MAX_EVENTS=200
SEED_N_SCHOOLS=10
SEED_RANDOMIZER_KEY=42
SEED_START_MMDDYY=1,1,2024
SEED_END_MMDDYY=12,31,2025
```

## Verification

After seeding, verify cumulative counts via SQL:

```sql
SELECT (SELECT COUNT(*) FROM student_profiles) AS students,
       (SELECT COUNT(*) FROM events) AS events,
       (SELECT COUNT(*) FROM attendances) AS attendances,
       (SELECT COUNT(*) FROM sanction_records) AS sanctions;
```
