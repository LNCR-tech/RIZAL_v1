import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Assistant speed mode. `true` = **Fast** (slim prompt, no tools — quick replies,
/// ideal for the on-device / local model). `false` = **Thinking** (full prompt +
/// data tools + charts, slower). Sent per request so the backend can switch.
/// Persisted; defaults to ON (fast) — that's what a small local model needs.
class FastModeController extends Notifier<bool> {
  static const _kKey = 'aura_assistant_fast_mode';
  SharedPreferences? _prefs;

  @override
  bool build() {
    Future.microtask(_restore);
    return true;
  }

  Future<void> _restore() async {
    _prefs = await SharedPreferences.getInstance();
    state = _prefs!.getBool(_kKey) ?? true;
  }

  void set(bool value) {
    if (value == state) return;
    state = value;
    _prefs?.setBool(_kKey, value);
  }
}

final fastModeProvider =
    NotifierProvider<FastModeController, bool>(FastModeController.new);
