import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../../core/theme/app_motion.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_tokens.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../shared/models/public_attendance.dart';

/// One outcome from a multi-face scan, rendered as a row inside the kiosk's
/// live log. Uses a colour-coded leading chip + mono confidence + small
/// liveness badge so the operator can read the result at a glance.
///
/// Plays a one-shot pop on mount: scale 0.94 → 1.0 + opacity 0 → 1 over 220ms,
/// with a tiny lateral shake for hard failures (spoof / rejected). Honors
/// reduced motion. Never animates from `scale(0)` — emil.
class GatherOutcomeTile extends StatefulWidget {
  const GatherOutcomeTile({
    super.key,
    required this.outcome,
    this.onSurfaceColor,
    this.dense = false,
  });

  final ScanOutcome outcome;

  /// When laid over a dark/camera surface, set this to a light text colour so
  /// the row reads correctly. Defaults to the theme's ink.
  final Color? onSurfaceColor;

  final bool dense;

  @override
  State<GatherOutcomeTile> createState() => _GatherOutcomeTileState();
}

class _GatherOutcomeTileState extends State<GatherOutcomeTile>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pop = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 260),
  );

  late final AnimationController _shake = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 320),
  );

  bool _scheduled = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_scheduled) return;
    _scheduled = true;
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (reduce) {
      _pop.value = 1;
      return;
    }
    _pop.forward();
    if (widget.outcome.isHardFailure && widget.outcome.isLivenessFailed) {
      // Short, sharp shake on spoof — never on plain "no_match" (would feel
      // accusatory toward unknown bystanders).
      _shake.forward();
    }
  }

  @override
  void dispose() {
    _pop.dispose();
    _shake.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final outcome = widget.outcome;
    final tones = _intentTones(t, outcome.intent);
    final onSurface = widget.onSurfaceColor ?? t.ink;
    final muted = widget.onSurfaceColor != null
        ? Colors.white.withOpacity(0.72)
        : t.textSecondary;

    final confidence = outcome.confidence;
    final confLabel =
        confidence != null ? '${(confidence.clamp(0, 1) * 100).round()}%' : null;

    final liveness = outcome.liveness;

    return AnimatedBuilder(
      animation: Listenable.merge([_pop, _shake]),
      builder: (context, child) {
        final p = AppMotion.easeOut.transform(_pop.value);
        final s = _shake.value;
        // Damped sine wave; quick peak then settles.
        final shakeOffset =
            s == 0 ? 0.0 : (1 - s) * 8 * (1 - s) * math.sin(s * 18);
        return Opacity(
          opacity: p,
          child: Transform.translate(
            offset: Offset(shakeOffset, (1 - p) * 6),
            child: Transform.scale(scale: 0.94 + 0.06 * p, child: child),
          ),
        );
      },
      child: Container(
        padding: widget.dense
            ? const EdgeInsets.symmetric(
                horizontal: AppSpacing.x12, vertical: AppSpacing.x8)
            : const EdgeInsets.all(AppSpacing.x12),
        decoration: BoxDecoration(
          color: widget.onSurfaceColor != null
              ? Colors.white.withOpacity(0.06)
              : t.surface,
          borderRadius: BorderRadius.circular(AppRadii.control),
          border: Border.all(
            color: widget.onSurfaceColor != null
                ? Colors.white.withOpacity(0.08)
                : t.border,
          ),
        ),
        child: Row(
          children: [
            _LeadingChip(icon: outcome.icon, tone: tones),
            const SizedBox(width: AppSpacing.x12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    outcome.displayName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style:
                        Theme.of(context).textTheme.titleLarge?.copyWith(
                              color: onSurface,
                              height: 1.15,
                            ),
                  ),
                  const SizedBox(height: 2),
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          outcome.actionLabel,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(color: muted),
                        ),
                      ),
                      if (liveness != null && !liveness.isReal) ...[
                        const SizedBox(width: AppSpacing.x8),
                        _LivenessBadge(
                            liveness: liveness, tones: tones, muted: muted),
                      ],
                    ],
                  ),
                ],
              ),
            ),
            if (confLabel != null) ...[
              const SizedBox(width: AppSpacing.x8),
              Text(
                confLabel,
                style: AppTypography.mono(
                  size: 14,
                  weight: FontWeight.w700,
                  color: tones.fg,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _LeadingChip extends StatelessWidget {
  const _LeadingChip({required this.icon, required this.tone});
  final IconData icon;
  final _IntentTones tone;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: tone.bg,
        borderRadius: BorderRadius.circular(AppRadii.control),
      ),
      child: Icon(icon, color: tone.fg, size: 22),
    );
  }
}

class _LivenessBadge extends StatelessWidget {
  const _LivenessBadge({
    required this.liveness,
    required this.tones,
    required this.muted,
  });
  final Liveness liveness;
  final _IntentTones tones;
  final Color muted;

  @override
  Widget build(BuildContext context) {
    final label = liveness.isFake
        ? 'Spoof'
        : (liveness.isBypassed ? 'Bypassed' : 'Real');
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: tones.fg.withOpacity(0.16),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: tones.fg.withOpacity(0.25)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            liveness.isFake
                ? Icons.gpp_bad_rounded
                : (liveness.isBypassed
                    ? Icons.shield_outlined
                    : Icons.shield_rounded),
            size: 11,
            color: tones.fg,
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              color: tones.fg,
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.1,
            ),
          ),
        ],
      ),
    );
  }
}

class _IntentTones {
  const _IntentTones(this.bg, this.fg);
  final Color bg;
  final Color fg;
}

_IntentTones _intentTones(AppTokens t, OutcomeIntent intent) {
  switch (intent) {
    case OutcomeIntent.success:
      return _IntentTones(t.present.withOpacity(t.isDark ? 0.22 : 0.16), t.present);
    case OutcomeIntent.info:
      return _IntentTones(t.accent.withOpacity(0.18), t.accentDark);
    case OutcomeIntent.warning:
      return _IntentTones(t.atRisk.withOpacity(0.18), t.atRisk);
    case OutcomeIntent.danger:
      return _IntentTones(t.absent.withOpacity(0.20), t.absent);
    case OutcomeIntent.neutral:
      return _IntentTones(t.surfaceAlt, t.textSecondary);
  }
}

