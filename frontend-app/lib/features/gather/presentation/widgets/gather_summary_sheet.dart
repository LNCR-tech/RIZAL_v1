import 'package:flutter/material.dart';

import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_tokens.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/widgets/aura_button.dart';
import '../../../../shared/models/public_attendance.dart';
import 'gather_outcome_tile.dart';

/// Stats for an operator-visible end-of-session recap, derived from the
/// session's full outcome log (we keep the live log capped at 40, so the
/// counters live separately in the screen state).
class GatherSessionStats {
  const GatherSessionStats({
    required this.signIns,
    required this.signOuts,
    required this.spoofs,
    required this.outOfScope,
    required this.duration,
    required this.recent,
  });

  final int signIns;
  final int signOuts;
  final int spoofs;
  final int outOfScope;
  final Duration duration;

  /// Newest-first; what to surface as the "recent" list on the sheet.
  final List<ScanOutcome> recent;

  int get totalRecognized => signIns + signOuts;
}

class GatherSummarySheet extends StatelessWidget {
  const GatherSummarySheet({
    super.key,
    required this.eventName,
    required this.stats,
    required this.onDone,
    this.onResume,
  });

  final String eventName;
  final GatherSessionStats stats;
  final VoidCallback onDone;

  /// When set, shows a "Resume" secondary action that re-opens the loop. Use
  /// from the scan screen's stop flow; on the back-from-kiosk flow, leave null.
  final VoidCallback? onResume;

  static Future<void> show(
    BuildContext context, {
    required String eventName,
    required GatherSessionStats stats,
    required VoidCallback onDone,
    VoidCallback? onResume,
  }) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => GatherSummarySheet(
        eventName: eventName,
        stats: stats,
        onDone: onDone,
        onResume: onResume,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return SafeArea(
      top: false,
      child: Container(
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius: AppRadii.rSheet,
        ),
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x24, AppSpacing.x12, AppSpacing.x24, AppSpacing.x24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Drag handle
            Center(
              child: Container(
                width: 38,
                height: 4,
                margin: const EdgeInsets.only(bottom: AppSpacing.x16),
                decoration: BoxDecoration(
                  color: t.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Text('Session complete', style: textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
            const SizedBox(height: 2),
            Text(eventName,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.x20),

            // Big mono total + duration
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '${stats.totalRecognized}',
                  style: AppTypography.mono(
                      size: 56, weight: FontWeight.w800, color: t.ink),
                ),
                const SizedBox(width: AppSpacing.x8),
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text(
                    stats.totalRecognized == 1 ? 'person' : 'people',
                    style: textTheme.bodyLarge?.copyWith(color: t.textSecondary),
                  ),
                ),
                const Spacer(),
                _DurationChip(duration: stats.duration),
              ],
            ),

            const SizedBox(height: AppSpacing.x16),

            // Breakdown
            Wrap(
              spacing: AppSpacing.x8,
              runSpacing: AppSpacing.x8,
              children: [
                _BreakdownChip(
                  icon: Icons.login_rounded,
                  label: 'Checked in',
                  count: stats.signIns,
                  tint: t.present,
                ),
                if (stats.signOuts > 0)
                  _BreakdownChip(
                    icon: Icons.logout_rounded,
                    label: 'Signed out',
                    count: stats.signOuts,
                    tint: t.sg,
                  ),
                if (stats.spoofs > 0)
                  _BreakdownChip(
                    icon: Icons.gpp_bad_rounded,
                    label: 'Spoofs caught',
                    count: stats.spoofs,
                    tint: t.absent,
                  ),
                if (stats.outOfScope > 0)
                  _BreakdownChip(
                    icon: Icons.do_not_disturb_on_rounded,
                    label: 'Out of scope',
                    count: stats.outOfScope,
                    tint: t.atRisk,
                  ),
              ],
            ),

            if (stats.recent.isNotEmpty) ...[
              const SizedBox(height: AppSpacing.x20),
              Text('Recent',
                  style: textTheme.labelLarge?.copyWith(color: t.textSecondary)),
              const SizedBox(height: AppSpacing.x8),
              for (final o in stats.recent.take(5))
                Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.x8),
                  child: GatherOutcomeTile(outcome: o, dense: true),
                ),
            ],

            const SizedBox(height: AppSpacing.x20),
            Row(
              children: [
                if (onResume != null) ...[
                  Expanded(
                    child: AuraButton(
                      label: 'Resume',
                      icon: Icons.play_arrow_rounded,
                      variant: AuraButtonVariant.ghost,
                      onPressed: () {
                        Navigator.of(context).pop();
                        onResume!();
                      },
                    ),
                  ),
                  const SizedBox(width: AppSpacing.x12),
                ],
                Expanded(
                  child: AuraButton(
                    label: 'Done',
                    icon: Icons.check_rounded,
                    onPressed: () {
                      Navigator.of(context).pop();
                      onDone();
                    },
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _BreakdownChip extends StatelessWidget {
  const _BreakdownChip({
    required this.icon,
    required this.label,
    required this.count,
    required this.tint,
  });
  final IconData icon;
  final String label;
  final int count;
  final Color tint;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x12, vertical: AppSpacing.x8),
      decoration: BoxDecoration(
        color: tint.withOpacity(t.isDark ? 0.20 : 0.14),
        borderRadius: BorderRadius.circular(AppRadii.pill),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: tint),
          const SizedBox(width: 6),
          Text(
            '$count ',
            style: AppTypography.mono(
                size: 14, weight: FontWeight.w800, color: t.ink),
          ),
          Text(label,
              style:
                  textTheme.bodySmall?.copyWith(color: t.textSecondary)),
        ],
      ),
    );
  }
}

class _DurationChip extends StatelessWidget {
  const _DurationChip({required this.duration});
  final Duration duration;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final h = duration.inHours;
    final m = duration.inMinutes.remainder(60);
    final s = duration.inSeconds.remainder(60);
    final label = h > 0
        ? '${h}h ${m}m'
        : (m > 0 ? '${m}m ${s.toString().padLeft(2, '0')}s' : '${s}s');
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x12, vertical: 6),
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: BorderRadius.circular(AppRadii.pill),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.schedule_rounded, size: 14, color: t.textSecondary),
          const SizedBox(width: 6),
          Text(label,
              style: AppTypography.mono(
                  size: 13, weight: FontWeight.w700, color: t.ink)),
          const SizedBox(width: 4),
          Text('runtime',
              style: textTheme.bodySmall?.copyWith(color: t.textMuted)),
        ],
      ),
    );
  }
}
