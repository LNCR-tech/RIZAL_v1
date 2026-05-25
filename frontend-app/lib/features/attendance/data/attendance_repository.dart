import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_paths.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/network/paginated.dart';
import '../../../shared/models/attendance.dart';
import '../../../shared/utils/json.dart';

class AttendanceRepository {
  AttendanceRepository(this._client);
  final DioClient _client;

  /// Self check-in/out via face scan. Sends the captured frame as base64
  /// plus geolocation; the backend (InsightFace) does matching + liveness.
  Future<FaceScanResult> faceScan({
    required int eventId,
    required String imageBase64,
    double? latitude,
    double? longitude,
    double? accuracyM,
    double? threshold,
  }) async {
    final res = await _client.post(Api.faceScan, data: {
      'event_id': eventId,
      'image_base64': imageBase64,
      'latitude': latitude,
      'longitude': longitude,
      'accuracy_m': accuracyM,
      'threshold': threshold,
    });
    return FaceScanResult.fromJson((res.data as Map).cast<String, dynamic>());
  }

  Future<List<AttendanceRecord>> myRecords({
    int? eventId,
    int skip = 0,
    int limit = 100,
  }) async {
    final res = await _client.get(Api.myAttendance, query: {
      'event_id': eventId,
      'skip': skip,
      'limit': limit,
    });
    return Paginated.from(
      res.data,
      (e) => AttendanceRecord.fromJson((e as Map).cast<String, dynamic>()),
    ).data;
  }

  /// Enroll the signed-in student's face reference.
  Future<String> registerFace(String imageBase64) async {
    final res =
        await _client.post(Api.faceRegister, data: {'image_base64': imageBase64});
    final data = res.data;
    return (data is Map ? asStr(data['message']) : null) ?? 'Face registered.';
  }
}

final attendanceRepositoryProvider = Provider<AttendanceRepository>(
  (ref) => AttendanceRepository(ref.watch(dioClientProvider)),
);
