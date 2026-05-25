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

  testWidgets(
    'AuraButton in loading state does not fire onPressed',
    (tester) async {
      var tapped = false;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AuraButton(
              label: 'Submit',
              loading: true,
              onPressed: () => tapped = true,
            ),
          ),
        ),
      );

      await tester.tap(find.byType(AuraButton));
      await tester.pump();
      expect(tapped, isFalse);
    },
  );

  testWidgets(
    'AuraButton shows a loading indicator while loading',
    (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: AuraButton(label: 'Log In', loading: true),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    },
  );

  testWidgets('AuraButton renders an optional leading icon', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AuraButton(
            label: 'Create',
            icon: Icons.add,
            onPressed: () {},
          ),
        ),
      ),
    );

    expect(find.byIcon(Icons.add), findsOneWidget);
    expect(find.text('Create'), findsOneWidget);
  });

  testWidgets(
    'AuraButton can render compact non-expanded actions',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(
              child: AuraButton(
                label: 'Cancel',
                variant: AuraButtonVariant.ghost,
                expand: false,
                onPressed: () {},
              ),
            ),
          ),
        ),
      );

      final row = tester.widget<Row>(
        find.descendant(
          of: find.byType(AuraButton),
          matching: find.byType(Row),
        ),
      );
      expect(row.mainAxisSize, MainAxisSize.min);
      expect(find.text('Cancel'), findsOneWidget);
    },
  );
}
