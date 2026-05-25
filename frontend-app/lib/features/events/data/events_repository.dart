import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_paths.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/network/paginated.dart';
import '../../../shared/models/event.dart';

class EventsRepository {
  EventsRepository(this._client);
  final DioClient _client;

  Future<List<AppEvent>> list({
    String? status,
    DateTime? from,
    DateTime? to,
    String? governanceContext,
    int skip = 0,
    int limit = 100,
  }) async {
    final res = await _client.get(Api.events, query: {
      'skip': skip,
      'limit': limit,
      'status': status,
      'start_from': from?.toUtc().toIso8601String(),
      'end_at': to?.toUtc().toIso8601String(),
      'governance_context': governanceContext,
    });
    return Paginated.from(
      res.data,
      (e) => AppEvent.fromJson((e as Map).cast<String, dynamic>()),
    ).data;
  }

  Future<List<AppEvent>> ongoing() async {
    final res = await _client.get(Api.eventsOngoing);
    return Paginated.from(
      res.data,
      (e) => AppEvent.fromJson((e as Map).cast<String, dynamic>()),
    ).data;
  }

  Future<AppEvent> detail(int id) async {
    final res = await _client.get(Api.event(id));
    return AppEvent.fromJson((res.data as Map).cast<String, dynamic>());
  }

  Future<EventTimeStatus> timeStatus(int id) async {
    final res = await _client.get(Api.eventTimeStatus(id));
    return EventTimeStatus.fromJson((res.data as Map).cast<String, dynamic>());
  }

  /// Create an event. When [governanceContext] (SSG|SG|ORG) is set, the backend
  /// auto-scopes the event to the officer's governance unit (don't send
  /// department_ids/program_ids — they're overridden).
  Future<AppEvent> create(Map<String, dynamic> body,
      {String? governanceContext}) async {
    final res = await _client.post(Api.events,
        data: body, query: {'governance_context': governanceContext});
    return AppEvent.fromJson((res.data as Map).cast<String, dynamic>());
  }

  /// Update an event (`PATCH /api/events/{id}`). Send only the fields you want
  /// to change; the backend leaves omitted fields untouched. When
  /// [governanceContext] is set the backend keeps the event in that unit's scope.
  Future<AppEvent> update(int id, Map<String, dynamic> body,
      {String? governanceContext}) async {
    final res = await _client.patch(Api.event(id),
        data: body, query: {'governance_context': governanceContext});
    return AppEvent.fromJson((res.data as Map).cast<String, dynamic>());
  }

  Future<void> delete(int id) => _client.delete(Api.event(id));
}

final eventsRepositoryProvider = Provider<EventsRepository>(
  (ref) => EventsRepository(ref.watch(dioClientProvider)),
);
