# Aura (RIZAL) Flutter app — Claude guide

Native **Android + iOS** client for the RIZAL/Aura school attendance & governance
platform. It is a **new client for the EXISTING cloud FastAPI backend** — never
change the backend from here. Over time it replaces the Vue 3 + Capacitor app.

Package `aura_app` · appId `com.aura.aura_app`. Visual/motion contract lives in
`DESIGN_SYSTEM.md`. Backend contract mirrors `../frontend-web/src/services/`.

## Stack
- **Flutter** (Material 3), Dart 3.
- **Riverpod** for state — hand-written `Notifier`s, **no codegen**.
- **go_router** with redirect guards (`lib/app/router.dart`).
- **Dio** HTTP (`lib/core/network/dio_client.dart`) + bearer-token interceptor.
- Models: plain immutable Dart with `fromJson`/`toJson` — **no freezed/build_runner**.
- **fl_chart** for charts. **google_fonts** for Manrope + JetBrains Mono.
- `flutter_secure_storage` (JWT) · `shared_preferences` (prefs + auth meta).
- Phase 1+ (commented in `pubspec.yaml`): camera, google_mlkit_face_detection,
  geolocator, google_sign_in, flutter_local_notifications, hive_flutter.

## Colours  (tokens: `lib/core/theme/app_colors.dart`, `app_tokens.dart`)
- **Accent / brand:** lime `#AAFF00` (pressed `#88CC00`) — use sparingly: at most
  one primary emphasis per view; never as a large fill or as text on light.
- **Ink / near-black:** `#0A0A0A`.
- **Light:** bg `#ECEEE7`, surface `#FFFFFF`, surfaceAlt `#F4F6EF`,
  text secondary `#555B50`, muted `#8A9182`, border `#E2E5DB`.
- **Dark (OLED):** bg = accent darkened ~96%, surface `#12150D`, surfaceAlt `#1A1E12`,
  ink `#F4F7EC`, border `#272C1D`.
- **Status (fixed, never branded):** present/compliant `#22C55E`, late `#FB923C`,
  at-risk `#F59E0B`, absent/non-compliant `#EF4444`, excused `#F97316`.
- **Governance:** SSG `#6366F1`, SG `#8B5CF6`.
- **School-customizable primary** overrides the accent at runtime
  (`theme_controller`, from the login token's `primary_color`). Pick on-colors with
  the YIQ helper in `lib/core/theme/contrast.dart`.

## Rules
**Design (ui-ux-pro-max + emil — full detail in `DESIGN_SYSTEM.md`):**
- Read styling from the theme: `AppTokens.of(context)` and
  `Theme.of(context).textTheme`. Never hardcode `Color(0x..)` in widgets.
- Motion (`app_motion.dart`): curves easeOut `(0.23,1,0.32,1)` / easeInOut / drawer;
  UI < 300ms; **never ease-in**; press scale **0.97**; list stagger 50ms; honor
  reduced motion (`MediaQuery.disableAnimations`); always `dispose()` controllers.
- Touch targets ≥ **48dp**, ≥ 8dp apart; tap (not hover); every action has
  loading + disabled states; async uses skeletons (`AuraSkeleton`); haptics on
  confirmations only.
- Icons: Material rounded icons — **no emoji**. Status shows **colour + icon**.
- Manrope for UI; `AppTypography.mono` (JetBrains Mono) for numbers/IDs/timestamps.

**Architecture:**
- Feature-first: `lib/features/<area>/{data,domain,presentation}`; shared code in
  `lib/core` and `lib/shared`. Providers colocated with their type.
- Keep widget trees shallow (extract widgets); `const` where possible;
  `ValueKey` on dynamic list items; `Hero` for card → detail transitions.

**Backend integration (mirror `frontend-web/src/services/`):**
- Base URL via `--dart-define=AURA_API_BASE_URL` (backend ROOT, no `/api`).
- Login: `POST /token` (form: `grant_type=password`, `username`, `password`),
  fallback `/api/token` → JWT + rich meta (roles, school branding, flags). Bearer
  is attached by the Dio interceptor; **401 → session logout**.
- Roles normalized (`campus-admin`→`school-it`); `Roles.workspaceFor` →
  student / schoolIt / admin / governance. Lists use the `{data,page,total,…}`
  envelope (`Paginated`). FastAPI `{detail}`/422 → `ApiException`.
- **Never commit secrets or real cloud URLs** — pass them via `--dart-define`.

**Workflow:**
- The user scaffolds the project (`flutter create`) and may run the app
  themselves — build by **writing source files directly**, not via the CLI generator.
- Verify before claiming done: `flutter pub get && flutter analyze && flutter test`
  must be clean (Phase 0 baseline: analyze clean, 23 tests pass).

## Versioning & changelog
- **Semantic Versioning.** Pre-1.0 while building parity: **each phase bumps the
  minor** (Phase 1 → 0.2.0, …), fixes bump the patch; **1.0.0** when all four
  workspaces ship.
- Record every change in `CHANGELOG.md` (Keep a Changelog) under `[Unreleased]`,
  then cut a dated version section on release.
- Keep `pubspec.yaml` `version:` in sync as `<semver>+<build>` (bump the build
  number each release).

## Run
```bash
flutter run --dart-define-from-file=config/cloud.json   # git-ignored endpoints
```
Endpoints live in `config/cloud.json` (git-ignored, never committed). The
IP-based staging server is HTTP, so dev-only cleartext is enabled (Android
`usesCleartextTraffic`, iOS ATS) — use HTTPS in production.

## Status
**v1.22.1 — assistant greeting + wait-don't-fail + toggle fix.** Chat opens with an
instant client-side greeting "Hi <name>! I'm Aura, powered by Jose AI…"
(`chat_controller.build()`). Assistant Dio `receiveTimeout` 300s so a slow local model
isn't mislabeled — `DioException` timeout → "taking a while to think", real failure →
"could not reach". Fast/Think segmented control moved from the app bar (overflowed) to
a row above the input. `run_local.ps1` adds `--mlock` (model stays in RAM; cold ~64s →
~6s). analyze clean, 42 tests.
**v1.22.0 — assistant Fast/Think toggle.** Segmented control in the Aura AI app bar
(`chat_screen.dart` `_ModeToggle`, sliding accent pill, ease-out, reduce-motion)
toggles `fastModeProvider` (`fast_mode_controller.dart`, persisted, default Fast);
sent per message via `assistant_service`/`chat_controller` (`fast: bool`). Backend
(`assistant/main.py`) honors `body.fast`: Fast = slim `FAST_SYSTEM_PROMPT` + no MCP
tools (~120-tok prompt, seconds vs ~2min on a 1.5B CPU model); Think = full prompt +
tools/charts. analyze clean, 42 tests.
**v1.21.0 — Aura AI renders charts + "powered by Jose AI" identity.** The assistant
chat draws the backend's `visualization` SSE events inline (`assistant_chart.dart` =
`ChartSpec` + `AssistantChart`, fl_chart bar/line/pie/doughnut, themed + legend):
`assistant_service` captures the `visual` payload, `chat_controller` attaches charts
to the message, `chat_screen` renders text+charts (was text-only — charts were
dropped). Assistant **backend** re-identified as "Aura, powered by Jose AI"
(`assistant/assistant_identity.py` prepended to `system_prompt.txt`; `main.py`
load_dotenv; `assistant/.env` → local llama.cpp `jose.gguf`;
`assistant/RUN_LOCAL_JOSE.md`). analyze clean, 42 tests.
**v1.20.2 — smoother long-list scrolling.** `RiseIn` (`rise_in.dart`) only animates the
initial on-load burst (shared `_revealUntil` window opened by index 0); rows mounted
later while scrolling render instantly (`_animate=false` → child directly, no
Opacity/Transform). Fixes janky settings scroll (rows were animating + running an
Opacity layer as they scrolled into view). analyze clean, 42 tests.
**v1.20.1 — export speed-up + smooth theme switch + trimmed beta text.** Export
(`export_sheet.dart`): logo + roster cached (static, per session) + all fetches
(stats/attendees/names/logo) run via `Future.wait` (was sequential; logo blocked at
60% on an 8s timeout → now 3s, parallel) → ~1–5s, repeat exports near-instant.
`AppTheme.light/dark` **memoized** (`_cache`) so `ColorScheme.fromSeed` isn't
recomputed every rebuild — fixes the light/dark toggle jank. Beta-features subtitles
shortened. analyze clean, 42 tests.
**v1.20.0 — background event check-in notifications + Beta features settings.**
`native_geofence` (OS geofences, Android-14-safe) registers the user's ongoing
geofenced events when "Nearby event check-in" is on; ENTER → OS notification (works
app-closed) via a background isolate (`geofence_background.dart` `nearbyGeofenceCallback`
+ `flutter_local_notifications`); tap → `pendingCheckInProvider` → `student_home`
listener opens `AttendanceScreen` directly. `geofenceBackgroundProvider` watched in
`AuraApp`. Android: desugaring on + bg-location/notification perms + native_geofence
receivers/service in manifest; iOS: bg-location + UIBackgroundModes. Account "Beta
features" group (BETA pills) incl. **Auto check-in** = "Coming soon" placeholder
(`autoCheckFullProvider`). Needs on-device field test + a geofenced event (backend).
analyze clean, 42 tests, debug APK builds.
**v1.19.0 — nearby event check-in (opt-in geofence prompt).** Account toggle
`auto_checkin_controller.dart` (off by default, persisted) gates
`nearby_event_provider.dart` (AutoDisposeNotifier): while the student Home is open it
polls `geolocation_service` against `ongoingEventsProvider` geofenced events (latlong2
distance ≤ radius) and surfaces `NearbyEventBanner` (events/presentation/widgets) → tap
→ `AttendanceScreen` (face scan). Location read only when enabled + a geofenced ongoing
event exists. Foreground only (background/OS push = future: flutter_local_notifications +
bg location). analyze clean, 42 tests.
**v1.18.2 — Liquid nav works on web again + BETA pill.** Reverted the blob to
`liquid_glass_renderer`'s `LiquidGlass` (the `liquid_glass_widgets` `GlassPanel` 404s on
web) and removed the `kIsWeb` guard that disabled Liquid on web; `main.dart` back to
plain (no `initialize()`/`wrap()`). `liquid_glass_widgets` dep now unused. BETA pill on
the toggle (`account_tab.dart` `_BetaPill`). analyze clean, 42 tests.
**v1.18.1 — on-device refinements.** Manrope is a **variable** font → drive the weight
axis with `fontVariations` per style (`app_typography.dart`) — fixes the super-thin/
unreadable text. Instant theme switch (`themeAnimationDuration: Duration.zero` in
`app.dart`) — the cross-fade janked on low-end GPUs. School logo shows its letter while
loading (`school_badge.dart`). **Dropped the package `GlassBottomBar`** (kept the custom
Liquid nav); beta flag is a **bool** again (Off/Liquid), `app_shell` no longer imports
`liquid_glass_widgets` (still used by the Liquid blob's `GlassPanel`). analyze clean, 42 tests.
**v1.18.0 — iOS 26 liquid glass (`liquid_glass_widgets`) + 3-way nav selector.** Account
toggle is now a `BetaNavStyle` enum (Off / Liquid / Glass bar, persisted, reversible):
Liquid = custom capsule blob via `GlassPanel`, Glass bar = package `GlassBottomBar`
(`standard` quality + `maskingQuality.off` — the jelly masking is too heavy for pre-A15 GPUs).
`main.dart` `initialize()`+`wrap()` (guarded `!kIsWeb`). **Web** 404s the shaders → falls
back to the standard nav (`kIsWeb` in `app_shell.dart`); glass is **Impeller/mobile-only**.
Android build fixed: inject `androidx.concurrent:concurrent-futures` into
`camera_android_camerax` (`android/build.gradle.kts`). analyze clean, 42 tests, debug APK builds.
**v1.17.13 — beta nav blob: no edge overlap.** Blob left/right clamped to the pill
inner bounds (inset 3) so it compresses at the first/last tab instead of overflowing;
zoom (Transform.scale) still pops out. analyze clean, 42 tests.
**v1.17.12 — beta nav blob: wide pill on busy bars + bigger.** `_blobH` 66, min width
`_blobMinW` = 1.6×height, centered on the tab (`(_blobSlot()+0.5)*itemW - blobW/2`) so
it's a horizontal pill even with 5 tabs (overflows the slot/pill, Clip.none); zoom 1.4×
(drag + tap pop). analyze clean, 42 tests.
**v1.17.11 — beta nav blob bigger at rest.** `_blobH` 62 + `_gapX` 3 so the resting
blob ≈ the old zoomed size; tap/slide zoom (1.32×) goes even bigger. analyze clean, 42 tests.
**v1.17.10 — beta nav blob: slide+zoom only (no stretch), zoom on tap.** `_blobLeft`
is a plain position lerp (fixed width, no elastic stretch); scale via per-frame
`Transform.scale` — 1.32× while dragging, triangle pop on tap; slide 240ms. analyze
clean, 42 tests.
**v1.17.9 — beta nav blob = Dynamic-Island capsule, zooms on slide.** Blob rendered
outside the pill clip (`Stack(clipBehavior: Clip.none)`) so it can pop out; `AnimatedScale`
1.32× while `_dragging` (easeOutBack), settles on release; horizontal capsule (radius
= height/2). analyze clean, 42 tests.
**v1.17.8 — beta nav blob: wider pill + pop + visible refraction.** `_gapX` 4 (wider =
horizontal pill, not oval); blob **pops** on tap (Positioned w/h × triangle factor, settles);
pill blur 8 + tint 0.20–0.28 so the page shows through and the blob refraction
(thickness 28 / refractiveIndex 1.5 / chromaticAberration 5) is visible. analyze clean,
42 tests.
**v1.17.7 — beta nav: smooth drag + glitch-free tap.** `liquid_glass_nav.dart` blob
uses a continuous fractional `_pos`: drag sets `_pos` to the finger (free, no snap) +
commits the view at tab boundaries, settles to nearest on release; tap animates `_pos`
from its real position (elastic from→to, two eased edges) so no glitch. Active icon
colour follows `_pos.round()` while dragging. analyze clean, 42 tests.
**v1.17.6 — beta nav blob = proper pill.** Blob radius = height/2 (`_blobH` 48 →
capsule ends), smaller side gap (`_gapX` 6) so width > height = horizontal pill (not a
rounded square/oval). analyze clean, 42 tests.
**v1.17.5 — beta nav: elastic blob + centered icons.** `liquid_glass_nav.dart` is now
stateful — the glass blob **stretches** between tabs (leading edge `easeOutCubic`,
trailing `easeInCubic`) so the liquid feel works on tap + drag; blob reshaped to a
content-fitting rounded rect (radius 22, h 54, centered) — fixed the tall-oval/misaligned
look; icons wrapped in `Center`. analyze clean, 42 tests.
**v1.17.4 — beta nav: bigger pill + drag + real blob refraction.** `liquid_glass_nav.dart`
pill height 82 + roomier icons; blob slides via tap **or drag** (`onHorizontalDragUpdate`,
position→index); pill tint is **translucent dark** (gradient 0.26→0.34 + blur 12) so the
page shows through and the blob can **refract** it (refractiveIndex 1.45, thickness 24,
chromaticAberration 4 — note `outlineIntensity` is NOT a field in 0.2.0-dev.4). Refraction
on the blob only; pill stays frosted. analyze clean, 42 tests.
**v1.17.3 — beta liquid glass nav visual rework.** Custom
`core/widgets/liquid_glass_nav.dart`: neutral **frosted tinted pill** (pure UI, no
brand colour, `navInk` tint + blur, same size/pill as `GlassBottomNav`) + a
**colourless `liquid_glass_renderer` blob** (chromatic aberration) sliding
(`AnimatedPositioned`, easeOutCubic) to the active tab; **active icon/label =
university primary** (`t.accent`, animated). Replaces the `liquid_bottom_nav_bar`
usage in `app_shell.dart` (dep now unused). Impeller-only; behind the beta toggle.
analyze clean, 42 tests.
**v1.17.2 — smoother tab switching + blob snap.** View transition is now a
state-preserving **cross-fade** (`_AnimatedTabStack`: outgoing fades out as incoming
fades in, no slide/flash) across all roles; beta liquid nav blob **slides on tap**
(`animationDuration` 320ms + easeOutCubic). analyze clean, 42 tests.
**v1.17.1 — Beta liquid glass tab bar = real refraction.** Beta nav wraps
`liquid_bottom_nav_bar` (transparent container) in a `liquid_glass_renderer`
`LiquidGlass.withOwnLayer` pill (`LiquidRoundedSuperellipse` radius 40 = pill, not a
rounded square) with **chromatic aberration** + thickness/light tuned for the iOS
look (`app_shell.dart`). Impeller-only; behind the beta toggle. deps:
liquid_glass_renderer 0.2.0-dev.4 (+ motor). analyze clean, 42 tests.
**v1.17.0 — Beta: opt-in iOS liquid glass tab bar (all roles).** Account toggle
(`core/theme/beta_controller.dart`, persisted) swaps the bottom nav to
`liquid_bottom_nav_bar` (liquid blob + glass blur, brand-accent themed) in
`app_shell.dart`; off = standard `GlassBottomNav`. Toggle warns it's beta / may lag
on low-end devices. analyze clean, 42 tests.
**v1.16.2** — event-creation + export fixes. Deployed backend **requires
`location`** on `POST /api/events/` (event editor now requires + always sends it —
was the create "internal server error", actually a 422). Governance **Events**
wrapped in `AppScaffold` (was a bare Column → `ChoiceChip` "No Material" crash when
pushed from the dashboard quick action). PDF text sanitized to Latin-1 (Helvetica
can't draw "–"/"—"). Report attendees show **Name | Student ID | Time in | Time out
| Status** (names via `GET /api/governance/students`, `accessibleStudents()`) with
a **real step progress bar**. Note: backend may still 500 on SG/ORG event creation
(unhandled `StopIteration` in scope resolution — a backend bug, not the client).
analyze clean, 42 tests.
**v1.16.1** — report export (PDF/Excel/CSV) no longer hangs/lags: byte generation
runs in a background isolate (`compute` + top-level `buildEventPdf/Csv/Xlsx` in
`event_report_service.dart`) and the logo fetch has an 8s timeout (`export_sheet.dart`).
**v1.16.0 — governance event creation + event map view with range.** Governance
Events screen (+ dashboard quick action) has a **New event** button (gated by
`unit.can('manage_events')`) → `EventEditorScreen(governanceContext: unit.type)`;
`EventsRepository.create(body, governanceContext:)` posts
`/api/events?governance_context=SSG|SG|ORG` and the backend auto-scopes
department/program. Read-only `EventLocationMap` (`core/widgets/event_location_map.dart`,
flutter_map static) shows the geofence centre + radius on event detail + governance
monitor. analyze clean, 42 tests.
Prior — **v1.15.0 — university logo shows everywhere + secondary colour applied.** Backend
`logo_url` is **relative** (`{public_prefix}/{file}`); the app rendered it raw and
gated on `startsWith('http')` → never shown. `core/network/media_url.dart`
(`mediaUrl()`) resolves it against the backend root. New `SchoolBadge`
(`core/widgets/school_badge.dart`) = logo in a primary→**secondary** gradient ring
(secondary colour now used) + initial fallback; on student/school-IT home headers,
governance header, account card, and profile (with university name). analyze clean,
42 tests.
Prior — **v1.14.0 — campus-admin Student Government panel + blank-settings fix.** School-IT
home → "Student Government" (`schoolit/presentation/campus_governance_screen.dart`)
auto-creates the SSG (`ssgSetup()` → `/api/governance/ssg/setup`) and adds/edits/
removes the President & officers (search student → position + per-officer
permissions; `assignMember`/`updateMember`/`removeMember`). **University settings
blank** was a full-width `AuraButton` inside a `Row` (infinite-width assertion) —
now constrained; not a backend issue. analyze clean, 42 tests.
Prior — **v1.13.1** — Users-by-College lists only students (`studentProfile != null`), so
"Unassigned" entries are real, assignable students (non-student accounts were
polluting it and had no assign action). **v1.13.0 — pagination fix + governance→student + localization.** `/api/users/`
paginates by **`page`** (ignores `skip`, envelope `{data,page,total,total_pages}`);
`schoolit_repository.students()` now walks `page=1..total_pages` + de-dups — fixes
duplicate accounts, endless skeleton, "--" counts, and accounts past page 1 not
loading (the "already exists but not found" case). Governance "Switch to student"
pushes the student shell (was a no-op). `flutter_localizations` (en/fil) added so
the app follows the device language. analyze clean, 42 tests.
Prior — **v1.12.0 — fixes + schedule filters.** Users-by-college loads **all** users
(paginated in `schoolit_repository.students`) so new accounts appear (the JRMSU
"exists but not found" bug); **university settings** renders from token `meta` (no
blank when `/api/school/me` lags); schedule calendars have **All/Today/Upcoming/Past**
pills (`event_calendar.dart`); colleges have rename/delete on each card. analyze
clean, 42 tests.
Prior — **v1.11.0 — student analytics polish.** Insights = attendance **arc gauge** +
**Now & next** (ongoing/upcoming) + breakdown + monthly trend + **event-type pie**
(`student/presentation/analytics_screen.dart`). Completes the governance / calendars
/ analytics plan (1.9.0 → 1.11.0). analyze clean, 42 tests.
Prior — **v1.10.0 — calendars with search (student / school-IT / governance).** Shared
`core/widgets/event_calendar.dart` (table_calendar) with status-colored markers +
search; wired into Schedule/Events, governance scoped to the unit. analyze clean,
42 tests.
Prior — **v1.9.0 — governance event-management dashboard + report export + map event
picker.** Governance home (`governance_home_screen.dart`) shows the officer's
position (`unitDetailProvider`), a compliance **arc gauge**
(`core/widgets/arc_gauge.dart`), metric chips, **permission-greyed quick actions**
(`unit.can(code)`), and a live event list (ongoing → `eventLiveStatsProvider`,
15s poll) with **export** to PDF/CSV/XLSX (`features/reports/event_report_service.dart`
+ `ExportSheet`). The event editor has an interactive **map + radius** geofence
(`flutter_map`/`latlong2`). Campus-admin avatar = school logo; splash bloom always
plays (`app/splash_gate.dart`). analyze clean, 42 tests.
Prior — **v1.8.0 — Face re-enroll from the camera.** Account → Security → Face ID opens a
front-camera capture (`auth/presentation/update_face_screen.dart`, reuses the
attendance camera pipeline) that sets the face reference — role-routed: students →
`/api/face/register` (`AttendanceRepository.registerFace`), admin/School-IT →
`/auth/security/face-reference` (`SecurityRepository.setFaceReference`). Backend
enforces liveness + a single face.
Prior — **v1.7.0 — School-IT customization + college management + bundled fonts.**
Manrope/JetBrains Mono are bundled asset fonts (`assets/fonts/`, no runtime
fetch). University settings (`school_settings_screen.dart`) is an iOS-style
surface with a live brand preview, logo upload (bytes — web+APK), primary+
secondary colours; saving applies primary to the theme live. Students are managed
**by college** — add/rename/delete colleges (`schoolit_repository` department
CRUD), add students manually, and assign/reassign a student's college (PATCH
`/api/users/student-profiles/{id}`). Governance header has a "Switch to student".
Duplicate-email on add surfaces the backend's global-uniqueness reason. analyze
clean, 42 tests.
Prior — **v1.6.0 — animated splash, Apple navbar, Security settings.** Bloom splash
(`splash_screen.dart`, recreates the SVG natively); navbar slides+fades between
tabs with no ripple (`glass_bottom_nav.dart` + `_AnimatedTabStack`); Account →
**Security**: edit profile, change password, sign-in & devices (sessions/login
history via `/auth/security/*`), Face ID status. analyze clean, 42 tests.
Prior — **v1.5.0 — School IT branding customization.** School settings edits name/code +
a **primary brand colour** (swatch picker) via `PUT /api/school/update`, applied
to the app theme **live** (`theme_controller`); logo shown when set. Builds on
v1.4.0 Apple-style polish (chart-led dashboards + staggered rise-in `rise_in.dart`;
iOS Settings `settings_tile.dart`; per-school AI toggle `ai_access.dart`). Tab
cross-fade (Offstage) + lowered nav + Reduce-motion. analyze clean, 42 tests.
Follow-ups (FCM, deep links, signing, store, AI backend field) in `RELEASE.md`.
