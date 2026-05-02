# Change Audit (2026-05-02)

## Scope

- Branch: `experiment/risky-changes`
- Compared range: `ccf8117` (before checkpoint commit) -> `36f2ff7` (`checkpoint: approvable local state`)
- Coverage: all included changes in that commit range

## Notes

- `HEAD` means the commit your current branch is currently pointing to.
- In this audit, `HEAD` is `36f2ff7`.

## Before/After/Problem/Fix

| Change Block | Files + Location | Before | Now | Problem | Fix |
|---|---|---|---|---|---|
| Mailpit container + persistence | `docker-compose.yml` (`services.mailpit`, `volumes.mailpit_data`) | No Mailpit service | Mailpit added with `mailpit_data` volume and ports `1025/8025` | No local mail inbox persistence for dev testing | Added persistent Mailpit container |
| Dev DB external access | `docker-compose.yml` (`services.postgres.ports`) | Postgres port not explicitly mapped | `DB_PORT` mapped to host | Harder to connect from DataGrip | Exposed DB port in compose |
| Email mode toggle | `backend/.env.example` (Email section), `backend/app/core/config.py` (`_resolve_email_delivery_mode`, `get_settings`) | Only `EMAIL_TRANSPORT` path | Added `EMAIL_DELIVERY_MODE` (`mailpit/smtp/mailjet/disabled`) and Mailpit host+port routing logic | Confusing email routing and dual `.env` behavior | Centralized delivery mode logic + Mailpit override |
| DB timezone default | `database/docker-init/init.sql` | Only DB creation | Added `ALTER DATABASE ... SET timezone 'Asia/Manila'` | Persistent timezone offset confusion | Set DB-level timezone default |
| Event datetime normalization (backend) | `backend/app/schemas/event.py` (`EventCreate` / `EventUpdate` validators) | Datetimes passed through as-is | Naive datetimes normalized to PH timezone; aware datetimes converted | 8-hour offset inconsistencies | Added timezone validators |
| Event timezone test coverage | `backend/tests/test_events.py` | No regression test for naive datetime normalization | Added test asserting create/store values stay correct in PH timezone | No guard against regression | Added backend test |
| Enum/string compatibility in auth/governance | `backend/app/services/auth_session.py`, `backend/app/services/governance_hierarchy_service/shared.py` | Direct `.value` assumptions on enum-like fields | `_enum_value(...)` helper used across sorting/messages/codes | Runtime brittleness when values are plain strings | Normalized enum/string handling |
| Permission relation schema compatibility | `backend/app/models/governance_hierarchy.py` (`GovernanceUnitPermission.id`, `GovernanceMemberPermission.id`) | No `id` compatibility alias on relation rows | Added computed `id` alias = `permission_id` | API/schema consumers expecting `id` could break | Added compatibility properties |
| Bulk import email delivery | `backend/app/services/student_import_service.py` (success loop) | Account-ready email queueing commented out | Queueing restored for each imported student | Bulk import produced no emails in Mailpit | Re-enabled email queue |
| Google button always visible | `frontend-web/src/components/auth/GoogleSignInButton.vue` (template + onMounted), `frontend-web/src/views/auth/LoginView.vue` (Google section) | Hidden when config missing (`googleUnavailable` gate) | Always visible fallback button + message; parent hide gate removed | Users thought Google login disappeared | Always render button area, show fallback state |
| Nav icon primary-color alignment | `DesktopSideNav.vue`, `SideNav.vue`, `BottomNav.vue`, `MobileBrandedBottomNav.vue`, `MobileGlassIconNav.vue` (icon color bindings) | Active/inactive mixed colors | Icons/dots/text forced to `var(--color-primary)` | Navbar icons did not match school primary color | Unified nav color mapping |
| Event form defaults from school settings | `SgEventsView.vue` (create form/template/script), `GovernanceWorkspaceView.vue` (`create-defaults`), `EventEditorSheet.vue` (`createDefaults` seed logic), `backendNormalizers.js` (default fields) | Create flow defaulted timing fields to hardcoded/zero behavior | Loads school default timings, allows override, validates, blocks submit while defaults load | Event creation not reflecting school defaults | Added create-default preload + payload + validation |
| Date serialization at frontend submit | `frontend-web/src/services/eventEditor.js`, `frontend-web/src/views/dashboard/SgEventsView.vue` (`toBackendDateTimeValue`) | Raw `datetime-local` string passed through | Converted to ISO string before API | Client-side datetime ambiguity across timezone contexts | Standardized ISO serialization |
| Map auto-init from current location | `EventLocationPicker.vue` (new prop + init flow), used by `EventEditorSheet.vue` and `SgEventsView.vue` | Map did not auto-initialize from device location on create | Optional auto-initialize with current location + status/error handling | Initial lat/lng not prefilled ergonomically | Added create-mode current-location initialization |
| Text contrast fix in governance UI | `GovernanceWorkspaceView.vue` (CSS color token replacements) | Some text used muted tokens with poor contrast | Switched to darker/surface-safe tokens | Text difficult to read on light surfaces | Updated typography color tokens |
| Documentation updates | `doc/changelog/branch-updates.md`, `doc/changelog/frontend.md` | Previous date/entries only | Added `2026-05-02` entry for event-default behavior changes | Changes not documented | Updated changelog docs |
