import 'dart:convert';

import '../../../core/services/geolocation_service.dart';
import '../../../shared/models/event.dart';

class AttendanceScanFlowError implements Exception {
  const AttendanceScanFlowError(this.message);

  final String message;

  @override
  String toString() => message;
}

class AttendanceScanRequest {
  const AttendanceScanRequest({
    required this.eventId,
    required this.imageBase64,
    this.latitude,
    this.longitude,
    this.accuracyM,
  });

  final int eventId;
  final String imageBase64;
  final double? latitude;
  final double? longitude;
  final double? accuracyM;
}

void validateAttendanceScanLocation({
  required AppEvent event,
  required GeoFix? geo,
}) {
  if (event.geoRequired && geo == null) {
    throw const AttendanceScanFlowError(
        'Location is required for this event. Enable location access and try again.');
  }
}

AttendanceScanRequest buildAttendanceScanRequest({
  required AppEvent event,
  required List<int> imageBytes,
  required GeoFix? geo,
}) {
  validateAttendanceScanLocation(event: event, geo: geo);

  return AttendanceScanRequest(
    eventId: event.id,
    imageBase64: base64Encode(imageBytes),
    latitude: geo?.latitude,
    longitude: geo?.longitude,
    accuracyM: geo?.accuracy,
  );
}
