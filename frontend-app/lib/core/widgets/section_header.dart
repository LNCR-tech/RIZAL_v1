import 'package:flutter/material.dart';

import '../theme/app_spacing.dart';
import '../theme/app_tokens.dart';
import 'pressable.dart';

/// Title + optional trailing action for a content section.
class SectionHeader extends StatelessWidget {
  const SectionHeader({
    super.key,
    required this.title,
    this.action,
    this.onAction,
  });

  final String title;
  final String? action;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(child: Text(title, style: textTheme.headlineSmall)),
          if (action != null)
            Pressable(
              onTap: onAction,
              child: Padding(
                padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.x8, vertical: AppSpacing.x4),
                child: Text(action!,
                    style: textTheme.labelLarge?.copyWith(color: t.textSecondary)),
              ),
            ),
        ],
      ),
    );
  }
}
