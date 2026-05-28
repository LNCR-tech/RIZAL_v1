import 'package:aura_app/features/events/application/event_schedule_cache.dart';
import 'package:aura_app/shared/models/event.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

EventTimeStatus _sample(int hourOffset) {
  // Local DateTime — the JSON round-trip normalizes through the device's
  // local zone, so using `DateTime.utc(...)` here would produce values whose
  // wall-clock differs after deserialization.
  final base = DateTime(2026, 5, 28, 0).add(Duration(hours: hourOffset));
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

    test('clear() empties the cache and persistence', () async {
      final c1 = EventScheduleCache();
      await c1.load();
      await c1.put(5, _sample(0));
      await c1.clear();

      final c2 = EventScheduleCache();
      await c2.load();
      expect(c2.get(5), isNull);
      expect(c2.keys(), isEmpty);
    });
  });
}
