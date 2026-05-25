import 'package:dio/dio.dart';
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
class DioClient {
  DioClient({required TokenStore tokenStore, this.cache, String? baseUrl})
      : _tokenStore = tokenStore,
        dio = Dio(
          BaseOptions(
            baseUrl: BackendBaseUrl.normalize(baseUrl ?? AppConfig.apiBaseUrl),
            connectTimeout: const Duration(milliseconds: AppConfig.apiTimeoutMs),
            receiveTimeout: const Duration(milliseconds: AppConfig.apiTimeoutMs),
            sendTimeout: const Duration(milliseconds: AppConfig.apiTimeoutMs),
            headers: const {'Accept': 'application/json'},
          ),
        ) {
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
          if (e.response?.statusCode == 401) onUnauthorized?.call();
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
