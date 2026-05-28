import 'package:aura_app/features/events/application/event_phase_provider.dart';
import 'package:aura_app/features/events/presentation/widgets/event_phase_banner.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _wrap({BannerSelection? selection}) {
  return ProviderScope(
    overrides: [
      eventPhaseProvider.overrideWith((ref) => selection),
    ],
    child: const MaterialApp(
      home: Scaffold(body: EventPhaseBanner()),
    ),
  );
}

void main() {
  testWidgets('renders empty when no phase is active', (tester) async {
    await tester.pumpWidget(_wrap(selection: null));
    // Single pump only: _PulseDot.repeat() never settles, so pumpAndSettle
    // would time out. Initial frame is enough to assert the rendered text.
    await tester.pump();
    expect(find.text('CHECK-IN IS OPEN'), findsNothing);
    expect(find.text('SIGN-OUT IS OPEN'), findsNothing);
    expect(find.text('LAST CALL: SIGN OUT'), findsNothing);
  });

  testWidgets('renders the check-in banner when checkInOpen', (tester) async {
    await tester.pumpWidget(_wrap(
      selection: BannerSelection(
          eventId: 1, name: 'General Assembly', phase: BannerPhase.checkInOpen),
    ));
    // Single pump only: _PulseDot.repeat() never settles, so pumpAndSettle
    // would time out. Initial frame is enough to assert the rendered text.
    await tester.pump();
    expect(find.text('CHECK-IN IS OPEN'), findsOneWidget);
    expect(find.text('General Assembly'), findsOneWidget);
    expect(find.text('Check in'), findsOneWidget);
  });

  testWidgets('renders the sign-out banner when signOutOpen', (tester) async {
    await tester.pumpWidget(_wrap(
      selection: BannerSelection(
          eventId: 2,
          name: 'Departmental Meeting',
          phase: BannerPhase.signOutOpen),
    ));
    // Single pump only: _PulseDot.repeat() never settles, so pumpAndSettle
    // would time out. Initial frame is enough to assert the rendered text.
    await tester.pump();
    expect(find.text('SIGN-OUT IS OPEN'), findsOneWidget);
    expect(find.text('Sign out'), findsOneWidget);
  });

  testWidgets('renders the last-call banner when signOutClosingSoon',
      (tester) async {
    await tester.pumpWidget(_wrap(
      selection: BannerSelection(
          eventId: 3,
          name: 'Departmental Meeting',
          phase: BannerPhase.signOutClosingSoon),
    ));
    // Single pump only: _PulseDot.repeat() never settles, so pumpAndSettle
    // would time out. Initial frame is enough to assert the rendered text.
    await tester.pump();
    expect(find.text('LAST CALL: SIGN OUT'), findsOneWidget);
  });
}
