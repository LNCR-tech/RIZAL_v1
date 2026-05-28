import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// One geocoded place returned by [GeocodingService.search].
///
/// [displayName] is Nominatim's full comma-separated string
/// (e.g. "Manila City Hall, Padre Burgos Avenue, Manila, Philippines").
/// [primaryName] and [secondaryLine] split it into the venue name and the
/// postal trail so the UI can render them on two lines without parsing.
class GeocodeResult {
  const GeocodeResult({
    required this.displayName,
    required this.latitude,
    required this.longitude,
    this.type,
    this.category,
  });

  final String displayName;
  final double latitude;
  final double longitude;

  /// Nominatim's `type` (e.g. "library", "university", "city"). Optional.
  final String? type;

  /// Nominatim's `class` (e.g. "amenity", "building"). Optional.
  final String? category;

  /// First comma-separated segment of [displayName] — usually the venue.
  String get primaryName {
    final i = displayName.indexOf(',');
    return i < 0 ? displayName : displayName.substring(0, i).trim();
  }

  /// Everything after [primaryName] — the postal trail. `null` if there is
  /// no comma in [displayName].
  String? get secondaryLine {
    final i = displayName.indexOf(',');
    if (i < 0 || i + 1 >= displayName.length) return null;
    final rest = displayName.substring(i + 1).trim();
    return rest.isEmpty ? null : rest;
  }
}

/// Thin client over the public OSM Nominatim endpoint
/// (https://nominatim.openstreetmap.org).
///
/// **Usage policy** — Nominatim requires every consumer to identify itself
/// via `User-Agent` and to stay under 1 request / second. The UI debounces
/// typing by 450 ms, which keeps a single typing user safely under that
/// limit. If this ever needs to support burst usage, swap to a self-hosted
/// Nominatim or a commercial geocoder.
///
/// **Error handling** — every failure (network, timeout, malformed payload)
/// collapses to an empty list. Callers render the "no matches" state
/// instead of catching exceptions.
class GeocodingService {
  GeocodingService({Dio? dio})
      : _dio = dio ??
            Dio(BaseOptions(
              baseUrl: 'https://nominatim.openstreetmap.org',
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 10),
              headers: const {
                'User-Agent': 'Aura (RIZAL)/1.36 com.aura.aura_app',
                'Accept': 'application/json',
              },
            ));

  final Dio _dio;

  /// Free-text search. Returns at most [limit] results (default 5).
  /// Empty / whitespace-only [query] returns an empty list immediately
  /// without hitting the network.
  Future<List<GeocodeResult>> search(String query, {int limit = 5}) async {
    final q = query.trim();
    if (q.isEmpty) return const [];
    try {
      final r = await _dio.get<dynamic>('/search', queryParameters: {
        'q': q,
        'format': 'json',
        'limit': limit,
        'addressdetails': 0,
      });
      final data = r.data;
      if (data is! List) return const [];
      final out = <GeocodeResult>[];
      for (final raw in data) {
        if (raw is Map) {
          final parsed = parseResult(raw.cast<String, dynamic>());
          if (parsed != null) out.add(parsed);
        }
      }
      return out;
    } catch (_) {
      return const [];
    }
  }

  /// Pure parser, exposed static so unit tests can lock in the contract
  /// without spinning up a Dio. Returns `null` when required fields are
  /// missing or malformed.
  static GeocodeResult? parseResult(Map<String, dynamic> raw) {
    final lat = double.tryParse('${raw['lat']}');
    final lng = double.tryParse('${raw['lon']}');
    final name = raw['display_name'];
    if (lat == null || lng == null || name is! String || name.isEmpty) {
      return null;
    }
    return GeocodeResult(
      displayName: name,
      latitude: lat,
      longitude: lng,
      type: raw['type']?.toString(),
      category: raw['class']?.toString(),
    );
  }
}

final geocodingServiceProvider = Provider<GeocodingService>(
  (ref) => GeocodingService(),
);
