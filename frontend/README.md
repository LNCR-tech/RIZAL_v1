# Frontend

This app supports three configuration paths, and each path uses a different env file.

## Env Files

- `frontend/.env.development.local`
  Manual Vite dev only. Keep this untracked and machine-specific.
- `frontend/.env.development.local.example`
  Tracked template for local Vite dev.
- `frontend/.env.docker`
  Standalone frontend Docker flow inside `frontend/` only.
- `frontend/.env.docker.example`
  Tracked template for the standalone frontend Docker flow.
- Root `.env`
  Repo-root Docker Compose, backend, assistant, and worker/beat settings.

## Manual Vite Dev

1. Copy `.env.development.local.example` to `.env.development.local`.
2. Update the backend URL if needed.
3. Run:

```bash
npm ci
npm run dev
```

Required local value:

```env
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8000
```

Optional local values:

```env
VITE_API_BASE_URL=/__backend__
VITE_API_TIMEOUT_MS=15000
VITE_NATIVE_API_BASE_URL=http://127.0.0.1:8000
```

## Standalone Frontend Docker

1. Copy `.env.docker.example` to `.env.docker`.
2. Set `BACKEND_ORIGIN` to the backend root URL.
3. Run:

```bash
docker compose --env-file .env.docker up --build -d
```

4. Open `http://localhost:8080`.

## Repo-Root Docker Compose

Do not edit `frontend/.env.docker` for the normal full-stack repo-root Docker flow.

Use the root `.env` and run:

```bash
docker compose up --build
```

## Runtime Behavior

The frontend resolves backend configuration in this order:

1. `window.__AURA_RUNTIME_CONFIG__`
2. `VITE_*` values loaded by Vite
3. built-in defaults such as `/__backend__`
