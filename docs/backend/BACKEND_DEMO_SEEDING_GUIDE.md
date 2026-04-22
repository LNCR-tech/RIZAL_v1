[<- Back to docs index](../../README.md)

# Backend Demo Seeding Guide (Production Grade)

Aura v3 includes a high-fidelity stochastic data engine designed to stress-test governance permissions, attendance reports, and AI assistant reasoning.

## Core Architecture

The new seeder is located in the root `/seeder` directory and is designed to be environment-agnostic. It works by generating a deterministic "Universe" based on your configured RNG seed.

### Key Logic
- **Hybrid Roles**: The seeder automatically assigns multiple governance roles (SSG, SG, ORG) to natural student leaders (top 15% of the population).
- **Stochastic Distribution**: College structures, program counts, and student populations are randomized within your defined ranges.
- **Deterministic RNG**: Using a fixed `SEED_RANDOMIZER_KEY` ensures that every developer on the team gets the exact same database state.

## Environment Configuration

All toggles are read from your root `.env`.

### Performance & Safety
- `SEED_DATABASE` (Required: `true`)
  - The master kill switch. If `false`, the script will exit without making changes.
- `SEED_WIPE_EXISTING` (Default: `false`)
  - Set to `true` to perform a clean-slate seed. **WARNING**: This deletes all existing records except the Platform Admin.
- `SEED_RANDOMIZER_KEY` (Default: `42`)
  - Change this to generate a completely different universe.

### Platform Admin
- `SEED_ADMIN_EMAIL`: The email for the global Platform Admin.
- `SEED_ADMIN_PASSWORD`: The password for the global Platform Admin (will be hashed with Bcrypt).

### Population Controls
- `SEED_N_SCHOOLS`: Total number of schools to generate.
- `SEED_MIN_STUDENTS` / `SEED_MAX_STUDENTS`: Range of students per school.
- `SEED_MIN_COLLEGES` / `SEED_MAX_COLLEGES`: Range of academic departments per school.
- `SEED_USER_SUFFIX_PROBABILITY`: Probability (0.0 to 1.0) of appending a numeric suffix to usernames to test name collision edge cases.

## How To Execute

### 1. Unified CLI (Recommended)
From the repository root, run:

```powershell
python seeder/seed.py demo
```

### 2. Docker Orchestration
If running via Docker Compose, the `seed` service will automatically trigger the seeder if `SEED_DATABASE=true` is found in your `.env`.

## Credential Outputs

The seeder generates specialized credential files in the following directory:
`storage/seeder_outputs/`

| File Name | Description |
| :--- | :--- |
| `campus_admin_credentials` | Logins for Campus Administrators (School-level). |
| `student_governance_credentials` | Logins for SSG, SG, and ORG leaders with mixed permissions. |
| `student_credentials` | Logins for the general student population. |

### Format Toggle
You can change the file format via `SEED_CREDENTIALS_FORMAT` (`csv`, `tsv`, or `psv`).

## Verification Flow

1. Set `SEED_DATABASE=true` in your `.env`.
2. Run `python seeder/seed.py demo`.
3. Check `storage/seeder_outputs/student_governance_credentials.csv`.
4. Log in as a student leader and open the **Aura Assistant**.
5. Ask: *"What are my current governance permissions?"* to verify the stochastic role hybridization.
