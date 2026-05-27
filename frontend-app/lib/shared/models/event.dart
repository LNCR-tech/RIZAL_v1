import '../utils/json.dart';

/// An event/attendance session. Mirrors the backend `Event` schema
/// (note the field names `start_datetime`/`end_datetime`).
class AppEvent {
  const AppEvent({
    required this.id,
    required this.name,
    this.schoolId,
    this.location,
    this.description,
    this.venue,
    this.bannerUrl,
    this.geoLatitude,
    this.geoLongitude,
    this.geoRadiusM,
    this.geoRequired = false,
    this.geoMaxAccuracyM,
    this.earlyCheckInMinutes = 0,
    this.lateThresholdMinutes = 0,
    this.signOutGraceMinutes = 0,
    this.startDatetime,
    this.endDatetime,
    this.status = 'upcoming',
    this.eventTypeId,
    this.eventTypeName,
    this.departmentIds = const [],
    this.programIds = const [],
    this.governanceUnitId,
  });

  final int id;
  final String name;
  final int? schoolId;
  final String? location;
  final String? description;
  final String? venue;
  final String? bannerUrl;
  final double? geoLatitude;
  final double? geoLongitude;
  final double? geoRadiusM;
  final bool geoRequired;
  final double? geoMaxAccuracyM;
  final int earlyCheckInMinutes;
  final int lateThresholdMinutes;
  final int signOutGraceMinutes;
  final DateTime? startDatetime;
  final DateTime? endDatetime;
  final String status;
  final int? eventTypeId;
  final String? eventTypeName;
  final List<int> departmentIds;
  final List<int> programIds;
  final int? governanceUnitId;

  bool get hasGeo => geoLatitude != null && geoLongitude != null;
  bool get isOngoing => status.toLowerCase() == 'ongoing';
  bool get isUpcoming => status.toLowerCase() == 'upcoming';
  bool get isCompleted => status.toLowerCase() == 'completed';
  bool get isCancelled => status.toLowerCase() == 'cancelled';

  factory AppEvent.fromJson(Map<String, dynamic> j) {
    List<int> ids(dynamic v) =>
        v is List ? v.map(asInt).whereType<int>().toList() : const [];
    final eventType = j['event_type'];
    return AppEvent(
      id: asInt(j['id']) ?? 0,
      name: asStr(j['name']) ?? 'Untitled event',
      schoolId: asInt(j['school_id']),
      location: asStr(j['location']) ?? asStr(j['venue']),
      description: asStr(j['description']),
      venue: asStr(j['venue']),
      bannerUrl: asStr(j['banner_url']),
      geoLatitude: asDouble(j['geo_latitude']),
      geoLongitude: asDouble(j['geo_longitude']),
      geoRadiusM: asDouble(j['geo_radius_m']),
      geoRequired: asBool(j['geo_required']),
      geoMaxAccuracyM: asDouble(j['geo_max_accuracy_m']),
      earlyCheckInMinutes: asInt(j['early_check_in_minutes']) ?? 0,
      lateThresholdMinutes: asInt(j['late_threshold_minutes']) ?? 0,
      signOutGraceMinutes: asInt(j['sign_out_grace_minutes']) ?? 0,
      startDatetime: asDate(j['start_datetime']),
      endDatetime: asDate(j['end_datetime']),
      status: asStr(j['status']) ?? 'upcoming',
      eventTypeId: asInt(j['event_type_id']),
      eventTypeName: eventType is Map ? asStr(eventType['name']) : null,
      departmentIds: ids(j['department_ids']),
      programIds: ids(j['program_ids']),
      governanceUnitId: asInt(j['governance_unit_id']),
    );
  }
}

/// Live timing/state for an event (from `/events/{id}/time-status`).
class EventTimeStatus {
  const EventTimeStatus({
    required this.eventStatus,
    this.currentTime,
    this.checkInOpensAt,
    this.startTime,
    this.endTime,
    this.lateThresholdTime,
    this.attendanceOverrideActive = false,
    this.signOutOpensAt,
    this.effectiveSignOutClosesAt,
    this.timezoneName,
  });

  final String eventStatus;
  final DateTime? currentTime;
  final DateTime? checkInOpensAt;
  final DateTime? startTime;
  final DateTime? endTime;
  final DateTime? lateThresholdTime;
  final bool attendanceOverrideActive;
  final DateTime? signOutOpensAt;
  final DateTime? effectiveSignOutClosesAt;
  final String? timezoneName;

  bool get checkInOpen =>
      const {'early_check_in', 'late_check_in'}.contains(eventStatus);
  bool get signOutOpen => eventStatus == 'sign_out_open';
  bool get isClosed => eventStatus == 'closed';

  factory EventTimeStatus.fromJson(Map<String, dynamic> j) => EventTimeStatus(
        eventStatus: asStr(j['event_status']) ?? 'closed',
        currentTime: asDate(j['current_time']),
        checkInOpensAt: asDate(j['check_in_opens_at']),
        startTime: asDate(j['start_time']),
        endTime: asDate(j['end_time']),
        lateThresholdTime: asDate(j['late_threshold_time']),
        attendanceOverrideActive: asBool(j['attendance_override_active']),
        signOutOpensAt: asDate(j['sign_out_opens_at']),
        effectiveSignOutClosesAt: asDate(j['effective_sign_out_closes_at']),
        timezoneName: asStr(j['timezone_name']),
      );
}
