import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Exposes the current [AppLifecycleState] as a Riverpod-readable value.
///
/// Subscribes to `WidgetsBinding.instance` exactly once (per app session,
/// because the provider is **not** `autoDispose` — at least one live
/// surface always holds a subscription so the observer is never torn
/// down mid-session) and republishes every state change.
///
/// Live-polling tickers gate on this: when the app isn't `resumed`, they
/// stop emitting and every provider that depends on them coasts on its
/// last good data. When the app returns to `resumed`, the tickers
/// resubscribe and emit immediately — every live surface auto-refreshes
/// without the user touching anything.
class AppLifecycleNotifier extends Notifier<AppLifecycleState>
    with WidgetsBindingObserver {
  @override
  AppLifecycleState build() {
    WidgetsBinding.instance.addObserver(this);
    ref.onDispose(() => WidgetsBinding.instance.removeObserver(this));
    return WidgetsBinding.instance.lifecycleState ??
        AppLifecycleState.resumed;
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    this.state = state;
  }
}

final appLifecycleProvider =
    NotifierProvider<AppLifecycleNotifier, AppLifecycleState>(
  AppLifecycleNotifier.new,
);
