import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Tiny JSON cache (shared_preferences) used to serve last-known GET responses
/// when the network is unavailable. Keyed by request URL; cleared on logout.
class CacheStore {
  static const _prefix = 'aura_cache:';
  SharedPreferences? _prefs;

  Future<SharedPreferences> get _p async =>
      _prefs ??= await SharedPreferences.getInstance();

  Future<void> write(String key, dynamic jsonData) async {
    try {
      final p = await _p;
      await p.setString('$_prefix$key', jsonEncode(jsonData));
    } catch (_) {
      // Non-encodable or storage failure — skip caching, never throw.
    }
  }

  Future<dynamic> read(String key) async {
    try {
      final p = await _p;
      final raw = p.getString('$_prefix$key');
      return raw == null ? null : jsonDecode(raw);
    } catch (_) {
      return null;
    }
  }

  Future<void> clear() async {
    try {
      final p = await _p;
      final keys = p.getKeys().where((k) => k.startsWith(_prefix)).toList();
      for (final k in keys) {
        await p.remove(k);
      }
    } catch (_) {}
  }
}

final cacheStoreProvider = Provider<CacheStore>((ref) => CacheStore());
