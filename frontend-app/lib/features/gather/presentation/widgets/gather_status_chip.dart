import 'package:flutter/material.dart';

import '../../../../core/theme/app_motion.dart';
import '../../../../core/theme/app_tokens.dart';

/// Live face-engine status the operator can scan in their peripheral vision.
/// The chip swaps between states with a 220ms scale + fade (custom ease-out;
/// never ease-in, which would feel sluggish). Always shows color + icon so
/// it's a11y-correct even on a colour-blind device.
enum GatherStatus {
  /// Loop is off (waiting for operator to start).
  standby,

  /// Loop is on, waiting for the next frame to come back.
  scanning,

  /// At least one verified face came back from the last frame.
  verified,

  /// The last frame returned a `liveness_failed` outcome — a spoof was caught.
  spoof,

  /// The anti-spoof model is unavailable; matches are landing in "Bypassed"
  /// mode.
  bypassed,

  /// The last frame returned only `out_of_scope` / `no_match` outcomes — the
  /// camera saw someone, but no one belonged to this event's audience.
  outOfScope,
}

class GatherStatusChip extends StatelessWidget {
  const GatherStatusChip({super.key, required this.status});

  final GatherStatus status;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final spec = _spec(t, status);

    // Stable key so AnimatedSwitcher actually transitions between states; if
    // the same status returns we want to keep the existing widget (no
    // re-animation).
    final child = _Chip(
      key: ValueKey<GatherStatus>(status),
      spec: spec,
    );

    return AnimatedSwitcher(
      duration:
          reduce ? Duration.zero : const Duration(milliseconds: 220),
      reverseDuration:
          reduce ? Duration.zero : const Duration(milliseconds: 140),
      switchInCurve: AppMotion.easeOut,
      switchOutCurve: AppMotion.easeOut,
      transitionBuilder: (child, anim) {
        // Asymmetric: incoming pops in, outgoing shrinks slightly. Never from
        // scale(0) — start at 0.94 so the swap looks intentional, not magic.
        final scale = Tween<double>(begin: 0.94, end: 1.0).animate(anim);
        return FadeTransition(
          opacity: anim,
          child: ScaleTransition(scale: scale, child: child),
        );
      },
      layoutBuilder: (current, previous) => Stack(
        alignment: Alignment.center,
        children: [...previous, if (current != null) current],
      ),
      child: child,
    );
  }
}

class _ChipSpec {
  const _ChipSpec({
    required this.label,
    required this.icon,
    required this.fg,
    required this.bg,
    this.pulsing = false,
  });
  final String label;
  final IconData icon;
  final Color fg;
  final Color bg;
  final bool pulsing;
}

_ChipSpec _spec(AppTokens t, GatherStatus s) {
  switch (s) {
    case GatherStatus.standby:
      return _ChipSpec(
        label: 'Standby',
        icon: Icons.pause_circle_filled_rounded,
        fg: Colors.white.withOpacity(0.92),
        bg: Colors.white.withOpacity(0.08),
      );
    case GatherStatus.scanning:
      return _ChipSpec(
        label: 'Looking',
        icon: Icons.center_focus_strong_rounded,
        fg: Colors.white,
        bg: Colors.black.withOpacity(0.55),
        pulsing: true,
      );
    case GatherStatus.verified:
      return _ChipSpec(
        label: 'Verified',
        icon: Icons.verified_rounded,
        fg: Colors.white,
        bg: t.present,
      );
    case GatherStatus.spoof:
      return _ChipSpec(
        label: 'Spoof rejected',
        icon: Icons.gpp_bad_rounded,
        fg: Colors.white,
        bg: t.absent,
      );
    case GatherStatus.bypassed:
      return _ChipSpec(
        label: 'Liveness bypassed',
        icon: Icons.shield_outlined,
        fg: Colors.white,
        bg: t.tardy,
      );
    case GatherStatus.outOfScope:
      return _ChipSpec(
        label: 'Out of scope',
        icon: Icons.do_not_disturb_on_rounded,
        fg: Colors.white,
        bg: t.atRisk,
      );
  }
}

class _Chip extends StatefulWidget {
  const _Chip({super.key, required this.spec});
  final _ChipSpec spec;

  @override
  State<_Chip> createState() => _ChipState();
}

class _ChipState extends State<_Chip> with SingleTickerProviderStateMixin {
  late final AnimationController _pulse = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1100),
  );

  @override
  void initState() {
    super.initState();
    if (widget.spec.pulsing) _pulse.repeat(reverse: true);
  }

  @override
  void didUpdateWidget(covariant _Chip old) {
    super.didUpdateWidget(old);
    if (widget.spec.pulsing && !_pulse.isAnimating) {
      _pulse.repeat(reverse: true);
    } else if (!widget.spec.pulsing && _pulse.isAnimating) {
      _pulse.stop();
      _pulse.value = 0;
    }
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final spec = widget.spec;
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    final dot = AnimatedBuilder(
      animation: _pulse,
      builder: (context, _) {
        final t = reduce ? 1.0 : (0.55 + _pulse.value * 0.45);
        return Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: spec.fg.withOpacity(t),
            shape: BoxShape.circle,
          ),
        );
      },
    );

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: spec.bg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (spec.pulsing) ...[
            dot,
            const SizedBox(width: 8),
          ] else ...[
            Icon(spec.icon, size: 14, color: spec.fg),
            const SizedBox(width: 6),
          ],
          Text(
            spec.label,
            style: TextStyle(
              color: spec.fg,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.1,
            ),
          ),
        ],
      ),
    );
  }
}
