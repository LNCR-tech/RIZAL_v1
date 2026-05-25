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
}

final sanctionsRepositoryProvider = Provider<SanctionsRepository>(
  (ref) => SanctionsRepository(ref.watch(dioClientProvider)),
);
