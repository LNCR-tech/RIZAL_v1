import '../utils/json.dart';
import 'school.dart';

class SchoolSummary {
  const SchoolSummary({
    required this.schoolId,
    this.schoolName,
    this.schoolCode,
    this.subscriptionStatus,
    this.activeStatus = true,
    this.createdAt,
  });
  final int schoolId;
  final String? schoolName;
  final String? schoolCode;
  final String? subscriptionStatus;
  final bool activeStatus;
  final DateTime? createdAt;

  factory SchoolSummary.fromJson(Map<String, dynamic> j) => SchoolSummary(
        schoolId: asInt(j['school_id']) ?? 0,
        schoolName: asStr(j['school_name']),
        schoolCode: asStr(j['school_code']),
        subscriptionStatus: asStr(j['subscription_status']),
        activeStatus: j['active_status'] == null ? true : asBool(j['active_status']),
        createdAt: asDate(j['created_at']),
      );
}

class SchoolItAccount {
  const SchoolItAccount({
    required this.userId,
    this.email,
    this.firstName,
    this.lastName,
    this.schoolId,
    this.schoolName,
    this.isActive = true,
  });
  final int userId;
  final String? email;
  final String? firstName;
  final String? lastName;
  final int? schoolId;
  final String? schoolName;
  final bool isActive;

  String get displayName {
    final n = [firstName, lastName]
        .where((e) => e != null && e.trim().isNotEmpty)
        .join(' ')
        .trim();
    return n.isNotEmpty ? n : (email ?? 'Account');
  }

  factory SchoolItAccount.fromJson(Map<String, dynamic> j) => SchoolItAccount(
        userId: asInt(j['user_id']) ?? asInt(j['id']) ?? 0,
        email: asStr(j['email']),
        firstName: asStr(j['first_name']),
        lastName: asStr(j['last_name']),
        schoolId: asInt(j['school_id']),
        schoolName: asStr(j['school_name']),
        isActive: j['is_active'] == null ? true : asBool(j['is_active']),
      );
}

class PasswordResetRequest {
  const PasswordResetRequest({
    required this.id,
    this.userId,
    this.email,
    this.firstName,
    this.lastName,
    this.roles = const [],
    this.status = 'pending',
    this.requestedAt,
  });
  final int id;
  final int? userId;
  final String? email;
  final String? firstName;
  final String? lastName;
  final List<String> roles;
  final String status;
  final DateTime? requestedAt;

  String get displayName {
    final n = [firstName, lastName]
        .where((e) => e != null && e.trim().isNotEmpty)
        .join(' ')
        .trim();
    return n.isNotEmpty ? n : (email ?? 'User');
  }

  factory PasswordResetRequest.fromJson(Map<String, dynamic> j) =>
      PasswordResetRequest(
        id: asInt(j['id']) ?? 0,
        userId: asInt(j['user_id']),
        email: asStr(j['email']),
        firstName: asStr(j['first_name']),
        lastName: asStr(j['last_name']),
        roles: j['roles'] is List
            ? (j['roles'] as List).map((e) => e.toString()).toList()
            : const [],
        status: asStr(j['status']) ?? 'pending',
        requestedAt: asDate(j['requested_at']),
      );
}

class CreateSchoolResult {
  const CreateSchoolResult({
    required this.school,
    this.schoolItUserId,
    this.schoolItEmail,
    this.generatedTemporaryPassword,
  });
  final SchoolBranding school;
  final int? schoolItUserId;
  final String? schoolItEmail;
  final String? generatedTemporaryPassword;

  factory CreateSchoolResult.fromJson(Map<String, dynamic> j) {
    final s = j['school'];
    return CreateSchoolResult(
      school: s is Map
          ? SchoolBranding.fromJson(s.cast<String, dynamic>())
          : const SchoolBranding(),
      schoolItUserId: asInt(j['school_it_user_id']),
      schoolItEmail: asStr(j['school_it_email']),
      generatedTemporaryPassword: asStr(j['generated_temporary_password']),
    );
  }
}
