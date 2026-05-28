import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/rise_in.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/public_attendance.dart';
import '../application/gather_providers.dart';
import 'gather_scan_screen.dart';
import 'widgets/gather_phase_pill.dart';

/// Kiosk entry — discover geofenced events near the device, then open one in
/// the multi-face scan kiosk. Public attendance is unauthenticated, so any
/// device standing inside an event radius can run it.
class GatherScreen extends ConsumerWidget {
  const GatherScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x12, AppSpacing.x20, 40);

  void _open(BuildContext context, NearbyEvent event, int cooldown) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) =>
          GatherScanScreen(event: event, cooldownSeconds: cooldown),
    ));
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final async = ref.watch(gatherNearbyProvider);

    return AppScaffold(
      title: 'Gather',
      body: RefreshIndicator(
        color: t.accent,
        backgroundColor: t.surface,
        onRefresh: () => ref.refresh(gatherNearbyProvider.future),
        child: async.when(
          loading: () =>
              const Padding(padding: _pad, child: LoadingCardList(count: 3)),
          error: (e, _) => ListView(
            padding: _pad,
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              const _HeaderIntro(),
              const SizedBox(height: AppSpacing.x16),
              ErrorView(
                message: e is ApiException
                    ? e.message
                    : 'Could not find nearby events.',
                onRetry: () => ref.invalidate(gatherNearbyProvider),
              ),
            ],
          ),
          data: (res) {
            if (res.events.isEmpty) {
              return ListView(
                padding: _pad,
                physics: const AlwaysScrollableScrollPhysics(),
                children: const [
                  _HeaderIntro(),
                  SizedBox(height: AppSpacing.x24),
                  _OutOfRangeCard(),
                ],
              );
            }
            final eligible = res.events.where((e) => e.isOpen).toList();
            final waiting = res.events.where((e) => !e.isOpen).toList();
            return ListView(
              padding: _pad,
              physics: const AlwaysScrollableScrollPhysics(),
              children: staggered([
                const _HeaderIntro(),
                const SizedBox(height: AppSpacing.x16),
                if (eligible.isNotEmpty) ...[
                  _SectionLabel(
                    label:
                        '${eligible.length} event${eligible.length == 1 ? '' : 's'} open near you',
                  ),
                  for (final e in eligible)
                    Padding(
                      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                      child: _NearbyCard(
                        event: e,
                        onTap: () => _open(context, e, res.cooldownSeconds),
                      ),
                    ),
                ],
                if (waiting.isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.x12),
                  const _SectionLabel(label: 'Waiting for window'),
                  for (final e in waiting)
                    Padding(
                      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                      child: _NearbyCard(event: e, onTap: null),
                    ),
                ],
              ]),
            );
          },
        ),
      ),
    );
  }
}

class _HeaderIntro extends StatelessWidget {
  const _HeaderIntro();

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AuraCard(
      color: t.accent.withOpacity(t.isDark ? 0.18 : 0.14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: t.surface,
              borderRadius: BorderRadius.circular(AppRadii.control),
            ),
            child: Icon(Icons.center_focus_strong_rounded,
                color: t.accentDark, size: 28),
          ),
          const SizedBox(width: AppSpacing.x16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Kiosk mode',
                    style: textTheme.labelLarge
                        ?.copyWith(color: t.textSecondary)),
                const SizedBox(height: 2),
                Text('Scan many at once',
                    style: textTheme.headlineSmall),
                const SizedBox(height: 6),
                Text(
                  'Pick an event below, then point the back camera at the room. '
                  'Up to 10 faces a frame get matched, recorded, and added to a '
                  'cooldown so the same person never double-counts.',
                  style:
                      textTheme.bodyMedium?.copyWith(color: t.textSecondary),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(2, AppSpacing.x4, 2, AppSpacing.x8),
      child: Text(
        label,
        style: textTheme.labelMedium?.copyWith(
          color: t.textSecondary,
          letterSpacing: 0.4,
        ),
      ),
    );
  }
}

class _NearbyCard extends StatelessWidget {
  const _NearbyCard({required this.event, required this.onTap});
  final NearbyEvent event;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final isDisabled = onTap == null;

    return AuraCard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Top row: phase + distance
          Row(
            children: [
              GatherPhasePill(event: event),
              const SizedBox(width: AppSpacing.x8),
              if (event.distanceM != null)
                _DistanceBadge(
                    distanceM: event.distanceM!,
                    accuracyM: event.accuracyM,
                    inside: event.insideGeofence),
              const Spacer(),
              if (!isDisabled)
                Icon(Icons.chevron_right_rounded, color: t.textMuted),
            ],
          ),
          const SizedBox(height: AppSpacing.x12),

          Text(
            event.name,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: textTheme.headlineSmall?.copyWith(
              color: isDisabled ? t.textSecondary : t.ink,
            ),
          ),

          // Venue + time window
          if (event.location != null) ...[
            const SizedBox(height: 2),
            Row(
              children: [
                Icon(Icons.place_outlined, size: 14, color: t.textMuted),
                const SizedBox(width: 4),
                Flexible(
                  child: Text(
                    event.location!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: textTheme.bodyMedium
                        ?.copyWith(color: t.textSecondary),
                  ),
                ),
              ],
            ),
          ],
          if (event.startDatetime != null) ...[
            const SizedBox(height: 6),
            _TimeWindow(
              start: event.startDatetime!,
              end: event.endDatetime,
            ),
          ],

          // Phase message ("Early check-in opens…")
          if (event.phaseMessage != null) ...[
            const SizedBox(height: AppSpacing.x12),
            Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.x12, vertical: AppSpacing.x8),
              decoration: BoxDecoration(
                color: t.surfaceAlt,
                borderRadius: BorderRadius.circular(AppRadii.control),
              ),
              child: Row(
                children: [
                  Icon(
                    event.isOpen
                        ? Icons.bolt_rounded
                        : Icons.schedule_rounded,
                    size: 14,
                    color: t.textSecondary,
                  ),
                  const SizedBox(width: 6),
                  Flexible(
                    child: Text(
                      event.phaseMessage!,
                      style: textTheme.bodySmall
                          ?.copyWith(color: t.textSecondary),
                    ),
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: AppSpacing.x12),
          GatherScopeChip(event: event),
        ],
      ),
    );
  }
}

class _DistanceBadge extends StatelessWidget {
  const _DistanceBadge({
    required this.distanceM,
    required this.accuracyM,
    required this.inside,
  });
  final double distanceM;
  final double? accuracyM;
  final bool inside;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final color = inside ? t.present : t.textSecondary;
    final accuracyText = (accuracyM != null && accuracyM! > 0)
        ? '·±${accuracyM!.round()}m'
        : '';

    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x8, vertical: 2),
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: BorderRadius.circular(AppRadii.pill),
        border: Border.all(color: t.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            inside ? Icons.gps_fixed_rounded : Icons.gps_off_rounded,
            size: 12,
            color: color,
          ),
          const SizedBox(width: 4),
          Text(
            '${distanceM.round()}m$accuracyText',
            style: AppTypography.mono(
                size: 12, weight: FontWeight.w600, color: color),
          ),
        ],
      ),
    );
  }
}

class _TimeWindow extends StatelessWidget {
  const _TimeWindow({required this.start, this.end});
  final DateTime start;
  final DateTime? end;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final fmt = DateFormat.jm();
    final dayFmt = DateFormat.MMMd();
    final label = end != null
        ? '${dayFmt.format(start)} · ${fmt.format(start)} – ${fmt.format(end!)}'
        : '${dayFmt.format(start)} · ${fmt.format(start)}';
    return Row(
      children: [
        Icon(Icons.schedule_rounded, size: 14, color: t.textMuted),
        const SizedBox(width: 4),
        Flexible(
          child: Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: textTheme.bodySmall?.copyWith(color: t.textSecondary),
          ),
        ),
      ],
    );
  }
}

class _OutOfRangeCard extends StatelessWidget {
  const _OutOfRangeCard();

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: t.surfaceAlt,
              borderRadius: BorderRadius.circular(AppRadii.card),
            ),
            child: Icon(Icons.travel_explore_rounded,
                size: 28, color: t.textSecondary),
          ),
          const SizedBox(height: AppSpacing.x16),
          Text('No events within range', style: textTheme.titleLarge),
          const SizedBox(height: 4),
          Text(
            "Stand within an event's geofence to open the kiosk. Public "
            "attendance only surfaces events whose location is set and whose "
            "check-in or sign-out window is open (or about to open).",
            style: textTheme.bodyMedium?.copyWith(color: t.textSecondary),
          ),
          const SizedBox(height: AppSpacing.x12),
          Row(
            children: [
              Icon(Icons.lightbulb_outline_rounded,
                  size: 16, color: t.textMuted),
              const SizedBox(width: 6),
              Flexible(
                child: Text(
                  'Pull down to refresh after moving.',
                  style: textTheme.bodySmall?.copyWith(color: t.textMuted),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
