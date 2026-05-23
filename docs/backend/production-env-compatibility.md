# Production Environment Compatibility

Production deployments accept both the current backend environment names and
the legacy names used by the existing VPS `.env.production`.

## Supported aliases

- `DEFAULT_ADMIN_EMAIL` can be provided as `ADMIN_EMAIL`.
- `DEFAULT_ADMIN_PASSWORD` can be provided as `ADMIN_PASSWORD`.
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` can be derived during
  deploy from `DB_USER`, `DB_PASSWORD`, and `DB_NAME`.
- `DATABASE_URL` is generated during deploy when it is missing, using the
  production Compose database service name `db`.

## Runtime behavior

`deploy.sh` and `rollback.sh` export the derived database values before running
Docker Compose, so the existing server `.env.production` can continue using the
legacy `DB_*` names. The backend settings loader also reads `ADMIN_EMAIL` and
`ADMIN_PASSWORD` as fallbacks for bootstrap.

Login remains available when optional session tracking, login history, or user
security preference writes are unavailable on an older database. In that case,
`POST /token` still returns a bearer token for valid credentials, falls back to
the normal token lifetime for `remember_me`, and skips optional privileged MFA
preference checks instead of returning HTTP 500.

## How to test

Run the production Compose validation with a production-style env file:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml config --quiet
```

For a backend-only deploy rehearsal on the VPS:

```bash
DEPLOY_SCOPE=backend DB_SERVICE=db ./deploy.sh
```

To verify login behavior after deployment, call `POST /token` with a valid
existing account and confirm it returns a bearer token instead of HTTP 500.
