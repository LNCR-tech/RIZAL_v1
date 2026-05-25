import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/services/geolocation_service.dart';
import '../data/public_attendance_repository.dart';

/// Discovers events near the device (requires location).
final gatherNearbyProvider =
    FutureProvider.autoDispose<NearbyResult>((ref) async {
  final fix = await ref.read(geolocationServiceProvider).current();
  if (fix == null) {
    throw ApiException(
        'Location is required to find nearby events. Enable location access and try again.');
  }
  return ref.read(publicAttendanceRepositoryProvider).nearby(
        latitude: fix.latitude,
        longitude: fix.longitude,
        accuracyM: fix.accuracy,
      );
});
