import 'package:flutter/widgets.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:native_geofence/native_geofence.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../shared/models/event.dart';
import 'auto_checkin_controller.dart';
import 'events_providers.dart';

const _channelId = 'nearby_checkin';
const _channelName = 'Event check-in';
const _payloadPrefix = 'checkin:';
const _namePrefix = 'geofence_event_name_';

NotificationDetails _details() => const NotificationDetails(
      android: AndroidNotificationDetails(
        _channelId,
        _channelName,
        channelDescription: 'Alerts you when you arrive at an event so you can '
            'check in.',
        importance: Importance.high,
        priority: Priority.high,
      ),
      iOS: DarwinNotificationDetails(),
    );

const _initSettings = InitializationSettings(
  android: AndroidInitializationSettings('@mipmap/ic_launcher'),
  iOS: DarwinInitializationSettings(),
);

/// OS geofence ENTER handler. Runs in a **background isolate** (even if the app
/// is closed), so it can only do isolate-safe work: show a local notification.
/// Tapping it is routed to the check-in screen by [GeofenceBackground] in the
/// main isolate.
@pragma('vm:entry-point')
Future<void> nearbyGeofenceCallback(GeofenceCallbackParams params) async {
  if (params.event != GeofenceEvent.enter) return;
  WidgetsFlutterBinding.ensureInitialized();
  final notifications = FlutterLocalNotificationsPlugin();
  await notifications.initialize(settings: _initSettings);
  final prefs = await SharedPreferences.getInstance();
  for (final g in params.geofences) {
    final id = int.tryParse(g.id.replaceFirst('event_', ''));
    if (id == null) continue;
    final name = prefs.getString('$_namePrefix${g.id}') ?? 'an event';
    await notifications.show(
      id: id,
      title: "You're at $name",
      body: 'Attendance is open — tap to check in',
      notificationDetails: _details(),
      payload: '$_payloadPrefix$id',
    );
  }
}

/// Main-isolate side of the background geofence feature: initializes
/// notifications + tap routing, and keeps OS geofences in sync with the user's
/// ongoing geofenced events.
class GeofenceBackground {
  GeofenceBackground._();

  static final _notifications = FlutterLocalNotificationsPlugin();
  static bool _notifReady = false;

  /// Called (main isolate) when a check-in notification is tapped.
  static void Function(int eventId)? onCheckIn;

  static Future<void> initNotifications() async {
    if (_notifReady) return;
    _notifReady = true;
    await _notifications.initialize(
      settings: _initSettings,
      onDidReceiveNotificationResponse: (r) => _dispatch(r.payload),
    );
    await _notifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.requestNotificationsPermission();
    // Cold start: app launched by tapping a notification.
    final launch = await _notifications.getNotificationAppLaunchDetails();
    if (launch?.didNotificationLaunchApp ?? false) {
      _dispatch(launch!.notificationResponse?.payload);
    }
  }

  static void _dispatch(String? payload) {
    if (payload == null || !payload.startsWith(_payloadPrefix)) return;
    final id = int.tryParse(payload.substring(_payloadPrefix.length));
    if (id != null) onCheckIn?.call(id);
  }

  /// Register one OS geofence per ongoing geofenced event (replacing any prior).
  static Future<void> sync(List<AppEvent> geoEvents) async {
    try {
      await NativeGeofenceManager.instance.initialize();
      await NativeGeofenceManager.instance.removeAllGeofences();
      final prefs = await SharedPreferences.getInstance();
      for (final e in geoEvents) {
        if (!e.hasGeo || (e.geoRadiusM ?? 0) <= 0) continue;
        final gid = 'event_${e.id}';
        await prefs.setString('$_namePrefix$gid', e.name);
        await NativeGeofenceManager.instance.createGeofence(
          Geofence(
            id: gid,
            location: Location(
                latitude: e.geoLatitude!, longitude: e.geoLongitude!),
            radiusMeters: e.geoRadiusM!,
            triggers: const {GeofenceEvent.enter},
            iosSettings: const IosGeofenceSettings(initialTrigger: true),
            androidSettings: const AndroidGeofenceSettings(
                initialTriggers: {GeofenceEvent.enter}),
          ),
          nearbyGeofenceCallback,
        );
      }
    } catch (_) {/* geofencing unavailable / permission denied */}
  }

  static Future<void> stop() async {
    try {
      await NativeGeofenceManager.instance.removeAllGeofences();
    } catch (_) {}
  }
}

/// Event id pending a check-in (set by a notification tap; consumed by a
/// listener that opens the attendance screen).
final pendingCheckInProvider = StateProvider<int?>((ref) => null);

/// Wires the background geofence feature to the "Nearby event check-in" toggle.
/// Watch this somewhere persistent (the app root) so it lives for the session.
final geofenceBackgroundProvider = Provider<void>((ref) {
  GeofenceBackground.onCheckIn =
      (id) => ref.read(pendingCheckInProvider.notifier).state = id;
  GeofenceBackground.initNotifications();

  if (!ref.watch(autoCheckInProvider)) {
    GeofenceBackground.stop();
    return;
  }
  ref.listen<AsyncValue<List<AppEvent>>>(
    ongoingEventsProvider,
    (_, next) => next.whenData((events) => GeofenceBackground.sync(
        events.where((e) => e.hasGeo && (e.geoRadiusM ?? 0) > 0).toList())),
    fireImmediately: true,
  );
});
