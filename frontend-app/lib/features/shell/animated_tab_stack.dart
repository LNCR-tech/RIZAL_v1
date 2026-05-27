import 'package:flutter/material.dart';

import '../../core/theme/app_motion.dart';

/// Keeps every tab mounted (state preserved) and **cross-fades** between
/// the outgoing and incoming tab — the old view fades out as the new fades
/// in, with no slide and no blank flash. Instant when reduced motion is on.
///
/// Used by both the mobile [AppShell] and the tablet/desktop shell so the
/// transition between tabs is identical across layouts.
class AnimatedTabStack extends StatefulWidget {
  const AnimatedTabStack({
    super.key,
    required this.index,
    required this.children,
  });

  final int index;
  final List<Widget> children;

  @override
  State<AnimatedTabStack> createState() => _AnimatedTabStackState();
}

class _AnimatedTabStackState extends State<AnimatedTabStack>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: AppMotion.modal, value: 1);
  int _prev = 0;

  @override
  void didUpdateWidget(AnimatedTabStack old) {
    super.didUpdateWidget(old);
    if (old.index != widget.index) {
      _prev = old.index;
      _c.forward(from: 0);
    }
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return Stack(
      children: [
        for (var i = 0; i < widget.children.length; i++)
          Positioned.fill(
            child: AnimatedBuilder(
              animation: _c,
              builder: (context, child) {
                final isCurrent = i == widget.index;
                // The outgoing tab stays painted (fading out) until the
                // cross-fade finishes, so there's no blank flash.
                final isLeaving = i == _prev && _c.value < 1.0;
                final v = Curves.easeOut.transform(_c.value);
                final opacity = reduce
                    ? (isCurrent ? 1.0 : 0.0)
                    : (isCurrent ? v : 1 - v);
                return Offstage(
                  offstage: !(isCurrent || isLeaving),
                  child: IgnorePointer(
                    ignoring: !isCurrent,
                    child: Opacity(
                      opacity: opacity.clamp(0.0, 1.0),
                      child: child,
                    ),
                  ),
                );
              },
              child: TickerMode(
                enabled: i == widget.index,
                child: widget.children[i],
              ),
            ),
          ),
      ],
    );
  }
}
