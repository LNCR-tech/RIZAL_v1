import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../../core/config/app_config.dart';

/// Friendly errors surfaced from the Google sign-in flow. The UI catches
/// these and shows [message] verbatim.
class GoogleSignInError implements Exception {
  GoogleSignInError(this.message);
  final String message;

  @override
  String toString() => 'GoogleSignInError: $message';
}

/// Holds whichever credential Google returned. On Android/native the SDK
/// always provides [idToken]. On web (implicit flow) only [accessToken] is
/// available; the backend accepts both via its /auth/google endpoint.
class GoogleToken {
  const GoogleToken({this.idToken, this.accessToken});
  final String? idToken;
  final String? accessToken;
}

/// Thin wrapper around the `google_sign_in` package. Reads the web/server
/// client ID from [AppConfig.googleWebClientId] (set via
/// `--dart-define=AURA_GOOGLE_WEB_CLIENT_ID=...`). If the ID isn't set the
/// service refuses to attempt sign-in and the UI shows a clear "not
/// configured" message rather than a cryptic platform error.
///
/// Returned ID tokens are sent verbatim to the backend
/// (`POST /auth/google`) which verifies them against the same client IDs
/// listed in its `google_web_client_id` / `google_android_client_id`
/// settings.
class GoogleSignInService {
  GoogleSignInService._() {
    final webClientId = AppConfig.googleWebClientId.trim();
    if (webClientId.isEmpty) {
      _client = null;
      return;
    }
    _client = GoogleSignIn(
      scopes: const ['email', 'profile'],
      // Web requires `clientId`. Native platforms ignore it (they read
      // the OAuth config from google-services.json / Info.plist).
      clientId: kIsWeb ? webClientId : null,
      // `serverClientId` makes the native SDK fetch a server-validatable
      // ID token (the same client ID the backend verifies against).
      serverClientId: webClientId,
    );
  }

  static final GoogleSignInService instance = GoogleSignInService._();

  GoogleSignIn? _client;

  /// True only when [AppConfig.googleWebClientId] is set — otherwise the
  /// Google button shows a "not configured" snackbar instead of attempting
  /// sign-in.
  bool get isConfigured => _client != null;

  /// Drives the Google sign-in sheet and returns the available credential.
  /// Returns `null` when the user cancels the picker. Throws
  /// [GoogleSignInError] for any other failure path.
  ///
  /// On Android/native [GoogleToken.idToken] is always populated.
  /// On web (implicit OAuth2 flow) only [GoogleToken.accessToken] is returned;
  /// the backend accepts both.
  Future<GoogleToken?> signIn() async {
    final client = _client;
    if (client == null) {
      throw GoogleSignInError(
        'Sign in with Google isn\'t enabled for this app yet. '
        'Use your school email and password, or ask your Campus Admin.',
      );
    }
    try {
      GoogleSignInAccount? account = await client.signInSilently();
      account ??= await client.signIn();
      if (account == null) return null; // user dismissed the picker
      final auth = await account.authentication;
      final idToken = auth.idToken;
      final accessToken = auth.accessToken;
      if ((idToken == null || idToken.isEmpty) &&
          (accessToken == null || accessToken.isEmpty)) {
        throw GoogleSignInError(
          'Google did not return a token. Please try again.',
        );
      }
      return GoogleToken(idToken: idToken, accessToken: accessToken);
    } on GoogleSignInError {
      rethrow;
    } catch (e) {
      throw GoogleSignInError(
        'Google sign-in could not complete. ${_friendly(e)}',
      );
    }
  }

  /// Clear the cached Google account so the next sign-in re-prompts.
  /// Safe to call even when sign-in is not configured.
  Future<void> signOut() async {
    try {
      await _client?.signOut();
    } catch (_) {
      // Best-effort. Failures here don't surface to the user.
    }
  }

  String _friendly(Object e) {
    final s = e.toString();
    // The PlatformException default toString is noisy; strip the prefix.
    final cleaned = s.replaceFirst(RegExp(r'^PlatformException\([^,]*,\s*'), '');
    if (cleaned.length > 200) return cleaned.substring(0, 200);
    return cleaned;
  }
}

final googleSignInServiceProvider = Provider<GoogleSignInService>(
  (ref) => GoogleSignInService.instance,
);
