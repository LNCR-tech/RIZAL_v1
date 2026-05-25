import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app_colors.dart';

/// Theme state: light/dark mode + optional per-school brand primary.
@immutable
class ThemeState {
  const ThemeState({this.mode = ThemeMode.system, this.brandPrimary});
  final ThemeMode mode;
  final Color? brandPrimary;

  ThemeState copyWith({ThemeMode? mode, Color? brandPrimary, bool clearBrand = false}) {
    return ThemeState(
      mode: mode ?? this.mode,
      brandPrimary: clearBrand ? null : (brandPrimary ?? this.brandPrimary),
    );
  }
}

/// Persists theme choices and applies school branding from the auth token.
class ThemeController extends Notifier<ThemeState> {
  static const _kMode = 'aura_theme_mode';
  static const _kBrand = 'aura_brand_primary';
  SharedPreferences? _prefs;

  @override
  ThemeState build() {
    // Kick off async restore; initial frame uses defaults.
    Future.microtask(_restore);
    return const ThemeState();
  }

  Future<void> _restore() async {
    _prefs = await SharedPreferences.getInstance();
    state = state.copyWith(
      mode: _modeFromString(_prefs!.getString(_kMode)),
      brandPrimary: AppColors.parseHex(_prefs!.getString(_kBrand)),
    );
  }

  void setMode(ThemeMode mode) {
    state = state.copyWith(mode: mode);
    _prefs?.setString(_kMode, mode.name);
  }

  void toggleDark() => setMode(
        state.mode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark,
      );

  /// Apply school branding (hex like "#AAFF00"); pass null/empty to clear.
  void setBrandPrimaryHex(String? hex) {
    final color = AppColors.parseHex(hex);
    state = state.copyWith(brandPrimary: color, clearBrand: color == null);
    if (color == null) {
      _prefs?.remove(_kBrand);
    } else {
      _prefs?.setString(_kBrand, hex!);
    }
  }

  static ThemeMode _modeFromString(String? s) {
    switch (s) {
      case 'light':
        return ThemeMode.light;
      case 'dark':
        return ThemeMode.dark;
      default:
        return ThemeMode.system;
    }
  }
}

final themeControllerProvider =
    NotifierProvider<ThemeController, ThemeState>(ThemeController.new);
