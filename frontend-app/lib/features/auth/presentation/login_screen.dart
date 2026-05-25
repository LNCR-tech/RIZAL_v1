import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_logo.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../data/auth_repository.dart';

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

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      backgroundColor: t.bg,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.x24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: AutofillGroup(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const _Brand(),
                    const SizedBox(height: AppSpacing.x32),
                    Text('Welcome back', style: textTheme.displaySmall),
                    const SizedBox(height: 4),
                    Text('Sign in to continue',
                        style: textTheme.bodyLarge
                            ?.copyWith(color: t.textSecondary)),
                    const SizedBox(height: AppSpacing.x32),
                    AuraTextField(
                      label: 'Email',
                      hint: 'you@school.edu',
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.next,
                      prefixIcon: Icons.mail_outline_rounded,
                      autofillHints: const [
                        AutofillHints.username,
                        AutofillHints.email
                      ],
                    ),
                    const SizedBox(height: AppSpacing.x16),
                    AuraTextField(
                      label: 'Password',
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
                    if (_error != null) ...[
                      const SizedBox(height: AppSpacing.x16),
                      _ErrorBanner(_error!),
                    ],
                    const SizedBox(height: AppSpacing.x24),
                    AuraButton(
                      label: 'Sign in',
                      loading: _loading,
                      onPressed: _loading ? null : _submit,
                    ),
                    const SizedBox(height: AppSpacing.x12),
                    AuraButton(
                      label: 'Continue with Google',
                      icon: Icons.g_mobiledata,
                      variant: AuraButtonVariant.ghost,
                      onPressed: _loading
                          ? null
                          : () => ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                    content: Text(
                                        'Google Sign-In wiring lands in Phase 1.')),
                              ),
                    ),
                    const SizedBox(height: AppSpacing.x24),
                    Text(
                      'Forgot your password? Reset it in the web app for now.',
                      textAlign: TextAlign.center,
                      style:
                          textTheme.bodySmall?.copyWith(color: t.textMuted),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Brand extends StatelessWidget {
  const _Brand();

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Row(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: t.navInk,
            borderRadius: BorderRadius.circular(14),
          ),
          child: const Padding(
            padding: EdgeInsets.all(9),
            child: AuraLogo(size: 30),
          ),
        ),
        const SizedBox(width: 12),
        Text('Aura', style: Theme.of(context).textTheme.headlineMedium),
      ],
    );
  }
}

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
