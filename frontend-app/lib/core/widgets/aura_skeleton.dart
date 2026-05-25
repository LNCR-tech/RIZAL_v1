import 'package:flutter/material.dart';

import '../theme/app_tokens.dart';

/// Gently pulsing placeholder for async content. Reserve real layout space
/// with these to avoid content jumping on load.
class AuraSkeleton extends StatefulWidget {
  const AuraSkeleton({
    super.key,
    this.width,
    this.height = 16,
    this.radius = 8,
  });

  final double? width;
  final double height;
  final double radius;

  @override
  State<AuraSkeleton> createState() => _AuraSkeletonState();
}

class _AuraSkeletonState extends State<AuraSkeleton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1100),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (reduce) {
      return _box(t.surfaceAlt.withOpacity(0.6));
    }
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) =>
          _box(t.surfaceAlt.withOpacity(0.4 + _controller.value * 0.4)),
    );
  }

  Widget _box(Color color) => Container(
        width: widget.width,
        height: widget.height,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(widget.radius),
        ),
      );
}
