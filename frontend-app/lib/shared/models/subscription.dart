import '../utils/json.dart';

/// A school's subscription / plan (the lever that gates capabilities).
class SchoolSubscription {
  const SchoolSubscription({
    this.schoolId,
    this.planName,
    this.userLimit,
    this.eventLimitMonthly,
    this.importLimitMonthly,
    this.renewalDate,
    this.autoRenew = false,
    this.reminderDaysBefore,
    this.metrics = const {},
  });
  final int? schoolId;
  final String? planName;
  final int? userLimit;
  final int? eventLimitMonthly;
  final int? importLimitMonthly;
  final DateTime? renewalDate;
  final bool autoRenew;
  final int? reminderDaysBefore;
  final Map<String, dynamic> metrics;

  factory SchoolSubscription.fromJson(Map<String, dynamic> j) =>
      SchoolSubscription(
        schoolId: asInt(j['school_id']),
        planName: asStr(j['plan_name']),
        userLimit: asInt(j['user_limit']),
        eventLimitMonthly: asInt(j['event_limit_monthly']),
        importLimitMonthly: asInt(j['import_limit_monthly']),
        renewalDate: asDate(j['renewal_date']),
        autoRenew: j['auto_renew'] == null ? false : asBool(j['auto_renew']),
        reminderDaysBefore: asInt(j['reminder_days_before']),
        metrics: j['metrics'] is Map
            ? (j['metrics'] as Map).cast<String, dynamic>()
            : const {},
      );
}
