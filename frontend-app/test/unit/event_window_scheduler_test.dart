import 'package:aura_app/features/events/application/event_window_scheduler.dart';
import 'package:aura_app/shared/models/event.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

DateTime _pht(int hour, int minute) {
  final utcHour = hour - 8;
  if (utcHour >= 0) {
    return DateTime.utc(2026, 5, 28, utcHour, minute);
  }
  return DateTime.utc(2026, 5, 27, utcHour + 24, minute);
}

EventTimeStatus _status({
  required int checkInOpensAtHour,
  required int checkInOpensAtMinute,
  required int signOutOpensAtHour,
  required int signOutOpensAtMinute,
  required int effectiveSignOutClosesAtHour,
  required int effectiveSignOutClosesAtMinute,
  String status = 'before_check_in',
  bool overrideActive = false,
  DateTime? currentTime,
}) {
  final checkInOpensAt = _pht(checkInOpensAtHour, checkInOpensAtMinute);
  final signOutOpensAt = _pht(signOutOpensAtHour, signOutOpensAtMinute);
  final effectiveSignOutClosesAt =
      _pht(effectiveSignOutClosesAtHour, effectiveSignOutClosesAtMinute);
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
  // Initialize at top-level: tz.getLocation runs during group declaration,
  // which is BEFORE setUpAll would fire.
  tzdata.initializeTimeZones();

  group('computeWindowFireTimes', () {
    final manila = tz.getLocation('Asia/Manila');
    final now = tz.TZDateTime(manila, 2026, 5, 28, 7, 0); // 07:00 PHT

    test('full schedule for a future event with all slots in the future', () {
      // Event at 08:00, ends at 10:00.
      final s = _status(
        checkInOpensAtHour: 8,
        checkInOpensAtMinute: 0,
        signOutOpensAtHour: 10,
        signOutOpensAtMinute: 0,
        effectiveSignOutClosesAtHour: 10,
        effectiveSignOutClosesAtMinute: 30,
      );
      final slots = computeWindowFireTimes(eventId: 1, snapshot: s, now: now);
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
      // Check-in opened at 06:55, sign-out at 10:00.
      final s = _status(
        checkInOpensAtHour: 6,
        checkInOpensAtMinute: 55,
        signOutOpensAtHour: 10,
        signOutOpensAtMinute: 0,
        effectiveSignOutClosesAtHour: 10,
        effectiveSignOutClosesAtMinute: 30,
      );
      final slots = computeWindowFireTimes(eventId: 1, snapshot: s, now: now);
      // checkInLead (06:45) and checkInOpen (06:55) are past. Skipped.
      expect(slots.map((s) => s.phase), [
        SchedulePhase.signOutLead,
        SchedulePhase.signOutOpen,
        SchedulePhase.signOutClosingSoon,
      ]);
    });

    test('skips signOutLead when it would collapse onto checkInOpensAt', () {
      // Very short event: 08:00–08:05.
      final s = _status(
        checkInOpensAtHour: 8,
        checkInOpensAtMinute: 0,
        signOutOpensAtHour: 8,
        signOutOpensAtMinute: 5,
        effectiveSignOutClosesAtHour: 8,
        effectiveSignOutClosesAtMinute: 25,
      );
      final slots = computeWindowFireTimes(eventId: 1, snapshot: s, now: now);
      expect(slots.map((s) => s.phase).contains(SchedulePhase.signOutLead),
          isFalse);
    });

    test('skips closingSoon when grace window is shorter than 10 minutes', () {
      // sign-out open at 10:00, closes at 10:05 → closingSoon at 09:55 < open.
      final s = _status(
        checkInOpensAtHour: 8,
        checkInOpensAtMinute: 0,
        signOutOpensAtHour: 10,
        signOutOpensAtMinute: 0,
        effectiveSignOutClosesAtHour: 10,
        effectiveSignOutClosesAtMinute: 5,
      );
      final slots = computeWindowFireTimes(eventId: 1, snapshot: s, now: now);
      expect(
          slots.map((s) => s.phase).contains(SchedulePhase.signOutClosingSoon),
          isFalse);
    });

    test('skips entire event when override is active and snapshot is stale',
        () {
      final s = _status(
        checkInOpensAtHour: 8,
        checkInOpensAtMinute: 0,
        signOutOpensAtHour: 10,
        signOutOpensAtMinute: 0,
        effectiveSignOutClosesAtHour: 10,
        effectiveSignOutClosesAtMinute: 30,
        overrideActive: true,
        currentTime: now.subtract(const Duration(minutes: 5)),
      );
      final slots = computeWindowFireTimes(eventId: 1, snapshot: s, now: now);
      expect(slots, isEmpty);
    });

    test('stable notification ids: baseOffset + eventId*10 + phase index', () {
      final s = _status(
        checkInOpensAtHour: 8,
        checkInOpensAtMinute: 0,
        signOutOpensAtHour: 10,
        signOutOpensAtMinute: 0,
        effectiveSignOutClosesAtHour: 10,
        effectiveSignOutClosesAtMinute: 30,
      );
      final slots = computeWindowFireTimes(eventId: 42, snapshot: s, now: now);
      expect(slots.first.notificationId, 100420); // 100000 + 42*10 + 0
      expect(slots.last.notificationId, 100424); // 100000 + 42*10 + 4
    });

    test('skips checkInLead when within 10 min of checkInOpensAt', () {
      // Check-in opens 07:05 → lead would be 06:55 which is past.
      final s = _status(
        checkInOpensAtHour: 7,
        checkInOpensAtMinute: 5,
        signOutOpensAtHour: 10,
        signOutOpensAtMinute: 0,
        effectiveSignOutClosesAtHour: 10,
        effectiveSignOutClosesAtMinute: 30,
      );
      final slots = computeWindowFireTimes(eventId: 1, snapshot: s, now: now);
      expect(slots.first.phase, SchedulePhase.checkInOpen);
    });
  });
}
