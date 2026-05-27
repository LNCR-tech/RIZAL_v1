import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/admin.dart';
import '../../../shared/models/logs.dart';
import '../../../shared/models/subscription.dart';
import '../data/admin_repository.dart';

final adminSchoolsProvider =
    FutureProvider.autoDispose<List<SchoolSummary>>((ref) {
  return ref.watch(adminRepositoryProvider).schools();
});

final adminAccountsProvider =
    FutureProvider.autoDispose<List<SchoolItAccount>>((ref) {
  return ref.watch(adminRepositoryProvider).accounts();
});

final subscriptionProvider =
    FutureProvider.autoDispose.family<SchoolSubscription, int>((ref, schoolId) {
  return ref.watch(adminRepositoryProvider).subscription(schoolId);
});

/// Audit logs keyed by a (search, status) filter record.
final auditLogsProvider = FutureProvider.autoDispose
    .family<AuditLogPage, ({String q, String status})>((ref, f) {
  return ref.watch(adminRepositoryProvider).auditLogs(q: f.q, status: f.status);
});

/// Notification logs keyed by a status filter ('' = all).
final notificationLogsProvider = FutureProvider.autoDispose
    .family<List<NotificationLogItem>, String>((ref, status) {
  return ref.watch(adminRepositoryProvider).notificationLogs(status: status);
});
