import 'package:aura_app/core/auth/role.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Roles.normalize', () {
    test('folds campus-admin → school-it', () {
      expect(Roles.normalize('campus_admin'), 'school-it');
      expect(Roles.normalize('Campus-Admin'), 'school-it');
    });
    test('lowercases and hyphenates underscores', () {
      expect(Roles.normalize('School_IT'), 'school-it');
      expect(Roles.normalize('ADMIN'), 'admin');
    });
  });

  group('Roles.normalizeList', () {
    test('accepts strings, {name}, and {role:{name}}', () {
      expect(Roles.normalizeList(['student']), ['student']);
      expect(
          Roles.normalizeList([
            {'name': 'admin'}
          ]),
          ['admin']);
      expect(
          Roles.normalizeList([
            {
              'role': {'name': 'campus_admin'}
            }
          ]),
          ['campus_admin']);
    });
    test('returns empty for non-lists', () {
      expect(Roles.normalizeList(null), isEmpty);
      expect(Roles.normalizeList('admin'), isEmpty);
    });
  });

  group('Roles.workspaceFor', () {
    test('prioritizes admin > school-it > governance > student', () {
      expect(Roles.workspaceFor(['admin', 'campus_admin']), Workspace.admin);
      expect(Roles.workspaceFor(['campus_admin']), Workspace.schoolIt);
      expect(Roles.workspaceFor(['ssg']), Workspace.governance);
      expect(Roles.workspaceFor(['student']), Workspace.student);
      expect(Roles.workspaceFor(const []), Workspace.student);
    });
  });

  group('Roles.hasPrivilegedPendingFace', () {
    test('true for privileged role with face_pending token', () {
      expect(
        Roles.hasPrivilegedPendingFace(
            roles: ['admin'],
            tokenType: 'face_pending',
            facePending: false,
            faceRequired: false),
        isTrue,
      );
    });
    test('false for a student even when flags set', () {
      expect(
        Roles.hasPrivilegedPendingFace(
            roles: ['student'],
            tokenType: 'bearer',
            facePending: true,
            faceRequired: true),
        isFalse,
      );
    });
  });
}
