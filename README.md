# Vue 3 + Vite

This template should help get you started developing with Vue 3 in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about IDE Support for Vue in the [Vue Docs Scaling up Guide](https://vuejs.org/guide/scaling-up/tooling.html#ide-support).

## Docker

This repo ships with a production-style Docker setup so the frontend can be demoed consistently without relying on a local Node install.

### Files

- `Dockerfile`
  Builds the Vue app with Vite, then serves the built files from Nginx.
- `docker-compose.yml`
  Starts the demo container and maps the app to a local port.
- `nginx.conf.template`
  Handles SPA routing and proxies backend requests from `/__backend__` to the configured backend origin.
- `.env.docker.example`
  Example runtime configuration for Docker.

### Container

- `aura-web`
  Serves the built Aura frontend on port `80`, keeps Vue Router working with `try_files`, and forwards API requests to the external backend through `/__backend__`.

### Start

1. Copy `.env.docker.example` to `.env.docker`.
2. Set `BACKEND_ORIGIN` to the backend root URL.
   Use the host root, not the `/api` suffix.
   Example: `https://your-ngrok-host.ngrok-free.dev`
3. Run:

```bash
docker compose --env-file .env.docker up --build -d
```

4. Open:

```text
http://localhost:8080
```

### Stop

```bash
docker compose --env-file .env.docker down
```

### Health Check

The container exposes a simple health endpoint at `/healthz` for Docker health checks.
