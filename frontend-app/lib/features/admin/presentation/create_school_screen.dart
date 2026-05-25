import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../../../core/widgets/section_header.dart';
import '../../../shared/models/admin.dart';
import '../application/admin_providers.dart';
import '../data/admin_repository.dart';

class CreateSchoolScreen extends ConsumerStatefulWidget {
  const CreateSchoolScreen({super.key});

  @override
  ConsumerState<CreateSchoolScreen> createState() => _CreateSchoolScreenState();
}

class _CreateSchoolScreenState extends ConsumerState<CreateSchoolScreen> {
  final _schoolName = TextEditingController();
  final _schoolCode = TextEditingController();
  final _email = TextEditingController();
  final _first = TextEditingController();
  final _last = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    for (final c in [_schoolName, _schoolCode, _email, _first, _last, _password]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    if (_schoolName.text.trim().isEmpty ||
        _email.text.trim().isEmpty ||
        _first.text.trim().isEmpty ||
        _last.text.trim().isEmpty) {
      setState(() => _error = 'School name and the admin name + email are required.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final res = await ref.read(adminRepositoryProvider).createSchool(
            schoolName: _schoolName.text.trim(),
            primaryColor: '#162F65',
            schoolCode: _schoolCode.text.trim(),
            itEmail: _email.text.trim(),
            itFirstName: _first.text.trim(),
            itLastName: _last.text.trim(),
            itPassword: _password.text,
          );
      ref.invalidate(adminSchoolsProvider);
      ref.invalidate(adminAccountsProvider);
      if (mounted) {
        await _showResult(res);
        if (mounted) Navigator.of(context).pop();
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not create the school.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _showResult(CreateSchoolResult res) {
    return showDialog<void>(
      context: context,
      builder: (context) {
        final t = AppTokens.of(context);
        return AlertDialog(
          title: const Text('School created'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${res.school.schoolName ?? 'School'} is ready.'),
              if (res.schoolItEmail != null) ...[
                const SizedBox(height: AppSpacing.x8),
                Text('Campus admin: ${res.schoolItEmail}'),
              ],
              if (res.generatedTemporaryPassword != null) ...[
                const SizedBox(height: AppSpacing.x12),
                Text('Temporary password',
                    style:
                        Theme.of(context).textTheme.labelMedium?.copyWith(color: t.textSecondary)),
                const SizedBox(height: 4),
                SelectableText(res.generatedTemporaryPassword!,
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 4),
                Text('Share this securely — it is shown only once.',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(color: t.textMuted)),
              ],
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Done')),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AppScaffold(
      title: 'New school',
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
        children: [
          AuraTextField(label: 'School name', controller: _schoolName),
          const SizedBox(height: AppSpacing.x16),
          AuraTextField(
              label: 'School code', controller: _schoolCode, hint: 'Optional'),
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Campus admin account'),
          AuraTextField(
              label: 'Email',
              controller: _email,
              keyboardType: TextInputType.emailAddress),
          const SizedBox(height: AppSpacing.x16),
          Row(
            children: [
              Expanded(
                  child:
                      AuraTextField(label: 'First name', controller: _first)),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                  child: AuraTextField(label: 'Last name', controller: _last)),
            ],
          ),
          const SizedBox(height: AppSpacing.x16),
          AuraTextField(
              label: 'Temporary password',
              controller: _password,
              hint: 'Optional — auto-generated if blank'),
          AuraCard(
            color: t.surfaceAlt,
            child: Text(
              'A campus-admin (School IT) account is created and linked to the new school.',
              style: textTheme.bodySmall?.copyWith(color: t.textSecondary),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.x16),
            Text(_error!,
                style: textTheme.bodySmall?.copyWith(color: t.absent)),
          ],
          const SizedBox(height: AppSpacing.x24),
          AuraButton(label: 'Create school', loading: _busy, onPressed: _save),
        ],
      ),
    );
  }
}
