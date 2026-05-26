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
      // A student inside the app must already have a face reference enrolled
      // (otherwise the new needsFaceRegistration gate would catch them).
      const session = SessionState(
        status: SessionStatus.authenticated,
        meta: AuthMeta(roles: ['student'], faceReferenceEnrolled: true),
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

    test(
        'students without a face reference are routed to register-face before workspaces',
        () {
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
        '/register-face',
        reason:
            'A student with no face_reference_enrolled must be gated to the '
            'first-login registration screen.',
      );
      // The register-face screen itself is allowed to render — no further
      // redirect once they're already there.
      expect(
        resolveAppRedirect(
          session: session,
          splashDone: true,
          location: '/register-face',
        ),
        isNull,
      );
    });

    test('face-registration gate does NOT apply to privileged roles', () {
      // Admin / school-IT / governance officers register from
      // Account → Security → Face ID; their MFA path is /face-verify.
      // The new gate is student-only.
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
          location: '/admin',
        ),
        isNull,
      );
      expect(
        resolveAppRedirect(
          session: schoolItSession,
          splashDone: true,
          location: '/workspace',
        ),
        isNull,
      );
    });
  });
}
