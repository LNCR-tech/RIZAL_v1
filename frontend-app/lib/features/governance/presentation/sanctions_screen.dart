import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/section_header.dart';
import '../../../core/widgets/states.dart';
import '../application/governance_providers.dart';
import 'sanction_event_screen.dart';

class SanctionsScreen extends ConsumerWidget {
  const SanctionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final async = ref.watch(sanctionsDashboardProvider);

    return AppScaffold(
      title: 'Sanctions',
      body: RefreshIndicator(
        color: t.accent,
        backgroundColor: t.surface,
        onRefresh: () => ref.refresh(sanctionsDashboardProvider.future),
        child: async.when(
          loading: () => const Padding(
              padding: EdgeInsets.all(AppSpacing.x20),
              child: LoadingCardList(count: 4)),
          error: (e, _) => ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(AppSpacing.x20),
            children: [
              const SizedBox(height: 24),
              ErrorView(
                message:
                    e is ApiException ? e.message : 'Could not load sanctions.',
                onRetry: () => ref.invalidate(sanctionsDashboardProvider),
              ),
            ],
          ),
          data: (d) => ListView(
            padding: const EdgeInsets.all(AppSpacing.x20),
            children: [
              Row(
                children: [
                  Expanded(child: _Stat('Pending', d.totalPending, t.atRisk)),
                  const SizedBox(width: AppSpacing.x12),
                  Expanded(child: _Stat('Complied', d.totalComplied, t.present)),
                  const SizedBox(width: AppSpacing.x12),
                  Expanded(child: _Stat('Absent', d.totalAbsent, t.absent)),
                ],
              ),
              const SizedBox(height: AppSpacing.x12),
              AuraCard(
                child: Row(
                  children: [
                    Expanded(
                        child: Text('Overall absence rate',
                            style: textTheme.bodyLarge)),
                    Text('${d.overallAbsenceRate.toStringAsFixed(1)}%',
                        style: AppTypography.mono(
                            size: 18, weight: FontWeight.w700, color: t.ink)),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.x24),
              const SectionHeader(title: 'By event'),
              if (d.events.isEmpty)
                const EmptyState(
                  icon: Icons.gavel_rounded,
                  title: 'Nothing to review',
                  message: 'Events with sanctions will appear here.',
                )
              else
                for (final e in d.events)
                  Padding(
                    padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                    child: AuraCard(
                      onTap: () => Navigator.of(context).push(MaterialPageRoute(
                        builder: (_) => SanctionEventScreen(
                            eventId: e.eventId, eventName: e.eventName),
                      )),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    if (e.ownerLevel != null) ...[
                                      _OwnerLevelBadge(level: e.ownerLevel!),
                                      const SizedBox(width: AppSpacing.x8),
                                    ],
                                    Expanded(
                                      child: Text(e.eventName,
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                          style: textTheme.titleLarge),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 2),
                                Text(
                                    '${e.absentCount} absent · ${e.participantCount} participants',
                                    style: textTheme.bodySmall
                                        ?.copyWith(color: t.textSecondary)),
                              ],
                            ),
                          ),
                          if (e.pendingSanctions > 0)
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: AppSpacing.x12, vertical: 4),
                              decoration: BoxDecoration(
                                color: t.atRisk.withOpacity(0.16),
                                borderRadius: BorderRadius.circular(AppRadii.pill),
                              ),
                              child: Text('${e.pendingSanctions} pending',
                                  style: textTheme.labelMedium
                                      ?.copyWith(color: t.atRisk)),
                            ),
                          Icon(Icons.chevron_right_rounded, color: t.textMuted),
                        ],
                      ),
                    ),
                  ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Tiny governance-tier badge surfaced on each event row. Colour comes
/// from the existing brand tokens (`t.ssg` indigo / `t.sg` violet) so the
/// hierarchy is recognisable everywhere it appears.
class _OwnerLevelBadge extends StatelessWidget {
  const _OwnerLevelBadge({required this.level});
  final String level; // 'SSG' | 'SG' | 'ORG'

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final upper = level.toUpperCase();
    final Color color;
    switch (upper) {
      case 'SSG':
        color = t.ssg;
        break;
      case 'SG':
        color = t.sg;
        break;
      case 'ORG':
        color = t.tardy; // amber — distinguishable from SSG/SG without a new token
        break;
      default:
        color = t.textMuted;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.14),
        borderRadius: BorderRadius.circular(AppRadii.pill),
      ),
      child: Text(
        upper,
        style: AppTypography.mono(
          size: 10,
          weight: FontWeight.w800,
          color: color,
        ),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.label, this.value, this.color);
  final String label;
  final int value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return AuraCard(
      padding: const EdgeInsets.all(AppSpacing.x16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$value',
              style: AppTypography.mono(
                  size: 22, weight: FontWeight.w700, color: t.ink)),
          const SizedBox(height: 6),
          Row(
            children: [
              Container(
                  width: 8,
                  height: 8,
                  decoration:
                      BoxDecoration(color: color, shape: BoxShape.circle)),
              const SizedBox(width: 6),
              Flexible(
                child: Text(label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: t.textSecondary)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
