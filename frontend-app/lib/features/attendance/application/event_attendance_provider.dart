import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/realtime/live_ticker.dart';
import '../../../core/realtime/polling_pace.dart';
import '../../../shared/models/attendance.dart';
import '../data/attendance_repository.dart';

/// The signed-in student's attendance record for a **single event**, or
/// `null` if they haven't scanned for it yet.
///
/// Drives both:
///   * the pre-scan UI (so the capture button can read "Sign out" instead
///     of "Check in" when the student is already checked in, and disable
///     entirely when neither window is open), and
///   * the after-scan result sheet (labeled check-in / check-out times).
///
/// Auto-refreshes at the fast cadence (15s) while the attendance screen
/// is open so a kiosk scan from a parallel device shows up almost
/// immediately. Pauses with the rest of the live tickers when the app
/// goes to background.
final eventAttendanceProvider =
    FutureProvider.autoDispose.family<AttendanceRecord?, int>(
        (ref, eventId) async {
  ref.watch(livePollingTickerProvider(PollingPace.fast));
  final records = await ref
      .read(attendanceRepositoryProvider)
      .myRecords(eventId: eventId, limit: 5);
  if (records.isEmpty) return null;
  // The most recent record wins. The backend typically returns at most one
  // per (event, student) pair, but if multiple slip through (older legacy
  // rows, etc.) the freshest one is the source of truth for current state.
  records.sort((a, b) {
    final ka = a.timeIn ?? a.eventDate ?? DateTime.fromMillisecondsSinceEpoch(0);
    final kb = b.timeIn ?? b.eventDate ?? DateTime.fromMillisecondsSinceEpoch(0);
    return kb.compareTo(ka);
  });
  return records.first;
});

/// What the scan screen should do RIGHT NOW. Pure-Dart so the UI just
/// reads a single sealed value instead of juggling four flags.
sealed class AttendanceScanState {
  const AttendanceScanState();
}

/// No record yet, check-in window is open — the scan will record a
/// fresh check-in.
class CanCheckIn extends AttendanceScanState {
  const CanCheckIn();
}

/// Student is already checked in AND the sign-out window is open — the
/// scan will record a sign-out.
class CanSignOut extends AttendanceScanState {
  const CanSignOut(this.checkedInAt);
  final DateTime checkedInAt;
}

/// Student already checked in but sign-out hasn't opened yet. **No scan
/// allowed**. UI tells them when to come back.
class AlreadyCheckedIn extends AttendanceScanState {
  const AlreadyCheckedIn({required this.checkedInAt, this.signOutOpensAt});
  final DateTime checkedInAt;
  final DateTime? signOutOpensAt;
}

/// Student has both a check-in and a check-out recorded. **No scan
/// allowed** — they're done with this event.
class AttendanceComplete extends AttendanceScanState {
  const AttendanceComplete({required this.checkedInAt, required this.signedOutAt});
  final DateTime checkedInAt;
  final DateTime signedOutAt;
}

/// Event hasn't opened any window yet (or already closed everything).
/// **No scan allowed**. UI tells them why.
class WindowsClosed extends AttendanceScanState {
  const WindowsClosed({this.checkInOpensAt, this.signOutClosedAt});
  final DateTime? checkInOpensAt;
  final DateTime? signOutClosedAt;
}

/// Resolve the scan state from the two server snapshots. Pure function,
/// unit-testable.
///
/// Decision table:
///   no record       + check-in open      -> CanCheckIn
///   no record       + neither open       -> WindowsClosed
///   in, no out      + sign-out open      -> CanSignOut
///   in, no out      + sign-out NOT open  -> AlreadyCheckedIn
///   in + out        + (any)              -> AttendanceComplete
AttendanceScanState resolveAttendanceScanState({
  required AttendanceRecord? record,
  required bool checkInOpen,
  required bool signOutOpen,
  DateTime? checkInOpensAt,
  DateTime? signOutOpensAt,
  DateTime? signOutClosesAt,
}) {
  final checkedIn = record?.timeIn;
  final signedOut = record?.timeOut;

  if (checkedIn != null && signedOut != null) {
    return AttendanceComplete(checkedInAt: checkedIn, signedOutAt: signedOut);
  }
  if (checkedIn != null) {
    if (signOutOpen) return CanSignOut(checkedIn);
    return AlreadyCheckedIn(
      checkedInAt: checkedIn,
      signOutOpensAt: signOutOpensAt,
    );
  }
  if (checkInOpen) return const CanCheckIn();
  return WindowsClosed(
    checkInOpensAt: checkInOpensAt,
    signOutClosedAt: signOutClosesAt,
  );
}
