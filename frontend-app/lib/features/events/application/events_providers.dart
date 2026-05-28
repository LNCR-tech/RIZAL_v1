import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/realtime/live_ticker.dart';
import '../../../core/realtime/polling_pace.dart';
import '../../../shared/models/event.dart';
import '../data/events_repository.dart';

/// All events visible to the signed-in user (their schedule).
///
/// Live: refetches every 30s while foregrounded so newly-published
/// events (created by an admin or governance officer on another
/// device) appear without manual refresh.
final scheduleEventsProvider =
    FutureProvider.autoDispose<List<AppEvent>>((ref) async {
  ref.watch(livePollingTickerProvider(PollingPace.medium));
  return ref.watch(eventsRepositoryProvider).list(limit: 200);
});

/// A single event's details.
final eventDetailProvider =
    FutureProvider.autoDispose.family<AppEvent, int>((ref, id) async {
  return ref.watch(eventsRepositoryProvider).detail(id);
});

/// Live timing/state for an event (drives the attendance window UI).
final eventTimeStatusProvider =
    FutureProvider.autoDispose.family<EventTimeStatus, int>((ref, id) async {
  return ref.watch(eventsRepositoryProvider).timeStatus(id);
});

/// Currently ongoing events (used by the quick-scan tab).
///
/// Live: refetches every 30s. Drives the "this event is happening
/// right now" surface; needs to be fresh enough that a student
/// arriving at an event sees it without a manual refresh.
final ongoingEventsProvider =
    FutureProvider.autoDispose<List<AppEvent>>((ref) async {
  ref.watch(livePollingTickerProvider(PollingPace.medium));
  return ref.watch(eventsRepositoryProvider).ongoing();
});
