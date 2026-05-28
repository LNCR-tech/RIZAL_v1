import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:timezone/timezone.dart' as tz;

import '../../../shared/models/event.dart';
import '../data/event_time_status_bulk.dart';
import 'event_schedule_cache.dart';
import 'event_window_reminders_controller.dart';
import 'event_window_scheduler.dart';
import 'events_providers.dart';
import 'geofence_background.dart';

/// Wires the scheduler to the schedule events list. Watch this once at the
/// app root so it lives for the session. Sync runs:
///   - whenever scheduleEventsProvider emits new data (pull-to-refresh, etc.)
///   - whenever the toggle flips on
///   - on cold start (the first emit fires immediately)
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

    // Listen for events list updates. fireImmediately catches the cached
    // value (or the loading state's first data emit) for cold start.
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

      // Replace cache for in-scope events. Out-of-scope events drop out.
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
