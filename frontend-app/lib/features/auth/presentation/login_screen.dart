import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_motion.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_brand_mark.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../../../core/widgets/pressable.dart';
import '../../../core/widgets/rise_in.dart';
import '../../help/data/help_content.dart';
import '../../help/presentation/help_center_screen.dart';
import '../data/auth_repository.dart';
import '../data/google_sign_in_service.dart';
import 'forgot_password_screen.dart';

/// Public marketing / overview site for Aura. Linked from the login
/// footer so prospective users can read about the platform before
/// signing in — they don't need an account just to find out what the
/// app does.
const String _kAuraSiteUrl = 'https://aura-test.coeofjrmsu.com/';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _obscure = true;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  /// Opens the public Aura site in the user's default browser. Falls
  /// back to a snackbar if no browser is available (e.g. a stripped-
  /// down Android build that has no default handler) — never silently
  /// swallow the failure.
  Future<void> _openAuraSite() async {
    final uri = Uri.parse(_kAuraSiteUrl);
    final messenger = ScaffoldMessenger.of(context);
    try {
      final ok = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!ok && mounted) {
        messenger.showSnackBar(
          const SnackBar(content: Text("Couldn't open the link.")),
        );
      }
    } catch (_) {
      if (!mounted) return;
      messenger.showSnackBar(
        const SnackBar(content: Text("Couldn't open the link.")),
      );
    }
  }

  Future<void> _submit() async {
    final email = _email.text.trim();
    final password = _password.text;
    if (email.isEmpty || password.isEmpty) {
      setState(() => _error = 'Enter your email and password.');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await ref
          .read(authRepositoryProvider)
          .login(email: email, password: password);
      await ref.read(sessionControllerProvider.notifier).completeLogin(
            accessToken: result.accessToken,
            meta: result.meta,
          );
      // The router's redirect reacts to the session change and navigates.
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Unexpected error. Please try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _continueWithGoogle() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final token = await ref.read(googleSignInServiceProvider).signIn();
      if (token == null) {
        if (mounted) setState(() => _loading = false);
        return;
      }
      final result = await ref
          .read(authRepositoryProvider)
          .loginWithGoogle(token: token);
      await ref.read(sessionControllerProvider.notifier).completeLogin(
            accessToken: result.accessToken,
            meta: result.meta,
          );
    } on GoogleSignInError catch (e) {
      if (mounted) setState(() => _error = e.message);
    } on ApiException catch (e) {
      String message = e.message;
      if (e.statusCode == 403) {
        message = 'Google sign-in is disabled for this deployment. '
            'Use your school email and password instead.';
      } else if (e.statusCode == 404) {
        message = 'No Aura account is linked to that Google email. '
            'Ask your Campus Admin to register your school email first.';
      } else if (e.statusCode == 401) {
        message = 'Google could not verify your account. '
            'Make sure your Google email is verified and try again.';
      }
      if (mounted) setState(() => _error = message);
    } catch (_) {
      if (mounted) {
        setState(() => _error =
            'Unexpected error while signing in with Google. Please try again.');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _openForgot() {
    if (_loading) return;
    ForgotPasswordScreen.push(
      context,
      initialEmail: _email.text.trim().isEmpty ? null : _email.text.trim(),
    );
  }

  void _openHelp() {
    if (_loading) return;
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) =>
            const HelpCenterScreen(audience: HelpAudience.public),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    return Scaffold(
      backgroundColor: t.bg,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.x24, vertical: AppSpacing.x32),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: AutofillGroup(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  mainAxisSize: MainAxisSize.min,
                  children: staggered([
                    // ── Brand hero (centered, soft halo) ──
                    const _BrandHero(),
                    const SizedBox(height: AppSpacing.x32),

                    // ── Headings ──
                    Text(
                      'Welcome back',
                      textAlign: TextAlign.center,
                      style: textTheme.displaySmall,
                    ),
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        'Sign in to continue',
                        textAlign: TextAlign.center,
                        style: textTheme.bodyLarge
                            ?.copyWith(color: t.textSecondary),
                      ),
                    ),
                    const SizedBox(height: AppSpacing.x32),

                    // ── Email ──
                    AuraTextField(
                      label: 'Email',
                      hint: 'you@school.edu',
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.next,
                      prefixIcon: Icons.mail_outline_rounded,
                      autofillHints: const [
                        AutofillHints.username,
                        AutofillHints.email,
                      ],
                    ),
                    const SizedBox(height: AppSpacing.x16),

                    // ── Password + inline "Forgot?" header ──
                    _PasswordLabelRow(
                      onForgot: _openForgot,
                      disabled: _loading,
                    ),
                    AuraTextField(
                      // label rendered above already; null here so AuraTextField
                      // doesn't draw a second one.
                      label: null,
                      hint: '••••••••',
                      controller: _password,
                      obscure: _obscure,
                      textInputAction: TextInputAction.done,
                      onSubmitted: (_) => _submit(),
                      prefixIcon: Icons.lock_outline_rounded,
                      autofillHints: const [AutofillHints.password],
                      suffix: Semantics(
                        container: true,
                        label: _obscure ? 'Show password' : 'Hide password',
                        button: true,
                        child: IconButton(
                          tooltip:
                              _obscure ? 'Show password' : 'Hide password',
                          icon: Icon(_obscure
                              ? Icons.visibility_off_rounded
                              : Icons.visibility_rounded),
                          onPressed: () => setState(() => _obscure = !_obscure),
                        ),
                      ),
                    ),

                    // ── Animated error banner ──
                    AnimatedSwitcher(
                      duration: reduce
                          ? Duration.zero
                          : const Duration(milliseconds: 220),
                      reverseDuration:
                          reduce ? Duration.zero : AppMotion.exit,
                      switchInCurve: AppMotion.easeOut,
                      switchOutCurve: AppMotion.easeOut,
                      transitionBuilder: (child, anim) {
                        // Slide-from-top + fade. Start at -8dp so the banner
                        // never animates from a place that looked empty.
                        return FadeTransition(
                          opacity: anim,
                          child: SlideTransition(
                            position: Tween<Offset>(
                              begin: const Offset(0, -0.10),
                              end: Offset.zero,
                            ).animate(anim),
                            child: child,
                          ),
                        );
                      },
                      child: _error == null
                          ? const SizedBox.shrink(key: ValueKey('no-error'))
                          : Padding(
                              key: ValueKey(_error),
                              padding: const EdgeInsets.only(
                                  top: AppSpacing.x16),
                              child: _ErrorBanner(_error!),
                            ),
                    ),
                    const SizedBox(height: AppSpacing.x24),

                    // ── Primary CTA ──
                    AuraButton(
                      label: 'Sign in',
                      loading: _loading,
                      onPressed: _loading ? null : _submit,
                    ),
                    const SizedBox(height: AppSpacing.x16),

                    // ── "or" divider ──
                    const _OrDivider(),
                    const SizedBox(height: AppSpacing.x16),

                    // ── Google CTA ──
                    AuraButton(
                      label: 'Continue with Google',
                      icon: Icons.g_mobiledata,
                      variant: AuraButtonVariant.ghost,
                      onPressed: _loading ? null : _continueWithGoogle,
                    ),
                    const SizedBox(height: AppSpacing.x24),

                    // ── Compact footer ──
                    _Footer(
                      onHelp: _openHelp,
                      onAuraSite: _openAuraSite,
                      disabled: _loading,
                    ),
                  ]),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ─── Brand hero ──────────────────────────────────────────────────────
/// Centered Aura mark sitting inside a soft accent halo, with the
/// wordmark below. The mark gets a tiny "settle" on first paint
/// (TweenAnimationBuilder scale 0.94 → 1.0 over 360ms ease-out) — never
/// scale(0) (emil); never ease-in. The halo is a pure radial gradient,
/// no shaders, performs everywhere.
class _BrandHero extends StatelessWidget {
  const _BrandHero();

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    return Column(
      children: [
        SizedBox(
          width: 200,
          height: 200,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Halo — soft accent radial.
              DecoratedBox(
                decoration: BoxDecoration(
                  gradient: RadialGradient(
                    colors: [
                      t.accent.withOpacity(t.isDark ? 0.18 : 0.14),
                      t.accent.withOpacity(0.0),
                    ],
                    stops: const [0.0, 0.85],
                    radius: 0.5,
                  ),
                ),
                child: const SizedBox.expand(),
              ),
              // Brand mark, with a one-shot settle.
              TweenAnimationBuilder<double>(
                tween: Tween<double>(begin: reduce ? 1 : 0.94, end: 1),
                duration: reduce
                    ? Duration.zero
                    : const Duration(milliseconds: 360),
                curve: AppMotion.easeOut,
                builder: (context, v, child) => Transform.scale(
                  scale: v,
                  child: Opacity(opacity: reduce ? 1 : v, child: child),
                ),
                child: const AppBrandMark(size: 88),
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.x4),
        AppNameText(
          style: textTheme.headlineMedium?.copyWith(
            letterSpacing: 0.5,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}

// ─── Password row label with inline "Forgot?" ────────────────────────
class _PasswordLabelRow extends StatelessWidget {
  const _PasswordLabelRow({
    required this.onForgot,
    required this.disabled,
  });
  final VoidCallback onForgot;
  final bool disabled;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 6, left: 4, right: 4),
      child: Row(
        children: [
          Text(
            'Password',
            style:
                textTheme.labelMedium?.copyWith(color: t.textSecondary),
          ),
          const Spacer(),
          Pressable(
            scale: 0.97,
            haptic: false,
            onTap: disabled ? null : onForgot,
            child: Text(
              'Forgot?',
              style: textTheme.labelMedium?.copyWith(
                color: disabled ? t.textMuted : t.accentDark,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── "or" divider ────────────────────────────────────────────────────
class _OrDivider extends StatelessWidget {
  const _OrDivider();

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Row(
      children: [
        Expanded(child: Divider(height: 1, color: t.border)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x12),
          child: Text(
            'or',
            style: textTheme.labelMedium?.copyWith(
              color: t.textMuted,
              letterSpacing: 1.6,
            ),
          ),
        ),
        Expanded(child: Divider(height: 1, color: t.border)),
      ],
    );
  }
}

// ─── Compact footer ──────────────────────────────────────────────────
/// Two muted links joined by a middle-dot, centered. Far less visually
/// loud than the previous 3-item Wrap which read as a row of spam.
class _Footer extends StatelessWidget {
  const _Footer({
    required this.onHelp,
    required this.onAuraSite,
    required this.disabled,
  });
  final VoidCallback onHelp;
  final VoidCallback onAuraSite;
  final bool disabled;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final style = textTheme.bodySmall?.copyWith(
      color: disabled ? t.textMuted : t.textSecondary,
      fontWeight: FontWeight.w600,
    );

    return FittedBox(
      fit: BoxFit.scaleDown,
      child: Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Pressable(
          scale: 0.98,
          haptic: false,
          onTap: disabled ? null : onHelp,
          child: Padding(
            padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.x8, vertical: AppSpacing.x8),
            child: Text('Need help', style: style),
          ),
        ),
        Text('·', style: style),
        Pressable(
          scale: 0.98,
          haptic: false,
          onTap: disabled ? null : onAuraSite,
          child: Padding(
            padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.x8, vertical: AppSpacing.x8),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Learn about Aura', style: style),
                const SizedBox(width: 4),
                Icon(
                  Icons.open_in_new_rounded,
                  size: 12,
                  color: disabled ? t.textMuted : t.textSecondary,
                ),
              ],
            ),
          ),
        ),
      ],
    ),
    );
  }
}

// ─── Error banner (visual unchanged; animation lives in parent) ──────
class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner(this.message);
  final String message;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Container(
      padding: const EdgeInsets.all(AppSpacing.x12),
      decoration: BoxDecoration(
        color: t.absent.withOpacity(0.12),
        borderRadius: AppRadii.rControl,
        border: Border.all(color: t.absent.withOpacity(0.35)),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline_rounded, size: 18, color: t.absent),
          const SizedBox(width: AppSpacing.x8),
          Expanded(
            child: Text(message,
                style: Theme.of(context)
                    .textTheme
                    .bodyMedium
                    ?.copyWith(color: t.absent)),
          ),
        ],
      ),
    );
  }
}
