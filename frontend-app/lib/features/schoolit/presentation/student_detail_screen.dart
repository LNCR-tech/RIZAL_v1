import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../shared/models/profile.dart';
import 'edit_student_screen.dart';

/// Read-only student profile card for campus admins. The pencil action in
/// the app bar pushes [EditStudentScreen] for the full edit surface
/// (identity + academics + status). Field-by-field edits are no longer
/// reachable here; the previous in-line "Change college" bottom sheet
/// folded into the dedicated edit screen.
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
      actions: [
        if (sp != null)
          IconButton(
            tooltip: 'Edit student',
            icon: const Icon(Icons.edit_rounded),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => EditStudentScreen(user: user),
              ),
            ),
          ),
      ],
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
        ],
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
