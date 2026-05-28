# Event window reminders — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Notify the user on time when an event becomes ready for check-in or sign-out, aligned exactly with the backend's `check_in_opens_at` and `sign_out_opens_at` thresholds, without disturbing the existing geofence-based nearby check-in feature.

**Architecture:** A new `EventWindowScheduler` calls `GET /events/{id}/time-status` for events within a 48-hour horizon, caches the responses, and schedules up to five `flutter_local_notifications.zonedSchedule` fires per event in Asia/Manila TZ. An `eventPhaseProvider` joins cached snapshots with a 30-second ticker to drive an in-app `EventPhaseBanner`. A new `eventWindowRemindersProvider` gates the whole feature. The existing `geofence_background.dart` plumbing is extended **additively only** (new channel, new payload variants accepted by the dispatcher).

**Tech Stack:** Flutter / Dart 3 · Riverpod hand-written notifiers · `flutter_local_notifications` 21 · `timezone` package (Asia/Manila) · `shared_preferences` · `dio` · existing Aura design tokens.

**Spec:** `docs/superpowers/specs/2026-05-28-event-window-reminders-design.md`

**Path corrections from the spec:**
- Account tab is at `frontend-app/lib/features/shell/account_tab.dart` (spec said `features/account/...`).
- The existing nearby check-in toggle lives in the **Notifications** section, not "Beta features". The new toggle goes beside it for discoverability.

---

## File Structure

| File | Responsibility |
|---|---|
| `lib/features/events/application/event_window_reminders_controller.dart` (new) | Persisted toggle `eventWindowRemindersProvider` |
| `lib/features/events/data/event_time_status_bulk.dart` (new) | Parallel `Future.wait` over `/events/{id}/time-status` |
| `lib/features/events/application/event_schedule_cache.dart` (new) | In-memory + `SharedPreferences` cache of `EventTimeStatus` keyed by event id |
| `lib/features/events/application/event_window_scheduler.dart` (new) | Pure computation of `(eventId, phase, fireTime)` tuples + `flutter_local_notifications.zonedSchedule` driver |
| `lib/features/events/application/event_window_sync.dart` (new) | `eventWindowSyncProvider` — wires toggle + scheduleEventsProvider + lifecycle + ticker to scheduler |
| `lib/features/events/application/event_phase_provider.dart` (new) | Derives current banner content from cache + 30s ticker |
| `lib/features/events/presentation/widgets/event_phase_banner.dart` (new) | The gradient in-app banner |
| `lib/features/events/application/pending_attendance_action.dart` (new) | New sibling provider `pendingAttendanceActionProvider` carrying an `AttendanceAction` hint |
| `lib/features/events/application/geofence_background.dart` (modify, additive) | Register `event_window` channel; extend `_dispatch` to parse new payload variants |
| `lib/main.dart` (modify) | Initialize the `timezone` database + Asia/Manila local |
| `lib/app/app.dart` (modify) | `ref.watch(eventWindowSyncProvider)` for the session |
| `lib/features/student/presentation/student_home_screen.dart` (modify) | Mount `EventPhaseBanner` above `NearbyEventBanner`; consume action hint |
| `lib/features/shell/account_tab.dart` (modify) | Add toggle tile in the Notifications section |
| `pubspec.yaml` (modify) | Bump to `1.36.0+80`; add explicit `timezone` dep |
| `CHANGELOG.md` (modify) | `[Unreleased]` entry |
| `test/unit/event_window_scheduler_test.dart` (new) | Pure timing tests |
| `test/unit/event_phase_provider_test.dart` (new) | Phase derivation tests |
| `test/unit/event_schedule_cache_test.dart` (new) | Cache round-trip tests |
| `test/widget/event_phase_banner_test.dart` (new) | Banner rendering per phase |

---

## Task 1: Add `timezone` dep and bootstrap it in `main.dart`

**Files:**
- Modify: `frontend-app/pubspec.yaml`
- Modify: `frontend-app/lib/main.dart`

- [ ] **Step 1: Add the explicit `timezone` dep to `pubspec.yaml`**

After the `flutter_local_notifications` line (around line 74 in the dependencies block), add:

```yaml
  flutter_local_notifications: ^21.0.0
  # Required by flutter_local_notifications.zonedSchedule (transitively
  # bundled, made explicit so tz.initializeTimeZones / tz.getLocation
  # imports resolve cleanly).
  timezone: ^0.9.4
  native_geofence: ^1.2.2
```

- [ ] **Step 2: Run `flutter pub get`**

Run from `frontend-app/`:
```bash
flutter pub get
```
Expected: `Got dependencies!` with no errors.

- [ ] **Step 3: Initialize the timezone database in `main.dart`**

Replace the current `main.dart` body with this exact content:

```dart
import 'package:device_preview/device_preview.dart';
import 'package:flutter/foundation.dart' show kReleaseMode;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import 'app/app.dart';
import 'core/config/app_config.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  // Initialize the IANA timezone database for flutter_local_notifications
  // .zonedSchedule. Asia/Manila is the canonical event timezone used by the
  // backend (backend/app/services/event_time_status.py:DEFAULT_EVENT_TIMEZONE).
  tzdata.initializeTimeZones();
  tz.setLocalLocation(tz.getLocation('Asia/Manila'));

  runApp(
    ProviderScope(
      // DevicePreview shows the app inside a selectable phone frame on
      // web/desktop (debug/profile only). On a real device it's a no-op.
      child: DevicePreview(
        enabled: !kReleaseMode && AppConfig.devicePreviewEnabled,
        builder: (context) => const AuraApp(),
      ),
    ),
  );
}
```

- [ ] **Step 4: Run analyze**

Run from `frontend-app/`:
```bash
flutter analyze lib/main.dart
```
Expected: no issues.

- [ ] **Step 5: Commit**

Run from repo root:
```bash
git add frontend-app/pubspec.yaml frontend-app/pubspec.lock frontend-app/lib/main.dart
git commit -m "$(cat <<'EOF'
feat(frontend-app): wire timezone init for scheduled notifications

Sets Asia/Manila as the local TZ for flutter_local_notifications
.zonedSchedule so reminders align with the backend's canonical event
timezone. Foundation for event window reminders.
EOF
)"
```

---

## Task 2: Persisted toggle — `eventWindowRemindersProvider`

**Files:**
- Create: `frontend-app/lib/features/events/application/event_window_reminders_controller.dart`
- Create: `frontend-app/test/unit/event_window_reminders_controller_test.dart`

- [ ] **Step 1: Write the failing test**

Create `frontend-app/test/unit/event_window_reminders_controller_test.dart`:

```dart
import 'package:aura_app/features/events/application/event_window_reminders_controller.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('EventWindowRemindersController', () {
    setUp(() {
      SharedPreferences.setMockInitialValues({});
    });

    test('defaults to true (opt-out) when nothing is persisted', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      expect(container.read(eventWindowRemindersProvider), isTrue);
    });

    test('persists explicit off across containers', () async {
      final c1 = ProviderContainer();
      c1.read(eventWindowRemindersProvider.notifier).set(false);
      // Wait one microtask for the persist call to settle.
      await Future.microtask(() {});
      c1.dispose();

      final c2 = ProviderContainer();
      addTearDown(c2.dispose);
      // Wait for the async restore.
      await Future.delayed(const Duration(milliseconds: 20));

      expect(c2.read(eventWindowRemindersProvider), isFalse);
    });
  });
}
```

- [ ] **Step 2: Run the test, see it fail**

Run from `frontend-app/`:
```bash
flutter test test/unit/event_window_reminders_controller_test.dart
```
Expected: FAIL — `event_window_reminders_controller.dart` does not exist.

- [ ] **Step 3: Implement the controller**

Create `frontend-app/lib/features/events/application/event_window_reminders_controller.dart`:

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Toggle for the time-based "event window reminders" feature. Separate from
/// [autoCheckInProvider] (location-based geofence prompt). Default ON — this
/// feature does not read location continuously; it only schedules local OS
/// notifications, so the battery cost is negligible.
class EventWindowRemindersController extends Notifier<bool> {
  static const _kKey = 'aura_event_window_reminders';
  SharedPreferences? _prefs;

  @override
  bool build() {
    Future.microtask(_restore);
    return true;
  }

  Future<void> _restore() async {
    _prefs = await SharedPreferences.getInstance();
    final stored = _prefs!.getBool(_kKey);
    if (stored != null) state = stored;
  }

  void set(bool value) {
    state = value;
    _prefs?.setBool(_kKey, value);
  }
}

final eventWindowRemindersProvider =
    NotifierProvider<EventWindowRemindersController, bool>(
        EventWindowRemindersController.new);
```

- [ ] **Step 4: Run the test, see it pass**

```bash
flutter test test/unit/event_window_reminders_controller_test.dart
```
Expected: PASS — both tests green.

- [ ] **Step 5: Commit**

```bash
git add frontend-app/lib/features/events/application/event_window_reminders_controller.dart \
        frontend-app/test/unit/event_window_reminders_controller_test.dart
git commit -m "feat(frontend-app): add eventWindowRemindersProvider (toggle, default on)"
```

---

## Task 3: `EventScheduleCache` — persisted snapshots

**Files:**
- Create: `frontend-app/lib/features/events/application/event_schedule_cache.dart`
- Create: `frontend-app/test/unit/event_schedule_cache_test.dart`

- [ ] **Step 1: Write the failing test**

Create `frontend-app/test/unit/event_schedule_cache_test.dart`:

```dart
import 'package:aura_app/features/events/application/event_schedule_cache.dart';
import 'package:aura_app/shared/models/event.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

EventTimeStatus _sample(int hourOffset) {
  final base = DateTime.utc(2026, 5, 28, 0).add(Duration(hours: hourOffset));
  return EventTimeStatus(
    eventStatus: 'before_check_in',
    currentTime: base,
    checkInOpensAt: base.add(const Duration(minutes: 30)),
    startTime: base.add(const Duration(hours: 1)),
    endTime: base.add(const Duration(hours: 3)),
    signOutOpensAt: base.add(const Duration(hours: 3)),
    effectiveSignOutClosesAt: base.add(const Duration(hours: 3, minutes: 20)),
    timezoneName: 'Asia/Manila',
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('EventScheduleCache', () {
    setUp(() => SharedPreferences.setMockInitialValues({}));

    test('round-trips snapshots across instances', () async {
      final c1 = EventScheduleCache();
      await c1.load();
      await c1.put(42, _sample(0));
      await c1.put(43, _sample(1));

      final c2 = EventScheduleCache();
      await c2.load();
      expect(c2.get(42)?.checkInOpensAt, _sample(0).checkInOpensAt);
      expect(c2.get(43)?.checkInOpensAt, _sample(1).checkInOpensAt);
    });

    test('replace() rewrites the entire map atomically', () async {
      final c = EventScheduleCache();
      await c.load();
      await c.put(1, _sample(0));
      await c.put(2, _sample(1));
      await c.replace({3: _sample(2)});

      expect(c.get(1), isNull);
      expect(c.get(2), isNull);
      expect(c.get(3)?.checkInOpensAt, _sample(2).checkInOpensAt);
    });

    test('keys() returns currently cached event ids', () async {
      final c = EventScheduleCache();
      await c.load();
      await c.put(7, _sample(0));
      await c.put(9, _sample(1));
      expect(c.keys().toSet(), {7, 9});
    });
  });
}
```

- [ ] **Step 2: Run the test, see it fail**

```bash
flutter test test/unit/event_schedule_cache_test.dart
```
Expected: FAIL — `event_schedule_cache.dart` not found.

- [ ] **Step 3: Implement the cache**

Create `frontend-app/lib/features/events/application/event_schedule_cache.dart`:

```dart
import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../../../shared/models/event.dart';
import '../../../shared/utils/json.dart';

/// Persisted in-memory cache of [EventTimeStatus] snapshots, keyed by event id.
/// The scheduler reads from this on cold start to avoid re-fetching every event's
/// time-status before it can show banner state. SharedPreferences-backed because
/// these are small JSON blobs and need to survive process death.
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

// Keep a single global pointer so the scheduler, sync, and banner all see the
// same in-memory state. The cache is small and serializes cheaply.
EventScheduleCache _singleton = EventScheduleCache();
EventScheduleCache get eventScheduleCache => _singleton;
// Test-only setter to allow replacing the singleton in unit tests.
set eventScheduleCacheForTest(EventScheduleCache value) => _singleton = value;
```

Note: `json.dart` (`asDate`, `asInt`, etc.) is already imported via `event.dart`'s `EventTimeStatus.fromJson`, so we don't need to import it directly.

- [ ] **Step 4: Run the test, see it pass**

```bash
flutter test test/unit/event_schedule_cache_test.dart
```
Expected: PASS — all three tests green.

- [ ] **Step 5: Commit**

```bash
git add frontend-app/lib/features/events/application/event_schedule_cache.dart \
        frontend-app/test/unit/event_schedule_cache_test.dart
git commit -m "feat(frontend-app): add EventScheduleCache (persisted time-status snapshots)"
```

---

## Task 4: Bulk `time-status` fetch helper

**Files:**
- Create: `frontend-app/lib/features/events/data/event_time_status_bulk.dart`

- [ ] **Step 1: Implement the helper**

Create `frontend-app/lib/features/events/data/event_time_status_bulk.dart`:

```dart
import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/event.dart';
import 'events_repository.dart';

/// Parallel fetcher for `/events/{id}/time-status`. Backend has no bulk
/// endpoint, so we issue per-event GETs with a concurrency cap to avoid
/// socket exhaustion on weak networks. Errors per-event are swallowed: a
/// single 5xx must not nuke the entire schedule. The caller treats absence
/// as "keep the previous snapshot" via [EventScheduleCache].
class EventTimeStatusBulk {
  EventTimeStatusBulk(this._repo);
  final EventsRepository _repo;

  static const int _concurrency = 6;

  Future<Map<int, EventTimeStatus>> fetch(Iterable<int> eventIds) async {
    final ids = eventIds.toList(growable: false);
    final out = <int, EventTimeStatus>{};
    for (var i = 0; i < ids.length; i += _concurrency) {
      final batch = ids.sublist(i, (i + _concurrency).clamp(0, ids.length));
      final results = await Future.wait(batch.map(_one), eagerError: false);
      for (var j = 0; j < batch.length; j++) {
        final r = results[j];
        if (r != null) out[batch[j]] = r;
      }
    }
    return out;
  }

  Future<EventTimeStatus?> _one(int id) async {
    try {
      return await _repo.timeStatus(id);
    } catch (_) {
      return null;
    }
  }
}

final eventTimeStatusBulkProvider = Provider<EventTimeStatusBulk>(
  (ref) => EventTimeStatusBulk(ref.watch(eventsRepositoryProvider)),
);
```

- [ ] **Step 2: Run analyze**

```bash
flutter analyze lib/features/events/data/event_time_status_bulk.dart
```
Expected: no issues.

- [ ] **Step 3: Commit**

```bash
git add frontend-app/lib/features/events/data/event_time_status_bulk.dart
git commit -m "feat(frontend-app): add bulk time-status fetcher with concurrency cap"
```

---

## Task 5: `EventWindowScheduler` — pure timing + zonedSchedule

This task is split: a **pure-function** computation that the test pins exactly, then a thin driver that calls `flutter_local_notifications`.

**Files:**
- Create: `frontend-app/lib/features/events/application/event_window_scheduler.dart`
- Create: `frontend-app/test/unit/event_window_scheduler_test.dart`

- [ ] **Step 1: Write the failing test**

Create `frontend-app/test/unit/event_window_scheduler_test.dart`:

```dart
import 'package:aura_app/features/events/application/event_window_scheduler.dart';
import 'package:aura_app/shared/models/event.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

EventTimeStatus _status({
  required DateTime checkInOpensAt,
  required DateTime signOutOpensAt,
  required DateTime effectiveSignOutClosesAt,
  String status = 'before_check_in',
  bool overrideActive = false,
  DateTime? currentTime,
}) {
  return EventTimeStatus(
    eventStatus: status,
    currentTime: currentTime,
    checkInOpensAt: checkInOpensAt,
    startTime: checkInOpensAt.add(const Duration(minutes: 30)),
    endTime: signOutOpensAt,
    signOutOpensAt: signOutOpensAt,
    effectiveSignOutClosesAt: effectiveSignOutClosesAt,
    attendanceOverrideActive: overrideActive,
    timezoneName: 'Asia/Manila',
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() {
    tzdata.initializeTimeZones();
    tz.setLocalLocation(tz.getLocation('Asia/Manila'));
  });

  group('computeWindowFireTimes', () {
    final manila = tz.getLocation('Asia/Manila');
    final now = tz.TZDateTime(manila, 2026, 5, 28, 7, 0); // 07:00 PHT

    test('full schedule for a future event with all slots in the future', () {
      // Event at 08:00, ends at 10:00, grace 30m → close at 10:30
      // check-in opens 08:00 (no early window), sign-out opens 10:00.
      final s = _status(
        checkInOpensAt: DateTime(2026, 5, 28, 8, 0),
        signOutOpensAt: DateTime(2026, 5, 28, 10, 0),
        effectiveSignOutClosesAt: DateTime(2026, 5, 28, 10, 30),
      );
      final slots = computeWindowFireTimes(eventId: 1, snapshot: s, now: now);
      // Phases: checkInLead(07:50), checkInOpen(08:00),
      //         signOutLead(09:50), signOutOpen(10:00),
      //         signOutClosingSoon(10:20)
      expect(slots.map((s) => s.phase), [
        SchedulePhase.checkInLead,
        SchedulePhase.checkInOpen,
        SchedulePhase.signOutLead,
        SchedulePhase.signOutOpen,
        SchedulePhase.signOutClosingSoon,
      ]);
      expect(slots.first.fireAt.hour, 7);
      expect(slots.first.fireAt.minute, 50);
      expect(slots.last.fireAt.hour, 10);
      expect(slots.last.fireAt.minute, 20);
    });

    test('skips past slots', () {
      // Event already in early check-in: check-in opened at 06:55.
      final s = _status(
        checkInOpensAt: DateTime(2026, 5, 28, 6, 55),
        signOutOpensAt: DateTime(2026, 5, 28, 10, 0),
        effectiveSignOutClosesAt: DateTime(2026, 5, 28, 10, 30),
      );
      final slots = computeWindowFireTimes(eventId: 1, snapshot: s, now: now);
      // checkInLead (06:45) is past. checkInOpen (06:55) is past. Skipped.
      expect(slots.map((s) => s.phase), [
        SchedulePhase.signOutLead,
        SchedulePhase.signOutOpen,
        SchedulePhase.signOutClosingSoon,
      ]);
    });

    test('skips signOutLead when it would collapse onto checkInOpensAt', () {
      // Very short event: 08:00–08:05.
      final s = _status(
        checkInOpensAt: DateTime(2026, 5, 28, 8, 0),
        signOutOpensAt: DateTime(2026, 5, 28, 8, 5),
        effectiveSignOutClosesAt: DateTime(2026, 5, 28, 8, 25),
      );
      final slots = computeWindowFireTimes(eventId: 1, snapshot: s, now: now);
      // signOutLead would be 07:55, which is BEFORE check-in opens (08:00).
      // Skip slot 2.
      expect(slots.map((s) => s.phase).contains(SchedulePhase.signOutLead),
          isFalse);
    });

    test('skips closingSoon when grace window is shorter than 10 minutes', () {
      // 10:00 sign-out open, 10:05 close → closingSoon at 09:55 is before open.
      final s = _status(
        checkInOpensAt: DateTime(2026, 5, 28, 8, 0),
        signOutOpensAt: DateTime(2026, 5, 28, 10, 0),
        effectiveSignOutClosesAt: DateTime(2026, 5, 28, 10, 5),
      );
      final slots = computeWindowFireTimes(eventId: 1, snapshot: s, now: now);
      expect(
          slots.map((s) => s.phase).contains(SchedulePhase.signOutClosingSoon),
          isFalse);
    });

    test('skips entire event when override is active and snapshot is stale', () {
      // currentTime is 60+ seconds older than now → defer.
      final s = _status(
        checkInOpensAt: DateTime(2026, 5, 28, 8, 0),
        signOutOpensAt: DateTime(2026, 5, 28, 10, 0),
        effectiveSignOutClosesAt: DateTime(2026, 5, 28, 10, 30),
        overrideActive: true,
        currentTime: now.subtract(const Duration(minutes: 5)),
      );
      final slots = computeWindowFireTimes(eventId: 1, snapshot: s, now: now);
      expect(slots, isEmpty);
    });

    test('stable notification ids: eventId*10 + phase index', () {
      final s = _status(
        checkInOpensAt: DateTime(2026, 5, 28, 8, 0),
        signOutOpensAt: DateTime(2026, 5, 28, 10, 0),
        effectiveSignOutClosesAt: DateTime(2026, 5, 28, 10, 30),
      );
      final slots = computeWindowFireTimes(eventId: 42, snapshot: s, now: now);
      expect(slots.first.notificationId, 420); // 42 * 10 + 0
      expect(slots.last.notificationId, 424); // 42 * 10 + 4
    });
  });
}
```

- [ ] **Step 2: Run the test, see it fail**

```bash
flutter test test/unit/event_window_scheduler_test.dart
```
Expected: FAIL — `event_window_scheduler.dart` not found.

- [ ] **Step 3: Implement the scheduler (pure compute + driver)**

Create `frontend-app/lib/features/events/application/event_window_scheduler.dart`:

```dart
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/timezone.dart' as tz;

import '../../../shared/models/event.dart';

/// Five phases of a single event's notification schedule, in fire-time order.
enum SchedulePhase {
  checkInLead, // 10 min before check_in_opens_at
  checkInOpen, // exactly check_in_opens_at
  signOutLead, // 10 min before sign_out_opens_at
  signOutOpen, // exactly sign_out_opens_at
  signOutClosingSoon, // 10 min before effective_sign_out_closes_at
}

/// One concrete notification to schedule for an event.
class EventWindowSlot {
  EventWindowSlot({
    required this.eventId,
    required this.phase,
    required this.fireAt,
  });
  final int eventId;
  final SchedulePhase phase;
  final tz.TZDateTime fireAt;

  int get notificationId => eventId * 10 + phase.index;
}

const _leadTime = Duration(minutes: 10);
const _overrideStalenessGate = Duration(seconds: 60);

/// Pure function: given a server snapshot and the current time, return all
/// notifications that should be scheduled for this event, in fire-time order.
/// Applies the skip rules from the spec.
List<EventWindowSlot> computeWindowFireTimes({
  required int eventId,
  required EventTimeStatus snapshot,
  required tz.TZDateTime now,
}) {
  // Defer scheduling for events with a live override when our cached snapshot
  // pre-dates the override decision — the next sync will bring a fresh one.
  if (snapshot.attendanceOverrideActive && snapshot.currentTime != null) {
    final age = now.difference(snapshot.currentTime!);
    if (age > _overrideStalenessGate) return const [];
  }

  final checkInOpensAt = snapshot.checkInOpensAt;
  final signOutOpensAt = snapshot.signOutOpensAt;
  final signOutClosesAt = snapshot.effectiveSignOutClosesAt;
  final out = <EventWindowSlot>[];

  tz.TZDateTime? asLocal(DateTime? d) =>
      d == null ? null : tz.TZDateTime.from(d, now.location);

  final ci = asLocal(checkInOpensAt);
  final so = asLocal(signOutOpensAt);
  final sc = asLocal(signOutClosesAt);

  void emit(SchedulePhase phase, tz.TZDateTime at) {
    if (!at.isAfter(now)) return; // skip past
    out.add(EventWindowSlot(eventId: eventId, phase: phase, fireAt: at));
  }

  if (ci != null) {
    final lead = ci.subtract(_leadTime);
    // Slot 0: skip if lead time is at or before now (slot 1 covers it).
    if (lead.isAfter(now)) {
      out.add(EventWindowSlot(
          eventId: eventId, phase: SchedulePhase.checkInLead, fireAt: lead));
    }
    emit(SchedulePhase.checkInOpen, ci);
  }

  if (so != null) {
    final lead = so.subtract(_leadTime);
    // Slot 2: skip if lead time would land before check-in opens (very short
    // events where lead times collapse).
    final tooEarly = ci != null && !lead.isAfter(ci);
    if (!tooEarly) emit(SchedulePhase.signOutLead, lead);
    emit(SchedulePhase.signOutOpen, so);
  }

  if (sc != null && so != null) {
    final lead = sc.subtract(_leadTime);
    // Slot 4: skip if grace window is < 10 minutes (lead lands at or before
    // sign-out open).
    if (lead.isAfter(so)) emit(SchedulePhase.signOutClosingSoon, lead);
  }

  return out;
}

/// Side-effecting driver: pushes the computed slots into the OS scheduler.
/// Pure compute lives above; this is the thin shell that talks to the plugin.
class EventWindowScheduler {
  EventWindowScheduler(this._plugin);

  final FlutterLocalNotificationsPlugin _plugin;

  static const String channelId = 'event_window';
  static const String channelName = 'Event window reminders';
  static const String channelDescription =
      'Reminders when check-in or sign-out opens for events you can attend.';

  /// Cancel any stale `event_window`-owned notifications, then schedule the
  /// next batch. [slotsByEvent] is the desired state for every tracked event.
  Future<void> sync({
    required Map<int, List<EventWindowSlot>> slotsByEvent,
    required Map<int, String> eventNamesById,
    AndroidScheduleMode androidMode = AndroidScheduleMode.exactAllowWhileIdle,
  }) async {
    final desired = <int, EventWindowSlot>{};
    for (final list in slotsByEvent.values) {
      for (final s in list) {
        desired[s.notificationId] = s;
      }
    }

    final pending = await _plugin.pendingNotificationRequests();
    final pendingOurs = pending
        .where((p) => _ownsId(p.id))
        .map((p) => p.id)
        .toSet();

    // Cancel ones no longer wanted.
    for (final id in pendingOurs.difference(desired.keys.toSet())) {
      await _plugin.cancel(id);
    }
    // Schedule (or re-schedule) every desired slot. `cancel` first to handle
    // the case where the fire time moved.
    final details = _details();
    for (final slot in desired.values) {
      final name = eventNamesById[slot.eventId] ?? 'an event';
      await _plugin.cancel(slot.notificationId);
      await _plugin.zonedSchedule(
        slot.notificationId,
        _titleFor(slot.phase, name),
        _bodyFor(slot.phase, name),
        slot.fireAt,
        details,
        androidScheduleMode: androidMode,
        payload: _payloadFor(slot),
      );
    }
  }

  /// Cancel every event-window notification (used on logout / toggle off).
  Future<void> cancelAll() async {
    final pending = await _plugin.pendingNotificationRequests();
    for (final p in pending) {
      if (_ownsId(p.id)) await _plugin.cancel(p.id);
    }
  }

  /// We own notification ids that match `eventId * 10 + phase.index` for
  /// phase.index in 0..4. The geofence feature uses raw `event.id` values
  /// (no multiplication), so there's no collision when eventId fits the
  /// normal int range (the geofence id is at most a couple million; ours
  /// is multiplied by 10 so they live in different ranges, and our valid
  /// last digits 0..4 are a further filter).
  bool _ownsId(int id) {
    if (id <= 0) return false;
    final phaseIndex = id % 10;
    return phaseIndex >= 0 && phaseIndex < SchedulePhase.values.length;
  }

  NotificationDetails _details() => const NotificationDetails(
        android: AndroidNotificationDetails(
          channelId,
          channelName,
          channelDescription: channelDescription,
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: DarwinNotificationDetails(),
      );

  String _titleFor(SchedulePhase p, String name) {
    switch (p) {
      case SchedulePhase.checkInLead:
        return 'Check-in opens in 10 min';
      case SchedulePhase.checkInOpen:
        return 'Check-in is open: $name';
      case SchedulePhase.signOutLead:
        return 'Sign-out opens in 10 min';
      case SchedulePhase.signOutOpen:
        return 'Sign-out is open: $name';
      case SchedulePhase.signOutClosingSoon:
        return 'Sign-out closes in 10 min';
    }
  }

  String _bodyFor(SchedulePhase p, String name) {
    switch (p) {
      case SchedulePhase.checkInLead:
      case SchedulePhase.checkInOpen:
        return 'Tap to sign in to $name.';
      case SchedulePhase.signOutLead:
      case SchedulePhase.signOutOpen:
      case SchedulePhase.signOutClosingSoon:
        return 'Tap to sign out of $name.';
    }
  }

  String _payloadFor(EventWindowSlot s) {
    final action = (s.phase == SchedulePhase.signOutLead ||
            s.phase == SchedulePhase.signOutOpen ||
            s.phase == SchedulePhase.signOutClosingSoon)
        ? 'signout'
        : 'checkin';
    return 'checkin:${s.eventId}:$action';
  }
}
```

Note: The `_ownsId` filter is the load-bearing claim that we won't accidentally cancel geofence notifications. The geofence notification ids use the raw event id (e.g. 47), which `id % 10 == 7` — that **does** satisfy our `phaseIndex < 5` check incorrectly. Need to refine:

Wait — geofence uses ids like 1, 2, 3...100, etc. Some of those would satisfy `id % 10 < 5`. **This is a collision risk.** Refine `_ownsId` to use a sentinel: we'll add an offset of 100,000 to our notification IDs so they never collide with raw event IDs (which are typically < 100,000).

Update the code above by replacing the `notificationId` getter and the `_ownsId`:

```dart
class EventWindowSlot {
  // ...
  static const int _baseOffset = 100000;
  int get notificationId => _baseOffset + eventId * 10 + phase.index;
}

// inside EventWindowScheduler:
bool _ownsId(int id) {
  if (id < EventWindowSlot._baseOffset) return false;
  final delta = id - EventWindowSlot._baseOffset;
  final phaseIndex = delta % 10;
  return phaseIndex >= 0 && phaseIndex < SchedulePhase.values.length;
}
```

Also update the test expectations:
- `slots.first.notificationId` should now be `100000 + 42*10 + 0 = 100420`.
- `slots.last.notificationId` should now be `100424`.

Apply both updates before the next step.

- [ ] **Step 4: Run the test, see it pass**

```bash
flutter test test/unit/event_window_scheduler_test.dart
```
Expected: PASS — all six tests green.

- [ ] **Step 5: Commit**

```bash
git add frontend-app/lib/features/events/application/event_window_scheduler.dart \
        frontend-app/test/unit/event_window_scheduler_test.dart
git commit -m "feat(frontend-app): add EventWindowScheduler (pure timing + zonedSchedule)"
```

---

## Task 6: Extend `geofence_background.dart` — additive only

**Files:**
- Modify: `frontend-app/lib/features/events/application/geofence_background.dart`

The existing channel `nearby_checkin`, the existing `nearbyGeofenceCallback`, and the existing `pendingCheckInProvider` (`StateProvider<int?>`) must remain unchanged. We only add: (a) exposure of the shared `FlutterLocalNotificationsPlugin` instance, (b) registration of the new Android channel, (c) parsing of the new payload format.

- [ ] **Step 1: Read the existing file to confirm baseline**

```bash
sed -n '1,40p' frontend-app/lib/features/events/application/geofence_background.dart
```
(Or use the Read tool. Just for reviewer reference.)

- [ ] **Step 2: Update `_dispatch` to parse the new payload format (additively)**

Find this block in `frontend-app/lib/features/events/application/geofence_background.dart` (around line 88–92):

```dart
  static void _dispatch(String? payload) {
    if (payload == null || !payload.startsWith(_payloadPrefix)) return;
    final id = int.tryParse(payload.substring(_payloadPrefix.length));
    if (id != null) onCheckIn?.call(id);
  }
```

Replace with:

```dart
  static void _dispatch(String? payload) {
    if (payload == null || !payload.startsWith(_payloadPrefix)) return;
    final rest = payload.substring(_payloadPrefix.length);
    // Accept both "checkin:<id>" (legacy geofence) and
    // "checkin:<id>:checkin" / "checkin:<id>:signout" (new event-window
    // reminders). The geofence flow only needs the id; the action hint is
    // surfaced via the sibling [pendingAttendanceActionProvider].
    final colonIdx = rest.indexOf(':');
    final idPart = colonIdx == -1 ? rest : rest.substring(0, colonIdx);
    final actionPart = colonIdx == -1 ? null : rest.substring(colonIdx + 1);
    final id = int.tryParse(idPart);
    if (id == null) return;
    onCheckIn?.call(id);
    if (actionPart != null) onAttendanceAction?.call(id, actionPart);
  }
```

- [ ] **Step 3: Add the action callback hook + new channel registration**

Add this field next to the existing `onCheckIn` declaration (around line 67–68):

```dart
  /// Called (main isolate) when an event-window notification is tapped, with
  /// the requested attendance action ("checkin" or "signout"). Optional —
  /// the geofence-only flow leaves this null.
  static void Function(int eventId, String action)? onAttendanceAction;
```

Then update `initNotifications` to also register the new channel. Find the existing block (around line 70–86):

```dart
  static Future<void> initNotifications() async {
    if (_notifReady) return;
    _notifReady = true;
    await _notifications.initialize(
      settings: _initSettings,
      onDidReceiveNotificationResponse: (r) => _dispatch(r.payload),
    );
    await _notifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.requestNotificationsPermission();
    // Cold start: app launched by tapping a notification.
    final launch = await _notifications.getNotificationAppLaunchDetails();
    if (launch?.didNotificationLaunchApp ?? false) {
      _dispatch(launch!.notificationResponse?.payload);
    }
  }
```

Replace the body with this version (adds explicit registration of the new
`event_window` channel via `AndroidNotificationChannel`):

```dart
  static Future<void> initNotifications() async {
    if (_notifReady) return;
    _notifReady = true;
    await _notifications.initialize(
      settings: _initSettings,
      onDidReceiveNotificationResponse: (r) => _dispatch(r.payload),
    );
    final android = _notifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();
    await android?.requestNotificationsPermission();
    // Pre-register the event-window channel so it appears in Android
    // settings even before the first scheduled fire.
    await android?.createNotificationChannel(
      const AndroidNotificationChannel(
        'event_window',
        'Event window reminders',
        description:
            'Reminders when check-in or sign-out opens for events you can attend.',
        importance: Importance.high,
      ),
    );
    // Cold start: app launched by tapping a notification.
    final launch = await _notifications.getNotificationAppLaunchDetails();
    if (launch?.didNotificationLaunchApp ?? false) {
      _dispatch(launch!.notificationResponse?.payload);
    }
  }
```

- [ ] **Step 4: Expose the shared plugin instance**

Add at the bottom of `class GeofenceBackground` (just before the closing brace):

```dart
  /// Shared FlutterLocalNotificationsPlugin instance — the event-window
  /// scheduler uses this so we don't double-initialize the plugin.
  static FlutterLocalNotificationsPlugin get notifications => _notifications;
```

- [ ] **Step 5: Run analyze on the modified file**

```bash
flutter analyze lib/features/events/application/geofence_background.dart
```
Expected: no issues.

- [ ] **Step 6: Run the full existing test suite to confirm nothing regressed**

```bash
flutter test
```
Expected: all existing tests still pass.

- [ ] **Step 7: Commit**

```bash
git add frontend-app/lib/features/events/application/geofence_background.dart
git commit -m "feat(frontend-app): additive event_window channel + payload parsing"
```

---

## Task 7: `pendingAttendanceActionProvider` (action hint)

**Files:**
- Create: `frontend-app/lib/features/events/application/pending_attendance_action.dart`

- [ ] **Step 1: Implement the provider**

Create `frontend-app/lib/features/events/application/pending_attendance_action.dart`:

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// What the user intended when they tapped an event-window notification.
/// Sibling to [pendingCheckInProvider] (which carries the event id). Reading
/// both lets the student-home listener pre-route to the right scan mode.
enum AttendanceAction { checkin, signout }

AttendanceAction? attendanceActionFromString(String? s) {
  switch (s) {
    case 'checkin':
      return AttendanceAction.checkin;
    case 'signout':
      return AttendanceAction.signout;
    default:
      return null;
  }
}

final pendingAttendanceActionProvider =
    StateProvider<AttendanceAction?>((ref) => null);
```

- [ ] **Step 2: Wire the geofence callback to set it**

Edit `frontend-app/lib/features/events/application/geofence_background.dart`,
find the existing `geofenceBackgroundProvider`:

```dart
final geofenceBackgroundProvider = Provider<void>((ref) {
  GeofenceBackground.onCheckIn =
      (id) => ref.read(pendingCheckInProvider.notifier).state = id;
  GeofenceBackground.initNotifications();
  ...
```

Replace the assignment block at the top with:

```dart
final geofenceBackgroundProvider = Provider<void>((ref) {
  GeofenceBackground.onCheckIn =
      (id) => ref.read(pendingCheckInProvider.notifier).state = id;
  GeofenceBackground.onAttendanceAction = (id, action) {
    ref.read(pendingCheckInProvider.notifier).state = id;
    ref.read(pendingAttendanceActionProvider.notifier).state =
        attendanceActionFromString(action);
  };
  GeofenceBackground.initNotifications();
```

Add the import at the top of the file:

```dart
import 'pending_attendance_action.dart';
```

- [ ] **Step 3: Run analyze + tests**

```bash
flutter analyze
flutter test test/unit/
```
Expected: no issues, no regressions.

- [ ] **Step 4: Commit**

```bash
git add frontend-app/lib/features/events/application/pending_attendance_action.dart \
        frontend-app/lib/features/events/application/geofence_background.dart
git commit -m "feat(frontend-app): pendingAttendanceActionProvider hint sibling"
```

---

## Task 8: `eventWindowSyncProvider` — wire it all together

**Files:**
- Create: `frontend-app/lib/features/events/application/event_window_sync.dart`

- [ ] **Step 1: Implement the sync provider**

Create `frontend-app/lib/features/events/application/event_window_sync.dart`:

```dart
import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:timezone/timezone.dart' as tz;

import '../../../shared/models/event.dart';
import '../data/event_time_status_bulk.dart';
import 'event_schedule_cache.dart';
import 'event_window_reminders_controller.dart';
import 'event_window_scheduler.dart';
import 'events_providers.dart';
import 'geofence_background.dart';

/// Wires the scheduler to the schedule events list + lifecycle. Watch this
/// once at the app root so it lives for the session. Sync runs:
///   - whenever scheduleEventsProvider emits new data (pull-to-refresh, etc.)
///   - whenever the toggle flips on
///   - whenever the cache is empty on cold start (handled by the first emit)
/// Throttled: skip if last sync < 5 minutes ago, unless eventsHash changed.
class EventWindowSyncController extends Notifier<DateTime?> {
  EventWindowScheduler? _scheduler;
  DateTime _lastSyncAt = DateTime.fromMillisecondsSinceEpoch(0);
  bool _running = false;
  String _lastEventsHash = '';

  @override
  DateTime? build() {
    final enabled = ref.watch(eventWindowRemindersProvider);
    _scheduler ??= EventWindowScheduler(GeofenceBackground.notifications);

    if (!enabled) {
      Future.microtask(() async {
        await _scheduler!.cancelAll();
        await eventScheduleCache.clear();
      });
      return null;
    }

    // Listen for events list updates.
    ref.listen<AsyncValue<List<AppEvent>>>(
      scheduleEventsProvider,
      (_, next) => next.whenData((events) => _maybeSync(events)),
      fireImmediately: true,
    );

    return null;
  }

  Future<void> _maybeSync(List<AppEvent> events) async {
    if (_running) return;
    _running = true;
    try {
      // Build a stable signature so we don't re-sync identical lists.
      final inScope = events.where(_inScope).toList()
        ..sort((a, b) => a.id.compareTo(b.id));
      final hash = inScope
          .map((e) =>
              '${e.id}:${e.startDatetime?.toIso8601String()}:${e.endDatetime?.toIso8601String()}')
          .join('|');
      final age = DateTime.now().difference(_lastSyncAt);
      if (hash == _lastEventsHash && age < const Duration(minutes: 5)) return;

      // Make sure the cache has been hydrated at least once.
      await eventScheduleCache.load();

      // Fetch fresh time-status for in-scope events.
      final bulk = ref.read(eventTimeStatusBulkProvider);
      final fresh = await bulk.fetch(inScope.map((e) => e.id));

      // Replace cache for in-scope events; leave others (just in case).
      final next = <int, EventTimeStatus>{
        for (final e in inScope)
          if (fresh[e.id] != null) e.id: fresh[e.id]!,
      };
      await eventScheduleCache.replace(next);

      // Compute slots per event.
      final manila = tz.getLocation('Asia/Manila');
      final now = tz.TZDateTime.now(manila);
      final slotsByEvent = <int, List<EventWindowSlot>>{};
      final namesById = <int, String>{};
      for (final e in inScope) {
        final snap = next[e.id];
        if (snap == null) continue;
        slotsByEvent[e.id] =
            computeWindowFireTimes(eventId: e.id, snapshot: snap, now: now);
        namesById[e.id] = e.name;
      }

      await _scheduler!
          .sync(slotsByEvent: slotsByEvent, eventNamesById: namesById);

      _lastEventsHash = hash;
      _lastSyncAt = DateTime.now();
      state = _lastSyncAt;
    } catch (_) {
      // Swallow — next trigger will retry. We keep the old schedule intact.
    } finally {
      _running = false;
    }
  }

  bool _inScope(AppEvent e) {
    final start = e.startDatetime;
    final end = e.endDatetime;
    if (start == null || end == null) return false;
    if (e.isCancelled) return false;
    final now = DateTime.now();
    // End hasn't passed (with a generous grace so we still cover the
    // sign-out close window).
    if (end.add(const Duration(hours: 2)).isBefore(now)) return false;
    // Starts within the next 48 hours (or already started).
    if (start.isAfter(now.add(const Duration(hours: 48)))) return false;
    return true;
  }
}

final eventWindowSyncProvider =
    NotifierProvider<EventWindowSyncController, DateTime?>(
        EventWindowSyncController.new);
```

- [ ] **Step 2: Add `ref.watch(eventWindowSyncProvider)` to the app root**

Edit `frontend-app/lib/app/app.dart`. Find this line (around line 28):

```dart
    // Keep the background geofence check-in alive for the session (notification
    // init + tap routing + geofence sync) — gated by the Nearby check-in toggle.
    ref.watch(geofenceBackgroundProvider);
```

Add immediately after:

```dart
    // Time-based event window reminders (check-in / sign-out opens) — gated
    // by the Event window reminders toggle.
    ref.watch(eventWindowSyncProvider);
```

And add the import near the top:

```dart
import '../features/events/application/event_window_sync.dart';
```

- [ ] **Step 3: Run analyze**

```bash
flutter analyze lib/features/events/application/event_window_sync.dart lib/app/app.dart
```
Expected: no issues.

- [ ] **Step 4: Commit**

```bash
git add frontend-app/lib/features/events/application/event_window_sync.dart \
        frontend-app/lib/app/app.dart
git commit -m "feat(frontend-app): wire eventWindowSyncProvider at app root"
```

---

## Task 9: `eventPhaseProvider` + `EventPhaseBanner`

**Files:**
- Create: `frontend-app/lib/features/events/application/event_phase_provider.dart`
- Create: `frontend-app/lib/features/events/presentation/widgets/event_phase_banner.dart`
- Create: `frontend-app/test/unit/event_phase_provider_test.dart`

- [ ] **Step 1: Write the failing test**

Create `frontend-app/test/unit/event_phase_provider_test.dart`:

```dart
import 'package:aura_app/features/events/application/event_phase_provider.dart';
import 'package:aura_app/shared/models/event.dart';
import 'package:flutter_test/flutter_test.dart';

EventTimeStatus _status({
  required String state,
  DateTime? signOutClosesAt,
}) =>
    EventTimeStatus(
      eventStatus: state,
      effectiveSignOutClosesAt: signOutClosesAt,
      timezoneName: 'Asia/Manila',
    );

void main() {
  group('selectBannerPhase', () {
    final now = DateTime(2026, 5, 28, 10, 0);

    test('sign_out_open beats early_check_in', () {
      final r = selectBannerPhase(
        candidates: [
          BannerCandidate(eventId: 1, name: 'A', status: _status(state: 'early_check_in')),
          BannerCandidate(eventId: 2, name: 'B', status: _status(state: 'sign_out_open')),
        ],
        now: now,
      );
      expect(r?.eventId, 2);
      expect(r?.phase, BannerPhase.signOutOpen);
    });

    test('closing-soon shown when within 10 min of close', () {
      final closes = now.add(const Duration(minutes: 5));
      final r = selectBannerPhase(
        candidates: [
          BannerCandidate(
              eventId: 9,
              name: 'C',
              status: _status(state: 'sign_out_open', signOutClosesAt: closes)),
        ],
        now: now,
      );
      expect(r?.phase, BannerPhase.signOutClosingSoon);
    });

    test('returns null when no candidate is in an actionable phase', () {
      final r = selectBannerPhase(
        candidates: [
          BannerCandidate(eventId: 1, name: 'A', status: _status(state: 'before_check_in')),
          BannerCandidate(eventId: 2, name: 'B', status: _status(state: 'closed')),
        ],
        now: now,
      );
      expect(r, isNull);
    });

    test('late_check_in surfaces as checkInOpen', () {
      final r = selectBannerPhase(
        candidates: [
          BannerCandidate(eventId: 4, name: 'D', status: _status(state: 'late_check_in')),
        ],
        now: now,
      );
      expect(r?.phase, BannerPhase.checkInOpen);
    });
  });
}
```

- [ ] **Step 2: Run the test, see it fail**

```bash
flutter test test/unit/event_phase_provider_test.dart
```
Expected: FAIL.

- [ ] **Step 3: Implement the phase provider**

Create `frontend-app/lib/features/events/application/event_phase_provider.dart`:

```dart
import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/event.dart';
import 'event_schedule_cache.dart';
import 'event_window_reminders_controller.dart';
import 'events_providers.dart';

/// Banner phase priorities, highest first.
enum BannerPhase {
  signOutOpen,
  checkInOpen,
  signOutClosingSoon,
}

class BannerCandidate {
  BannerCandidate({
    required this.eventId,
    required this.name,
    required this.status,
  });
  final int eventId;
  final String name;
  final EventTimeStatus status;
}

class BannerSelection {
  BannerSelection({required this.eventId, required this.name, required this.phase});
  final int eventId;
  final String name;
  final BannerPhase phase;
}

/// Pure selection: pick the highest-priority candidate, if any.
BannerSelection? selectBannerPhase({
  required List<BannerCandidate> candidates,
  required DateTime now,
}) {
  BannerSelection? best;
  int bestRank = -1;

  for (final c in candidates) {
    final phase = _phaseFor(c.status, now);
    if (phase == null) continue;
    final rank = _rank(phase);
    if (rank > bestRank) {
      bestRank = rank;
      best = BannerSelection(eventId: c.eventId, name: c.name, phase: phase);
    }
  }
  return best;
}

BannerPhase? _phaseFor(EventTimeStatus s, DateTime now) {
  final state = s.eventStatus;
  if (state == 'sign_out_open') {
    final closes = s.effectiveSignOutClosesAt;
    if (closes != null &&
        closes.difference(now) <= const Duration(minutes: 10) &&
        closes.isAfter(now)) {
      return BannerPhase.signOutClosingSoon;
    }
    return BannerPhase.signOutOpen;
  }
  if (state == 'early_check_in' || state == 'late_check_in') {
    return BannerPhase.checkInOpen;
  }
  return null;
}

int _rank(BannerPhase p) => switch (p) {
      BannerPhase.signOutOpen => 3,
      BannerPhase.checkInOpen => 2,
      BannerPhase.signOutClosingSoon => 1,
    };

/// 30-second ticker so the banner re-evaluates on the wall clock.
final _bannerTickerProvider = StreamProvider.autoDispose<DateTime>((ref) {
  final c = StreamController<DateTime>();
  c.add(DateTime.now());
  final t = Stream.periodic(const Duration(seconds: 30), (_) => DateTime.now());
  final sub = t.listen(c.add);
  ref.onDispose(() {
    sub.cancel();
    c.close();
  });
  return c.stream;
});

/// Reads the current banner selection from cache + a 30-second ticker.
/// Returns null when reminders are off, or no event qualifies.
final eventPhaseProvider =
    Provider.autoDispose<BannerSelection?>((ref) {
  final enabled = ref.watch(eventWindowRemindersProvider);
  if (!enabled) return null;
  final now = ref.watch(_bannerTickerProvider).valueOrNull ?? DateTime.now();
  final events = ref.watch(scheduleEventsProvider).valueOrNull ?? const [];

  final candidates = <BannerCandidate>[];
  for (final e in events) {
    final snap = eventScheduleCache.get(e.id);
    if (snap == null) continue;
    candidates.add(BannerCandidate(eventId: e.id, name: e.name, status: snap));
  }
  return selectBannerPhase(candidates: candidates, now: now);
});
```

- [ ] **Step 4: Run the test, see it pass**

```bash
flutter test test/unit/event_phase_provider_test.dart
```
Expected: PASS — all four tests green.

- [ ] **Step 5: Implement the banner widget**

Create `frontend-app/lib/features/events/presentation/widgets/event_phase_banner.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_tokens.dart';
import '../../application/event_phase_provider.dart';
import '../../application/pending_attendance_action.dart';
import '../../events/application/events_providers.dart' as ev;
// (note: kept consistent with directory layout — see file path)

/// In-app prompt shown when an event the user can attend is currently in
/// an actionable phase (early_check_in, late_check_in, sign_out_open) or
/// is about to close sign-out. Sits above [NearbyEventBanner] on Home so
/// the time-based reminder is the first thing the user sees.
class EventPhaseBanner extends ConsumerWidget {
  const EventPhaseBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sel = ref.watch(eventPhaseProvider);
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 320),
      switchInCurve: Curves.easeOutCubic,
      switchOutCurve: Curves.easeIn,
      transitionBuilder: (child, anim) => SizeTransition(
        sizeFactor: anim,
        axisAlignment: -1,
        child: FadeTransition(opacity: anim, child: child),
      ),
      child: sel == null
          ? const SizedBox(width: double.infinity)
          : Padding(
              key: ValueKey('${sel.eventId}-${sel.phase.name}'),
              padding: const EdgeInsets.only(bottom: AppSpacing.x20),
              child: _Card(selection: sel, onTap: () => _tap(ref, sel)),
            ),
    );
  }

  void _tap(WidgetRef ref, BannerSelection sel) {
    ref.read(ev.pendingCheckInProvider.notifier).state = sel.eventId;
    ref.read(pendingAttendanceActionProvider.notifier).state =
        sel.phase == BannerPhase.checkInOpen
            ? AttendanceAction.checkin
            : AttendanceAction.signout;
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.selection, required this.onTap});
  final BannerSelection selection;
  final VoidCallback onTap;

  ({String label, IconData icon, String cta, Color tint}) _spec(AppTokens t) {
    switch (selection.phase) {
      case BannerPhase.signOutOpen:
        return (
          label: 'SIGN-OUT IS OPEN',
          icon: Icons.logout_rounded,
          cta: 'Sign out',
          tint: t.accent,
        );
      case BannerPhase.checkInOpen:
        return (
          label: 'CHECK-IN IS OPEN',
          icon: Icons.login_rounded,
          cta: 'Check in',
          tint: t.accent,
        );
      case BannerPhase.signOutClosingSoon:
        return (
          label: 'LAST CALL: SIGN OUT',
          icon: Icons.logout_rounded,
          cta: 'Sign out',
          tint: t.late_,
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final spec = _spec(t);
    final on = t.onAccent;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(22),
        child: Ink(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [spec.tint, t.accentDark],
            ),
            borderRadius: BorderRadius.circular(22),
            boxShadow: [
              BoxShadow(
                color: spec.tint.withOpacity(0.35),
                blurRadius: 18,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          padding: const EdgeInsets.all(AppSpacing.x16),
          child: Row(
            children: [
              _PulseDot(color: on, icon: spec.icon),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      spec.label,
                      style: textTheme.labelSmall?.copyWith(
                        color: on.withOpacity(0.85),
                        letterSpacing: 0.8,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      selection.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: textTheme.titleLarge?.copyWith(color: on),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: AppSpacing.x12),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
                decoration: BoxDecoration(
                  color: t.surface,
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      spec.cta,
                      style: textTheme.labelLarge?.copyWith(
                        color: t.accentDark,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Icon(Icons.arrow_forward_rounded, size: 16, color: t.accentDark),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PulseDot extends StatefulWidget {
  const _PulseDot({required this.color, required this.icon});
  final Color color;
  final IconData icon;

  @override
  State<_PulseDot> createState() => _PulseDotState();
}

class _PulseDotState extends State<_PulseDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: const Duration(seconds: 2))
        ..repeat();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final c = widget.color;
    return SizedBox(
      width: 40,
      height: 40,
      child: Stack(
        alignment: Alignment.center,
        children: [
          if (!reduce)
            AnimatedBuilder(
              animation: _c,
              builder: (context, _) {
                final v = _c.value;
                return Container(
                  width: 18 + 22 * v,
                  height: 18 + 22 * v,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: c.withOpacity((1 - v) * 0.35),
                  ),
                );
              },
            ),
          Container(
            width: 30,
            height: 30,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: c.withOpacity(0.18),
            ),
            child: Icon(widget.icon, size: 18, color: c),
          ),
        ],
      ),
    );
  }
}
```

Note: the import line `import '../../events/application/events_providers.dart' as ev;` should be `import '../../application/events_providers.dart' as ev;` — adjust the relative path because the file lives at `widgets/event_phase_banner.dart` whose parent is `presentation/`, two ups to `events/`. Use:

```dart
import '../../application/events_providers.dart' as ev;
```

Replace the import in the code above before saving the file.

Also, `t.late_` may not exist verbatim in `AppTokens`. Look up the late color in
`lib/core/theme/app_tokens.dart`; the existing project uses `t.late_` or `t.warning` for amber. Check before saving and substitute the matching token name (likely `t.late_` based on the design system table for late = `#FB923C`).

- [ ] **Step 6: Run analyze**

```bash
flutter analyze lib/features/events/presentation/widgets/event_phase_banner.dart \
                lib/features/events/application/event_phase_provider.dart
```
Expected: no issues.

- [ ] **Step 7: Commit**

```bash
git add frontend-app/lib/features/events/application/event_phase_provider.dart \
        frontend-app/lib/features/events/presentation/widgets/event_phase_banner.dart \
        frontend-app/test/unit/event_phase_provider_test.dart
git commit -m "feat(frontend-app): add eventPhaseProvider + EventPhaseBanner widget"
```

---

## Task 10: Mount the banner on student Home + consume action hint

**Files:**
- Modify: `frontend-app/lib/features/student/presentation/student_home_screen.dart`

- [ ] **Step 1: Add the banner and the action-hint listener**

Edit `frontend-app/lib/features/student/presentation/student_home_screen.dart`. Two changes:

**1.** Add these imports near the other event imports (around line 14):

```dart
import '../../events/application/pending_attendance_action.dart';
import '../../events/presentation/widgets/event_phase_banner.dart';
```

**2.** Replace the existing `ref.listen` block (around lines 38–49) with this version that consumes the action hint:

```dart
    // A tapped check-in notification (foreground or cold start) routes here —
    // open the attendance screen for that event directly.
    ref.listen<int?>(pendingCheckInProvider, (_, id) async {
      if (id == null) return;
      ref.read(pendingCheckInProvider.notifier).state = null;
      // Read + clear the action hint so it doesn't leak into the next route.
      final _hint = ref.read(pendingAttendanceActionProvider);
      ref.read(pendingAttendanceActionProvider.notifier).state = null;
      try {
        final event = await ref.read(eventDetailProvider(id).future);
        if (context.mounted) {
          Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => AttendanceScreen(event: event)),
          );
        }
      } catch (_) {/* event unavailable */}
    });
```

Note: `_hint` is read for completeness (to clear the provider) but not consumed by `AttendanceScreen` in this revision — the screen already infers action from event state. Leaving the underscore-prefixed name signals intentional ignore.

**3.** In the `ListView` `children: staggered([...])` block (around line 90), replace:

```dart
          const NearbyEventBanner(),
```

with:

```dart
          const EventPhaseBanner(),
          const NearbyEventBanner(),
```

- [ ] **Step 2: Run analyze**

```bash
flutter analyze lib/features/student/presentation/student_home_screen.dart
```
Expected: no issues.

- [ ] **Step 3: Commit**

```bash
git add frontend-app/lib/features/student/presentation/student_home_screen.dart
git commit -m "feat(frontend-app): mount EventPhaseBanner above NearbyEventBanner on Home"
```

---

## Task 11: Account toggle tile

**Files:**
- Modify: `frontend-app/lib/features/shell/account_tab.dart`

- [ ] **Step 1: Add the toggle tile**

Edit `frontend-app/lib/features/shell/account_tab.dart`.

**1.** Add this import near the other event imports (around line 26):

```dart
import '../events/application/event_window_reminders_controller.dart';
```

**2.** In the `build` method, near the existing `final autoCheckIn = ref.watch(autoCheckInProvider);` (around line 59), add:

```dart
    final eventWindowReminders = ref.watch(eventWindowRemindersProvider);
```

**3.** In the **Notifications** `SettingsSection` (around line 266), insert the new tile immediately after the inbox tile and **before** "Nearby event check-in":

```dart
            _BetaSwitchTile(
              icon: Icons.alarm_rounded,
              iconColor: _indigo,
              title: 'Event window reminders',
              subtitle:
                  'Notify me when check-in or sign-out opens for events on my schedule.',
              value: eventWindowReminders,
              onChanged: (v) =>
                  ref.read(eventWindowRemindersProvider.notifier).set(v),
            ),
```

- [ ] **Step 2: Run analyze**

```bash
flutter analyze lib/features/shell/account_tab.dart
```
Expected: no issues.

- [ ] **Step 3: Commit**

```bash
git add frontend-app/lib/features/shell/account_tab.dart
git commit -m "feat(frontend-app): add 'Event window reminders' toggle in Notifications"
```

---

## Task 12: Banner widget test

**Files:**
- Create: `frontend-app/test/widget/event_phase_banner_test.dart`

- [ ] **Step 1: Write the widget test**

First, ensure the `test/widget` directory exists:

```bash
mkdir -p frontend-app/test/widget
```

Create `frontend-app/test/widget/event_phase_banner_test.dart`:

```dart
import 'package:aura_app/features/events/application/event_phase_provider.dart';
import 'package:aura_app/features/events/presentation/widgets/event_phase_banner.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  Widget _wrap({BannerSelection? selection}) {
    return ProviderScope(
      overrides: [
        eventPhaseProvider.overrideWith((ref) => selection),
      ],
      child: const MaterialApp(
        home: Scaffold(body: EventPhaseBanner()),
      ),
    );
  }

  testWidgets('renders empty when no phase is active', (tester) async {
    await tester.pumpWidget(_wrap(selection: null));
    await tester.pumpAndSettle();
    expect(find.text('CHECK-IN IS OPEN'), findsNothing);
    expect(find.text('SIGN-OUT IS OPEN'), findsNothing);
  });

  testWidgets('renders the check-in banner when checkInOpen', (tester) async {
    await tester.pumpWidget(_wrap(
      selection: BannerSelection(
          eventId: 1, name: 'General Assembly', phase: BannerPhase.checkInOpen),
    ));
    await tester.pumpAndSettle();
    expect(find.text('CHECK-IN IS OPEN'), findsOneWidget);
    expect(find.text('General Assembly'), findsOneWidget);
    expect(find.text('Check in'), findsOneWidget);
  });

  testWidgets('renders the sign-out banner when signOutOpen', (tester) async {
    await tester.pumpWidget(_wrap(
      selection: BannerSelection(
          eventId: 2, name: 'Departmental Meeting', phase: BannerPhase.signOutOpen),
    ));
    await tester.pumpAndSettle();
    expect(find.text('SIGN-OUT IS OPEN'), findsOneWidget);
    expect(find.text('Sign out'), findsOneWidget);
  });

  testWidgets('renders the last-call banner when signOutClosingSoon',
      (tester) async {
    await tester.pumpWidget(_wrap(
      selection: BannerSelection(
          eventId: 3,
          name: 'Departmental Meeting',
          phase: BannerPhase.signOutClosingSoon),
    ));
    await tester.pumpAndSettle();
    expect(find.text('LAST CALL: SIGN OUT'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run the test**

```bash
flutter test test/widget/event_phase_banner_test.dart
```
Expected: PASS — all four widget tests green.

- [ ] **Step 3: Commit**

```bash
git add frontend-app/test/widget/event_phase_banner_test.dart
git commit -m "test(frontend-app): EventPhaseBanner renders per phase"
```

---

## Task 13: Changelog + version bump

**Files:**
- Modify: `frontend-app/pubspec.yaml`
- Modify: `frontend-app/CHANGELOG.md`

- [ ] **Step 1: Bump version**

Edit `frontend-app/pubspec.yaml` line 4:

```yaml
version: 1.36.0+80
```

- [ ] **Step 2: Add CHANGELOG entry**

Edit `frontend-app/CHANGELOG.md`. Under the existing `## [Unreleased]` section (or insert one if missing), add:

```markdown
### Added
- **Event window reminders.** Notifies the user when an event's check-in or
  sign-out window opens, aligned to the backend's `check_in_opens_at` /
  `sign_out_opens_at` thresholds (Asia/Manila). Five scheduled fires per
  event in scope (lead + open for check-in, lead + open + closing-soon
  for sign-out), driven by `flutter_local_notifications.zonedSchedule`.
  In-app `EventPhaseBanner` mounts above `NearbyEventBanner` and surfaces
  the active phase on Home. New `eventWindowRemindersProvider` toggle
  under Account → Notifications, default on.

### Changed
- `geofence_background.dart` extended additively to register the new
  `event_window` notification channel and parse `checkin:<id>:<action>`
  payloads. Existing `nearby_checkin` channel and `NearbyEventBanner`
  flow are unchanged.
```

If `## [Unreleased]` is not present, prepend it just below the changelog
header.

- [ ] **Step 3: Commit**

```bash
git add frontend-app/pubspec.yaml frontend-app/CHANGELOG.md
git commit -m "chore(frontend-app): bump to 1.36.0+80 + changelog for window reminders"
```

---

## Task 14: Full verification

- [ ] **Step 1: Analyze the whole frontend-app**

```bash
cd frontend-app
flutter analyze
```
Expected: 0 issues.

- [ ] **Step 2: Run the full test suite**

```bash
flutter test
```
Expected: existing tests PASS + 4 new test files PASS. Total new tests: ~17.

- [ ] **Step 3: Manual smoke — accuracy check**

1. With `eventWindowRemindersProvider` on, in the admin UI create an event
   starting 2 minutes from now, `early_check_in_minutes = 0`, no geo.
2. Open the app once so it picks up the event and syncs.
3. Lock the device and wait.
4. Expect OS notification within ±5 s of the scheduled minute.
5. Tap notification: app routes straight to `AttendanceScreen` for that event.

- [ ] **Step 4: Manual smoke — banner**

1. With the app foreground, observe `EventPhaseBanner` enter within 30 s
   of the phase transitioning to `early_check_in` / `late_check_in` /
   `sign_out_open`.

- [ ] **Step 5: Manual smoke — admin edit invalidates schedule**

1. With a scheduled event 30 min away, edit it via the web admin to start
   1 hour later instead. Cold-restart the app. Confirm the schedule
   replaces the old fire times (use `dumpsys alarm | grep event_window`
   on Android via `adb` to confirm).

- [ ] **Step 6: Regression smoke — existing nearby check-in**

1. Turn on "Nearby event check-in". Turn off "Event window reminders".
2. Walk into a geofenced event's radius. Confirm the existing OS
   notification fires from the `nearby_checkin` channel.
3. Turn on both toggles. Walk into a geofenced event during its
   check-in window. Confirm both notification types fire on their
   respective channels.

- [ ] **Step 7: Regression smoke — toggle off cancels schedule**

1. Turn off "Event window reminders". Confirm that previously-scheduled
   `event_window`-owned notifications are cancelled. (Use the toggle in
   Account → Notifications.) Confirm `NearbyEventBanner` still fires
   when the user enters a geofence — unrelated.

---

## Self-review

**1. Spec coverage:**
- Backend ground truth + customization cascade → reflected in tasks 4, 5 (use server-authoritative `check_in_opens_at` / `sign_out_opens_at` from `/events/{id}/time-status`). ✓
- Hard "don't break geofence" constraint → tasks 6, 7 are explicitly additive; task 14 step 6 regression-tests it. ✓
- Five scheduled notifications + skip rules → task 5 implements all five phases, all four skip rules tested. ✓
- Re-sync triggers (app resume, schedule data change, toggle) → task 8 listens on `scheduleEventsProvider` and the toggle; `ref.watch` at app root ensures the controller is alive for the session. **Gap:** lifecycle resume (`AppLifecycleState.resumed`) not explicitly handled. Mitigation: when the app resumes, Riverpod re-evaluates `scheduleEventsProvider` (because `autoDispose` providers refire); plus the user typically pulls-to-refresh on Home. Adding a `WidgetsBindingObserver` is a follow-up improvement, not a blocker.
- In-app banner with priority order → task 9 implements `selectBannerPhase` with tested priority order. ✓
- Toggle, default ON, in Notifications section → tasks 2, 11. ✓
- Notification channel separation → task 6 registers `event_window`. ✓
- Tap routing extension → tasks 6, 7. ✓
- Failure modes (admin edits, time-status errors, permission denied) → task 4 swallows per-event errors; task 8 keeps old cache on failure. Permission denied: handled by `flutter_local_notifications` returning silently; the in-app banner still works. ✓
- Regression checks → task 14 covers all listed scenarios from the spec. ✓

**2. Placeholder scan:**
- No "TBD" / "TODO" remain. All steps contain complete code or commands. ✓
- One callout inside Task 5 about ID-collision was caught and the fix (offset by 100,000) was applied inline. ✓
- One callout in Task 9 about `t.late_` token name — engineer should verify the existing token name before saving. This is a pointer at a real existing file the engineer needs to read, not a placeholder.

**3. Type consistency:**
- `EventWindowSlot` defined in task 5, used in tasks 5 and 8. Field names match (`eventId`, `phase`, `fireAt`, `notificationId`). ✓
- `SchedulePhase` enum order matches `phase.index` math in `notificationId`. ✓
- `BannerSelection` defined and used consistently in task 9 + test + widget. ✓
- `AttendanceAction` (`checkin` / `signout`) consistent across tasks 7, 10. ✓
- `EventScheduleCache` interface (`load`, `get`, `put`, `replace`, `clear`, `keys`) consistent across tasks 3 and 8. ✓

Plan stands.

---

## Execution handoff

Plan complete and saved to
`docs/superpowers/plans/2026-05-28-event-window-reminders.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task,
   review between tasks, fast iteration with isolation. Best for not
   contaminating this conversation's context and for catching regressions
   per task.
2. **Inline Execution** — Execute tasks in this session using
   `executing-plans`, batch execution with checkpoints for review. Best
   if you want to follow along step-by-step.

Which approach?
