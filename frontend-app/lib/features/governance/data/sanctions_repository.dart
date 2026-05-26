import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_paths.dart';
import '../../../core/network/dio_client.dart';
import '../../../shared/models/sanctions.dart';

class SanctionsRepository {
  SanctionsRepository(this._client);
  final DioClient _client;

  Future<SanctionsDashboard> dashboard() async {
    final r = await _client.get(Api.sanctionsDashboard);
    return SanctionsDashboard.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<PaginatedSanctions> eventStudents(
    int eventId, {
    String? status,
    int skip = 0,
    int limit = 100,
  }) async {
    final r = await _client.get(Api.sanctionEventStudents(eventId),
        query: {'status': status, 'skip': skip, 'limit': limit});
    return PaginatedSanctions.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<void> approve(int eventId, int userId) =>
      _client.post(Api.sanctionApprove(eventId, userId));

  /// `GET /api/sanctions/students/me` — current student's own sanction
  /// records across every event they've been sanctioned in. Empty list when
  /// the student has no outstanding sanctions.
  Future<List<SanctionRecord>> mine() async {
    final r = await _client.get(Api.sanctionsMine);
    final raw = r.data;
    if (raw is! List) return const <SanctionRecord>[];
    return raw
        .whereType<Map>()
        .map((m) => SanctionRecord.fromJson(m.cast<String, dynamic>()))
        .toList();
  }

  /// `GET /api/sanctions/clearance-deadline` — the school-wide clearance
  /// deadline if one is active. Returns null when none is set.
  Future<ClearanceDeadline?> activeClearanceDeadline() async {
    final r = await _client.get(Api.sanctionsClearanceDeadline);
    final raw = r.data;
    if (raw is! Map) return null;
    return ClearanceDeadline.fromJson(raw.cast<String, dynamic>());
  }
}

final sanctionsRepositoryProvider = Provider<SanctionsRepository>(
  (ref) => SanctionsRepository(ref.watch(dioClientProvider)),
);
