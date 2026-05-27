import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../data/profile_repository.dart';

/// Edit the signed-in user's own account (name only) via PATCH /users/{id}.
/// Email is shown for reference but is intentionally **not editable** —
/// account email changes must go through the user's campus admin so the
/// audit trail stays intact. The field is rendered disabled and the email
/// value is never sent in the PATCH payload.
class EditProfileScreen extends ConsumerStatefulWidget {
  const EditProfileScreen({super.key});

  @override
  ConsumerState<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends ConsumerState<EditProfileScreen> {
  late final TextEditingController _first;
  late final TextEditingController _last;
  late final TextEditingController _email;
  bool _busy = false;
  String? _error;
  String? _ok;

  @override
  void initState() {
    super.initState();
    final meta = ref.read(sessionControllerProvider).meta;
    _first = TextEditingController(text: meta?.firstName ?? '');
    _last = TextEditingController(text: meta?.lastName ?? '');
    _email = TextEditingController(text: meta?.email ?? '');
  }

  @override
  void dispose() {
    _first.dispose();
    _last.dispose();
    _email.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final uid = ref.read(sessionControllerProvider).meta?.userId;
    if (uid == null) {
      setState(() => _error = 'Could not identify your account.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
      _ok = null;
    });
    try {
      await ref.read(profileRepositoryProvider).updateUser(uid, {
        if (_first.text.trim().isNotEmpty) 'first_name': _first.text.trim(),
        if (_last.text.trim().isNotEmpty) 'last_name': _last.text.trim(),
        // Email is intentionally omitted — the field is read-only in the
        // UI and must be changed through the user's campus admin.
      });
      if (mounted) setState(() => _ok = 'Saved — updates apply on next sign-in.');
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not save your profile.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AppScaffold(
      title: 'Edit profile',
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
        children: [
          AuraTextField(label: 'First name', controller: _first),
          const SizedBox(height: AppSpacing.x16),
          AuraTextField(label: 'Last name', controller: _last),
          const SizedBox(height: AppSpacing.x16),
          AuraTextField(
            label: 'Email',
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            enabled: false,
          ),
          const SizedBox(height: AppSpacing.x4),
          Padding(
            padding: const EdgeInsets.only(left: AppSpacing.x4),
            child: Text(
              "Email can't be changed here. Contact your campus admin if "
              "it's wrong.",
              style: textTheme.bodySmall?.copyWith(color: t.textMuted),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.x16),
            Text(_error!, style: textTheme.bodySmall?.copyWith(color: t.absent)),
          ],
          if (_ok != null) ...[
            const SizedBox(height: AppSpacing.x16),
            Text(_ok!, style: textTheme.bodySmall?.copyWith(color: t.present)),
          ],
          const SizedBox(height: AppSpacing.x24),
          AuraButton(label: 'Save', loading: _busy, onPressed: _save),
        ],
      ),
    );
  }
}
