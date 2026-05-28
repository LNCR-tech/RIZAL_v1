import 'package:aura_app/features/schoolit/application/student_filter.dart';
import 'package:aura_app/shared/models/profile.dart';
import 'package:flutter_test/flutter_test.dart';

UserProfile _student(
  int id, {
  String firstName = 'Juan',
  String lastName = 'Dela Cruz',
  String? email,
  String? studentNumber,
  int? programId,
  int? yearLevel,
  String? status,
  bool isFaceRegistered = false,
}) {
  return UserProfile(
    id: id,
    email: email ?? 'student$id@school.edu',
    firstName: firstName,
    lastName: lastName,
    studentProfile: StudentProfile(
      id: id + 1000,
      userId: id,
      studentNumber: studentNumber ?? 'CS-2023-$id',
      programId: programId,
      yearLevel: yearLevel,
      studentStatus: status,
      isFaceRegistered: isFaceRegistered,
    ),
  );
}

/// A non-student account (faculty / school-IT / admin) — should never
/// appear in filter output regardless of the rest of the predicates.
UserProfile _faculty(int id) => UserProfile(
      id: id,
      email: 'faculty$id@school.edu',
      firstName: 'F',
      lastName: 'Acuity',
      // no studentProfile
    );

void main() {
  group('StudentFilter.isActive', () {
    test('empty filter is inactive', () {
      expect(const StudentFilter().isActive, isFalse);
      expect(const StudentFilter().activeCount, 0);
    });

    test('whitespace-only query is NOT considered active', () {
      const f = StudentFilter(query: '   ');
      expect(f.isActive, isFalse);
    });

    test('each axis contributes one to activeCount', () {
      const f = StudentFilter(
        query: 'juan',
        programIds: {1, 2},
        yearLevels: {2},
        statuses: {'ACTIVE'},
        faceEnrolledOnly: true,
      );
      expect(f.isActive, isTrue);
      expect(f.activeCount, 5);
    });
  });

  group('StudentFilter.apply', () {
    test('empty filter passes every STUDENT and drops non-students', () {
      final users = [
        _student(1),
        _student(2),
        _faculty(99),
      ];
      final result = const StudentFilter().apply(users);
      expect(result.map((u) => u.id), [1, 2],
          reason: 'Faculty accounts (no studentProfile) must be dropped '
              'even with an empty filter so the screen never accidentally '
              'lists them under a college.');
    });

    test('query matches displayName, email, and studentNumber', () {
      final users = [
        _student(1, firstName: 'Maria', lastName: 'Reyes'),
        _student(2, email: 'specialcase@school.edu'),
        _student(3, studentNumber: 'ENG-2024-077'),
        _student(4, firstName: 'Pedro'),
      ];

      expect(const StudentFilter(query: 'maria').apply(users).map((u) => u.id),
          [1]);
      expect(
          const StudentFilter(query: 'specialcase')
              .apply(users)
              .map((u) => u.id),
          [2]);
      expect(const StudentFilter(query: 'eng-2024').apply(users).map((u) => u.id),
          [3]);
    });

    test('query is case-insensitive and trims whitespace', () {
      final users = [_student(1, firstName: 'Juan')];
      expect(
          const StudentFilter(query: '  JUAN  ').apply(users).map((u) => u.id),
          [1]);
    });

    test('programIds filter narrows to selected programs', () {
      final users = [
        _student(1, programId: 1),
        _student(2, programId: 2),
        _student(3, programId: 3),
        _student(4, programId: null),
      ];
      final result =
          const StudentFilter(programIds: {1, 3}).apply(users).map((u) => u.id);
      expect(result, [1, 3],
          reason: 'Null programId never matches an explicit program set.');
    });

    test('yearLevels filter narrows to selected years', () {
      final users = [
        _student(1, yearLevel: 1),
        _student(2, yearLevel: 2),
        _student(3, yearLevel: 4),
        _student(4, yearLevel: null),
      ];
      final result =
          const StudentFilter(yearLevels: {2, 4}).apply(users).map((u) => u.id);
      expect(result, [2, 3]);
    });

    test('statuses filter is case-insensitive on the source side', () {
      final users = [
        _student(1, status: 'ACTIVE'),
        _student(2, status: 'active'), // backend may differ; normalize.
        _student(3, status: 'INACTIVE'),
      ];
      final result = const StudentFilter(statuses: {'ACTIVE'})
          .apply(users)
          .map((u) => u.id);
      expect(result, [1, 2]);
    });

    test('faceEnrolledOnly requires isFaceRegistered=true', () {
      final users = [
        _student(1, isFaceRegistered: true),
        _student(2, isFaceRegistered: false),
      ];
      final result = const StudentFilter(faceEnrolledOnly: true)
          .apply(users)
          .map((u) => u.id);
      expect(result, [1]);
    });

    test('multiple filters AND together', () {
      final users = [
        _student(1, programId: 1, yearLevel: 2, status: 'ACTIVE'),
        _student(2, programId: 1, yearLevel: 3, status: 'ACTIVE'),
        _student(3, programId: 2, yearLevel: 2, status: 'ACTIVE'),
        _student(4, programId: 1, yearLevel: 2, status: 'INACTIVE'),
      ];
      final result = const StudentFilter(
        programIds: {1},
        yearLevels: {2},
        statuses: {'ACTIVE'},
      ).apply(users).map((u) => u.id);
      expect(result, [1],
          reason: 'Only id=1 satisfies program=1 AND year=2 AND status=ACTIVE.');
    });

    test('copyWith preserves untouched axes', () {
      const a = StudentFilter(
        query: 'juan',
        yearLevels: {1, 2},
      );
      final b = a.copyWith(faceEnrolledOnly: true);
      expect(b.query, 'juan');
      expect(b.yearLevels, {1, 2});
      expect(b.faceEnrolledOnly, isTrue);
    });

    test('cleared() returns a no-constraint filter', () {
      const a = StudentFilter(query: 'juan', yearLevels: {1});
      final empty = a.cleared();
      expect(empty.isActive, isFalse);
      expect(empty.activeCount, 0);
    });

    test('equality is value-based across all axes', () {
      const a = StudentFilter(
        query: 'juan',
        programIds: {1, 2},
        yearLevels: {2},
        statuses: {'ACTIVE'},
        faceEnrolledOnly: true,
      );
      const b = StudentFilter(
        query: 'juan',
        programIds: {2, 1}, // same set, different iteration order
        yearLevels: {2},
        statuses: {'ACTIVE'},
        faceEnrolledOnly: true,
      );
      expect(a, equals(b));
      expect(a.hashCode, b.hashCode);
    });
  });
}
