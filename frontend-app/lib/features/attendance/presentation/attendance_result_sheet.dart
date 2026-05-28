import 'package:flutter/material.dart';

import '../../../core/theme/app_motion.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/rise_in.dart';
import '../../../shared/models/attendance.dart';
import '../../../shared/utils/formatting.dart';

/// Bottom sheet shown after a face scan completes. Designed to leave **zero
/// doubt** about what just happened:
///
///   * A big action title with colour + icon: "Checked in", "Signed out",
///     "Already checked in" — never an ambiguous "Recorded".
///   * The captured time in JetBrains Mono with explicit `CHECK-IN TIME` /
///     `CHECK-OUT TIME` labels, so a glance is enough.
///   * For a fresh check-in: a follow-up row telling the student **when
///     the sign-out window opens** so they know to come back.
///   * For a sign-out: total duration ("6h 18m") computed from the pair.
///
/// Motion (emil + flutter-animations): rows rise-in with a 50ms stagger,
/// the action icon settles via TweenAnimationBuilder (scale 0.92 → 1.0 +
/// fade, 260ms ease-out — never scale(0)), reduced-motion fully honoured.
class AttendanceResultSheet extends StatelessWidget {
  const AttendanceResultSheet({
    super.key,
    required this.result,
    this.signOutOpensAt,
  });

  final FaceScanResult result;

  /// Optional context the caller (the attendance screen) can pass in so
  /// the sheet can show "Sign-out opens at HH:MM" right after a fresh
  /// check-in. When the scan was itself a sign-out, this is ignored.
  final DateTime? signOutOpensAt;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    final visual = _visualFor(result, t);

    return Container(
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: AppRadii.rSheet,
      ),
      padding: EdgeInsets.fromLTRB(
        AppSpacing.x24,
        AppSpacing.x16,
        AppSpacing.x24,
        AppSpacing.x24 + MediaQuery.of(context).padding.bottom,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: staggered([
          // ── Drag handle ──
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: t.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.x24),

          // ── Action icon + title ──
          Center(child: _ActionIcon(color: visual.color, icon: visual.icon)),
          const SizedBox(height: AppSpacing.x16),
          Center(
            child: Text(
              visual.title,
              textAlign: TextAlign.center,
              style: textTheme.headlineSmall,
            ),
          ),
          if (result.studentName != null) ...[
            const SizedBox(height: 2),
            Center(
              child: Text(
                result.studentName!,
                style: textTheme.bodyMedium?.copyWith(color: t.textSecondary),
              ),
            ),
          ],
          const SizedBox(height: AppSpacing.x20),

          // ── Labeled timestamps (the headline new feature) ──
          if (result.timeIn != null)
            _TimeRow(
              label: 'CHECK-IN TIME',
              time: result.timeIn!,
              icon: Icons.login_rounded,
              color: t.present,
              highlight: result.isTimeIn,
            ),
          if (result.timeIn != null &&
              (result.timeOut != null || _showSignOutHint()))
            const SizedBox(height: AppSpacing.x8),
          if (result.timeOut != null)
            _TimeRow(
              label: 'CHECK-OUT TIME',
              time: result.timeOut!,
              icon: Icons.logout_rounded,
              color: t.sg,
              highlight: result.isTimeOut,
            )
          else if (_showSignOutHint())
            _UpcomingRow(
              label: 'SIGN-OUT OPENS',
              time: signOutOpensAt!,
              icon: Icons.schedule_rounded,
              tint: t.textSecondary,
            ),

          // ── Duration (only when both timestamps exist) ──
          if (result.timeIn != null && result.timeOut != null) ...[
            const SizedBox(height: AppSpacing.x12),
            _DurationChip(
              duration: result.timeOut!.difference(result.timeIn!),
            ),
          ],

          // ── Backend message (only when present + meaningful) ──
          if (result.message != null && result.message!.trim().isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x16),
            Container(
              padding: const EdgeInsets.all(AppSpacing.x12),
              decoration: BoxDecoration(
                color: t.surfaceAlt,
                borderRadius: BorderRadius.circular(AppRadii.control),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline_rounded,
                      size: 16, color: t.textSecondary),
                  const SizedBox(width: AppSpacing.x8),
                  Expanded(
                    child: Text(
                      result.message!,
                      style: textTheme.bodySmall
                          ?.copyWith(color: t.textSecondary),
                    ),
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: AppSpacing.x24),

          AuraButton(
            label: 'Done',
            onPressed: () => Navigator.of(context).pop(),
          ),
        ]),
      ),
    );
  }

  bool _showSignOutHint() =>
      result.isTimeIn && result.timeOut == null && signOutOpensAt != null;
}

// ─── Action icon (large, animated, color-coded) ───────────────────────
class _ActionIcon extends StatelessWidget {
  const _ActionIcon({required this.color, required this.icon});
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: reduce ? 1 : 0.92, end: 1),
      duration:
          reduce ? Duration.zero : const Duration(milliseconds: 260),
      curve: AppMotion.easeOut,
      builder: (context, v, child) => Transform.scale(
        scale: v,
        child: Opacity(opacity: reduce ? 1 : v, child: child),
      ),
      child: Container(
        width: 72,
        height: 72,
        decoration: BoxDecoration(
          color: color.withOpacity(0.16),
          shape: BoxShape.circle,
        ),
        child: Icon(icon, size: 38, color: color),
      ),
    );
  }
}

// ─── Time row (labeled timestamp; the centerpiece) ────────────────────
class _TimeRow extends StatelessWidget {
  const _TimeRow({
    required this.label,
    required this.time,
    required this.icon,
    required this.color,
    this.highlight = false,
  });
  final String label;
  final DateTime time;
  final IconData icon;
  final Color color;

  /// When `true`, this is the row that corresponds to the action that
  /// JUST happened (e.g. CHECK-IN TIME after a fresh check-in scan).
  /// Slightly punchier visual treatment.
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x16, vertical: AppSpacing.x12),
      decoration: BoxDecoration(
        color: highlight ? color.withOpacity(t.isDark ? 0.22 : 0.14) : t.surfaceAlt,
        borderRadius: BorderRadius.circular(AppRadii.control),
        border: Border.all(
          color: highlight ? color.withOpacity(0.4) : t.border,
          width: highlight ? 1.5 : 1,
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color.withOpacity(t.isDark ? 0.30 : 0.20),
              borderRadius: BorderRadius.circular(AppRadii.control),
            ),
            child: Icon(icon, size: 18, color: color),
          ),
          const SizedBox(width: AppSpacing.x12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  label,
                  style: textTheme.labelMedium?.copyWith(
                    color: t.textSecondary,
                    letterSpacing: 0.8,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  fmtTime(time),
                  style: AppTypography.mono(
                    size: 22,
                    weight: FontWeight.w800,
                    color: t.ink,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Upcoming row (e.g. "SIGN-OUT OPENS at 3:00 PM") ──────────────────
class _UpcomingRow extends StatelessWidget {
  const _UpcomingRow({
    required this.label,
    required this.time,
    required this.icon,
    required this.tint,
  });
  final String label;
  final DateTime time;
  final IconData icon;
  final Color tint;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x16, vertical: AppSpacing.x12),
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: BorderRadius.circular(AppRadii.control),
        border: Border.all(color: t.border),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: t.surface,
              borderRadius: BorderRadius.circular(AppRadii.control),
            ),
            child: Icon(icon, size: 18, color: tint),
          ),
          const SizedBox(width: AppSpacing.x12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  label,
                  style: textTheme.labelMedium?.copyWith(
                    color: t.textMuted,
                    letterSpacing: 0.8,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  fmtTime(time),
                  style: AppTypography.mono(
                    size: 18,
                    weight: FontWeight.w700,
                    color: t.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Duration chip (only when both check-in and check-out exist) ──────
class _DurationChip extends StatelessWidget {
  const _DurationChip({required this.duration});
  final Duration duration;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final h = duration.inHours;
    final m = duration.inMinutes.remainder(60);
    final label = h > 0 ? '${h}h ${m}m' : '${m}m';

    return Center(
      child: Container(
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x16, vertical: AppSpacing.x8),
        decoration: BoxDecoration(
          color: t.accent.withOpacity(t.isDark ? 0.24 : 0.16),
          borderRadius: BorderRadius.circular(AppRadii.pill),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.schedule_rounded, size: 16, color: t.accentDark),
            const SizedBox(width: 6),
            Text(
              'Total time: ',
              style:
                  textTheme.bodySmall?.copyWith(color: t.textSecondary),
            ),
            Text(
              label,
              style: AppTypography.mono(
                size: 14,
                weight: FontWeight.w800,
                color: t.ink,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Visual specs per result.action ───────────────────────────────────
class _Visual {
  const _Visual({required this.title, required this.color, required this.icon});
  final String title;
  final Color color;
  final IconData icon;
}

_Visual _visualFor(FaceScanResult r, AppTokens t) {
  if (r.isTimeIn) {
    return _Visual(
      title: 'Checked in',
      color: t.present,
      icon: Icons.check_circle_rounded,
    );
  }
  if (r.isTimeOut) {
    return _Visual(
      title: 'Signed out',
      color: t.sg,
      icon: Icons.logout_rounded,
    );
  }
  // Backend returned a non-time action (e.g. `already_signed_in`,
  // `already_signed_out`, `rejected`). The message field carries the
  // detail; the title here just frames it neutrally instead of the old
  // ambiguous "Recorded".
  return _Visual(
    title: 'Already recorded',
    color: t.textSecondary,
    icon: Icons.task_alt_rounded,
  );
}
