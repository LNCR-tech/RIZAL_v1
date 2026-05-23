import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_tokens.dart';

/// A chart the assistant asked the app to render — decoded from the backend's
/// `visualization` SSE event (a Chart.js-style payload:
/// `{type, title, payload:{labels, datasets:[{label, data}]}, footer}`).
class ChartSpec {
  const ChartSpec({
    required this.type,
    required this.title,
    required this.footer,
    required this.labels,
    required this.series,
    required this.seriesLabels,
  });

  final String type; // bar | line | pie | doughnut
  final String title;
  final String footer;
  final List<String> labels;
  final List<List<double>> series; // one list of values per dataset
  final List<String> seriesLabels; // one name per dataset

  bool get isPie => type == 'pie' || type == 'doughnut';

  /// Defensive parse of the `visual` object (model output can be messy).
  static ChartSpec? tryParse(Map<String, dynamic>? v) {
    if (v == null) return null;
    final payload = v['payload'];
    if (payload is! Map) return null;
    final labels = [
      for (final l in (payload['labels'] as List? ?? const []))
        l?.toString() ?? '',
    ];
    final series = <List<double>>[];
    final seriesLabels = <String>[];
    for (final ds in (payload['datasets'] as List? ?? const [])) {
      if (ds is! Map) continue;
      series.add([
        for (final n in (ds['data'] as List? ?? const [])) _toDouble(n),
      ]);
      seriesLabels.add(ds['label']?.toString() ?? '');
    }
    if (labels.isEmpty || series.isEmpty || series.first.isEmpty) return null;
    return ChartSpec(
      type: (v['type']?.toString() ?? 'bar').toLowerCase().trim(),
      title: v['title']?.toString() ?? '',
      footer: v['footer']?.toString() ?? '',
      labels: labels,
      series: series,
      seriesLabels: seriesLabels,
    );
  }

  static double _toDouble(dynamic n) =>
      n is num ? n.toDouble() : double.tryParse(n?.toString() ?? '') ?? 0;
}

/// Renders a [ChartSpec] inside a chat bubble — themed, no touch interactions.
class AssistantChart extends StatelessWidget {
  const AssistantChart({super.key, required this.spec});
  final ChartSpec spec;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      margin: const EdgeInsets.only(top: AppSpacing.x12),
      padding: const EdgeInsets.all(AppSpacing.x16),
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: BorderRadius.circular(AppRadii.card),
        border: Border.all(color: t.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (spec.title.isNotEmpty) ...[
            Text(spec.title, style: textTheme.titleMedium),
            const SizedBox(height: AppSpacing.x16),
          ],
          SizedBox(height: 200, child: _body(t)),
          if (_showLegend) ...[
            const SizedBox(height: AppSpacing.x12),
            _legend(context, t),
          ],
          if (spec.footer.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x8),
            Text(spec.footer,
                style: textTheme.bodySmall?.copyWith(color: t.textSecondary)),
          ],
        ],
      ),
    );
  }

  bool get _showLegend => spec.isPie || spec.series.length > 1;

  // Categorical palette pulled from theme tokens (no hardcoded brand colors).
  List<Color> _palette(AppTokens t) =>
      [t.accentDark, t.ssg, t.present, t.tardy, t.sg, t.atRisk, t.excused, t.absent];

  Color _color(AppTokens t, int i) {
    final p = _palette(t);
    return p[i % p.length];
  }

  Widget _body(AppTokens t) {
    switch (spec.type) {
      case 'pie':
      case 'doughnut':
        return PieChart(_pieData(t));
      case 'line':
        return LineChart(_lineData(t));
      default:
        return BarChart(_barData(t));
    }
  }

  // --- Bar ---
  BarChartData _barData(AppTokens t) {
    final multi = spec.series.length > 1;
    final groups = <BarChartGroupData>[];
    for (var i = 0; i < spec.labels.length; i++) {
      final rods = <BarChartRodData>[];
      for (var s = 0; s < spec.series.length; s++) {
        final data = spec.series[s];
        rods.add(BarChartRodData(
          toY: i < data.length ? data[i] : 0,
          color: _color(t, multi ? s : i),
          width: multi ? 8 : 14,
          borderRadius: BorderRadius.circular(4),
        ));
      }
      groups.add(BarChartGroupData(x: i, barRods: rods));
    }
    return BarChartData(
      minY: 0,
      barGroups: groups,
      alignment: BarChartAlignment.spaceAround,
      gridData: _grid(t),
      borderData: FlBorderData(show: false),
      titlesData: _titles(t),
      barTouchData: BarTouchData(enabled: false),
    );
  }

  // --- Line ---
  LineChartData _lineData(AppTokens t) {
    final bars = <LineChartBarData>[];
    for (var s = 0; s < spec.series.length; s++) {
      final data = spec.series[s];
      bars.add(LineChartBarData(
        spots: [for (var i = 0; i < data.length; i++) FlSpot(i.toDouble(), data[i])],
        isCurved: true,
        color: _color(t, s),
        barWidth: 3,
        dotData: FlDotData(show: data.length <= 12),
        belowBarData: BarAreaData(
          show: !_showLegend,
          color: _color(t, s).withOpacity(0.12),
        ),
      ));
    }
    return LineChartData(
      minY: 0,
      lineBarsData: bars,
      gridData: _grid(t),
      borderData: FlBorderData(show: false),
      titlesData: _titles(t),
      lineTouchData: const LineTouchData(enabled: false),
    );
  }

  // --- Pie / doughnut (first dataset) ---
  PieChartData _pieData(AppTokens t) {
    final data = spec.series.first;
    final total = data.fold<double>(0, (a, b) => a + b);
    return PieChartData(
      sectionsSpace: 2,
      centerSpaceRadius: spec.type == 'doughnut' ? 42 : 0,
      sections: [
        for (var i = 0; i < data.length; i++)
          PieChartSectionData(
            value: data[i],
            color: _color(t, i),
            radius: 64,
            title: total > 0 && data[i] / total >= 0.08
                ? '${(data[i] / total * 100).round()}%'
                : '',
            titleStyle: const TextStyle(
                color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700),
          ),
      ],
    );
  }

  // --- Shared axis + grid ---
  FlGridData _grid(AppTokens t) => FlGridData(
        show: true,
        drawVerticalLine: false,
        getDrawingHorizontalLine: (value) =>
            FlLine(color: t.border.withOpacity(0.7), strokeWidth: 1),
      );

  FlTitlesData _titles(AppTokens t) {
    final style = TextStyle(color: t.textMuted, fontSize: 10);
    final step = (spec.labels.length / 6).ceil().clamp(1, 9999);
    return FlTitlesData(
      topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      leftTitles: AxisTitles(
        sideTitles: SideTitles(
          showTitles: true,
          reservedSize: 34,
          getTitlesWidget: (value, meta) =>
              Text(_fmtNum(value), style: style),
        ),
      ),
      bottomTitles: AxisTitles(
        sideTitles: SideTitles(
          showTitles: true,
          reservedSize: 28,
          interval: 1,
          getTitlesWidget: (value, meta) {
            final i = value.round();
            if ((value - i).abs() > 0.01) return const SizedBox.shrink();
            if (i < 0 || i >= spec.labels.length) return const SizedBox.shrink();
            if (i % step != 0) return const SizedBox.shrink();
            return Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(_shortLabel(spec.labels[i]),
                  style: style, maxLines: 1, overflow: TextOverflow.ellipsis),
            );
          },
        ),
      ),
    );
  }

  Widget _legend(BuildContext context, AppTokens t) {
    final textTheme = Theme.of(context).textTheme;
    final items = spec.isPie ? spec.labels : spec.seriesLabels;
    return Wrap(
      spacing: AppSpacing.x16,
      runSpacing: AppSpacing.x8,
      children: [
        for (var i = 0; i < items.length; i++)
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 10,
                height: 10,
                decoration:
                    BoxDecoration(color: _color(t, i), shape: BoxShape.circle),
              ),
              const SizedBox(width: 6),
              Text(items[i].isEmpty ? '—' : items[i],
                  style: textTheme.bodySmall?.copyWith(color: t.textSecondary)),
            ],
          ),
      ],
    );
  }

  static String _fmtNum(double v) =>
      v == v.roundToDouble() ? v.toInt().toString() : v.toStringAsFixed(1);

  static String _shortLabel(String s) =>
      s.length <= 7 ? s : '${s.substring(0, 6)}…';
}
