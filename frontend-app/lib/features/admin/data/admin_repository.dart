import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_paths.dart';
import '../../../core/network/dio_client.dart';
import '../../../shared/models/admin.dart';
import '../../../shared/models/logs.dart';
import '../../../shared/models/school.dart';
import '../../../shared/models/subscription.dart';
import '../../../shared/utils/json.dart';

class AdminRepository {
  AdminRepository(this._client);
  final DioClient _client;

  Future<List<SchoolSummary>> schools() async {
    final r = await _client.get(Api.adminSchools);
    return asMapList(r.data).map(SchoolSummary.fromJson).toList();
  }

  Future<SchoolBranding> updateSchoolStatus(int id,
      {bool? active, String? subscription}) async {
    final r = await _client.patch(Api.adminSchoolStatus(id), data: {
      if (active != null) 'active_status': active,
      if (subscription != null) 'subscription_status': subscription,
    });
    return SchoolBranding.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<CreateSchoolResult> createSchool({
    required String schoolName,
    required String primaryColor,
    String? schoolCode,
    required String itEmail,
    required String itFirstName,
    String? itMiddleName,
    required String itLastName,
    String? itPassword,
  }) async {
    final form = FormData.fromMap({
      'school_name': schoolName,
      'primary_color': primaryColor,
      if (schoolCode != null && schoolCode.isNotEmpty) 'school_code': schoolCode,
      'school_it_email': itEmail,
      'school_it_first_name': itFirstName,
      if (itMiddleName != null && itMiddleName.isNotEmpty)
        'school_it_middle_name': itMiddleName,
      'school_it_last_name': itLastName,
      if (itPassword != null && itPassword.isNotEmpty)
        'school_it_password': itPassword,
    });
    final r = await _client.post(Api.adminCreateSchoolIt, data: form);
    return CreateSchoolResult.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<List<SchoolItAccount>> accounts() async {
    final r = await _client.get(Api.adminSchoolItAccounts);
    return asMapList(r.data).map(SchoolItAccount.fromJson).toList();
  }

  Future<SchoolItAccount> updateAccountStatus(int userId, bool isActive) async {
    final r = await _client
        .patch(Api.adminAccountStatus(userId), data: {'is_active': isActive});
    return SchoolItAccount.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<String?> resetAccountPassword(int userId) async {
    final r = await _client.post(Api.adminAccountResetPassword(userId));
    final d = r.data;
    return d is Map ? asStr(d['temporary_password']) : null;
  }

  // ── Subscription (per-school plan / capability lever) ──
  Future<SchoolSubscription> subscription(int schoolId) async {
    final r =
        await _client.get(Api.subscriptionMe, query: {'school_id': schoolId});
    return SchoolSubscription.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<SchoolSubscription> updateSubscription(
    int schoolId, {
    String? planName,
    int? userLimit,
    int? eventLimitMonthly,
    int? importLimitMonthly,
    bool? autoRenew,
    int? reminderDaysBefore,
  }) async {
    final r = await _client.put(
      '${Api.subscriptionMe}?school_id=$schoolId',
      data: {
        if (planName != null) 'plan_name': planName,
        if (userLimit != null) 'user_limit': userLimit,
        if (eventLimitMonthly != null) 'event_limit_monthly': eventLimitMonthly,
        if (importLimitMonthly != null)
          'import_limit_monthly': importLimitMonthly,
        if (autoRenew != null) 'auto_renew': autoRenew,
        if (reminderDaysBefore != null)
          'reminder_days_before': reminderDaysBefore,
      },
    );
    return SchoolSubscription.fromJson((r.data as Map).cast<String, dynamic>());
  }

  // ── Logs ──
  Future<AuditLogPage> auditLogs({
    String? q,
    String? action,
    String? status,
    int limit = 50,
    int offset = 0,
  }) async {
    final r = await _client.get(Api.auditLogs, query: {
      if (q != null && q.isNotEmpty) 'q': q,
      if (action != null && action.isNotEmpty) 'action': action,
      if (status != null && status.isNotEmpty) 'status': status,
      'limit': limit,
      'offset': offset,
    });
    return AuditLogPage.from(r.data);
  }

  Future<List<NotificationLogItem>> notificationLogs({
    int? schoolId,
    String? status,
    int limit = 100,
  }) async {
    final r = await _client.get(Api.notificationLogs, query: {
      if (schoolId != null) 'school_id': schoolId,
      if (status != null && status.isNotEmpty) 'status': status,
      'limit': limit,
    });
    return asMapList(r.data).map(NotificationLogItem.fromJson).toList();
  }
}

final adminRepositoryProvider = Provider<AdminRepository>(
  (ref) => AdminRepository(ref.watch(dioClientProvider)),
);
