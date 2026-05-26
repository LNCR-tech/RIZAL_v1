import 'package:aura_app/shared/utils/location_display.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('location display helpers', () {
    test('formats valid coordinates and reports invalid coordinates clearly', () {
      expect(
        formatCoordinateLocationLabel(
            latitude: 8.155234, longitude: 123.842145),
        '8.1552, 123.8421',
      );
      expect(
        formatCoordinateLocationLabel(latitude: 'bad', longitude: 123.842145),
        'Current location unavailable',
      );
    });

    test('measures and formats venue distance labels', () {
      final distance = measureDistanceMeters(
        const CoordinatePoint(latitude: 8.1552, longitude: 123.8421),
        const CoordinatePoint(latitude: 8.1552, longitude: 123.8511),
      );

      expect(distance, greaterThan(900));
      expect(formatVenueDistance(36.4), '36 m to venue');
      expect(formatVenueDistance(1530), '1.5 km to venue');
      expect(formatVenueDistance(-1), '');
    });
  });
}
