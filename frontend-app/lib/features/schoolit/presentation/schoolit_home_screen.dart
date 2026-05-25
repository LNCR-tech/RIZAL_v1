import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/dashboard.dart';
import '../../../core/widgets/rise_in.dart';
import '../../../core/widgets/school_badge.dart';
import '../../../core/widgets/section_header.dart';
import '../application/schoolit_providers.dart';
import 'campus_governance_screen.dart';
import 'import_students_screen.dart';
import 'school_settings_screen.dart';

/// School IT "Home" — students ring, department/program metrics, a
/// students-by-department chart, and management actions.
class SchoolItHomeScreen extends ConsumerWidget {
  const SchoolItHomeScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x20, AppSpacing.x20, 130);

  String _short(String s) => s.length > 8 ? '${s.substring(0, 8)}…' : s;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final meta = ref.watch(sessionControllerProvider).meta;
    final students = ref.watch(studentsProvider).valueOrNull;
    final depts = ref.watch(departmentsProvider).valueOrNull;
    final progs = ref.watch(programsProvider).valueOrNull;

    final total = students?.length;
    final enrolled = students
        ?.where((u) => u.studentProfile?.isFaceRegistered ?? false)
        .length;
    final pct = (total != null && total > 0 && enrolled != null)
        ? enrolled / total * 100
        : null;

    final deptName = {for (final d in depts ?? []) d.id: d.name};
    final counts = <int, int>{};
    for (final u in students ?? []) {
      final did = u.studentProfile?.departmentId;
      if (did != null) counts[did] = (counts[did] ?? 0) + 1;
    }
    final top = counts.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    final topN = top.take(5).toList();
    final chartLabels = [
      for (final e in topN) _short(deptName[e.key] ?? '#${e.key}')
    ];
    final chartValues = [for (final e in topN) e.value];

    return RefreshIndicator(
      color: t.accent,
      backgroundColor: t.surface,
      onRefresh: () async {
        ref.invalidate(studentsProvider);
        ref.invalidate(departmentsProvider);
        ref.invalidate(programsProvider);
        await ref.read(studentsProvider.future);
      },
      child: ListView(
        padding: _pad,
        physics: const AlwaysScrollableScrollPhysics(),
        children: staggered([
          Row(
            children: [
              SchoolBadge(
                logoUrl: meta?.logoUrl,
                schoolName: meta?.schoolName,
                primaryHex: meta?.primaryColor,
                secondaryHex: meta?.secondaryColor,
                size: 52,
              ),
              const SizedBox(width: AppSpacing.x16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Workspace', style: textTheme.displaySmall),
                    Text(meta?.schoolName ?? 'Campus administration',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: textTheme.bodyLarge
                            ?.copyWith(color: t.textSecondary)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.x20),
          HeroRingCard(
            title: 'Students',
            value: total?.toString() ?? '—',
            footnote: enrolled != null ? '$enrolled face-enrolled' : 'loading…',
            percent: pct,
            icon: Icons.school_rounded,
          ),
          const SizedBox(height: AppSpacing.x12),
          Row(
            children: [
              Expanded(
                child: MetricChipCard(
                  icon: Icons.account_tree_rounded,
                  label: 'Departments',
                  value: depts?.length.toString() ?? '—',
                  tint: t.ssg,
                ),
              ),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: MetricChipCard(
                  icon: Icons.menu_book_rounded,
                  label: 'Programs',
                  value: progs?.length.toString() ?? '—',
                  tint: t.sg,
                ),
              ),
            ],
          ),
          if (chartLabels.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x24),
            const SectionHeader(title: 'Students by department'),
            AuraCard(
              child: DashboardBarChart(
                labels: chartLabels,
                values: chartValues,
                colors: [t.accentDark],
              ),
            ),
          ],
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Manage'),
          DashboardActionRow(
            icon: Icons.upload_file_rounded,
            label: 'Bulk import students',
            subtitle: 'Upload a CSV or XLSX',
            onTap: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => const ImportStudentsScreen())),
          ),
          const SizedBox(height: AppSpacing.x12),
          DashboardActionRow(
            icon: Icons.account_balance_rounded,
            label: 'Student Government',
            subtitle: 'SSG officers & permissions',
            onTap: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => const CampusGovernanceScreen())),
          ),
          const SizedBox(height: AppSpacing.x12),
          DashboardActionRow(
            icon: Icons.settings_rounded,
            label: 'School settings',
            subtitle: 'Branding & event policy',
            tint: t.textSecondary,
            onTap: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => const SchoolSettingsScreen())),
          ),
        ]),
      ),
    );
  }
}
