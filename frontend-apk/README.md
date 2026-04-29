# Aura APK Workspace

<!--nav-->
[Previous](../README.md) | [Next](../frontend-web/docs/android-apk-build.md) | [Home](/README.md)

---
<!--/nav-->

This folder contains the native Android workspace for the Aura Capacitor app.

## What lives here

- `android/` — the editable Android Studio / Gradle project
- `build-apk.cmd` — wrapper that builds the APK from `frontend-web/`
- `outputs/` — copied debug or release APK files after a build

## How it works

The Vue app lives in `frontend-web/`. Capacitor is configured so `npx cap sync android` writes web assets and plugin changes into `frontend-apk/android`.

## Build

From this folder:

```bat
.\build-apk.cmd
.\build-apk.cmd release
```

Or from `frontend-web/`:

```powershell
npm run android:build:debug
npm run android:build:release
```

## Docs

- [Android APK Build Guide](../frontend-web/docs/android-apk-build.md)
