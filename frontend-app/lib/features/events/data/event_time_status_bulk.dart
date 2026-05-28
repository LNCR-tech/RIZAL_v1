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
