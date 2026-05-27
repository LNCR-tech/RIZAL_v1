import 'package:aura_app/shared/models/admin.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('SchoolSummary parses status', () {
    final s = SchoolSummary.fromJson({
      'school_id': 1,
      'school_name': 'Acme',
      'school_code': 'ACME',
      'subscription_status': 'active',
      'active_status': false,
    });
    expect(s.schoolId, 1);
    expect(s.schoolName, 'Acme');
    expect(s.activeStatus, isFalse);
  });

  test('SchoolItAccount parses + displayName', () {
    final a = SchoolItAccount.fromJson({
      'user_id': 5,
      'email': 'a@b.com',
      'first_name': 'Jo',
      'last_name': 'Cruz',
      'school_id': 1,
      'school_name': 'Acme',
      'is_active': true,
    });
    expect(a.userId, 5);
    expect(a.displayName, 'Jo Cruz');
    expect(a.isActive, isTrue);
  });

  test('CreateSchoolResult parses nested school + temp password', () {
    final c = CreateSchoolResult.fromJson({
      'school': {'school_id': 1, 'school_name': 'Acme'},
      'school_it_user_id': 5,
      'school_it_email': 'it@acme.edu',
      'generated_temporary_password': 'TempPass1!',
    });
    expect(c.school.schoolName, 'Acme');
    expect(c.schoolItUserId, 5);
    expect(c.generatedTemporaryPassword, 'TempPass1!');
  });
}
