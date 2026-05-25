import 'package:device_preview/device_preview.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/theme/app_theme.dart';
import '../core/theme/motion_controller.dart';
import '../core/theme/theme_controller.dart';
import '../features/events/application/geofence_background.dart';
import 'router.dart';

/// Root widget: wires theme (light/dark + school branding), motion preference,
/// and the router.
class AuraApp extends ConsumerWidget {
  const AuraApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    final theme = ref.watch(themeControllerProvider);
    final motionPref = ref.watch(motionControllerProvider);
    final osReduce = MediaQueryData.fromView(View.of(context)).disableAnimations;
    final reduceMotion = MotionController.resolve(motionPref, osReduce);
    // Keep the background geofence check-in alive for the session (notification
    // init + tap routing + geofence sync) — gated by the Nearby check-in toggle.
    ref.watch(geofenceBackgroundProvider);

    return MaterialApp.router(
      title: 'Aura',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(
          brandPrimary: theme.brandPrimary, reduceMotion: reduceMotion),
      darkTheme: AppTheme.dark(
          brandPrimary: theme.brandPrimary, reduceMotion: reduceMotion),
      themeMode: theme.mode,
      // Instant theme switch — the animated cross-fade rebuilds the glass nav
      // (BackdropFilter) every frame and janks on low-end GPUs.
      themeAnimationDuration: Duration.zero,
      locale: DevicePreview.locale(context),
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [Locale('en'), Locale('fil')],
      // Compose device_preview's builder with a MediaQuery override so the
      // user's "reduce motion" choice flows to every disableAnimations check.
      builder: (context, child) => DevicePreview.appBuilder(
        context,
        Builder(
          builder: (ctx) {
            final mq = MediaQuery.of(ctx);
            return MediaQuery(
              data: mq.copyWith(disableAnimations: reduceMotion),
              child: child ?? const SizedBox.shrink(),
            );
          },
        ),
      ),
      routerConfig: router,
    );
  }
}
