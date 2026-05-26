import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../cache/cache_store.dart';
import '../cache/school_logo_cache.dart';
import '../network/media_url.dart';
import '../theme/app_branding_controller.dart';
import '../theme/theme_controller.dart';
import 'auth_meta.dart';
import 'role.dart';
import 'token_store.dart';

enum SessionStatus { unknown, authenticated, unauthenticated }

@immutable
class SessionState {
  const SessionState({this.status = SessionStatus.unknown, this.meta});
  final SessionStatus status;
  final AuthMeta? meta;

  bool get isAuthenticated =>
      status == SessionStatus.authenticated && meta != null;
  bool get isResolved => status != SessionStatus.unknown;

  Workspace get workspace =>
      meta == null ? Workspace.student : Roles.workspaceFor(meta!.roles);

  /// Gate flags consulted by the router.
  bool get needsPasswordChange => meta?.mustChangePassword ?? false;
  bool get needsPrivilegedFace => meta?.pendingPrivilegedFace ?? false;

  /// First-login face-registration gate. True when a student is signed in
  /// but the backend says no face reference is enrolled yet — they get
  /// redirected to [RegisterFaceScreen] before reaching their workspace.
  ///
  /// Privileged accounts (admin / school-IT / governance) are intentionally
  /// excluded: they register from Account → Security → Face ID, and their
  /// MFA flow is the separate [needsPrivilegedFace] gate.
  bool get needsFaceRegistration {
    final m = meta;
    if (m == null) return false;
    if (m.faceReferenceEnrolled) return false;
    return Roles.workspaceFor(m.roles) == Workspace.student;
  }

  SessionState copyWith(
          {SessionStatus? status, AuthMeta? meta, bool clearMeta = false}) =>
      SessionState(
        status: status ?? this.status,
        meta: clearMeta ? null : (meta ?? this.meta),
      );
}

/// Owns auth lifecycle: restore on launch, login, logout, and 401 handling.
class SessionController extends Notifier<SessionState> {
  static const _kMeta = 'aura_auth_meta';
  // Grace window after a fresh login during which transient 401s do NOT
  // drive the session into expired state. Real causes seen in the wild:
  //   * backend commits the UserSession row a few ms after the token
  //     response goes out — the very first authed request races and hits
  //     `assert_session_valid` before the INSERT lands.
  //   * Flutter fires multiple parallel queries on dashboard mount; one
  //     transient network blip 401s and would otherwise log out.
  // 3 seconds is enough for the backend session table to be queryable +
  // for Flutter's initial fan-out to settle. Real session revocations
  // (admin invalidates a device) take much longer than 3 seconds to
  // notice in any UX, so this trade-off is safe.
  static const Duration _loginGrace = Duration(seconds: 3);
  SharedPreferences? _prefs;
  DateTime? _loginAt;

  @override
  SessionState build() {
    Future.microtask(_restore);
    return const SessionState();
  }

  Future<void> _restore() async {
    _prefs = await SharedPreferences.getInstance();
    final token = await ref.read(tokenStoreProvider).read();
    final metaStr = _prefs!.getString(_kMeta);
    if (token != null && token.isNotEmpty && metaStr != null) {
      try {
        final meta =
            AuthMeta.fromJson(jsonDecode(metaStr) as Map<String, dynamic>);
        state = SessionState(status: SessionStatus.authenticated, meta: meta);
        _applyBranding(meta);
        return;
      } catch (_) {
        // Corrupt meta — fall through to signed-out.
      }
    }
    state = const SessionState(status: SessionStatus.unauthenticated);
  }

  Future<void> completeLogin(
      {required String accessToken, required AuthMeta meta}) async {
    await ref.read(tokenStoreProvider).write(accessToken);
    _prefs ??= await SharedPreferences.getInstance();
    await _prefs!.setString(_kMeta, jsonEncode(meta.toJson()));
    _loginAt = DateTime.now();
    state = SessionState(status: SessionStatus.authenticated, meta: meta);
    _applyBranding(meta);
  }

  Future<void> logout() async {
    _loginAt = null;
    await ref.read(tokenStoreProvider).clear();
    await ref.read(cacheStoreProvider).clear();
    // Drop the cached school logo bytes — the next sign-in re-fetches and
    // re-caches. Keep the user's App appearance toggle choices intact (those
    // are personal prefs, not session state).
    unawaited(ref.read(schoolLogoCacheProvider).clear());
    unawaited(ref.read(appBrandingProvider.notifier).clearSnapshot());
    _prefs ??= await SharedPreferences.getInstance();
    await _prefs!.remove(_kMeta);
    ref.read(themeControllerProvider.notifier).setBrandPrimaryHex(null);
    state = const SessionState(status: SessionStatus.unauthenticated);
  }

  /// Called by the Dio 401 interceptor when the token is rejected.
  /// Honours [_loginGrace] so a transient race in the first few seconds
  /// after login doesn't immediately log the user back out.
  void handleUnauthorized() {
    if (state.status != SessionStatus.authenticated) return;
    final loginAt = _loginAt;
    if (loginAt != null &&
        DateTime.now().difference(loginAt) < _loginGrace) {
      // Race against the backend committing the session row, or a parallel
      // dashboard query crossing wires with token write. Hold off on
      // logout — if the session is *really* invalid, the next authed
      // request after the grace window will catch it.
      return;
    }
    logout();
  }

  /// Called by [RegisterFaceScreen] after the backend confirms the face
  /// reference is enrolled, so the router's [SessionState.needsFaceRegistration]
  /// gate clears immediately and the student lands on their home workspace
  /// without waiting for a re-login.
  Future<void> markFaceRegistered() async {
    final current = state.meta;
    if (current == null) return;
    final updated = current.copyWith(faceReferenceEnrolled: true);
    state = state.copyWith(meta: updated);
    _prefs ??= await SharedPreferences.getInstance();
    await _prefs!.setString(_kMeta, jsonEncode(updated.toJson()));
  }

  void _applyBranding(AuthMeta meta) {
    Future.microtask(() {
      ref
          .read(themeControllerProvider.notifier)
          .setBrandPrimaryHex(meta.primaryColor);
      // Keep the persisted App-appearance snapshot in sync with the latest
      // login so a returning user sees the right school brand on splash /
      // login even before the next network round-trip.
      ref.read(appBrandingProvider.notifier).captureSchoolSnapshot(meta);
      // Warm the disk cache so the brand mark renders without a network
      // round-trip on the next launch.
      final url = mediaUrl(meta.logoUrl);
      if (url != null) {
        unawaited(ref
            .read(schoolLogoCacheProvider)
            .preload(url, meta.schoolId));
      }
    });
  }
}

final sessionControllerProvider =
    NotifierProvider<SessionController, SessionState>(SessionController.new);
