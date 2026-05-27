import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/role.dart';
import '../../core/layout/breakpoints.dart';
import '../../core/theme/app_tokens.dart';
import 'animated_tab_stack.dart';
import 'navigation_items.dart';
import 'sidebar_nav.dart';

/// Tablet & desktop layout: a fixed [SidebarNav] on the start side plus
/// the same tab content as the mobile shell, cross-faded via
/// [AnimatedTabStack]. Used only at [Breakpoint.medium] and above — at
/// [Breakpoint.compact] the original [AppShell] code path runs unchanged.
///
/// State (selected index) lives in the parent [AppShell] so the choice
/// of layout is purely visual: switching breakpoints mid-session keeps
/// the user on the same tab.
class DesktopShell extends ConsumerWidget {
  const DesktopShell({
    super.key,
    required this.workspace,
    required this.tabs,
    required this.selectedIndex,
    required this.onSelect,
  });

  final Workspace workspace;
  final List<ShellTabSpec> tabs;
  final int selectedIndex;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final isExpanded = context.breakpoint == Breakpoint.expanded;

    return Scaffold(
      backgroundColor: t.bg,
      body: SafeArea(
        bottom: false,
        child: Row(
          children: [
            SidebarNav(
              workspace: workspace,
              tabs: tabs,
              selectedIndex: selectedIndex,
              onSelect: onSelect,
              isExpanded: isExpanded,
            ),
            Expanded(
              child: AnimatedTabStack(
                index: selectedIndex,
                children: [for (final tab in tabs) tab.screen],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
