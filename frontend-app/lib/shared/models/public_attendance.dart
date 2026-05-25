import '../utils/json.dart';

/// An event surfaced by the kiosk "nearby" discovery endpoint.
class NearbyEvent {
  const NearbyEvent({
    required this.id,
    required this.name,
    this.schoolName,
    this.location,
    this.startDatetime,
    this.endDatetime,
    this.geoRadiusM,
    this.distanceM,
    this.attendancePhase,
    this.phaseMessage,
    this.scopeLabel,
  });

  final int id;
  final String name;
  final String? schoolName;
  final String? location;
  final DateTime? startDatetime;
  final DateTime? endDatetime;
  final double? geoRadiusM;
  final double? distanceM;
  final String? attendancePhase; // sign_in | sign_out
  final String? phaseMessage;
  final String? scopeLabel;

  bool get isSignOut => attendancePhase == 'sign_out';

  factory NearbyEvent.fromJson(Map<String, dynamic> j) => NearbyEvent(
        id: asInt(j['id']) ?? 0,
        name: asStr(j['name']) ?? 'Event',
        schoolName: asStr(j['school_name']),
        location: asStr(j['location']),
        startDatetime: asDate(j['start_datetime']),
        endDatetime: asDate(j['end_datetime']),
        geoRadiusM: asDouble(j['geo_radius_m']),
        distanceM: asDouble(j['distance_m']),
        attendancePhase: asStr(j['attendance_phase']),
        phaseMessage: asStr(j['phase_message']),
        scopeLabel: asStr(j['scope_label']),
      );
}

/// One person's outcome within a multi-face scan.
class ScanOutcome {
  const ScanOutcome({
    required this.action,
    this.message = '',
    this.studentId,
    this.studentName,
    this.attendanceId,
  });

  final String action;
  final String message;
  final String? studentId;
  final String? studentName;
  final int? attendanceId;

  bool get isSuccess => action == 'time_in' || action == 'time_out';

  factory ScanOutcome.fromJson(Map<String, dynamic> j) => ScanOutcome(
        action: asStr(j['action']) ?? '',
        message: asStr(j['message']) ?? '',
        studentId: asStr(j['student_id']),
        studentName: asStr(j['student_name']),
        attendanceId: asInt(j['attendance_id']),
      );
}

class MultiScanResult {
  const MultiScanResult({
    required this.eventId,
    this.eventPhase,
    this.message = '',
    this.scanCooldownSeconds = 5,
    this.outcomes = const [],
  });

  final int eventId;
  final String? eventPhase;
  final String message;
  final int scanCooldownSeconds;
  final List<ScanOutcome> outcomes;

  factory MultiScanResult.fromJson(Map<String, dynamic> j) => MultiScanResult(
        eventId: asInt(j['event_id']) ?? 0,
        eventPhase: asStr(j['event_phase']),
        message: asStr(j['message']) ?? '',
        scanCooldownSeconds: asInt(j['scan_cooldown_seconds']) ?? 5,
        outcomes: asMapList(j['outcomes'])
            .map(ScanOutcome.fromJson)
            .toList(),
      );
}
