import 'package:flutter/material.dart';

import 'app_spacing.dart';
import 'app_tokens.dart';
import 'app_typography.dart';

/// Builds [ThemeData] from [AppTokens]. Kept to stable theme sub-APIs only
/// (AppBarTheme / InputDecorationTheme / DividerThemeData) to avoid churn;
/// components style themselves from `AppTokens.of(context)`.
class AppTheme {
  AppTheme._();

  // ThemeData (especially ColorScheme.fromSeed) is expensive to build. Memoize
  // by inputs so toggling light/dark — or any AuraApp rebuild — reuses the cached
  // themes instead of recomputing the palette every time (the theme-switch jank).
  static final Map<String, ThemeData> _cache = {};

  static ThemeData light({Color? brandPrimary, bool reduceMotion = false}) =>
      _cache.putIfAbsent(
        'L|${brandPrimary?.toString() ?? ''}|$reduceMotion',
        () => _build(AppTokens.light(brandPrimary: brandPrimary), reduceMotion),
      );

  static ThemeData dark({Color? brandPrimary, bool reduceMotion = false}) =>
      _cache.putIfAbsent(
        'D|${brandPrimary?.toString() ?? ''}|$reduceMotion',
        () => _build(AppTokens.dark(brandPrimary: brandPrimary), reduceMotion),
      );

  static ThemeData _build(AppTokens t, bool reduceMotion) {
    final scheme = ColorScheme.fromSeed(
      seedColor: t.accent,
      brightness: t.brightness,
    ).copyWith(
      primary: t.accent,
      onPrimary: t.onAccent,
      surface: t.surface,
      onSurface: t.ink,
      error: t.absent,
    );

    final textTheme = AppTypography.textTheme(t.ink);

    return ThemeData(
      useMaterial3: true,
      brightness: t.brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: t.bg,
      canvasColor: t.bg,
      fontFamily: AppTypography.fontFamily,
      textTheme: textTheme,
      extensions: <ThemeExtension<dynamic>>[t],
      visualDensity: VisualDensity.standard,
      pageTransitionsTheme: PageTransitionsTheme(
        builders: {
          for (final p in TargetPlatform.values)
            p: reduceMotion
                ? const _NoPageTransitionsBuilder()
                : const _AuraPageTransitionsBuilder(),
        },
      ),
      dividerTheme: DividerThemeData(color: t.border, thickness: 1, space: 1),
      appBarTheme: AppBarTheme(
        backgroundColor: t.bg,
        foregroundColor: t.ink,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: textTheme.headlineSmall,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: t.surfaceAlt,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x16,
          vertical: AppSpacing.x16,
        ),
        border: const OutlineInputBorder(
          borderRadius: AppRadii.rControl,
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: AppRadii.rControl,
          borderSide: BorderSide(color: t.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: AppRadii.rControl,
          borderSide: BorderSide(color: t.accent, width: 2),
        ),
        hintStyle: textTheme.bodyMedium?.copyWith(color: t.textMuted),
        labelStyle: textTheme.labelMedium?.copyWith(color: t.textSecondary),
      ),
    );
  }
}

/// Lightweight horizontal route transition used instead of depending on a
/// platform-specific builder export that varies across Flutter SDK versions.
class _AuraPageTransitionsBuilder extends PageTransitionsBuilder {
  const _AuraPageTransitionsBuilder();

  @override
  Widget buildTransitions<T>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    final position = Tween<Offset>(
      begin: const Offset(0.08, 0),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(parent: animation, curve: Curves.easeOutCubic),
    );
    return SlideTransition(position: position, child: child);
  }
}

/// No-op route transition used when reduced motion is active.
class _NoPageTransitionsBuilder extends PageTransitionsBuilder {
  const _NoPageTransitionsBuilder();
  @override
  Widget buildTransitions<T>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) =>
      child;
}
