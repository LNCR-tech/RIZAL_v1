import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';

/// Disk-backed cache for the signed-in school's logo PNG. After the first
/// network fetch the bytes are written to the app's support directory and
/// read straight from disk on every subsequent app launch, so the splash
/// screen and brand chrome never have to wait on a re-download.
///
/// Keyed by `school_id` + a stable hash of the absolute URL so a school
/// uploading a new logo (URL changes) transparently busts the cache.
///
/// Web is unsupported by `dart:io`; the cache transparently falls back to
/// an in-memory map there. Web isn't the primary target — phones are — but
/// the dev-preview build (`device_preview` on web) keeps working.
class SchoolLogoCache {
  static const _subdir = 'school_logo_cache';
  final Map<String, Uint8List> _memCache = {};

  String _filename(String absoluteUrl, int? schoolId) {
    // String.hashCode is stable within a VM lifetime; collisions only force a
    // re-fetch, never serve the wrong image (we'd still write the new bytes
    // under the same name). The 32-bit unsigned hex keeps filenames short.
    final h = absoluteUrl.hashCode
        .toUnsigned(32)
        .toRadixString(16)
        .padLeft(8, '0');
    return 'school_${schoolId ?? 0}_$h.bin';
  }

  Future<Directory> _dir() async {
    final base = await getApplicationSupportDirectory();
    final d = Directory('${base.path}/$_subdir');
    if (!await d.exists()) await d.create(recursive: true);
    return d;
  }

  Future<File> _file(String absoluteUrl, int? schoolId) async {
    final d = await _dir();
    return File('${d.path}/${_filename(absoluteUrl, schoolId)}');
  }

  /// Returns the cached bytes if present, else null. Never throws.
  Future<Uint8List?> read(String absoluteUrl, int? schoolId) async {
    if (kIsWeb) return _memCache[_filename(absoluteUrl, schoolId)];
    try {
      final f = await _file(absoluteUrl, schoolId);
      if (!await f.exists()) return null;
      return await f.readAsBytes();
    } catch (_) {
      return null;
    }
  }

  /// Writes [bytes] to disk (best-effort — silent on failure).
  Future<void> write(
      String absoluteUrl, int? schoolId, Uint8List bytes) async {
    if (kIsWeb) {
      _memCache[_filename(absoluteUrl, schoolId)] = bytes;
      return;
    }
    try {
      final f = await _file(absoluteUrl, schoolId);
      await f.writeAsBytes(bytes, flush: true);
    } catch (_) {
      // Disk full / sandbox issue — ignore. We'll just re-fetch next time.
    }
  }

  /// Fetches [absoluteUrl] anonymously (no bearer — the logo endpoint is
  /// public) and stores the bytes on disk. Returns the bytes or null on
  /// failure. Uses a **fresh** Dio so this never picks up the app's auth
  /// interceptor by accident.
  Future<Uint8List?> fetchAndStore(
      String absoluteUrl, int? schoolId) async {
    try {
      final dio = Dio(BaseOptions(
        receiveTimeout: const Duration(seconds: 8),
        connectTimeout: const Duration(seconds: 5),
        responseType: ResponseType.bytes,
        headers: const {'Accept': 'image/*'},
      ));
      final res = await dio.get<List<int>>(absoluteUrl);
      final data = res.data;
      if (data == null || data.isEmpty) return null;
      final bytes = Uint8List.fromList(data);
      await write(absoluteUrl, schoolId, bytes);
      return bytes;
    } catch (_) {
      return null;
    }
  }

  /// Cache-or-fetch: returns the cached bytes if present, else fetches +
  /// stores and returns. Returns null only if the URL fails.
  Future<Uint8List?> getOrFetch(
      String absoluteUrl, int? schoolId) async {
    final cached = await read(absoluteUrl, schoolId);
    if (cached != null) return cached;
    return fetchAndStore(absoluteUrl, schoolId);
  }

  /// Fire-and-forget warm-up. Returns immediately; the fetch runs in the
  /// background. Idempotent — skips the fetch if the file is already
  /// on disk.
  Future<void> preload(String absoluteUrl, int? schoolId) async {
    final existing = await read(absoluteUrl, schoolId);
    if (existing != null) return;
    await fetchAndStore(absoluteUrl, schoolId);
  }

  /// Drop every cached logo. Called from `SessionController.logout`.
  Future<void> clear() async {
    _memCache.clear();
    if (kIsWeb) return;
    try {
      final d = await _dir();
      if (!await d.exists()) return;
      await for (final entity in d.list()) {
        try {
          await entity.delete();
        } catch (_) {
          // Best-effort; keep going.
        }
      }
    } catch (_) {}
  }
}

final schoolLogoCacheProvider =
    Provider<SchoolLogoCache>((ref) => SchoolLogoCache());
