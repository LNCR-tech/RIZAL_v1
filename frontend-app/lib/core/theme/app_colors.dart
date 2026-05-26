import 'package:flutter/material.dart';

/// Raw brand palette + color math.
///
/// Semantic, mode-aware tokens live in [AppTokens] (app_tokens.dart). Widgets
/// should read tokens from the theme, not these raw constants directly — except
/// for the fixed status/governance colors which never change with branding.
class AppColors {
  AppColors._();

  // ── Brand ────────────────────────────────────────────────────────────
  static const Color accent = Color(0xFFAAFF00); // electric lime
  static const Color accentDark = Color(0xFF88CC00);
  static const Color ink = Color(0xFF0A0A0A);
  static const Color paper = Color(0xFFFFFFFF);

  // ── Light surfaces ───────────────────────────────────────────────────
  static const Color lightBg = Color(0xFFECEEE7);
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightSurfaceAlt = Color(0xFFF4F6EF);
  static const Color lightTextSecondary = Color(0xFF555B50);
  static const Color lightTextMuted = Color(0xFF8A9182);
  static const Color lightBorder = Color(0xFFE2E5DB);

  // ── Dark surfaces (OLED-leaning) ─────────────────────────────────────
  static const Color darkBg = Color(0xFF070A00);
  static const Color darkSurface = Color(0xFF12150D);
  static const Color darkSurfaceAlt = Color(0xFF1A1E12);
  static const Color darkInk = Color(0xFFF4F7EC);
  static const Color darkTextSecondary = Color(0xFFA6AE9B);
  static const Color darkTextMuted = Color(0xFF6E7567);
  static const Color darkBorder = Color(0xFF272C1D);

  // ── Status (fixed, never branded) ────────────────────────────────────
  static const Color present = Color(0xFF22C55E);
  static const Color tardy = Color(0xFFFB923C); // "late" (reserved word in Dart)
  static const Color atRisk = Color(0xFFF59E0B);
  static const Color absent = Color(0xFFEF4444);
  static const Color excused = Color(0xFFF97316);

  // ── Governance accents ───────────────────────────────────────────────
  static const Color ssg = Color(0xFF6366F1);
  static const Color sg = Color(0xFF8B5CF6);

  // ── Color math ───────────────────────────────────────────────────────
  /// Darken [c] by [percent] (0–100).
  static Color darken(Color c, double percent) {
    final f = 1 - (percent.clamp(0, 100) / 100);
    return Color.fromARGB(
      c.alpha,
      (c.red * f).round(),
      (c.green * f).round(),
      (c.blue * f).round(),
    );
  }

  /// Blend [a] (weight [aWeight] 0–1) over [b].
  static Color mix(Color a, Color b, double aWeight) {
    final w = aWeight.clamp(0.0, 1.0);
    final iw = 1 - w;
    return Color.fromARGB(
      255,
      (a.red * w + b.red * iw).round(),
      (a.green * w + b.green * iw).round(),
      (a.blue * w + b.blue * iw).round(),
    );
  }

  /// Parse "#RRGGBB" / "RRGGBB" / "#RGB" → [Color], else [fallback].
  static Color? parseHex(String? hex, {Color? fallback}) {
    if (hex == null) return fallback;
    var s = hex.trim().replaceAll('#', '');
    if (s.length == 3) s = s.split('').map((c) => '$c$c').join();
    if (s.length == 8) s = s.substring(0, 6); // drop alpha channel
    if (s.length != 6) return fallback;
    final v = int.tryParse(s, radix: 16);
    if (v == null) return fallback;
    return Color(0xFF000000 | v);
  }
}
