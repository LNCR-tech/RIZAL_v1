import '../utils/json.dart';

class AuditLogItem {
  const AuditLogItem({
    required this.id,
    this.schoolId,
    this.actorUserId,
    this.action = '',
    this.status = '',
    this.details,
    this.createdAt,
  });
  final int id;
  final int? schoolId;
  final int? actorUserId;
  final String action;
  final String status;
  final String? details;
  final DateTime? createdAt;

  factory AuditLogItem.fromJson(Map<String, dynamic> j) {
    final dj = j['details_json'];
    final details = j['details'] is String
        ? j['details'] as String
        : dj?.toString();
    return AuditLogItem(
      id: asInt(j['id']) ?? 0,
      schoolId: asInt(j['school_id']),
      actorUserId: asInt(j['actor_user_id']),
      action: asStr(j['action']) ?? '',
      status: asStr(j['status']) ?? '',
      details: details,
      createdAt: asDate(j['created_at']),
    );
  }
}

class AuditLogPage {
  const AuditLogPage({this.total = 0, this.items = const []});
  final int total;
  final List<AuditLogItem> items;

  /// Accepts both the `{total, items}` envelope and a plain list.
  factory AuditLogPage.from(dynamic data) {
    if (data is Map) {
      return AuditLogPage(
        total: asInt(data['total']) ?? 0,
        items: asMapList(data['items']).map(AuditLogItem.fromJson).toList(),
      );
    }
    final items = asMapList(data).map(AuditLogItem.fromJson).toList();
    return AuditLogPage(total: items.length, items: items);
  }
}

class NotificationLogItem {
  const NotificationLogItem({
    required this.id,
    this.schoolId,
    this.userId,
    this.category = '',
    this.channel = '',
    this.status = '',
    this.subject,
    this.message,
    this.createdAt,
  });
  final int id;
  final int? schoolId;
  final int? userId;
  final String category;
  final String channel;
  final String status;
  final String? subject;
  final String? message;
  final DateTime? createdAt;

  factory NotificationLogItem.fromJson(Map<String, dynamic> j) =>
      NotificationLogItem(
        id: asInt(j['id']) ?? 0,
        schoolId: asInt(j['school_id']),
        userId: asInt(j['user_id']),
        category: asStr(j['category']) ?? '',
        channel: asStr(j['channel']) ?? '',
        status: asStr(j['status']) ?? '',
        subject: asStr(j['subject']),
        message: asStr(j['message']),
        createdAt: asDate(j['created_at']),
      );
}
