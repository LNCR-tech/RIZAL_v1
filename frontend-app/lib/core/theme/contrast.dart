import 'package:flutter/material.dart';

/// Pick a readable on-color for [bg] using the YIQ luminance formula.
///
/// Ported from the web app's `getContrastYIQ` (frontend-web/src/config/theme.js)
/// so brand-colored surfaces choose the same light/dark text the web app does.
Color contrastText(
  Color bg, {
  Color light = const Color(0xFFF4F7EC),
  Color dark = const Color(0xFF0A0A0A),
}) {
  final yiq = (bg.red * 299 + bg.green * 587 + bg.blue * 114) / 1000;
  return yiq >= 128 ? dark : light;
}
