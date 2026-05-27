import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/role.dart';
import '../../core/layout/breakpoints.dart';
import '../../core/theme/beta_controller.dart';
import '../../core/widgets/app_scaffold.dart';
import '../../core/widgets/glass_bottom_nav.dart';
import '../../core/widgets/liquid_glass_nav.dart';
import 'animated_tab_stack.dart';
import 'desktop_shell.dart';
import 'navigation_items.dart';

/// Role-based shell: an [AnimatedTabStack] of tabs.
///
/// Layout branches on [BreakpointContext.breakpoint]:
///   * [Breakpoint.compact] (< 600 dp): the mobile shell with the
///     glass / liquid bottom nav. Byte-for-byte identical to the
///     pre-responsive build.
///   * [Breakpoint.medium] / [Breakpoint.expanded]: [DesktopShell]
///     with [SidebarNav] on the start side.
///
/// State (the selected tab index) lives here so the user keeps their
/// position when the window crosses a breakpoint (e.g. tablet rotation).
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

    if (context.breakpoint.hasSidebar) {
      return DesktopShell(
        workspace: widget.workspace,
        tabs: tabs,
        selectedIndex: safeIndex,
        onSelect: (i) => setState(() => _index = i),
      );
    }

    // Mobile path — unchanged from the pre-responsive build: glass or
    // liquid bottom nav driven by the beta toggle.
    final beta = ref.watch(betaNavProvider);

    return AppScaffold(
      body: AnimatedTabStack(
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
