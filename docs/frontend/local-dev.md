# Frontend Local Dev

<!--nav-->
[← Frontend Docs](README.md) | [🏠 Home](/README.md) | [Frontend Configuration →](configuration.md)

---
<!--/nav-->

## Install and Run

```powershell
cd .\\frontend
npm ci
npm run dev
```

Vite will print the dev URL (default `http://localhost:5173`).

## Env File For Vite Dev

Use `frontend/.env.development.local` for manual frontend development.

Start from the tracked example:

```powershell
Copy-Item .\.env.development.local.example .\.env.development.local -Force
```

Required local value:

- `VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8000`

Optional local values:

- `VITE_API_BASE_URL=/__backend__`
- `VITE_API_TIMEOUT_MS=15000`
- `VITE_NATIVE_API_BASE_URL=http://127.0.0.1:8000` for native/mobile builds
- `VITE_ASSISTANT_PROXY_TARGET=http://127.0.0.1:8500`
- `VITE_ASSISTANT_BASE_URL=http://127.0.0.1:8500`

Assistant note:

- these assistant env vars still exist and are part of local frontend configuration
- the current Vite config only defines a backend proxy under `/__backend__`

## Backend Connectivity (Dev)

The current Vite dev server proxies backend requests through `/__backend__`.

Details and the exact environment variables are documented in: [Frontend configuration](./configuration.md).
