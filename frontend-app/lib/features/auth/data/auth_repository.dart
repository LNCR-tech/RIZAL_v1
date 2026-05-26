import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/auth_meta.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/network/dio_client.dart';

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

  /// Submit a password-reset request for admin approval
  /// (`POST /auth/forgot-password`). Backend always returns a generic message
  /// (no enumeration), which is the string we surface to the user verbatim.
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

  /// Exchange a Google ID token for an Aura access token + meta
  /// (`POST /auth/google`). Backend errors:
  /// 403 → Google login disabled, 401 → invalid token / unverified email,
  /// 404 → email not registered. All surface as [ApiException].
  Future<LoginResult> loginWithGoogle({required String idToken}) async {
    final body = {'id_token': idToken};
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
    final token = (data['access_token'] ?? '').toString();
    if (token.isEmpty) {
      throw ApiException(
        'Signed in with Google, but the server did not return a token.',
        statusCode: res.statusCode ?? 0,
      );
    }
    return LoginResult(accessToken: token, meta: AuthMeta.fromJson(data));
  }
}

final authRepositoryProvider =
    Provider<AuthRepository>((ref) => AuthRepository(ref.watch(dioClientProvider)));
