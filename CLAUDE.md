# RIZAL v1 — Project Instructions for Claude Code

## Documentation Rule (MANDATORY)

**Any change to the backend MUST be reflected in `docs/Backend Documentation.md`.**

This includes:
- New endpoints (add the full endpoint entry with method, path, auth, request body, response)
- Changed request/response fields (update the schema and example)
- Removed endpoints (remove the entry)
- Changed auth requirements (update the Auth line)
- New query params or changed defaults (update the params table)
- New error codes or changed error behavior (update the Errors section)
- Changes to pagination behavior (update the Pagination section)
- Changes to business logic that affect what the frontend must send or expect

After every backend change, update `docs/Backend Documentation.md` in the same commit. Do not make a separate commit for the docs update — it should always travel with the backend change.

## Frontend Rule (STRICT)

**Never modify any frontend code.**

- No changes to `frontend-app/` (Flutter mobile app)
- Backend changes only

**Never push any changes in frontend code**

- No changes push to `frontend-app/` (Flutter mobile app)
- Backend changes only push

## General

- Primary language: Python (FastAPI + SQLAlchemy)
- All datetimes are Philippine Time (UTC+8 / Asia/Manila)
- SSH deploy target: `ubuntu@18.142.190.113` key at `C:\Users\frien\Downloads\for-test-env.pem`
- Production repo on server: `/data/applications/Aura/Testing/RIZAL_v1`
- Deploy command: `docker compose -f docker-compose.prod.yml build migrate && docker compose -f docker-compose.prod.yml up -d --force-recreate --no-deps backend worker beat`
