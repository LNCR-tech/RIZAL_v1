import 'package:device_preview/device_preview.dart';
import 'package:flutter/foundation.dart' show kReleaseMode;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/app.dart';
import 'core/config/app_config.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
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
