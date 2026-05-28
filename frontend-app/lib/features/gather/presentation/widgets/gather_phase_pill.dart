import 'package:flutter/material.dart';

import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_tokens.dart';
import '../../../../shared/models/public_attendance.dart';

/// Phase status badge — sign-in / sign-out / closed — sized to sit next to a
/// title in a card or kiosk header. Color reads from the semantic token set
/// (never branded): sign-in = accent, sign-out = SG indigo-violet, closed =
/// muted. Always shows colour + icon (a11y), and the optional [tone]
/// `subtle` variant softens the fill for use over busy backgrounds.
class GatherPhasePill extends StatelessWidget {
  const GatherPhasePill({
    super.key,
    required this.event,
    this.tone = GatherPillTone.subtle,
    this.dense = false,
  });

  final NearbyEvent event;
  final GatherPillTone tone;
  final bool dense;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    final (Color base, IconData icon) = switch (event.attendancePhase) {
      'sign_in' => (t.accentDark, Icons.login_rounded),
      'sign_out' => (t.sg, Icons.logout_rounded),
      _ => (t.textMuted, Icons.do_not_disturb_on_outlined),
    };

    final bg = tone == GatherPillTone.solid
        ? base
        : base.withOpacity(t.isDark ? 0.22 : 0.16);
    final fg = tone == GatherPillTone.solid ? Colors.white : base;

    final padding = dense
        ? const EdgeInsets.symmetric(horizontal: AppSpacing.x8, vertical: 2)
        : const EdgeInsets.symmetric(
            horizontal: AppSpacing.x12, vertical: 4);

    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(AppRadii.pill),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: dense ? 12 : 14, color: fg),
          const SizedBox(width: 6),
          Text(
            event.phaseLabel,
            style: (dense ? textTheme.labelMedium : textTheme.labelLarge)
                ?.copyWith(color: fg),
          ),
        ],
      ),
    );
  }
}

enum GatherPillTone { subtle, solid }

/// Scope chip — "Campus-wide" or department/program names. When more than
/// [maxItems] scopes are present, the rest collapse into "+N".
class GatherScopeChip extends StatelessWidget {
  const GatherScopeChip({
    super.key,
    required this.event,
    this.maxItems = 2,
  });

  final NearbyEvent event;
  final int maxItems;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);

    final hasScope = event.programs.isNotEmpty || event.departments.isNotEmpty;
    if (!hasScope) {
      return _chip(
        context,
        icon: Icons.public_rounded,
        label: event.scopeLabel ?? 'Campus-wide',
        tint: t.textSecondary,
      );
    }

    // Programs are stricter than departments — surface them first.
    final names = [...event.programs, ...event.departments];
    final shown = names.take(maxItems).join(' · ');
    final extra = names.length - maxItems;
    final label = extra > 0 ? '$shown  +$extra' : shown;

    return _chip(
      context,
      icon: event.programs.isNotEmpty
          ? Icons.menu_book_rounded
          : Icons.account_tree_rounded,
      label: label,
      tint: t.textSecondary,
    );
  }

  Widget _chip(
    BuildContext context, {
    required IconData icon,
    required String label,
    required Color tint,
  }) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x12, vertical: 4),
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: BorderRadius.circular(AppRadii.pill),
        border: Border.all(color: t.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: tint),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: textTheme.labelMedium?.copyWith(color: tint),
            ),
          ),
        ],
      ),
    );
  }
}
