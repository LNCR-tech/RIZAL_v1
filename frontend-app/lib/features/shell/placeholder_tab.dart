import 'package:flutter/material.dart';

import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_tokens.dart';

/// Styled "coming soon" tab used for surfaces not yet built in this phase.
class PlaceholderTab extends StatelessWidget {
  const PlaceholderTab({
    super.key,
    required this.title,
    required this.icon,
    this.message,
  });

  final String title;
  final IconData icon;
  final String? message;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.x32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: t.surfaceAlt,
                borderRadius: BorderRadius.circular(AppRadii.card),
              ),
              child: Icon(icon, size: 32, color: t.textSecondary),
            ),
            const SizedBox(height: AppSpacing.x16),
            Text(title, style: textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.x8),
            Text(
              message ?? 'This area is coming in a later build.',
              textAlign: TextAlign.center,
              style: textTheme.bodyMedium?.copyWith(color: t.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}
