import 'package:aura_app/app/app.dart';
import 'package:aura_app/app/splash_gate.dart';
import 'package:aura_app/core/auth/auth_meta.dart';
import 'package:aura_app/core/auth/session_controller.dart';
import 'package:aura_app/core/auth/token_store.dart';
import 'package:aura_app/core/network/dio_client.dart';
import 'package:aura_app/core/theme/beta_controller.dart';
import 'package:aura_app/features/events/application/events_providers.dart';
import 'package:aura_app/features/events/application/geofence_background.dart';
import 'package:aura_app/features/events/data/events_repository.dart';
import 'package:aura_app/features/schoolit/presentation/event_editor_screen.dart';
import 'package:aura_app/features/student/application/student_providers.dart';
import 'package:aura_app/shared/models/analytics.dart';
import 'package:aura_app/shared/models/event.dart';
import 'package:aura_app/shared/models/profile.dart';
import 'package:device_preview/device_preview.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ReadySplashGate extends SplashGate {
  @override
  bool build() => true;
}

class FixedBetaNavController extends BetaNavController {
  @override
  bool build() => false;
}

class TestSessionController extends SessionController {
  TestSessionController(this.initial);

  final SessionState initial;

  @override
  SessionState build() => initial;
}

class NoopTokenStore extends TokenStore {
  @override
  Future<String?> read() async => null;

  @override
  Future<void> write(String token) async {}

  @override
  Future<void> clear() async {}
}

class CapturingEventsRepository extends EventsRepository {
  CapturingEventsRepository()
      : super(DioClient(
          tokenStore: NoopTokenStore(),
          baseUrl: 'https://api.test',
        ));

  Map<String, dynamic>? createdBody;
  Map<String, dynamic>? updatedBody;

  @override
  Future<AppEvent> create(
    Map<String, dynamic> body, {
    String? governanceContext,
  }) async {
    createdBody = body;
    return AppEvent(
      id: 99,
      name: body['name'] as String? ?? 'Created event',
      location: body['location'] as String?,
    );
  }

  @override
  Future<AppEvent> update(
    int id,
    Map<String, dynamic> body, {
    String? governanceContext,
  }) async {
    updatedBody = body;
    return AppEvent(
      id: id,
      name: body['name'] as String? ?? 'Updated event',
      location: body['location'] as String?,
    );
  }
}

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

const _signedOutSession = SessionState(status: SessionStatus.unauthenticated);

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
    absentEvents: 1,
    attendanceRate: 75.0,
  ),
);

List<Override> _appOverrides(SessionState session) => [
      sessionControllerProvider
          .overrideWith(() => TestSessionController(session)),
      splashGateProvider.overrideWith(() => ReadySplashGate()),
      betaNavProvider.overrideWith(() => FixedBetaNavController()),
      geofenceBackgroundProvider.overrideWith((ref) {}),
      myProfileProvider.overrideWith((ref) async => _sampleProfile),
      studentReportProvider.overrideWith((ref) async => _sampleReport),
      scheduleEventsProvider.overrideWith((ref) async => [_sampleEvent]),
      ongoingEventsProvider.overrideWith((ref) async => const <AppEvent>[]),
    ];

Future<void> _pumpAuraApp(
  WidgetTester tester, {
  required SessionState session,
}) async {
  SharedPreferences.setMockInitialValues({});
  await tester.pumpWidget(
    ProviderScope(
      overrides: _appOverrides(session),
      child: DevicePreview(
        enabled: false,
        builder: (_) => const AuraApp(),
      ),
    ),
  );
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 500));
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('signed-out app lands on login and exposes login controls',
      (tester) async {
    await _pumpAuraApp(tester, session: _signedOutSession);

    expect(find.text('Welcome back'), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);
    expect(find.text('Continue with Google'), findsOneWidget);

    await tester.tap(find.byTooltip('Show password'));
    await tester.pump();
    expect(find.byTooltip('Hide password'), findsOneWidget);

    await tester.tap(find.text('Sign in'));
    await tester.pump();
    expect(find.text('Enter your email and password.'), findsOneWidget);
  });

  testWidgets('student shell supports primary tab navigation', (tester) async {
    await _pumpAuraApp(tester, session: _studentSession);

    expect(find.text('Hi, E2E'), findsOneWidget);
    expect(find.text('Home'), findsOneWidget);
    expect(find.text('Schedule'), findsOneWidget);
    expect(find.text('Scan'), findsOneWidget);
    expect(find.text('Insights'), findsOneWidget);
    expect(find.text('Account'), findsOneWidget);

    await tester.tap(find.text('Schedule'));
    await tester.pump(const Duration(milliseconds: 350));
    expect(find.text('Schedule'), findsWidgets);

    await tester.tap(find.text('Scan').first);
    await tester.pump(const Duration(milliseconds: 350));
    expect(find.text('No live events'), findsOneWidget);

    await tester.tap(find.text('Insights').first);
    await tester.pump(const Duration(milliseconds: 350));
    expect(find.text('Attendance'), findsWidgets);
  });

  testWidgets('event editor edit flow saves through the event repository',
      (tester) async {
    final repo = CapturingEventsRepository();
    final start = DateTime.utc(2099, 1, 1, 9);
    final end = DateTime.utc(2099, 1, 1, 11);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          eventsRepositoryProvider.overrideWithValue(repo),
        ],
        child: MaterialApp(
          home: Builder(
            builder: (context) => Scaffold(
              body: Center(
                child: TextButton(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => EventEditorScreen(
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
                  child: const Text('Open editor'),
                ),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Open editor'));
    await tester.pump(const Duration(milliseconds: 500));
    await tester.scrollUntilVisible(
      find.text('Save changes'),
      260,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Save changes'));
    await tester.pump(const Duration(milliseconds: 500));

    expect(repo.updatedBody, isNotNull);
    expect(repo.updatedBody?['name'], 'Assembly');
    expect(repo.updatedBody?['location'], 'Main Hall');
    expect(
      DateTime.parse(repo.updatedBody?['start_datetime'] as String).toUtc(),
      start,
    );
    expect(
      DateTime.parse(repo.updatedBody?['end_datetime'] as String).toUtc(),
      end,
    );
    expect(repo.updatedBody?['geo_required'], isFalse);
  });
}
