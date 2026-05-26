import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_branding_controller.dart';
import '../../core/theme/app_motion.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_tokens.dart';
import '../../core/theme/app_typography.dart';
import '../../core/widgets/app_brand_mark.dart';
import '../../core/widgets/aura_card.dart';

/// The "App appearance" section in Account.
///
/// One focused card: a live preview row at the top, then two
/// `SegmentedButton<bool>` controls for the brand mark and app name.
/// Calm hierarchy — preview leads, controls support, the OS-icon note
/// closes. Nothing is hardcoded; every color comes from [AppTokens] and
/// every motion through [AppMotion].
class AppAppearanceSection extends ConsumerWidget {
  const AppAppearanceSection({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final pref = ref.watch(appBrandingProvider);
    final ctrl = ref.read(appBrandingProvider.notifier);
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    final hasLogo = pref.hasLogo;
    final hasCode = pref.hasCode;
    final logoLabel =
        hasLogo ? (pref.schoolName ?? 'School') : 'No school logo yet';
    final codeLabel = hasCode ? pref.schoolCode! : 'No school code yet';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(
              left: AppSpacing.x4, bottom: AppSpacing.x8),
          child: Text('APP APPEARANCE',
              style: textTheme.labelSmall
                  ?.copyWith(color: t.textMuted, letterSpacing: 0.8)),
        ),
        AuraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _PreviewRow(pref: pref, reduce: reduce),
              const SizedBox(height: AppSpacing.x20),
              Divider(height: 1, color: t.border),
              const SizedBox(height: AppSpacing.x20),
              _ControlRow(
                title: 'Brand mark',
                subtitle: 'The logo on the sign-in and splash screens.',
                value: pref.useSchoolLogo,
                disabled: !hasLogo,
                disabledHint: 'Your school hasn’t uploaded a logo yet.',
                offLabel: 'Aura',
                onLabel: logoLabel,
                onChanged: (v) => ctrl.setUseSchoolLogo(v),
              ),
              const SizedBox(height: AppSpacing.x20),
              _ControlRow(
                title: 'App name',
                subtitle: 'The wordmark beside the logo.',
                value: pref.useSchoolCodeAsName,
                disabled: !hasCode,
                disabledHint: 'Your school hasn’t set a code yet.',
                offLabel: 'Aura',
                onLabel: codeLabel,
                onLabelStyle: AppTypography.mono(
                    size: 13, weight: FontWeight.w600, color: t.ink),
                onChanged: (v) => ctrl.setUseSchoolCodeAsName(v),
              ),
              const SizedBox(height: AppSpacing.x16),
              _Footnote(t: t, textTheme: textTheme),
            ],
          ),
        ),
      ],
    );
  }
}

/// Animated preview of how the brand mark + wordmark look right now.
class _PreviewRow extends StatelessWidget {
  const _PreviewRow({required this.pref, required this.reduce});
  final AppBrandingPref pref;
  final bool reduce;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x16, vertical: AppSpacing.x20),
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          AnimatedSwitcher(
            duration: reduce ? Duration.zero : AppMotion.dropdown,
            switchInCurve: AppMotion.easeOut,
            switchOutCurve: AppMotion.easeOut,
            transitionBuilder: (child, anim) => FadeTransition(
              opacity: anim,
              child: ScaleTransition(
                scale: reduce
                    ? const AlwaysStoppedAnimation(1.0)
                    : Tween(begin: 0.94, end: 1.0).animate(anim),
                child: child,
              ),
            ),
            child: KeyedSubtree(
              key: ValueKey(pref.effectiveUseSchoolLogo),
              child: const AppBrandMark(size: 52),
            ),
          ),
          const SizedBox(width: AppSpacing.x16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Preview',
                    style: textTheme.labelSmall
                        ?.copyWith(color: t.textMuted, letterSpacing: 0.8)),
                const SizedBox(height: 4),
                AnimatedSwitcher(
                  duration: reduce ? Duration.zero : AppMotion.dropdown,
                  switchInCurve: AppMotion.easeOut,
                  switchOutCurve: AppMotion.easeOut,
                  transitionBuilder: (child, anim) => FadeTransition(
                    opacity: anim,
                    child: child,
                  ),
                  child: Text(
                    pref.resolvedAppName(),
                    key: ValueKey(pref.resolvedAppName()),
                    style: pref.useSchoolCodeAsName && pref.hasCode
                        ? AppTypography.mono(
                            size: 24, weight: FontWeight.w700, color: t.ink)
                        : textTheme.headlineSmall,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// One row of: title + subtitle + segmented control.
class _ControlRow extends StatelessWidget {
  const _ControlRow({
    required this.title,
    required this.subtitle,
    required this.value,
    required this.disabled,
    required this.disabledHint,
    required this.offLabel,
    required this.onLabel,
    required this.onChanged,
    this.onLabelStyle,
  });

  final String title;
  final String subtitle;
  final bool value;
  final bool disabled;
  final String disabledHint;
  final String offLabel;
  final String onLabel;
  final TextStyle? onLabelStyle;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    // When disabled, the toggle is locked OFF visually + functionally, but the
    // tile still renders so the user sees *what's possible* once the school
    // populates the data.
    final effective = disabled ? false : value;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(title, style: textTheme.titleLarge),
          const SizedBox(height: 2),
          Text(
            disabled ? disabledHint : subtitle,
            style: textTheme.bodySmall?.copyWith(
              color: disabled ? t.tardy : t.textSecondary,
            ),
          ),
          const SizedBox(height: AppSpacing.x12),
          Opacity(
            opacity: disabled ? 0.55 : 1.0,
            child: IgnorePointer(
              ignoring: disabled,
              child: SegmentedButton<bool>(
                segments: [
                  ButtonSegment(
                    value: false,
                    label: Text(offLabel),
                  ),
                  ButtonSegment(
                    value: true,
                    label: Text(onLabel,
                        style: onLabelStyle,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis),
                  ),
                ],
                selected: {effective},
                showSelectedIcon: false,
                onSelectionChanged: (s) => onChanged(s.first),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Small grey footnote — sets expectation that the OS launcher icon stays
/// as Aura. Anchors the user's mental model without nagging.
class _Footnote extends StatelessWidget {
  const _Footnote({required this.t, required this.textTheme});
  final AppTokens t;
  final TextTheme textTheme;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(Icons.info_outline_rounded, size: 14, color: t.textMuted),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            'These choices change how Aura looks once you’re inside the app. '
            'The home-screen icon stays the same.',
            style: textTheme.bodySmall?.copyWith(color: t.textMuted),
          ),
        ),
      ],
    );
  }
}
