import 'package:aura_app/core/widgets/aura_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('AuraButton renders its label and fires onPressed', (tester) async {
    var tapped = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AuraButton(label: 'Sign in', onPressed: () => tapped = true),
        ),
      ),
    );

    expect(find.text('Sign in'), findsOneWidget);
    await tester.tap(find.text('Sign in'));
    await tester.pump();
    expect(tapped, isTrue);
  });

  testWidgets('AuraButton in loading state does not fire onPressed', (tester) async {
    var tapped = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AuraButton(
              label: 'Submit', loading: true, onPressed: () => tapped = true),
        ),
      ),
    );

    await tester.tap(find.byType(AuraButton));
    await tester.pump();
    expect(tapped, isFalse);
  });
}
