# Release & operations — Aura (RIZAL) Flutter app

How to build, sign, and ship the app, plus the credential-gated follow-ups
(push, store listings) that need accounts only the team has.

## Build

```bash
flutter pub get
# Endpoints come from the git-ignored config/cloud.json:
flutter build apk        --dart-define-from-file=config/cloud.json   # Android APK
flutter build appbundle  --dart-define-from-file=config/cloud.json   # Play Store
flutter build ipa        --dart-define-from-file=config/cloud.json   # iOS (on macOS)
```

CI (`.github/workflows/aura-app-ci.yml`) runs `flutter analyze` + `flutter test`
on every change to `frontend-app/`, then builds a debug APK.

## Android signing
1. Create a keystore (keep it OUT of git):
   ```bash
   keytool -genkey -v -keystore aura-release.jks -keyalg RSA -keysize 2048 \
     -validity 10000 -alias aura
   ```
2. Add `android/key.properties` (git-ignored):
   ```
   storePassword=...
   keyPassword=...
   keyAlias=aura
   storeFile=/absolute/path/to/aura-release.jks
   ```
3. In `android/app/build.gradle.kts`, load `key.properties` and add a
   `release` `signingConfig`, then set `buildTypes.release.signingConfig` to it.
   (Add `key.properties` and `*.jks` to `.gitignore`.)

## iOS signing
- Open `ios/Runner.xcworkspace` in Xcode, set the Team and a unique bundle id
  under Signing & Capabilities, then `flutter build ipa`.
- Add NSCameraUsageDescription / NSLocationWhenInUseUsageDescription are already
  present in `ios/Runner/Info.plist`.

## App icon & splash (recommended)
- Add `flutter_launcher_icons` + `flutter_native_splash` dev-deps and a lime/ink
  icon asset, then run their generators. (Currently using the default icon.)

## Production hardening checklist
- [ ] Serve the backend over **HTTPS** and remove the dev-only cleartext flags
      (Android `usesCleartextTraffic`, iOS `NSAppTransportSecurity`).
- [ ] Provide production `config/cloud.json` (or pass `--dart-define`s in CI).
- [ ] Set a clean `applicationId` / bundle id for stores (currently
      `com.aura.aura_app`).

## Push notifications (FCM) — follow-up, needs a Firebase project
Not wired yet (requires the team's Firebase project + config files):
1. `flutter pub add firebase_core firebase_messaging`.
2. `flutterfire configure` → places `android/app/google-services.json` and
   `ios/Runner/GoogleService-Info.plist`, and the Gradle google-services plugin.
3. Init `Firebase.initializeApp()` in `main.dart`; request permission; read the
   FCM token and register it with the backend; handle `onMessage` /
   `onMessageOpenedApp` and route to the relevant screen.
4. Backend sends pushes for the existing notification categories (missed events,
   low attendance, account security).
   - For local/scheduled reminders without a server, add
     `flutter_local_notifications` instead.

## Deep links — follow-up
Add Android `intent-filter` (App Links) + iOS Associated Domains, then map
incoming paths (e.g. `/events/{id}`) to the relevant screen.

## Store metadata checklist
- [ ] App name, short + full description, keywords.
- [ ] Screenshots (phone + tablet), feature graphic.
- [ ] Privacy policy URL; data-safety / privacy nutrition labels (camera,
      location, biometric face data → processed server-side).
- [ ] Content rating, category (Education), contact details.
