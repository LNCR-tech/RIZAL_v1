# Migration Guide: Bulk Import and Email Sender Fixes

This guide explains how to migrate the improved **Bulk Import** and **Email Sender** modules from the `Agentic` path to your current project. These updates focus on reliability, Gmail API best practices, and a cleaner, preview-first import workflow.

> [!IMPORTANT]
> This guide assumes you have already removed **MFA** and the **Event Organizer** role. When copying these files, ensure any leftover MFA code is stripped out to maintain consistency.

---

## Part 1: Modularizing the Email Service

The legacy `email_service.py` is now a modular package. This allows for better transport handling (Gmail API vs. SMTP) and cleaner template rendering.

### Steps:
1. **Delete the old service**: Remove `Backend/app/services/email_service.py`.
2. **Create the new package**: Copy the `email_service/` directory from `Agentic/Backend/app/services/` to your project.
3. **Structure Overview**:
   - `__init__.py`: Public API (exports `send_welcome_email`, etc.).
   - `config.py`: Centrally handles Gmail/SMTP settings and validation.
   - `transport.py`: Handles the actual sending logic (Google API or SMTP TLS).
   - `rendering.py`: Pure logic for building the email body and subjects.
   - `use_cases.py`: High-level business functions for specific email types (Onboarding, Resets).

---

## Part 2: Consolidating the Bulk Import Pipeline

The `Agentic` version of the import pipeline introduces a **Preview-First** strategy that is significantly more robust than the legacy logic.

### Steps:
1. **Router Update**: Replace `Backend/app/routers/admin_import.py` with the version from `Agentic`.
   - **Improvement**: It now supports a `preview_token` workflow, allowing users to verify errors before committing 1,000+ rows.
2. **Service Update**: Replace `Backend/app/services/student_import_service.py` with the version from `Agentic`.
   - **Improvement**: Added `_process_preview_manifest` which "trusts" the pre-validated JSON manifest for 5x faster final imports.
3. **New Helper**: Copy `Backend/app/services/import_file_service.py` from `Agentic`.
   - This isolates `.csv` and `.xlsx` parsing logic from the business logic.
4. **Repository Sync**: Update `Backend/app/repositories/import_repository.py`.
   - Ensure it includes the `log_email_delivery` and `update_progress` methods used by the new service.

---

## Part 3: Schema and Configuration Alignment

To support the new import features (tracking progress, individual row errors), you must ensure your database and environment variables are aligned.

### Steps:
1. **Database Model**: Check `Backend/app/models/import_job.py`. Ensure `BulkImportJob` has the following fields if they are missing:
   - `total_rows` (Integer)
   - `processed_rows` (Integer)
   - `success_count` / `failed_count` (Integer)
   - `eta_seconds` (Integer)
   - `failed_report_path` (String)
2. **Environment Variables**: Add or verify these in your `.env`:
   ```env
   IMPORT_STORAGE_DIR=/tmp/valid8_imports
   IMPORT_CHUNK_SIZE=500
   IMPORT_MAX_FILE_SIZE_MB=50
   ```

---

## Part 4: Final Cleanup (Post-Migration)

Once the new files are in place:
1. **Strip MFA**: If any `send_mfa_code_email` calls or imports appear in the new router/service, delete them.
2. **Remove Dead Routes**: Ensure `Backend/app/routers/school_settings.py` no longer contains the old import endpoints, as they are now consolidated in `admin_import.py`.
3. **Restart Workers**: Since tasks were likely renamed or updated (e.g., `send_student_import_onboarding_email`), restart your Celery worker to load the new definitions.
