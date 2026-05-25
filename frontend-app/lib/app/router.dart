import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/auth/role.dart';
import '../core/auth/session_controller.dart';
import 'splash_gate.dart';
import '../features/auth/presentation/change_password_screen.dart';
import '../features/auth/presentation/face_verify_screen.dart';
import '../features/auth/presentation/login_screen.dart';
import '../features/auth/presentation/splash_screen.dart';
import '../features/shell/app_shell.dart';

String workspacePath(Workspace w) {
  switch (w) {
    case Workspace.student:
      return '/student';
    case Workspace.governance:
      return '/governance';
    case Workspace.schoolIt:
      return '/workspace';
    case Workspace.admin:
      return '/admin';
  }
}

/// App router. Redirects react to session changes via [refreshListenable],
/// enforcing: splash while unknown → login when signed out → password/face
/// gates → the correct role workspace.
final routerProvider = Provider<GoRouter>((ref) {
  final refresh = ValueNotifier<int>(0);
  ref.listen(sessionControllerProvider, (_, __) => refresh.value++);
  ref.listen(splashGateProvider, (_, __) => refresh.value++);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: refresh,
    redirect: (context, state) {
      final s = ref.read(sessionControllerProvider);
      final splashDone = ref.read(splashGateProvider);
      final loc = state.matchedLocation;

      if (s.status == SessionStatus.unknown || !splashDone) {
        return loc == '/splash' ? null : '/splash';
      }
      if (!s.isAuthenticated) {
        return loc == '/login' ? null : '/login';
      }
      if (s.needsPasswordChange) {
        return loc == '/change-password' ? null : '/change-password';
      }
      if (s.needsPrivilegedFace) {
        return loc == '/face-verify' ? null : '/face-verify';
      }

      const transient = {
        '/splash',
        '/login',
        '/change-password',
        '/face-verify',
        '/',
      };
      if (transient.contains(loc)) return workspacePath(s.workspace);
      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (_, __) => const SplashScreen()),
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(
          path: '/change-password',
          builder: (_, __) => const ChangePasswordScreen()),
      GoRoute(
          path: '/face-verify', builder: (_, __) => const FaceVerifyScreen()),
      GoRoute(
          path: '/student',
          builder: (_, __) => const AppShell(workspace: Workspace.student)),
      GoRoute(
          path: '/governance',
          builder: (_, __) => const AppShell(workspace: Workspace.governance)),
      GoRoute(
          path: '/workspace',
          builder: (_, __) => const AppShell(workspace: Workspace.schoolIt)),
      GoRoute(
          path: '/admin',
          builder: (_, __) => const AppShell(workspace: Workspace.admin)),
    ],
  );
});
