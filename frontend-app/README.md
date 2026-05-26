# Aura (RIZAL) — Flutter app

Native Android + iOS client for the RIZAL/Aura school attendance & governance
platform. Talks to the **existing cloud backend** (FastAPI) — no backend changes.
Package: `aura_app` · application id: `com.aura.aura_app`.

See `DESIGN_SYSTEM.md` for the visual/motion contract (ui-ux-pro-max + emil).

## Status — Phase 0 (foundation) complete
- Theme system (light/dark + per-school brand primary), Manrope + JetBrains Mono.
- Networking (Dio + bearer auth + FastAPI error mapping + paginated envelope).
- Auth (secure token store, role normalization, session + 401 handling).
- Role-based router (auth / password / face gates → 4 workspace shells).
- Component library (button, card, pill, status chip, glass nav, stat ring, …).
- Email/password login wired to `POST /token`.

Next: **Phase 1 — Student** (attendance face-scan + geolocation, schedule,
analytics, AI chat). Then Governance → School IT → Admin → polish.

## Run

Endpoints live in a **git-ignored** `config/cloud.json` (kept out of version control).

```bash
flutter pub get

# Against the cloud backend (reads config/cloud.json):
flutter run --dart-define-from-file=config/cloud.json

# Or pass directly:
flutter run --dart-define=AURA_API_BASE_URL=<backend> \
            --dart-define=AURA_ASSISTANT_BASE_URL=<assistant>

# With no defines, the Android emulator falls back to http://10.0.2.2:8000.
```

Config keys: `AURA_API_BASE_URL`, `AURA_ASSISTANT_BASE_URL`, `AURA_API_TIMEOUT_MS`,
`AURA_GOOGLE_WEB_CLIENT_ID`, `AURA_GOOGLE_IOS_CLIENT_ID`. The staging server is
HTTP, so dev-only cleartext is enabled (Android `usesCleartextTraffic`, iOS ATS) —
use HTTPS in production.

## Verify

```bash
flutter analyze
flutter test
```

## Phase 1+ native plugins
Camera/geolocation/ML-Kit/Google-Sign-In/local-notifications are commented in
`pubspec.yaml`. Uncomment per phase and add the matching iOS `Info.plist` usage
strings and Android permissions before use.

## Project layout
```
lib/
  app/        MaterialApp.router + guards
  core/       config · network · auth · theme · widgets · services
  features/   auth · shell · student · governance · schoolit · admin · …
  shared/     models · utils
```
