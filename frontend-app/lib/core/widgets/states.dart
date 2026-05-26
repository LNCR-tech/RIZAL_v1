import 'package:flutter/material.dart';

import '../theme/app_spacing.dart';
import '../theme/app_tokens.dart';
import 'aura_button.dart';
import 'aura_card.dart';
import 'aura_skeleton.dart';

/// Friendly empty state.
class EmptyState extends StatelessWidget {
  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    this.message,
  });
  final IconData icon;
  final String title;
  final String? message;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
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
            child: Icon(icon, size: 30, color: t.textSecondary),
          ),
          const SizedBox(height: AppSpacing.x16),
          Text(title, textAlign: TextAlign.center, style: textTheme.titleLarge),
          if (message != null) ...[
            const SizedBox(height: AppSpacing.x8),
            Text(message!,
                textAlign: TextAlign.center,
                style: textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
          ],
        ],
      ),
    );
  }
}

/// Error state with optional retry.
class ErrorView extends StatelessWidget {
  const ErrorView({super.key, required this.message, this.onRetry});
  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.x32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.cloud_off_rounded, size: 34, color: t.textMuted),
          const SizedBox(height: AppSpacing.x16),
          Text('Something went wrong',
              textAlign: TextAlign.center, style: textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x8),
          Text(message,
              textAlign: TextAlign.center,
              style: textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
          if (onRetry != null) ...[
            const SizedBox(height: AppSpacing.x20),
            AuraButton(
              label: 'Try again',
              icon: Icons.refresh_rounded,
              variant: AuraButtonVariant.tonal,
              expand: false,
              onPressed: onRetry,
            ),
          ],
        ],
      ),
    );
  }
}

/// Skeleton placeholder list of cards for loading states.
class LoadingCardList extends StatelessWidget {
  const LoadingCardList({super.key, this.count = 4});
  final int count;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (var i = 0; i < count; i++)
          const Padding(
            padding: EdgeInsets.only(bottom: AppSpacing.x12),
            child: AuraCard(
              child: Row(
                children: [
                  AuraSkeleton(width: 52, height: 56, radius: 12),
                  SizedBox(width: AppSpacing.x16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        AuraSkeleton(width: 160, height: 16),
                        SizedBox(height: 10),
                        AuraSkeleton(width: 110, height: 12),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}
