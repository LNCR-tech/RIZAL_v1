import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/auth_meta.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/network/dio_client.dart';
import 'google_sign_in_service.dart' show GoogleToken;

class LoginResult {
  const LoginResult({required this.accessToken, required this.meta});
  final String accessToken;
  final AuthMeta meta;
}

/// Authentication endpoints. `/token` uses the OAuth2 password form, with a
/// fallback to `/api/token` for deployments that mount auth under `/api`.
class AuthRepository {
  AuthRepository(this._client);
  final DioClient _client;

  Future<LoginResult> login({
    required String email,
    required String password,
    bool rememberMe = false,
  }) async {
    final form = {
      'grant_type': 'password',
      'username': email.trim(),
      'password': password,
      'remember_me': rememberMe.toString(),
    };
    final options = Options(contentType: Headers.formUrlEncodedContentType);

    Response<dynamic> res;
    try {
      res = await _client.post('/token', data: form, options: options);
    } on ApiException catch (e) {
      if (e.isNotFound || e.statusCode == 405) {
        res = await _client.post('/api/token', data: form, options: options);
      } else {
        rethrow;
      }
    }

    final data = (res.data as Map).cast<String, dynamic>();
    final token = (data['access_token'] ?? '').toString();
    if (token.isEmpty) {
      throw ApiException(
        'Signed in, but the server did not return a token.',
        statusCode: res.statusCode ?? 0,
      );
    }
    return LoginResult(accessToken: token, meta: AuthMeta.fromJson(data));
  }

  /// Change the signed-in user's password (`POST /auth/change-password`).
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    final body = {
      'current_password': currentPassword,
      'new_password': newPassword,
    };
    try {
      await _client.post('/auth/change-password', data: body);
    } on ApiException catch (e) {
      if (e.isNotFound) {
        await _client.post('/api/auth/change-password', data: body);
        return;
      }
      rethrow;
    }
  }

  /// Request a self-service password reset (`POST /auth/forgot-password`).
  /// Backend mails a 6-digit code (15-minute expiry) via Resend and always
  /// returns the same generic message regardless of whether the email exists
  /// (no enumeration) — surface it verbatim. The companion step is
  /// [resetPasswordWithCode].
  Future<String> forgotPassword(String email) async {
    final body = {'email': email.trim()};
    Response<dynamic> res;
    try {
      res = await _client.post('/auth/forgot-password', data: body);
    } on ApiException catch (e) {
      if (e.isNotFound) {
        res = await _client.post('/api/auth/forgot-password', data: body);
      } else {
        rethrow;
      }
    }
    final data = (res.data as Map).cast<String, dynamic>();
    return (data['message'] ?? 'Reset request submitted.').toString();
  }

  /// Verify the emailed 6-digit code (`POST /auth/verify-reset-code`) and
  /// return the short-lived `reset_token`. The token is single-use and
  /// expires at the same time as the original code (15-minute window). On
  /// failure the backend returns 400 (invalid/expired code) or 429 (rate
  /// limited); both surface as [ApiException].
  Future<String> verifyResetCode({
    required String email,
    required String code,
  }) async {
    final body = {
      'email': email.trim(),
      'code': code.trim(),
    };
    Response<dynamic> res;
    try {
      res = await _client.post('/auth/verify-reset-code', data: body);
    } on ApiException catch (e) {
      if (e.isNotFound) {
        res = await _client.post('/api/auth/verify-reset-code', data: body);
      } else {
        rethrow;
      }
    }
    final data = (res.data as Map).cast<String, dynamic>();
    final token = (data['reset_token'] ?? '').toString();
    if (token.isEmpty) {
      throw ApiException(
        'Code verified, but the server did not return a reset token.',
        statusCode: res.statusCode ?? 0,
      );
    }
    return token;
  }

  /// Consume the short-lived `reset_token` from [verifyResetCode] and set
  /// the new password (`POST /auth/reset-password`). The token is
  /// single-use; the backend returns 400 if it is invalid, expired, or
  /// already spent — surfaces as [ApiException].
  Future<String> resetPassword({
    required String resetToken,
    required String newPassword,
  }) async {
    final body = {
      'reset_token': resetToken,
      'new_password': newPassword,
    };
    Response<dynamic> res;
    try {
      res = await _client.post('/auth/reset-password', data: body);
    } on ApiException catch (e) {
      if (e.isNotFound) {
        res = await _client.post('/api/auth/reset-password', data: body);
      } else {
        rethrow;
      }
    }
    final data = (res.data as Map).cast<String, dynamic>();
    return (data['message'] ?? 'Password has been reset successfully.')
        .toString();
  }

  /// Exchange a Google credential for an Aura access token + meta
  /// (`POST /auth/google`). Sends [id_token] when available (Android/native),
  /// falls back to [access_token] for web implicit flow. Backend errors:
  /// 403 → Google login disabled, 401 → invalid token / unverified email,
  /// 404 → email not registered. All surface as [ApiException].
  Future<LoginResult> loginWithGoogle({required GoogleToken token}) async {
    final body = token.idToken != null
        ? {'id_token': token.idToken}
        : {'access_token': token.accessToken};
    Response<dynamic> res;
    try {
      res = await _client.post('/auth/google', data: body);
    } on ApiException catch (e) {
      if (e.isNotFound) {
        res = await _client.post('/api/auth/google', data: body);
      } else {
        rethrow;
      }
    }
    final data = (res.data as Map).cast<String, dynamic>();
    final accessToken = (data['access_token'] ?? '').toString();
    if (accessToken.isEmpty) {
      throw ApiException(
        'Signed in with Google, but the server did not return a token.',
        statusCode: res.statusCode ?? 0,
      );
    }
    return LoginResult(accessToken: accessToken, meta: AuthMeta.fromJson(data));
  }
}

final authRepositoryProvider =
    Provider<AuthRepository>((ref) => AuthRepository(ref.watch(dioClientProvider)));
