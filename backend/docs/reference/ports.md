# Ports and URLs

<!--nav-->
[Previous](env.md) | [Next](repository-layout.md) | [Home](/README.md)

---
<!--/nav-->

These are the defaults from `docker-compose.yml`.

## Local (Docker)

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8001`
  - OpenAPI docs: `http://localhost:8001/docs`
  - OpenAPI docs via frontend proxy: `http://localhost:5173/__backend__/docs`
- Assistant:
  - OpenAPI docs: `http://localhost:8500/docs`
  - Health: `http://localhost:8500/health`
- pgAdmin: `http://localhost:5050`
- Log viewer: `http://localhost:8080`
- Postgres: `postgres:5432` inside the Docker network; not published to the host by default
- Redis: `redis:6379` inside the Docker network; not published to the host by default

## Local (Manual / No Docker)

- Frontend dev server: `http://localhost:5173`
- Backend API: `http://127.0.0.1:8000`
  - OpenAPI docs: `http://127.0.0.1:8000/docs`
- Assistant v2: `http://127.0.0.1:8500`
  - Health: `http://127.0.0.1:8500/health`
  - OpenAPI docs: `http://127.0.0.1:8500/docs`

## Notes

- `8001` is used for the backend host port so it can run beside stacks that already publish `8000`.
- `8080` is used by the local log viewer, which reads container stdout/stderr through the read-only Docker socket mount.
- The frontend reverse-proxies:
  - `/__backend__/...` to the backend origin
  - `/__assistant__/...` to the assistant origin

