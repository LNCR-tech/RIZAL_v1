import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_paths.dart';
import '../../../core/network/dio_client.dart';
import '../../../shared/models/analytics.dart';

class ReportsRepository {
  ReportsRepository(this._client);
  final DioClient _client;

  Future<StudentReport> studentReport(int studentProfileId) async {
    final res = await _client.get(Api.studentReport(studentProfileId));
    return StudentReport.fromJson((res.data as Map).cast<String, dynamic>());
  }
}

final reportsRepositoryProvider = Provider<ReportsRepository>(
  (ref) => ReportsRepository(ref.watch(dioClientProvider)),
);
