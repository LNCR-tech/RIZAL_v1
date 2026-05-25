import '../utils/json.dart';

class Liveness {
  const Liveness({this.label, this.score, this.reason});
  final String? label;
  final double? score;
  final String? reason;

  bool get isLive {
    final l = (label ?? '').toLowerCase();
    return l == 'live' || l == 'bypassed';
  }

  factory Liveness.fromJson(Map<String, dynamic> j) => Liveness(
        label: asStr(j['label']),
        score: asDouble(j['score']),
        reason: asStr(j['reason']),
      );
}

class GeoVerification {
  const GeoVerification({
    this.ok = false,
    this.reason,
    this.distanceM,
    this.effectiveDistanceM,
    this.radiusM,
    this.accuracyM,
  });
  final bool ok;
  final String? reason;
  final double? distanceM;
  final double? effectiveDistanceM;
  final double? radiusM;
  final double? accuracyM;

  factory GeoVerification.fromJson(Map<String, dynamic> j) => GeoVerification(
        ok: asBool(j['ok']),
        reason: asStr(j['reason']),
        distanceM: asDouble(j['distance_m']),
        effectiveDistanceM: asDouble(j['effective_distance_m']),
        radiusM: asDouble(j['radius_m']),
        accuracyM: asDouble(j['accuracy_m']),
      );
}

/// Result of a self-scan check-in/out (`/face/face-scan-with-recognition`).
class FaceScanResult {
  const FaceScanResult({
    required this.action,
    this.studentId,
    this.studentName,
    this.attendanceId,
    this.distance,
    this.confidence,
    this.threshold,
    this.liveness,
    this.geo,
    this.timeIn,
    this.timeOut,
    this.durationMinutes,
    this.message,
  });

  final String action; // time_in | timeout
  final String? studentId;
  final String? studentName;
  final int? attendanceId;
  final double? distance;
  final double? confidence;
  final double? threshold;
  final Liveness? liveness;
  final GeoVerification? geo;
  final DateTime? timeIn;
  final DateTime? timeOut;
  final int? durationMinutes;
  final String? message;

  bool get isTimeIn => action == 'time_in';
  bool get isTimeOut => action == 'timeout' || action == 'time_out';

  factory FaceScanResult.fromJson(Map<String, dynamic> j) {
    final liv = j['liveness'];
    final geo = j['geo'];
    return FaceScanResult(
      action: asStr(j['action']) ?? '',
      studentId: asStr(j['student_id']),
      studentName: asStr(j['student_name']),
      attendanceId: asInt(j['attendance_id']),
      distance: asDouble(j['distance']),
      confidence: asDouble(j['confidence']),
      threshold: asDouble(j['threshold']),
      liveness: liv is Map ? Liveness.fromJson(liv.cast<String, dynamic>()) : null,
      geo: geo is Map ? GeoVerification.fromJson(geo.cast<String, dynamic>()) : null,
      timeIn: asDate(j['time_in']),
      timeOut: asDate(j['time_out']),
      durationMinutes: asInt(j['duration_minutes']),
      message: asStr(j['message']),
    );
  }
}

/// An attendance record. Report records carry extra event fields, all optional.
class AttendanceRecord {
  const AttendanceRecord({
    required this.id,
    this.studentId,
    this.eventId,
    this.eventName,
    this.eventLocation,
    this.eventDate,
    this.timeIn,
    this.timeOut,
    this.method,
    this.status = '',
    this.displayStatus,
    this.checkInStatus,
    this.checkOutStatus,
    this.completionState,
    this.isValidAttendance = false,
    this.durationMinutes,
    this.notes,
  });

  final int id;
  final int? studentId;
  final int? eventId;
  final String? eventName;
  final String? eventLocation;
  final DateTime? eventDate;
  final DateTime? timeIn;
  final DateTime? timeOut;
  final String? method;
  final String status;
  final String? displayStatus;
  final String? checkInStatus;
  final String? checkOutStatus;
  final String? completionState;
  final bool isValidAttendance;
  final int? durationMinutes;
  final String? notes;

  String get effectiveStatus => displayStatus ?? status;
  bool get isComplete => completionState == 'completed';

  factory AttendanceRecord.fromJson(Map<String, dynamic> j) => AttendanceRecord(
        id: asInt(j['id']) ?? 0,
        studentId: asInt(j['student_id']),
        eventId: asInt(j['event_id']),
        eventName: asStr(j['event_name']),
        eventLocation: asStr(j['event_location']),
        eventDate: asDate(j['event_date']),
        timeIn: asDate(j['time_in']),
        timeOut: asDate(j['time_out']),
        method: asStr(j['method']),
        status: asStr(j['status']) ?? '',
        displayStatus: asStr(j['display_status']),
        checkInStatus: asStr(j['check_in_status']),
        checkOutStatus: asStr(j['check_out_status']),
        completionState: asStr(j['completion_state']),
        isValidAttendance: asBool(j['is_valid_attendance']),
        durationMinutes: asInt(j['duration_minutes']),
        notes: asStr(j['notes']),
      );
}
