# Tech Stack

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Source of truth:**
> - `Backend/requirements.txt`
> - `Backend/Dockerfile.prod`
> - `Frontend/package.json`
> - `Frontend/Dockerfile.prod`
> - `docker-compose.yml`
> - `docker-compose.prod.yml`

---

## Purpose

This page records the actual technologies used by the project, why they are used, and where their versions or declarations come from.

See also:
- [system-architecture.md](./system-architecture.md)
- [api-overview.md](../api/api-overview.md)
- [functional-requirements.md](../../requirements/functional-requirements.md)

## Versioning Rule

- Use the manifest or Docker file as the source of truth for versions.
- If a dependency is declared in `Backend/requirements.txt` without a pinned version, document the technology but do not invent a version number.
- If the runtime image changes, update this page in the same change set.

## Backend Application Stack

| Technology | Source | Why it is used |
|---|---|---|
| Python 3.10 | `Backend/Dockerfile.prod` | Backend runtime for the FastAPI application and worker processes. |
| FastAPI | `Backend/requirements.txt` | REST API framework with validation and auto-generated docs endpoints. |
| Uvicorn | `Backend/requirements.txt`, `Backend/Dockerfile.prod` | ASGI server used to run the backend application. |
| SQLAlchemy | `Backend/requirements.txt` | ORM and DB session layer. |
| Pydantic | `Backend/requirements.txt` | Request and response validation for API schemas. |
| Alembic | `Backend/requirements.txt` | Database migration management. |
| Celery | `Backend/requirements.txt` | Background and scheduled job execution. |
| `python-jose` | `Backend/requirements.txt` | JWT handling for authentication flows. |
| `passlib` and `bcrypt` | `Backend/requirements.txt` | Password hashing and verification. |
| `face-recognition` and `dlib` | `Backend/requirements.txt` | Biometric encoding and face-matching support. |
| `opencv-python-headless` and `onnxruntime` | `Backend/requirements.txt` | Image-processing and model runtime support used by face-related flows. |
| `openpyxl` | `Backend/requirements.txt` | Excel import processing for student bulk import. |
| `psycopg2-binary` | `Backend/requirements.txt` | PostgreSQL database driver. |

## Frontend Application Stack

| Technology | Version from manifest | Why it is used |
|---|---|---|
| React | `^19.0.0` | Frontend component model and SPA rendering. |
| React DOM | `^19.0.0` | Browser rendering for the React app. |
| TypeScript | `~5.7.2` | Type-safe frontend code. |
| Vite | `^6.2.0` | Dev server and production build tool. |
| React Router DOM | `^7.2.0` | Route registration and navigation. |
| Axios | `^1.8.1` | HTTP client for backend API access. |
| Bootstrap | `^5.2.3` | Shared layout and UI styling base. |
| Chart.js and `react-chartjs-2` | `^4.4.9`, `^5.3.0` | Charts and reporting views. |
| Recharts | `^2.15.1` | Additional reporting and dashboard visualizations. |
| Leaflet and `react-leaflet` | `^1.9.4`, `^5.0.0` | Map-based UI and geofence interaction. |
| Framer Motion | `^12.6.3` | UI motion where interactive transitions are needed. |
| Font Awesome and `react-icons` | `^6.7.2`, `^5.5.0` | Iconography used across the interface. |

## Infrastructure and Runtime Stack

| Technology | Source | Why it is used |
|---|---|---|
| Docker Compose | `docker-compose.yml`, `docker-compose.prod.yml` | Multi-service orchestration for local and production-style runtime. |
| PostgreSQL 15 | Compose image `postgres:15` | Primary relational datastore. |
| Redis 7 Alpine | Compose image `redis:7-alpine` | Celery broker and result backend. |
| Nginx 1.27 Alpine | `Frontend/Dockerfile.prod` | Serves built frontend assets in production. |
| Node 20 | `Frontend/Dockerfile.prod` | Frontend build-stage runtime. |
| Mailpit | `docker-compose.yml` | Local SMTP capture for email testing. |
| pgAdmin 4 | `docker-compose.yml` | Development database inspection UI. |

## Requirement Alignment

| Requirement area | Stack elements that directly support it |
|---|---|
| FR-01 Authentication and Session Management | FastAPI, `python-jose`, `passlib`, `bcrypt`, React Router DOM |
| FR-02 User Management and Import | FastAPI, SQLAlchemy, `openpyxl`, Celery, Redis |
| FR-03 Event Management | FastAPI, SQLAlchemy, Celery, React, Axios |
| FR-04 Face-recognition Attendance | `face-recognition`, `dlib`, OpenCV, ONNX Runtime, React camera and attendance UI modules |
| FR-05 Governance Hierarchy | FastAPI, SQLAlchemy, React Router DOM, TypeScript |
| FR-06 Notifications | Celery, Mailpit in development, backend email services, frontend notification pages |
| FR-07 Reporting and Audit | PostgreSQL, Chart.js, Recharts, FastAPI reporting endpoints |

## Documentation Controls

- Do not list frameworks that are not present in the manifests. For example, the current frontend stack uses Bootstrap and custom CSS, not Tailwind.
- Re-check this page whenever `package.json`, `requirements.txt`, Docker files, or compose files change.
- Keep technology descriptions tied to actual system behavior, not generic stack labels.
