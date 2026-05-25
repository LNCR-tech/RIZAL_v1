import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';

class GeoFix {
  const GeoFix(this.latitude, this.longitude, this.accuracy);
  final double latitude;
  final double longitude;
  final double? accuracy;
}

/// Thin wrapper over geolocator with permission handling. Returns null when
/// location is unavailable or denied (callers decide if it's required).
class GeolocationService {
  Future<GeoFix?> current() async {
    if (!await Geolocator.isLocationServiceEnabled()) return null;

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      return null;
    }

    final pos = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
    );
    return GeoFix(pos.latitude, pos.longitude, pos.accuracy);
  }
}

final geolocationServiceProvider =
    Provider<GeolocationService>((ref) => GeolocationService());
