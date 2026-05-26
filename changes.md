# Changes

## 2026-05-26 (Flutter App CI, UI Quality, and Analyze Fixes)

### CI Workflow Changes

**`.github/workflows/aura-app-ci.yml`**
- Runs the Flutter app CI on pushes to `main`, `develop`, `feature/*`, and `integrate/pilot-merge`, with manual `workflow_dispatch` support.
- Kept the fast Flutter gates in order: `flutter pub get`, `flutter analyze`, then `flutter test`.
- Added real-backend setup to the Android job:
  - Starts PostgreSQL with `pgvector/pgvector:pg15`.
  - Starts Redis with `redis:7-alpine`.
  - Installs backend Python dependencies.
  - Creates `fastapi_db`.
  - Runs Alembic migrations.
  - Seeds the backend test data from `backend/tests/conftest.py`.
  - Starts FastAPI on port `8000` for the emulator.
- Kept the Android job focused on emulator-based integration checks:
  - Enables KVM permissions on the GitHub runner.
  - Starts an Android API 33 x86_64 `google_apis` emulator through `reactivecircus/android-emulator-runner@v2`.
  - Uses a lighter Pixel 2 profile, 2 GB RAM, explicit no-window/no-snapshot emulator options, and a 300-second boot timeout so emulator boot failures fail clearly instead of repeating indefinitely.
  - Resolves the attached Android device from `adb devices` and runs `flutter test integration_test -d "$device"` with `AURA_RUN_BACKEND_E2E=true`.
  - Uploads `backend/backend.log` as a short-retention artifact for mobile E2E failures.
- Removed the separate `flutter build apk --debug`, ADB install, manual launch, and process-liveness smoke check from CI.
- CD/deployment workflows remain manual-only through `workflow_dispatch`; pushing to `integrate/pilot-merge` runs CI, not deployment.

### Flutter App Test Coverage

**`frontend-app/pubspec.yaml` / `frontend-app/pubspec.lock`**
- Added the Flutter SDK `integration_test` dev dependency so app-level integration tests can run in CI.

**`frontend-app/integration_test/app_e2e_test.dart`**
- Added app-level Flutter integration coverage that boots `AuraApp()` with mocked Riverpod providers.
- Covers signed-out login behavior, password visibility, required-login validation, student shell tab navigation, and event-editor save behavior.

**`frontend-app/integration_test/real_backend_e2e_test.dart`**
- Added a skipped-by-default mobile E2E smoke test that is enabled in CI with `AURA_RUN_BACKEND_E2E=true`.
- Boots the actual Flutter app on the Android emulator while keeping test-only splash, beta-nav, token-store, and geofence overrides.
- Logs in through the app UI as `student@test.com` / `TestPass123!` against the seeded FastAPI backend.
- Verifies the student workspace loads, opens the Schedule tab, switches to Upcoming, finds `Seed Year Level Event`, and opens the real backend event detail showing `Seed Hall`.

**`frontend-app/test/ui_quality_test.dart`**
- Added Flutter-side UI/UX quality checks to mirror the intent of the web Playwright UI-quality suite.
- Pumps key app states across common viewport sizes: mobile, tablet, and desktop.
- Fails on Flutter layout/runtime exceptions, catching overflow-style UI regressions.
- Checks accessible semantics labels for login controls, bottom navigation tabs, and event-editor icon-only controls.
- Verifies icon-only `IconButton`s used in the tested surfaces expose a tooltip or semantic label.

**Other Flutter app tests**
- Added and expanded focused unit/widget tests for router redirects, navigation items, repository API paths, geolocation behavior, attendance scan flow, event-editor draft/payload logic, location display formatting, and event editor repository submission.
- Expanded `AuraButton` widget coverage for loading state, disabled interaction, icons, and compact layout.

### Flutter App Source Changes Supporting Tests

**`frontend-app/lib/features/shell/navigation_items.dart`**
- Centralized workspace tab definitions so navigation structure can be tested independently from the shell widget.

**`frontend-app/lib/features/shell/app_shell.dart`**
- Refactored shell tabs to consume the centralized navigation item list.

**`frontend-app/lib/features/events/application/event_editor_draft.dart`**
- Added pure event-editor draft logic for initializing editable form state from an event.

**`frontend-app/lib/features/events/application/event_editor_payload.dart`**
- Added pure event-editor payload building and validation for create/edit submissions.

**`frontend-app/lib/features/attendance/application/attendance_scan_flow.dart`**
- Added pure attendance scan flow helpers for testable event/location decision logic.

**`frontend-app/lib/shared/utils/location_display.dart`**
- Added shared coordinate formatting helpers for consistent location display.

**`frontend-app/lib/features/schoolit/presentation/event_editor_screen.dart`**
- Moved save-payload construction through the shared event-editor payload helper.
- Added tooltips to the date/time icon buttons: `Pick start date`, `Pick start time`, `Pick end date`, and `Pick end time`.

**`frontend-app/lib/app/router.dart`**
- Extracted redirect decision logic so route guard behavior can be unit-tested.

**`frontend-app/lib/core/services/geolocation_service.dart`**
- Added an injectable geolocation platform adapter so permission/location behavior can be tested without native device access.
- Fixed the analyzer `prefer_const_constructors` finding by using `const GeolocationService()` in the provider.

### Flutter Analyze Fixes

**`frontend-app/lib/core/theme/app_theme.dart`**
- Replaced `CupertinoPageTransitionsBuilder` with a local `_AuraPageTransitionsBuilder`.
- This avoids the CI analyzer failure where the Flutter SDK used by CI did not resolve `CupertinoPageTransitionsBuilder`.
- The replacement keeps a lightweight horizontal route transition and still uses `_NoPageTransitionsBuilder` when reduced motion is enabled.

### Backend Model Defaults

**`backend/app/models/school.py`**
- Added default-enabled school event policy columns on `SchoolEventPolicy`:
  - `privileged_face_verification_enabled = true`
  - `attendance_face_recognition_enabled = true`
  - `first_time_face_registration_required = true`
- These defaults keep existing schools permissive unless a later policy path explicitly disables face verification or first-time registration requirements.

### Backend Test Data Fixes

**`backend/tests/test_event_announcement_notifications.py`**
- Replaced an invalid `YEAR_LEVEL` target value of `99` with a valid `year_level=5`.
- The empty-recipient notification test now creates a temporary school with no students, so it still verifies zero recipients without leaving invalid event-target data in the shared CI test session.
- This prevents later event-list API tests from failing response validation on `year_level <= 5`.

### Backend CI Lint Fixes

**`backend/app/services/centralized_ai_service.py`**
- Removed the unused `full_tool_calls` name from a nested stream parser's `nonlocal` declaration.
- This resolves the CI flake8 `F824` failure while preserving streamed tool-call accumulation through in-place dictionary mutation.

### Flutter CI Failure Follow-up

**`frontend-app/lib/core/widgets/liquid_glass_nav.dart`**
- Kept the existing shader-backed `LiquidGlass.withOwnLayer` beta nav path so the app's visual design is unchanged.

**`frontend-app/pubspec.yaml` / `frontend-app/pubspec.lock`**
- Restored the liquid-glass nav dependencies.
- Pointed `liquid_glass_renderer` to a local patched copy under `frontend-app/third_party/liquid_glass_renderer` so CI can compile the same renderer without changing the app widget.

**`frontend-app/third_party/liquid_glass_renderer`**
- Vendored `liquid_glass_renderer` `0.2.0-dev.4`.
- Patched the shader SDF helper to read `uShapeData` as a global uniform instead of passing uniform arrays through helper functions. This avoids the SkSL compiler generating unsupported array initializer code while preserving the renderer's behavior.
- Replaced the remaining dynamic `uShapeData[baseIndex]` SDF lookup with fully unrolled literal uniform-array indices, because Impeller/SkSL rejects runtime uniform-array indexing.
- Unrolled SDF shape merging to avoid SkSL `min(int,int)` and loop-initializer limitations.
- Replaced derivative intrinsics with finite-difference normal sampling for runtime-effect compatibility.
- Removed loops from the experimental arbitrary shader's center sampler and gradient helper so the file compiles under SkSL.
- Removed `sampler2D`/shader parameters from shared liquid-glass shader helpers and routed background texture reads through entry-shader sampling macros. This addresses SkSL's unsupported shader-parameter compilation path while preserving the same shader-backed liquid-glass visual path.

**`frontend-app/lib/core/widgets/aura_button.dart`**
- Made button labels flexible with ellipsis so long labels do not overflow narrow mobile layouts.
- Added a semantics container to the button so accessibility-label tests can reliably find labels such as `Sign in`.
- Excluded child semantics inside the button semantics node so the accessible label stays exact instead of merging with the visible text.

**`frontend-app/lib/core/widgets/glass_bottom_nav.dart` / `frontend-app/lib/core/widgets/liquid_glass_nav.dart`**
- Added stable, non-visual keys to bottom navigation items for Flutter UI tests.

**`frontend-app/lib/features/auth/presentation/login_screen.dart`**
- Added explicit semantics around the password visibility toggle so UI-quality tests can verify the accessible label.

**`frontend-app/test/event_editor_screen_test.dart`**
- Replaced direct `ensureVisible` usage with `scrollUntilVisible` for the save button, because the editor body is a lazy `ListView`.

**`frontend-app/integration_test/app_e2e_test.dart`**
- Applied the same scroll-to-save behavior in the app integration test.

**`frontend-app/test/ui_quality_test.dart`**
- Relaxed the password semantics assertion to accept one or more matching semantics nodes, avoiding brittleness from Flutter's tooltip/semantics merging.
- Added a Flutter-side safe-pressable response test for key controls:
  - Login password visibility toggle.
  - Empty login submit validation.
  - Google sign-in placeholder snackbar.
  - Student Schedule, Scan, Insights, and Account tab navigation.
  - Schedule `Upcoming` filter.
  - Event editor date and time picker buttons.
- Hardened pressable UI tests to use hit-testable targets and route-ready pumping before tapping navigation controls.
- Reset the test app tree between signed-out and student sessions so Riverpod/router state from the prior pump cannot hide the student shell.
- Switched student bottom-nav taps from visible text lookup to stable bottom-nav keys.

### Notes

- The web UI/UX Playwright suite still lives under `frontend-web/e2e/workflows/`.
- The web Playwright E2E job in `.github/workflows/ci.yml` is gated to run only on the `pilot` branch.
- The Flutter UI-quality tests now run through `flutter test` on `frontend-app/**` pushes.
- The Android emulator step now runs Flutter integration tests only; separate APK build/install/launch smoke is no longer part of Flutter CI.

## 2026-05-22 (Campus Admin Enhancements)

### Frontend Changes
- **iPhone Mockup & Custom Color Picker:** Redesigned the simulated phone preview into a high-fidelity, photorealistic iPhone 15 Pro mockup featuring a Titanium-look metallic chassis, rounded uniform bezels, Dynamic Island, top iOS status bar, and bottom home indicator. Replaced the restricted 6-color grid with an unlimited HSV color picker dialog, a SweepGradient rainbow swatch, presets, and real-time custom hex code input.
- **School Settings Customization:** Redesigned `SchoolSettingsScreen` into an Apple-style preferences view with a Mini UI preview that reacts instantly to color and logo changes. Switched from multipart file upload to accepting direct image URLs for logos.
- **Account Tab:** Updated the student `AccountTab` to display the school's custom logo adjacent to the school name, pulling directly from the updated session metadata.
- **Student Management:** Refined `SchoolItUsersScreen` to remove the global student search bar, enforcing management strictly by college. Added both `Manual Add` and `Bulk Import` options directly within `CollegeStudentsScreen` for better organization.

## 2026-05-09 (Phase 12: Rejected Scan Audit Logging)

### Architecture Decision
Used the existing `SchoolAuditLog` table (`school_audit_logs`) rather than creating a new `attendance_scan_attempts` table. Rationale:
- No new table, no Alembic migration, zero schema risk.
- `SchoolAuditLog` already stores structured JSON in its `details` column and is already queryable via `GET /api/audit-logs`.
- Rejected scans are a security/audit concern, not an operational data concern — the general audit log is the correct home.
- A new table would require a migration, a new model, new schema, and new router endpoints, all for data that is already well-served by the existing infrastructure.

### Backend Changes

**`backend/app/routers/attendance/shared.py`**
- Added `from app.models.school import SchoolAuditLog` and `import json as _json`.
- Added `_log_rejected_scan_attempt(db, *, school_id, scanner_user_id, event_id, student_profile_id, attempt_type, reason_code, reason_message)` — writes a `SchoolAuditLog` row with `action="attendance_scan_rejected"`, `status="rejected"`, and a JSON `details` blob. All exceptions are caught and logged as warnings so audit logging never breaks the main request path.
- Added `_ensure_student_is_event_participant_with_audit(db, *, student, event, school_id, scanner_user_id, attempt_type)` — calls `is_student_eligible_for_event`, logs on rejection via `_log_rejected_scan_attempt`, then re-raises HTTP 403 unchanged. Accepted scans are not logged.
- Kept the original `_ensure_student_is_event_participant` unchanged for callers that do not need auditing (bulk endpoint, face-scan-timeout, etc.).

**`backend/app/routers/attendance/check_in_out.py`**
- `record_face_scan_attendance`: replaced `_ensure_student_is_event_participant(student, event)` with `_ensure_student_is_event_participant_with_audit(db, student=student, event=event, school_id=school_id, scanner_user_id=current_user.id, attempt_type="SIGN_IN")`.
- `record_manual_attendance`: same replacement with `attempt_type="MANUAL"`.

### Tests
- Created `backend/tests/test_scan_audit_log.py` — 10 test cases:
  - `_log_rejected_scan_attempt` writes a row to `school_audit_logs`.
  - Written row has correct `action`, `status`, and `details` JSON fields.
  - DB error in `_log_rejected_scan_attempt` does not propagate.
  - `_ensure_student_is_event_participant_with_audit` does not raise for eligible student.
  - `_ensure_student_is_event_participant_with_audit` raises 403 for ineligible student.
  - `_ensure_student_is_event_participant_with_audit` creates audit log on rejection.
  - HTTP: rejected face-scan does not create `AttendanceRecord`.
  - HTTP: rejected face-scan creates `SchoolAuditLog` row.
  - HTTP: rejected scan not in attendance report.
  - HTTP: accepted scan creates attendance record and no rejection audit row.

### Documentation
- Updated `docs/attendance-eligibility.md` — added Phase 12 Rejected Scan Audit Logging section with field reference, `attempt_type` values, `reason_code` values, guarantees, and query example.
- Updated `docs/year-level-events-plan.md` — Phase 12 marked complete.


### Backend Changes

**`backend/app/services/event_target_permissions.py`** (new file)
- `validate_event_targets_for_actor(db, *, current_user, event_targets)` — enforces which `EventTargetScope` values each actor may use:
  - Campus Admin / Admin: unrestricted (early return).
  - SSG member with `MANAGE_EVENTS`: `ALL` and `YEAR_LEVEL` only.
  - SG member with `MANAGE_EVENTS`: `DEPARTMENT` and `DEPARTMENT_YEAR` restricted to the unit's own `department_id`.
  - ORG member with `MANAGE_EVENTS`: `COURSE` and `COURSE_YEAR` restricted to the unit's own `program_id`.
  - Raises HTTP 403 with a descriptive message on any violation.
- Uses existing `governance_hierarchy_service.get_governance_units_with_permission` — no new DB tables or migrations required.

**`backend/app/routers/events/shared.py`**
- Added `from app.services.event_target_permissions import validate_event_targets_for_actor` import.

**`backend/app/routers/events/crud.py`**
- `create_event`: calls `validate_event_targets_for_actor` immediately after `_ensure_event_manager` passes, before any DB writes. Passes `event.event_targets or []`.
- `update_event`: calls `validate_event_targets_for_actor` when `event_update.event_targets is not None` (i.e., only when the caller is explicitly replacing targets).

### Tests
- Created `backend/tests/test_event_target_permissions.py` — 28 test cases:
  - **Unit tests** (mocked DB + governance service): campus_admin unrestricted for all 6 scopes; SSG allows ALL/YEAR_LEVEL, forbids DEPARTMENT/COURSE; SG allows own dept/dept+year, forbids other dept/ALL/YEAR_LEVEL/COURSE; ORG allows own course/course+year, forbids other course/ALL/DEPARTMENT/YEAR_LEVEL; empty targets always passes; no governance units passes.
  - **HTTP integration tests**: campus_admin creates ALL-scope event (200); campus_admin creates YEAR_LEVEL event (200); student blocked (403); unauthenticated blocked (401); campus_admin updates event targets (200).

### Documentation
- Updated `docs/event-targeting.md` — added Phase 11 Target Scope Permissions section with role table and enforcement point description.
- Updated `docs/year-level-events-plan.md` — Phase 11 marked complete, Phase 12 placeholder added.


### Frontend Changes

**`frontend-web/src/services/eventEditor.js`**
- Added `AUDIENCE_SCOPE_OPTIONS` — six scope entries (ALL, YEAR_LEVEL, DEPARTMENT, COURSE, DEPARTMENT_YEAR, COURSE_YEAR) with display labels.
- Added `YEAR_LEVEL_OPTIONS` — 1st–5th Year entries.
- Added `scopeNeedsYearLevel(scope)`, `scopeNeedsDepartment(scope)`, `scopeNeedsCourse(scope)` — pure predicate helpers used by both the service and the component.
- Added `buildEventTargetsFromDraft(draft)` — builds the `event_targets` array from audience draft fields. Throws descriptive errors for missing required sub-fields (year level out of range, no department selected, no course selected).
- Added `audienceDraftFromEventTargets(eventTargets)` (internal) — reads the first target from an existing event's `event_targets` array and returns the four audience draft fields.
- Updated `createEventEditorDraft(event)` — spreads audience fields from `audienceDraftFromEventTargets(event?.event_targets)` so edit mode pre-populates correctly.
- Updated `buildEventUpdatePayloadFromDraft(draft)` — adds `event_targets: buildEventTargetsFromDraft(draft)` to the returned payload.

**`frontend-web/src/components/events/EventEditorSheet.vue`**
- Added `departments` and `programs` props (Array, default `[]`).
- Imported `Users` icon from `lucide-vue-next`.
- Imported `AUDIENCE_SCOPE_OPTIONS`, `YEAR_LEVEL_OPTIONS`, `scopeNeedsYearLevel`, `scopeNeedsDepartment`, `scopeNeedsCourse` from `eventEditor.js`.
- Added computed `showYearLevel`, `showDepartment`, `showCourse` driven by `draft.audienceScope`.
- Added Audience section between the Attendance section and the Location section: scope `<select>`, conditional year-level `<select>`, conditional department `<select>`, conditional course `<select>`. All fields carry `data-testid` attributes.

**`frontend-web/src/views/dashboard/SgEventsView.vue`**
- Added `getDepartments` and `getPrograms` to the `backendApi.js` import.
- Added `buildEventTargetsFromDraft` to the `eventEditor.js` import.
- Added `cachedDepartments` and `cachedPrograms` refs.
- `loadEvents` now fires `getDepartments` and `getPrograms` as best-effort background fetches when the view loads.
- Passes `:departments="cachedDepartments"` and `:programs="cachedPrograms"` to `EventEditorSheet`.
- Added `audienceScope`, `audienceYearLevel`, `audienceDepartmentId`, `audienceCourseId` to the `form` ref initial state and `resetEventForm`.
- `buildCreateEventPayload` now includes `event_targets: buildEventTargetsFromDraft(form.value)`.
- Added Audience section to the inline create form with the same six scope options and conditional year/dept/course dropdowns.

### Tests
- Created `frontend-web/tests/unit/services/eventEditor.spec.js` — 30 test cases:
  - Scope predicate helpers (`scopeNeedsYearLevel`, `scopeNeedsDepartment`, `scopeNeedsCourse`).
  - `AUDIENCE_SCOPE_OPTIONS` shape and completeness.
  - `YEAR_LEVEL_OPTIONS` shape.
  - `buildEventTargetsFromDraft` for all six scopes — valid payloads and error cases for missing required fields.
  - `createEventEditorDraft` audience hydration from `event_targets` for all six scopes and null/empty cases.

### Documentation
- Updated `docs/year-level-events-plan.md` — Phase 10 marked complete.


### Backend Changes
- **`notification_center_service.py`**:
  - Added `dispatch_event_announcement_notifications(db, *, event)` — sends in-app + email notifications only to eligible ACTIVE students matching the event's `event_targets` scope. Delegates recipient resolution entirely to `get_event_participant_student_ids`, which enforces school boundary, ACTIVE status, and all six scope types.
  - Fixed `dispatch_event_reminder_notifications` — added `joinedload(Event.event_targets, Event.programs, Event.departments)` to the event query. Previously the relationship was lazy-loaded per event (N+1); now it is eagerly loaded in a single query, and scope resolution is guaranteed to have the full target data.
  - Added `joinedload` to the top-level imports (was previously imported inline).
- **`routers/notifications.py`**:
  - Added `POST /api/notifications/dispatch/event-announcement/{event_id}` endpoint. Requires `campus_admin` or `admin`. Enforces school boundary: returns 404 if the event belongs to a different school than the actor.
  - Added `Event` model import.
  - Added `dispatch_event_announcement_notifications` to the service import block.

### Tests
- Created `backend/tests/test_event_announcement_notifications.py` with 11 test cases:
  - `test_year_level_target_notifies_only_matching_year` — YEAR_LEVEL scope sends to year 2, not year 3.
  - `test_course_year_target_notifies_only_matching_course_and_year` — COURSE_YEAR scope sends to prog+year1, not prog+year2.
  - `test_graduated_student_does_not_receive_notification` — GRADUATED excluded from ALL scope.
  - `test_inactive_student_does_not_receive_notification` — INACTIVE excluded from ALL scope.
  - `test_out_of_scope_student_does_not_receive_notification` — year 5 student excluded from YEAR_LEVEL=1 event.
  - `test_all_scope_notifies_active_students_only` — ACTIVE notified, TRANSFERRED not notified.
  - `test_empty_participant_list_returns_zero_counts` — no participants → all counts zero.
  - `test_dispatch_announcement_endpoint_enforces_school_boundary` — campus_admin gets 404 for other school's event.
  - `test_dispatch_announcement_endpoint_returns_summary` — HTTP 200 with correct summary fields.
  - `test_dispatch_announcement_requires_admin` — student gets 403.
  - `test_dispatch_announcement_requires_auth` — unauthenticated gets 401.

### Documentation
- Updated `docs/event-targeting.md` — added Phase 9 Notifications section with endpoint reference and eligibility rules.
- Updated `docs/year-level-events-plan.md` — marked Phase 9 complete, added Phase 10 placeholder.


### Documentation
- Rewrote `docs/year-level-events-plan.md` with full codebase analysis:
  - Mapped all relevant backend and frontend files.
  - Documented `Event` / `EventTarget` / `StudentProfile` model structures.
  - Traced the complete attendance sign-in/sign-out flow.
  - Traced the attendance report flow through `build_participant_subquery`.
  - Documented the frontend event form flow and the missing `event_targets` gap in `eventEditor.js` and `EventEditorSheet.vue`.
  - Listed recommended Phase 9 implementation order.
  - Flagged high-risk files that must be edited carefully.


## 2026-05-08 (Phase 8: Attendance Reports Update)

### Backend Changes
- **Report Logic:** Re-implemented `build_participant_subquery` in `app/reports/attendance/queries.py` to use the `event_targets` system for calculating expected attendees.
- **ACTIVE Status Enforcement:** Expected attendees and absentees are now strictly filtered by `student_status == ACTIVE`, as per Rule 4.
- **Sign-out Tracking:** Added `signed_out_attendees` and `no_sign_out_attendees` metrics to the `AttendanceReportResponse` schema and service logic.
- **Dynamic Filters:** Updated attendance report endpoints (`/events/{event_id}/report`, `/events/{event_id}/attendees`, etc.) to support filtering by `year_level`, `department_id`, `program_id`, and `status`.
- **Historical Support:** Implemented `list_event_attendance_rows_for_event_report` to ensure historical attendance records for graduated or inactive students remain visible in reports while being correctly excluded from "expected" counts.

### Documentation
- Updated `docs/attendance-eligibility.md` with the new reporting logic definitions.
- Updated `docs/event-targeting.md` highlighting the targeting-to-reporting integration.
- Updated `docs/year-level-events-plan.md` to reflect Phase 8 completion.

## 2026-05-08 (Phase 7: Attendance Enforcement)

### Backend Changes
- **Attendance Routers:** Hardened `record_face_scan_attendance` in `app/routers/attendance/check_in_out.py` to enforce event eligibility using the centralized service.
- **Status Codes:** Updated `_ensure_student_is_event_participant` in `app/routers/attendance/shared.py` to return HTTP 403 (Forbidden) instead of 400, specifically for student targeting violations.
- **Standardized Messaging:** Standardized the rejection message to "Student is not included in this event scope." in `EventEligibilityService`.

### Frontend Changes
- **Public Attendance Service:** Updated `describePublicAttendanceError` and `normalizeOutcome` in `src/services/publicAttendance.js` to translate the backend error code into user-friendly messages:
    - Top-level: "You are not included in this event."
    - Scan outcomes: "Not included in this event."

### Documentation
- Updated `docs/year-level-events-plan.md` to reflect Phase 7 completion.
- Updated `docs/attendance-eligibility.md` to reflect the 403 status code change.

## 2026-05-08 (Phase 6: Student Dashboard Filtering)

### Backend Changes
- **Queries:** Updated event listing routes in `app/routers/events/queries.py` to proactively load `event_targets`, ensuring the eligibility service has the necessary data for filtering.
- **Filtering:** Dashboard events are now strictly filtered using the centralized `EventEligibilityService`, ensuring students only see events matching their Year Level, Department, or Course.

### Frontend Changes
- **Components:** Updated `EventsCard.vue` to display a personalized "No upcoming events assigned to you" message when no eligible events are found for the current student.

### Documentation
- Created `docs/event-targeting.md` as a consolidated reference for the whole targeting system.
- Updated `docs/year-level-events-plan.md` to reflect Phase 6 completion.

## 2026-05-08 (Phase 5: Centralized Eligibility Service)

### Backend Changes
- **Services:**
    - Created `app/services/event_eligibility_service.py` to centralize student eligibility checks.
    - Implemented rules for School matching, Student Status (must be ACTIVE), and Targeting Scopes.
    - Added standardized rejection codes (`STUDENT_NOT_ACTIVE`, `STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE`, etc.).
- **Routers:**
    - Refactored `app/routers/attendance/shared.py` to use the new eligibility service for check-in validation.
    - Refactored `app/routers/events/shared.py` to use the new eligibility service for filtering the student dashboard.

### Documentation
- Created `docs/attendance-eligibility.md` defining the core eligibility rules.
- Updated `docs/year-level-events-plan.md` to reflect Phase 5 completion.

## 2026-05-08 (Phase 4: Event Targeting API Integration)

### Backend Changes
- **Schemas:**
    - Renamed `targets` to `event_targets` in `app/schemas/event.py` for clarity and Phase 4 alignment.
    - Updated `EventCreate` and `EventUpdate` to accept `event_targets` list.
- **Routers:**
    - **CRUD:** Updated `app/routers/events/crud.py` with transaction-safe targeting logic.
    - **Backward Compatibility:** Implemented automatic migration of legacy `department_ids`/`program_ids` to `event_targets` if the new field is absent.
- **Models:**
    - Renamed `targets` relationship to `event_targets` in `Event` model.

## 2026-05-08 (Phase 3: Event Targeting Infrastructure)

### Backend Changes
- **Models:**
    - Created `EventTarget` model in `app/models/event.py` for scope-based targeting.
- **Database:**
    - Created and applied Alembic migration `b033a6f7e275` for the `event_targets` table.

## 2026-05-08 (Phase 2: Student Bulk Import Update)

### Backend Changes
- **Services:** Updated `app/services/import_validation_service.py` to support new columns: `School_ID`, `Year Level`, and `Status`.

### Frontend Changes
- **Views:** Updated `SchoolItImportStudentsView.vue` and the import preview list to display `Year Level` and `Status` tags.

## 2026-05-08 (Phase 1: Student Profile Stabilization)

### Backend Changes
- **Models:** Updated `StudentProfile` in `app/models/user.py` to include `student_status` (Enum) and `promotion_locked` (Boolean).
- **Database:** Created Alembic migration `0003_add_student_status`.
