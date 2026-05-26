import '../utils/json.dart';

/// A row from the user's notification inbox (`/notifications/inbox/me`).
class NotificationItem {
  const NotificationItem({
    required this.id,
    this.category,
    this.channel,
    this.status,
    this.subject = '',
    this.message = '',
    this.createdAt,
  });

  final int id;
  final String? category;
  final String? channel;
  final String? status;
  final String subject;
  final String message;
  final DateTime? createdAt;

  factory NotificationItem.fromJson(Map<String, dynamic> j) => NotificationItem(
        id: asInt(j['id']) ?? 0,
        category: asStr(j['category']),
        channel: asStr(j['channel']),
        status: asStr(j['status']),
        subject: asStr(j['subject']) ?? '',
        message: asStr(j['message']) ?? '',
        createdAt: asDate(j['created_at']),
      );
}
