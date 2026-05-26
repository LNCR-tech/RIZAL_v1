import 'package:flutter/material.dart';

import '../../core/auth/role.dart';
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

class ShellTabSpec {
  const ShellTabSpec(this.icon, this.label, this.screen);

  final IconData icon;
  final String label;
  final Widget screen;
}

List<ShellTabSpec> shellTabsForWorkspace(Workspace workspace) {
  switch (workspace) {
    case Workspace.student:
      return const [
        ShellTabSpec(Icons.home_rounded, 'Home', StudentHomeScreen()),
        ShellTabSpec(Icons.calendar_month_rounded, 'Schedule', ScheduleScreen()),
        ShellTabSpec(Icons.center_focus_strong_rounded, 'Scan', ScanEntryScreen()),
        ShellTabSpec(Icons.insights_rounded, 'Insights', AnalyticsScreen()),
        ShellTabSpec(Icons.person_rounded, 'Account', AccountTab()),
      ];
    case Workspace.governance:
      return const [
        ShellTabSpec(Icons.dashboard_rounded, 'Home', GovernanceHomeScreen()),
        ShellTabSpec(Icons.groups_rounded, 'Members', GovernanceMembersScreen()),
        ShellTabSpec(Icons.event_rounded, 'Events', GovernanceEventsScreen()),
        ShellTabSpec(Icons.person_rounded, 'Account', AccountTab()),
      ];
    case Workspace.schoolIt:
      return const [
        ShellTabSpec(Icons.dashboard_rounded, 'Home', SchoolItHomeScreen()),
        ShellTabSpec(Icons.people_rounded, 'Users', SchoolItUsersScreen()),
        ShellTabSpec(
            Icons.calendar_month_rounded, 'Schedule', SchoolItScheduleScreen()),
        ShellTabSpec(Icons.person_rounded, 'Account', AccountTab()),
      ];
    case Workspace.admin:
      return const [
        ShellTabSpec(Icons.dashboard_rounded, 'Home', AdminHomeScreen()),
        ShellTabSpec(Icons.apartment_rounded, 'Schools', AdminSchoolsScreen()),
        ShellTabSpec(Icons.admin_panel_settings_rounded, 'Accounts',
            AdminAccountsScreen()),
        ShellTabSpec(Icons.receipt_long_rounded, 'Logs', AdminLogsScreen()),
        ShellTabSpec(Icons.person_rounded, 'Account', AccountTab()),
      ];
  }
}
