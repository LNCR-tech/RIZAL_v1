import 'package:aura_app/core/auth/auth_meta.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('parses a token payload', () {
    final m = AuthMeta.fromJson({
      'access_token': 'x',
      'token_type': 'bearer',
      'email': 'a@b.com',
      'roles': ['campus_admin'],
      'user_id': 5,
      'first_name': 'Jane',
      'last_name': 'Doe',
      'must_change_password': true,
      'school_id': 2,
      'school_name': 'Acme',
      'primary_color': '#AAFF00',
      'face_verification_pending': true,
    });
    expect(m.email, 'a@b.com');
    expect(m.roles, ['campus_admin']);
    expect(m.userId, 5);
    expect(m.displayName, 'Jane Doe');
    expect(m.mustChangePassword, isTrue);
    expect(m.primaryColor, '#AAFF00');
    expect(m.isAdmin, isFalse); // campus_admin is not platform admin
  });

  test('derives is_admin from roles when omitted', () {
    expect(AuthMeta.fromJson({'roles': ['admin']}).isAdmin, isTrue);
  });

  test('builds initials and falls back to email for name', () {
    expect(AuthMeta.fromJson({'first_name': 'Jane', 'last_name': 'Doe'}).initials, 'JD');
    expect(AuthMeta.fromJson({'email': 'x@y.com'}).displayName, 'x@y.com');
  });

  test('round-trips through json', () {
    final m = AuthMeta.fromJson({'email': 'a@b.com', 'roles': ['student'], 'user_id': 1});
    final again = AuthMeta.fromJson(m.toJson());
    expect(again.email, 'a@b.com');
    expect(again.roles, ['student']);
    expect(again.userId, 1);
  });
}
