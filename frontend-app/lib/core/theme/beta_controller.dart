import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Opt-in experimental "liquid glass" tab bar (the custom animated capsule nav).
/// Persisted across launches. Off by default — it is GPU-heavy and may lag on
/// low-end devices, and renders only on Impeller (mobile/desktop); the standard
/// nav is used on web.
class BetaNavController extends Notifier<bool> {
  static const _kKey = 'aura_beta_liquid_nav';
  SharedPreferences? _prefs;

  @override
  bool build() {
    Future.microtask(_restore);
    return false;
  }

  Future<void> _restore() async {
    _prefs = await SharedPreferences.getInstance();
    state = _prefs!.getBool(_kKey) ?? false;
  }

  void set(bool value) {
    state = value;
    _prefs?.setBool(_kKey, value);
  }
}

final betaNavProvider =
    NotifierProvider<BetaNavController, bool>(BetaNavController.new);
