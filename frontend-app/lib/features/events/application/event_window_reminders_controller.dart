import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Toggle for the time-based "event window reminders" feature. Separate from
/// [autoCheckInProvider] (location-based geofence prompt). Default ON — this
/// feature does not read location continuously; it only schedules local OS
/// notifications, so the battery cost is negligible.
class EventWindowRemindersController extends Notifier<bool> {
  static const _kKey = 'aura_event_window_reminders';
  SharedPreferences? _prefs;
  // True when set() was called before _restore finished — _restore then
  // persists the explicit value instead of overwriting it.
  bool _dirty = false;

  @override
  bool build() {
    Future.microtask(_restore);
    return true;
  }

  Future<void> _restore() async {
    _prefs = await SharedPreferences.getInstance();
    if (_dirty) {
      // set() ran before _prefs was ready; persist the explicit value now.
      await _prefs!.setBool(_kKey, state);
    } else {
      final stored = _prefs!.getBool(_kKey);
      if (stored != null) state = stored;
    }
  }

  void set(bool value) {
    state = value;
    _dirty = true;
    _prefs?.setBool(_kKey, value);
  }
}

final eventWindowRemindersProvider =
    NotifierProvider<EventWindowRemindersController, bool>(
        EventWindowRemindersController.new);
