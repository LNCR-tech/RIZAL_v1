import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/arc_gauge.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/section_header.dart';
import '../../../core/widgets/states.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../shared/models/analytics.dart';
import '../../../shared/models/event.dart';
import '../../../shared/utils/formatting.dart';
import '../../events/application/events_providers.dart';
import '../../events/presentation/event_detail_screen.dart';
import '../../events/presentation/widgets/event_card.dart';
import '../application/student_providers.dart';

class AnalyticsScreen extends ConsumerWidget {
  const AnalyticsScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x24, AppSpacing.x20, 120);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final async = ref.watch(studentReportProvider);
    final events = ref.watch(scheduleEventsProvider).valueOrNull ?? const [];

    Widget header() => Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.x16),
          child: Text('Insights', style: textTheme.displaySmall),
        );

    return RefreshIndicator(
      color: t.accent,
      backgroundColor: t.surface,
      onRefresh: () {
        ref.invalidate(myProfileProvider);
        ref.invalidate(scheduleEventsProvider);
        return ref.refresh(studentReportProvider.future);
      },
      child: async.when(
        loading: () => ListView(
          padding: _pad,
          physics: const AlwaysScrollableScrollPhysics(),
          children: [header(), const SizedBox(height: 60), const Center(child: CircularProgressIndicator())],
        ),
        error: (e, _) => ListView(
          padding: _pad,
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            header(),
            const SizedBox(height: 24),
            ErrorView(
              message:
                  e is ApiException ? e.message : 'Could not load analytics.',
              onRetry: () => ref.invalidate(studentReportProvider),
            ),
          ],
        ),
        data: (report) =>
            _Content(report: report, events: events, header: header()),
      ),
    );
  }
}

class _Content extends StatelessWidget {
  const _Content(
      {required this.report, required this.events, required this.header});
  final StudentReport report;
  final List<AppEvent> events;
  final Widget header;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final s = report.summary;
    final now = DateTime.now();

    final ongoing = events.where((e) => e.isOngoing).toList();
    final upcoming = events
        .where((e) =>
            e.isUpcoming && (e.startDatetime?.isAfter(now) ?? true))
        .toList()
      ..sort((a, b) => (a.startDatetime ?? DateTime(2100))
          .compareTo(b.startDatetime ?? DateTime(2100)));
    final nowNext = [...ongoing, ...upcoming.take(3)];

    final recent = [...report.records]..sort((a, b) =>
        (b.eventDate ?? DateTime(1900)).compareTo(a.eventDate ?? DateTime(1900)));

    return ListView(
      padding: AnalyticsScreen._pad,
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        header,
        // Hero gauge
        AuraCard(
          color: t.accent.withOpacity(0.14),
          child: Column(
            children: [
              ArcGauge(
                percent: s.attendanceRate,
                color: t.accentDark,
                trackColor: t.surface,
                size: 210,
                stroke: 17,
                center: Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('${s.attendanceRate.round()}%',
                          style: AppTypography.mono(
                              size: 32, weight: FontWeight.w800, color: t.ink)),
                      Text('Attendance',
                          style: textTheme.bodyMedium
                              ?.copyWith(color: t.textSecondary)),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.x8),
              Text('${s.attendedEvents} of ${s.totalEvents} events attended',
                  style: textTheme.bodySmall?.copyWith(color: t.textSecondary)),
            ],
          ),
        ),

        if (nowNext.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Now & next'),
          for (final e in nowNext)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.x12),
              child: EventCard(
                event: e,
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => EventDetailScreen(eventId: e.id))),
              ),
            ),
        ],

        const SizedBox(height: AppSpacing.x24),
        const SectionHeader(title: 'Breakdown'),
        Row(children: [
          Expanded(child: _StatTile('Present', s.attendedEvents, t.present)),
          const SizedBox(width: AppSpacing.x12),
          Expanded(child: _StatTile('Late', s.lateEvents, t.tardy)),
          const SizedBox(width: AppSpacing.x12),
          Expanded(child: _StatTile('Absent', s.absentEvents, t.absent)),
        ]),
        const SizedBox(height: AppSpacing.x12),
        Row(children: [
          Expanded(child: _StatTile('Excused', s.excusedEvents, t.excused)),
          const SizedBox(width: AppSpacing.x12),
          Expanded(child: _StatTile('Incomplete', s.incompleteEvents, t.atRisk)),
          const SizedBox(width: AppSpacing.x12),
          const Expanded(child: SizedBox()),
        ]),

        if (report.monthly.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Monthly attendance'),
          AuraCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                    height: 140,
                    child:
                        _TrendChart(monthly: report.monthly, color: t.accent)),
                const SizedBox(height: AppSpacing.x8),
                Text('Events attended per month',
                    style: textTheme.bodySmall?.copyWith(color: t.textMuted)),
              ],
            ),
          ),
        ],

        if (report.eventTypeStats.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'By event type'),
          AuraCard(child: _TypePie(stats: report.eventTypeStats)),
        ],

        if (recent.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Recent'),
          for (final r in recent.take(12))
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.x12),
              child: AuraCard(
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(r.eventName ?? 'Event',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: textTheme.titleLarge),
                          const SizedBox(height: 2),
                          Text(fmtFullDate(r.eventDate),
                              style: textTheme.bodySmall
                                  ?.copyWith(color: t.textSecondary)),
                        ],
                      ),
                    ),
                    const SizedBox(width: AppSpacing.x12),
                    StatusChip.forStatus(context, r.effectiveStatus),
                  ],
                ),
              ),
            ),
        ],
      ],
    );
  }
}

class _StatTile extends StatelessWidget {
  const _StatTile(this.label, this.value, this.color);
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
                  size: 24, weight: FontWeight.w700, color: t.ink)),
          const SizedBox(height: 6),
          Row(children: [
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
          ]),
        ],
      ),
    );
  }
}

class _TrendChart extends StatelessWidget {
  const _TrendChart({required this.monthly, required this.color});
  final Map<String, Map<String, int>> monthly;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final keys = monthly.keys.toList()..sort();
    final spots = <FlSpot>[];
    for (var i = 0; i < keys.length; i++) {
      final m = monthly[keys[i]]!;
      final y = (m['present'] ?? m['attended'] ?? m['total'] ?? 0).toDouble();
      spots.add(FlSpot(i.toDouble(), y));
    }
    if (spots.isEmpty) return const SizedBox.shrink();
    return LineChart(
      LineChartData(
        minY: 0,
        titlesData: const FlTitlesData(show: false),
        gridData: const FlGridData(show: false),
        borderData: FlBorderData(show: false),
        lineTouchData: const LineTouchData(enabled: false),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: color,
            barWidth: 3,
            dotData: FlDotData(show: spots.length <= 6),
            belowBarData:
                BarAreaData(show: true, color: color.withOpacity(0.12)),
          ),
        ],
      ),
    );
  }
}

class _TypePie extends StatelessWidget {
  const _TypePie({required this.stats});
  final Map<String, int> stats;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final palette = [
      t.accentDark,
      t.present,
      t.ssg,
      t.sg,
      t.tardy,
      t.absent,
      t.excused,
    ];
    final entries = stats.entries.where((e) => e.value > 0).toList();
    if (entries.isEmpty) {
      return Text('No event-type data yet.',
          style: textTheme.bodySmall?.copyWith(color: t.textMuted));
    }
    return Row(
      children: [
        SizedBox(
          width: 130,
          height: 130,
          child: PieChart(
            PieChartData(
              sectionsSpace: 2,
              centerSpaceRadius: 32,
              sections: [
                for (var i = 0; i < entries.length; i++)
                  PieChartSectionData(
                    value: entries[i].value.toDouble(),
                    color: palette[i % palette.length],
                    title: '${entries[i].value}',
                    radius: 34,
                    titleStyle: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w700),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(width: AppSpacing.x16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (var i = 0; i < entries.length; i++)
                Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    children: [
                      Container(
                          width: 10,
                          height: 10,
                          decoration: BoxDecoration(
                              color: palette[i % palette.length],
                              shape: BoxShape.circle)),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text('${entries[i].key} (${entries[i].value})',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: textTheme.bodySmall),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }
}
