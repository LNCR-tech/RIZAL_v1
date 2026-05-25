import 'dart:math' as math;

class CoordinatePoint {
  const CoordinatePoint({required this.latitude, required this.longitude});

  final double latitude;
  final double longitude;
}

double? _asFiniteDouble(Object? value) {
  final parsed = value is num ? value.toDouble() : double.tryParse('$value');
  return parsed != null && parsed.isFinite ? parsed : null;
}

String formatCoordinateLocationLabel({
  required Object? latitude,
  required Object? longitude,
}) {
  final lat = _asFiniteDouble(latitude);
  final lng = _asFiniteDouble(longitude);
  if (lat == null || lng == null) return 'Current location unavailable';
  return '${lat.toStringAsFixed(4)}, ${lng.toStringAsFixed(4)}';
}

double measureDistanceMeters(CoordinatePoint from, CoordinatePoint to) {
  const earthRadiusMeters = 6371008.8;
  final lat1 = _toRadians(from.latitude);
  final lat2 = _toRadians(to.latitude);
  final deltaLat = _toRadians(to.latitude - from.latitude);
  final deltaLng = _toRadians(to.longitude - from.longitude);
  final a = math.sin(deltaLat / 2) * math.sin(deltaLat / 2) +
      math.cos(lat1) *
          math.cos(lat2) *
          math.sin(deltaLng / 2) *
          math.sin(deltaLng / 2);
  final c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
  return earthRadiusMeters * c;
}

String formatVenueDistance(Object? meters) {
  final distance = _asFiniteDouble(meters);
  if (distance == null || distance < 0) return '';
  if (distance < 1000) return '${distance.round()} m to venue';
  return '${(distance / 1000).toStringAsFixed(1)} km to venue';
}

double _toRadians(double degrees) => degrees * math.pi / 180;
