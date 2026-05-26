import 'package:aura_app/shared/models/analytics.dart';
import 'package:aura_app/shared/models/attendance.dart';
import 'package:aura_app/shared/models/event.dart';
import 'package:aura_app/shared/models/profile.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('AppEvent parses core fields + status helpers', () {
    final e = AppEvent.fromJson({
      'id': 7,
      'name': 'Assembly',
      'status': 'ongoing',
      'start_datetime': '2026-05-22T08:00:00+08:00',
      'end_datetime': '2026-05-22T10:00:00+08:00',
      'geo_latitude': 14.6,
      'geo_longitude': 121.0,
      'geo_required': true,
      'event_type': {'name': 'Assembly'},
      'department_ids': [1, 2],
    });
    expect(e.id, 7);
    expect(e.name, 'Assembly');
    expect(e.isOngoing, isTrue);
    expect(e.hasGeo, isTrue);
    expect(e.geoRequired, isTrue);
    expect(e.eventTypeName, 'Assembly');
    expect(e.departmentIds, [1, 2]);
    expect(e.startDatetime, isNotNull);
  });

  test('FaceScanResult parses action, liveness, and geo', () {
    final r = FaceScanResult.fromJson({
      'action': 'time_in',
      'student_name': 'Jane',
      'attendance_id': 3,
      'liveness': {'label': 'Live', 'score': 0.99},
      'geo': {'ok': true, 'distance_m': 5.0},
      'time_in': '2026-05-22T08:01:00+08:00',
      'message': 'Checked in',
    });
    expect(r.isTimeIn, isTrue);
    expect(r.studentName, 'Jane');
    expect(r.liveness?.isLive, isTrue);
    expect(r.geo?.ok, isTrue);
  });

  test('StudentReport parses summary, records, monthly, type stats', () {
    final rep = StudentReport.fromJson({
      'student': {
        'student_name': 'Jane',
        'total_events': 10,
        'attended_events': 8,
        'attendance_rate': 80.0,
      },
      'attendance_records': [
        {'id': 1, 'event_name': 'A', 'status': 'present'}
      ],
      'monthly_stats': {
        '2026-05': {'present': 3, 'total': 4}
      },
      'event_type_stats': {'Assembly': 2},
    });
    expect(rep.summary.attendedEvents, 8);
    expect(rep.summary.attendanceRate, 80.0);
    expect(rep.records.length, 1);
    expect(rep.records.first.eventName, 'A');
    expect(rep.monthly['2026-05']?['present'], 3);
    expect(rep.eventTypeStats['Assembly'], 2);
  });

  test('UserProfile parses roles and nested student_profile', () {
    final u = UserProfile.fromJson({
      'id': 1,
      'email': 'a@b.com',
      'first_name': 'Jane',
      'last_name': 'Doe',
      'roles': [
        {
          'role': {'name': 'student'}
        }
      ],
      'student_profile': {
        'id': 5,
        'student_id': '2026-001',
        'year_level': 2,
        'is_face_registered': true,
      },
    });
    expect(u.displayName, 'Jane Doe');
    expect(u.roles, ['student']);
    expect(u.studentProfile?.id, 5);
    expect(u.studentProfile?.studentNumber, '2026-001');
    expect(u.studentProfile?.isFaceRegistered, isTrue);
  });
}
