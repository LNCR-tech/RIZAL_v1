import 'package:aura_app/app/app.dart';
import 'package:aura_app/app/splash_gate.dart';
import 'package:aura_app/core/auth/token_store.dart';
import 'package:aura_app/core/theme/beta_controller.dart';
import 'package:aura_app/features/events/application/geofence_background.dart';
import 'package:device_preview/device_preview.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _runBackendE2e = bool.fromEnvironment('AURA_RUN_BACKEND_E2E');
const _studentEmail = String.fromEnvironment(
  'AURA_E2E_STUDENT_EMAIL',
  defaultValue: 'student@test.com',
);
const _studentPassword = String.fromEnvironment(
  'AURA_E2E_STUDENT_PASSWORD',
  defaultValue: 'TestPass123!',
);

class ReadySplashGate extends SplashGate {
  @override
  bool build() => true;
}

class FixedBetaNavController extends BetaNavController {
  @override
  bool build() => false;
}

class MemoryTokenStore extends TokenStore {
  String? _token;

  @override
  Future<String?> read() async => _token;

  @override
  Future<void> write(String token) async {
    _token = token;
  }

  @override
  Future<void> clear() async {
    _token = null;
  }
}

Future<void> _pumpRealApp(WidgetTester tester) async {
  await tester.pumpWidget(const SizedBox.shrink());
  await tester.pump();
  SharedPreferences.setMockInitialValues({});
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        splashGateProvider.overrideWith(() => ReadySplashGate()),
        betaNavProvider.overrideWith(() => FixedBetaNavController()),
        geofenceBackgroundProvider.overrideWith((ref) {}),
        tokenStoreProvider.overrideWithValue(MemoryTokenStore()),
      ],
      child: DevicePreview(
        enabled: false,
        builder: (_) => const HeroMode(
          enabled: false,
          child: AuraApp(),
        ),
      ),
    ),
  );
  await tester.pump();
}

Finder _bottomNavTab(String label) => find.byKey(ValueKey('bottom-nav-$label'));

Future<void> _pumpUntilFound(
  WidgetTester tester,
  Finder finder, {
  String? reason,
  int attempts = 100,
}) async {
  for (var i = 0; i < attempts; i++) {
    await tester.pump(const Duration(milliseconds: 250));
    if (finder.evaluate().isNotEmpty) {
      return;
    }
  }
  fail('Timed out waiting for ${reason ?? finder.toString()}');
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets(
    'student can sign in against the real backend and open a scheduled event',
    (tester) async {
      await _pumpRealApp(tester);
      await _pumpUntilFound(
        tester,
        find.text('Welcome back'),
        reason: 'login screen',
      );

      await tester.enterText(find.byType(TextField).at(0), _studentEmail);
      await tester.enterText(find.byType(TextField).at(1), _studentPassword);
      await tester.pump();
      await tester.ensureVisible(find.text('Sign in'));
      await tester.tap(find.text('Sign in'));

      await _pumpUntilFound(
        tester,
        find.text('Hi, Test'),
        reason: 'student home after backend login',
      );
      expect(_bottomNavTab('Home'), findsOneWidget);
      expect(_bottomNavTab('Schedule'), findsOneWidget);

      await tester.tap(_bottomNavTab('Schedule'));
      await _pumpUntilFound(
        tester,
        find.text('Upcoming'),
        reason: 'schedule loaded from backend',
      );
      await tester.tap(find.text('Upcoming'));

      final seededEvent = find.text('Seed Year Level Event');
      await _pumpUntilFound(
        tester,
        seededEvent,
        reason: 'seeded backend event',
      );
      await tester.ensureVisible(seededEvent);
      await tester.tap(seededEvent);

      await _pumpUntilFound(
        tester,
        find.text('Seed Hall'),
        reason: 'event detail loaded from backend',
      );
      expect(find.text('Location'), findsWidgets);
    },
    skip: !_runBackendE2e,
  );
}
