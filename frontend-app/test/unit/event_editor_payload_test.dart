import 'package:aura_app/features/events/application/event_editor_payload.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('buildEventEditorPayload', () {
    test('builds a trimmed create payload with geofence fields', () {
      final start = DateTime.utc(2099, 1, 1, 9);
      final end = DateTime.utc(2099, 1, 1, 11);

      final payload = buildEventEditorPayload(
        name: '  Assembly  ',
        location: '  Main Hall  ',
        description: '  Welcome program  ',
        start: start,
        end: end,
        geoRequired: true,
        geoLatitude: 8.1552,
        geoLongitude: 123.8421,
        geoRadiusM: 149.6,
        isEdit: false,
        yearLevels: const [3, 1, 1],
        earlyCheckInMinutes: 30,
        lateThresholdMinutes: 10,
        signOutGraceMinutes: 15,
      );

      expect(payload, {
        'name': 'Assembly',
        'location': 'Main Hall',
        'description': 'Welcome program',
        'start_datetime': start.toIso8601String(),
        'end_datetime': end.toIso8601String(),
        'year_levels': [1, 3],
        'early_check_in_minutes': 30,
        'late_threshold_minutes': 10,
        'sign_out_grace_minutes': 15,
        'geo_required': true,
        'geo_latitude': 8.1552,
        'geo_longitude': 123.8421,
        'geo_radius_m': 150,
      });
    });

    test('always sends year_levels (empty list = open to all)', () {
      final start = DateTime.utc(2099, 1, 1, 9);
      final end = DateTime.utc(2099, 1, 1, 11);

      final payload = buildEventEditorPayload(
        name: 'Assembly',
        location: 'Main Hall',
        start: start,
        end: end,
        geoRequired: false,
        isEdit: false,
      );

      expect(payload['year_levels'], const <int>[]);
    });

    test('rejects out-of-range year levels and minute fields', () {
      final start = DateTime.utc(2099, 1, 1, 9);
      final end = DateTime.utc(2099, 1, 1, 11);

      expect(
        () => buildEventEditorPayload(
          name: 'A',
          location: 'B',
          start: start,
          end: end,
          geoRequired: false,
          isEdit: false,
          yearLevels: const [6],
        ),
        throwsA(isA<EventEditorPayloadError>()),
      );

      expect(
        () => buildEventEditorPayload(
          name: 'A',
          location: 'B',
          start: start,
          end: end,
          geoRequired: false,
          isEdit: false,
          earlyCheckInMinutes: -1,
        ),
        throwsA(isA<EventEditorPayloadError>()),
      );

      expect(
        () => buildEventEditorPayload(
          name: 'A',
          location: 'B',
          start: start,
          end: end,
          geoRequired: false,
          isEdit: false,
          lateThresholdMinutes: 2000,
        ),
        throwsA(isA<EventEditorPayloadError>()),
      );
    });

    test('omits empty descriptions and disables geofence on edit', () {
      final start = DateTime.utc(2099, 1, 1, 9);
      final end = DateTime.utc(2099, 1, 1, 11);

      final payload = buildEventEditorPayload(
        name: 'Assembly',
        location: 'Main Hall',
        description: '   ',
        start: start,
        end: end,
        geoRequired: false,
        isEdit: true,
      );

      expect(payload.containsKey('description'), isFalse);
      expect(payload['geo_required'], isFalse);
    });

    test('rejects missing required fields', () {
      expect(
        () => buildEventEditorPayload(
          name: '',
          location: 'Main Hall',
          start: DateTime.utc(2099, 1, 1, 9),
          end: DateTime.utc(2099, 1, 1, 11),
          geoRequired: false,
          isEdit: false,
        ),
        throwsA(isA<EventEditorPayloadError>()),
      );

      expect(
        () => buildEventEditorPayload(
          name: 'Assembly',
          location: '',
          start: DateTime.utc(2099, 1, 1, 9),
          end: DateTime.utc(2099, 1, 1, 11),
          geoRequired: false,
          isEdit: false,
        ),
        throwsA(isA<EventEditorPayloadError>()),
      );
    });

    test('rejects invalid times and missing geofence coordinates', () {
      expect(
        () => buildEventEditorPayload(
          name: 'Assembly',
          location: 'Main Hall',
          start: DateTime.utc(2099, 1, 1, 11),
          end: DateTime.utc(2099, 1, 1, 9),
          geoRequired: false,
          isEdit: false,
        ),
        throwsA(isA<EventEditorPayloadError>()),
      );

      expect(
        () => buildEventEditorPayload(
          name: 'Assembly',
          location: 'Main Hall',
          start: DateTime.utc(2099, 1, 1, 9),
          end: DateTime.utc(2099, 1, 1, 11),
          geoRequired: true,
          geoLatitude: 8.1552,
          isEdit: false,
        ),
        throwsA(isA<EventEditorPayloadError>()),
      );
    });
  });
}
