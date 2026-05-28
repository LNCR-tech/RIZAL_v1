import 'package:aura_app/features/schoolit/application/edit_student_form.dart';
import 'package:aura_app/shared/models/profile.dart';
import 'package:flutter_test/flutter_test.dart';

UserProfile _student({
  String firstName = 'Juan',
  String? middleName,
  String lastName = 'Dela Cruz',
  String email = 'juan@school.edu',
  String studentNumber = 'CS-2023-001',
  int? departmentId = 2,
  int? programId = 3,
  int yearLevel = 2,
  String studentStatus = 'ACTIVE',
  bool promotionLocked = false,
}) {
  return UserProfile(
    id: 42,
    email: email,
    firstName: firstName,
    middleName: middleName,
    lastName: lastName,
    studentProfile: StudentProfile(
      id: 10,
      userId: 42,
      studentNumber: studentNumber,
      departmentId: departmentId,
      programId: programId,
      yearLevel: yearLevel,
      studentStatus: studentStatus,
      promotionLocked: promotionLocked,
    ),
  );
}

void main() {
  group('EditStudentForm.fromUser', () {
    test('seeds every field from the source UserProfile', () {
      final form = EditStudentForm.fromUser(_student(
        middleName: 'Antonio',
        promotionLocked: true,
      ));

      expect(form.firstName, 'Juan');
      expect(form.middleName, 'Antonio');
      expect(form.lastName, 'Dela Cruz');
      expect(form.email, 'juan@school.edu');
      expect(form.studentNumber, 'CS-2023-001');
      expect(form.departmentId, 2);
      expect(form.programId, 3);
      expect(form.yearLevel, 2);
      expect(form.studentStatus, 'ACTIVE');
      expect(form.promotionLocked, isTrue);
    });

    test('falls back to ACTIVE when source status is null or unrecognised',
        () {
      final form = EditStudentForm.fromUser(_student(studentStatus: 'XYZ'));
      expect(form.studentStatus, 'ACTIVE');
    });
  });

  group('Dirty tracking', () {
    test('clean form has no dirty sections', () {
      final form = EditStudentForm.fromUser(_student());
      expect(form.identityDirty, isFalse);
      expect(form.academicsDirty, isFalse);
      expect(form.anyDirty, isFalse);
    });

    test('changing email flips identityDirty only', () {
      final form = EditStudentForm.fromUser(_student());
      form.email = 'newjuan@school.edu';
      expect(form.identityDirty, isTrue);
      expect(form.academicsDirty, isFalse);
      expect(form.anyDirty, isTrue);
    });

    test('changing year level flips academicsDirty only', () {
      final form = EditStudentForm.fromUser(_student());
      form.yearLevel = 3;
      expect(form.identityDirty, isFalse);
      expect(form.academicsDirty, isTrue);
    });

    test('changing status to a destructive value flags '
        'statusChangeIsDestructive', () {
      final form = EditStudentForm.fromUser(_student());
      form.studentStatus = 'ARCHIVED';
      expect(form.statusChangeIsDestructive, isTrue);
    });

    test('staying ARCHIVED is NOT a destructive change', () {
      // Already archived, no transition happening → don't confuse the user
      // with a confirmation dialog for an unchanged field.
      final form =
          EditStudentForm.fromUser(_student(studentStatus: 'ARCHIVED'));
      expect(form.studentStatus, 'ARCHIVED');
      expect(form.statusChangeIsDestructive, isFalse);
    });

    test('transitioning to ACTIVE is not destructive', () {
      final form =
          EditStudentForm.fromUser(_student(studentStatus: 'INACTIVE'));
      form.studentStatus = 'ACTIVE';
      expect(form.statusChangeIsDestructive, isFalse);
    });
  });

  group('identityPatch', () {
    test('returns empty map when nothing changed', () {
      final form = EditStudentForm.fromUser(_student());
      expect(form.identityPatch(), isEmpty);
    });

    test('only includes the fields the user actually touched', () {
      final form = EditStudentForm.fromUser(_student());
      form.email = 'newjuan@school.edu';
      expect(form.identityPatch(), {'email': 'newjuan@school.edu'});
    });

    test('emptying middle_name sends explicit null so backend can clear it',
        () {
      final form =
          EditStudentForm.fromUser(_student(middleName: 'Antonio'));
      form.middleName = '   '; // whitespace-only counts as empty
      expect(form.identityPatch(), {'middle_name': null});
    });

    test('trims whitespace before comparing and sending', () {
      final form = EditStudentForm.fromUser(_student());
      form.firstName = '  Juan  '; // same as initial after trim → not dirty
      expect(form.identityDirty, isFalse);
      expect(form.identityPatch(), isEmpty);
    });
  });

  group('academicsPatch', () {
    test('only includes fields the user actually touched', () {
      final form = EditStudentForm.fromUser(_student());
      form.yearLevel = 3;
      form.studentStatus = 'GRADUATED';
      expect(form.academicsPatch(), {
        'year_level': 3,
        'student_status': 'GRADUATED',
      });
    });

    test('omits dept/program when they are unchanged but other fields '
        'are dirty', () {
      final form = EditStudentForm.fromUser(_student());
      form.promotionLocked = true;
      expect(form.academicsPatch(), {'promotion_locked': true});
    });
  });

  group('validateIdentity', () {
    test('passes for a well-formed identity', () {
      final form = EditStudentForm.fromUser(_student());
      expect(form.validateIdentity(), isNull);
    });

    test('flags an empty first name', () {
      final form = EditStudentForm.fromUser(_student());
      form.firstName = '';
      expect(form.validateIdentity(), contains('First name'));
    });

    test('flags a malformed email', () {
      final form = EditStudentForm.fromUser(_student());
      form.email = 'not-an-email';
      expect(form.validateIdentity(), contains('valid email'));
    });
  });

  group('validateAcademics', () {
    test('passes for a well-formed academics block', () {
      final form = EditStudentForm.fromUser(_student());
      expect(form.validateAcademics(), isNull);
    });

    test('flags student numbers with disallowed characters', () {
      // Backend regex (docs:967) allows only [A-Za-z0-9-]; a space here
      // must fail BEFORE the request goes out.
      final form = EditStudentForm.fromUser(_student());
      form.studentNumber = 'CS 2023 001';
      expect(form.validateAcademics(), contains('letters, numbers'));
    });

    test('flags a too-short student number', () {
      final form = EditStudentForm.fromUser(_student());
      form.studentNumber = 'CS';
      expect(form.validateAcademics(), contains('3'));
    });

    test('flags a missing college', () {
      final form = EditStudentForm.fromUser(_student());
      form.departmentId = null;
      expect(form.validateAcademics(), contains('college'));
    });

    test('flags a missing program', () {
      final form = EditStudentForm.fromUser(_student());
      form.programId = null;
      expect(form.validateAcademics(), contains('program'));
    });
  });
}
