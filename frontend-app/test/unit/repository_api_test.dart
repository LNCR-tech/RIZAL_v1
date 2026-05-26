import 'package:aura_app/core/auth/token_store.dart';
import 'package:aura_app/core/network/api_paths.dart';
import 'package:aura_app/core/network/dio_client.dart';
import 'package:aura_app/features/attendance/data/attendance_repository.dart';
import 'package:aura_app/features/events/data/events_repository.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

class MemoryTokenStore extends TokenStore {
  MemoryTokenStore([this.token]);

  String? token;

  @override
  Future<String?> read() async => token;

  @override
  Future<void> write(String token) async {
    this.token = token;
  }

  @override
  Future<void> clear() async {
    token = null;
  }
}

DioClient stubClient({
  required Object? responseData,
  required void Function(RequestOptions options) onRequest,
}) {
  final client = DioClient(
    tokenStore: MemoryTokenStore('test-token'),
    baseUrl: 'https://api.test',
  );
  client.dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) {
        onRequest(options);
        handler.resolve(
          Response<dynamic>(
            requestOptions: options,
            statusCode: 200,
            data: responseData,
          ),
        );
      },
    ),
  );
  return client;
}

void main() {
  group('EventsRepository API calls', () {
    test('create posts the event body with governance context query', () async {
      late RequestOptions captured;
      final repo = EventsRepository(
        stubClient(
          responseData: {'id': 7, 'name': 'Assembly'},
          onRequest: (options) => captured = options,
        ),
      );

      final event = await repo.create(
        {'name': 'Assembly'},
        governanceContext: 'SSG',
      );

      expect(event.id, 7);
      expect(captured.method, 'POST');
      expect(captured.path, Api.events);
      expect(captured.data, {'name': 'Assembly'});
      expect(captured.queryParameters, {'governance_context': 'SSG'});
      expect(captured.headers['Authorization'], 'Bearer test-token');
    });

    test('update patches the event endpoint with the supplied body', () async {
      late RequestOptions captured;
      final repo = EventsRepository(
        stubClient(
          responseData: {'id': 7, 'name': 'Updated Assembly'},
          onRequest: (options) => captured = options,
        ),
      );

      final event = await repo.update(
        7,
        {'name': 'Updated Assembly'},
      );

      expect(event.name, 'Updated Assembly');
      expect(captured.method, 'PATCH');
      expect(captured.path, Api.event(7));
      expect(captured.data, {'name': 'Updated Assembly'});
      expect(captured.queryParameters, isEmpty);
    });
  });

  group('AttendanceRepository API calls', () {
    test('faceScan posts event, image, and geolocation fields', () async {
      late RequestOptions captured;
      final repo = AttendanceRepository(
        stubClient(
          responseData: {'action': 'time_in', 'attendance_id': 99},
          onRequest: (options) => captured = options,
        ),
      );

      final result = await repo.faceScan(
        eventId: 42,
        imageBase64: 'abc123',
        latitude: 8.1552,
        longitude: 123.8421,
        accuracyM: 18,
      );

      expect(result.isTimeIn, isTrue);
      expect(captured.method, 'POST');
      expect(captured.path, Api.faceScan);
      expect(captured.data, {
        'event_id': 42,
        'image_base64': 'abc123',
        'latitude': 8.1552,
        'longitude': 123.8421,
        'accuracy_m': 18,
        'threshold': null,
      });
    });
  });
}
