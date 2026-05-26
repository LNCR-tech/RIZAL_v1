import 'package:aura_app/app/router.dart';
import 'package:aura_app/core/auth/auth_meta.dart';
import 'package:aura_app/core/auth/session_controller.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('resolveAppRedirect', () {
    test('keeps unresolved sessions on splash', () {
      expect(
        resolveAppRedirect(
          session: const SessionState(),
          splashDone: true,
          location: '/login',
        ),
        '/splash',
      );
      expect(
        resolveAppRedirect(
          session: const SessionState(),
          splashDone: true,
          location: '/splash',
        ),
        isNull,
      );
    });

    test('routes signed-out sessions to login', () {
      const session = SessionState(status: SessionStatus.unauthenticated);

      expect(
        resolveAppRedirect(
          session: session,
          splashDone: true,
          location: '/student',
        ),
        '/login',
      );
      expect(
        resolveAppRedirect(
          session: session,
          splashDone: true,
          location: '/login',
        ),
        isNull,
      );
    });

    test('routes password and privileged face gates before workspaces', () {
      const passwordSession = SessionState(
        status: SessionStatus.authenticated,
        meta: AuthMeta(roles: ['student'], mustChangePassword: true),
      );
      const faceSession = SessionState(
        status: SessionStatus.authenticated,
        meta: AuthMeta(roles: ['admin'], tokenType: 'face_pending'),
      );

      expect(
        resolveAppRedirect(
          session: passwordSession,
          splashDone: true,
          location: '/student',
        ),
        '/change-password',
      );
      expect(
        resolveAppRedirect(
          session: faceSession,
          splashDone: true,
          location: '/admin',
        ),
        '/face-verify',
      );
    });

    test('routes authenticated transient pages to the role workspace', () {
      const adminSession = SessionState(
        status: SessionStatus.authenticated,
        meta: AuthMeta(roles: ['admin']),
      );
      const schoolItSession = SessionState(
        status: SessionStatus.authenticated,
        meta: AuthMeta(roles: ['campus_admin']),
      );

      expect(
        resolveAppRedirect(
          session: adminSession,
          splashDone: true,
          location: '/login',
        ),
        '/admin',
      );
      expect(
        resolveAppRedirect(
          session: schoolItSession,
          splashDone: true,
          location: '/',
        ),
        '/workspace',
      );
    });

    test('does not redirect authenticated users already inside the app', () {
      const session = SessionState(
        status: SessionStatus.authenticated,
        meta: AuthMeta(roles: ['student']),
      );

      expect(
        resolveAppRedirect(
          session: session,
          splashDone: true,
          location: '/student',
        ),
        isNull,
      );
    });
  });
}
