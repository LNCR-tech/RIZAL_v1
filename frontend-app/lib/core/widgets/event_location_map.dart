import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../theme/app_spacing.dart';
import '../theme/app_tokens.dart';

/// Read-only map showing an event's geofence: the centre pin + the radius range
/// circle. Static (no gestures) so it sits cleanly inside a scrolling view.
class EventLocationMap extends StatelessWidget {
  const EventLocationMap({
    super.key,
    required this.lat,
    required this.lng,
    required this.radiusM,
    this.label,
    this.height = 180,
  });

  final double lat;
  final double lng;
  final double radiusM;
  final String? label;
  final double height;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final center = LatLng(lat, lng);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(AppRadii.control),
          child: SizedBox(
            height: height,
            child: FlutterMap(
              options: MapOptions(
                initialCenter: center,
                initialZoom: 16,
                interactionOptions:
                    const InteractionOptions(flags: InteractiveFlag.none),
              ),
              children: [
                TileLayer(
                  urlTemplate:
                      'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.aura.aura_app',
                ),
                CircleLayer(
                  circles: [
                    CircleMarker(
                      point: center,
                      radius: radiusM,
                      useRadiusInMeter: true,
                      color: t.accent.withOpacity(0.18),
                      borderColor: t.accentDark,
                      borderStrokeWidth: 2,
                    ),
                  ],
                ),
                MarkerLayer(
                  markers: [
                    Marker(
                      point: center,
                      width: 40,
                      height: 40,
                      child: Icon(Icons.location_on,
                          color: t.accentDark, size: 36),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 6),
        Row(
          children: [
            Icon(Icons.my_location_rounded, size: 14, color: t.textMuted),
            const SizedBox(width: 6),
            Text(label ?? 'Check in within ${radiusM.round()} m of this point',
                style: textTheme.bodySmall?.copyWith(color: t.textMuted)),
          ],
        ),
      ],
    );
  }
}
