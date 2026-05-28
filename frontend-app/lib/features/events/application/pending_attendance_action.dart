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
