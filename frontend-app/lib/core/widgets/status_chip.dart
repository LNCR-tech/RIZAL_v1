import 'package:flutter/material.dart';

import '../theme/app_spacing.dart';
import '../theme/app_tokens.dart';

/// Pill that conveys status with BOTH color and an icon (never color alone).
class StatusChip extends StatelessWidget {
  const StatusChip({super.key, required this.label, required this.color, this.icon});

  final String label;
  final Color color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x12, vertical: AppSpacing.x4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.14),
        borderRadius: AppRadii.rPill,
        border: Border.all(color: color.withOpacity(0.30)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null)
            Padding(
              padding: const EdgeInsets.only(right: 4),
              child: Icon(icon, size: 14, color: color),
            ),
          Text(label,
              style: Theme.of(context)
                  .textTheme
                  .labelMedium
                  ?.copyWith(color: color)),
        ],
      ),
    );
  }

  /// Map an attendance/event/sanction status string → a themed chip.
  factory StatusChip.forStatus(BuildContext context, String status) {
    final t = AppTokens.of(context);
    final s = status.toLowerCase().replaceAll('-', '_');
    switch (s) {
      case 'present':
      case 'compliant':
      case 'complied':
        return StatusChip(
            label: _cap(status), color: t.present, icon: Icons.check_circle_rounded);
      case 'late':
      case 'tardy':
        return StatusChip(
            label: _cap(status), color: t.tardy, icon: Icons.schedule_rounded);
      case 'absent':
      case 'non_compliant':
        return StatusChip(
            label: _cap(status), color: t.absent, icon: Icons.cancel_rounded);
      case 'excused':
        return StatusChip(
            label: _cap(status), color: t.excused, icon: Icons.event_busy_rounded);
      case 'at_risk':
        return StatusChip(
            label: 'At risk', color: t.atRisk, icon: Icons.warning_amber_rounded);
      case 'pending':
        return StatusChip(
            label: 'Pending', color: t.atRisk, icon: Icons.hourglass_bottom_rounded);
      case 'ongoing':
        return StatusChip(
            label: 'Ongoing', color: t.present, icon: Icons.play_circle_rounded);
      case 'upcoming':
        return StatusChip(
            label: 'Upcoming', color: t.textSecondary, icon: Icons.event_rounded);
      case 'completed':
        return StatusChip(
            label: 'Completed', color: t.textSecondary, icon: Icons.task_alt_rounded);
      case 'cancelled':
      case 'canceled':
        return StatusChip(
            label: 'Cancelled', color: t.absent, icon: Icons.block_rounded);
      default:
        return StatusChip(label: _cap(status), color: t.textSecondary);
    }
  }

  static String _cap(String s) {
    if (s.isEmpty) return s;
    final x = s.replaceAll('_', ' ');
    return x[0].toUpperCase() + x.substring(1);
  }
}
