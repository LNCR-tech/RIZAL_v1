# Repository Instructions

- For every backend code change under `backend/`, update the documentation in `docs/backend/`.
- Update any affected backend guide with the changed logic, routes, schemas, models, migrations, or configuration.
- If a backend change affects runtime behavior, document how to test it.
- Do not implement hardcoded answers or preset question-to-answer mappings for chat. Responses must be generated from model reasoning based on the user's prompt and available context.
- for every changes made do git add -A, git commit -m. you decide whatever commit message to say. then git push
- if a git push doesn't work, git pull --rebase and fix if there are any merge conflicts, ask the user which one to pick, then git push again
- When git merging, ensure that ONLY the `pilot` branch has the `seeder/` folder. It MUST NOT be present in `preproduction` or `production` branches.
- **frontend-app/ is READ-ONLY — do NOT edit any file inside `frontend-app/`. It is the APK source and can only be reviewed. Only `backend/` files may be edited.**

## Pre-Fix Discovery Rule (MANDATORY — applies to ALL fixes)

- **Before implementing ANY fix, change, or suggestion, ALWAYS grep/search the entire codebase first.**
- Search for existing logic, functions, endpoints, services, models, or utilities that already solve or partially solve the problem.
- If existing code already handles the requirement, use or extend it — do NOT create a duplicate or propose changes that are already covered.
- This applies to: endpoints, services, utilities, models, schemas, frontend components, configs, and anything else.
- Only propose creating new code if a thorough search confirms nothing existing satisfies the requirement.

## Endpoint Discovery Rule (MANDATORY)

- **Before suggesting a new endpoint or modifying an existing one, ALWAYS grep/search the entire `backend/` codebase first to check if a suitable endpoint already exists.**
- Search `backend/app/routers/`, `backend/app/reports/`, and router files for the needed data shape.
- Only propose creating or modifying an endpoint if no existing endpoint satisfies the requirement.
- If an existing endpoint returns the needed data, point to it directly — do NOT create a duplicate.

## Known Endpoint Inventory (update when endpoints are added/removed)

| Method | Path | Returns | Notes |
|--------|------|---------|-------|
| GET | `/api/events/{id}/attendees` | `list[Attendance]` | No student names — only student_id (DB int) |
| GET | `/api/attendance/events/{id}/attendees` | `list[Attendance]` | No student names |
| GET | `/api/attendance/events/{id}/attendances` | `list[AttendanceWithStudent]` | ✅ Includes `student_name` + `student_id` (student number) |
| GET | `/api/attendance/events/{id}/attendances-with-students` | `list[AttendanceWithStudent]` | ✅ Includes `student_name` + `student_id` (student number) |
| GET | `/api/attendance/events/{id}/report` | `AttendanceReportResponse` | Aggregate report, no per-student names |
| GET | `/api/governance/students` | Student list with user + profile | ✅ Includes names, student number |
| GET | `/api/governance/students/search` | Student search results | ✅ Includes names |
| GET | `/api/auth/security/face-reference` | Face reference save | For campus_admin / admin only |
| POST | `/api/face/register` | Face registration | For students only |
| GET | `/api/users/me/` | Current user profile | ✅ Includes first/last name |
