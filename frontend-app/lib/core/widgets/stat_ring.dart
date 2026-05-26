import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../theme/app_motion.dart';
import '../theme/app_tokens.dart';
import '../theme/app_typography.dart';

/// Animated radial gauge for a percentage (e.g. attendance rate). Sweeps from
/// 0 → value on first build; center shows the value in mono figures.
class StatRing extends StatelessWidget {
  const StatRing({
    super.key,
    required this.percent,
    this.size = 120,
    this.label,
    this.color,
    this.stroke = 12,
  });

  final double percent;
  final double size;
  final String? label;
  final Color? color;
  final double stroke;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final c = color ?? t.accent;
    final target = percent.clamp(0, 100).toDouble();
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    return SizedBox(
      width: size,
      height: size,
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: reduce ? target : 0, end: target),
        duration: reduce ? Duration.zero : const Duration(milliseconds: 700),
        curve: AppMotion.easeOut,
        builder: (context, value, _) {
          return Stack(
            alignment: Alignment.center,
            children: [
              PieChart(
                PieChartData(
                  startDegreeOffset: -90,
                  sectionsSpace: 0,
                  centerSpaceRadius: (size / 2) - stroke,
                  sections: [
                    PieChartSectionData(
                        value: value, color: c, radius: stroke, showTitle: false),
                    PieChartSectionData(
                        value: 100 - value,
                        color: t.surfaceAlt,
                        radius: stroke,
                        showTitle: false),
                  ],
                ),
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('${value.round()}%',
                      style: AppTypography.mono(
                          size: size * 0.2,
                          weight: FontWeight.w700,
                          color: t.ink)),
                  if (label != null)
                    Text(label!,
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: t.textSecondary)),
                ],
              ),
            ],
          );
        },
      ),
    );
  }
}
