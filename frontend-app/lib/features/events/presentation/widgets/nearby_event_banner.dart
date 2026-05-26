import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_tokens.dart';
import '../../../../shared/models/event.dart';
import '../../../attendance/presentation/attendance_screen.dart';
import '../../application/nearby_event_provider.dart';

/// In-app prompt shown when the user is detected inside an event's geofence.
/// Renders nothing until the [nearbyEventProvider] reports a match; then it
/// slides in. Tapping goes straight to the face-scan check-in — no navigating
/// to the event first. Gated by the "nearby event check-in" setting.
class NearbyEventBanner extends ConsumerWidget {
  const NearbyEventBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final event = ref.watch(nearbyEventProvider);
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 320),
      switchInCurve: Curves.easeOutCubic,
      switchOutCurve: Curves.easeIn,
      transitionBuilder: (child, anim) => SizeTransition(
        sizeFactor: anim,
        axisAlignment: -1,
        child: FadeTransition(opacity: anim, child: child),
      ),
      child: event == null
          ? const SizedBox(width: double.infinity)
          : Padding(
              key: ValueKey(event.id),
              padding: const EdgeInsets.only(bottom: AppSpacing.x20),
              child: _Card(event: event),
            ),
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.event});
  final AppEvent event;

  void _checkIn(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => AttendanceScreen(event: event)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final on = t.onAccent;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => _checkIn(context),
        borderRadius: BorderRadius.circular(22),
        child: Ink(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [t.accent, t.accentDark],
            ),
            borderRadius: BorderRadius.circular(22),
            boxShadow: [
              BoxShadow(
                color: t.accent.withOpacity(0.35),
                blurRadius: 18,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          padding: const EdgeInsets.all(AppSpacing.x16),
          child: Row(
            children: [
              _PulseDot(color: on),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "YOU'RE AT AN EVENT",
                      style: textTheme.labelSmall?.copyWith(
                        color: on.withOpacity(0.85),
                        letterSpacing: 0.8,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      event.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: textTheme.titleLarge?.copyWith(color: on),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Attendance is open — tap to check in',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style:
                          textTheme.bodySmall?.copyWith(color: on.withOpacity(0.9)),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: AppSpacing.x12),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
                decoration: BoxDecoration(
                  color: t.surface,
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'Check in',
                      style: textTheme.labelLarge?.copyWith(
                        color: t.accentDark,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Icon(Icons.arrow_forward_rounded,
                        size: 16, color: t.accentDark),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// A location dot with a soft expanding "live" pulse (static when reduced motion).
class _PulseDot extends StatefulWidget {
  const _PulseDot({required this.color});
  final Color color;

  @override
  State<_PulseDot> createState() => _PulseDotState();
}

class _PulseDotState extends State<_PulseDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: const Duration(seconds: 2))
        ..repeat();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final c = widget.color;
    return SizedBox(
      width: 40,
      height: 40,
      child: Stack(
        alignment: Alignment.center,
        children: [
          if (!reduce)
            AnimatedBuilder(
              animation: _c,
              builder: (context, _) {
                final v = _c.value;
                return Container(
                  width: 18 + 22 * v,
                  height: 18 + 22 * v,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: c.withOpacity((1 - v) * 0.35),
                  ),
                );
              },
            ),
          Container(
            width: 30,
            height: 30,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: c.withOpacity(0.18),
            ),
            child: Icon(Icons.location_on_rounded, size: 18, color: c),
          ),
        ],
      ),
    );
  }
}
