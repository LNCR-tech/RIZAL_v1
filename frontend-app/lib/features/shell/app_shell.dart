import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/role.dart';
import '../../core/theme/app_motion.dart';
import '../../core/theme/beta_controller.dart';
import '../../core/widgets/app_scaffold.dart';
import '../../core/widgets/glass_bottom_nav.dart';
import '../../core/widgets/liquid_glass_nav.dart';
import '../admin/presentation/admin_accounts_screen.dart';
import '../admin/presentation/admin_home_screen.dart';
import '../admin/presentation/admin_logs_screen.dart';
import '../admin/presentation/admin_schools_screen.dart';
import '../events/presentation/scan_entry_screen.dart';
import '../events/presentation/schedule_screen.dart';
import '../governance/presentation/governance_events_screen.dart';
import '../governance/presentation/governance_home_screen.dart';
import '../governance/presentation/governance_members_screen.dart';
import '../schoolit/presentation/schoolit_home_screen.dart';
import '../schoolit/presentation/schoolit_schedule_screen.dart';
import '../schoolit/presentation/schoolit_users_screen.dart';
import '../student/presentation/analytics_screen.dart';
import '../student/presentation/student_home_screen.dart';
import 'account_tab.dart';

class _TabSpec {
  const _TabSpec(this.icon, this.label, this.screen);
  final IconData icon;
  final String label;
  final Widget screen;
}

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
    final tabs = _tabsFor(widget.workspace);
    final safeIndex = _index.clamp(0, tabs.length - 1);
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

  List<_TabSpec> _tabsFor(Workspace w) {
    switch (w) {
      case Workspace.student:
        return const [
          _TabSpec(Icons.home_rounded, 'Home', StudentHomeScreen()),
          _TabSpec(Icons.calendar_month_rounded, 'Schedule', ScheduleScreen()),
          _TabSpec(Icons.center_focus_strong_rounded, 'Scan', ScanEntryScreen()),
          _TabSpec(Icons.insights_rounded, 'Insights', AnalyticsScreen()),
          _TabSpec(Icons.person_rounded, 'Account', AccountTab()),
        ];
      case Workspace.governance:
        return const [
          _TabSpec(Icons.dashboard_rounded, 'Home', GovernanceHomeScreen()),
          _TabSpec(Icons.groups_rounded, 'Members', GovernanceMembersScreen()),
          _TabSpec(Icons.event_rounded, 'Events', GovernanceEventsScreen()),
          _TabSpec(Icons.person_rounded, 'Account', AccountTab()),
        ];
      case Workspace.schoolIt:
        return const [
          _TabSpec(Icons.dashboard_rounded, 'Home', SchoolItHomeScreen()),
          _TabSpec(Icons.people_rounded, 'Users', SchoolItUsersScreen()),
          _TabSpec(Icons.calendar_month_rounded, 'Schedule',
              SchoolItScheduleScreen()),
          _TabSpec(Icons.person_rounded, 'Account', AccountTab()),
        ];
      case Workspace.admin:
        return const [
          _TabSpec(Icons.dashboard_rounded, 'Home', AdminHomeScreen()),
          _TabSpec(Icons.apartment_rounded, 'Schools', AdminSchoolsScreen()),
          _TabSpec(Icons.admin_panel_settings_rounded, 'Accounts',
              AdminAccountsScreen()),
          _TabSpec(Icons.receipt_long_rounded, 'Logs', AdminLogsScreen()),
          _TabSpec(Icons.person_rounded, 'Account', AccountTab()),
        ];
    }
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
