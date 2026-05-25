import '../utils/json.dart';

class SanctionStudent {
  const SanctionStudent({
    this.userId,
    this.studentProfileId,
    this.studentId,
    this.firstName,
    this.lastName,
    this.programName,
    this.departmentName,
    this.yearLevel,
  });
  final int? userId;
  final int? studentProfileId;
  final String? studentId;
  final String? firstName;
  final String? lastName;
  final String? programName;
  final String? departmentName;
  final int? yearLevel;

  String get displayName {
    final n = [firstName, lastName]
        .where((e) => e != null && e.trim().isNotEmpty)
        .join(' ')
        .trim();
    return n.isNotEmpty ? n : (studentId ?? 'Student');
  }

  factory SanctionStudent.fromJson(Map<String, dynamic> j) => SanctionStudent(
        userId: asInt(j['user_id']),
        studentProfileId: asInt(j['student_profile_id']),
        studentId: asStr(j['student_id']),
        firstName: asStr(j['first_name']),
        lastName: asStr(j['last_name']),
        programName: asStr(j['program_name']),
        departmentName: asStr(j['department_name']),
        yearLevel: asInt(j['year_level']),
      );
}

class SanctionItem {
  const SanctionItem({
    required this.id,
    this.itemName = '',
    this.itemDescription,
    this.status = 'pending',
    this.compliedAt,
  });
  final int id;
  final String itemName;
  final String? itemDescription;
  final String status; // pending | complied | excused | waived
  final DateTime? compliedAt;

  factory SanctionItem.fromJson(Map<String, dynamic> j) => SanctionItem(
        id: asInt(j['id']) ?? 0,
        itemName: asStr(j['item_name']) ?? '',
        itemDescription: asStr(j['item_description']),
        status: asStr(j['status']) ?? 'pending',
        compliedAt: asDate(j['complied_at']),
      );
}

class SanctionRecord {
  const SanctionRecord({
    required this.id,
    this.eventId,
    this.status = 'pending',
    this.student,
    this.items = const [],
    this.compliedAt,
  });
  final int id;
  final int? eventId;
  final String status; // pending | approved | complied | rejected
  final SanctionStudent? student;
  final List<SanctionItem> items;
  final DateTime? compliedAt;

  factory SanctionRecord.fromJson(Map<String, dynamic> j) {
    final s = j['student'];
    return SanctionRecord(
      id: asInt(j['id']) ?? 0,
      eventId: asInt(j['event_id']),
      status: asStr(j['status']) ?? 'pending',
      student:
          s is Map ? SanctionStudent.fromJson(s.cast<String, dynamic>()) : null,
      items: asMapList(j['items']).map(SanctionItem.fromJson).toList(),
      compliedAt: asDate(j['complied_at']),
    );
  }
}

class PaginatedSanctions {
  const PaginatedSanctions({this.total = 0, this.items = const []});
  final int total;
  final List<SanctionRecord> items;

  factory PaginatedSanctions.fromJson(Map<String, dynamic> j) =>
      PaginatedSanctions(
        total: asInt(j['total']) ?? 0,
        items: asMapList(j['items']).map(SanctionRecord.fromJson).toList(),
      );
}

class SanctionEventRow {
  const SanctionEventRow({
    required this.eventId,
    this.eventName = '',
    this.ownerLevel,
    this.participantCount = 0,
    this.absentCount = 0,
    this.pendingSanctions = 0,
    this.compliedSanctions = 0,
    this.absenceRatePercent = 0,
  });
  final int eventId;
  final String eventName;
  final String? ownerLevel;
  final int participantCount;
  final int absentCount;
  final int pendingSanctions;
  final int compliedSanctions;
  final double absenceRatePercent;

  factory SanctionEventRow.fromJson(Map<String, dynamic> j) => SanctionEventRow(
        eventId: asInt(j['event_id']) ?? 0,
        eventName: asStr(j['event_name']) ?? 'Event',
        ownerLevel: asStr(j['owner_level']),
        participantCount: asInt(j['participant_count']) ?? 0,
        absentCount: asInt(j['absent_count']) ?? 0,
        pendingSanctions: asInt(j['pending_sanctions']) ?? 0,
        compliedSanctions: asInt(j['complied_sanctions']) ?? 0,
        absenceRatePercent: asDouble(j['absence_rate_percent']) ?? 0,
      );
}

class SanctionsDashboard {
  const SanctionsDashboard({
    this.totalEvents = 0,
    this.totalParticipants = 0,
    this.totalAbsent = 0,
    this.totalPending = 0,
    this.totalComplied = 0,
    this.overallAbsenceRate = 0,
    this.events = const [],
  });
  final int totalEvents;
  final int totalParticipants;
  final int totalAbsent;
  final int totalPending;
  final int totalComplied;
  final double overallAbsenceRate;
  final List<SanctionEventRow> events;

  factory SanctionsDashboard.fromJson(Map<String, dynamic> j) =>
      SanctionsDashboard(
        totalEvents: asInt(j['total_events']) ?? 0,
        totalParticipants: asInt(j['total_participants']) ?? 0,
        totalAbsent: asInt(j['total_absent']) ?? 0,
        totalPending: asInt(j['total_pending_sanctions']) ?? 0,
        totalComplied: asInt(j['total_complied_sanctions']) ?? 0,
        overallAbsenceRate: asDouble(j['overall_absence_rate_percent']) ?? 0,
        events: asMapList(j['events']).map(SanctionEventRow.fromJson).toList(),
      );
}
