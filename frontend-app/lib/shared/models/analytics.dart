import '../utils/json.dart';
import 'attendance.dart';

class StudentSummary {
  const StudentSummary({
    this.studentName = '',
    this.studentId,
    this.totalEvents = 0,
    this.attendedEvents = 0,
    this.lateEvents = 0,
    this.incompleteEvents = 0,
    this.absentEvents = 0,
    this.excusedEvents = 0,
    this.attendanceRate = 0,
    this.lastAttendance,
  });

  final String studentName;
  final String? studentId;
  final int totalEvents;
  final int attendedEvents;
  final int lateEvents;
  final int incompleteEvents;
  final int absentEvents;
  final int excusedEvents;
  final double attendanceRate; // 0–100
  final DateTime? lastAttendance;

  factory StudentSummary.fromJson(Map<String, dynamic> j) => StudentSummary(
        studentName: asStr(j['student_name']) ?? '',
        studentId: asStr(j['student_id']),
        totalEvents: asInt(j['total_events']) ?? 0,
        attendedEvents: asInt(j['attended_events']) ?? 0,
        lateEvents: asInt(j['late_events']) ?? 0,
        incompleteEvents: asInt(j['incomplete_events']) ?? 0,
        absentEvents: asInt(j['absent_events']) ?? 0,
        excusedEvents: asInt(j['excused_events']) ?? 0,
        attendanceRate: asDouble(j['attendance_rate']) ?? 0,
        lastAttendance: asDate(j['last_attendance']),
      );
}

/// Full student attendance report (summary + history + breakdowns).
class StudentReport {
  const StudentReport({
    required this.summary,
    this.records = const [],
    this.monthly = const {},
    this.eventTypeStats = const {},
  });

  final StudentSummary summary;
  final List<AttendanceRecord> records;
  final Map<String, Map<String, int>> monthly;
  final Map<String, int> eventTypeStats;

  factory StudentReport.fromJson(Map<String, dynamic> j) {
    final records = j['attendance_records'] is List
        ? (j['attendance_records'] as List)
            .whereType<Map>()
            .map((e) => AttendanceRecord.fromJson(e.cast<String, dynamic>()))
            .toList()
        : <AttendanceRecord>[];

    final monthly = <String, Map<String, int>>{};
    final mj = j['monthly_stats'];
    if (mj is Map) {
      mj.forEach((k, v) {
        if (v is Map) {
          monthly[k.toString()] =
              v.map((kk, vv) => MapEntry(kk.toString(), asInt(vv) ?? 0));
        }
      });
    }

    final eventTypeStats = <String, int>{};
    final ej = j['event_type_stats'];
    if (ej is Map) {
      ej.forEach((k, v) => eventTypeStats[k.toString()] = asInt(v) ?? 0);
    }

    final s = j['student'];
    return StudentReport(
      summary: s is Map
          ? StudentSummary.fromJson(s.cast<String, dynamic>())
          : const StudentSummary(),
      records: records,
      monthly: monthly,
      eventTypeStats: eventTypeStats,
    );
  }
}
