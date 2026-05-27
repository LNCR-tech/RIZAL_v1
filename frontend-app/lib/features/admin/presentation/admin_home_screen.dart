import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/pressable.dart';
import '../../../core/widgets/rise_in.dart';
import '../../../core/widgets/section_header.dart';
import '../../../core/widgets/stat_ring.dart';
import '../../../shared/models/admin.dart';
import '../application/admin_providers.dart';
import 'create_school_screen.dart';

/// Platform Admin "Overview" — a chart-led dashboard: active-schools hero
/// ring, a Campus-admins metric, and a subscription breakdown chart.
class AdminHomeScreen extends ConsumerWidget {
  const AdminHomeScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x20, AppSpacing.x20, 130);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final meta = ref.watch(sessionControllerProvider).meta;
    final schools = ref.watch(adminSchoolsProvider).valueOrNull;
    final accounts = ref.watch(adminAccountsProvider).valueOrNull;

    final list = schools ?? const <SchoolSummary>[];
    final total = list.length;
    final active = list.where((s) => s.activeStatus).length;
    final subs = <String, int>{'active': 0, 'trial': 0, 'suspended': 0};
    for (final s in list) {
      final k = (s.subscriptionStatus ?? 'trial').toLowerCase();
      if (subs.containsKey(k)) subs[k] = subs[k]! + 1;
    }

    return RefreshIndicator(
      color: t.accent,
      backgroundColor: t.surface,
      onRefresh: () async {
        ref.invalidate(adminSchoolsProvider);
        ref.invalidate(adminAccountsProvider);
        await ref.read(adminSchoolsProvider.future);
      },
      child: ListView(
        padding: _pad,
        physics: const AlwaysScrollableScrollPhysics(),
        children: staggered([
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Overview', style: textTheme.displaySmall),
                    Text('Welcome back, ${meta?.firstName ?? 'Admin'}',
                        style: textTheme.bodyLarge
                            ?.copyWith(color: t.textSecondary)),
                  ],
                ),
              ),
              CircleAvatar(
                radius: 24,
                backgroundColor: t.accent,
                child: Text(meta?.initials ?? 'A',
                    style: textTheme.titleLarge?.copyWith(color: t.onAccent)),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.x20),
          _HeroCard(total: total, active: active, ready: schools != null),
          const SizedBox(height: AppSpacing.x12),
          _MetricCard(
            icon: Icons.admin_panel_settings_rounded,
            label: 'Campus admins',
            value: accounts?.length.toString() ?? '—',
            tint: t.ssg,
          ),
          const SizedBox(height: AppSpacing.x12),
          _SubsChart(counts: subs, ready: schools != null),
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Manage'),
          _ActionRow(
            icon: Icons.add_business_rounded,
            label: 'Create school',
            subtitle: 'Onboard a school + its campus admin',
            onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const CreateSchoolScreen())),
          ),
        ]),
      ),
    );
  }
}

class _HeroCard extends StatelessWidget {
  const _HeroCard(
      {required this.total, required this.active, required this.ready});
  final int total;
  final int active;
  final bool ready;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final pct = total > 0 ? (active / total) * 100 : 0.0;

    return AuraCard(
      color: t.accent.withOpacity(0.14),
      padding: const EdgeInsets.all(AppSpacing.x20),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Active schools',
                    style: textTheme.labelLarge?.copyWith(color: t.textSecondary)),
                const SizedBox(height: AppSpacing.x8),
                Text(ready ? '$active' : '—',
                    style: AppTypography.mono(
                        size: 40, weight: FontWeight.w800, color: t.ink)),
                Text(ready ? 'of $total total' : 'loading…',
                    style: textTheme.bodyMedium
                        ?.copyWith(color: t.textSecondary)),
              ],
            ),
          ),
          StatRing(percent: pct, size: 92, stroke: 11, color: t.accentDark),
        ],
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.tint,
  });
  final IconData icon;
  final String label;
  final String value;
  final Color tint;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AuraCard(
      padding: const EdgeInsets.all(AppSpacing.x16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
                color: tint.withOpacity(0.16),
                borderRadius: BorderRadius.circular(AppRadii.control)),
            child: Icon(icon, color: tint, size: 22),
          ),
          const SizedBox(height: AppSpacing.x16),
          Text(value,
              style: AppTypography.mono(
                  size: 28, weight: FontWeight.w700, color: t.ink)),
          const SizedBox(height: 2),
          Text(label,
              style: textTheme.bodySmall?.copyWith(color: t.textSecondary)),
        ],
      ),
    );
  }
}

class _SubsChart extends StatelessWidget {
  const _SubsChart({required this.counts, required this.ready});
  final Map<String, int> counts;
  final bool ready;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    const labels = ['Active', 'Trial', 'Susp.'];
    const keys = ['active', 'trial', 'suspended'];
    final colors = [t.present, t.tardy, t.absent];
    final values = [for (final k in keys) counts[k] ?? 0];
    final maxV = values.fold<int>(0, (p, c) => c > p ? c : p);
    final maxY = (maxV < 1 ? 1 : maxV) * 1.3;

    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Subscriptions', style: textTheme.titleLarge),
          Text('Schools by plan status',
              style: textTheme.bodySmall?.copyWith(color: t.textSecondary)),
          const SizedBox(height: AppSpacing.x16),
          SizedBox(
            height: 150,
            child: !ready
                ? Center(
                    child: Text('—',
                        style: textTheme.bodySmall
                            ?.copyWith(color: t.textMuted)))
                : BarChart(
                    BarChartData(
                      alignment: BarChartAlignment.spaceAround,
                      maxY: maxY,
                      minY: 0,
                      barTouchData: BarTouchData(enabled: false),
                      gridData: const FlGridData(show: false),
                      borderData: FlBorderData(show: false),
                      titlesData: FlTitlesData(
                        leftTitles: const AxisTitles(
                            sideTitles: SideTitles(showTitles: false)),
                        rightTitles: const AxisTitles(
                            sideTitles: SideTitles(showTitles: false)),
                        topTitles: const AxisTitles(
                            sideTitles: SideTitles(showTitles: false)),
                        bottomTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 44,
                            getTitlesWidget: (value, m) {
                              final i = value.toInt();
                              if (i < 0 || i >= labels.length) {
                                return const SizedBox.shrink();
                              }
                              return Padding(
                                padding: const EdgeInsets.only(top: 6),
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Text('${values[i]}',
                                        style: AppTypography.mono(
                                            size: 14,
                                            weight: FontWeight.w700,
                                            color: t.ink)),
                                    Text(labels[i],
                                        style: textTheme.bodySmall
                                            ?.copyWith(color: t.textMuted)),
                                  ],
                                ),
                              );
                            },
                          ),
                        ),
                      ),
                      barGroups: [
                        for (var i = 0; i < labels.length; i++)
                          BarChartGroupData(x: i, barRods: [
                            BarChartRodData(
                              toY: values[i].toDouble(),
                              color: colors[i],
                              width: 30,
                              borderRadius: const BorderRadius.vertical(
                                  top: Radius.circular(8)),
                              backDrawRodData: BackgroundBarChartRodData(
                                show: true,
                                toY: maxY,
                                color: t.surfaceAlt,
                              ),
                            ),
                          ]),
                      ],
                    ),
                    swapAnimationDuration:
                        reduce ? Duration.zero : const Duration(milliseconds: 450),
                  ),
          ),
        ],
      ),
    );
  }
}

class _ActionRow extends StatelessWidget {
  const _ActionRow({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.onTap,
  });
  final IconData icon;
  final String label;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Pressable(
      onTap: onTap,
      child: AuraCard(
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                  color: t.accent.withOpacity(0.16),
                  borderRadius: BorderRadius.circular(AppRadii.control)),
              child: Icon(icon, color: t.accentDark),
            ),
            const SizedBox(width: AppSpacing.x16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: textTheme.titleLarge),
                  Text(subtitle,
                      style: textTheme.bodySmall
                          ?.copyWith(color: t.textSecondary)),
                ],
              ),
            ),
            Icon(Icons.chevron_right_rounded, color: t.textMuted),
          ],
        ),
      ),
    );
  }
}
