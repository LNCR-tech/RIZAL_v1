import 'package:flutter/material.dart';

import '../theme/app_tokens.dart';

/// Tiny pulsing accent dot — the only visual cue that a surface is
/// auto-refreshing in the background. Sized to sit next to a screen
/// title without competing with it. Honors reduced motion (renders a
/// static dot when the OS asks for less animation).
class LiveDot extends StatefulWidget {
  const LiveDot({
    super.key,
    this.size = 6,
    this.color,
    this.tooltip = 'Updating live',
  });

  final double size;
  final Color? color;
  final String tooltip;

  @override
  State<LiveDot> createState() => _LiveDotState();
}

class _LiveDotState extends State<LiveDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1400),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final color = widget.color ?? t.accentDark;
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    final dot = AnimatedBuilder(
      animation: _c,
      builder: (context, _) {
        final scale = reduce ? 1.0 : (0.85 + _c.value * 0.30);
        final opacity = reduce ? 1.0 : (0.55 + _c.value * 0.45);
        return Opacity(
          opacity: opacity,
          child: Transform.scale(
            scale: scale,
            child: Container(
              width: widget.size,
              height: widget.size,
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
                boxShadow: reduce
                    ? null
                    : [
                        BoxShadow(
                          color: color.withOpacity(0.45),
                          blurRadius: widget.size * 0.8,
                        ),
                      ],
              ),
            ),
          ),
        );
      },
    );

    return Tooltip(
      message: widget.tooltip,
      child: SizedBox(
        // Reserve square space so the surrounding text doesn't jitter as
        // the dot scales 0.85 → 1.15 each pulse.
        width: widget.size * 1.5,
        height: widget.size * 1.5,
        child: Center(child: dot),
      ),
    );
  }

}
