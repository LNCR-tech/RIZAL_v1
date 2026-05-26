import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../shared/models/profile.dart';
import '../../student/data/profile_repository.dart';
import '../application/schoolit_providers.dart';

class StudentDetailScreen extends ConsumerWidget {
  const StudentDetailScreen({
    super.key,
    required this.user,
    this.departmentName,
    this.programName,
  });
  final UserProfile user;
  final String? departmentName;
  final String? programName;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final sp = user.studentProfile;

    return AppScaffold(
      title: user.displayName,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
        children: [
          Center(
            child: Column(
              children: [
                CircleAvatar(
                  radius: 38,
                  backgroundColor: t.surfaceAlt,
                  child: Text(user.initials,
                      style: textTheme.headlineSmall?.copyWith(color: t.ink)),
                ),
                const SizedBox(height: AppSpacing.x12),
                Text(user.displayName, style: textTheme.headlineSmall),
                if (user.email != null)
                  Text(user.email!,
                      style: textTheme.bodyMedium
                          ?.copyWith(color: t.textSecondary)),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.x24),
          AuraCard(
            child: Column(
              children: [
                _KV('Student no.', sp?.studentNumber ?? '—'),
                const Divider(height: AppSpacing.x24),
                _KV('College', departmentName ?? 'Unassigned'),
                const Divider(height: AppSpacing.x24),
                _KV('Program', programName ?? '—'),
                const Divider(height: AppSpacing.x24),
                _KV('Year level', sp?.yearLevel?.toString() ?? '—'),
                const Divider(height: AppSpacing.x24),
                _KV('Status', sp?.studentStatus ?? '—'),
                const Divider(height: AppSpacing.x24),
                _KV('Face enrolled',
                    (sp?.isFaceRegistered ?? false) ? 'Yes' : 'No'),
              ],
            ),
          ),
          if (sp != null) ...[
            const SizedBox(height: AppSpacing.x16),
            AuraButton(
              label: departmentName == null
                  ? 'Assign to a college'
                  : 'Change college',
              icon: Icons.account_balance_rounded,
              variant: AuraButtonVariant.tonal,
              onPressed: () => showModalBottomSheet<void>(
                context: context,
                isScrollControlled: true,
                backgroundColor: Colors.transparent,
                builder: (_) => _AssignSheet(profileId: sp.id),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _AssignSheet extends ConsumerStatefulWidget {
  const _AssignSheet({required this.profileId});
  final int profileId;

  @override
  ConsumerState<_AssignSheet> createState() => _AssignSheetState();
}

class _AssignSheetState extends ConsumerState<_AssignSheet> {
  int? _dept;
  int? _prog;
  bool _busy = false;
  String? _error;

  Future<void> _save() async {
    if (_dept == null || _prog == null) {
      setState(() => _error = 'Pick a college and a program.');
      return;
    }
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(profileRepositoryProvider).updateStudentProfile(
          widget.profileId, {'department_id': _dept, 'program_id': _prog});
      ref.invalidate(studentsProvider);
      navigator.pop();
      messenger
          .showSnackBar(const SnackBar(content: Text('Student reassigned.')));
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not reassign the student.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final depts = ref.watch(departmentsProvider).valueOrNull ?? [];
    final allProgs = ref.watch(programsProvider).valueOrNull ?? [];
    final progs = _dept == null
        ? allProgs
        : allProgs
            .where((p) =>
                p.departmentIds.isEmpty || p.departmentIds.contains(_dept))
            .toList();
    final progValid = progs.any((p) => p.id == _prog) ? _prog : null;

    return Padding(
      padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.x20),
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius:
              const BorderRadius.vertical(top: Radius.circular(AppRadii.sheet)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                    color: t.border,
                    borderRadius: BorderRadius.circular(2)),
              ),
            ),
            const SizedBox(height: AppSpacing.x16),
            Text('Assign to a college', style: textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.x16),
            DropdownButtonFormField<int>(
              value: _dept,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'College'),
              items: [
                for (final d in depts)
                  DropdownMenuItem(value: d.id, child: Text(d.name)),
              ],
              onChanged: (v) => setState(() {
                _dept = v;
                _prog = null;
              }),
            ),
            const SizedBox(height: AppSpacing.x16),
            DropdownButtonFormField<int>(
              value: progValid,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Program'),
              items: [
                for (final p in progs)
                  DropdownMenuItem(value: p.id, child: Text(p.name)),
              ],
              onChanged: (v) => setState(() => _prog = v),
            ),
            if (_error != null) ...[
              const SizedBox(height: AppSpacing.x12),
              Text(_error!,
                  style: textTheme.bodySmall?.copyWith(color: t.absent)),
            ],
            const SizedBox(height: AppSpacing.x20),
            AuraButton(label: 'Save', loading: _busy, onPressed: _save),
            const SizedBox(height: AppSpacing.x8),
          ],
        ),
      ),
    );
  }
}

class _KV extends StatelessWidget {
  const _KV(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label,
            style: textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
        Flexible(
          child: Text(value,
              textAlign: TextAlign.right, style: textTheme.bodyLarge),
        ),
      ],
    );
  }
}
