# Frontend Architecture

[<- Back to frontend index](./README.md)

## Folder Map (`frontend/src`)

- `assets/`: global styles and static assets.
- `components/`: reusable UI components.
- `composables/`: reusable composition utilities (session bootstrap, etc).
- `config/`: theme and static configuration helpers.
- `layouts/`: layout shells (for authenticated routes).
- `router/`: Vue Router setup and route guards.
- `services/`: API clients, integration helpers, and cross-cutting services.
- `stores/`: Pinia stores.
- `views/`: route-level views.

## Routing

Routes are defined in `frontend/src/router/index.js`.

## API Base URL Resolution

The backend and assistant base URLs are resolved in:

- `frontend/src/services/backendBaseUrl.js`
- `frontend/src/services/assistantBaseUrl.js`

These read from (in priority order):

- explicit overrides passed by callers
- `window.__AURA_RUNTIME_CONFIG__` (Docker/NGINX)
- `import.meta.env.VITE_*` variables (Vite builds)

