import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/event_location_map.dart';
import '../../../core/widgets/section_header.dart';
import '../../../core/widgets/stat_ring.dart';
import '../../../core/widgets/states.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../shared/models/event.dart';
import '../../../shared/models/governance.dart';
import '../../../shared/utils/formatting.dart';
import '../../schoolit/presentation/event_editor_screen.dart';
import '../application/governance_providers.dart';

/// Live attendance monitor for a governance event: stats + attendee list.
class GovernanceEventMonitorScreen extends ConsumerWidget {
  const GovernanceEventMonitorScreen({super.key, required this.event});
  final AppEvent event;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final unit = ref.watch(effectiveUnitProvider);
    final statsAsync = ref.watch(eventStatsProvider(event.id));
    final attendeesAsync = ref.watch(eventAttendeesProvider(event.id));

    return AppScaffold(
      title: event.name,
      actions: (unit != null && unit.can('manage_events'))
          ? [
              IconButton(
                tooltip: 'Edit event',
                icon: const Icon(Icons.edit_rounded),
                onPressed: () async {
                  final changed = await Navigator.of(context).push<bool>(
                    MaterialPageRoute(
                      builder: (_) => EventEditorScreen(
                          event: event, governanceContext: unit.type),
                    ),
                  );
                  // The event object here is now stale — return to the
                  // (refreshed) list so the change is visible.
                  if (changed == true && context.mounted) {
                    ref.invalidate(governanceEventsProvider(unit.type));
                    Navigator.of(context).pop();
                  }
                },
              ),
            ]
          : null,
      body: RefreshIndicator(
        color: t.accent,
        backgroundColor: t.surface,
        onRefresh: () => Future.wait([
          ref.refresh(eventStatsProvider(event.id).future),
          ref.refresh(eventAttendeesProvider(event.id).future),
        ]),
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.x20),
          children: [
            statsAsync.when(
              loading: () => const AuraCard(
                  child: SizedBox(
                      height: 120,
                      child: Center(child: CircularProgressIndicator()))),
              error: (e, _) => AuraCard(
                child: Text(
                    e is ApiException ? e.message : 'Stats unavailable',
                    style: TextStyle(color: t.textSecondary)),
              ),
              data: (s) => _StatsCard(stats: s),
            ),
            const SizedBox(height: AppSpacing.x24),
            if (event.hasGeo) ...[
              const SectionHeader(title: 'Location'),
              const SizedBox(height: AppSpacing.x12),
              EventLocationMap(
                lat: event.geoLatitude!,
                lng: event.geoLongitude!,
                radiusM: event.geoRadiusM ?? 100,
              ),
              const SizedBox(height: AppSpacing.x24),
            ],
            const SectionHeader(title: 'Attendees'),
            attendeesAsync.when(
              loading: () => const LoadingCardList(count: 5),
              error: (e, _) => ErrorView(
                message:
                    e is ApiException ? e.message : 'Could not load attendees.',
                onRetry: () => ref.invalidate(eventAttendeesProvider(event.id)),
              ),
              data: (list) {
                if (list.isEmpty) {
                  return const Padding(
                    padding: EdgeInsets.only(top: 24),
                    child: EmptyState(
                      icon: Icons.how_to_reg_outlined,
                      title: 'No check-ins yet',
                      message: 'Attendees appear here as they check in.',
                    ),
                  );
                }
                return Column(
                  children: [
                    for (final a in list)
                      Padding(
                        key: ValueKey(a.id),
                        padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                        child: AuraCard(
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Student #${a.studentId ?? '—'}',
                                        style:
                                            Theme.of(context).textTheme.titleLarge),
                                    if (a.timeIn != null)
                                      Text('In: ${fmtTime(a.timeIn)}',
                                          style: Theme.of(context)
                                              .textTheme
                                              .bodySmall
                                              ?.copyWith(
                                                  color: t.textSecondary)),
                                  ],
                                ),
                              ),
                              StatusChip.forStatus(context, a.effectiveStatus),
                            ],
                          ),
                        ),
                      ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _StatsCard extends StatelessWidget {
  const _StatsCard({required this.stats});
  final EventStats stats;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final present = stats.countOf('present');
    final rate = stats.total > 0 ? (present / stats.total) * 100 : 0.0;

    return AuraCard(
      child: Row(
        children: [
          StatRing(percent: rate, size: 96, label: 'Present'),
          const SizedBox(width: AppSpacing.x20),
          Expanded(
            child: Wrap(
              spacing: AppSpacing.x8,
              runSpacing: AppSpacing.x8,
              children: [
                _CountChip('Present', stats.countOf('present'), t.present),
                _CountChip('Late', stats.countOf('late'), t.tardy),
                _CountChip('Absent', stats.countOf('absent'), t.absent),
                _CountChip('Excused', stats.countOf('excused'), t.excused),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CountChip extends StatelessWidget {
  const _CountChip(this.label, this.count, this.color);
  final String label;
  final int count;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x12, vertical: AppSpacing.x8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.14),
        borderRadius: BorderRadius.circular(AppRadii.control),
      ),
      child: Text('$count $label',
          style: textTheme.labelMedium?.copyWith(color: color)),
    );
  }
}
