import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_motion.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../application/chat_controller.dart';
import '../application/fast_mode_controller.dart';
import 'widgets/assistant_chart.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _input = TextEditingController();
  final _scroll = ScrollController();

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _send() {
    final text = _input.text;
    if (text.trim().isEmpty) return;
    _input.clear();
    ref.read(chatControllerProvider.notifier).send(text);
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent + 200,
            duration: AppMotion.dropdown, curve: AppMotion.easeOut);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(chatControllerProvider, (_, __) => _scrollToBottom());
    final state = ref.watch(chatControllerProvider);

    return AppScaffold(
      title: 'Aura AI',
      body: Column(
        children: [
          Expanded(
            child: state.messages.isEmpty
                ? const _Intro()
                : ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.all(AppSpacing.x20),
                    itemCount: state.messages.length,
                    itemBuilder: (context, i) =>
                        _Bubble(message: state.messages[i]),
                  ),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(
                AppSpacing.x16, 0, AppSpacing.x16, AppSpacing.x8),
            child:
                Align(alignment: Alignment.centerLeft, child: _ModeToggle()),
          ),
          _InputBar(controller: _input, sending: state.sending, onSend: _send),
        ],
      ),
    );
  }
}

class _Intro extends StatelessWidget {
  const _Intro();

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.x32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration:
                  BoxDecoration(color: t.accent, borderRadius: BorderRadius.circular(20)),
              child: Center(
                child: Text('A',
                    style: TextStyle(
                        color: t.onAccent,
                        fontWeight: FontWeight.w800,
                        fontSize: 32)),
              ),
            ),
            const SizedBox(height: AppSpacing.x16),
            Text('Ask Aura', style: textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.x8),
            Text(
              'Ask about your attendance, upcoming events, or your schedule.',
              textAlign: TextAlign.center,
              style: textTheme.bodyMedium?.copyWith(color: t.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.message});
  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final isUser = message.fromUser;
    final screenW = MediaQuery.of(context).size.width;

    final thinking = !isUser &&
        message.streaming &&
        message.text.isEmpty &&
        message.charts.isEmpty;
    final showBubble = isUser || thinking || message.text.isNotEmpty;

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (showBubble)
            Align(
              alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
              child: ConstrainedBox(
                constraints: BoxConstraints(maxWidth: screenW * 0.8),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.x16, vertical: AppSpacing.x12),
                  decoration: BoxDecoration(
                    color: isUser ? t.accent : t.surfaceAlt,
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(AppRadii.card),
                      topRight: const Radius.circular(AppRadii.card),
                      bottomLeft: Radius.circular(isUser ? AppRadii.card : 6),
                      bottomRight: Radius.circular(isUser ? 6 : AppRadii.card),
                    ),
                  ),
                  child: thinking
                      ? Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            SizedBox(
                                width: 14,
                                height: 14,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2, color: t.textMuted)),
                            const SizedBox(width: AppSpacing.x8),
                            Text('Thinking…',
                                style: textTheme.bodyMedium
                                    ?.copyWith(color: t.textMuted)),
                          ],
                        )
                      : Text(
                          message.text,
                          style: textTheme.bodyLarge?.copyWith(
                              color: isUser ? t.onAccent : t.ink),
                        ),
                ),
              ),
            ),
          for (final chart in message.charts)
            ConstrainedBox(
              constraints: BoxConstraints(maxWidth: screenW * 0.95),
              child: AssistantChart(spec: chart),
            ),
        ],
      ),
    );
  }
}

class _InputBar extends StatelessWidget {
  const _InputBar(
      {required this.controller, required this.sending, required this.onSend});
  final TextEditingController controller;
  final bool sending;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Container(
      decoration: BoxDecoration(
        color: t.bg,
        border: Border(top: BorderSide(color: t.border)),
      ),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
              AppSpacing.x16, AppSpacing.x8, AppSpacing.x16, AppSpacing.x8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  minLines: 1,
                  maxLines: 5,
                  textInputAction: TextInputAction.send,
                  onSubmitted: (_) => onSend(),
                  decoration: const InputDecoration(hintText: 'Ask Aura…'),
                ),
              ),
              const SizedBox(width: AppSpacing.x8),
              _SendButton(busy: sending, onTap: onSend),
            ],
          ),
        ),
      ),
    );
  }
}

class _SendButton extends StatelessWidget {
  const _SendButton({required this.busy, required this.onTap});
  final bool busy;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Semantics(
      button: true,
      label: 'Send',
      child: GestureDetector(
        onTap: busy ? null : onTap,
        child: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: busy ? t.surfaceAlt : t.accent,
            shape: BoxShape.circle,
          ),
          child: busy
              ? Padding(
                  padding: const EdgeInsets.all(14),
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: t.textMuted),
                )
              : Icon(Icons.arrow_upward_rounded, color: t.onAccent),
        ),
      ),
    );
  }
}

/// Compact app-bar segmented control: **Fast** (slim, quick) vs **Think** (full
/// data + charts, slower). Drives [fastModeProvider]; the mode is sent per request.
class _ModeToggle extends ConsumerWidget {
  const _ModeToggle();

  static const double _segW = 70;
  static const double _h = 34;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final fast = ref.watch(fastModeProvider);
    final reduce = MediaQuery.of(context).disableAnimations;
    return Container(
      width: _segW * 2 + 8,
      height: _h,
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: BorderRadius.circular(_h / 2),
        border: Border.all(color: t.border),
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          AnimatedAlign(
            alignment: fast ? Alignment.centerLeft : Alignment.centerRight,
            duration:
                reduce ? Duration.zero : const Duration(milliseconds: 220),
            curve: AppMotion.easeOut,
            child: Container(
              width: _segW,
              height: _h - 6,
              decoration: BoxDecoration(
                color: t.accent,
                borderRadius: BorderRadius.circular((_h - 6) / 2),
              ),
            ),
          ),
          Row(
            children: [
              _segment(ref, t,
                  active: fast,
                  value: true,
                  icon: Icons.bolt_rounded,
                  label: 'Fast',
                  tip: 'Fast — quick replies'),
              _segment(ref, t,
                  active: !fast,
                  value: false,
                  icon: Icons.auto_awesome_rounded,
                  label: 'Think',
                  tip: 'Thinking — full data + charts (slower)'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _segment(WidgetRef ref, AppTokens t,
      {required bool active,
      required bool value,
      required IconData icon,
      required String label,
      required String tip}) {
    final fg = active ? t.onAccent : t.textSecondary;
    return Tooltip(
      message: tip,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () => ref.read(fastModeProvider.notifier).set(value),
        child: SizedBox(
          width: _segW,
          height: _h - 6,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 14, color: fg),
              const SizedBox(width: 4),
              Text(label,
                  style: TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                      color: fg)),
            ],
          ),
        ),
      ),
    );
  }
}
