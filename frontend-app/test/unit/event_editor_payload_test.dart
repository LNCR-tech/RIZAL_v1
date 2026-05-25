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
      );

      expect(payload, {
        'name': 'Assembly',
        'location': 'Main Hall',
        'description': 'Welcome program',
        'start_datetime': start.toIso8601String(),
        'end_datetime': end.toIso8601String(),
        'geo_required': true,
        'geo_latitude': 8.1552,
        'geo_longitude': 123.8421,
        'geo_radius_m': 150,
      });
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
