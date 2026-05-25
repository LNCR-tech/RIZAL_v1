import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_paths.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/network/paginated.dart';
import '../../../shared/models/notification_item.dart';

class NotificationsRepository {
  NotificationsRepository(this._client);
  final DioClient _client;

  Future<List<NotificationItem>> inbox({int limit = 50}) async {
    final res =
        await _client.get(Api.notificationsInbox, query: {'limit': limit});
    return Paginated.from(
      res.data,
      (e) => NotificationItem.fromJson((e as Map).cast<String, dynamic>()),
    ).data;
  }
}

final notificationsRepositoryProvider = Provider<NotificationsRepository>(
  (ref) => NotificationsRepository(ref.watch(dioClientProvider)),
);
