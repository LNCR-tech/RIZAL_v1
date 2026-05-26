import 'dart:convert';

import 'package:aura_app/core/services/geolocation_service.dart';
import 'package:aura_app/features/attendance/application/attendance_scan_flow.dart';
import 'package:aura_app/shared/models/event.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('buildAttendanceScanRequest', () {
    test('builds a face scan request with encoded image and geolocation', () {
      const event = AppEvent(id: 42, name: 'Assembly', geoRequired: true);
      const geo = GeoFix(8.1552, 123.8421, 18);

      final request = buildAttendanceScanRequest(
        event: event,
        imageBytes: [1, 2, 3, 4],
        geo: geo,
      );

      expect(request.eventId, 42);
      expect(request.imageBase64, base64Encode([1, 2, 3, 4]));
      expect(request.latitude, 8.1552);
      expect(request.longitude, 123.8421);
      expect(request.accuracyM, 18);
    });

    test('allows missing location when event does not require geofence', () {
      const event = AppEvent(id: 42, name: 'Assembly');

      final request = buildAttendanceScanRequest(
        event: event,
        imageBytes: [5, 6, 7],
        geo: null,
      );

      expect(request.imageBase64, base64Encode([5, 6, 7]));
      expect(request.latitude, isNull);
      expect(request.longitude, isNull);
      expect(request.accuracyM, isNull);
    });

    test('rejects missing location when event requires geofence', () {
      const event = AppEvent(id: 42, name: 'Assembly', geoRequired: true);

      expect(
        () => buildAttendanceScanRequest(
          event: event,
          imageBytes: [1, 2, 3],
          geo: null,
        ),
        throwsA(isA<AttendanceScanFlowError>()),
      );
    });
  });
}
