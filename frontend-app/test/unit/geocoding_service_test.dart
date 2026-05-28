import 'package:aura_app/core/services/geocoding_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('GeocodingService.parseResult', () {
    test('parses a typical Nominatim hit', () {
      final r = GeocodingService.parseResult({
        'lat': '14.5995',
        'lon': '120.9842',
        'display_name': 'Manila City Hall, Padre Burgos Avenue, Manila',
        'type': 'townhall',
        'class': 'amenity',
      });
      expect(r, isNotNull);
      expect(r!.latitude, 14.5995);
      expect(r.longitude, 120.9842);
      expect(r.displayName, 'Manila City Hall, Padre Burgos Avenue, Manila');
      expect(r.type, 'townhall');
      expect(r.category, 'amenity');
      expect(r.primaryName, 'Manila City Hall');
      expect(r.secondaryLine, 'Padre Burgos Avenue, Manila');
    });

    test('numeric lat/lon (not strings) also parse', () {
      final r = GeocodingService.parseResult({
        'lat': 8.6543,
        'lon': 123.4254,
        'display_name': 'Dapitan, Zamboanga del Norte, Philippines',
      });
      expect(r, isNotNull);
      expect(r!.latitude, 8.6543);
      expect(r.longitude, 123.4254);
      expect(r.primaryName, 'Dapitan');
      expect(r.secondaryLine, 'Zamboanga del Norte, Philippines');
    });

    test('returns null when lat is missing', () {
      expect(
        GeocodingService.parseResult({
          'lon': '120.0',
          'display_name': 'X',
        }),
        isNull,
      );
    });

    test('returns null when lat is malformed', () {
      expect(
        GeocodingService.parseResult({
          'lat': 'not-a-number',
          'lon': '120.0',
          'display_name': 'X',
        }),
        isNull,
      );
    });

    test('returns null when display_name is missing or empty', () {
      expect(
        GeocodingService.parseResult({'lat': '1', 'lon': '2'}),
        isNull,
      );
      expect(
        GeocodingService.parseResult(
            {'lat': '1', 'lon': '2', 'display_name': ''}),
        isNull,
      );
    });

    test('primaryName falls back to full string when no comma', () {
      final r = GeocodingService.parseResult({
        'lat': '0',
        'lon': '0',
        'display_name': 'SinglePlaceName',
      });
      expect(r, isNotNull);
      expect(r!.primaryName, 'SinglePlaceName');
      expect(r.secondaryLine, isNull);
    });

    test('secondaryLine is null when nothing follows the comma', () {
      final r = GeocodingService.parseResult({
        'lat': '0',
        'lon': '0',
        'display_name': 'Place,',
      });
      expect(r!.primaryName, 'Place');
      expect(r.secondaryLine, isNull);
    });
  });

  group('GeocodingService.search', () {
    test('empty / whitespace-only query returns empty list without I/O',
        () async {
      final svc = GeocodingService();
      expect(await svc.search(''), isEmpty);
      expect(await svc.search('   '), isEmpty);
    });
  });
}
