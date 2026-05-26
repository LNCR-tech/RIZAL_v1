import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../data/auth_repository.dart';

/// Change password. Used both as a self-service screen (pushed from Settings)
/// and as the forced gate for accounts flagged `must_change_password` — in the
/// gate case there's nothing to pop, so a successful change signs out for a
/// clean re-login with the new password.
class ChangePasswordScreen extends ConsumerStatefulWidget {
  const ChangePasswordScreen({super.key});

  @override
  ConsumerState<ChangePasswordScreen> createState() =>
      _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends ConsumerState<ChangePasswordScreen> {
  final _current = TextEditingController();
  final _new = TextEditingController();
  final _confirm = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _current.dispose();
    _new.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_current.text.isEmpty || _new.text.isEmpty) {
      setState(() => _error = 'Fill in your current and new password.');
      return;
    }
    if (_new.text.length < 8) {
      setState(() => _error = 'New password must be at least 8 characters.');
      return;
    }
    if (_new.text != _confirm.text) {
      setState(() => _error = 'New passwords do not match.');
      return;
    }
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    final canPop = navigator.canPop();
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(authRepositoryProvider).changePassword(
            currentPassword: _current.text,
            newPassword: _new.text,
          );
      if (!mounted) return;
      if (canPop) {
        navigator.pop();
        messenger.showSnackBar(
            const SnackBar(content: Text('Password updated.')));
      } else {
        messenger.showSnackBar(const SnackBar(
            content: Text('Password updated — please sign in again.')));
        await ref.read(sessionControllerProvider.notifier).logout();
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Could not change your password.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final forced = !Navigator.of(context).canPop();

    return AppScaffold(
      title: 'Change password',
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x16, AppSpacing.x20, 40),
        children: [
          if (forced)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.x16),
              child: Text(
                'Your account must set a new password before continuing.',
                style: textTheme.bodyMedium?.copyWith(color: t.textSecondary),
              ),
            ),
          AuraTextField(
              label: 'Current password', controller: _current, obscure: true),
          const SizedBox(height: AppSpacing.x16),
          AuraTextField(
              label: 'New password', controller: _new, obscure: true),
          const SizedBox(height: AppSpacing.x16),
          AuraTextField(
              label: 'Confirm new password',
              controller: _confirm,
              obscure: true),
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.x16),
            Text(_error!, style: textTheme.bodySmall?.copyWith(color: t.absent)),
          ],
          const SizedBox(height: AppSpacing.x24),
          AuraButton(
              label: 'Update password', loading: _busy, onPressed: _save),
          if (forced) ...[
            const SizedBox(height: AppSpacing.x16),
            AuraButton(
              label: 'Sign out',
              icon: Icons.logout_rounded,
              variant: AuraButtonVariant.ghost,
              onPressed: () =>
                  ref.read(sessionControllerProvider.notifier).logout(),
            ),
          ],
        ],
      ),
    );
  }
}
