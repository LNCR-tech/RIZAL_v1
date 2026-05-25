import 'package:flutter/material.dart';

/// The official Aura brand mark (downloaded from the web app's `/logos/`).
///
/// The white artwork is the default — place it on a dark/ink surface. Pass
/// [onDark] = false to use the black variant on light surfaces; it falls back
/// to the white asset if the black one is unavailable.
class AuraLogo extends StatelessWidget {
  const AuraLogo({super.key, this.size = 40, this.onDark = true});
  final double size;
  final bool onDark;

  static const _white = 'assets/logos/aura_logo_white.png';
  static const _black = 'assets/logos/aura_logo_black.png';

  @override
  Widget build(BuildContext context) {
    return Image.asset(
      onDark ? _white : _black,
      width: size,
      height: size,
      fit: BoxFit.contain,
      errorBuilder: (context, error, stack) =>
          Image.asset(_white, width: size, height: size, fit: BoxFit.contain),
    );
  }
}
