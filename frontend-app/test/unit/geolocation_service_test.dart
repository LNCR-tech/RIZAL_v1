import 'package:aura_app/core/services/geolocation_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geolocator/geolocator.dart';

class FakeGeolocationPlatform implements GeolocationPlatform {
  FakeGeolocationPlatform({
    this.serviceEnabled = true,
    this.permission = LocationPermission.always,
    this.requestedPermission = LocationPermission.always,
    this.fix = const GeoFix(8.1552, 123.8421, 21),
  });

  bool serviceEnabled;
  LocationPermission permission;
  LocationPermission requestedPermission;
  GeoFix fix;
  int checkPermissionCalls = 0;
  int requestPermissionCalls = 0;
  int currentPositionCalls = 0;

  @override
  Future<bool> isLocationServiceEnabled() async => serviceEnabled;

  @override
  Future<LocationPermission> checkPermission() async {
    checkPermissionCalls += 1;
    return permission;
  }

  @override
  Future<LocationPermission> requestPermission() async {
    requestPermissionCalls += 1;
    permission = requestedPermission;
    return permission;
  }

  @override
  Future<GeoFix> getCurrentPosition() async {
    currentPositionCalls += 1;
    return fix;
  }
}

void main() {
  group('GeolocationService.current', () {
    test('returns null when location services are disabled', () async {
      final platform = FakeGeolocationPlatform(serviceEnabled: false);
      final service = GeolocationService(platform);

      expect(await service.current(), isNull);
      expect(platform.checkPermissionCalls, 0);
      expect(platform.currentPositionCalls, 0);
    });

    test('requests permission when initially denied and returns a fix', () async {
      final platform = FakeGeolocationPlatform(
        permission: LocationPermission.denied,
        requestedPermission: LocationPermission.whileInUse,
      );
      final service = GeolocationService(platform);

      final fix = await service.current();

      expect(fix?.latitude, 8.1552);
      expect(platform.requestPermissionCalls, 1);
      expect(platform.currentPositionCalls, 1);
    });

    test('returns null when permission remains denied', () async {
      final platform = FakeGeolocationPlatform(
        permission: LocationPermission.denied,
        requestedPermission: LocationPermission.denied,
      );
      final service = GeolocationService(platform);

      expect(await service.current(), isNull);
      expect(platform.requestPermissionCalls, 1);
      expect(platform.currentPositionCalls, 0);
    });

    test('uses existing permission without prompting', () async {
      final platform =
          FakeGeolocationPlatform(permission: LocationPermission.always);
      final service = GeolocationService(platform);

      expect(await service.current(), isA<GeoFix>());
      expect(platform.requestPermissionCalls, 0);
      expect(platform.currentPositionCalls, 1);
    });
  });
}
