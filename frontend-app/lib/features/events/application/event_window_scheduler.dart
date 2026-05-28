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

  /// Offset so our notification IDs never collide with the geofence feature's
  /// raw event-id IDs. Event ids in the real backend are well under 100k.
  static const int baseOffset = 100000;
  int get notificationId => baseOffset + eventId * 10 + phase.index;
}

const Duration _leadTime = Duration(minutes: 10);
const Duration _overrideStalenessGate = Duration(seconds: 60);

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

  final out = <EventWindowSlot>[];

  tz.TZDateTime? asLocal(DateTime? d) =>
      d == null ? null : tz.TZDateTime.from(d, now.location);

  final ci = asLocal(snapshot.checkInOpensAt);
  final so = asLocal(snapshot.signOutOpensAt);
  final sc = asLocal(snapshot.effectiveSignOutClosesAt);

  void emit(SchedulePhase phase, tz.TZDateTime at) {
    if (!at.isAfter(now)) return;
    out.add(EventWindowSlot(eventId: eventId, phase: phase, fireAt: at));
  }

  if (ci != null) {
    final lead = ci.subtract(_leadTime);
    if (lead.isAfter(now)) {
      out.add(EventWindowSlot(
          eventId: eventId, phase: SchedulePhase.checkInLead, fireAt: lead));
    }
    emit(SchedulePhase.checkInOpen, ci);
  }

  if (so != null) {
    final lead = so.subtract(_leadTime);
    final tooEarly = ci != null && !lead.isAfter(ci);
    if (!tooEarly) emit(SchedulePhase.signOutLead, lead);
    emit(SchedulePhase.signOutOpen, so);
  }

  if (sc != null && so != null) {
    final lead = sc.subtract(_leadTime);
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
    final pendingOurs =
        pending.where((p) => _ownsId(p.id)).map((p) => p.id).toSet();

    // Cancel ones no longer wanted.
    for (final id in pendingOurs.difference(desired.keys.toSet())) {
      await _plugin.cancel(id: id);
    }
    // Schedule (or re-schedule) every desired slot. `cancel` first to handle
    // the case where the fire time moved.
    final details = _details();
    for (final slot in desired.values) {
      final name = eventNamesById[slot.eventId] ?? 'an event';
      await _plugin.cancel(id: slot.notificationId);
      await _plugin.zonedSchedule(
        id: slot.notificationId,
        title: _titleFor(slot.phase, name),
        body: _bodyFor(slot.phase, name),
        scheduledDate: slot.fireAt,
        notificationDetails: details,
        androidScheduleMode: androidMode,
        payload: _payloadFor(slot),
      );
    }
  }

  /// Cancel every event-window notification (used on logout / toggle off).
  Future<void> cancelAll() async {
    final pending = await _plugin.pendingNotificationRequests();
    for (final p in pending) {
      if (_ownsId(p.id)) await _plugin.cancel(id: p.id);
    }
  }

  /// Our notification ids live in `[baseOffset, baseOffset + max_event_id*10 + 4]`
  /// and `(id - baseOffset) % 10` is in `0..4`. The geofence feature uses raw
  /// `event.id` (well under baseOffset), so the ranges never collide.
  bool _ownsId(int id) {
    if (id < EventWindowSlot.baseOffset) return false;
    final delta = id - EventWindowSlot.baseOffset;
    final phaseIndex = delta % 10;
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
