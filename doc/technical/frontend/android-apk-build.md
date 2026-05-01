# Android APK Build Guide

[<- Back to frontend docs](./README.md)

> **Status:** ACTIVE
> **Last Updated:** 2026-04-25

---

## SSOT Note

This guide summarizes the Android packaging flow.
Canonical configuration behavior is defined in:

- `frontend/package.json` (android scripts)
- `frontend/scripts/write-capacitor-config.mjs`
- `frontend/capacitor.config.json` (generated output)
- `frontend/aura-apk/android/` (native Android project)

If this guide conflicts with those files, follow the code/config files above.

---

## Project Layout

- Frontend web app root: `frontend/`
- Native Android workspace: `frontend/aura-apk/android/`
- APK wrapper script: `frontend/aura-apk/build-apk.cmd`

---

## Required Environment Inputs

At minimum, configure backend target values used by the Capacitor config generator:

```env
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8000
VITE_NATIVE_API_BASE_URL=http://127.0.0.1:8000
VITE_API_BASE_URL=/__backend__
```

For production/distributed builds, set `VITE_BACKEND_PROXY_TARGET` and `VITE_NATIVE_API_BASE_URL` to your public backend root URL.

Do not use `/api` suffix for these base values.

---

## Build Commands

Run from `frontend/`:

```powershell
npm ci
npm run android:build:debug
npm run android:build:release
```

Alternative wrapper from `frontend/aura-apk/`:

```bat
.\build-apk.cmd
.\build-apk.cmd release
```

---

## Build Outputs

- Debug APK:
  - `frontend/aura-apk/android/app/build/outputs/apk/debug/app-debug.apk`
- Release APK (unsigned by default):
  - `frontend/aura-apk/android/app/build/outputs/apk/release/app-release-unsigned.apk`

---

## Android Baseline

From `frontend/aura-apk/android/variables.gradle` and `app/build.gradle`:

- Package ID: `com.aura.app`
- Min SDK: `24` (Android 7.0)
- Target SDK: `36`

---

## Permissions Declared

From `frontend/aura-apk/android/app/src/main/AndroidManifest.xml`:

- `INTERNET`
- `ACCESS_NETWORK_STATE`
- `CAMERA`
- `ACCESS_FINE_LOCATION`
- `ACCESS_COARSE_LOCATION`
- `POST_NOTIFICATIONS`
- `RECEIVE_BOOT_COMPLETED`
- `VIBRATE`
- `WAKE_LOCK`

Camera and location prompts appear at runtime based on feature usage.

---

## Install APK On Device

Via ADB:

```powershell
adb install -r frontend\aura-apk\android\app\build\outputs\apk\debug\app-debug.apk
```

Or copy the APK to the phone and install manually.

---

## Rebuild Rules

Rebuild the APK whenever any of the following changes:

- frontend source code
- backend base URL values
- Capacitor/plugin configuration

Use `npm run android:build:debug` after each change set to keep assets and config in sync.

