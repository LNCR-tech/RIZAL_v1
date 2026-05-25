import 'package:flutter/material.dart';

import '../theme/app_spacing.dart';
import '../theme/app_tokens.dart';
import 'pressable.dart';

/// Bento surface — rounded 24, hairline border, soft shadow in light mode.
/// Optional [onTap] adds press feedback; optional [heroTag] enables a shared
/// element transition into a detail screen.
class AuraCard extends StatelessWidget {
  const AuraCard({
    super.key,
    required this.child,
    this.onTap,
    this.padding = AppSpacing.card,
    this.heroTag,
    this.color,
  });

  final Widget child;
  final VoidCallback? onTap;
  final EdgeInsets padding;
  final Object? heroTag;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);

    Widget card = Container(
      padding: padding,
      decoration: BoxDecoration(
        color: color ?? t.surface,
        borderRadius: AppRadii.rCard,
        border: Border.all(color: t.border),
        boxShadow: AppElevation.card(t.brightness),
      ),
      child: child,
    );

    if (heroTag != null) {
      card = Hero(
        tag: heroTag!,
        child: Material(type: MaterialType.transparency, child: card),
      );
    }

    return onTap == null ? card : Pressable(onTap: onTap, child: card);
  }
}
