import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../cache/cache_store.dart';
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
  SharedPreferences? _prefs;

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
    state = SessionState(status: SessionStatus.authenticated, meta: meta);
    _applyBranding(meta);
  }

  Future<void> logout() async {
    await ref.read(tokenStoreProvider).clear();
    await ref.read(cacheStoreProvider).clear();
    _prefs ??= await SharedPreferences.getInstance();
    await _prefs!.remove(_kMeta);
    ref.read(themeControllerProvider.notifier).setBrandPrimaryHex(null);
    state = const SessionState(status: SessionStatus.unauthenticated);
  }

  /// Called by the Dio 401 interceptor when the token is rejected.
  void handleUnauthorized() {
    if (state.status == SessionStatus.authenticated) {
      logout();
    }
  }

  void _applyBranding(AuthMeta meta) {
    Future.microtask(() => ref
        .read(themeControllerProvider.notifier)
        .setBrandPrimaryHex(meta.primaryColor));
  }
}

final sessionControllerProvider =
    NotifierProvider<SessionController, SessionState>(SessionController.new);
