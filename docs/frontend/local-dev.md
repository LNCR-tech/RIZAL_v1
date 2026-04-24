# Frontend Local Dev

[<- Back to frontend index](./README.md)

## Install and Run

```powershell
cd .\\frontend
npm ci
npm run dev
```

Vite will print the dev URL (default `http://localhost:5173`).

## Dev Defaults (`.env.development`)

This repo includes `frontend/.env.development` so `npm run dev` works out of the box:

- `VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8000`
- `VITE_ASSISTANT_PROXY_TARGET=http://127.0.0.1:8500`
- `VITE_ASSISTANT_BASE_URL=http://127.0.0.1:8500` (bypasses proxy to avoid SSE buffering issues)

## Backend/Assistant Connectivity (Dev)

There are two common ways to point the frontend at the backend/assistant during dev:

1. Use the Vite proxy and keep app URLs relative.
2. Use absolute URLs (useful for native/Android builds).

Details and the exact environment variables are documented in: [Frontend configuration](./configuration.md).
