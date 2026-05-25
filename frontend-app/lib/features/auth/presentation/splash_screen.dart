import 'package:flutter/material.dart';

import '../../../core/widgets/aura_logo.dart';

/// Launch splash — a native recreation of `aura_animated_bloom.svg`: a green
/// aura reveals behind the white Aura mark, which blooms in with an elastic
/// overshoot. Renders its final state instantly when reduced motion is on.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1500))
    ..forward();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: AnimatedBuilder(
          animation: _c,
          builder: (context, _) {
            final p = _c.value;
            final auraOpacity = reduce
                ? 0.5
                : Curves.easeOut.transform((p / 0.5).clamp(0.0, 1.0)) * 0.6;
            final auraScale = reduce ? 1.0 : 0.85 + 0.25 * p;
            final logoP = reduce
                ? 1.0
                : Curves.easeOutBack
                    .transform(((p - 0.12) / 0.7).clamp(0.0, 1.0));
            final logoScale = 0.72 + 0.28 * logoP;

            return Stack(
              alignment: Alignment.center,
              children: [
                Opacity(
                  opacity: auraOpacity.clamp(0.0, 1.0),
                  child: Transform.scale(
                    scale: auraScale,
                    child: Container(
                      width: 360,
                      height: 360,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: RadialGradient(
                          colors: [
                            Color(0x8CAAFF00),
                            Color(0x1F00FFCC),
                            Color(0x00000000),
                          ],
                          stops: [0.0, 0.45, 1.0],
                        ),
                      ),
                    ),
                  ),
                ),
                Opacity(
                  opacity: logoP.clamp(0.0, 1.0),
                  child: Transform.scale(
                    scale: logoScale,
                    child: const SizedBox(
                      width: 132,
                      height: 132,
                      child: AuraLogo(size: 132),
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
