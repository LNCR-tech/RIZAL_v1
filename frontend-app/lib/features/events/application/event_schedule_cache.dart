import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../../../shared/models/event.dart';

/// Persisted in-memory cache of [EventTimeStatus] snapshots, keyed by event id.
/// The scheduler reads from this on cold start to avoid re-fetching every
/// event's time-status before showing banner state. SharedPreferences-backed
/// because these are small JSON blobs and need to survive process death.
class EventScheduleCache {
  static const _kKey = 'aura_event_window_snapshots_v1';
  final Map<int, EventTimeStatus> _map = {};
  SharedPreferences? _prefs;

  Future<void> load() async {
    _prefs = await SharedPreferences.getInstance();
    final raw = _prefs!.getString(_kKey);
    if (raw == null) return;
    final decoded = jsonDecode(raw);
    if (decoded is! Map) return;
    decoded.forEach((k, v) {
      final id = int.tryParse(k.toString());
      if (id != null && v is Map) {
        _map[id] = EventTimeStatus.fromJson(v.cast<String, dynamic>());
      }
    });
  }

  EventTimeStatus? get(int eventId) => _map[eventId];
  Iterable<int> keys() => _map.keys;

  Future<void> put(int eventId, EventTimeStatus snapshot) async {
    _map[eventId] = snapshot;
    await _flush();
  }

  Future<void> replace(Map<int, EventTimeStatus> next) async {
    _map
      ..clear()
      ..addAll(next);
    await _flush();
  }

  Future<void> clear() async {
    _map.clear();
    await _flush();
  }

  Future<void> _flush() async {
    final prefs = _prefs;
    if (prefs == null) return;
    final encoded = jsonEncode({
      for (final entry in _map.entries) '${entry.key}': _toJson(entry.value),
    });
    await prefs.setString(_kKey, encoded);
  }

  Map<String, dynamic> _toJson(EventTimeStatus s) => {
        'event_status': s.eventStatus,
        'current_time': s.currentTime?.toIso8601String(),
        'check_in_opens_at': s.checkInOpensAt?.toIso8601String(),
        'start_time': s.startTime?.toIso8601String(),
        'end_time': s.endTime?.toIso8601String(),
        'late_threshold_time': s.lateThresholdTime?.toIso8601String(),
        'attendance_override_active': s.attendanceOverrideActive,
        'sign_out_opens_at': s.signOutOpensAt?.toIso8601String(),
        'effective_sign_out_closes_at':
            s.effectiveSignOutClosesAt?.toIso8601String(),
        'timezone_name': s.timezoneName,
      };
}

// Single global pointer so the scheduler, sync, and banner all see the same
// in-memory state. The cache is small and serializes cheaply.
EventScheduleCache _singleton = EventScheduleCache();
EventScheduleCache get eventScheduleCache => _singleton;
// Test-only setter to allow replacing the singleton in unit tests.
set eventScheduleCacheForTest(EventScheduleCache value) => _singleton = value;
