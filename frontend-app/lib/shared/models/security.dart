import '../utils/json.dart';

class UserSession {
  const UserSession({
    required this.id,
    this.ipAddress,
    this.userAgent,
    this.createdAt,
    this.lastSeenAt,
    this.expiresAt,
    this.revokedAt,
    this.isCurrent = false,
  });
  final String id;
  final String? ipAddress;
  final String? userAgent;
  final DateTime? createdAt;
  final DateTime? lastSeenAt;
  final DateTime? expiresAt;
  final DateTime? revokedAt;
  final bool isCurrent;

  bool get isActive => revokedAt == null;

  factory UserSession.fromJson(Map<String, dynamic> j) => UserSession(
        id: asStr(j['id']) ?? '',
        ipAddress: asStr(j['ip_address']),
        userAgent: asStr(j['user_agent']),
        createdAt: asDate(j['created_at']),
        lastSeenAt: asDate(j['last_seen_at']),
        expiresAt: asDate(j['expires_at']),
        revokedAt: asDate(j['revoked_at']),
        isCurrent: j['is_current'] == true,
      );
}

class LoginHistoryItem {
  const LoginHistoryItem({
    required this.id,
    this.success = false,
    this.authMethod,
    this.failureReason,
    this.ipAddress,
    this.userAgent,
    this.createdAt,
  });
  final int id;
  final bool success;
  final String? authMethod;
  final String? failureReason;
  final String? ipAddress;
  final String? userAgent;
  final DateTime? createdAt;

  factory LoginHistoryItem.fromJson(Map<String, dynamic> j) => LoginHistoryItem(
        id: asInt(j['id']) ?? 0,
        success: j['success'] == true,
        authMethod: asStr(j['auth_method']),
        failureReason: asStr(j['failure_reason']),
        ipAddress: asStr(j['ip_address']),
        userAgent: asStr(j['user_agent']),
        createdAt: asDate(j['created_at']),
      );
}
