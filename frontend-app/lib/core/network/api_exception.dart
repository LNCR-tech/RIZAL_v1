import 'package:dio/dio.dart';

/// Friendly, typed error surfaced to the UI. Maps FastAPI error bodies
/// (`{detail: "..."}`, `{detail: [{loc, msg}]}`) to readable messages,
/// mirroring `extractBackendErrorMessage` in the web client.
class ApiException implements Exception {
  ApiException(
    this.message, {
    this.statusCode = 0,
    this.details,
    this.isNetwork = false,
  });

  final String message;
  final int statusCode;
  final Object? details;
  final bool isNetwork;

  bool get isUnauthorized => statusCode == 401;
  bool get isForbidden => statusCode == 403;
  bool get isNotFound => statusCode == 404;

  @override
  String toString() => 'ApiException($statusCode): $message';

  factory ApiException.fromDio(DioException e) {
    final status = e.response?.statusCode ?? 0;

    const networkTypes = {
      DioExceptionType.connectionError,
      DioExceptionType.connectionTimeout,
      DioExceptionType.receiveTimeout,
      DioExceptionType.sendTimeout,
    };
    if (networkTypes.contains(e.type)) {
      return ApiException(
        'Network problem. Check your connection and try again.',
        statusCode: status,
        isNetwork: true,
      );
    }

    final msg = _extractMessage(e.response?.data) ??
        e.message ??
        'Something went wrong. Please try again.';
    return ApiException(msg, statusCode: status, details: e.response?.data);
  }

  static String? _extractMessage(dynamic data) {
    String? visit(dynamic v) {
      if (v == null) return null;
      if (v is String) {
        final s = v.trim();
        if (s.startsWith('<!DOCTYPE') || s.startsWith('<html')) return null;
        return s.isEmpty ? null : s;
      }
      if (v is List) {
        final parts = v.map(visit).whereType<String>().take(3).toList();
        return parts.isEmpty ? null : parts.join('; ');
      }
      if (v is Map) {
        final msg = (v['msg'] ?? v['message'] ?? v['reason'])?.toString();
        if (msg != null && msg.trim().isNotEmpty) {
          final loc = v['loc'];
          if (loc is List && loc.isNotEmpty) {
            final path = loc
                .map((e) => e.toString())
                .where((s) =>
                    !['body', 'query', 'path', 'response']
                        .contains(s.toLowerCase()))
                .join('.');
            return path.isEmpty ? msg : '$path: $msg';
          }
          return msg;
        }
        for (final key in ['detail', 'message', 'reason', 'error', 'errors', 'title']) {
          final found = visit(v[key]);
          if (found != null) return found;
        }
      }
      return null;
    }

    return visit(data);
  }
}
