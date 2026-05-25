import '../utils/json.dart';

class Department {
  const Department({required this.id, this.schoolId, this.name = ''});
  final int id;
  final int? schoolId;
  final String name;

  factory Department.fromJson(Map<String, dynamic> j) => Department(
        id: asInt(j['id']) ?? 0,
        schoolId: asInt(j['school_id']),
        name: asStr(j['name']) ?? 'Department',
      );
}

class Program {
  const Program({
    required this.id,
    this.schoolId,
    this.name = '',
    this.departmentIds = const [],
  });
  final int id;
  final int? schoolId;
  final String name;
  final List<int> departmentIds;

  factory Program.fromJson(Map<String, dynamic> j) {
    final ids = j['department_ids'] is List
        ? (j['department_ids'] as List).map(asInt).whereType<int>().toList()
        : const <int>[];
    return Program(
      id: asInt(j['id']) ?? 0,
      schoolId: asInt(j['school_id']),
      name: asStr(j['name']) ?? 'Program',
      departmentIds: ids,
    );
  }
}

/// School info + branding + default event policy (`/school/me`).
class SchoolBranding {
  const SchoolBranding({
    this.schoolId,
    this.schoolName,
    this.schoolCode,
    this.logoUrl,
    this.primaryColor,
    this.secondaryColor,
    this.earlyCheckInMinutes = 0,
    this.lateThresholdMinutes = 0,
    this.signOutGraceMinutes = 0,
    this.subscriptionStatus,
    this.activeStatus = true,
  });
  final int? schoolId;
  final String? schoolName;
  final String? schoolCode;
  final String? logoUrl;
  final String? primaryColor;
  final String? secondaryColor;
  final int earlyCheckInMinutes;
  final int lateThresholdMinutes;
  final int signOutGraceMinutes;
  final String? subscriptionStatus;
  final bool activeStatus;

  factory SchoolBranding.fromJson(Map<String, dynamic> j) => SchoolBranding(
        schoolId: asInt(j['school_id']),
        schoolName: asStr(j['school_name']),
        schoolCode: asStr(j['school_code']),
        logoUrl: asStr(j['logo_url']),
        primaryColor: asStr(j['primary_color']),
        secondaryColor: asStr(j['secondary_color']),
        earlyCheckInMinutes:
            asInt(j['event_default_early_check_in_minutes']) ?? 0,
        lateThresholdMinutes:
            asInt(j['event_default_late_threshold_minutes']) ?? 0,
        signOutGraceMinutes:
            asInt(j['event_default_sign_out_grace_minutes']) ?? 0,
        subscriptionStatus: asStr(j['subscription_status']),
        activeStatus: j['active_status'] == null
            ? true
            : asBool(j['active_status']),
      );
}
