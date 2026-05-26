# Changelog

All notable changes to the Aura (RIZAL) Flutter app are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this
project adheres to [Semantic Versioning](https://semver.org/). Pre-1.0 while
building toward full four-workspace parity: **each phase bumps the minor**, bug
fixes bump the patch, and **1.0.0** lands when all four workspaces ship.
`pubspec.yaml` `version:` tracks the latest entry as `<semver>+<build>`.

## [Unreleased]

## [1.28.1] - 2026-05-27

### Fixed
- **"Network error" on a real Android phone** when running
  `flutter run -d <device>` without
  `--dart-define-from-file=config/cloud.json`. The default in
  `lib/core/config/app_config.dart` was the Android-*emulator*-only
  host-loopback `http://10.0.2.2:8000`; on a real phone that hostname
  doesn't resolve and every API request failed. The default now points
  at the staging cloud backend (`http://18.142.190.113:8001`) so the
  flag is optional. The IP is already in the root README and Android
  network-security-config, so it's not a new secret. Override with
  `--dart-define=AURA_API_BASE_URL=...` for a different environment.
- **`config/cloud.json` had a stray colon** in the assistant URL
  (`":http://18.142.190.113:8500"`), which made the AI assistant
  unreachable whenever the flag *was* passed. Stripped the leading
  colon. (`config/cloud.json` is git-ignored — this only matters for
  contributors who already have the file checked out locally.)

### Changed
- **Liquid glass tab bar — icons now actually bend under the blob**
  (`lib/core/widgets/liquid_glass_nav.dart`). The old build used
  `LiquidGlass.withOwnLayer`, which wraps the shape in an internal
  `RepaintBoundary`; on Impeller the icon row sometimes got isolated
  from the BackdropFilter sample, so only the page beneath the nav
  bent. Now we manage the `LiquidGlassLayer` ourselves and wrap the
  icon row in a `RepaintBoundary` so its pixels are guaranteed to
  land in the parent compositing texture the lens samples. Lens
  settings boosted to iOS-26 territory:
  `thickness 24 → 32`, `refractiveIndex 1.4 → 1.55`,
  `chromaticAberration 4 → 6.5`, `lightIntensity 2.2 → 2.6`,
  `saturation 1.25 → 1.35`. The icon under the blob now reads as
  lensed (~6–8px displacement + visible chromatic fringe at the
  edges), matching the iOS Dynamic-Island feel.

## [1.28.0] - 2026-05-27

### Added
- **In-app branding swap (App appearance).** Account → **App appearance**
  lets the user choose whether the brand mark and app name use the Aura
  defaults or the signed-in school's logo + code. Two independent
  `SegmentedButton<bool>` controls (Brand mark · App name) plus a live
  preview card on top; defaults off until the user opts in. Premium
  layout — one focused `AuraCard`, calm hierarchy, JetBrainsMono for the
  school-code option, `AnimatedSwitcher` fade+scale between states.
  Tiles render even when the school has no logo / code uploaded yet (the
  toggle locks OFF with a friendly hint) so the user can see what's
  possible. Footnote explicitly sets expectation: the **home-screen icon
  stays as Aura** — see "Notes" below.
- **`AppBrandingPref` + `AppBrandingController`**
  (`lib/core/theme/app_branding_controller.dart`). Persists the two
  toggles **plus a snapshot of the school's metadata** (code, name, logo
  URL, primary / secondary hex, school id), refreshed every successful
  login via `captureSchoolSnapshot(meta)`. The snapshot lets the login
  screen and `MaterialApp.title` render the school brand on cold launch
  before any network round-trip, so returning users never see an
  "Aura → school" flash.
- **`SchoolLogoCache`** (`lib/core/cache/school_logo_cache.dart`).
  Disk-backed cache of the school logo bytes in
  `getApplicationSupportDirectory()/school_logo_cache/`, keyed by
  `school_id` + URL hash. After the first network fetch the logo loads
  from disk on every subsequent app launch — no re-download, no flash of
  the fallback initial. Web falls back to an in-memory map. Uses a fresh
  `Dio` instance (no auth interceptor — the logo endpoint is public).
  Cleared on logout.
- **`SchoolLogoImage`** (`lib/core/widgets/school_logo_image.dart`).
  `Image.network` replacement that consults `SchoolLogoCache` first and
  writes through on miss. Used inside `SchoolBadge` so every existing
  badge surface (account header, governance header, profile, etc.)
  inherits the disk-caching benefit transparently.
- **`AppBrandMark` + `AppNameText`** (`lib/core/widgets/app_brand_mark.dart`).
  Composite widgets that pick the Aura mark / wordmark vs. the school's
  logo / code from the `AppBrandingPref`. Drop-in for any chrome that
  previously hardcoded `AuraLogo` + `Text('Aura')`.

### Changed
- **`SchoolBadge` accepts an optional `schoolId`** and renders the logo
  via `SchoolLogoImage`. Callers in `account_tab.dart` pass the schoolId
  so cache keys are stable across logo updates.
- **`MaterialApp.title`** (`lib/app/app.dart`) is now reactive — it
  watches `appBrandingProvider` and uses `resolvedAppName()` so the
  title shown in the OS task switcher and browser tab follows the
  user's choice (Aura by default, the school's code when opted in).
- **`LoginScreen._Brand`** swaps the hardcoded `AuraLogo` chip +
  `Text('Aura')` for `AppBrandMark` + `AppNameText`. The "Aura" import
  on the login screen is now unused and removed.
- **`SessionController.completeLogin`** captures the school snapshot
  via `captureSchoolSnapshot(meta)` and fire-and-forget warms the
  `SchoolLogoCache` with `preload(url, schoolId)`. `logout()` clears the
  cache and snapshot but keeps the user's toggle choices so the same
  person logging back in picks up where they left off.

### Notes — what this deliberately does NOT change
- The **OS launcher icon** (the home-screen icon you tap to open Aura)
  stays as Aura. iOS `UIApplication.setAlternateIconName` and Android
  activity-aliases both require pre-bundled icon variants at build time
  — a school's uploaded logo can't become the OS icon at runtime. The
  settings card surfaces this as a small `info_outline` footnote so
  expectations stay correct.
- The same constraint applies to the **OS launcher label** (the text
  under the home-screen icon). The `MaterialApp.title` — which is what
  shows in the task switcher / app picker / browser tab — *is*
  reactive; the home-screen label is not.

## [1.27.2] - 2026-05-26

### Fixed (root cause for the v1.27.1 sign-in loop)
The actual bug behind "dashboard flashes then logs back out" turned out
to be a schema-vs-ORM type mismatch on the `user_sessions.token_jti`
column. Backend-side fix that takes effect after the migration runs.

- **`backend/alembic/versions/0010_user_sessions_token_jti_text.py`** —
  new migration. Runs
  `ALTER TABLE user_sessions ALTER COLUMN token_jti TYPE TEXT USING rtrim(token_jti)`.
  The `rtrim()` strips the trailing-space padding Postgres added when
  the column was CHAR(64), so rows that already exist resolve
  correctly after the migration; nobody has to re-sign-in. Unique
  constraint and the implicit unique-index are preserved across the
  type change.
- **`backend/alembic/schema.sql`** — fresh-DB bootstrap now uses
  `TEXT NOT NULL UNIQUE` instead of `CHAR(64) NOT NULL UNIQUE`, so
  a clean deploy doesn't reintroduce the same bug.

### Why the bug looked like a Flutter issue
Postgres CHAR is blank-padded. A 36-character UUID stored in CHAR(64)
becomes 36 chars + 28 trailing spaces. The ORM model declares
`token_jti = Column(Text, ...)` and SQLAlchemy binds the WHERE-clause
parameter as TEXT. Postgres's implicit cast between the padded CHAR
column and the TEXT parameter fails the equality test, so
`assert_session_valid` returns None for every freshly-issued JTI.
Login INSERT succeeds → JWT returned → very next authed request 401s
with "Session is not valid" → Flutter logs out → loop.

The v1.27.1 client-side mitigations (3-second login grace,
401-diagnostic logging, login-endpoint exclusion in `DioClient`) stay
in place — they're still defensible regardless of this specific bug
and give the next "logged out mysteriously" report a real lead to
chase.

### Deploy
Required on the cloud backend:
```
git pull origin main
docker compose -f docker-compose.prod.yml run --rm migrate
```
That single migrate run applies `0010` to the live DB. The frontend
needs no rebuild — the fix is purely server-side.

## [1.27.1] - 2026-05-26

### Fixed
- **"Sign in flashes the dashboard then returns to login" loop.** Three
  changes addressing the same root cause from different angles:
  - `DioClient.onError` no longer fires `onUnauthorized` for 401s on
    login-style endpoints (`/token`, `/login`, `/auth/google`,
    `/auth/forgot-password`). A 401 there means "wrong credentials",
    not "session invalidated" — calling `logout()` on the
    already-unauthenticated state was a no-op, but the path is now
    intentionally narrowed so future auth-flow refactors can't get this
    wrong.
  - `SessionController.handleUnauthorized` now honours a **3-second
    login grace window** after `completeLogin()`. A 401 in that window
    is ignored (likely a backend race committing the `user_sessions`
    row, or a parallel dashboard query crossing wires with token
    write). After 3s the normal logout-on-401 behaviour resumes.
  - **Diagnostic 401 logging in debug builds** — the failing
    `METHOD path → detail` is printed to console so future
    "logged out mysteriously" reports include the actual culprit
    endpoint without needing DevTools.

### Backend (deploy required for cloud)
- **`backend/app/services/auth_session.py` no longer silently swallows
  `create_user_session` exceptions.** The previous `try / except
  Exception: db.rollback()` returned a JWT to the client even when the
  `user_sessions` row failed to insert, leaving the client with a
  token whose `jti` was unknown to `assert_session_valid` — every
  authed request thereafter 401'd. Now logs the exception (with stack
  trace) and re-raises so login fails fast with a proper 500, instead
  of producing a "ghost session" that flashes the dashboard then logs
  the user out.

## [1.27.0] - 2026-05-26

### Added
- **Student-facing "My sanctions" screen.** Surfaces
  `GET /api/sanctions/students/me` data that the backend was already
  exposing but had no Flutter UI for. Account → Compliance → My
  sanctions (visible only to students). Summary chips for Pending /
  Cleared counts, an opt-in clearance-deadline banner that intensifies
  colour as the deadline approaches (`>72h` muted → `24–72h` tardy/amber
  → `<24h` absent/red), and one card per sanction record with a 4px
  coloured status bar at the top, status pill, and numbered penalty
  rows. Cleared penalties strike through + show the clearance
  timestamp.
- **`SanctionsRepository.mine()`** — `GET /api/sanctions/students/me`,
  returns the signed-in student's full sanction list.
- **`SanctionsRepository.activeClearanceDeadline()`** —
  `GET /api/sanctions/clearance-deadline`, returns the school-wide
  active deadline (null when none set).
- **`ClearanceDeadline` model** with `isUpcoming` + `hoursRemaining`
  helpers used by the banner heat-up logic.
- **`mySanctionsProvider` + `activeClearanceDeadlineProvider`** in
  `governance_providers.dart` (auto-dispose Riverpod futures).
- **API paths**: `Api.sanctionsMine`, `Api.sanctionsClearanceDeadline`.
- **`_OwnerLevelBadge` on the officer dashboard** — every event row in
  the governance Sanctions screen now shows an SSG / SG / ORG pill
  coloured from the existing brand tokens (`t.ssg` indigo, `t.sg`
  violet, `t.tardy` for ORG). Hierarchy is recognisable at a glance.
- **Diagnostic Android-build script** (`scripts/diagnose-android-build.ps1`).
  Runs `clean → pub get → analyze → build apk --debug` in sequence and
  stops on the first real Flutter error instead of the Gradle wrapper
  swallowing it.

### Changed
- **Gradle JVM heap dropped from 8G to 4G** in `android/gradle.properties`.
  The previous 8G heap left ~5G on a 16GB Windows machine for the
  Flutter Dart compiler + Defender + IDE; mid-build the OS swapped to
  disk, `flutter.bat` timed out internally, and `compileFlutterBuildDebug`
  exited 1 after ~34 minutes. 4G is plenty for our Gradle graph and
  leaves room for the rest of the toolchain.

### Design notes
- Every colour comes from `AppTokens` — nothing hardcoded.
- Status conveyed by colour + icon (per ui-ux-pro-max accessibility
  rule); pending uses `t.tardy` + hourglass, cleared uses `t.present`
  + check.
- Stagger entrance via the existing `staggered()` helper (50ms,
  ease-out), reduced motion respected by `RiseIn`.
- Mono numerals (`AppTypography.mono`) for counts so data is distinct
  from prose; matches the Help Center step style.

## [1.26.1] - 2026-05-26

### Security
Client-side hardening of every Flutter-controllable surface while the
backend still runs HTTP. Wire traffic remains cleartext to the IP-based
staging backend (only HTTPS deployment closes that hole) — everything
else tightens.

#### Network
- **Android Network Security Config**
  (`android/app/src/main/res/xml/network_security_config.xml`).
  Base policy: `cleartextTrafficPermitted="false"`. A narrow
  `<domain-config>` whitelists HTTP only for `18.142.190.113`, `10.0.2.2`,
  `127.0.0.1`, `localhost`. Any other HTTP destination is rejected at the
  network stack. `<debug-overrides>` intentionally omitted so a MITM CA
  can't be installed on a dev device by accident.
- **iOS App Transport Security** rewritten. `NSAllowsArbitraryLoads`
  removed (App Store would reject it anyway). Replaced with
  `NSExceptionDomains` scoped to `18.142.190.113` /
  `localhost` / `127.0.0.1` only; the staging exception requires
  `NSExceptionMinimumTLSVersion = TLSv1.2`.
- **`android:usesCleartextTraffic="true"`** removed from
  `AndroidManifest.xml` (superseded by the network security config).
- **Application-layer HTTPS guard** in `DioClient`
  (`_assertSecureInRelease`). Release builds compiled with a plain-HTTP
  base URL throw `StateError` before the first request fires. Debug
  builds remain permissive for development.
- **TLS certificate-pinning hook** wired as `_pinTlsCertificates` —
  currently a no-op (no HTTPS to pin against yet); flips to enforce a
  SHA-256 SPKI pin the moment the backend ships HTTPS. Code + docs
  ready.

#### Data at rest
- **Android backups disabled.** `AndroidManifest.xml` sets
  `android:allowBackup="false"`, `android:fullBackupContent="false"`,
  and `android:dataExtractionRules="@xml/data_extraction_rules"`. New
  `data_extraction_rules.xml` excludes every path from both
  `cloud-backup` and `device-transfer`, so `adb backup` and Android 12+
  flows cannot pull the EncryptedSharedPreferences blob holding the
  access token.
- Existing JWT storage already used `flutter_secure_storage` with
  `encryptedSharedPreferences: true` (Keystore-backed on Android,
  Keychain on iOS) — unchanged.

#### Reverse-engineering
- **Release-build script for Android**
  (`scripts/build-release-android.ps1`) invokes `flutter build apk` with
  `--obfuscate --split-debug-info=build/symbols/<version>
  --tree-shake-icons`. Dart symbols are replaced with short tokens in
  the APK; the symbol map ships out-of-band so a crash stack trace from
  the wild can't be symbolicated without it.
- **Release-build script for iOS** (`scripts/build-release-ios.ps1`)
  mirrors the Android flags for `flutter build ipa`.

#### Request hygiene
- `X-Requested-With: AuraApp` sent on every request so the backend can
  distinguish app traffic from browser-form-style POSTs if it ever adds
  CSRF heuristics.
- No `User-Agent` override (custom UAs are a fingerprinting hint —
  let Dart's default speak for itself).

### Fixed
- `analysis_options.yaml` excludes `third_party/**` so `flutter analyze`
  no longer reports the vendored `liquid_glass_renderer` package's
  upstream lint findings (it would otherwise show ~9k issues from the
  vendored shader code; none in app source).

### Notes — what this does NOT fix
- The base URL in `cloud.json` is embedded in the compiled binary;
  with HTTPS deployed, leaking the URL is harmless because bytes on
  the wire are encrypted. **Production HTTPS is still required.**
- TLS certificate pinning is wired but disabled until the backend
  ships HTTPS. Flip `_pinTlsCertificates` live once a real cert is
  reachable.

## [1.26.0] - 2026-05-26

### Added
- **Real Google sign-in.** "Continue with Google" on the login screen is
  now functional. New `GoogleSignInService` reads
  `AURA_GOOGLE_WEB_CLIENT_ID` via `--dart-define`, drives the
  `google_sign_in` SDK (web + native), and posts the resulting ID token to
  `POST /auth/google`. Backend errors translate to actionable copy:
  - 403 (Google login disabled) → "Google sign-in is disabled for this
    deployment. Use your school email and password instead."
  - 404 (email not registered) → "No Aura account is linked to that
    Google email. Ask your Campus Admin to register your school email
    first."
  - 401 (invalid token / unverified email) → "Google could not verify
    your account. Make sure your Google email is verified and try
    again."
  - Not configured (empty client ID) → "Sign in with Google isn't
    enabled for this app yet." Service refuses to attempt sign-in.
  - User cancels → silent (no error banner). `AppConfig` gains
    `googleAndroidClientId` + `isGoogleSignInConfigured` helper.
- **Real forgot-password flow.** Replaced "Reset it in the web app for
  now" with a `ForgotPasswordDialog` (Card-styled modal with reset-icon
  badge, email field, Cancel/Send actions, loading + error states). It
  calls `AuthRepository.forgotPassword(email)` → `POST /auth/forgot-password`
  → backend's generic admin-approval message → snackbar. Pre-fills the
  email from the login form. Validates locally for empty/no-@ before
  hitting the network.
- **Public Help Center from the login screen.** New "Need help?" link
  beside "Forgot your password?" opens
  `HelpCenterScreen(audience: HelpAudience.public)` — a trimmed
  catalogue (no privileged or dev-docs content) for unauthenticated
  visitors.
- **Role-based Help Center.** New `HelpAudience` enum
  (`public`/`student`/`campusAdmin`/`governance`/`admin`) tagged on every
  category and on individual articles. The screen derives the viewer
  from the current session — students see attendance + AI + their own
  workflow; campus admins see manage-users / imports / governance setup;
  governance officers see event-management; super-admins see everything
  plus the new Developer docs. Quick-help chips and search are filtered
  to the viewer's tier.
- **Developer docs section (admin-only).** New `developer-docs` category
  visible only to platform admins, with 8 quick-reference articles
  sourced from `docs/technical/`: architecture, tech stack, API
  reference, database/migrations, deployment/CI/CD, local dev setup,
  testing strategy, and SaaS billing + subscription state. Each article
  points to the canonical source-of-truth in the in-repo docs tree.
- **Forgot-password help article.** New `ac-forgot-password` article in
  the Account category, public-visible, with step-by-step admin-approval
  flow. Promoted to the first Quick-help chip ("Forgot password").
- **Audience-aware screen UX.** `_IntroHeader` writes a per-tier
  subtitle ("Attendance, schedule, your account…" for students,
  "Operations, developer docs, and SaaS billing…" for admins).
  `_QuickHelpRow` accepts a pre-filtered list of entries so chips never
  link to articles the viewer can't see.

### Changed
- **Help search bar polish.** Surface-light fill in idle, surface-white
  + accent ring + soft accent-tinted shadow on focus. Search icon
  scales 1.08× when focused. Clear button is now a circular soft chip
  with `AnimatedSwitcher` fade/scale entry. Cursor uses the brand
  accent. Hint copy clarified to "Search guides, FAQ, troubleshooting…"
- **Bottom nav semantics.** `_NavButton` in `glass_bottom_nav.dart` and
  `_NavItem` in `liquid_glass_nav.dart` now wrap the inner button in
  `ExcludeSemantics` and add `container: true` on the parent
  `Semantics` so `find.bySemanticsLabel('Home' | 'Schedule' | …)`
  returns the bottom-nav nodes cleanly (the prior tree merged the child
  Text's label, masking the parent label and breaking
  `ui_quality_test`).
- **Quick-help line-up.** "Forgot password" and "Install the app" join
  the chip row; "Change password" article remains in the Account
  category but is no longer a chip (the forgot-password flow is what
  users actually need pre-signin).
- **Login screen layout.** Footer links use `Wrap` (instead of `Row`)
  so the "Forgot your password? · Need help?" pair wraps to two lines
  at mobile widths instead of overflowing.

### Fixed
- **`ui_quality_test.dart` semantics handle leak.** The
  `key app controls expose accessible semantics labels` test now
  disposes the `SemanticsHandle` via `try/finally` so dispose runs
  before `_endOfTestVerifications` (addTearDown ordering left a stray
  handle and tripped the "SemanticsHandle was active at end of test"
  assertion once the body actually reached the end).

### Verified
- `flutter analyze` clean.
- `flutter test` — 120 tests pass (115 existing + 5 new audience
  filtering tests in `test/unit/help_content_test.dart`).

## [1.25.0] - 2026-05-26

### Added
- **In-app Help Center.** A new "Help Center" tile under Account → Support
  opens a dedicated, searchable help surface that mirrors the
  `docs/user-guide/` content. **9 categories, 45 articles** written as
  step-by-step actions rather than prose: Getting started, Attendance &
  events, Your account, Schedule & events, Aura AI assistant, For staff &
  officers, Troubleshooting, Security & good practice, and About Aura.
  - **Search** is the hero — a focus-animated pill that filters every
    article live, with a 120-char snippet centred on the match and a
    category-coloured badge above each result. Empty-state suggests common
    queries (login, face, password, permissions, late, reset).
  - **Quick-help chips** above the search field deep-link straight into
    the top-asked articles (cannot log in, face scan failed, change
    password, grant permissions).
  - **Accordion category cards** with an animated chevron, tinted icon
    tile, and a JetBrains Mono count pill. Tap → reveal the article list
    via `AnimatedSize`/`ClipRect`; honours `MediaQuery.disableAnimations`.
  - **Article bottom sheet** (`DraggableScrollableSheet`, initial 0.75,
    drag 0.45–0.95) shows the category chip, headline-sized title, body,
    numbered steps (mono numerals in a tinted square), and an optional
    italic tip callout with a left accent bar.
  - **Contact card** with three tap-to-copy rows — Campus Admin email, IT
    support email, full documentation URL — using `Clipboard.setData` and
    a confirmation snackbar.
  - **Footer** prints `Aura v{version} · build {build} · powered by Jose
    AI` in mono.
  - Motion follows `AppMotion`: ease-out under 300ms, press scale 0.97,
    50ms stagger entrance, reduced-motion respected. Manrope display +
    body, JetBrains Mono for numerals.
  - New files: `lib/features/help/data/help_content.dart` (pure-data
    catalogue with `HelpCategory`, `HelpArticle`, `search()`,
    `findArticle()`, `findCategory()`) and
    `lib/features/help/presentation/help_center_screen.dart`.
  - Wired into `account_tab.dart` as a new "Support" `SettingsSection`
    between Security and Workspaces — rose-coloured
    `Icons.help_outline_rounded` tile with subtitle "Guides, FAQ,
    troubleshooting & contact".
  - **12 new unit tests** in `test/unit/help_content_test.dart` lock the
    catalogue's invariants: unique category and article IDs, non-empty
    bodies and steps, case-insensitive search, keyword-list matching, and
    quick-help link integrity. analyze clean, 54 tests.

## [1.24.0] - 2026-05-23
### Added
- **Edit governance events.** The event monitor screen now has an Edit action
  (gated by `manage_events`) that opens the editor **prefilled from the event**
  and saves via `PATCH /api/events/{id}` (`EventsRepository.update`,
  `EventEditorScreen(event:)`), scoped by `governance_context`; the geofence can
  be changed or turned off. `DioClient.patch` now forwards query params.
### Notes
- Event **creation** still returns HTTP 500 from the backend (cloud **and**
  local). Traced server-side: a valid `EventCreate` payload (name + start/end,
  status defaults to `upcoming`) reaches the handler and fails during processing —
  most likely the deployed/local DB is missing newer `events` / `event_targets`
  columns because migrations didn't run (those columns live only in `schema.sql`,
  not a versioned alembic migration). The app sends a correct request; the fix is
  a backend migration/redeploy, not a client change.

## [1.23.2] - 2026-05-23
### Fixed
- **Governance Members screen had no back button** when opened from a dashboard
  quick action (e.g. after drilling into a child SG/ORG), and its title sat under
  the status bar. It's now wrapped in `AppScaffold` like the Events screen — a
  proper "Members" app bar with an automatic back button when pushed, the "Add
  officer" action moved into the app bar, and the unit name shown as a context
  line. Still works as a bottom-nav tab.

## [1.23.1] - 2026-05-23
### Changed
- **App name is now "Aura"** (was `aura_app`) — Android `android:label` + iOS
  `CFBundleDisplayName`.
- **Real launcher icon.** The Aura mark now ships as the app icon: legacy density
  buckets (mdpi–xxxhdpi) **plus an Android adaptive icon** (`mipmap-anydpi-v26`,
  the mark centred in the safe zone over a near-black background) so it renders
  correctly on Android 12+. Sourced from the clean `pwa-512` brand asset — the
  `frontend-apk` icon copies were CRLF-corrupted (an extra `0D` in the PNG header)
  and undecodable.

## [1.23.0] - 2026-05-23
### Added
- **Governance hierarchy management UI (SSG → SG → ORG).** Officers can now build
  the governance tree in-app — the backend already supported it, but Flutter had no
  view to do it.
  - **Create child units.** A permission-gated action on the governance dashboard:
    "Create college SG" (when an SSG officer holds `create_sg`) and "Create program
    ORG" (when an SG officer holds `create_org`); locked with a "Not permitted"
    tooltip otherwise. New `UnitCreatorScreen` (`unit_creator_screen.dart`) — SG mode
    shows a college picker (`govDepartmentsProvider`), ORG mode shows the college
    inherited from the parent SG plus a program picker scoped to that college
    (`Program.departmentIds`); it sends `department_id` / `program_id` per the backend
    contract and surfaces validation errors (e.g. one SG per college) inline.
    (`governance_repository.createUnit`, `createGovernanceUnit` helper)
  - **Child units + drill-in.** The dashboard lists child units (SGs under an SSG,
    ORGs under an SG); tapping one switches the workspace into it — carrying the
    management permissions the backend propagates from a *direct* parent membership
    (`manage_members` / `assign_permissions`) — with a back control to return.
  - **Empower officers down the chain.** A shared `OfficerEditor`
    (`officer_editor.dart`) replaces the SSG-only one and offers exactly the
    permissions each unit type allows (matching the backend whitelist — only SSG can
    grant `create_sg`, only SG `create_org`). Wired into the campus-admin SSG panel and
    the governance Members screen (add **and** edit officers with position +
    permissions), so an SSG can appoint SG officers and an SG can appoint ORG officers.
### Changed
- `GovernanceUnitSummary` now parses `department_id` / `program_id`; `GovUnitAccess`
  gains `fromSummary` for tap-to-switch. The Members screen's add flow moved from a
  search-only bottom sheet to the full `OfficerEditor`.

## [1.22.1] - 2026-05-23
### Added
- **Personalized greeting.** The Aura AI chat opens with an instant, client-side
  greeting — "Hi <name>! I'm Aura, powered by Jose AI …" (no model call, no waiting).
  (`chat_controller.dart`)
### Fixed
- **Don't mislabel a slow model as unreachable.** The chat now waits up to 5 min for a
  reply (`receiveTimeout` 300s) and, on a timeout, says "Aura is taking a while to
  think" — "could not reach" is now reserved for a real connection failure
  (`DioException` type check). (`assistant_service.dart`, `chat_controller.dart`)
- **Fast/Think toggle overflow.** Moved the segmented control out of the cramped app
  bar to a row above the input. (`chat_screen.dart`)
- Local model stays warm (`run_local.ps1` adds `--mlock`) so replies don't crawl after
  idle (cold ~64s → ~6s).

## [1.22.0] - 2026-05-23
### Added
- **Assistant Fast / Think toggle.** A compact segmented control in the Aura AI app
  bar switches the assistant between **Fast** (slim prompt, no tools — quick replies,
  ideal for the on-device/local model) and **Think** (full prompt + data tools +
  charts, slower). Persisted (`fast_mode_controller.dart`); sent per message
  (`fast: bool`) and honored per request by the backend. Sliding accent pill,
  ease-out, reduce-motion aware, tooltips, no emoji.
  (`chat_screen.dart` `_ModeToggle`, `assistant_service.dart`, `chat_controller.dart`)

## [1.21.0] - 2026-05-23
### Added
- **Aura AI renders charts.** The assistant chat now parses the backend's
  `visualization` SSE events (Chart.js-style spec) and draws them inline with
  `fl_chart` — bar / line / pie / doughnut, themed, with a legend
  (`features/assistant/presentation/widgets/assistant_chart.dart`,
  `ChartSpec` + `AssistantChart`). `assistant_service.dart` now captures the
  `visual` payload, `chat_controller.dart` attaches parsed charts to the reply,
  and `chat_screen.dart` renders text **and** charts in the bubble. Previously the
  client dropped these events (text-only).
### Changed
- AI assistant identity is now **"Aura, powered by Jose AI"** (assistant *backend*:
  new `assistant/assistant_identity.py` prepended to the system prompt; `.env`
  points at a local llama.cpp server serving `jose.gguf`). Setup in
  `assistant/RUN_LOCAL_JOSE.md`. No change to the Flutter app to use the local model.

## [1.20.2] - 2026-05-23
### Fixed
- **Smoother settings (and any long-list) scrolling.** `RiseIn` was replaying its
  rise/fade — and running an `Opacity` layer — every time a row mounted, which a
  `ListView` does lazily *while scrolling*. Now only the initial on-load burst
  animates (a shared reveal window opened by the list head); rows scrolled into view
  render instantly with no wrapper. (`rise_in.dart`)

## [1.20.1] - 2026-05-23
### Fixed
- **Export no longer stalls at 60% ("Adding brand logo").** The logo + student
  roster are cached per session and fetched **in parallel** with stats/attendees
  (was sequential, with the logo blocking last on an 8s timeout). Logo timeout cut
  to 3s; the "Adding branding" blocking step is gone. Repeat exports skip the fetches
  entirely → ~1–5s typical. (`export_sheet.dart`)
- **Smooth light/dark switch.** `AppTheme.light/dark` are now memoized — the
  expensive `ColorScheme.fromSeed` was being recomputed on every app rebuild (and
  both themes every time), which caused the toggle jank. (`app_theme.dart`)
- **Trimmed the crowded Beta-features descriptions** to one short line each
  (`account_tab.dart`).

## [1.20.0] - 2026-05-23
### Added
- **Background event check-in notifications + one-tap check-in.** With "Nearby
  event check-in" on, the app registers OS-level geofences (`native_geofence`) for
  the user's ongoing geofenced events; entering one fires an OS notification
  ("You're at <event> — tap to check in") **even when the app is closed**, and
  tapping it opens the **attendance / face-scan screen directly** (deep-link via
  `pendingCheckInProvider` → `student_home` listener). `geofence_background.dart`
  (background isolate callback) + `flutter_local_notifications`. The 1.19.0
  in-app prompt still works in the foreground.
- **"Beta features" settings group** — Account groups the experimental toggles
  (Liquid glass tab bar, Nearby event check-in) into an iOS-style section with BETA
  pills, plus a new **Auto check-in** toggle (BETA) that shows **"Coming soon"**
  (hands-free, no-scan check-in — placeholder, `autoCheckFullProvider`).

### Changed
- Android: core library desugaring enabled (`app/build.gradle.kts`) +
  geofence/notification permissions + native_geofence receivers/service in the
  manifest. iOS: background-location usage string + `UIBackgroundModes` in Info.plist.
- Swapped `geofence_service` → `native_geofence` (OS geofences are Android-14-safe —
  no typed foreground service needed).

### Notes
- The background trigger + notification need **on-device field testing** (walk into a
  geofenced event) and a geofenced event to exist (after the backend redeploy).
  Gated behind the off-by-default toggle. analyze clean, 42 tests, debug APK builds.

## [1.19.0] - 2026-05-23
### Added
- **Nearby event check-in (opt-in).** Account → Preferences → **"Nearby event
  check-in"** (off by default, persisted — `auto_checkin_controller.dart`). When on,
  while the student Home is open the app polls device location — but only when
  there's an ongoing **geofenced** event to match — and if the student is inside an
  event's radius it shows an in-app prompt (`NearbyEventBanner`): tap **Check in** to
  go straight to the face scan, no navigating to the event. Detection in
  `nearby_event_provider.dart` (latlong2 distance vs `ongoingEventsProvider` +
  `geolocation_service`). Nothing hardcoded — radius/centre/window come from each
  event.

### Notes
- Foreground only (works while the app is open). True always-on background geofence
  + OS push would need `flutter_local_notifications` + background-location + a
  foreground service (future work). analyze clean, 42 tests.

## [1.18.2] - 2026-05-23
### Fixed
- **Liquid nav stopped rendering (esp. on web).** Reverted the blob from the
  `liquid_glass_widgets` `GlassPanel` (which 404s its shaders on web) back to
  `liquid_glass_renderer`'s `LiquidGlass`, and removed the `kIsWeb` guard that had
  disabled the Liquid nav on web. It renders again on web **and** mobile (real
  refraction on Impeller). `main.dart` no longer needs `initialize()`/`wrap()`.

### Added
- **BETA pill** on the "Liquid glass tab bar" toggle (`account_tab.dart`,
  `_BetaPill`).

## [1.18.1] - 2026-05-23
On-device refinements (tested on an entry-level Android).

### Fixed
- **Manrope rendered super-thin.** The bundled Manrope is a **variable** font but
  its weight axis wasn't being driven, so every weight looked thin/unreadable. Now
  set `fontVariations: [FontVariation('wght', …)]` per style (`app_typography.dart`)
  so regular/medium/bold render correctly.
- **Laggy light↔dark switch** on low-end GPUs — set
  `themeAnimationDuration: Duration.zero` (`app.dart`); the animated cross-fade was
  re-rendering the glass nav every frame.
- **School logo** now shows the school letter while the network image loads instead
  of a blank disc (`school_badge.dart`, `loadingBuilder` + `gaplessPlayback`).

### Changed
- **Dropped the package `GlassBottomBar` option** (kept the custom **Liquid** nav,
  which won on device). The beta control is back to a simple **Off / Liquid** switch
  (`beta_controller.dart` is a bool again; `app_shell.dart` no longer imports
  `liquid_glass_widgets`, which is now used only by the Liquid blob).

## [1.18.0] - 2026-05-23
### Added
- **iOS 26 liquid glass via `liquid_glass_widgets`** + a **3-way nav selector**
  (Account → "Liquid glass tab bar": **Off / Liquid / Glass bar**, persisted, fully
  reversible). **Liquid** = the custom animated capsule blob, now rendered with the
  package's `GlassPanel` (shader refraction). **Glass bar** = the package's
  `GlassBottomBar` (iOS-26 bar, `standard` quality + `maskingQuality.off` so it
  stays smooth on older/entry-level GPUs) for comparison. `main.dart` calls
  `LiquidGlassWidgets.initialize()` + `wrap()`.

### Changed
- The beta nav flag (`beta_controller.dart`) is now an enum `BetaNavStyle` (was a bool).

### Fixed
- **Android build** — `camera_android_camerax` (camera-core 1.5.x) failed to compile
  ("CallbackToFutureAdapter not found"); inject `androidx.concurrent:concurrent-futures`
  into that module (`android/build.gradle.kts`).

### Notes
- The glass shaders need **Impeller (mobile/desktop)**; on **web** the package 404s
  its shaders, so web skips `initialize()`/`wrap()` and the nav falls back to the
  standard frosted nav (`kIsWeb` guards). Test the glass on a device/emulator.
- analyze clean, 42 tests, debug APK builds.

## [1.17.13] - 2026-05-23
### Changed
- **Beta nav blob: no edge overlap.** The blob clamps to the pill's inner bounds,
  so on the first/last tab its edge **compresses** instead of spilling out of the
  pill. The tap/slide zoom still pops out.

## [1.17.12] - 2026-05-23
### Changed
- **Beta nav blob: always a wide pill (even with many tabs) + bigger.** The blob
  now has a minimum width (≥ 1.6× its height) and is centered on the tab, so it
  stays a horizontal pill instead of a circle on 5-tab bars (it can overflow the
  slot/pill — that's fine). Taller resting size and a bigger tap/slide zoom (1.4×)
  that pops out of the pill.

## [1.17.11] - 2026-05-23
### Changed
- **Beta nav blob bigger at rest.** The resting blob is now larger (≈ the old
  zoomed size — taller `_blobH` 62, smaller side gap), so tap/slide zooms to an
  even bigger size.

## [1.17.10] - 2026-05-23
### Changed
- **Beta nav blob: zoom on tap too, faster, no stretch.** The blob no longer
  stretches/elongates — it just **slides + zooms**. Tapping now zooms (a quick
  pop in/out) like dragging does, and the slide is faster (240ms).

## [1.17.9] - 2026-05-23
### Changed
- **Beta nav blob: Dynamic-Island capsule that zooms while sliding.** The blob is
  rendered outside the pill clip (`Clip.none`) and **zooms bigger (1.32×) while you
  drag** — popping out of the pill like a Dynamic Island — settling back on release.
  Shape is a horizontal capsule (radius = height/2, width > height).

## [1.17.8] - 2026-05-23
### Changed
- **Beta nav blob: wider pill, pop-on-tap, clearer refraction.** The blob fills
  more of its slot (a real horizontal pill, not an oval), **pops bigger** on tap
  then settles back to a normal pill, and the frosted pill is lighter/less-blurred
  so the page shows through — making the blob's refraction (thickness 28,
  refractiveIndex 1.5, chromatic aberration 5) actually visible.

## [1.17.7] - 2026-05-23
### Changed
- **Beta nav: smooth drag, glitch-free tap.** The blob now follows the finger
  **continuously** while dragging (a free fractional position) instead of snapping
  tab-to-tab, and settles to the nearest tab on release. Tapping animates the blob
  from its real current position with the elastic stretch, so it no longer glitches.
  The active icon colour tracks the blob during the drag.

## [1.17.6] - 2026-05-23
### Changed
- **Beta nav blob is now a proper pill.** Its corner radius equals half its height
  (fully rounded ends) and it's a bit shorter with a smaller side gap, so it reads
  as a horizontal capsule instead of a rounded square / vertical oval.

## [1.17.5] - 2026-05-23
### Changed
- **Beta liquid glass nav — elastic blob + centered icons.** The blob now
  **stretches** as it slides between tabs (restores the liquid feel on both tap and
  drag) via a stateful elastic animation — the leading edge leads and the trailing
  edge lags (two eased curves). Reshaped to a content-fitting rounded blob (was a
  tall oval) and the icons + labels are now properly centered in each slot.

## [1.17.4] - 2026-05-23
### Changed
- **Beta liquid glass nav — bigger pill, drag-to-slide, and real refraction.** The
  pill is taller (82) with roomier icons/labels; the blob now slides via **tap or
  drag** (`onHorizontalDragUpdate`). The frosted pill tint is now **translucent
  dark** so the page shows through it — giving the `liquid_glass_renderer` blob
  actual light to **refract** (refractiveIndex 1.45 + thickness 24 + chromatic
  aberration). The refraction is on the **blob only**; the back pill stays frosted.

## [1.17.3] - 2026-05-23
### Changed
- **Beta liquid glass nav — visual rework** to match the iOS reference. Replaced
  the package-styled bar with a custom `core/widgets/liquid_glass_nav.dart`: a
  neutral **frosted, tinted pill** (pure UI — no backend brand colour, same size
  and pill shape as the standard nav) holding a **colourless `liquid_glass_renderer`
  blob** that slides to the active tab. Only the **active icon + label** takes the
  university **primary** colour (animated). `liquid_bottom_nav_bar` is no longer
  used by the shell.

## [1.17.2] - 2026-05-23
### Changed
- **Smoother tab switching (all roles).** The view transition is now a
  state-preserving **cross-fade** — the outgoing view fades out as the incoming
  fades in, with no slide and no blank flash (was an abrupt slide-in that left a
  gap). `_AnimatedTabStack` in `app_shell.dart`.
- **Beta liquid nav: the blob now slides on tap.** Added an explicit snap
  `animationDuration` (320ms) + `easeOutCubic` curve so tapping a tab glides the
  liquid blob to it instead of teleporting.

## [1.17.1] - 2026-05-23
### Changed
- **Beta liquid glass tab bar is now real liquid glass.** The beta nav is wrapped
  in a `liquid_glass_renderer` `LiquidGlass` pill (transparent
  `liquid_bottom_nav_bar` container) for genuine refraction with **chromatic
  aberration** over the page behind it, plus light/thickness tuned for the native
  iOS look. The shape is now a **pill** (was a rounded square — the radius was
  smaller than half the bar height). Impeller-only; stays behind the beta toggle.

## [1.17.0] - 2026-05-23
Beta: opt-in iOS liquid glass tab bar (all roles).

### Added
- **Liquid glass tab bar (Beta)** — Account → Preferences → "Liquid glass tab bar".
  When on, every workspace's bottom navigation becomes an iOS-style liquid bar
  (`liquid_bottom_nav_bar`: liquid blob animation + glass blur, themed with the
  brand accent); off keeps the standard nav. The choice is persisted
  (`core/theme/beta_controller.dart`) and the toggle warns it's beta and may lag on
  low-end devices.

### Notes
- analyze clean, 42 tests.

## [1.16.2] - 2026-05-23
Event creation fixed; PDF font + Events-screen crash fixed; report names + progress.

### Fixed
- **Creating an event failed** (looked like an "internal server error"). The
  **deployed backend requires `location`**, but the form only sent it when
  non-empty — confirmed live: `422 {"loc":["body","location"],"msg":"Field
  required"}`. The venue field is now required and always sent.
- **Governance "Events" showed a red Flutter error** when opened from the
  dashboard quick action — the screen was a bare `Column` with no `Material`
  ancestor, so its `ChoiceChip`/`TextField` threw "No Material widget found".
  Wrapped in `AppScaffold` (works as a tab and when pushed; the create "+" moved
  to the app bar).
- **PDF export failed on dashes** — the built-in Helvetica font can't draw
  "–"/"—" (U+2013/U+2014). All report text is now sanitized to Latin-1
  (typographic glyphs → ASCII).

### Added
- **Report attendee columns: Name | Student ID | Time in | Time out | Status** —
  names/numbers resolved via `GET /api/governance/students`.
- **Real step progress bar** on export (Loading attendance → Matching names →
  Branding → Building), not a fixed-duration dummy.

### Notes
- analyze clean, 42 tests.

## [1.16.1] - 2026-05-23
### Fixed
- **Report export (PDF / Excel / CSV) hung and lagged the app.** Byte generation
  ran on the UI isolate — the heavy PDF/XLSX building froze the app, and a slow
  logo fetch could spin forever. Generation now runs in a **background isolate**
  (`compute`) and the logo fetch has an 8s timeout, so the sheet stays responsive
  and the share dialog opens promptly.

## [1.16.0] - 2026-05-23
Governance event creation + a map view with range on events.

### Added
- **Governance officers can create events.** The governance Events screen (and the
  dashboard quick action) now has a **New event** button — shown when the unit
  grants `manage_events` — opening the event editor scoped to the unit via
  `POST /api/events?governance_context=SSG|SG|ORG` (the backend auto-scopes
  department/program). The new event appears under the unit immediately.
- **Map view with range** on events — a read-only `EventLocationMap`
  (`core/widgets/event_location_map.dart`) showing the geofence centre + radius
  circle, on the **event detail** (student) and **governance monitor** screens.

### Notes
- analyze clean, 42 tests.

## [1.15.0] - 2026-05-23
University logo now displays everywhere; secondary brand colour applied.

### Fixed
- **University logo never displayed.** The backend returns `logo_url` as a
  **relative** path (`{public_prefix}/{file}`); the app rendered it raw and every
  check gated on `startsWith('http')`, so it was silently dropped. Added
  `core/network/media_url.dart` (`mediaUrl()`) to resolve relative paths against the
  backend root, used wherever the logo is shown (account, settings, export, …).

### Added
- **`SchoolBadge`** (`core/widgets/school_badge.dart`) — the school logo inside a
  primary→secondary **gradient ring** (so the **secondary brand colour is now
  used**), with an initial fallback. Placed next to the greeting/name on the
  **student** and **school-IT** home, in the **governance** header, the **account**
  profile card, and the **profile** screen (with the university name).

### Notes
- analyze clean, 42 tests.

## [1.14.0] - 2026-05-23
Campus-admin Student Government panel; blank University settings fixed.

### Fixed
- **University settings was a blank screen** — a full-width `AuraButton` (the
  "Choose" logo button) sat directly inside a `Row` (unbounded width), throwing an
  infinite-width layout assertion that failed the whole body subtree. Constrained
  it. (Not a backend or data problem — confirmed from the render exception.)

### Added
- **Campus-admin "Student Government" panel** (School-IT home → Student Government):
  auto-creates the school **SSG** (`GET /api/governance/ssg/setup`) and lets the
  campus admin **add / edit / remove the President & officers** — search a student,
  set the position title, and grant per-officer permissions. New repository methods
  `ssgSetup()` + `updateMember()`.

### Notes
- analyze clean, 42 tests.

## [1.13.1] - 2026-05-23
### Fixed
- **Assigning an "Unassigned" student now works.** Users-by-College was listing
  non-student accounts (which have no student profile, hence no "Assign to a
  college" action) under "Unassigned". The view is now restricted to actual
  students, so every entry under "Unassigned" is assignable (open it → "Assign to
  a college").

## [1.13.0] - 2026-05-23
Critical pagination fix, governance→student switch, localization.

### Fixed
- **Users list pagination.** The backend paginates by **`page`** and ignores
  `skip`; the previous skip-loop re-fetched page 1 repeatedly → **duplicate
  accounts, very slow / endless skeleton loading, "--" counts**, and accounts past
  the first page never loaded (the "already exists but can't find it" account —
  e.g. `aclaogloryzann30@gmail.com`, id 2232, COE — sat on page 2). Now walks
  `page=1..total_pages` with de-dup.
- **Governance "Switch to student"** now actually opens the student view (was a
  no-op `maybePop`).

### Added
- **System language** support — `flutter_localizations` delegates + supported
  locales (en, fil); the app follows the device language for Material widgets and
  date/number formatting.

### Notes
- analyze clean, 42 tests.

## [1.12.0] - 2026-05-23
Fixes: full user list, schedule filters, college management.

### Fixed
- **Users by college now loads ALL users** (paginated). A newly-created account on
  a large school (e.g. JRMSU) sat beyond the first page (id ASC), so it was
  invisible to the list + search even though it existed — the "already exists but
  can't find it" bug.
- **University settings no longer shows a blank screen** — it renders from the
  in-token branding instantly (name/code/logo/colours); the network call only
  refreshes.

### Added
- **Schedule filter pills** (All / Today / Upcoming / Past) in every calendar.
- **Rename / Delete a college** from each college card (⋯ menu); unassigned
  students remain assignable to a college from the student detail.

### Notes
- analyze clean, 42 tests.

## [1.11.0] - 2026-05-23
Student analytics polish.

### Added
- **Insights** redesigned: attendance **arc gauge**, a **Now & next** section
  (ongoing + upcoming events), present/late/absent/excused/incomplete breakdown,
  monthly trend, an **event-type pie**, and recent events with per-event status.

### Notes
- Completes the governance dashboard / calendars / analytics plan
  (1.9.0 → 1.11.0). analyze clean, 42 tests.

## [1.10.0] - 2026-05-23
Calendars with search for all three workspaces.

### Added
- **Calendars** (`core/widgets/event_calendar.dart`, table_calendar) with
  status-colored day markers, a selected-day list, and **search**:
  - Student "Schedule" — their events; tap → detail + status.
  - School-IT "Schedule" — all school events (upcoming/ongoing/done) + new event.
  - Governance "Events" — scoped to the active unit (its college/org).

### Notes
- analyze clean, 42 tests.

## [1.9.0] - 2026-05-23
Governance event-management dashboard, report export, and a map event picker.

### Added
- **Governance dashboard** rebuilt: shows the officer's **position**, a compliance
  **arc gauge**, real metric chips, **permission-aware quick actions** (greyed +
  locked when not permitted), and a **Manage events** list with a **live
  attendance progress bar** for ongoing events (15s polling).
- **Export an event report** to **PDF / CSV / XLSX** (university logo + name,
  college, date/time, schedule, attendance summary + attendee list) —
  `features/reports/event_report_service.dart` + `ExportSheet`.
- **Event-creation form** redesigned (sectioned) with an interactive **map**
  (flutter_map / OpenStreetMap) to set the geofence centre + a **radius slider**.
- Campus-admin **profile avatar = school logo**.
- **Splash** always plays its bloom now (minimum-display gate).
- Shared `core/widgets/arc_gauge.dart` (semicircle % gauge).

### Notes
- New deps: table_calendar, pdf, printing, excel, share_plus, path_provider,
  flutter_map, latlong2. analyze clean, 42 tests.

## [1.8.0] - 2026-05-23
Face re-enroll from the camera.

### Added
- **Update face** (Account → Security → Face ID): capture a new photo with the
  front camera to set your face reference. Role-routed — students hit
  `/api/face/register`, admin/School-IT hit `/auth/security/face-reference`. The
  backend enforces liveness + a single face; failures (e.g. "Face not found.")
  show inline. Reuses the attendance camera pipeline; no new dependencies.

## [1.7.0] - 2026-05-23
School-IT customization, college management, and bundled fonts.

### Added
- **Bundled Manrope + JetBrains Mono** as asset fonts — correct typography in
  release/offline builds (no runtime font fetch).
- **University settings** redesigned (iOS Display style): a live brand **preview**,
  **logo upload** (web + APK), **primary & secondary** brand colours, name/code,
  and a compact event-policy row. Saving applies the primary colour to the theme
  live.
- **College management**: add a college, rename/delete a college (delete warns +
  surfaces the backend error when students are still assigned).
- **Assign / reassign a student to a college** from the student detail screen.
- Add students **manually** per college (alongside bulk import).
- **Governor → student** quick switch in the Governance header.

### Notes
- The duplicate-email check is global across schools on the backend, so the
  add-student form now surfaces the backend's exact reason (e.g. "registered in
  another school").
- 42 tests; analyze clean.

## [1.6.0] - 2026-05-22
Animated splash, Apple-style navbar, and a Security section.

### Added
- **Security** settings (Account → Security): **Edit profile** (name/email →
  `PATCH /api/users/{id}`), **Change password** (real form →
  `/auth/change-password`), **Sign-in & devices** (active sessions + revoke
  others + recent sign-ins via `/auth/security/*`), and a **Face ID** status tile.
- **Animated bloom splash** — a native recreation of `aura_animated_bloom.svg`
  (green aura reveal + white-logo elastic bloom); honours Reduce motion. (The SVG
  itself can't render in Flutter — CSS/SMIL + chroma filters — so it's rebuilt.)

### Changed
- **Bottom navigation** redesigned: switching tabs now **slides + fades** in the
  swipe direction (state-preserving, no overlap); the tap **ripple is removed**
  (Pressable scale); the active item gets a soft accent pill + label.

### Notes
- 42 tests; analyze clean. Face re-enrollment is admin/kiosk-only (the backend
  face endpoints are privileged), so the tile shows status + guidance.

## [1.5.0] - 2026-05-22
School IT branding customization.

### Added
- School IT can customize their school in **School settings**: edit the school
  **name** + **code** and pick a **primary brand colour** (swatch picker). Saving
  posts to `PUT /api/school/update` and applies the colour to the app theme
  **live** (`theme_controller`), so the accent reflects the school brand. The
  school **logo** is shown when set.

## [1.4.0] - 2026-05-22
Apple-style polish: iOS settings, staggered motion, per-school AI toggle.

### Added
- **Staggered "rise-up" entrance** on every dashboard + the Account screen (cards
  fade + rise in, sequenced) — plays only when Reduce motion is off
  (`RiseIn` / `staggered` in `core/widgets/rise_in.dart`).
- **iOS-style Account / Settings**: grouped inset sections with soft colored icon
  tiles (`SettingsTile` / `SettingsSection`), a tappable profile row, and
  preference cards.
- **Per-school Aura AI toggle** in the admin school detail — turn the AI assistant
  on/off for a school. (Saved on-device for now; platform-wide enforcement needs a
  backend `ai_enabled` field, flagged in code.)

### Notes
- 42 tests; analyze clean.

## [1.3.1] - 2026-05-22
### Fixed
- Tab views no longer overlap when switching between workspace tabs — the
  animated tab stack now `Offstage`s inactive tabs (only the active one is laid
  out + painted; state is still preserved). They were painting through before.

## [1.3.0] - 2026-05-22
Dashboard redesign across all workspaces.

### Added
- **Student / School IT / Governance home screens redesigned** to match the Admin
  dashboard — hero ring + metric cards with icon chips + a real chart:
  - Student: attendance ring, present/absence chips, monthly-attendance bar chart,
    and the next upcoming event (was a Phase-0 placeholder — now real data).
  - School IT: students ring (face-enrolled %), department/program chips, and a
    students-by-department bar chart.
  - Governance: compliance ring + pending sanctions (sanctions dashboard),
    students/published chips, an absences-by-event bar chart, recent announcements.
- Shared `core/widgets/dashboard.dart` (HeroRingCard, MetricChipCard,
  DashboardActionRow, DashboardBarChart) so every workspace home stays consistent.

## [1.2.0] - 2026-05-22
Admin dashboard redesign + Apple-style tab transitions.

### Added
- **Admin Overview redesigned** as a chart-led dashboard: an active-schools hero
  ring, metric cards with icon chips, and a **Subscriptions** bar chart (fl_chart)
  — airy and readable instead of plain stat boxes.
- App-wide **cross-fade + lift** transition when switching bottom-nav tabs
  (state-preserving, Apple-style fade-through); honours Reduce motion.
- Status-colored icon chips on school cards.

### Changed
- Bottom navigation sits a little lower (smaller bottom inset).

## [1.1.0] - 2026-05-22
Admin parity, the real Aura logo + web preview, and Apple-style motion.

### Added
- **Admin school detail** opens reliably (renders from the loaded summary — the
  deployed backend has no per-school detail GET) with a **subscription status**
  control (active/trial/suspended) and a **Plan & limits** editor
  (`/api/subscription/me`) — the per-school capability lever.
- **Admin Logs** tab: audit logs (`/api/audit-logs`, search + status filters) and
  notification logs (`/api/notifications/logs`).
- **Reduce motion** setting (System / On / Off) in Account → Appearance; app-wide
  Apple-style page transitions (Cupertino) that collapse when motion is reduced.
  Reduce-motion also gates the stat ring + bottom-nav indicator.
- Official **Aura logo** (from the web app) on splash + login via `AuraLogo`;
  `device_preview` phone-frame preview; web platform enabled (`--web-port=5173`).

### Changed
- Semantic colors: Sign out, attendance **sign-out**, and suspended/deactivated
  states are **red**; attendance **check-in** is **green**.
- Splash + login brand mark switched from the text "A" to the real Aura logo.
- `intl` bumped to `^0.20.2`.

### Fixed
- Tapping a school in Admin no longer shows "Something went wrong" (it called a
  detail route absent from the deployed backend).

### Tests
- Audit/notification log + subscription parsing tests. 42 total; analyze clean.

## [1.0.0] - 2026-05-22
Phase 5 — cross-cutting polish. First complete release: all four role workspaces.

### Added
- Offline read-cache: a Dio interceptor caches successful GETs and serves them on
  network failure (cleared on logout) — schedules, dashboards, and lists keep
  working offline.
- CI: GitHub Actions workflow (`aura-app-ci.yml`) running analyze + test, then a
  debug APK build, on changes to `frontend-app/`.
- Accessibility: tooltips on icon-only actions (new event/school/member/
  announcement, password visibility) atop existing Semantics, reduced-motion, and
  text-scaling support.
- `RELEASE.md`: Android/iOS signing, store-metadata checklist, and credential-gated
  follow-ups (FCM push, deep links).

### Notes
- 38 tests; `flutter analyze` clean. Push notifications, deep links, app icon, and
  store signing are documented in `RELEASE.md` (need the team's Firebase project /
  keystore / store accounts).

## [0.5.0] - 2026-05-22
Phase 4 — Platform Admin workspace. All four role workspaces are now functional.

### Added
- Overview: platform metrics (schools / campus admins / pending) + pending
  password-reset approvals (`/auth/password-reset-requests` + approve at root).
- Schools: list (`/api/school/admin/list`), detail with activate/deactivate
  (`PATCH /api/school/admin/{id}/status`), and create-school + campus-admin in one
  step (`POST /api/school/admin/create-school-it`, multipart) showing the generated
  temporary password.
- Accounts: campus-admin list (`/api/school/admin/school-it-accounts`) with
  activate/deactivate and password reset.
- Admin models/repository. Retired the placeholder tabs — every workspace now
  renders real screens.

### Tests
- Admin model-parsing tests. 38 total; analyze clean.

## [0.4.0] - 2026-05-22
Phase 3 — School IT (campus admin) workspace.

### Added
- Dashboard with school metrics (students / departments / programs) and management
  entry points.
- Users tab: students list with live search, mapped to department/program names,
  plus a student detail screen.
- Schedule tab: events list, an event editor (name, location, start/end pickers,
  optional device-location geofence) creating via `POST /api/events/`, and the
  live attendance monitor.
- Bulk import: pick a CSV/XLSX, preview validation, commit, and poll job status
  with a progress bar and per-row errors (`file_picker` added).
- School settings: school info + editable default event policy (`/api/school/me`,
  `PUT /api/school/update`).
- School IT models/repository; events repo gains create/delete. Verified School IT
  routes live under `/api`.

### Tests
- School IT model-parsing tests. 34 total; analyze clean.

## [0.3.0] - 2026-05-22
Phase 2 — Governance (student government) workspace.

### Added
- Governance access discovery (`/governance/access/me`) with a workspace entry in
  Account (shown only when the user belongs to a unit) and an SSG>SG>ORG
  active-unit switcher.
- Dashboard overview (`/governance/units/{id}/dashboard-overview`): student +
  published-announcement counts, recent announcements, quick actions.
- Members tab: officers of the active unit, with add (student search → assign)
  and remove.
- Events tab: events in the unit's governance context, with a live attendance
  monitor (stats ring + status breakdown + attendee list).
- Announcements: list + create.
- Sanctions: dashboard (`/sanctions/dashboard`), per-event sanctioned students,
  and compliance approval.
- Governance + sanctions models/repositories; events repo gains a
  `governance_context` filter. Verified governance/sanctions routes live under `/api`.

### Tests
- Governance + sanctions parsing tests. 31 total; analyze clean.

## [0.2.1] - 2026-05-22
Phase 1 — Student workspace complete.

### Added
- AI assistant chat: streamed SSE replies from `/assistant/stream` with live
  typing, conversation continuity, and user context.
- Gather kiosk: nearby-event discovery (`/public-attendance/events/nearby`) plus an
  auto-scanning multi-face check-in loop (`/multi-face-scan`) with a recorded count
  and per-person outcomes; recorded students go on a cooldown set.
- Account → Manage links to Aura AI and Gather (kiosk).

### Security
- Backend + assistant URLs moved to a git-ignored `config/cloud.json` (loaded with
  `--dart-define-from-file`); no endpoints are hardcoded in source. Dev-only
  cleartext HTTP enabled (Android `usesCleartextTraffic`, iOS ATS) for the IP-based
  staging server — switch to HTTPS for production.

### Fixed
- API path prefix set to `/api` (verified against the staging server: `/api/events/`
  responds, `/api/v1/...` 404s); overridable via `--dart-define=AURA_API_PREFIX`.

## [0.2.0] - 2026-05-22
Phase 1 — Student workspace (core surfaces).

### Added
- Student data models (event, attendance, profile, notifications, analytics) with
  lenient JSON parsing, plus typed repositories over the cloud API.
- Schedule (grouped by day) and Event Detail with live attendance-window status.
- Face-scan attendance: front-camera capture + geolocation posted to
  `/face/face-scan-with-recognition`, with a result sheet. Native camera/location
  permissions added for Android + iOS.
- Quick "Scan" tab listing ongoing events for one-tap check-in.
- Insights: attendance-rate ring, status breakdown, monthly trend chart
  (fl_chart), and recent history.
- Profile and Notifications screens; Account tab links to both.
- `camera` + `geolocator` plugins and a geolocation service wrapper.

### Tests
- Added model-parsing tests (event/attendance/report/profile). 27 total; analyze clean.

## [0.1.0] - 2026-05-22
Phase 0 — foundation.

### Added
- Flutter Android + iOS client `aura_app` (appId `com.aura.aura_app`).
- Design system: light/dark theme + per-school brand primary, Manrope +
  JetBrains Mono type scale, spacing/radii/elevation, motion tokens (emil),
  YIQ contrast helper. Documented in `DESIGN_SYSTEM.md`.
- Component library: `AuraButton`, `AuraCard`, `AuraPill`/`StatusChip`,
  `AuraTextField`, `GlassBottomNav`, `StatRing`, `AppScaffold`, `SectionHeader`,
  `AuraSkeleton`, `Pressable`.
- Networking: Dio client with bearer interceptor, base-URL normalization,
  FastAPI error mapping (`ApiException`), paginated envelope (`Paginated`).
- Auth: secure token store, token-payload/role parsing, session controller with
  401 handling; email/password login via `POST /token` (fallback `/api/token`).
- Role-based router (go_router) with auth / password-change / privileged-face
  gates routing to Student / School IT / Admin / Governance shells.
- Workspace shells with glass bottom nav and home previews; shared Account tab
  (theme switch + sign out).
- Tests (23): roles, base-URL, token meta, pagination, contrast, `AuraButton`.

### Notes
- Reuses the existing cloud FastAPI backend unchanged; base URLs via
  `--dart-define`. No codegen (hand-written Riverpod + plain models).
- `flutter analyze` clean; `flutter test` green.

[Unreleased]: #unreleased
[1.28.1]: #1281---2026-05-27
[1.28.0]: #1280---2026-05-27
[1.20.1]: #1201---2026-05-23
[1.20.0]: #1200---2026-05-23
[1.19.0]: #1190---2026-05-23
[1.18.2]: #1182---2026-05-23
[1.18.1]: #1181---2026-05-23
[1.18.0]: #1180---2026-05-23
[1.17.13]: #11713---2026-05-23
[1.17.12]: #11712---2026-05-23
[1.17.11]: #11711---2026-05-23
[1.17.10]: #11710---2026-05-23
[1.17.9]: #1179---2026-05-23
[1.17.8]: #1178---2026-05-23
[1.17.7]: #1177---2026-05-23
[1.17.6]: #1176---2026-05-23
[1.17.5]: #1175---2026-05-23
[1.17.4]: #1174---2026-05-23
[1.17.3]: #1173---2026-05-23
[1.17.2]: #1172---2026-05-23
[1.17.1]: #1171---2026-05-23
[1.17.0]: #1170---2026-05-23
[1.16.2]: #1162---2026-05-23
[1.16.1]: #1161---2026-05-23
[1.16.0]: #1160---2026-05-23
[1.15.0]: #1150---2026-05-23
[1.14.0]: #1140---2026-05-23
[1.13.1]: #1131---2026-05-23
[1.13.0]: #1130---2026-05-23
[1.12.0]: #1120---2026-05-23
[1.11.0]: #1110---2026-05-23
[1.10.0]: #1100---2026-05-23
[1.9.0]: #190---2026-05-23
[1.8.0]: #180---2026-05-23
[1.7.0]: #170---2026-05-23
[1.6.0]: #160---2026-05-22
[1.5.0]: #150---2026-05-22
[1.4.0]: #140---2026-05-22
[1.3.1]: #131---2026-05-22
[1.3.0]: #130---2026-05-22
[1.2.0]: #120---2026-05-22
[1.1.0]: #110---2026-05-22
[1.0.0]: #100---2026-05-22
[0.5.0]: #050---2026-05-22
[0.4.0]: #040---2026-05-22
[0.3.0]: #030---2026-05-22
[0.2.1]: #021---2026-05-22
[0.2.0]: #020---2026-05-22
[0.1.0]: #010---2026-05-22
