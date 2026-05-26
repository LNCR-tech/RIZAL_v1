import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../auth/auth_meta.dart';

/// Persisted choice + snapshot of the school's branding metadata.
///
/// Two independent toggles control whether the **in-app** brand mark and
/// app-name use the signed-in school's logo + code (instead of the default
/// Aura mark + "Aura" wordmark). The OS launcher icon and label are
/// unaffected — neither iOS nor Android allows arbitrary runtime icons.
///
/// We persist a snapshot of `schoolCode` / `schoolName` / `logoUrl` /
/// `primary` + `secondary` hex so the splash and login screens can render
/// the user's school brand immediately on cold start, before any network
/// round-trip completes. The snapshot is refreshed every successful login.
@immutable
class AppBrandingPref {
  const AppBrandingPref({
    this.useSchoolLogo = false,
    this.useSchoolCodeAsName = false,
    this.schoolId,
    this.schoolCode,
    this.schoolName,
    this.schoolLogoUrl,
    this.schoolPrimaryHex,
    this.schoolSecondaryHex,
  });

  final bool useSchoolLogo;
  final bool useSchoolCodeAsName;

  final int? schoolId;
  final String? schoolCode;
  final String? schoolName;
  final String? schoolLogoUrl;
  final String? schoolPrimaryHex;
  final String? schoolSecondaryHex;

  bool get hasLogo => (schoolLogoUrl ?? '').trim().isNotEmpty;
  bool get hasCode => (schoolCode ?? '').trim().isNotEmpty;

  /// Effective in-app brand label. Falls back to "Aura" when the user opted
  /// in but the school hasn't set a code, so the chrome never renders an
  /// empty string.
  String resolvedAppName({String fallback = 'Aura'}) {
    if (useSchoolCodeAsName && hasCode) return schoolCode!.trim();
    return fallback;
  }

  /// Should the SchoolBadge / brand mark render the school's uploaded logo?
  /// Only true when the user opted in AND a logo URL exists in the snapshot.
  bool get effectiveUseSchoolLogo => useSchoolLogo && hasLogo;

  AppBrandingPref copyWith({
    bool? useSchoolLogo,
    bool? useSchoolCodeAsName,
    int? schoolId,
    String? schoolCode,
    String? schoolName,
    String? schoolLogoUrl,
    String? schoolPrimaryHex,
    String? schoolSecondaryHex,
    bool clearSnapshot = false,
  }) {
    if (clearSnapshot) {
      return AppBrandingPref(
        useSchoolLogo: useSchoolLogo ?? this.useSchoolLogo,
        useSchoolCodeAsName: useSchoolCodeAsName ?? this.useSchoolCodeAsName,
      );
    }
    return AppBrandingPref(
      useSchoolLogo: useSchoolLogo ?? this.useSchoolLogo,
      useSchoolCodeAsName: useSchoolCodeAsName ?? this.useSchoolCodeAsName,
      schoolId: schoolId ?? this.schoolId,
      schoolCode: schoolCode ?? this.schoolCode,
      schoolName: schoolName ?? this.schoolName,
      schoolLogoUrl: schoolLogoUrl ?? this.schoolLogoUrl,
      schoolPrimaryHex: schoolPrimaryHex ?? this.schoolPrimaryHex,
      schoolSecondaryHex: schoolSecondaryHex ?? this.schoolSecondaryHex,
    );
  }

  Map<String, dynamic> toJson() => {
        'use_school_logo': useSchoolLogo,
        'use_school_code_as_name': useSchoolCodeAsName,
        'school_id': schoolId,
        'school_code': schoolCode,
        'school_name': schoolName,
        'school_logo_url': schoolLogoUrl,
        'school_primary_hex': schoolPrimaryHex,
        'school_secondary_hex': schoolSecondaryHex,
      };

  factory AppBrandingPref.fromJson(Map<String, dynamic> json) {
    String? s(dynamic v) {
      final str = v?.toString().trim();
      return (str == null || str.isEmpty) ? null : str;
    }

    int? i(dynamic v) =>
        v is num ? v.toInt() : (v is String ? int.tryParse(v) : null);

    return AppBrandingPref(
      useSchoolLogo: json['use_school_logo'] == true,
      useSchoolCodeAsName: json['use_school_code_as_name'] == true,
      schoolId: i(json['school_id']),
      schoolCode: s(json['school_code']),
      schoolName: s(json['school_name']),
      schoolLogoUrl: s(json['school_logo_url']),
      schoolPrimaryHex: s(json['school_primary_hex']),
      schoolSecondaryHex: s(json['school_secondary_hex']),
    );
  }
}

/// Owns the persisted [AppBrandingPref] and writes through to
/// `SharedPreferences`. The snapshot fields refresh on every successful
/// login (via [captureSchoolSnapshot]); the toggles only change when the
/// user flips them in Account → App appearance.
class AppBrandingController extends Notifier<AppBrandingPref> {
  static const _kKey = 'aura_app_branding_v1';
  SharedPreferences? _prefs;

  @override
  AppBrandingPref build() {
    Future.microtask(_restore);
    return const AppBrandingPref();
  }

  Future<void> _restore() async {
    _prefs = await SharedPreferences.getInstance();
    final raw = _prefs!.getString(_kKey);
    if (raw == null || raw.isEmpty) return;
    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map<String, dynamic>) {
        state = AppBrandingPref.fromJson(decoded);
      }
    } catch (_) {
      // Corrupt blob — leave defaults, overwrite on next write.
    }
  }

  Future<void> _persist() async {
    _prefs ??= await SharedPreferences.getInstance();
    await _prefs!.setString(_kKey, jsonEncode(state.toJson()));
  }

  Future<void> setUseSchoolLogo(bool value) async {
    state = state.copyWith(useSchoolLogo: value);
    await _persist();
  }

  Future<void> setUseSchoolCodeAsName(bool value) async {
    state = state.copyWith(useSchoolCodeAsName: value);
    await _persist();
  }

  /// Refresh the snapshot from the latest [AuthMeta]. Called after every
  /// successful login so a returning user's splash/login still uses their
  /// last school's branding even when offline.
  Future<void> captureSchoolSnapshot(AuthMeta meta) async {
    state = state.copyWith(
      schoolId: meta.schoolId,
      schoolCode: meta.schoolCode,
      schoolName: meta.schoolName,
      schoolLogoUrl: meta.logoUrl,
      schoolPrimaryHex: meta.primaryColor,
      schoolSecondaryHex: meta.secondaryColor,
    );
    await _persist();
  }

  /// Drop the snapshot fields on sign-out while keeping the user's toggle
  /// choices. If the same person signs back in, the snapshot rebuilds from
  /// the new auth meta.
  Future<void> clearSnapshot() async {
    state = state.copyWith(clearSnapshot: true);
    await _persist();
  }
}

final appBrandingProvider =
    NotifierProvider<AppBrandingController, AppBrandingPref>(
        AppBrandingController.new);
