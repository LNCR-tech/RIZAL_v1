import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_tokens.dart';
import '../../application/event_phase_provider.dart';
import '../../application/geofence_background.dart';
import '../../application/pending_attendance_action.dart';

/// In-app prompt shown when an event the user can attend is currently in an
/// actionable phase (early_check_in, late_check_in, sign_out_open) or is
/// about to close sign-out. Mounts above [NearbyEventBanner] on student
/// Home so the time-based reminder is the first thing the user sees.
class EventPhaseBanner extends ConsumerWidget {
  const EventPhaseBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sel = ref.watch(eventPhaseProvider);
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 320),
      switchInCurve: Curves.easeOutCubic,
      switchOutCurve: Curves.easeIn,
      transitionBuilder: (child, anim) => SizeTransition(
        sizeFactor: anim,
        axisAlignment: -1,
        child: FadeTransition(opacity: anim, child: child),
      ),
      child: sel == null
          ? const SizedBox(width: double.infinity)
          : Padding(
              key: ValueKey('${sel.eventId}-${sel.phase.name}'),
              padding: const EdgeInsets.only(bottom: AppSpacing.x20),
              child: _Card(selection: sel, onTap: () => _tap(ref, sel)),
            ),
    );
  }

  void _tap(WidgetRef ref, BannerSelection sel) {
    ref.read(pendingCheckInProvider.notifier).state = sel.eventId;
    ref.read(pendingAttendanceActionProvider.notifier).state =
        sel.phase == BannerPhase.checkInOpen
            ? AttendanceAction.checkin
            : AttendanceAction.signout;
  }
}

class _BannerSpec {
  const _BannerSpec({
    required this.label,
    required this.icon,
    required this.cta,
    required this.tint,
  });
  final String label;
  final IconData icon;
  final String cta;
  final Color tint;
}

class _Card extends StatelessWidget {
  const _Card({required this.selection, required this.onTap});
  final BannerSelection selection;
  final VoidCallback onTap;

  _BannerSpec _spec(AppTokens t) {
    switch (selection.phase) {
      case BannerPhase.signOutOpen:
        return _BannerSpec(
          label: 'SIGN-OUT IS OPEN',
          icon: Icons.logout_rounded,
          cta: 'Sign out',
          tint: t.accent,
        );
      case BannerPhase.checkInOpen:
        return _BannerSpec(
          label: 'CHECK-IN IS OPEN',
          icon: Icons.login_rounded,
          cta: 'Check in',
          tint: t.accent,
        );
      case BannerPhase.signOutClosingSoon:
        return _BannerSpec(
          label: 'LAST CALL: SIGN OUT',
          icon: Icons.logout_rounded,
          cta: 'Sign out',
          tint: t.tardy,
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final spec = _spec(t);
    final on = t.onAccent;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(22),
        child: Ink(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [spec.tint, t.accentDark],
            ),
            borderRadius: BorderRadius.circular(22),
            boxShadow: [
              BoxShadow(
                color: spec.tint.withOpacity(0.35),
                blurRadius: 18,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          padding: const EdgeInsets.all(AppSpacing.x16),
          child: Row(
            children: [
              _PulseDot(color: on, icon: spec.icon),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      spec.label,
                      style: textTheme.labelSmall?.copyWith(
                        color: on.withOpacity(0.85),
                        letterSpacing: 0.8,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      selection.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: textTheme.titleLarge?.copyWith(color: on),
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
                      spec.cta,
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

class _PulseDot extends StatefulWidget {
  const _PulseDot({required this.color, required this.icon});
  final Color color;
  final IconData icon;

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
            child: Icon(widget.icon, size: 18, color: c),
          ),
        ],
      ),
    );
  }
}
