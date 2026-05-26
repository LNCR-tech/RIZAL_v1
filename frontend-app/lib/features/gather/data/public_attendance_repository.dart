import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_paths.dart';
import '../../../core/network/dio_client.dart';
import '../../../shared/models/public_attendance.dart';
import '../../../shared/utils/json.dart';

class NearbyResult {
  const NearbyResult(this.events, this.cooldownSeconds);
  final List<NearbyEvent> events;
  final int cooldownSeconds;
}

/// Public (kiosk) attendance: nearby discovery + multi-face scan.
class PublicAttendanceRepository {
  PublicAttendanceRepository(this._client);
  final DioClient _client;

  Future<NearbyResult> nearby({
    required double latitude,
    required double longitude,
    double? accuracyM,
  }) async {
    final res = await _client.post(Api.publicNearby, data: {
      'latitude': latitude,
      'longitude': longitude,
      'accuracy_m': accuracyM,
    });
    final data = (res.data as Map).cast<String, dynamic>();
    final events =
        asMapList(data['events']).map(NearbyEvent.fromJson).toList();
    return NearbyResult(events, asInt(data['scan_cooldown_seconds']) ?? 5);
  }

  Future<MultiScanResult> multiScan({
    required int eventId,
    required String imageBase64,
    required double latitude,
    required double longitude,
    double? accuracyM,
    List<String> cooldownStudentIds = const [],
  }) async {
    final res = await _client.post(Api.publicMultiScan(eventId), data: {
      'image_base64': imageBase64,
      'latitude': latitude,
      'longitude': longitude,
      'accuracy_m': accuracyM,
      'cooldown_student_ids': cooldownStudentIds,
    });
    return MultiScanResult.fromJson((res.data as Map).cast<String, dynamic>());
  }
}

final publicAttendanceRepositoryProvider = Provider<PublicAttendanceRepository>(
  (ref) => PublicAttendanceRepository(ref.watch(dioClientProvider)),
);
