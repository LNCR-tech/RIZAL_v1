import 'package:aura_app/core/auth/role.dart';
import 'package:aura_app/features/admin/presentation/admin_accounts_screen.dart';
import 'package:aura_app/features/admin/presentation/admin_home_screen.dart';
import 'package:aura_app/features/admin/presentation/admin_logs_screen.dart';
import 'package:aura_app/features/admin/presentation/admin_schools_screen.dart';
import 'package:aura_app/features/events/presentation/scan_entry_screen.dart';
import 'package:aura_app/features/events/presentation/schedule_screen.dart';
import 'package:aura_app/features/governance/presentation/governance_events_screen.dart';
import 'package:aura_app/features/governance/presentation/governance_home_screen.dart';
import 'package:aura_app/features/governance/presentation/governance_members_screen.dart';
import 'package:aura_app/features/schoolit/presentation/schoolit_home_screen.dart';
import 'package:aura_app/features/schoolit/presentation/schoolit_schedule_screen.dart';
import 'package:aura_app/features/schoolit/presentation/schoolit_users_screen.dart';
import 'package:aura_app/features/shell/account_tab.dart';
import 'package:aura_app/features/shell/navigation_items.dart';
import 'package:aura_app/features/student/presentation/analytics_screen.dart';
import 'package:aura_app/features/student/presentation/student_home_screen.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('shellTabsForWorkspace', () {
    test('returns student navigation items', () {
      final tabs = shellTabsForWorkspace(Workspace.student);

      expect(tabs.map((tab) => tab.label).toList(), [
        'Home',
        'Schedule',
        'Scan',
        'Insights',
        'Account',
      ]);
      expect(tabs[0].screen, isA<StudentHomeScreen>());
      expect(tabs[1].screen, isA<ScheduleScreen>());
      expect(tabs[2].screen, isA<ScanEntryScreen>());
      expect(tabs[3].screen, isA<AnalyticsScreen>());
      expect(tabs[4].screen, isA<AccountTab>());
    });

    test('returns governance navigation items', () {
      final tabs = shellTabsForWorkspace(Workspace.governance);

      expect(tabs.map((tab) => tab.label).toList(), [
        'Home',
        'Members',
        'Events',
        'Account',
      ]);
      expect(tabs[0].screen, isA<GovernanceHomeScreen>());
      expect(tabs[1].screen, isA<GovernanceMembersScreen>());
      expect(tabs[2].screen, isA<GovernanceEventsScreen>());
      expect(tabs[3].screen, isA<AccountTab>());
    });

    test('returns school IT navigation items', () {
      final tabs = shellTabsForWorkspace(Workspace.schoolIt);

      expect(tabs.map((tab) => tab.label).toList(), [
        'Home',
        'Users',
        'Schedule',
        'Account',
      ]);
      expect(tabs[0].screen, isA<SchoolItHomeScreen>());
      expect(tabs[1].screen, isA<SchoolItUsersScreen>());
      expect(tabs[2].screen, isA<SchoolItScheduleScreen>());
      expect(tabs[3].screen, isA<AccountTab>());
    });

    test('returns admin navigation items', () {
      final tabs = shellTabsForWorkspace(Workspace.admin);

      expect(tabs.map((tab) => tab.label).toList(), [
        'Home',
        'Schools',
        'Accounts',
        'Logs',
        'Account',
      ]);
      expect(tabs[0].screen, isA<AdminHomeScreen>());
      expect(tabs[1].screen, isA<AdminSchoolsScreen>());
      expect(tabs[2].screen, isA<AdminAccountsScreen>());
      expect(tabs[3].screen, isA<AdminLogsScreen>());
      expect(tabs[4].screen, isA<AccountTab>());
    });
  });
}
