import 'package:flutter/widgets.dart' show AppLifecycleState;
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app_lifecycle_provider.dart';
import 'polling_pace.dart';

/// A live tick counter for a given [PollingPace]. Any `FutureProvider`
/// that watches this provider re-evaluates whenever the counter
/// increments — that's the whole real-time mechanism.
///
/// Behavior:
/// - Emits `0` immediately when first subscribed (so the screen that
///   just mounted gets fresh data without waiting one interval).
/// - Emits `1, 2, 3, ...` on every `pace.interval` thereafter.
/// - When the app **leaves** the `resumed` state, the stream switches
///   to `empty` (no more ticks → no more refetches → no battery /
///   network drain in the background).
/// - When the app **returns** to `resumed`, the stream resubscribes
///   and the `yield 0` fires immediately → every live provider
///   refreshes the moment the user comes back.
///
/// One ticker per pace — six tickers in the whole app, max — so live
/// providers that share a pace share a tick. No fan-out.
final livePollingTickerProvider =
    StreamProvider.family<int, PollingPace>((ref, pace) {
  final isForeground =
      ref.watch(appLifecycleProvider) == AppLifecycleState.resumed;
  if (!isForeground) {
    return const Stream<int>.empty();
  }
  return _liveTicks(pace.interval);
});

Stream<int> _liveTicks(Duration interval) async* {
  yield 0;
  yield* Stream<int>.periodic(interval, (i) => i + 1);
}
