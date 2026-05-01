# Architecture Diagrams

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Rule:** Only keep diagrams that can be verified against code, compose files, or schema docs.

---

## Purpose

This page is the index for architecture diagrams used in the project. It exists to prevent vague, outdated, or duplicate diagrams.

## Current Diagram Inventory

| Diagram | Primary location | Must match | Update trigger |
|---|---|---|---|
| System container topology | [system-architecture.md](./system-architecture.md) | `docker-compose.yml`, `docker-compose.prod.yml` | Service, port, dependency, or deployment change |
| Backend request and worker flow | [backend-structure.md](./backend-structure.md) | `Backend/app/main.py`, `Backend/app/core/`, `Backend/app/routers/`, `Backend/app/services/`, `Backend/app/workers/` | Router, service, or worker-path change |
| Frontend route and UI structure | [frontend-structure.md](./frontend-structure.md) | `Frontend/src/App.tsx`, `Frontend/src/api/`, `Frontend/src/components/`, `Frontend/src/dashboard/`, `Frontend/src/pages/` | Route, guard, page, or API-module change |
| ERD | [ERDv2.md](../ERD/ERDv2.md) | Backend models, migrations, and `aura_db.png` | Table, relationship, or schema change |
| ERD reading guide | [ERDGuide.md](../ERD/ERDGuide.md) | ERD v2 and database docs | Domain grouping or explanation change |
| API authentication flow | [authentication.md](../api/authentication.md) | `Backend/app/routers/auth.py`, `Frontend/src/api/authApi.ts`, related auth pages | Login, password, or session-flow change |

## Diagram Standards

- Prefer Mermaid for diagrams stored inside Markdown.
- Keep the diagram close to the feature doc that owns it, then register it here.
- Use actual module, route, and service names from the codebase.
- If a diagram no longer matches the implemented system, update it immediately or mark it obsolete.
- Do not keep "future-state" architecture diagrams in place of current implemented architecture.

## Minimum Verification Checklist

Before keeping or adding an architecture diagram, verify:

- service names and ports match the compose files
- route names match `Frontend/src/App.tsx` and backend router modules
- worker paths match `Backend/app/workers/`
- database entities and relationships match the ERD and model docs
- linked requirements still describe the same implemented behavior

## Maintenance Rule

When a new architecture diagram is added anywhere under `docs/technical/`, add its location and verification source to this file in the same documentation update.
