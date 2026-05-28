import 'package:flutter/material.dart';

/// A calm two-ring pulse drawn over the camera preview while the scan loop is
/// active. Two concentric rings ride out from the centre on slightly offset
/// phases, fade as they grow, then loop. Honors reduced-motion (renders a
/// single static outline). Cheap — only `opacity` + `transform`, no layout
/// changes, runs on the GPU.
class GatherScanningRing extends StatefulWidget {
  const GatherScanningRing({
    super.key,
    required this.color,
    this.size = 220,
    this.active = true,
  });

  final Color color;
  final double size;
  final bool active;

  @override
  State<GatherScanningRing> createState() => _GatherScanningRingState();
}

class _GatherScanningRingState extends State<GatherScanningRing>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1800),
  );

  bool _reduce = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (reduce != _reduce) {
      _reduce = reduce;
      _sync();
    }
  }

  @override
  void didUpdateWidget(covariant GatherScanningRing oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active != oldWidget.active) _sync();
  }

  void _sync() {
    if (_reduce || !widget.active) {
      _c.stop();
      _c.value = 0;
    } else if (!_c.isAnimating) {
      _c.repeat();
    }
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final color = widget.color;
    if (_reduce || !widget.active) {
      return IgnorePointer(
        ignoring: true,
        child: Center(
          child: _Ring(color: color.withOpacity(0.35), size: widget.size),
        ),
      );
    }

    return IgnorePointer(
      ignoring: true,
      child: Center(
        child: SizedBox(
          width: widget.size + 60,
          height: widget.size + 60,
          child: AnimatedBuilder(
            animation: _c,
            builder: (context, _) {
              final a = _c.value;
              // Two ripples 180° out of phase so the corner of one waves the
              // other in. Each scales from 0.85 → 1.1 and fades 0.55 → 0.
              final p1 = a;
              final p2 = (a + 0.5) % 1.0;
              return Stack(
                alignment: Alignment.center,
                children: [
                  _ripple(p1, color),
                  _ripple(p2, color),
                  _Ring(color: color, size: widget.size),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _ripple(double p, Color color) {
    final scale = 0.85 + p * 0.25;
    final opacity = (1.0 - p).clamp(0.0, 1.0) * 0.55;
    return Opacity(
      opacity: opacity,
      child: Transform.scale(
        scale: scale,
        child: _Ring(color: color, size: widget.size, width: 1.4),
      ),
    );
  }
}

class _Ring extends StatelessWidget {
  const _Ring({required this.color, required this.size, this.width = 2});
  final Color color;
  final double size;
  final double width;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(color: color, width: width),
      ),
    );
  }
}

/// Floating capsule that reads "Scanning…" with a small spinner. Sits over
/// the camera preview while the scan loop is running.
class GatherScanningChip extends StatelessWidget {
  const GatherScanningChip({
    super.key,
    required this.accent,
    this.label = 'Scanning…',
  });
  final Color accent;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.55),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 12,
            height: 12,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(accent),
            ),
          ),
          const SizedBox(width: 8),
          Text(label,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.1,
              )),
        ],
      ),
    );
  }
}

/// Reticle / framing brackets in each of the four corners of the camera view.
/// A subtle, kiosk-y "we're looking" affordance. Paint-only, no animation.
class GatherFramingBrackets extends StatelessWidget {
  const GatherFramingBrackets({
    super.key,
    required this.color,
    this.inset = 18,
    this.length = 36,
    this.thickness = 2.4,
  });

  final Color color;
  final double inset;
  final double length;
  final double thickness;

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      ignoring: true,
      child: CustomPaint(
        size: Size.infinite,
        painter: _BracketPainter(
          color: color,
          inset: inset,
          length: length,
          thickness: thickness,
        ),
      ),
    );
  }
}

class _BracketPainter extends CustomPainter {
  _BracketPainter({
    required this.color,
    required this.inset,
    required this.length,
    required this.thickness,
  });
  final Color color;
  final double inset;
  final double length;
  final double thickness;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeWidth = thickness;

    void corner(Offset o, bool right, bool bottom) {
      final dx = right ? -length : length;
      final dy = bottom ? -length : length;
      canvas.drawLine(o, o.translate(dx, 0), paint);
      canvas.drawLine(o, o.translate(0, dy), paint);
    }

    corner(Offset(inset, inset), false, false);
    corner(Offset(size.width - inset, inset), true, false);
    corner(Offset(inset, size.height - inset), false, true);
    corner(Offset(size.width - inset, size.height - inset), true, true);
  }

  @override
  bool shouldRepaint(_BracketPainter old) =>
      old.color != color ||
      old.inset != inset ||
      old.length != length ||
      old.thickness != thickness;
}
