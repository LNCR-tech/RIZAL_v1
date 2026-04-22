# Environment Variables

[<- Back to docs index](../../README.md)

## Source of Truth

- Use `.env.example` as the authoritative list of supported keys and defaults.
- Backend settings are parsed in `Backend/app/core/config.py`.
- Frontend runtime configuration is injected via `Frontend/runtime-config.js.template` and Docker/NGINX templates.

## Minimum Local Setup (Docker)

Copy `.env.example` to `.env` and set at least:

- `SECRET_KEY`, `JWT_SECRET`
- `SEED_DATABASE=true` (If you want to initialize demo data)
- `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD` (For platform admin creation)
- Assistant / AI:
  - `AI_MODEL`, `AI_API_BASE`, `AI_API_KEY`

Then run the Docker stack. See: [Getting Started (Docker)](../getting-started/docker.md).

## Seeding & Development

The following variables govern the stochastic data engine:

- `SEED_RANDOMIZER_KEY`: Master seed for 100% deterministic, reproducible runs.
- `SEED_WIPE_EXISTING`: If true, wipes existing records before seeding.
- `SEED_N_SCHOOLS`: Number of schools to generate.
- `SEED_USER_SUFFIX_PROBABILITY`: Probability of adding a random suffix to usernames (test collisions).
- `SEED_CREDENTIALS_FORMAT`: `csv` | `tsv` | `psv` (Output format for generated logins).

See: [Backend Demo Seeding Guide](../backend/BACKEND_DEMO_SEEDING_GUIDE.md).

## Minimum Local Setup (No Docker)

When running services manually, you will also need DB connection strings (see `.env.example` "MANUAL SETUP" section), notably:

- `DATABASE_URL`
- `DATABASE_ADMIN_URL`
- `ASSISTANT_DB_URL`
- `TENANT_DATABASE_URL`
- `APP_DATABASE_URL`

See: [Getting Started (Local Dev)](../getting-started/local-dev.md).


