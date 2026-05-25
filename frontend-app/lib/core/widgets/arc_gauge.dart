import 'dart:math' as math;

import 'package:flutter/material.dart';

/// A FitNook-style semicircle gauge (top half-arc) showing a 0–100% value over a
/// rounded track. Animates the sweep unless reduced motion is on. Place the
/// value text / label via [center].
class ArcGauge extends StatelessWidget {
  const ArcGauge({
    super.key,
    required this.percent,
    required this.color,
    required this.trackColor,
    this.size = 168,
    this.stroke = 16,
    this.center,
  });

  final double percent; // 0..100
  final Color color;
  final Color trackColor;
  final double size;
  final double stroke;
  final Widget? center;

  @override
  Widget build(BuildContext context) {
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final target = percent.clamp(0, 100) / 100.0;
    final radius = (size - stroke) / 2;
    final height = radius + stroke;
    return SizedBox(
      width: size,
      height: height + 6,
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: reduce ? target : 0.0, end: target),
        duration: reduce ? Duration.zero : const Duration(milliseconds: 750),
        curve: const Cubic(0.23, 1, 0.32, 1),
        builder: (context, value, _) => CustomPaint(
          size: Size(size, height),
          painter: _ArcPainter(
              value: value, color: color, track: trackColor, stroke: stroke),
          child: center == null
              ? null
              : Align(alignment: Alignment.bottomCenter, child: center),
        ),
      ),
    );
  }
}

class _ArcPainter extends CustomPainter {
  _ArcPainter({
    required this.value,
    required this.color,
    required this.track,
    required this.stroke,
  });
  final double value;
  final Color color;
  final Color track;
  final double stroke;

  @override
  void paint(Canvas canvas, Size size) {
    final radius = (size.width - stroke) / 2;
    final center = Offset(size.width / 2, radius + stroke / 2);
    final rect = Rect.fromCircle(center: center, radius: radius);
    final base = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.round
      ..color = track;
    final fill = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.round
      ..color = color;
    canvas.drawArc(rect, math.pi, math.pi, false, base);
    if (value > 0) {
      canvas.drawArc(rect, math.pi, math.pi * value, false, fill);
    }
  }

  @override
  bool shouldRepaint(_ArcPainter old) =>
      old.value != value || old.color != color || old.track != track;
}
