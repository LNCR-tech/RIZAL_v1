import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Opens ~1.7s after launch. The router keeps `/splash` until both the session
/// has resolved AND this gate is open, so the splash bloom always plays even
/// when session restore is instant.
class SplashGate extends Notifier<bool> {
  @override
  bool build() {
    final timer =
        Timer(const Duration(milliseconds: 1700), () => state = true);
    ref.onDispose(timer.cancel);
    return false;
  }
}

final splashGateProvider = NotifierProvider<SplashGate, bool>(SplashGate.new);
