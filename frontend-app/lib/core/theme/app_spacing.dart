import 'package:flutter/material.dart';

/// Spacing scale (dp). Use these instead of magic numbers.
class AppSpacing {
  AppSpacing._();
  static const double x2 = 2;
  static const double x4 = 4;
  static const double x8 = 8;
  static const double x12 = 12;
  static const double x16 = 16;
  static const double x20 = 20;
  static const double x24 = 24;
  static const double x32 = 32;
  static const double x40 = 40;
  static const double x56 = 56;

  static const EdgeInsets screen =
      EdgeInsets.symmetric(horizontal: x20, vertical: x16);
  static const EdgeInsets card = EdgeInsets.all(x20);
}

/// Corner radii.
class AppRadii {
  AppRadii._();
  static const double control = 12;
  static const double card = 24;
  static const double sheet = 28;
  static const double hero = 32;
  static const double pill = 999;

  static const BorderRadius rControl =
      BorderRadius.all(Radius.circular(control));
  static const BorderRadius rCard = BorderRadius.all(Radius.circular(card));
  static const BorderRadius rSheet =
      BorderRadius.vertical(top: Radius.circular(sheet));
  static const BorderRadius rPill = BorderRadius.all(Radius.circular(pill));
}

/// Soft, never-harsh shadows. Dark mode leans on strokes instead of shadow.
class AppElevation {
  AppElevation._();
  static List<BoxShadow> card(Brightness b) => b == Brightness.dark
      ? const <BoxShadow>[]
      : const [
          BoxShadow(
              color: Color(0x1A000000), blurRadius: 32, offset: Offset(0, 14)),
        ];

  static List<BoxShadow> nav(Brightness b) => const [
        BoxShadow(
            color: Color(0x38000000), blurRadius: 32, offset: Offset(0, 18)),
        BoxShadow(
            color: Color(0x1F000000), blurRadius: 10, offset: Offset(0, 2)),
      ];
}
