# Aura APK Workspace

This folder contains the native Android workspace for the Aura Capacitor app.

## What lives here

- `android/`: the editable Android Studio / Gradle project
- `build-apk.cmd`: wrapper that builds the APK from the repo root web app
- `outputs/`: copied debug or release APK files after a build

## How it works

The Vue app lives in the repo root. Capacitor is configured so `npx cap sync android` writes web assets and plugin changes into `aura-apk/android`.

## Build

From this folder:

```bat
.\build-apk.cmd
.\build-apk.cmd release
```

Or from the repo root:

```powershell
npm run android:build:debug
npm run android:build:release
```
