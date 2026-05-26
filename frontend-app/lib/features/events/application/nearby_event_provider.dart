import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';

import '../../../core/services/geolocation_service.dart';
import '../../../shared/models/event.dart';
import 'auto_checkin_controller.dart';
import 'events_providers.dart';

/// While "nearby event check-in" is enabled, polls the device location against
/// ongoing **geofenced** events and exposes the event the user is physically
/// inside (within its radius), or null. Foreground only. Drives the in-app
/// check-in prompt ([NearbyEventBanner]).
///
/// Privacy: location is only read when the toggle is on AND there is at least
/// one ongoing geofenced event to match against.
class NearbyEventController extends AutoDisposeNotifier<AppEvent?> {
  Timer? _timer;
  bool _checking = false;

  static const _pollInterval = Duration(seconds: 45);

  @override
  AppEvent? build() {
    _timer?.cancel();
    ref.onDispose(() => _timer?.cancel());

    final enabled = ref.watch(autoCheckInProvider);
    if (!enabled) return null;

    Future.microtask(_check);
    _timer = Timer.periodic(_pollInterval, (_) => _check());
    return null;
  }

  /// Re-run detection immediately (e.g. after a manual refresh).
  Future<void> refreshNow() => _check();

  Future<void> _check() async {
    if (_checking) return;
    _checking = true;
    try {
      final List<AppEvent> events;
      try {
        events = await ref.read(ongoingEventsProvider.future);
      } catch (_) {
        return; // can't load events right now — keep the last state
      }

      final geofenced = events
          .where((e) => e.hasGeo && (e.geoRadiusM ?? 0) > 0)
          .toList(growable: false);
      if (geofenced.isEmpty) {
        state = null;
        return; // nothing to match — don't even read location
      }

      final fix = await ref.read(geolocationServiceProvider).current();
      if (fix == null) {
        state = null; // location unavailable / denied
        return;
      }

      const distance = Distance();
      final here = LatLng(fix.latitude, fix.longitude);
      AppEvent? closestInside;
      var closestMeters = double.infinity;
      for (final e in geofenced) {
        final meters = distance.as(
          LengthUnit.Meter,
          here,
          LatLng(e.geoLatitude!, e.geoLongitude!),
        );
        if (meters <= e.geoRadiusM! && meters < closestMeters) {
          closestMeters = meters;
          closestInside = e;
        }
      }
      state = closestInside;
    } finally {
      _checking = false;
    }
  }
}

final nearbyEventProvider =
    AutoDisposeNotifierProvider<NearbyEventController, AppEvent?>(
        NearbyEventController.new);
