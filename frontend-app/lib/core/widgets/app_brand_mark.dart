import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../theme/app_branding_controller.dart';
import '../theme/app_tokens.dart';
import 'aura_logo.dart';
import 'school_badge.dart';

/// The app's brand mark — Aura by default, the school's logo when the user
/// has opted in via Account → App appearance (and a logo is cached). Used
/// by the login screen and any pre-/post-auth chrome that previously
/// hardcoded [AuraLogo].
///
/// The visual contract differs by source:
///   * **Aura**: rounded-square ink tile with the Aura mark centred
///     (mirrors the original login brand chip).
///   * **School**: circular gradient-ringed logo via [SchoolBadge], so the
///     school's primary/secondary colours frame the mark.
///
/// Sizes route to a consistent visual weight across both modes.
class AppBrandMark extends ConsumerWidget {
  const AppBrandMark({
    super.key,
    this.size = 48,
    this.onDarkSurface = true,
  });

  final double size;

  /// When the Aura tile renders, what's behind it? `true` (default) uses
  /// the ink chip + white logo; `false` uses the surface chip + black logo.
  final bool onDarkSurface;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pref = ref.watch(appBrandingProvider);
    final t = AppTokens.of(context);

    if (pref.effectiveUseSchoolLogo) {
      return SchoolBadge(
        logoUrl: pref.schoolLogoUrl,
        schoolName: pref.schoolName,
        primaryHex: pref.schoolPrimaryHex,
        secondaryHex: pref.schoolSecondaryHex,
        schoolId: pref.schoolId,
        size: size,
      );
    }

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: onDarkSurface ? t.navInk : t.surface,
        borderRadius: BorderRadius.circular(size * 0.3),
      ),
      child: Padding(
        padding: EdgeInsets.all(size * 0.19),
        child: AuraLogo(size: size * 0.62, onDark: onDarkSurface),
      ),
    );
  }
}

/// The app's wordmark — "Aura" by default, the school's code when the user
/// has opted in. Falls back to the supplied [fallback] string (default
/// "Aura") whenever the snapshot lacks a code.
class AppNameText extends ConsumerWidget {
  const AppNameText({
    super.key,
    this.style,
    this.fallback = 'Aura',
  });

  final TextStyle? style;
  final String fallback;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final name = ref.watch(appBrandingProvider).resolvedAppName(
          fallback: fallback,
        );
    return Text(name, style: style);
  }
}
