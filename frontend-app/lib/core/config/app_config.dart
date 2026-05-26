/// Compile-time configuration, supplied via `--dart-define`.
///
/// Example (run against the cloud backend):
///   flutter run \
///     --dart-define=AURA_API_BASE_URL=https://api.yourdomain.com \
///     --dart-define=AURA_ASSISTANT_BASE_URL=https://assistant.yourdomain.com
class AppConfig {
  AppConfig._();

  /// Backend root (no trailing `/api`). Defaults to the Android emulator's
  /// host-loopback for local dev; override with the cloud URL at run/build time.
  static const String apiBaseUrl = String.fromEnvironment(
    'AURA_API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  /// AI assistant service root.
  static const String assistantBaseUrl = String.fromEnvironment(
    'AURA_ASSISTANT_BASE_URL',
    defaultValue: 'http://10.0.2.2:8500',
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
}
