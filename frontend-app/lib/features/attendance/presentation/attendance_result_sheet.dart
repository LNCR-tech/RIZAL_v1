import 'package:flutter/material.dart';

import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../shared/models/attendance.dart';
import '../../../shared/utils/formatting.dart';

/// Bottom sheet shown after a successful scan.
class AttendanceResultSheet extends StatelessWidget {
  const AttendanceResultSheet({super.key, required this.result});
  final FaceScanResult result;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    final title = result.isTimeIn
        ? 'Checked in'
        : (result.isTimeOut ? 'Signed out' : 'Recorded');
    final accent = result.isTimeIn ? t.present : t.accent;
    final stamp = result.isTimeOut ? result.timeOut : result.timeIn;

    return Container(
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: AppRadii.rSheet,
      ),
      padding: EdgeInsets.fromLTRB(AppSpacing.x24, AppSpacing.x16,
          AppSpacing.x24, AppSpacing.x24 + MediaQuery.of(context).padding.bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
                color: t.border, borderRadius: BorderRadius.circular(2)),
          ),
          const SizedBox(height: AppSpacing.x24),
          Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              color: accent.withOpacity(0.16),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.check_rounded, size: 38, color: accent),
          ),
          const SizedBox(height: AppSpacing.x16),
          Text(title, style: textTheme.headlineSmall),
          if (result.studentName != null) ...[
            const SizedBox(height: 2),
            Text(result.studentName!,
                style: textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
          ],
          if (stamp != null) ...[
            const SizedBox(height: AppSpacing.x8),
            Text(fmtTime(stamp),
                style: textTheme.bodyLarge?.copyWith(color: t.textSecondary)),
          ],
          if (result.message != null) ...[
            const SizedBox(height: AppSpacing.x12),
            Text(result.message!,
                textAlign: TextAlign.center,
                style: textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
          ],
          const SizedBox(height: AppSpacing.x24),
          AuraButton(
            label: 'Done',
            onPressed: () => Navigator.of(context).pop(),
          ),
        ],
      ),
    );
  }
}
