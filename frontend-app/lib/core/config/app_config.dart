import 'package:flutter/foundation.dart';

/// Compile-time configuration, supplied via `--dart-define`.
///
/// Example (run against the cloud backend):
///   flutter run \
///     --dart-define=AURA_API_BASE_URL=https://api.yourdomain.com \
///     --dart-define=AURA_ASSISTANT_BASE_URL=https://assistant.yourdomain.com
///
/// Security note: the values come from `--dart-define-from-file=config/cloud.json`
/// (git-ignored). They're embedded into the compiled binary, NOT read from disk
/// at run time — so reverse-engineering the APK can reveal them. Use HTTPS
/// for both backend + assistant in production so the bytes on the wire are
/// encrypted regardless of whether the URLs are leaked.
class AppConfig {
  AppConfig._();

  /// Backend root (no trailing `/api`). Defaults to the staging cloud
  /// backend so `flutter run -d <real-phone>` works without remembering
  /// `--dart-define-from-file=config/cloud.json` — real phones can't resolve
  /// the emulator-only `10.0.2.2` address, so a 10.0.2.2 default made every
  /// API call fail with "Network error" on hardware. Override with
  /// `--dart-define=AURA_API_BASE_URL=...` for a different environment.
  /// The IP is already in the project README + AndroidManifest network
  /// security config, so it's not a secret.
  static const String apiBaseUrl = String.fromEnvironment(
    'AURA_API_BASE_URL',
    defaultValue: 'http://18.142.190.113:8001',
  );

  /// AI assistant service root. Same reasoning as [apiBaseUrl] for the
  /// staging-cloud default.
  static const String assistantBaseUrl = String.fromEnvironment(
    'AURA_ASSISTANT_BASE_URL',
    defaultValue: 'http://18.142.190.113:8500',
  );

  static const int apiTimeoutMs =
      int.fromEnvironment('AURA_API_TIMEOUT_MS', defaultValue: 15000);

  static const int importApiTimeoutMs =
      int.fromEnvironment('AURA_IMPORT_API_TIMEOUT_MS', defaultValue: 60000);

  // Google OAuth client IDs.
  // Web client ID is also used as `serverClientId` on Android/iOS so the
  // backend (which checks `aud` against `google_web_client_id`) can validate
  // the ID token returned by the native SDK.
  static const String googleWebClientId =
      String.fromEnvironment('AURA_GOOGLE_WEB_CLIENT_ID', defaultValue: '');
  static const String googleIosClientId =
      String.fromEnvironment('AURA_GOOGLE_IOS_CLIENT_ID', defaultValue: '');
  static const String googleAndroidClientId =
      String.fromEnvironment('AURA_GOOGLE_ANDROID_CLIENT_ID', defaultValue: '');

  static bool get isApiConfigured => apiBaseUrl.trim().isNotEmpty;

  /// True when Google sign-in has the minimum config (web/server client id).
  /// Without this the backend cannot validate the returned ID token.
  static bool get isGoogleSignInConfigured =>
      googleWebClientId.trim().isNotEmpty;

  /// True when the *production* (release) build was compiled pointing at a
  /// plain-HTTP backend. Used by [DioClient] and the splash screen to refuse
  /// to send credentials over the wire in clear text.
  ///
  /// Debug builds are intentionally allowed to talk HTTP to the IP-based
  /// staging backend during development.
  static bool get isInsecureInRelease {
    if (kDebugMode) return false;
    final api = apiBaseUrl.trim().toLowerCase();
    final assistant = assistantBaseUrl.trim().toLowerCase();
    return api.startsWith('http://') || assistant.startsWith('http://');
  }
}
