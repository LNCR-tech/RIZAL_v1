import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_motion.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../../../core/widgets/pressable.dart';
import '../data/auth_repository.dart';

/// Self-service password reset — three-stage flow matching the backend
/// contract (commit 154c815):
///
///   1. `POST /auth/forgot-password`     → emails a 6-digit code.
///   2. `POST /auth/verify-reset-code`   → returns a short-lived reset_token.
///   3. `POST /auth/reset-password`      → consumes the token + new password.
///
/// The user only sees the new-password form *after* the code is verified —
/// stage 3 is unreachable without a valid reset_token. Anti-enumeration is
/// preserved at stage 1 (always-generic response).
///
/// Motion (flutter-animations + emil-design-eng):
///   - Stage transition: `AppMotion.modal` (260ms) cross-fade with
///     asymmetric lift — outgoing drops 12 dp, incoming lifts 8 dp.
///     `AppMotion.easeOut` only; never ease-in for UI.
///   - OTP cell pop on digit entry: 80 ms scale up, 140 ms settle —
///     asymmetric, feedback-first.
///   - Error banner: 200 ms fade + 6 dp downward slide via
///     `AnimatedSwitcher`.
///   - Stage-progress strip: per-segment colour animated 240 ms ease-out
///     on stage advance. Active = brand accent, completed = accent 50 %,
///     upcoming = border tint.
///   - All paths gated on `MediaQuery.disableAnimations` →
///     `Duration.zero`.
class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key, this.initialEmail});

  final String? initialEmail;

  static Future<void> push(BuildContext context, {String? initialEmail}) {
    return Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) => ForgotPasswordScreen(initialEmail: initialEmail),
      ),
    );
  }

  @override
  ConsumerState<ForgotPasswordScreen> createState() =>
      _ForgotPasswordScreenState();
}

enum _Stage { email, code, password }

const int _kResendCooldownSeconds = 45;
const int _kCodeLength = 6;
const int _kMinPasswordLength = 8;

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  late final TextEditingController _email =
      TextEditingController(text: widget.initialEmail ?? '');
  final TextEditingController _code = TextEditingController();
  final TextEditingController _password = TextEditingController();
  final TextEditingController _confirm = TextEditingController();
  final FocusNode _codeFocus = FocusNode();
  final FocusNode _passwordFocus = FocusNode();

  _Stage _stage = _Stage.email;
  bool _loading = false;
  String? _error;
  bool _obscurePassword = true;
  bool _obscureConfirm = true;

  Timer? _cooldownTimer;
  int _cooldown = 0;

  /// Short-lived token returned by `/auth/verify-reset-code`. Present only
  /// between successful code verification and a successful (or failed)
  /// password reset.
  String? _resetToken;

  @override
  void dispose() {
    _cooldownTimer?.cancel();
    _email.dispose();
    _code.dispose();
    _password.dispose();
    _confirm.dispose();
    _codeFocus.dispose();
    _passwordFocus.dispose();
    super.dispose();
  }

  // -- cooldown ----------------------------------------------------------

  void _startCooldown() {
    _cooldownTimer?.cancel();
    setState(() => _cooldown = _kResendCooldownSeconds);
    _cooldownTimer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) {
        t.cancel();
        return;
      }
      setState(() {
        _cooldown -= 1;
        if (_cooldown <= 0) {
          _cooldown = 0;
          t.cancel();
        }
      });
    });
  }

  // -- network handlers --------------------------------------------------

  Future<void> _sendCode({bool isResend = false}) async {
    final email = _email.text.trim();
    if (email.isEmpty) {
      setState(() => _error = 'Enter your school email.');
      return;
    }
    if (!email.contains('@')) {
      setState(() => _error = "That doesn't look like an email address.");
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(authRepositoryProvider).forgotPassword(email);
      if (!mounted) return;
      _startCooldown();
      final messenger = isResend ? ScaffoldMessenger.of(context) : null;
      setState(() {
        _loading = false;
        if (!isResend) _stage = _Stage.code;
      });
      if (isResend) {
        messenger?.showSnackBar(
          const SnackBar(content: Text('Resent. Check your inbox.')),
        );
      } else {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) _codeFocus.requestFocus();
        });
      }
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.message;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error =
            "Couldn't reach the server. Check your connection and try again.";
      });
    }
  }

  Future<void> _verifyCode() async {
    final code = _code.text;
    if (code.length != _kCodeLength) {
      setState(() =>
          _error = 'Enter the $_kCodeLength-digit code from your email.');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final token = await ref.read(authRepositoryProvider).verifyResetCode(
            email: _email.text.trim(),
            code: code,
          );
      if (!mounted) return;
      setState(() {
        _loading = false;
        _resetToken = token;
        _stage = _Stage.password;
      });
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _passwordFocus.requestFocus();
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.message;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error =
            "Couldn't reach the server. Check your connection and try again.";
      });
    }
  }

  Future<void> _resetPassword() async {
    final pw = _password.text;
    final token = _resetToken;
    if (token == null || token.isEmpty) {
      // Defensive: unreachable in normal flow — stage 3 is gated on a
      // non-null token. Surface a recovery path instead of silently
      // failing.
      setState(() {
        _error = 'Verify your code first.';
        _stage = _Stage.code;
      });
      return;
    }
    if (pw.length < _kMinPasswordLength) {
      setState(() => _error =
          'Use at least $_kMinPasswordLength characters for the new password.');
      return;
    }
    if (pw != _confirm.text) {
      setState(() => _error = "The two passwords don't match.");
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(authRepositoryProvider).resetPassword(
            resetToken: token,
            newPassword: pw,
          );
      if (!mounted) return;
      // Capture the messenger before popping — after pop, the local
      // context is detached, but the ancestor's messenger still resolves.
      final messenger = ScaffoldMessenger.of(context);
      HapticFeedback.lightImpact();
      Navigator.of(context).pop();
      messenger.showSnackBar(
        const SnackBar(
          content: Text('Password reset. Sign in with your new password.'),
        ),
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.message;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error =
            "Couldn't reach the server. Check your connection and try again.";
      });
    }
  }

  // -- back navigation ---------------------------------------------------

  void _backOrCancel() {
    if (_loading) return;
    switch (_stage) {
      case _Stage.email:
        Navigator.of(context).pop();
        break;
      case _Stage.code:
        setState(() {
          _stage = _Stage.email;
          _code.clear();
          _error = null;
        });
        break;
      case _Stage.password:
        // The token is single-use and time-bound; once we've moved off the
        // password stage we drop it so the user re-verifies — keeps the
        // server-side guarantee honest.
        setState(() {
          _stage = _Stage.code;
          _password.clear();
          _confirm.clear();
          _resetToken = null;
          _error = null;
        });
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) _codeFocus.requestFocus();
        });
        break;
    }
  }

  // -- build -------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final reduceMotion =
        MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final transition = reduceMotion ? Duration.zero : AppMotion.modal;

    return Scaffold(
      backgroundColor: t.bg,
      appBar: AppBar(
        backgroundColor: t.bg,
        elevation: 0,
        scrolledUnderElevation: 0,
        leading: BackButton(
          color: t.ink,
          onPressed: _loading ? null : _backOrCancel,
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x20,
            vertical: AppSpacing.x8,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _StageProgress(stage: _stage, reduceMotion: reduceMotion),
              const SizedBox(height: AppSpacing.x24),
              AnimatedSwitcher(
                duration: transition,
                switchInCurve: AppMotion.easeOut,
                switchOutCurve: AppMotion.easeOut,
                layoutBuilder: (currentChild, previousChildren) {
                  return Stack(
                    alignment: Alignment.topCenter,
                    children: [
                      ...previousChildren,
                      if (currentChild != null) currentChild,
                    ],
                  );
                },
                transitionBuilder: _stageTransition,
                child: switch (_stage) {
                  _Stage.email => _buildEmailStage(context),
                  _Stage.code => _buildCodeStage(context),
                  _Stage.password => _buildPasswordStage(context),
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Asymmetric stage transition: outgoing drops 12 dp + fades; incoming
  /// lifts 8 dp + fades. Feedback-first per emil-design-eng — the user's
  /// eyes track upward to the next form before the outgoing one is gone.
  Widget _stageTransition(Widget child, Animation<double> anim) {
    final entering = anim.status == AnimationStatus.forward ||
        anim.status == AnimationStatus.completed;
    final slide = Tween<Offset>(
      begin: Offset(0, entering ? 0.04 : -0.06),
      end: Offset.zero,
    ).animate(anim);
    return FadeTransition(
      opacity: anim,
      child: SlideTransition(position: slide, child: child),
    );
  }

  // -- stage builders ----------------------------------------------------

  Widget _buildEmailStage(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Column(
      key: const ValueKey<_Stage>(_Stage.email),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const _IconBadge(icon: Icons.lock_reset_rounded),
        const SizedBox(height: AppSpacing.x20),
        Text('Reset your password', style: textTheme.headlineSmall),
        const SizedBox(height: AppSpacing.x8),
        Text(
          "Enter your school email and we'll send a 6-digit code to your "
          'inbox. The code is valid for 15 minutes.',
          style: textTheme.bodyMedium
              ?.copyWith(color: t.textSecondary, height: 1.5),
        ),
        const SizedBox(height: AppSpacing.x24),
        AuraTextField(
          label: 'School email',
          hint: 'you@school.edu',
          controller: _email,
          keyboardType: TextInputType.emailAddress,
          textInputAction: TextInputAction.done,
          prefixIcon: Icons.mail_outline_rounded,
          autofillHints: const [
            AutofillHints.username,
            AutofillHints.email,
          ],
          enabled: !_loading,
          onSubmitted: (_) => _sendCode(),
        ),
        _ErrorBanner.show(error: _error),
        const SizedBox(height: AppSpacing.x20),
        AuraButton(
          label: 'Send reset code',
          icon: Icons.send_rounded,
          loading: _loading,
          onPressed: _loading ? null : _sendCode,
        ),
        const SizedBox(height: AppSpacing.x16),
        Center(
          child: Pressable(
            scale: 0.99,
            haptic: false,
            onTap: _loading ? null : () => Navigator.of(context).pop(),
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.x12,
                vertical: AppSpacing.x8,
              ),
              child: RichText(
                text: TextSpan(
                  style: textTheme.bodyMedium
                      ?.copyWith(color: t.textSecondary),
                  children: [
                    const TextSpan(text: 'Remember your password? '),
                    TextSpan(
                      text: 'Sign in.',
                      style: TextStyle(
                        color: t.ink,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCodeStage(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final canResend = _cooldown <= 0 && !_loading;
    return Column(
      key: const ValueKey<_Stage>(_Stage.code),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const _IconBadge(icon: Icons.mark_email_read_rounded),
        const SizedBox(height: AppSpacing.x20),
        Text('Check your inbox', style: textTheme.headlineSmall),
        const SizedBox(height: AppSpacing.x8),
        RichText(
          text: TextSpan(
            style: textTheme.bodyMedium
                ?.copyWith(color: t.textSecondary, height: 1.5),
            children: [
              const TextSpan(text: 'We sent a 6-digit code to '),
              TextSpan(
                text: _email.text.trim(),
                style: AppTypography.mono(
                  size: 14,
                  weight: FontWeight.w600,
                  color: t.ink,
                ),
              ),
              const TextSpan(text: '. Enter it below to continue.'),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.x24),
        _OtpField(
          controller: _code,
          focusNode: _codeFocus,
          enabled: !_loading,
          length: _kCodeLength,
          onSubmitted: _verifyCode,
        ),
        _ErrorBanner.show(error: _error, topSpacing: AppSpacing.x16),
        const SizedBox(height: AppSpacing.x24),
        AuraButton(
          label: 'Verify code',
          icon: Icons.arrow_forward_rounded,
          loading: _loading,
          onPressed: _loading ? null : _verifyCode,
        ),
        const SizedBox(height: AppSpacing.x12),
        Center(
          child: Pressable(
            scale: 0.99,
            haptic: false,
            onTap: canResend ? () => _sendCode(isResend: true) : null,
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.x12,
                vertical: AppSpacing.x8,
              ),
              child: canResend
                  ? RichText(
                      text: TextSpan(
                        style: textTheme.bodyMedium
                            ?.copyWith(color: t.textSecondary),
                        children: [
                          const TextSpan(text: "Didn't get it? "),
                          TextSpan(
                            text: 'Resend code',
                            style: TextStyle(
                              color: t.ink,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    )
                  : Text(
                      'Resend in ${_formatCooldown(_cooldown)}',
                      style: AppTypography.mono(
                        size: 15,
                        weight: FontWeight.w500,
                        color: t.textMuted,
                      ),
                    ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPasswordStage(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Column(
      key: const ValueKey<_Stage>(_Stage.password),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const _IconBadge(icon: Icons.lock_open_rounded),
        const SizedBox(height: AppSpacing.x20),
        Text('Set a new password', style: textTheme.headlineSmall),
        const SizedBox(height: AppSpacing.x8),
        Text(
          'Use at least $_kMinPasswordLength characters. We recommend a '
          "phrase you don't use elsewhere.",
          style: textTheme.bodyMedium
              ?.copyWith(color: t.textSecondary, height: 1.5),
        ),
        const SizedBox(height: AppSpacing.x24),
        AuraTextField(
          label: 'New password',
          hint: 'At least $_kMinPasswordLength characters',
          controller: _password,
          focusNode: _passwordFocus,
          obscure: _obscurePassword,
          textInputAction: TextInputAction.next,
          prefixIcon: Icons.lock_outline_rounded,
          autofillHints: const [AutofillHints.newPassword],
          enabled: !_loading,
          suffix: _ObscureToggle(
            obscured: _obscurePassword,
            onTap: () =>
                setState(() => _obscurePassword = !_obscurePassword),
          ),
        ),
        const SizedBox(height: AppSpacing.x16),
        AuraTextField(
          label: 'Confirm new password',
          hint: 'Re-type the new password',
          controller: _confirm,
          obscure: _obscureConfirm,
          textInputAction: TextInputAction.done,
          prefixIcon: Icons.lock_outline_rounded,
          autofillHints: const [AutofillHints.newPassword],
          enabled: !_loading,
          onSubmitted: (_) => _resetPassword(),
          suffix: _ObscureToggle(
            obscured: _obscureConfirm,
            onTap: () => setState(() => _obscureConfirm = !_obscureConfirm),
          ),
        ),
        _ErrorBanner.show(error: _error),
        const SizedBox(height: AppSpacing.x20),
        AuraButton(
          label: 'Reset password',
          icon: Icons.lock_open_rounded,
          loading: _loading,
          onPressed: _loading ? null : _resetPassword,
        ),
      ],
    );
  }
}

String _formatCooldown(int seconds) {
  final m = seconds ~/ 60;
  final s = seconds % 60;
  return '$m:${s.toString().padLeft(2, '0')}';
}

// -- stage progress ------------------------------------------------------

/// Three-segment progress strip above the stage IconBadge. The active
/// segment paints `t.accent`; completed segments paint `t.accent` at 50 %
/// opacity; upcoming segments paint a softened `t.border`. Each segment's
/// colour animates 240 ms ease-out on stage advance, honouring reduced
/// motion.
class _StageProgress extends StatelessWidget {
  const _StageProgress({required this.stage, required this.reduceMotion});
  final _Stage stage;
  final bool reduceMotion;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final idx = _Stage.values.indexOf(stage);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x4),
      child: Row(
        children: [
          for (var i = 0; i < _Stage.values.length; i++) ...[
            if (i > 0) const SizedBox(width: AppSpacing.x8),
            Expanded(
              child: _StageSegment(
                status: i < idx
                    ? _SegmentStatus.completed
                    : i == idx
                        ? _SegmentStatus.active
                        : _SegmentStatus.upcoming,
                accent: t.accent,
                border: t.border,
                reduceMotion: reduceMotion,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

enum _SegmentStatus { completed, active, upcoming }

class _StageSegment extends StatelessWidget {
  const _StageSegment({
    required this.status,
    required this.accent,
    required this.border,
    required this.reduceMotion,
  });
  final _SegmentStatus status;
  final Color accent;
  final Color border;
  final bool reduceMotion;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      _SegmentStatus.completed => accent.withOpacity(0.5),
      _SegmentStatus.active => accent,
      _SegmentStatus.upcoming => border.withOpacity(0.6),
    };
    return AnimatedContainer(
      duration:
          reduceMotion ? Duration.zero : const Duration(milliseconds: 240),
      curve: AppMotion.easeOut,
      height: 4,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(2),
      ),
    );
  }
}

// -- sub-widgets ---------------------------------------------------------

class _IconBadge extends StatelessWidget {
  const _IconBadge({required this.icon});
  final IconData icon;
  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: t.accent.withOpacity(0.14),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Icon(icon, size: 24, color: t.accent),
      ),
    );
  }
}

class _ObscureToggle extends StatelessWidget {
  const _ObscureToggle({required this.obscured, required this.onTap});
  final bool obscured;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Pressable(
      scale: 0.94,
      haptic: false,
      onTap: onTap,
      child: SizedBox(
        width: 48,
        height: 48,
        child: Icon(
          obscured
              ? Icons.visibility_outlined
              : Icons.visibility_off_outlined,
          size: 20,
          color: t.textSecondary,
        ),
      ),
    );
  }
}

/// Animated wrapper around the visible error banner: 200 ms fade + 6 dp
/// downward slide on appearance (via [AnimatedSwitcher]). When [error] is
/// null this collapses to nothing, including the prepended top spacer —
/// the caller doesn't need a conditional in the parent column.
class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner._({
    super.key,
    required this.message,
    required this.topSpacing,
  });
  final String message;
  final double topSpacing;

  static Widget show({String? error, double topSpacing = AppSpacing.x12}) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 200),
      switchInCurve: AppMotion.easeOut,
      switchOutCurve: AppMotion.easeOut,
      transitionBuilder: (child, anim) {
        final slide = Tween<Offset>(
          begin: const Offset(0, -0.18),
          end: Offset.zero,
        ).animate(anim);
        return FadeTransition(
          opacity: anim,
          child: SlideTransition(position: slide, child: child),
        );
      },
      child: error == null
          ? const SizedBox(key: ValueKey('no-error'), height: 0)
          : _ErrorBanner._(
              key: ValueKey(error),
              message: error,
              topSpacing: topSpacing,
            ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: EdgeInsets.only(top: topSpacing),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.x12),
        decoration: BoxDecoration(
          color: t.absent.withOpacity(0.12),
          borderRadius: AppRadii.rControl,
          border: Border.all(color: t.absent.withOpacity(0.35)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.error_outline_rounded, size: 18, color: t.absent),
            const SizedBox(width: AppSpacing.x8),
            Expanded(
              child: Text(
                message,
                style: textTheme.bodyMedium?.copyWith(color: t.absent),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Six-cell numeric input. A single hidden TextField captures input
/// (digit-only, length-limited, supports paste + iOS/Android SMS autofill),
/// while six visible cells mirror its content. The hidden field sits on
/// top so tapping any cell focuses the same controller.
class _OtpField extends StatefulWidget {
  const _OtpField({
    required this.controller,
    required this.focusNode,
    required this.length,
    required this.enabled,
    required this.onSubmitted,
  });
  final TextEditingController controller;
  final FocusNode focusNode;
  final int length;
  final bool enabled;
  final VoidCallback onSubmitted;

  @override
  State<_OtpField> createState() => _OtpFieldState();
}

class _OtpFieldState extends State<_OtpField> {
  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onChange);
    widget.focusNode.addListener(_onChange);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onChange);
    widget.focusNode.removeListener(_onChange);
    super.dispose();
  }

  void _onChange() {
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final text = widget.controller.text;
    final hasFocus = widget.focusNode.hasFocus;
    return Stack(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: List.generate(widget.length, (i) {
            final filled = i < text.length;
            final isCurrent = !filled && i == text.length;
            return _OtpCell(
              digit: filled ? text[i] : '',
              filled: filled,
              isCurrent: isCurrent && hasFocus,
            );
          }),
        ),
        Positioned.fill(
          child: Opacity(
            opacity: 0,
            child: TextField(
              controller: widget.controller,
              focusNode: widget.focusNode,
              keyboardType: TextInputType.number,
              textInputAction: TextInputAction.done,
              enabled: widget.enabled,
              showCursor: false,
              autofillHints: const [AutofillHints.oneTimeCode],
              inputFormatters: [
                FilteringTextInputFormatter.digitsOnly,
                LengthLimitingTextInputFormatter(widget.length),
              ],
              onSubmitted: (_) => widget.onSubmitted(),
            ),
          ),
        ),
      ],
    );
  }
}

class _OtpCell extends StatefulWidget {
  const _OtpCell({
    required this.digit,
    required this.filled,
    required this.isCurrent,
  });
  final String digit;
  final bool filled;
  final bool isCurrent;

  @override
  State<_OtpCell> createState() => _OtpCellState();
}

class _OtpCellState extends State<_OtpCell>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pop;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _pop = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 80),
      reverseDuration: const Duration(milliseconds: 140),
    );
    _scale = Tween<double>(begin: 1.0, end: 1.06).animate(
      CurvedAnimation(parent: _pop, curve: AppMotion.easeOut),
    );
  }

  @override
  void didUpdateWidget(_OtpCell oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.filled && !oldWidget.filled) {
      final reduce =
          MediaQuery.maybeOf(context)?.disableAnimations ?? false;
      if (!reduce) {
        _pop.forward().then((_) {
          if (mounted) _pop.reverse();
        });
      }
    }
  }

  @override
  void dispose() {
    _pop.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final borderColor = widget.isCurrent
        ? t.accent
        : widget.filled
            ? t.ink.withOpacity(0.22)
            : t.border;
    final borderWidth = widget.isCurrent ? 1.5 : 1.0;
    return ScaleTransition(
      scale: _scale,
      child: AnimatedContainer(
        duration: AppMotion.press,
        curve: AppMotion.easeOut,
        width: 44,
        height: 56,
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius: AppRadii.rControl,
          border: Border.all(color: borderColor, width: borderWidth),
        ),
        alignment: Alignment.center,
        child: Text(
          widget.digit,
          style: AppTypography.mono(
            size: 22,
            weight: FontWeight.w600,
            color: t.ink,
          ),
        ),
      ),
    );
  }
}
