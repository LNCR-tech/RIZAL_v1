import 'package:flutter/animation.dart';

/// Motion tokens (emil-design-eng).
///
/// Rules encoded here: custom curves (the built-in ones are too weak), all UI
/// transitions < 300ms (sheets excepted), **never ease-in** for UI, exits
/// faster than enters, stagger lists ~50ms, press feedback scales to 0.97.
class AppMotion {
  AppMotion._();

  // Curves — strong, intentional.
  static const Cubic easeOut = Cubic(0.23, 1, 0.32, 1); // enter / most UI
  static const Cubic easeInOut = Cubic(0.77, 0, 0.175, 1); // on-screen move
  static const Cubic drawer = Cubic(0.32, 0.72, 0, 1); // sheets / drawers

  // Durations.
  static const Duration press = Duration(milliseconds: 120);
  static const Duration popover = Duration(milliseconds: 180);
  static const Duration dropdown = Duration(milliseconds: 220);
  static const Duration modal = Duration(milliseconds: 260);
  static const Duration sheet = Duration(milliseconds: 360);
  static const Duration exit = Duration(milliseconds: 160);

  // Stagger + press feedback.
  static const Duration staggerStep = Duration(milliseconds: 50);
  static const double pressScale = 0.97;
}
