import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../theme/app_spacing.dart';
import '../theme/app_tokens.dart';
import '../theme/app_typography.dart';
import 'aura_card.dart';
import 'pressable.dart';
import 'stat_ring.dart';

/// Accent-tinted hero: a big metric with an optional progress ring (or an icon
/// badge when there's no natural percentage). Shared across workspace homes.
class HeroRingCard extends StatelessWidget {
  const HeroRingCard({
    super.key,
    required this.title,
    required this.value,
    required this.footnote,
    this.percent,
    this.icon = Icons.insights_rounded,
    this.ringColor,
  });
  final String title;
  final String value;
  final String footnote;
  final double? percent;
  final IconData icon;
  final Color? ringColor;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final ring = ringColor ?? t.accentDark;

    return AuraCard(
      color: t.accent.withOpacity(0.14),
      padding: const EdgeInsets.all(AppSpacing.x20),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: textTheme.labelLarge
                        ?.copyWith(color: t.textSecondary)),
                const SizedBox(height: AppSpacing.x8),
                Text(value,
                    style: AppTypography.mono(
                        size: 40, weight: FontWeight.w800, color: t.ink)),
                Text(footnote,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style:
                        textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.x16),
          if (percent != null)
            StatRing(
                percent: percent!.clamp(0, 100).toDouble(),
                size: 92,
                stroke: 11,
                color: ring)
          else
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: ring.withOpacity(0.16),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: ring, size: 32),
            ),
        ],
      ),
    );
  }
}

/// Compact metric card with an icon chip, big mono number, and a label.
class MetricChipCard extends StatelessWidget {
  const MetricChipCard({
    super.key,
    required this.icon,
    required this.label,
    required this.value,
    required this.tint,
  });
  final IconData icon;
  final String label;
  final String value;
  final Color tint;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AuraCard(
      padding: const EdgeInsets.all(AppSpacing.x16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
                color: tint.withOpacity(0.16),
                borderRadius: BorderRadius.circular(AppRadii.control)),
            child: Icon(icon, color: tint, size: 22),
          ),
          const SizedBox(height: AppSpacing.x16),
          Text(value,
              style: AppTypography.mono(
                  size: 26, weight: FontWeight.w700, color: t.ink)),
          const SizedBox(height: 2),
          Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: textTheme.bodySmall?.copyWith(color: t.textSecondary)),
        ],
      ),
    );
  }
}

/// Tappable action row with a tinted icon chip, label, optional subtitle.
class DashboardActionRow extends StatelessWidget {
  const DashboardActionRow({
    super.key,
    required this.icon,
    required this.label,
    required this.onTap,
    this.subtitle,
    this.tint,
  });
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final String? subtitle;
  final Color? tint;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final c = tint ?? t.accentDark;
    return Pressable(
      onTap: onTap,
      child: AuraCard(
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                  color: c.withOpacity(0.16),
                  borderRadius: BorderRadius.circular(AppRadii.control)),
              child: Icon(icon, color: c),
            ),
            const SizedBox(width: AppSpacing.x16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: textTheme.titleLarge),
                  if (subtitle != null)
                    Text(subtitle!,
                        style: textTheme.bodySmall
                            ?.copyWith(color: t.textSecondary)),
                ],
              ),
            ),
            Icon(Icons.chevron_right_rounded, color: t.textMuted),
          ],
        ),
      ),
    );
  }
}

/// Simple bar chart with a count + label under each bar and faint track bars.
class DashboardBarChart extends StatelessWidget {
  const DashboardBarChart({
    super.key,
    required this.labels,
    required this.values,
    required this.colors,
    this.height = 150,
    this.suffix = '',
  });
  final List<String> labels;
  final List<num> values;
  final List<Color> colors;
  final double height;
  final String suffix;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final maxV = values.fold<double>(0, (p, c) => c > p ? c.toDouble() : p);
    final maxY = (maxV < 1 ? 1 : maxV) * 1.3;

    return SizedBox(
      height: height,
      child: BarChart(
        BarChartData(
          alignment: BarChartAlignment.spaceAround,
          maxY: maxY,
          minY: 0,
          barTouchData: BarTouchData(enabled: false),
          gridData: const FlGridData(show: false),
          borderData: FlBorderData(show: false),
          titlesData: FlTitlesData(
            leftTitles:
                const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles:
                const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles:
                const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 44,
                getTitlesWidget: (value, m) {
                  final i = value.toInt();
                  if (i < 0 || i >= labels.length) {
                    return const SizedBox.shrink();
                  }
                  return Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('${values[i]}$suffix',
                            style: AppTypography.mono(
                                size: 13,
                                weight: FontWeight.w700,
                                color: t.ink)),
                        Text(labels[i],
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: textTheme.bodySmall
                                ?.copyWith(color: t.textMuted)),
                      ],
                    ),
                  );
                },
              ),
            ),
          ),
          barGroups: [
            for (var i = 0; i < labels.length; i++)
              BarChartGroupData(x: i, barRods: [
                BarChartRodData(
                  toY: values[i].toDouble(),
                  color: colors[i % colors.length],
                  width: 26,
                  borderRadius:
                      const BorderRadius.vertical(top: Radius.circular(8)),
                  backDrawRodData: BackgroundBarChartRodData(
                      show: true, toY: maxY, color: t.surfaceAlt),
                ),
              ]),
          ],
        ),
        swapAnimationDuration:
            reduce ? Duration.zero : const Duration(milliseconds: 450),
      ),
    );
  }
}
