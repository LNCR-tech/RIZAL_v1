import 'package:aura_app/shared/models/governance.dart';
import 'package:aura_app/shared/models/sanctions.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('GovernanceAccess parses units and prefers SSG', () {
    final a = GovernanceAccess.fromJson({
      'user_id': 1,
      'school_id': 2,
      'permission_codes': ['manage_events'],
      'units': [
        {
          'governance_unit_id': 5,
          'unit_code': 'ORG-1',
          'unit_name': 'Robotics',
          'unit_type': 'ORG',
          'permission_codes': ['view_students'],
        },
        {
          'governance_unit_id': 3,
          'unit_code': 'SSG',
          'unit_name': 'Supreme SG',
          'unit_type': 'SSG',
          'permission_codes': ['manage_members'],
        },
      ],
    });
    expect(a.hasAccess, isTrue);
    expect(a.units.length, 2);
    expect(a.preferred?.type, 'SSG');
    expect(a.preferred?.can('manage_members'), isTrue);
  });

  test('GovernanceUnitDetail parses members + permission codes', () {
    final d = GovernanceUnitDetail.fromJson({
      'id': 3,
      'unit_code': 'SSG',
      'unit_name': 'Supreme SG',
      'unit_type': 'SSG',
      'member_count': 1,
      'members': [
        {
          'id': 9,
          'user_id': 11,
          'position_title': 'President',
          'is_active': true,
          'user': {
            'id': 11,
            'first_name': 'Jane',
            'last_name': 'Doe',
            'student_profile': {'student_id': '2026-1', 'program_name': 'BSCS'},
          },
          'member_permissions': [
            {
              'permission': {'permission_code': 'manage_events'}
            }
          ],
        },
      ],
      'unit_permissions': [
        {
          'permission': {'permission_code': 'view_students'}
        }
      ],
    });
    expect(d.summary.name, 'Supreme SG');
    expect(d.members.length, 1);
    expect(d.members.first.user?.displayName, 'Jane Doe');
    expect(d.members.first.user?.programName, 'BSCS');
    expect(d.members.first.permissionCodes, contains('manage_events'));
    expect(d.unitPermissionCodes, contains('view_students'));
  });

  test('EventStats parses status counts', () {
    final s = EventStats.fromJson({
      'total': 10,
      'statuses': {
        'present': {'count': 7, 'percentage': 70.0},
        'late': {'count': 2, 'percentage': 20.0},
      },
    });
    expect(s.total, 10);
    expect(s.countOf('present'), 7);
    expect(s.countOf('absent'), 0);
  });

  test('SanctionsDashboard + record parse', () {
    final d = SanctionsDashboard.fromJson({
      'total_events': 4,
      'total_pending_sanctions': 3,
      'overall_absence_rate_percent': 12.5,
      'events': [
        {
          'event_id': 1,
          'event_name': 'Assembly',
          'pending_sanctions': 2,
          'participant_count': 50,
          'absent_count': 5,
        }
      ],
    });
    expect(d.totalEvents, 4);
    expect(d.totalPending, 3);
    expect(d.events.first.eventName, 'Assembly');

    final r = SanctionRecord.fromJson({
      'id': 1,
      'event_id': 1,
      'status': 'pending',
      'student': {'first_name': 'A', 'last_name': 'B', 'user_id': 9},
      'items': [
        {'id': 1, 'item_name': 'Detention', 'status': 'pending'}
      ],
    });
    expect(r.student?.displayName, 'A B');
    expect(r.items.first.itemName, 'Detention');
  });
}
