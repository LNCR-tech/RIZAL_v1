import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/session_controller.dart';
import '../auth/token_store.dart';
import '../cache/cache_store.dart';
import '../config/app_config.dart';
import 'api_exception.dart';
import 'base_url.dart';

typedef UnauthorizedCallback = void Function();

/// Thin Dio wrapper: attaches the bearer token, normalizes errors to
/// [ApiException], and signals 401s to the session layer.
///
/// Security:
///   * Release builds refuse plain HTTP base URLs (defence in depth — the
///     Android network-security-config and iOS ATS already reject cleartext
///     to anything but the known dev hosts, but this is a third belt at the
///     application layer).
///   * `Accept` + `X-Requested-With` are sent on every request so server-side
///     CSRF heuristics can reject browser-form-style POSTs.
///   * No `User-Agent` override — leaving the default makes traffic look like
///     stock Dart; custom UA strings are a fingerprinting hint.
///   * TLS certificate pinning hook is wired but disabled until the backend
///     ships HTTPS. See [_pinTlsCertificates] below.
class DioClient {
  DioClient({required TokenStore tokenStore, this.cache, String? baseUrl})
      : _tokenStore = tokenStore,
        dio = Dio(
          BaseOptions(
            baseUrl: BackendBaseUrl.normalize(baseUrl ?? AppConfig.apiBaseUrl),
            connectTimeout: const Duration(milliseconds: AppConfig.apiTimeoutMs),
            receiveTimeout: const Duration(milliseconds: AppConfig.apiTimeoutMs),
            sendTimeout: const Duration(milliseconds: AppConfig.apiTimeoutMs),
            headers: const {
              'Accept': 'application/json',
              // Lets the backend distinguish app traffic from a browser
              // form-submit if it ever adds CSRF heuristics.
              'X-Requested-With': 'AuraApp',
            },
          ),
        ) {
    _assertSecureInRelease(dio.options.baseUrl);
    _pinTlsCertificates(dio);
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _tokenStore.read();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onResponse: (response, handler) async {
          if (cache != null &&
              response.requestOptions.method == 'GET' &&
              response.statusCode == 200) {
            await cache!.write(
                response.requestOptions.uri.toString(), response.data);
          }
          handler.next(response);
        },
        onError: (e, handler) async {
          const networkTypes = {
            DioExceptionType.connectionError,
            DioExceptionType.connectionTimeout,
            DioExceptionType.receiveTimeout,
            DioExceptionType.sendTimeout,
          };
          if (cache != null &&
              e.requestOptions.method == 'GET' &&
              networkTypes.contains(e.type)) {
            final cached = await cache!.read(e.requestOptions.uri.toString());
            if (cached != null) {
              handler.resolve(Response(
                requestOptions: e.requestOptions,
                data: cached,
                statusCode: 200,
              ));
              return;
            }
          }
          if (e.response?.statusCode == 401) {
            // Diagnostic — only in debug builds. In release this is silent so
            // we don't leak URLs to the console.
            if (kDebugMode) {
              final path = e.requestOptions.path;
              final method = e.requestOptions.method;
              final body = e.response?.data;
              // ignore: avoid_print
              print(
                'AURA 401 → $method $path '
                '${body is Map ? body.cast<String, dynamic>()['detail'] ?? body : body}',
              );
            }
            // Don't logout on 401s from login-style endpoints — those are
            // credential failures, not session invalidations. Only authed
            // requests should drive the session into expired state.
            final path = e.requestOptions.path.toLowerCase();
            final isLoginEndpoint = path.endsWith('/token') ||
                path.endsWith('/login') ||
                path.endsWith('/auth/google') ||
                path.endsWith('/auth/forgot-password');
            if (!isLoginEndpoint) {
              onUnauthorized?.call();
            }
          }
          handler.next(e);
        },
      ),
    );
  }

  final Dio dio;
  final TokenStore _tokenStore;
  final CacheStore? cache;

  /// Invoked when any request returns 401. Wired by [dioClientProvider].
  UnauthorizedCallback? onUnauthorized;

  Future<Response<dynamic>> get(String path, {Map<String, dynamic>? query}) =>
      _guard(() => dio.get(path, queryParameters: _clean(query)));

  Future<Response<dynamic>> post(
    String path, {
    dynamic data,
    Map<String, dynamic>? query,
    Options? options,
  }) =>
      _guard(() => dio.post(path,
          data: data, queryParameters: _clean(query), options: options));

  Future<Response<dynamic>> put(String path, {dynamic data}) =>
      _guard(() => dio.put(path, data: data));

  Future<Response<dynamic>> patch(String path,
          {dynamic data, Map<String, dynamic>? query}) =>
      _guard(() => dio.patch(path, data: data, queryParameters: _clean(query)));

  Future<Response<dynamic>> delete(String path, {dynamic data}) =>
      _guard(() => dio.delete(path, data: data));

  Future<Response<dynamic>> _guard(
      Future<Response<dynamic>> Function() run) async {
    try {
      return await run();
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  static Map<String, dynamic>? _clean(Map<String, dynamic>? q) {
    if (q == null) return null;
    final out = <String, dynamic>{};
    q.forEach((k, v) {
      if (v != null && v != '') out[k] = v;
    });
    return out;
  }

  /// Application-layer HTTPS guard. Release builds that were compiled with a
  /// plain-HTTP base URL refuse to talk to it — credentials never leave the
  /// device over clear text in production no matter what `cloud.json` said.
  /// Debug builds still allow HTTP for development against IP-based dev
  /// backends.
  static void _assertSecureInRelease(String baseUrl) {
    if (kDebugMode) return;
    if (baseUrl.toLowerCase().startsWith('http://')) {
      throw StateError(
        'Aura was built in release mode with a non-HTTPS base URL '
        '("$baseUrl"). Refusing to send requests over cleartext. Rebuild '
        'with `--dart-define=AURA_API_BASE_URL=https://...` once your '
        'backend is reachable over HTTPS.',
      );
    }
  }

  /// TLS certificate pinning hook. Disabled until the backend ships HTTPS —
  /// pinning a cert against an HTTP origin is impossible.
  ///
  /// When you do flip the backend to HTTPS:
  ///   1. Run `openssl s_client -connect api.aura.school:443 -showcerts`
  ///      (or use the issuer cert in `infra/certs/`).
  ///   2. Compute the SHA-256 fingerprint of the public-key SubjectPublicKeyInfo:
  ///      `openssl x509 -in cert.pem -pubkey -noout |
  ///       openssl pkey -pubin -outform der |
  ///       openssl dgst -sha256 -binary | openssl enc -base64`
  ///   3. Replace the empty list below with the expected pin(s) and
  ///      uncomment the [IOHttpClientAdapter] override.
  ///
  /// References:
  ///   https://pub.dev/packages/dio  — `IOHttpClientAdapter`
  ///   https://owasp.org/www-community/controls/Certificate_and_Public_Key_Pinning
  static void _pinTlsCertificates(Dio dio) {
    // Intentionally a no-op for now. The scaffolding stays so the
    // production hardening pass only flips a flag instead of restructuring
    // network code under time pressure.
    //
    // const expectedSpkiSha256 = <String>[
    //   // 'sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=',
    // ];
    // dio.httpClientAdapter = IOHttpClientAdapter(
    //   createHttpClient: () {
    //     final client = HttpClient()
    //       ..badCertificateCallback = (cert, host, port) => false;
    //     return client;
    //   },
    //   validateCertificate: (cert, host, port) {
    //     final spki = sha256
    //         .convert(cert!.der)
    //         .bytes;
    //     final encoded = 'sha256/${base64.encode(spki)}';
    //     return expectedSpkiSha256.contains(encoded);
    //   },
    // );
  }
}

/// App-wide Dio client. 401s drive the session into an expired state.
final dioClientProvider = Provider<DioClient>((ref) {
  final client = DioClient(
    tokenStore: ref.watch(tokenStoreProvider),
    cache: ref.watch(cacheStoreProvider),
  );
  client.onUnauthorized =
      () => ref.read(sessionControllerProvider.notifier).handleUnauthorized();
  return client;
});
