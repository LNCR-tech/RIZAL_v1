import 'package:aura_app/app/app.dart';
import 'package:aura_app/app/splash_gate.dart';
import 'package:aura_app/core/auth/auth_meta.dart';
import 'package:aura_app/core/auth/session_controller.dart';
import 'package:aura_app/core/theme/beta_controller.dart';
import 'package:aura_app/features/events/application/events_providers.dart';
import 'package:aura_app/features/events/application/geofence_background.dart';
import 'package:aura_app/features/governance/application/governance_providers.dart';
import 'package:aura_app/features/schoolit/presentation/event_editor_screen.dart';
import 'package:aura_app/features/student/application/student_providers.dart';
import 'package:aura_app/shared/models/analytics.dart';
import 'package:aura_app/shared/models/event.dart';
import 'package:aura_app/shared/models/governance.dart';
import 'package:aura_app/shared/models/profile.dart';
import 'package:device_preview/device_preview.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _ReadySplashGate extends SplashGate {
  @override
  bool build() => true;
}

class _FixedBetaNavController extends BetaNavController {
  @override
  bool build() => false;
}

class _TestSessionController extends SessionController {
  _TestSessionController(this.initial);

  final SessionState initial;

  @override
  SessionState build() => initial;
}

class _QualityViewport {
  const _QualityViewport(this.name, this.size);

  final String name;
  final Size size;
}

const _viewports = [
  _QualityViewport('mobile', Size(390, 844)),
  _QualityViewport('tablet', Size(768, 1024)),
  _QualityViewport('desktop', Size(1440, 900)),
];

const _signedOutSession = SessionState(status: SessionStatus.unauthenticated);

const _studentSession = SessionState(
  status: SessionStatus.authenticated,
  meta: AuthMeta(
    email: 'student@test.com',
    roles: ['student'],
    firstName: 'E2E',
    lastName: 'Student',
    schoolName: 'Test University',
  ),
);

final _sampleEvent = AppEvent(
  id: 1,
  name: 'E2E Orientation',
  location: 'Main Hall',
  status: 'upcoming',
  startDatetime: DateTime.now().add(const Duration(days: 7)),
  endDatetime: DateTime.now().add(const Duration(days: 7, hours: 2)),
);

const _sampleProfile = UserProfile(
  id: 1,
  email: 'student@test.com',
  firstName: 'E2E',
  lastName: 'Student',
  roles: ['student'],
  studentProfile: StudentProfile(id: 10, studentNumber: 'S-001'),
);

const _sampleReport = StudentReport(
  summary: StudentSummary(
    studentName: 'E2E Student',
    totalEvents: 4,
    attendedEvents: 3,
    lateEvents: 0,
    absentEvents: 1,
    attendanceRate: 75,
  ),
  monthly: {
    '2026-01': {'present': 2},
    '2026-02': {'present': 3},
  },
);

List<Override> _appOverrides(SessionState session) => [
      sessionControllerProvider
          .overrideWith(() => _TestSessionController(session)),
      splashGateProvider.overrideWith(() => _ReadySplashGate()),
      betaNavProvider.overrideWith(() => _FixedBetaNavController()),
      geofenceBackgroundProvider.overrideWith((ref) {}),
      governanceAccessProvider
          .overrideWith((ref) async => const GovernanceAccess()),
      myProfileProvider.overrideWith((ref) async => _sampleProfile),
      studentReportProvider.overrideWith((ref) async => _sampleReport),
      scheduleEventsProvider.overrideWith((ref) async => [_sampleEvent]),
      ongoingEventsProvider.overrideWith((ref) async => const <AppEvent>[]),
    ];

Future<void> _pumpAuraApp(
  WidgetTester tester, {
  required SessionState session,
}) async {
  await tester.pumpWidget(const SizedBox.shrink());
  await tester.pump();
  SharedPreferences.setMockInitialValues({});
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: _appOverrides(session),
      child: DevicePreview(
        enabled: false,
        builder: (_) => const AuraApp(),
      ),
    ),
  );
  await tester.pump();
  for (var i = 0; i < 4; i++) {
    await tester.pump(const Duration(milliseconds: 250));
  }
}

Future<void> _pumpEventEditor(WidgetTester tester) async {
  final start = DateTime.now().add(const Duration(days: 7));
  final end = start.add(const Duration(hours: 2));

  await tester.pumpWidget(
    ProviderScope(
      child: MaterialApp(
        home: EventEditorScreen(
          event: AppEvent(
            id: 7,
            name: 'Assembly',
            location: 'Main Hall',
            startDatetime: start,
            endDatetime: end,
          ),
        ),
      ),
    ),
  );
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 300));
}

Future<void> _withViewport(
  WidgetTester tester,
  _QualityViewport viewport,
  Future<void> Function() body,
) async {
  await tester.binding.setSurfaceSize(viewport.size);
  try {
    await body();
  } finally {
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.binding.setSurfaceSize(null);
  }
}

void _expectNoFlutterExceptions(WidgetTester tester, String context) {
  final exceptions = <Object>[];
  for (var exception = tester.takeException();
      exception != null;
      exception = tester.takeException()) {
    exceptions.add(exception);
  }

  expect(exceptions, isEmpty, reason: context);
}

void _expectVisibleIconButtonsHaveLabels(
  WidgetTester tester,
  String context,
) {
  final missing = <String>[];
  for (final element in find.byType(IconButton).evaluate()) {
    final button = element.widget as IconButton;
    if (button.onPressed == null) continue;

    final tooltip = button.tooltip?.trim();
    final iconLabel = button.icon is Icon
        ? ((button.icon as Icon).semanticLabel ?? '').trim()
        : '';
    if ((tooltip == null || tooltip.isEmpty) && iconLabel.isEmpty) {
      missing.add(element.widget.toStringShort());
    }
  }

  expect(
    missing,
    isEmpty,
    reason: '$context has visible icon-only buttons without labels',
  );
}

Finder _bottomNavTab(String label) => find.byKey(ValueKey('bottom-nav-$label'));

Future<void> _tapAndExpectUiResponse(
  WidgetTester tester, {
  required Finder target,
  required String context,
  required VoidCallback expectResponse,
}) async {
  if (target.evaluate().isEmpty) {
    fail('$context target is missing');
  }

  final visibleTarget =
      target.hitTestable().evaluate().isNotEmpty ? target.hitTestable() : target;
  await tester.ensureVisible(visibleTarget.first);
  await tester.pump();
  await tester.tap(visibleTarget.first);
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 500));
  _expectNoFlutterExceptions(tester, context);
  expectResponse();
}

void main() {
  testWidgets(
    'key app states avoid layout exceptions across common viewports',
    (tester) async {
      for (final viewport in _viewports) {
        await _withViewport(tester, viewport, () async {
          await _pumpAuraApp(tester, session: _signedOutSession);
          _expectNoFlutterExceptions(tester, 'login at ${viewport.name}');

          await _pumpAuraApp(tester, session: _studentSession);
          _expectNoFlutterExceptions(tester, 'student home at ${viewport.name}');

          for (final label in ['Schedule', 'Scan', 'Insights']) {
            final target = _bottomNavTab(label);
            if (target.evaluate().isEmpty) {
              fail('student $label tab target is missing at ${viewport.name}');
            }
            await tester.tap(target.first);
            await tester.pump(const Duration(milliseconds: 500));
            _expectNoFlutterExceptions(
              tester,
              'student $label tab at ${viewport.name}',
            );
          }

          await _pumpEventEditor(tester);
          _expectNoFlutterExceptions(
            tester,
            'event editor at ${viewport.name}',
          );
        });
      }
    },
  );

  testWidgets(
    'key app controls expose accessible semantics labels',
    (tester) async {
      final semantics = tester.ensureSemantics();
      addTearDown(semantics.dispose);

      await _pumpAuraApp(tester, session: _signedOutSession);
      expect(find.bySemanticsLabel('Show password'), findsWidgets);
      expect(find.bySemanticsLabel('Sign in'), findsWidgets);
      expect(find.bySemanticsLabel('Continue with Google'), findsWidgets);
      _expectVisibleIconButtonsHaveLabels(tester, 'login');

      await _pumpAuraApp(tester, session: _studentSession);
      for (final label in ['Home', 'Schedule', 'Scan', 'Insights', 'Account']) {
        expect(find.bySemanticsLabel(label), findsWidgets);
      }
      _expectVisibleIconButtonsHaveLabels(tester, 'student home');

      await _pumpEventEditor(tester);
      expect(find.byTooltip('Pick start date'), findsOneWidget);
      expect(find.byTooltip('Pick start time'), findsOneWidget);
      expect(find.byTooltip('Pick end date'), findsOneWidget);
      expect(find.byTooltip('Pick end time'), findsOneWidget);
      _expectVisibleIconButtonsHaveLabels(tester, 'event editor');
    },
  );

  testWidgets(
    'key safe pressables produce expected UI responses',
    (tester) async {
      await _pumpAuraApp(tester, session: _signedOutSession);

      await _tapAndExpectUiResponse(
        tester,
        target: find.byTooltip('Show password'),
        context: 'login password visibility toggle',
        expectResponse: () =>
            expect(find.byTooltip('Hide password'), findsOneWidget),
      );

      await _tapAndExpectUiResponse(
        tester,
        target: find.text('Sign in'),
        context: 'empty login submit validation',
        expectResponse: () =>
            expect(find.text('Enter your email and password.'), findsOneWidget),
      );

      await _tapAndExpectUiResponse(
        tester,
        target: find.text('Continue with Google'),
        context: 'google sign-in placeholder feedback',
        expectResponse: () => expect(
          find.text('Google Sign-In wiring lands in Phase 1.'),
          findsOneWidget,
        ),
      );

      await _pumpAuraApp(tester, session: _studentSession);

      await _tapAndExpectUiResponse(
        tester,
        target: _bottomNavTab('Schedule'),
        context: 'student schedule tab navigation',
        expectResponse: () =>
            expect(find.text('Upcoming'), findsOneWidget),
      );

      await _tapAndExpectUiResponse(
        tester,
        target: find.text('Upcoming'),
        context: 'schedule upcoming filter',
        expectResponse: () =>
            expect(find.text('E2E Orientation'), findsOneWidget),
      );

      await _tapAndExpectUiResponse(
        tester,
        target: _bottomNavTab('Scan'),
        context: 'student scan tab navigation',
        expectResponse: () =>
            expect(find.text('No live events'), findsOneWidget),
      );

      await _tapAndExpectUiResponse(
        tester,
        target: _bottomNavTab('Insights'),
        context: 'student insights tab navigation',
        expectResponse: () => expect(find.text('75%'), findsOneWidget),
      );

      await _tapAndExpectUiResponse(
        tester,
        target: _bottomNavTab('Account'),
        context: 'student account tab navigation',
        expectResponse: () =>
            expect(find.text('student@test.com'), findsOneWidget),
      );

      await _pumpEventEditor(tester);

      await _tapAndExpectUiResponse(
        tester,
        target: find.byTooltip('Pick start date'),
        context: 'event editor start date picker',
        expectResponse: () =>
            expect(find.byType(DatePickerDialog), findsOneWidget),
      );
      Navigator.of(tester.element(find.byType(DatePickerDialog))).pop();
      await tester.pump(const Duration(milliseconds: 300));

      await _tapAndExpectUiResponse(
        tester,
        target: find.byTooltip('Pick start time'),
        context: 'event editor start time picker',
        expectResponse: () =>
            expect(find.byType(TimePickerDialog), findsOneWidget),
      );
      Navigator.of(tester.element(find.byType(TimePickerDialog))).pop();
      await tester.pump(const Duration(milliseconds: 300));
    },
  );
}
