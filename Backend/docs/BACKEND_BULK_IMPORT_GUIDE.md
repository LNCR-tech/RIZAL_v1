# Backend Bulk Import Guide

## Purpose

This guide documents the student bulk import contract, especially the preview-first validation flow used by Campus Admin users and the high-volume import path used for large school rosters.

## Current Flow

1. `POST /api/admin/import-students/preview`
2. Review preview errors and approval state
3. Optional: `POST /api/admin/import-preview-errors/{preview_token}/remove-invalid` to keep only valid rows from an invalid preview
4. `POST /api/admin/import-students` with the returned `preview_token`
5. Poll `GET /api/admin/import-status/{job_id}`

## Deprecated Legacy Routes

- `GET /school-settings/me/users/import-template`
- `POST /school-settings/me/users/import`

These legacy school-settings import routes are no longer supported and now return `410 Gone`.

Use this supported flow instead:

1. `GET /api/admin/import-students/template`
2. `POST /api/admin/import-students/preview`
3. `POST /api/admin/import-students`

## Preview Responsibilities

- accept uploaded `.csv` files directly and normalize uploaded `.xlsx` files into CSV-backed rows before validation
- validate the uploaded tabular structure and header order
- validate every row against required fields, duplicate rows inside the file, and email format
- allow new department names, course/program names, and department-program pairings to pass preview so import can create them in bulk
- check the target database for conflicts such as:
  - existing user email
  - existing `Student_ID` within the same school
- run database duplicate checks in chunks so preview stays stable for larger uploads
- return `can_commit=true` only when the entire file is approved
- persist the approved rows into a preview manifest under `IMPORT_STORAGE_DIR/previews/`

## Import Responsibilities

- accept only a preview-approved `preview_token`
- queue a background job that reads the stored preview manifest instead of re-reading the original upload
- fall back to FastAPI background-task execution when Celery job publishing is unavailable
- skip normal row validation during the standard import path because preview is the authoritative validation step
- keep defensive database conflict handling only for late races, such as another process creating the same email after preview approval
- create missing `departments`, `programs`, and `program_department_association` rows for the target school in bulk before student profiles are inserted
- assign one shared temporary password per import job and store its bcrypt hash on each imported user instead of generating and hashing a unique password for every imported user
- queue onboarding emails outside the critical import path; the worker task now sends the same credentials-style message used by create-user flows
- if onboarding-email task publishing fails, the import falls back to an inline Gmail API send attempt for that student instead of silently dropping delivery work

## Response Contract

### `POST /api/admin/import-students/preview`

- returns the normal preview counts and row samples
- returns `preview_token` for preview manifests, including invalid previews that need preview-only downloads
- invalid previews can use the same token for preview error exports, but cannot be submitted to the import route

### `POST /api/admin/import-students`

- expects multipart form data with `preview_token`
- returns `400` with `Preview the file first before importing.` when called without a preview token
- returns `400` with `Preview still has invalid rows. Fix them before importing.` when the submitted preview token still has preview errors

### Preview Error Downloads

- `GET /api/admin/import-preview-errors/{preview_token}/download`
  - downloads an Excel file with the failed preview rows plus an `Error` column
- `GET /api/admin/import-preview-errors/{preview_token}/retry-download`
  - downloads an Excel file containing only the preview-failed rows in template format so they can be corrected and re-uploaded
- `POST /api/admin/import-preview-errors/{preview_token}/remove-invalid`
  - removes the preview-failed rows from that preview manifest
  - keeps only the already approved rows
  - returns an updated preview response that can proceed straight to import when at least one valid row remains

## Operational Notes

- retry-failed imports still rebuild a workbook and create a new job, because that flow is explicitly for rows that failed after queueing
- preview manifests live on disk, so `IMPORT_STORAGE_DIR` must be writable by the API and worker processes
- when Celery is unavailable, import processing still runs in the API process, and onboarding email delivery now falls back to direct Gmail API sends during the background import run
- preview approval belongs to the user and school that created it; another user or school cannot consume the same token
- large preview duplicate checks should not use one giant SQL `IN (...)` expression; the repository now chunks those lookups to avoid PostgreSQL stack-depth failures
- PostgreSQL import locking is now scoped per school, so concurrent imports from different schools can run at the same time while same-school jobs still serialize safely
- imported users receive the generated temporary password by email and can sign in with the emailed credentials
- successful worker-side or inline-fallback onboarding sends are recorded in `email_delivery_logs` with `status=sent`
- if both task publishing and the inline fallback fail, the error is recorded in `email_delivery_logs` with `status=failed`

## How To Test

1. Preview a valid `.xlsx` import file and confirm `can_commit=true` with a non-empty `preview_token`.
2. Preview the same logical file as `.csv` and confirm the response matches the `.xlsx` preview path.
3. Preview a file that contains a brand-new department and brand-new course/program name and confirm preview still returns `can_commit=true`.
4. Import using that `preview_token` and confirm a pending job is created.
5. After the job finishes, confirm the target school now contains the new `departments`, `programs`, and `program_department_association` rows referenced by the file.
6. Call `POST /api/admin/import-students` without preview and confirm it returns `400`.
7. Preview a file that duplicates an existing student email and confirm preview reports `Email already exists`.
8. Preview a file that duplicates an existing `Student_ID` inside the same school and confirm preview reports `Duplicate Student_ID within School_ID`.
9. From an invalid preview, download the preview error report and retry file and confirm both files contain the failed preview rows.
10. From an invalid preview that still has at least one valid row, call `POST /api/admin/import-preview-errors/{preview_token}/remove-invalid` and confirm the response changes to `can_commit=true` with `invalid_rows=0`.
11. Import using that same cleaned `preview_token` and confirm the job is queued successfully.
12. Open an imported user's onboarding email and confirm it includes the student email, temporary password, and frontend login URL.
13. Sign in with an imported account using the emailed password and confirm login succeeds.
14. If Celery is unavailable, confirm the job still completes and imported accounts still receive onboarding emails through the inline fallback path.
15. In that same fallback case, confirm `email_delivery_logs` records `status=sent` on success or `status=failed` if the Gmail API send also fails.
16. If the worker is available and Gmail API delivery is configured correctly, confirm imported accounts create `email_delivery_logs` rows with `status=sent`.
17. Call both deprecated `/school-settings/me/users/import*` routes and confirm they return `410 Gone` with the replacement admin-import endpoints in the error detail.
