import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../data/auth_repository.dart';

/// Modal that submits a password-reset request to the backend
/// (`POST /auth/forgot-password`). The backend always returns the same
/// generic message regardless of whether the email exists — we surface
/// that verbatim. Reset is admin-approval based; the user does not
/// receive a self-serve token.
class ForgotPasswordDialog extends ConsumerStatefulWidget {
  const ForgotPasswordDialog({super.key, this.initialEmail});

  final String? initialEmail;

  static Future<void> show(BuildContext context, {String? initialEmail}) {
    return showDialog<void>(
      context: context,
      barrierDismissible: true,
      builder: (_) => ForgotPasswordDialog(initialEmail: initialEmail),
    );
  }

  @override
  ConsumerState<ForgotPasswordDialog> createState() =>
      _ForgotPasswordDialogState();
}

class _ForgotPasswordDialogState extends ConsumerState<ForgotPasswordDialog> {
  late final TextEditingController _email =
      TextEditingController(text: widget.initialEmail ?? '');
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final email = _email.text.trim();
    if (email.isEmpty) {
      setState(() => _error = 'Enter your school email.');
      return;
    }
    if (!email.contains('@')) {
      setState(() => _error = 'That doesn\'t look like an email address.');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final message =
          await ref.read(authRepositoryProvider).forgotPassword(email);
      if (!mounted) return;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message)),
      );
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = e.message;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = 'Something went wrong. Please try again.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Dialog(
      backgroundColor: t.surface,
      shape: const RoundedRectangleBorder(borderRadius: AppRadii.rCard),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 440),
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.x24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: t.accent.withOpacity(0.14),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(Icons.lock_reset_rounded,
                        color: t.accent, size: 20),
                  ),
                  const SizedBox(width: AppSpacing.x12),
                  Expanded(
                    child: Text('Forgot your password?',
                        style: textTheme.titleLarge),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.x12),
              Text(
                'Enter your school email. Aura will submit a reset request '
                'for your Campus Admin to approve — they\'ll get back to you '
                'with a temporary password.',
                style: textTheme.bodyMedium?.copyWith(
                  color: t.textSecondary,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: AppSpacing.x20),
              AuraTextField(
                label: 'School email',
                hint: 'you@school.edu',
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.done,
                prefixIcon: Icons.mail_outline_rounded,
                onSubmitted: (_) => _submit(),
                autofillHints: const [
                  AutofillHints.username,
                  AutofillHints.email,
                ],
              ),
              if (_error != null) ...[
                const SizedBox(height: AppSpacing.x12),
                Container(
                  padding: const EdgeInsets.all(AppSpacing.x12),
                  decoration: BoxDecoration(
                    color: t.absent.withOpacity(0.12),
                    borderRadius: AppRadii.rControl,
                    border: Border.all(color: t.absent.withOpacity(0.35)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.error_outline_rounded,
                          size: 18, color: t.absent),
                      const SizedBox(width: AppSpacing.x8),
                      Expanded(
                        child: Text(_error!,
                            style: textTheme.bodyMedium
                                ?.copyWith(color: t.absent)),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: AppSpacing.x20),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: _loading
                        ? null
                        : () => Navigator.of(context).pop(),
                    child: const Text('Cancel'),
                  ),
                  const SizedBox(width: AppSpacing.x8),
                  AuraButton(
                    label: 'Send request',
                    loading: _loading,
                    expand: false,
                    onPressed: _loading ? null : _submit,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
