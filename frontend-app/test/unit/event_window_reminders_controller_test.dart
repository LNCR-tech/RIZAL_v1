import 'package:aura_app/features/events/application/event_window_reminders_controller.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('EventWindowRemindersController', () {
    setUp(() {
      SharedPreferences.setMockInitialValues({});
    });

    test('defaults to true (opt-out) when nothing is persisted', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      expect(container.read(eventWindowRemindersProvider), isTrue);
    });

    test('persists explicit off across containers', () async {
      final c1 = ProviderContainer();
      c1.read(eventWindowRemindersProvider.notifier).set(false);
      // Wait for _restore to complete — it observes _dirty and persists the
      // explicit value (otherwise the early set() races ahead of _prefs init).
      await Future.delayed(const Duration(milliseconds: 30));
      c1.dispose();

      final c2 = ProviderContainer();
      addTearDown(c2.dispose);
      // First read triggers build() which queues _restore.
      c2.read(eventWindowRemindersProvider);
      // Wait for _restore to finish and update the state.
      await Future.delayed(const Duration(milliseconds: 30));

      expect(c2.read(eventWindowRemindersProvider), isFalse);
    });
  });
}
