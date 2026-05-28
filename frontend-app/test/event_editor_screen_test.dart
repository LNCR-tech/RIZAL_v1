import 'package:aura_app/core/auth/token_store.dart';
import 'package:aura_app/core/network/dio_client.dart';
import 'package:aura_app/features/events/data/events_repository.dart';
import 'package:aura_app/features/schoolit/presentation/event_editor_screen.dart';
import 'package:aura_app/shared/models/event.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class MemoryTokenStore extends TokenStore {
  @override
  Future<String?> read() async => null;

  @override
  Future<void> write(String token) async {}

  @override
  Future<void> clear() async {}
}

class FakeEventsRepository extends EventsRepository {
  FakeEventsRepository()
      : super(DioClient(
          tokenStore: MemoryTokenStore(),
          baseUrl: 'https://api.test',
        ));

  Map<String, dynamic>? updatedBody;

  @override
  Future<AppEvent> update(
    int id,
    Map<String, dynamic> body, {
    String? governanceContext,
  }) async {
    updatedBody = body;
    final startValue = body['start_datetime'] as String?;
    final endValue = body['end_datetime'] as String?;
    return AppEvent(
      id: id,
      name: body['name'] as String? ?? 'Updated event',
      location: body['location'] as String?,
      startDatetime: DateTime.tryParse(startValue ?? ''),
      endDatetime: DateTime.tryParse(endValue ?? ''),
    );
  }
}

void main() {
  testWidgets(
    'EventEditorScreen sends edit payload through EventsRepository',
    (tester) async {
      final fakeRepo = FakeEventsRepository();
      final start = DateTime.utc(2099, 1, 1, 9);
      final end = DateTime.utc(2099, 1, 1, 11);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            eventsRepositoryProvider.overrideWithValue(fakeRepo),
          ],
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

      await tester.scrollUntilVisible(
        find.text('Save changes'),
        260,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.ensureVisible(find.text('Save changes'));
      await tester.pump();
      await tester.tap(find.text('Save changes'));
      await tester.pump();

      expect(fakeRepo.updatedBody, isNotNull);
      expect(fakeRepo.updatedBody?['name'], 'Assembly');
      expect(fakeRepo.updatedBody?['location'], 'Main Hall');
      expect(fakeRepo.updatedBody?['start_datetime'], start.toIso8601String());
      expect(fakeRepo.updatedBody?['end_datetime'], end.toIso8601String());
      expect(fakeRepo.updatedBody?['geo_required'], isFalse);
    },
  );
}
