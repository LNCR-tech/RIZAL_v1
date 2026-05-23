import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/token_store.dart';
import '../../../core/config/app_config.dart';
import '../../../core/network/base_url.dart';

/// One decoded SSE event from the assistant stream.
class AssistantChunk {
  const AssistantChunk(
      {required this.event, this.content, this.conversationId, this.visual});
  final String event; // message | thought | tool_call | tool_done | visualization | done
  final String? content;
  final String? conversationId;
  final Map<String, dynamic>? visual; // chart spec, present on `visualization`
}

/// Streams replies from the assistant service (`POST /assistant/stream`, SSE).
class AssistantService {
  AssistantService(this._dio);
  final Dio _dio;

  Stream<AssistantChunk> stream({
    required String message,
    String? conversationId,
    String? userName,
    String? userSchool,
    int? userSchoolId,
    bool? fast,
  }) async* {
    final res = await _dio.post(
      '/assistant/stream',
      data: {
        'message': message,
        if (conversationId != null) 'conversation_id': conversationId,
        if (userName != null) 'user_name': userName,
        if (userSchool != null) 'user_school': userSchool,
        if (userSchoolId != null) 'user_school_id': userSchoolId,
        if (fast != null) 'fast': fast,
      },
      options: Options(
        responseType: ResponseType.stream,
        headers: {'Accept': 'text/event-stream'},
      ),
    );

    final body = res.data as ResponseBody;
    var buffer = '';
    await for (final bytes in body.stream) {
      buffer += utf8.decode(bytes, allowMalformed: true);
      var idx = buffer.indexOf('\n\n');
      while (idx >= 0) {
        final block = buffer.substring(0, idx);
        buffer = buffer.substring(idx + 2);
        final chunk = _parseBlock(block);
        if (chunk != null) {
          yield chunk;
          if (chunk.event == 'done') return;
        }
        idx = buffer.indexOf('\n\n');
      }
    }
  }

  AssistantChunk? _parseBlock(String block) {
    var event = '';
    var data = '';
    for (final line in block.split('\n')) {
      if (line.startsWith('event:')) event = line.substring(6).trim();
      if (line.startsWith('data:')) data = line.substring(5).trim();
    }
    if (data.isEmpty) return null;

    Map<String, dynamic>? json;
    try {
      final decoded = jsonDecode(data);
      if (decoded is Map) json = decoded.cast<String, dynamic>();
    } catch (_) {
      // Non-JSON data line; treat as raw content.
      return AssistantChunk(event: event.isEmpty ? 'message' : event, content: data);
    }

    final visual = json?['visual'];
    return AssistantChunk(
      event: event.isEmpty ? 'message' : event,
      content: json?['content']?.toString(),
      conversationId: json?['conversation_id']?.toString(),
      visual: visual is Map ? visual.cast<String, dynamic>() : null,
    );
  }
}

/// Dedicated Dio for the assistant service (separate base URL + bearer).
final assistantDioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: BackendBaseUrl.normalize(AppConfig.assistantBaseUrl),
      connectTimeout: const Duration(seconds: 30),
      // A local CPU model can take a while to think. WAIT for it — only a real
      // connection failure should ever surface as "could not reach".
      receiveTimeout: const Duration(seconds: 300),
    ),
  );
  dio.interceptors.add(
    InterceptorsWrapper(onRequest: (options, handler) async {
      final token = await ref.read(tokenStoreProvider).read();
      if (token != null && token.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $token';
      }
      handler.next(options);
    }),
  );
  return dio;
});

final assistantServiceProvider = Provider<AssistantService>(
  (ref) => AssistantService(ref.watch(assistantDioProvider)),
);
