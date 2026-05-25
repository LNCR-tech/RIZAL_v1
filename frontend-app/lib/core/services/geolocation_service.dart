import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';

class GeoFix {
  const GeoFix(this.latitude, this.longitude, this.accuracy);
  final double latitude;
  final double longitude;
  final double? accuracy;
}

abstract class GeolocationPlatform {
  Future<bool> isLocationServiceEnabled();
  Future<LocationPermission> checkPermission();
  Future<LocationPermission> requestPermission();
  Future<GeoFix> getCurrentPosition();
}

class GeolocatorPlatformAdapter implements GeolocationPlatform {
  const GeolocatorPlatformAdapter();

  @override
  Future<bool> isLocationServiceEnabled() =>
      Geolocator.isLocationServiceEnabled();

  @override
  Future<LocationPermission> checkPermission() => Geolocator.checkPermission();

  @override
  Future<LocationPermission> requestPermission() =>
      Geolocator.requestPermission();

  @override
  Future<GeoFix> getCurrentPosition() async {
    final pos = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
    );
    return GeoFix(pos.latitude, pos.longitude, pos.accuracy);
  }
}

/// Thin wrapper over geolocator with permission handling. Returns null when
/// location is unavailable or denied (callers decide if it's required).
class GeolocationService {
  const GeolocationService([this._platform = const GeolocatorPlatformAdapter()]);

  final GeolocationPlatform _platform;

  Future<GeoFix?> current() async {
    if (!await _platform.isLocationServiceEnabled()) return null;

    var permission = await _platform.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await _platform.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      return null;
    }

    return _platform.getCurrentPosition();
  }
}

final geolocationServiceProvider =
    Provider<GeolocationService>((ref) => GeolocationService());
