import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// User preference for motion. `system` follows the OS "reduce motion"
/// accessibility setting; `on` forces reduced motion; `off` forces full motion.
enum MotionPref { system, on, off }

class MotionController extends Notifier<MotionPref> {
  static const _kKey = 'aura_reduce_motion';
  SharedPreferences? _prefs;

  @override
  MotionPref build() {
    Future.microtask(_restore);
    return MotionPref.system;
  }

  Future<void> _restore() async {
    _prefs = await SharedPreferences.getInstance();
    final v = _prefs!.getString(_kKey);
    state = MotionPref.values.firstWhere(
      (e) => e.name == v,
      orElse: () => MotionPref.system,
    );
  }

  void set(MotionPref pref) {
    state = pref;
    _prefs?.setString(_kKey, pref.name);
  }

  /// Whether motion should be reduced, given the OS accessibility flag.
  static bool resolve(MotionPref pref, bool osDisableAnimations) {
    switch (pref) {
      case MotionPref.on:
        return true;
      case MotionPref.off:
        return false;
      case MotionPref.system:
        return osDisableAnimations;
    }
  }
}

final motionControllerProvider =
    NotifierProvider<MotionController, MotionPref>(MotionController.new);
