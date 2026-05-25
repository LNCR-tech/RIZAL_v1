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
import '../../../core/widgets/states.dart';
import '../../attendance/presentation/attendance_screen.dart';
import '../../events/application/events_providers.dart';
import '../../events/application/geofence_background.dart';
import '../../events/presentation/event_detail_screen.dart';
import '../../events/presentation/widgets/event_card.dart';
import '../../events/presentation/widgets/nearby_event_banner.dart';
import '../application/student_providers.dart';

/// Student "Home" — attendance ring, present/absence metrics, a monthly trend
/// chart, and the next upcoming event.
class StudentHomeScreen extends ConsumerWidget {
  const StudentHomeScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x20, AppSpacing.x20, 130);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final meta = ref.watch(sessionControllerProvider).meta;
    final name = meta?.firstName ?? 'there';

    // A tapped check-in notification (foreground or cold start) routes here —
    // open the attendance screen for that event directly.
    ref.listen<int?>(pendingCheckInProvider, (_, id) async {
      if (id == null) return;
      ref.read(pendingCheckInProvider.notifier).state = null;
      try {
        final event = await ref.read(eventDetailProvider(id).future);
        if (context.mounted) {
          Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => AttendanceScreen(event: event)),
          );
        }
      } catch (_) {/* event unavailable */}
    });

    final report = ref.watch(studentReportProvider).valueOrNull;
    final s = report?.summary;

    final events = ref.watch(scheduleEventsProvider).valueOrNull ?? const [];
    final now = DateTime.now();
    final upcoming = events
        .where((e) =>
            e.startDatetime != null &&
            e.startDatetime!.isAfter(now) &&
            !e.isCancelled)
        .toList()
      ..sort((a, b) => a.startDatetime!.compareTo(b.startDatetime!));
    final next = upcoming.isNotEmpty ? upcoming.first : null;

    final monthly = report?.monthly ?? const <String, Map<String, int>>{};
    final mkeys = monthly.keys.toList()..sort();
    final recent6 =
        mkeys.length > 6 ? mkeys.sublist(mkeys.length - 6) : mkeys;
    final monthLabels = [
      for (final k in recent6) k.length >= 7 ? k.substring(5) : k
    ];
    final monthValues = [
      for (final k in recent6)
        (monthly[k]?['present'] ??
            monthly[k]?['attended'] ??
            monthly[k]?['total'] ??
            0)
    ];

    return RefreshIndicator(
      color: t.accent,
      backgroundColor: t.surface,
      onRefresh: () {
        ref.invalidate(scheduleEventsProvider);
        return ref.refresh(studentReportProvider.future);
      },
      child: ListView(
        padding: _pad,
        physics: const AlwaysScrollableScrollPhysics(),
        children: staggered([
          const NearbyEventBanner(),
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
                    Text('Hi, $name', style: textTheme.displaySmall),
                    Text(meta?.schoolName ?? 'Welcome to Aura',
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
            title: 'Attendance',
            value: s != null ? '${s.attendanceRate.round()}%' : '—',
            footnote: s != null
                ? '${s.attendedEvents} of ${s.totalEvents} events'
                : 'loading…',
            percent: s?.attendanceRate,
          ),
          const SizedBox(height: AppSpacing.x12),
          Row(
            children: [
              Expanded(
                child: MetricChipCard(
                  icon: Icons.check_circle_rounded,
                  label: 'Present',
                  value: s?.attendedEvents.toString() ?? '—',
                  tint: t.present,
                ),
              ),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: MetricChipCard(
                  icon: Icons.cancel_rounded,
                  label: 'Absences',
                  value: s?.absentEvents.toString() ?? '—',
                  tint: t.absent,
                ),
              ),
            ],
          ),
          if (monthLabels.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x24),
            const SectionHeader(title: 'Monthly attendance'),
            AuraCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  DashboardBarChart(
                    labels: monthLabels,
                    values: monthValues,
                    colors: [t.accentDark],
                  ),
                  const SizedBox(height: AppSpacing.x8),
                  Text('Events attended per month',
                      style:
                          textTheme.bodySmall?.copyWith(color: t.textMuted)),
                ],
              ),
            ),
          ],
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Up next'),
          if (next != null)
            EventCard(
              event: next,
              onTap: () => Navigator.of(context).push(MaterialPageRoute(
                  builder: (_) => EventDetailScreen(eventId: next.id))),
            )
          else
            const EmptyState(
              icon: Icons.event_available_rounded,
              title: 'Nothing scheduled',
              message: 'Upcoming events will appear here.',
            ),
        ]),
      ),
    );
  }
}
