# Ports and URLs

<!--nav-->
[← Environment Variables](env.md) | [🏠 Home](/README.md) | [Repository Layout →](repository-layout.md)

---
<!--/nav-->

These are the defaults from `docker-compose.yml`.

## Local (Docker)

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
  - OpenAPI docs: `http://localhost:8000/docs`
  - OpenAPI docs via frontend proxy: `http://localhost:5173/__backend__/docs`
- Assistant:
  - OpenAPI docs: `http://localhost:8500/docs`
  - Health: `http://localhost:8500/health`
- pgAdmin: `http://localhost:5050`
- Log viewer: `http://localhost:8088`
- Postgres: `localhost:5433` on the host and `db:5432` inside the Docker network
- Redis: `localhost:6379`

## Local (Manual / No Docker)

- Frontend dev server: `http://localhost:5173`
- Backend API: `http://127.0.0.1:8000`
  - OpenAPI docs: `http://127.0.0.1:8000/docs`
- Assistant v2: `http://127.0.0.1:8500`
  - Health: `http://127.0.0.1:8500/health`
  - OpenAPI docs: `http://127.0.0.1:8500/docs`

## Notes

- `5433` is used in Docker to avoid conflicts with a local Postgres already bound to `5432`.
- `8088` is used by the local log viewer, which reads container stdout/stderr through the read-only Docker socket mount.
- The frontend reverse-proxies:
  - `/__backend__/...` to the backend origin
  - `/__assistant__/...` to the assistant origin
