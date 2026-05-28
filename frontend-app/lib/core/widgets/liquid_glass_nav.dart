import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:liquid_glass_renderer/liquid_glass_renderer.dart';

import '../theme/app_spacing.dart';
import '../theme/app_tokens.dart';

class LiquidGlassNavItem {
  const LiquidGlassNavItem(this.icon, this.label);
  final IconData icon;
  final String label;
}

/// Beta tab bar: a translucent dark **frosted pill** (pure UI) with a colourless
/// **liquid-glass capsule** blob (Dynamic-Island / medicine-pill shape) that
/// follows the finger, **zooms bigger while sliding** (rendered outside the pill
/// clip so it can pop out), and refracts the page showing through. Only the
/// active icon/label takes the university primary colour.
class LiquidGlassNav extends StatefulWidget {
  const LiquidGlassNav({
    super.key,
    required this.items,
    required this.currentIndex,
    required this.onTap,
  });

  final List<LiquidGlassNavItem> items;
  final int currentIndex;
  final ValueChanged<int> onTap;

  @override
  State<LiquidGlassNav> createState() => _LiquidGlassNavState();
}

class _LiquidGlassNavState extends State<LiquidGlassNav>
    with SingleTickerProviderStateMixin {
  static const double _height = 82;
  static const double _gapX = 3;
  static const double _blobH = 66;
  // The blob is always at least this much wider than tall, so it stays a
  // horizontal pill (not a circle) even on bars with many tabs.
  static const double _blobMinW = _blobH * 1.6;

  late final AnimationController _anim = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 240));
  late double _pos = widget.currentIndex.toDouble();
  double _animFrom = 0;
  double _animTo = 0;
  bool _dragging = false;

  @override
  void initState() {
    super.initState();
    _animTo = _pos;
  }

  @override
  void didUpdateWidget(LiquidGlassNav old) {
    super.didUpdateWidget(old);
    if (old.currentIndex != widget.currentIndex && !_dragging) {
      _animateTo(widget.currentIndex.toDouble());
    }
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  void _animateTo(double target) {
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (reduce) {
      setState(() => _pos = target);
      return;
    }
    _animFrom = _pos;
    _animTo = target;
    _pos = target;
    _anim.forward(from: 0);
  }

  /// Current blob slot position (fractional) — plain slide, no stretch.
  double _blobSlot() {
    return (_dragging || !_anim.isAnimating)
        ? _pos
        : lerpDouble(
            _animFrom, _animTo, Curves.easeOutCubic.transform(_anim.value))!;
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final primary = t.accent; // university primary — active icon only
    final n = widget.items.length;
    final activeIndex =
        _dragging ? _pos.round().clamp(0, n - 1) : widget.currentIndex;

    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x12, 0, AppSpacing.x12, AppSpacing.x8),
        child: SizedBox(
          height: _height,
          child: LayoutBuilder(
            builder: (context, c) {
              final itemW = c.maxWidth / n;
              final top = (c.maxHeight - _blobH) / 2;
              final maxPos = (n - 1).toDouble();

              void commit(int i) {
                final clamped = i.clamp(0, n - 1);
                if (clamped != widget.currentIndex) {
                  HapticFeedback.selectionClick();
                  widget.onTap(clamped);
                }
              }

              void dragTo(Offset local) {
                final p = (local.dx / itemW - 0.5).clamp(0.0, maxPos);
                setState(() => _pos = p);
                commit(p.round());
              }

              return GestureDetector(
                behavior: HitTestBehavior.opaque,
                onHorizontalDragStart: (d) {
                  _anim.stop();
                  setState(() => _dragging = true);
                  dragTo(d.localPosition);
                },
                onHorizontalDragUpdate: (d) => dragTo(d.localPosition),
                onHorizontalDragEnd: (_) {
                  final target = _pos.round().clamp(0, n - 1);
                  setState(() => _dragging = false);
                  commit(target);
                  _animateTo(target.toDouble());
                },
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    // 1. Frosted pill (clipped capsule).
                    Positioned.fill(
                      child: ClipRRect(
                        borderRadius: AppRadii.rPill,
                        child: BackdropFilter(
                          filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                begin: Alignment.topCenter,
                                end: Alignment.bottomCenter,
                                colors: [
                                  Colors.black.withOpacity(0.20),
                                  Colors.black.withOpacity(0.28),
                                ],
                              ),
                              borderRadius: AppRadii.rPill,
                              border:
                                  Border.all(color: Colors.white.withOpacity(0.14)),
                            ),
                          ),
                        ),
                      ),
                    ),
                    // 2. Icons + labels — wrapped in a RepaintBoundary so the
                    // pixels are guaranteed to land in the parent compositing
                    // texture that the blob's BackdropFilter samples. Without
                    // this, Impeller can defer the icon paint into a sibling
                    // sub-layer that the lens shader never reads, and the icons
                    // appear flat under the blob. The RepaintBoundary also
                    // means scrolling the page above doesn't repaint the icons
                    // every frame — a small perf bonus on low-end devices.
                    Positioned.fill(
                      child: RepaintBoundary(
                        child: Row(
                          children: [
                            for (var i = 0; i < n; i++)
                              Expanded(
                                child: _NavItem(
                                  key: ValueKey(
                                    'bottom-nav-${widget.items[i].label}',
                                  ),
                                  item: widget.items[i],
                                  active: i == activeIndex,
                                  activeColor: primary,
                                  onTap: () => commit(i),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                    // 3. Liquid-glass capsule blob. We manage the
                    // [LiquidGlassLayer] ourselves (rather than
                    // `LiquidGlass.withOwnLayer`) so we can:
                    //   * Read / tune the lens settings in one place.
                    //   * Avoid the package's nested RepaintBoundary that
                    //     occasionally isolates the icons from the
                    //     BackdropFilter sample on Impeller — the symptom
                    //     was the blob bending the page beneath the nav but
                    //     not the icons sliding under it (iOS 26 bends both).
                    // Settings boosted to iOS-26 territory: thicker virtual
                    // depth, higher refractive index, visible chromatic
                    // fringe at the lens edge. Adjust to taste — these are
                    // calibrated to bend a 23dp icon by ~6-8px which the eye
                    // reads as a real lens, not just a tint.
                    AnimatedBuilder(
                      animation: _anim,
                      builder: (context, child) {
                        // Zoom while dragging, and pop (zoom in/out) on tap —
                        // no stretch, just slide + zoom.
                        final scale = _dragging
                            ? 1.4
                            : (_anim.isAnimating
                                ? 1 + 0.4 * (1 - (2 * _anim.value - 1).abs())
                                : 1.0);
                        final slotW = itemW - _gapX * 2;
                        final desiredW = slotW > _blobMinW ? slotW : _blobMinW;
                        final center = (_blobSlot() + 0.5) * itemW;
                        // Clamp the blob within the pill so it compresses at the
                        // left/right edges instead of overlapping out of it (the
                        // zoom still pops out via Transform.scale).
                        const inset = 3.0;
                        var left = center - desiredW / 2;
                        var right = center + desiredW / 2;
                        if (left < inset) left = inset;
                        if (right > c.maxWidth - inset) right = c.maxWidth - inset;
                        return Positioned(
                          left: left,
                          top: top,
                          width: right - left,
                          height: _blobH,
                          child: Transform.scale(scale: scale, child: child),
                        );
                      },
                      child: const IgnorePointer(
                        child: LiquidGlassLayer(
                          settings: LiquidGlassSettings(
                            blur: 0,
                            thickness: 32,
                            refractiveIndex: 1.55,
                            // Subtle hint of chromatic aberration — the
                            // refraction/bending was the wanted effect; the
                            // strong colour fringing at 6.5 read as gritty
                            // up close. 1.5 keeps a tasteful glass-edge
                            // shimmer without the rainbow smear.
                            chromaticAberration: 1.5,
                            glassColor: Color(0x14FFFFFF),
                            lightAngle: 1.5708,
                            lightIntensity: 2.6,
                            saturation: 1.35,
                          ),
                          child: LiquidGlass(
                            glassContainsChild: false,
                            shape: LiquidRoundedSuperellipse(
                                borderRadius: _blobH / 2),
                            child: SizedBox.expand(),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem({
    super.key,
    required this.item,
    required this.active,
    required this.activeColor,
    required this.onTap,
  });
  final LiquidGlassNavItem item;
  final bool active;
  final Color activeColor;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final target = active ? activeColor : Colors.white.withOpacity(0.64);
    return Semantics(
      container: true,
      button: true,
      selected: active,
      label: item.label,
      child: ExcludeSemantics(
        child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onTap,
        child: Center(
          child: TweenAnimationBuilder<Color?>(
            duration: const Duration(milliseconds: 250),
            curve: Curves.easeOut,
            tween: ColorTween(end: target),
            builder: (context, color, _) {
              final c = color ?? target;
              return Column(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(item.icon, size: 23, color: c),
                  const SizedBox(height: 4),
                  Text(
                    item.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 11,
                      height: 1,
                      fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                      color: c,
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ),
      ),
    );
  }
}
