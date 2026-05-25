import 'package:flutter/material.dart';

import 'app_colors.dart';
import 'contrast.dart';

/// Semantic, mode-aware design tokens exposed through [ThemeData.extensions].
///
/// Widgets read these via `AppTokens.of(context)` rather than hardcoding colors,
/// so light/dark and per-school branding flow through one place.
@immutable
class AppTokens extends ThemeExtension<AppTokens> {
  const AppTokens({
    required this.brightness,
    required this.accent,
    required this.accentDark,
    required this.onAccent,
    required this.bg,
    required this.surface,
    required this.surfaceAlt,
    required this.ink,
    required this.textSecondary,
    required this.textMuted,
    required this.border,
    required this.navInk,
    required this.present,
    required this.tardy,
    required this.atRisk,
    required this.absent,
    required this.excused,
    required this.ssg,
    required this.sg,
  });

  final Brightness brightness;
  final Color accent;
  final Color accentDark;
  final Color onAccent;
  final Color bg;
  final Color surface;
  final Color surfaceAlt;
  final Color ink;
  final Color textSecondary;
  final Color textMuted;
  final Color border;
  final Color navInk;

  // Fixed status + governance colors (never branded).
  final Color present;
  final Color tardy; // "late" is reserved in Dart
  final Color atRisk;
  final Color absent;
  final Color excused;
  final Color ssg;
  final Color sg;

  bool get isDark => brightness == Brightness.dark;

  /// Light tokens. [brandPrimary] (school customization) overrides the accent.
  factory AppTokens.light({Color? brandPrimary}) {
    final accent = brandPrimary ?? AppColors.accent;
    return AppTokens(
      brightness: Brightness.light,
      accent: accent,
      accentDark: AppColors.darken(accent, 18),
      onAccent: contrastText(accent),
      bg: AppColors.lightBg,
      surface: AppColors.lightSurface,
      surfaceAlt: AppColors.lightSurfaceAlt,
      ink: AppColors.ink,
      textSecondary: AppColors.lightTextSecondary,
      textMuted: AppColors.lightTextMuted,
      border: AppColors.lightBorder,
      navInk: AppColors.ink,
      present: AppColors.present,
      tardy: AppColors.tardy,
      atRisk: AppColors.atRisk,
      absent: AppColors.absent,
      excused: AppColors.excused,
      ssg: AppColors.ssg,
      sg: AppColors.sg,
    );
  }

  /// Dark tokens. Background derives from the brand color darkened ~96%
  /// (mirrors the web app), giving a branded near-black instead of flat grey.
  factory AppTokens.dark({Color? brandPrimary}) {
    final accent = brandPrimary ?? AppColors.accent;
    return AppTokens(
      brightness: Brightness.dark,
      accent: accent,
      accentDark: AppColors.darken(accent, 12),
      onAccent: contrastText(accent),
      bg: AppColors.darken(accent, 96),
      surface: AppColors.darkSurface,
      surfaceAlt: AppColors.darkSurfaceAlt,
      ink: AppColors.darkInk,
      textSecondary: AppColors.darkTextSecondary,
      textMuted: AppColors.darkTextMuted,
      border: AppColors.darkBorder,
      navInk: AppColors.ink,
      present: AppColors.present,
      tardy: AppColors.tardy,
      atRisk: AppColors.atRisk,
      absent: AppColors.absent,
      excused: AppColors.excused,
      ssg: AppColors.ssg,
      sg: AppColors.sg,
    );
  }

  static AppTokens of(BuildContext context) =>
      Theme.of(context).extension<AppTokens>() ?? AppTokens.light();

  @override
  AppTokens copyWith({
    Brightness? brightness,
    Color? accent,
    Color? accentDark,
    Color? onAccent,
    Color? bg,
    Color? surface,
    Color? surfaceAlt,
    Color? ink,
    Color? textSecondary,
    Color? textMuted,
    Color? border,
    Color? navInk,
    Color? present,
    Color? tardy,
    Color? atRisk,
    Color? absent,
    Color? excused,
    Color? ssg,
    Color? sg,
  }) {
    return AppTokens(
      brightness: brightness ?? this.brightness,
      accent: accent ?? this.accent,
      accentDark: accentDark ?? this.accentDark,
      onAccent: onAccent ?? this.onAccent,
      bg: bg ?? this.bg,
      surface: surface ?? this.surface,
      surfaceAlt: surfaceAlt ?? this.surfaceAlt,
      ink: ink ?? this.ink,
      textSecondary: textSecondary ?? this.textSecondary,
      textMuted: textMuted ?? this.textMuted,
      border: border ?? this.border,
      navInk: navInk ?? this.navInk,
      present: present ?? this.present,
      tardy: tardy ?? this.tardy,
      atRisk: atRisk ?? this.atRisk,
      absent: absent ?? this.absent,
      excused: excused ?? this.excused,
      ssg: ssg ?? this.ssg,
      sg: sg ?? this.sg,
    );
  }

  @override
  AppTokens lerp(ThemeExtension<AppTokens>? other, double t) {
    if (other is! AppTokens) return this;
    Color c(Color a, Color b) => Color.lerp(a, b, t)!;
    return AppTokens(
      brightness: t < 0.5 ? brightness : other.brightness,
      accent: c(accent, other.accent),
      accentDark: c(accentDark, other.accentDark),
      onAccent: c(onAccent, other.onAccent),
      bg: c(bg, other.bg),
      surface: c(surface, other.surface),
      surfaceAlt: c(surfaceAlt, other.surfaceAlt),
      ink: c(ink, other.ink),
      textSecondary: c(textSecondary, other.textSecondary),
      textMuted: c(textMuted, other.textMuted),
      border: c(border, other.border),
      navInk: c(navInk, other.navInk),
      present: c(present, other.present),
      tardy: c(tardy, other.tardy),
      atRisk: c(atRisk, other.atRisk),
      absent: c(absent, other.absent),
      excused: c(excused, other.excused),
      ssg: c(ssg, other.ssg),
      sg: c(sg, other.sg),
    );
  }
}
