import 'package:aura_app/core/layout/breakpoints.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Breakpoints.fromWidth', () {
    test('width < 600 → compact', () {
      expect(Breakpoints.fromWidth(0), Breakpoint.compact);
      expect(Breakpoints.fromWidth(320), Breakpoint.compact);
      expect(Breakpoints.fromWidth(599.99), Breakpoint.compact);
    });

    test('600 ≤ width < 1024 → medium', () {
      expect(Breakpoints.fromWidth(600), Breakpoint.medium);
      expect(Breakpoints.fromWidth(768), Breakpoint.medium);
      expect(Breakpoints.fromWidth(1023.99), Breakpoint.medium);
    });

    test('width ≥ 1024 → expanded', () {
      expect(Breakpoints.fromWidth(1024), Breakpoint.expanded);
      expect(Breakpoints.fromWidth(1440), Breakpoint.expanded);
      expect(Breakpoints.fromWidth(3000), Breakpoint.expanded);
    });
  });

  group('BreakpointHelpers', () {
    test('hasSidebar is false only at compact', () {
      expect(Breakpoint.compact.hasSidebar, isFalse);
      expect(Breakpoint.medium.hasSidebar, isTrue);
      expect(Breakpoint.expanded.hasSidebar, isTrue);
    });

    test('isCompact / isMedium / isExpanded', () {
      expect(Breakpoint.compact.isCompact, isTrue);
      expect(Breakpoint.compact.isMedium, isFalse);
      expect(Breakpoint.compact.isExpanded, isFalse);

      expect(Breakpoint.medium.isMedium, isTrue);
      expect(Breakpoint.medium.isCompact, isFalse);

      expect(Breakpoint.expanded.isExpanded, isTrue);
      expect(Breakpoint.expanded.isMedium, isFalse);
    });

    test('sidebarWidth matches Breakpoints constants', () {
      expect(Breakpoint.compact.sidebarWidth, 0);
      expect(Breakpoint.medium.sidebarWidth,
          Breakpoints.sidebarCollapsedWidth);
      expect(Breakpoint.expanded.sidebarWidth,
          Breakpoints.sidebarExpandedWidth);
    });
  });

  group('BreakpointContext extension', () {
    testWidgets('reads MediaQuery width at compact', (tester) async {
      Breakpoint? captured;
      await tester.pumpWidget(
        MediaQuery(
          data: const MediaQueryData(size: Size(400, 800)),
          child: Builder(
            builder: (context) {
              captured = context.breakpoint;
              return const SizedBox.shrink();
            },
          ),
        ),
      );
      expect(captured, Breakpoint.compact);
    });

    testWidgets('reads MediaQuery width at medium', (tester) async {
      Breakpoint? captured;
      await tester.pumpWidget(
        MediaQuery(
          data: const MediaQueryData(size: Size(800, 1000)),
          child: Builder(
            builder: (context) {
              captured = context.breakpoint;
              return const SizedBox.shrink();
            },
          ),
        ),
      );
      expect(captured, Breakpoint.medium);
    });

    testWidgets('reads MediaQuery width at expanded', (tester) async {
      Breakpoint? captured;
      await tester.pumpWidget(
        MediaQuery(
          data: const MediaQueryData(size: Size(1280, 800)),
          child: Builder(
            builder: (context) {
              captured = context.breakpoint;
              return const SizedBox.shrink();
            },
          ),
        ),
      );
      expect(captured, Breakpoint.expanded);
    });
  });
}
