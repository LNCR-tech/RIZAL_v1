import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/event.dart';
import '../data/events_repository.dart';

/// All events visible to the signed-in user (their schedule).
final scheduleEventsProvider =
    FutureProvider.autoDispose<List<AppEvent>>((ref) async {
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
final ongoingEventsProvider =
    FutureProvider.autoDispose<List<AppEvent>>((ref) async {
  return ref.watch(eventsRepositoryProvider).ongoing();
});
