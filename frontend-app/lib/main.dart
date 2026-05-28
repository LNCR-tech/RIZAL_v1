import 'package:device_preview/device_preview.dart';
import 'package:flutter/foundation.dart' show kReleaseMode;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import 'app/app.dart';
import 'core/config/app_config.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  // Initialize the IANA timezone database for flutter_local_notifications
  // .zonedSchedule. Asia/Manila is the canonical event timezone used by the
  // backend (backend/app/services/event_time_status.py:DEFAULT_EVENT_TIMEZONE).
  tzdata.initializeTimeZones();
  tz.setLocalLocation(tz.getLocation('Asia/Manila'));

  runApp(
    ProviderScope(
      // DevicePreview shows the app inside a selectable phone frame on
      // web/desktop (debug/profile only). On a real device it's a no-op.
      child: DevicePreview(
        enabled: !kReleaseMode && AppConfig.devicePreviewEnabled,
        builder: (context) => const AuraApp(),
      ),
    ),
  );
}
