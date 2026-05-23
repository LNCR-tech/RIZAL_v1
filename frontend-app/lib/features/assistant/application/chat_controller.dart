import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/network/api_exception.dart';
import '../data/assistant_service.dart';
import '../presentation/widgets/assistant_chart.dart';
import 'fast_mode_controller.dart';

@immutable
class ChatMessage {
  const ChatMessage(
      {required this.fromUser,
      required this.text,
      this.streaming = false,
      this.charts = const []});
  final bool fromUser;
  final String text;
  final bool streaming;
  final List<ChartSpec> charts; // charts the assistant generated for this reply

  ChatMessage copyWith({String? text, bool? streaming, List<ChartSpec>? charts}) =>
      ChatMessage(
        fromUser: fromUser,
        text: text ?? this.text,
        streaming: streaming ?? this.streaming,
        charts: charts ?? this.charts,
      );
}

@immutable
class ChatState {
  const ChatState(
      {this.messages = const [], this.sending = false, this.conversationId});
  final List<ChatMessage> messages;
  final bool sending;
  final String? conversationId;

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? sending,
    String? conversationId,
  }) =>
      ChatState(
        messages: messages ?? this.messages,
        sending: sending ?? this.sending,
        conversationId: conversationId ?? this.conversationId,
      );
}

class ChatController extends AutoDisposeNotifier<ChatState> {
  @override
  ChatState build() {
    final meta = ref.read(sessionControllerProvider).meta;
    return ChatState(messages: [
      ChatMessage(fromUser: false, text: _greeting(meta?.displayName)),
    ]);
  }

  /// Instant, client-side personalized greeting (no model call).
  static String _greeting(String? fullName) {
    final first = (fullName ?? '').trim().split(RegExp(r'\s+')).first;
    final hi = first.isEmpty ? 'Hi there!' : 'Hi $first!';
    return "$hi I'm Aura, powered by Jose AI — your campus assistant. "
        "Ask me about your events, attendance, or schedule, or try "
        "\"chart my attendance\" for a quick visual.";
  }

  Future<void> send(String raw) async {
    final text = raw.trim();
    if (text.isEmpty || state.sending) return;

    final meta = ref.read(sessionControllerProvider).meta;
    final messages = [
      ...state.messages,
      ChatMessage(fromUser: true, text: text),
      const ChatMessage(fromUser: false, text: '', streaming: true),
    ];
    final assistantIndex = messages.length - 1;
    state = state.copyWith(messages: messages, sending: true);

    final buffer = StringBuffer();
    try {
      final stream = ref.read(assistantServiceProvider).stream(
            message: text,
            conversationId: state.conversationId,
            userName: meta?.displayName,
            userSchool: meta?.schoolName,
            userSchoolId: meta?.schoolId,
            fast: ref.read(fastModeProvider),
          );
      await for (final chunk in stream) {
        if (chunk.conversationId != null) {
          state = state.copyWith(conversationId: chunk.conversationId);
        }
        if (chunk.event == 'message' && chunk.content != null) {
          buffer.write(chunk.content);
          _setAssistant(assistantIndex, buffer.toString(), streaming: true);
        } else if (chunk.event == 'visualization') {
          final spec = ChartSpec.tryParse(chunk.visual);
          if (spec != null) _addChart(assistantIndex, spec);
        }
      }
      final finalText = buffer.toString().trim();
      final hasCharts = assistantIndex < state.messages.length &&
          state.messages[assistantIndex].charts.isNotEmpty;
      _setAssistant(
          assistantIndex,
          finalText.isEmpty
              ? (hasCharts ? '' : 'Aura had nothing to add.')
              : finalText,
          streaming: false);
      state = state.copyWith(sending: false);
    } on ApiException catch (e) {
      _setAssistant(assistantIndex, e.message, streaming: false);
      state = state.copyWith(sending: false);
    } on DioException catch (e) {
      // A timeout means the model is busy/slow — not unreachable. Say so honestly.
      final slow = e.type == DioExceptionType.receiveTimeout ||
          e.type == DioExceptionType.sendTimeout ||
          e.type == DioExceptionType.connectionTimeout;
      _setAssistant(
          assistantIndex,
          slow
              ? 'Aura is taking a while to think (the local model is busy). Please try again.'
              : 'Could not reach Aura AI. Please try again.',
          streaming: false);
      state = state.copyWith(sending: false);
    } catch (_) {
      _setAssistant(assistantIndex,
          'Could not reach Aura AI. Please try again.', streaming: false);
      state = state.copyWith(sending: false);
    }
  }

  void _setAssistant(int index, String text, {required bool streaming}) {
    if (index >= state.messages.length) return;
    final list = [...state.messages];
    list[index] = list[index].copyWith(text: text, streaming: streaming);
    state = state.copyWith(messages: list);
  }

  void _addChart(int index, ChartSpec spec) {
    if (index >= state.messages.length) return;
    final list = [...state.messages];
    final m = list[index];
    list[index] = m.copyWith(charts: [...m.charts, spec]);
    state = state.copyWith(messages: list);
  }
}

final chatControllerProvider =
    AutoDisposeNotifierProvider<ChatController, ChatState>(ChatController.new);
