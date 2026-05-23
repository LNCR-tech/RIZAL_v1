import 'package:flutter/material.dart';

import '../theme/app_motion.dart';

/// Plays once on first mount: the child rises up + fades in, staggered by
/// [index]. A no-op when reduced motion is active (renders instantly).
class RiseIn extends StatefulWidget {
  const RiseIn({super.key, required this.child, this.index = 0, this.dy = 18});
  final Widget child;
  final int index;
  final double dy;

  @override
  State<RiseIn> createState() => _RiseInState();
}

class _RiseInState extends State<RiseIn> with SingleTickerProviderStateMixin {
  // Shared reveal window. The head of a freshly-built list (index 0) opens it;
  // rows that mount later — i.e. scrolled into view — fall outside it and render
  // instantly, so long lists scroll smoothly (no per-row animation/Opacity).
  static DateTime _revealUntil = DateTime.fromMillisecondsSinceEpoch(0);

  late final AnimationController _c = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 460));
  late final Animation<double> _curved =
      CurvedAnimation(parent: _c, curve: AppMotion.easeOut);
  bool _scheduled = false;
  bool _animate = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_scheduled) return;
    _scheduled = true;

    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final now = DateTime.now();
    if (widget.index == 0 && now.isAfter(_revealUntil)) {
      _revealUntil = now.add(const Duration(milliseconds: 1100));
    }
    if (reduce || now.isAfter(_revealUntil)) {
      _c.value = 1; // reduced motion, or scrolled into view later → instant
      return;
    }

    _animate = true;
    final delayMs =
        widget.index.clamp(0, 12) * AppMotion.staggerStep.inMilliseconds;
    Future.delayed(Duration(milliseconds: delayMs), () {
      if (mounted) _c.forward();
    });
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Non-animated rows skip the Opacity/Transform layers entirely.
    if (!_animate) return widget.child;
    return AnimatedBuilder(
      animation: _curved,
      builder: (context, child) {
        final v = _curved.value;
        return Opacity(
          opacity: v,
          child: Transform.translate(
            offset: Offset(0, (1 - v) * widget.dy),
            child: child,
          ),
        );
      },
      child: widget.child,
    );
  }
}

/// Wraps a list of column/list children in staggered [RiseIn] reveals.
/// Pure spacer `SizedBox`es are passed through so the cadence stays tight.
List<Widget> staggered(List<Widget> children) {
  var i = 0;
  return [
    for (final c in children)
      if (c is SizedBox && c.child == null)
        c
      else
        RiseIn(index: i++, child: c),
  ];
}
