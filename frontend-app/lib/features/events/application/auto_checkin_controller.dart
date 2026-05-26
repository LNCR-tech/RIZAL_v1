import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Opt-in: detect when the user is at an event location and prompt them to check
/// in. Off by default — it reads device location (while the app is open) to match
/// the user against nearby events.
class AutoCheckInController extends Notifier<bool> {
  static const _kKey = 'aura_auto_checkin_nearby';
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

final autoCheckInProvider =
    NotifierProvider<AutoCheckInController, bool>(AutoCheckInController.new);

/// Placeholder toggle for fully hands-free auto check-in (no scan needed). Not
/// wired to any behaviour yet — surfaced in settings as "coming soon".
class AutoCheckFullController extends Notifier<bool> {
  static const _kKey = 'aura_auto_checkin_full';
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

final autoCheckFullProvider =
    NotifierProvider<AutoCheckFullController, bool>(AutoCheckFullController.new);
