import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_branding_controller.dart';
import '../../core/theme/app_motion.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_tokens.dart';
import '../../core/theme/app_typography.dart';
import '../../core/widgets/app_brand_mark.dart';
import '../../core/widgets/app_scaffold.dart';
import '../../core/widgets/aura_logo.dart';
import '../../core/widgets/pressable.dart';
import '../../core/widgets/school_badge.dart';

/// Dedicated "App appearance" screen — opened from a single tile in the
/// Account tab. Splits a previously crowded inline section into a focused
/// surface: hero preview, two visual option-card pickers, footnote.
class AppAppearanceScreen extends ConsumerWidget {
  const AppAppearanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final pref = ref.watch(appBrandingProvider);
    final ctrl = ref.read(appBrandingProvider.notifier);
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    return AppScaffold(
      title: 'App appearance',
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, AppSpacing.x40),
        children: [
          _Preview(pref: pref, reduce: reduce),
          const SizedBox(height: AppSpacing.x32),
          const _SectionLabel(text: 'Brand mark'),
          const SizedBox(height: AppSpacing.x12),
          Row(
            children: [
              Expanded(
                child: _OptionCard(
                  selected: !pref.useSchoolLogo,
                  onTap: () => ctrl.setUseSchoolLogo(false),
                  label: 'Aura',
                  preview: const _AuraTile(size: 56),
                ),
              ),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: _OptionCard(
                  selected: pref.useSchoolLogo && pref.hasLogo,
                  disabled: !pref.hasLogo,
                  disabledHint: 'School hasn’t uploaded a logo',
                  onTap: () => ctrl.setUseSchoolLogo(true),
                  label: pref.hasLogo
                      ? (pref.schoolName ?? 'School')
                      : 'School logo',
                  preview: pref.hasLogo
                      ? SchoolBadge(
                          logoUrl: pref.schoolLogoUrl,
                          schoolName: pref.schoolName,
                          primaryHex: pref.schoolPrimaryHex,
                          secondaryHex: pref.schoolSecondaryHex,
                          schoolId: pref.schoolId,
                          size: 56,
                        )
                      : const _PlaceholderTile(size: 56),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.x32),
          const _SectionLabel(text: 'App name'),
          const SizedBox(height: AppSpacing.x12),
          Row(
            children: [
              Expanded(
                child: _OptionCard(
                  selected: !pref.useSchoolCodeAsName,
                  onTap: () => ctrl.setUseSchoolCodeAsName(false),
                  label: 'Default',
                  preview: Text(
                    'Aura',
                    style: textTheme.headlineSmall,
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: _OptionCard(
                  selected: pref.useSchoolCodeAsName && pref.hasCode,
                  disabled: !pref.hasCode,
                  disabledHint: 'School hasn’t set a code',
                  onTap: () => ctrl.setUseSchoolCodeAsName(true),
                  label: pref.hasCode ? 'School code' : 'School code',
                  preview: Text(
                    pref.hasCode ? pref.schoolCode! : '—',
                    style: AppTypography.mono(
                      size: 22,
                      weight: FontWeight.w700,
                      color: t.ink,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.x24),
          _Footnote(t: t, textTheme: textTheme),
        ],
      ),
    );
  }
}

/// Single hero preview — the brand mark + wordmark as they'd render in the
/// app's chrome, animated when the user flips a choice.
class _Preview extends StatelessWidget {
  const _Preview({required this.pref, required this.reduce});
  final AppBrandingPref pref;
  final bool reduce;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x24, vertical: AppSpacing.x32),
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: t.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('PREVIEW',
              style: textTheme.labelSmall
                  ?.copyWith(color: t.textMuted, letterSpacing: 1.2)),
          const SizedBox(height: AppSpacing.x16),
          Row(
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
                  child: const AppBrandMark(size: 64),
                ),
              ),
              const SizedBox(width: AppSpacing.x20),
              Expanded(
                child: AnimatedSwitcher(
                  duration: reduce ? Duration.zero : AppMotion.dropdown,
                  switchInCurve: AppMotion.easeOut,
                  switchOutCurve: AppMotion.easeOut,
                  transitionBuilder: (child, anim) =>
                      FadeTransition(opacity: anim, child: child),
                  child: Text(
                    pref.resolvedAppName(),
                    key: ValueKey(pref.resolvedAppName()),
                    style: pref.useSchoolCodeAsName && pref.hasCode
                        ? AppTypography.mono(
                            size: 28, weight: FontWeight.w700, color: t.ink)
                        : textTheme.headlineMedium,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// A premium visual picker card — a single option with a centered preview
/// glyph, a label, and an animated selection ring. Tap to select. Press
/// scales 0.97 per AppMotion.
class _OptionCard extends StatelessWidget {
  const _OptionCard({
    required this.selected,
    required this.onTap,
    required this.label,
    required this.preview,
    this.disabled = false,
    this.disabledHint,
  });

  final bool selected;
  final VoidCallback onTap;
  final String label;
  final Widget preview;
  final bool disabled;
  final String? disabledHint;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    final card = AnimatedContainer(
      duration: AppMotion.dropdown,
      curve: AppMotion.easeOut,
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x12, vertical: AppSpacing.x20),
      decoration: BoxDecoration(
        color: selected ? t.surface : t.surfaceAlt,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: selected ? t.accent : t.border,
          width: selected ? 2 : 1,
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            height: 64,
            child: Center(child: preview),
          ),
          const SizedBox(height: AppSpacing.x12),
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            textAlign: TextAlign.center,
            style: textTheme.bodyMedium?.copyWith(
              fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
              color: selected ? t.ink : t.textSecondary,
            ),
          ),
          if (disabled && disabledHint != null) ...[
            const SizedBox(height: 2),
            Text(
              disabledHint!,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: textTheme.bodySmall?.copyWith(color: t.textMuted),
            ),
          ],
        ],
      ),
    );

    return Opacity(
      opacity: disabled ? 0.55 : 1.0,
      child: IgnorePointer(
        ignoring: disabled,
        child: Pressable(scale: 0.97, onTap: onTap, child: card),
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel({required this.text});
  final String text;
  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(left: AppSpacing.x4),
      child: Text(text.toUpperCase(),
          style: textTheme.labelSmall
              ?.copyWith(color: t.textMuted, letterSpacing: 0.8)),
    );
  }
}

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

/// Default Aura mark on an ink chip — the visual we show when "Aura"
/// is the selected brand mark.
class _AuraTile extends StatelessWidget {
  const _AuraTile({required this.size});
  final double size;
  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: t.navInk,
        borderRadius: BorderRadius.circular(size * 0.3),
      ),
      child: Padding(
        padding: EdgeInsets.all(size * 0.19),
        child: AuraLogo(size: size * 0.62),
      ),
    );
  }
}

/// Placeholder used when the school hasn't uploaded a logo yet — a soft
/// dashed circle with an upload-cloud icon, so the user sees "this slot
/// exists, it just isn't filled".
class _PlaceholderTile extends StatelessWidget {
  const _PlaceholderTile({required this.size});
  final double size;
  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: t.surface,
        shape: BoxShape.circle,
        border: Border.all(color: t.border, width: 1.5),
      ),
      child: Icon(Icons.image_outlined,
          size: size * 0.42, color: t.textMuted),
    );
  }
}
