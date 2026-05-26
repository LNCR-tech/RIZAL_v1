import 'package:aura_app/shared/models/import_job.dart';
import 'package:aura_app/shared/models/school.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Department + Program parse', () {
    expect(Department.fromJson({'id': 1, 'name': 'CCS'}).name, 'CCS');
    final p =
        Program.fromJson({'id': 2, 'name': 'BSCS', 'department_ids': [1, 3]});
    expect(p.name, 'BSCS');
    expect(p.departmentIds, [1, 3]);
  });

  test('SchoolBranding parses event policy', () {
    final s = SchoolBranding.fromJson({
      'school_id': 1,
      'school_name': 'Acme U',
      'school_code': 'ACME',
      'primary_color': '#AAFF00',
      'event_default_early_check_in_minutes': 15,
      'event_default_late_threshold_minutes': 30,
      'event_default_sign_out_grace_minutes': 10,
      'subscription_status': 'active',
    });
    expect(s.schoolName, 'Acme U');
    expect(s.earlyCheckInMinutes, 15);
    expect(s.lateThresholdMinutes, 30);
    expect(s.signOutGraceMinutes, 10);
    expect(s.subscriptionStatus, 'active');
  });

  test('ImportPreview + ImportJobStatus parse', () {
    final p = ImportPreview.fromJson({
      'filename': 'x.csv',
      'total_rows': 10,
      'valid_rows': 8,
      'invalid_rows': 2,
      'can_commit': false,
      'preview_token': 'tok',
      'rows': [
        {'row': 1, 'status': 'valid', 'errors': []},
        {
          'row': 2,
          'status': 'failed',
          'errors': ['bad email']
        },
      ],
    });
    expect(p.totalRows, 10);
    expect(p.validRows, 8);
    expect(p.canCommit, isFalse);
    expect(p.rows.length, 2);
    expect(p.rows[1].errors.first, 'bad email');

    final s = ImportJobStatus.fromJson({
      'job_id': 'j1',
      'state': 'completed',
      'total_rows': 8,
      'processed_rows': 8,
      'success_count': 8,
      'failed_count': 0,
      'percentage_completed': 100.0,
    });
    expect(s.isDone, isTrue);
    expect(s.successCount, 8);
    expect(s.isFailed, isFalse);
  });
}
