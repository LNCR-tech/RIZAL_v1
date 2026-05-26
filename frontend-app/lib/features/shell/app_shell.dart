import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/role.dart';
import '../../core/theme/app_motion.dart';
import '../../core/theme/beta_controller.dart';
import '../../core/widgets/app_scaffold.dart';
import '../../core/widgets/glass_bottom_nav.dart';
import '../../core/widgets/liquid_glass_nav.dart';
import 'navigation_items.dart';

/// Role-based shell: an [IndexedStack] of tabs with the glass bottom nav.
/// Tab sets differ per [Workspace]; deeper navigation arrives per phase.
class AppShell extends ConsumerStatefulWidget {
  const AppShell({super.key, required this.workspace});
  final Workspace workspace;

  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _AppShellState extends ConsumerState<AppShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final tabs = shellTabsForWorkspace(widget.workspace);
    final safeIndex = _index.clamp(0, tabs.length - 1).toInt();
    final beta = ref.watch(betaNavProvider);

    return AppScaffold(
      body: _AnimatedTabStack(
        index: safeIndex,
        children: [for (final tab in tabs) tab.screen],
      ),
      bottomNav: beta
          ? LiquidGlassNav(
              currentIndex: safeIndex,
              onTap: (i) => setState(() => _index = i),
              items: [
                for (final tab in tabs)
                  LiquidGlassNavItem(tab.icon, tab.label),
              ],
            )
          : GlassBottomNav(
              currentIndex: safeIndex,
              onTap: (i) => setState(() => _index = i),
              items: [
                for (final tab in tabs)
                  GlassNavItem(icon: tab.icon, label: tab.label),
              ],
            ),
    );
  }
}

/// Keeps every tab mounted (state preserved) and **cross-fades** between the
/// outgoing and incoming tab — the old view fades out as the new fades in, with
/// no slide and no blank flash. Instant when reduced motion is on.
class _AnimatedTabStack extends StatefulWidget {
  const _AnimatedTabStack({required this.index, required this.children});
  final int index;
  final List<Widget> children;

  @override
  State<_AnimatedTabStack> createState() => _AnimatedTabStackState();
}

class _AnimatedTabStackState extends State<_AnimatedTabStack>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: AppMotion.modal, value: 1);
  int _prev = 0;

  @override
  void didUpdateWidget(_AnimatedTabStack old) {
    super.didUpdateWidget(old);
    if (old.index != widget.index) {
      _prev = old.index;
      _c.forward(from: 0);
    }
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return Stack(
      children: [
        for (var i = 0; i < widget.children.length; i++)
          Positioned.fill(
            child: AnimatedBuilder(
              animation: _c,
              builder: (context, child) {
                final isCurrent = i == widget.index;
                // The outgoing tab stays painted (fading out) until the
                // cross-fade finishes, so there's no blank flash.
                final isLeaving = i == _prev && _c.value < 1.0;
                final v = Curves.easeOut.transform(_c.value);
                final opacity = reduce
                    ? (isCurrent ? 1.0 : 0.0)
                    : (isCurrent ? v : 1 - v);
                return Offstage(
                  offstage: !(isCurrent || isLeaving),
                  child: IgnorePointer(
                    ignoring: !isCurrent,
                    child: Opacity(
                      opacity: opacity.clamp(0.0, 1.0),
                      child: child,
                    ),
                  ),
                );
              },
              child: TickerMode(
                enabled: i == widget.index,
                child: widget.children[i],
              ),
            ),
          ),
      ],
    );
  }
}
