import 'package:flutter/material.dart';

import '../theme/app_spacing.dart';
import '../theme/app_tokens.dart';
import 'aura_card.dart';
import 'pressable.dart';

/// An iOS-Settings-style row: a soft colored icon tile, a title (+ optional
/// subtitle), and a trailing widget or chevron. Scales slightly on press.
class SettingsTile extends StatelessWidget {
  const SettingsTile({
    super.key,
    required this.icon,
    required this.iconColor,
    required this.title,
    this.subtitle,
    this.trailing,
    this.onTap,
    this.showChevron = true,
  });
  final IconData icon;
  final Color iconColor;
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final VoidCallback? onTap;
  final bool showChevron;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final row = Padding(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x16, vertical: AppSpacing.x12),
      child: Row(
        children: [
          Container(
            width: 30,
            height: 30,
            decoration: BoxDecoration(
              color: iconColor,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: Colors.white, size: 18),
          ),
          const SizedBox(width: AppSpacing.x12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: textTheme.bodyLarge),
                if (subtitle != null)
                  Text(subtitle!,
                      style: textTheme.bodySmall
                          ?.copyWith(color: t.textSecondary)),
              ],
            ),
          ),
          if (trailing != null)
            trailing!
          else if (showChevron && onTap != null)
            Icon(Icons.chevron_right_rounded, color: t.textMuted),
        ],
      ),
    );
    return onTap == null ? row : Pressable(onTap: onTap, scale: 0.99, child: row);
  }
}

/// A grouped, inset settings section: an optional header label above a single
/// card whose tiles are separated by hairline dividers (indented past the icon).
class SettingsSection extends StatelessWidget {
  const SettingsSection({super.key, this.header, required this.tiles});
  final String? header;
  final List<Widget> tiles;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (header != null)
          Padding(
            padding: const EdgeInsets.only(
                left: AppSpacing.x4, bottom: AppSpacing.x8),
            child: Text(header!.toUpperCase(),
                style: textTheme.labelSmall?.copyWith(
                    color: t.textMuted, letterSpacing: 0.8)),
          ),
        AuraCard(
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              for (var i = 0; i < tiles.length; i++) ...[
                tiles[i],
                if (i != tiles.length - 1)
                  Divider(
                      height: 1,
                      thickness: 1,
                      indent: 58,
                      color: t.border),
              ],
            ],
          ),
        ),
      ],
    );
  }
}
