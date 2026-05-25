import 'package:flutter/material.dart';

import '../theme/app_spacing.dart';
import '../theme/app_tokens.dart';
import 'pressable.dart';

enum AuraButtonVariant { filled, tonal, ghost, destructive, success }

/// Primary action button. 52dp tall (≥ 48dp target), scale-on-press, and a
/// loading state that disables interaction and shows a spinner.
class AuraButton extends StatelessWidget {
  const AuraButton({
    super.key,
    required this.label,
    this.onPressed,
    this.icon,
    this.variant = AuraButtonVariant.filled,
    this.loading = false,
    this.expand = true,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final AuraButtonVariant variant;
  final bool loading;
  final bool expand;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final disabled = onPressed == null || loading;

    Color bg;
    Color fg;
    BoxBorder? border;
    switch (variant) {
      case AuraButtonVariant.filled:
        bg = t.accent;
        fg = t.onAccent;
        break;
      case AuraButtonVariant.tonal:
        bg = t.surfaceAlt;
        fg = t.ink;
        break;
      case AuraButtonVariant.ghost:
        bg = Colors.transparent;
        fg = t.ink;
        border = Border.all(color: t.border);
        break;
      case AuraButtonVariant.destructive:
        bg = t.absent;
        fg = Colors.white;
        break;
      case AuraButtonVariant.success:
        bg = t.present;
        fg = Colors.white;
        break;
    }

    final body = Container(
      height: 52,
      width: expand ? double.infinity : null,
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x24),
      decoration: BoxDecoration(
        color: bg == Colors.transparent
            ? bg
            : (disabled ? bg.withOpacity(0.45) : bg),
        borderRadius: AppRadii.rControl,
        border: border,
      ),
      child: Row(
        mainAxisSize: expand ? MainAxisSize.max : MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (loading)
            SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(fg),
              ),
            )
          else ...[
            if (icon != null)
              Padding(
                padding: const EdgeInsets.only(right: AppSpacing.x8),
                child: Icon(icon, size: 18, color: fg),
              ),
            Flexible(
              fit: FlexFit.loose,
              child: Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: textTheme.labelLarge
                    ?.copyWith(color: disabled ? fg.withOpacity(0.6) : fg),
              ),
            ),
          ],
        ],
      ),
    );

    return Semantics(
      button: true,
      enabled: !disabled,
      label: label,
      child: Pressable(onTap: disabled ? null : onPressed, child: body),
    );
  }
}
