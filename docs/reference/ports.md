# Ports and URLs

[<- Back to docs index](../../README.md)

These are the defaults from `docker-compose.yml` (and the root README).

## Local (Docker)

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
  - OpenAPI docs: `http://localhost:8000/docs`
  - OpenAPI docs (via frontend proxy): `http://localhost:5173/__backend__/docs`
- Assistant (not published on host by default):
  - OpenAPI docs (via frontend proxy): `http://localhost:5173/__assistant__/docs`
  - Health (via frontend proxy): `http://localhost:5173/__assistant__/health`
- pgAdmin: `http://localhost:5050` (default login `admin@example.com` / `admin123`)
- Mailpit (email inbox): `http://localhost:8025`
- Postgres (host-exposed): `localhost:5433` (inside Docker network it is `db:5432`)
- Redis: `localhost:6379`

## Local (Manual / No Docker)

These are the defaults used in the docs and common commands:

- Frontend dev server: `http://localhost:5173`
- Backend API: `http://127.0.0.1:8000`
  - OpenAPI docs: `http://127.0.0.1:8000/docs`
- Assistant (v2 default): `http://127.0.0.1:8500`
  - Health: `http://127.0.0.1:8500/health`
  - OpenAPI docs: `http://127.0.0.1:8500/docs`

## Notes

- `5433` is used to avoid conflicts with a locally installed Postgres on `5432`.
- The frontend reverse-proxies:
  - `/__backend__/...` to the backend origin
  - `/__assistant__/...` to the assistant origin
  See [Frontend configuration](../frontend/configuration.md).

