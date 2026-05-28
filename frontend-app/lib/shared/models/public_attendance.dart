import 'package:flutter/material.dart';

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
    this.effectiveDistanceM,
    this.accuracyM,
    this.attendancePhase,
    this.phaseMessage,
    this.scopeLabel,
    this.departments = const [],
    this.programs = const [],
  });

  final int id;
  final String name;
  final String? schoolName;
  final String? location;
  final DateTime? startDatetime;
  final DateTime? endDatetime;
  final double? geoRadiusM;
  final double? distanceM;
  final double? effectiveDistanceM;
  final double? accuracyM;
  final String? attendancePhase; // sign_in | sign_out | null (closed)
  final String? phaseMessage;
  final String? scopeLabel;
  final List<String> departments;
  final List<String> programs;

  bool get isSignOut => attendancePhase == 'sign_out';
  bool get isSignIn => attendancePhase == 'sign_in';
  bool get isOpen => isSignIn || isSignOut;

  /// "Sign-in", "Sign-out", or "Closed".
  String get phaseLabel => switch (attendancePhase) {
        'sign_in' => 'Sign-in',
        'sign_out' => 'Sign-out',
        _ => 'Closed',
      };

  /// Whether the device coordinates are inside the event geofence (best-effort
  /// using `distance ≤ radius`; server runs a stricter check on scan).
  bool get insideGeofence {
    final r = geoRadiusM;
    final d = effectiveDistanceM ?? distanceM;
    if (r == null || d == null) return false;
    return d <= r;
  }

  factory NearbyEvent.fromJson(Map<String, dynamic> j) => NearbyEvent(
        id: asInt(j['id']) ?? 0,
        name: asStr(j['name']) ?? 'Event',
        schoolName: asStr(j['school_name']),
        location: asStr(j['location']),
        startDatetime: asDate(j['start_datetime']),
        endDatetime: asDate(j['end_datetime']),
        geoRadiusM: asDouble(j['geo_radius_m']),
        distanceM: asDouble(j['distance_m']),
        effectiveDistanceM: asDouble(j['effective_distance_m']),
        accuracyM: asDouble(j['accuracy_m']),
        attendancePhase: asStr(j['attendance_phase']),
        phaseMessage: asStr(j['phase_message']),
        scopeLabel: asStr(j['scope_label']),
        departments: asStrList(j['departments']),
        programs: asStrList(j['programs']),
      );
}

/// Anti-spoof verdict for one face.
class Liveness {
  const Liveness({required this.label, this.score, this.reason});

  /// "Real" | "Fake" | "Bypassed".
  final String label;

  /// Anti-spoof score in `[0, 1]`. Higher is more likely to be real.
  final double? score;

  /// Optional human reason (e.g. "model_unavailable" when bypassed).
  final String? reason;

  bool get isReal => label == 'Real';
  bool get isFake => label == 'Fake';
  bool get isBypassed => label == 'Bypassed';

  factory Liveness.fromJson(Map<String, dynamic> j) => Liveness(
        label: asStr(j['label']) ?? 'Bypassed',
        score: asDouble(j['score']),
        reason: asStr(j['reason']),
      );
}

/// Geolocation verification block on a multi-scan response.
class GeoStatus {
  const GeoStatus({
    required this.ok,
    this.reason,
    this.distanceM,
    this.effectiveDistanceM,
    this.radiusM,
    this.accuracyM,
  });

  final bool ok;
  final String? reason; // "outside_geofence", "accuracy_too_poor", etc.
  final double? distanceM;
  final double? effectiveDistanceM;
  final double? radiusM;
  final double? accuracyM;

  factory GeoStatus.fromJson(Map<String, dynamic> j) => GeoStatus(
        ok: asBool(j['ok']),
        reason: asStr(j['reason']),
        distanceM: asDouble(j['distance_m']),
        effectiveDistanceM: asDouble(j['effective_distance_m']),
        radiusM: asDouble(j['radius_m']),
        accuracyM: asDouble(j['accuracy_m']),
      );
}

/// One person's outcome within a multi-face scan.
class ScanOutcome {
  const ScanOutcome({
    required this.action,
    this.reasonCode,
    this.message = '',
    this.studentId,
    this.studentName,
    this.attendanceId,
    this.distance,
    this.confidence,
    this.threshold,
    this.liveness,
    this.timeIn,
    this.timeOut,
    this.durationMinutes,
  });

  /// One of: `time_in`, `time_out`, `already_signed_in`, `already_signed_out`,
  /// `rejected`, `out_of_scope`, `no_match`, `liveness_failed`, `duplicate_face`,
  /// `cooldown_skipped`.
  final String action;

  /// Backend reason code (e.g. `spoof_detected`, `student_not_in_event_scope`).
  final String? reasonCode;

  final String message;
  final String? studentId;
  final String? studentName;
  final int? attendanceId;

  /// L2 distance in `[0, 2]` (normalized embeddings); null when no match was
  /// attempted or returned.
  final double? distance;

  /// `1.0 - distance`, surfaced so the UI doesn't have to derive it.
  final double? confidence;

  /// Threshold used for this match (server- or request-overridable).
  final double? threshold;

  final Liveness? liveness;
  final DateTime? timeIn;
  final DateTime? timeOut;
  final int? durationMinutes;

  bool get isSuccess => action == 'time_in' || action == 'time_out';
  bool get isSignIn => action == 'time_in';
  bool get isSignOut => action == 'time_out';
  bool get isAlreadyRecorded =>
      action == 'already_signed_in' || action == 'already_signed_out';
  bool get isLivenessFailed => action == 'liveness_failed';
  bool get isOutOfScope => action == 'out_of_scope';
  bool get isNoMatch => action == 'no_match';
  bool get isDuplicate => action == 'duplicate_face';
  bool get isCooldownSkipped => action == 'cooldown_skipped';
  bool get isRejected => action == 'rejected';

  /// True for hard, visible failures the operator should see (spoof, no match,
  /// out of scope, generic reject). Not duplicates or cooldown (those are
  /// noise from the scan loop, not user-facing problems).
  bool get isHardFailure =>
      isLivenessFailed || isNoMatch || isOutOfScope || isRejected;

  /// Best display name fallback.
  String get displayName => studentName ?? studentId ?? 'Unknown person';

  /// Short human label for the action.
  String get actionLabel => switch (action) {
        'time_in' => 'Checked in',
        'time_out' => 'Signed out',
        'already_signed_in' => 'Already checked in',
        'already_signed_out' => 'Already signed out',
        'liveness_failed' => 'Liveness failed',
        'out_of_scope' => 'Outside event scope',
        'no_match' => 'No match',
        'duplicate_face' => 'Duplicate in frame',
        'cooldown_skipped' => 'Cooldown',
        'rejected' => 'Rejected',
        _ => action.replaceAll('_', ' '),
      };

  factory ScanOutcome.fromJson(Map<String, dynamic> j) => ScanOutcome(
        action: asStr(j['action']) ?? '',
        reasonCode: asStr(j['reason_code']),
        message: asStr(j['message']) ?? '',
        studentId: asStr(j['student_id']),
        studentName: asStr(j['student_name']),
        attendanceId: asInt(j['attendance_id']),
        distance: asDouble(j['distance']),
        confidence: asDouble(j['confidence']),
        threshold: asDouble(j['threshold']),
        liveness: j['liveness'] is Map
            ? Liveness.fromJson(
                (j['liveness'] as Map).cast<String, dynamic>())
            : null,
        timeIn: asDate(j['time_in']),
        timeOut: asDate(j['time_out']),
        durationMinutes: asInt(j['duration_minutes']),
      );
}

/// Surface-level colour intent for a [ScanOutcome] — kept here (not in a
/// widget) so the same mapping is reused by the live status chip, outcome
/// tiles, the session summary, and any future surfaces.
enum OutcomeIntent { success, info, warning, danger, neutral }

extension ScanOutcomeIntent on ScanOutcome {
  OutcomeIntent get intent {
    if (isSuccess) return OutcomeIntent.success;
    if (isLivenessFailed || isRejected) return OutcomeIntent.danger;
    if (isOutOfScope || isNoMatch) return OutcomeIntent.warning;
    if (isAlreadyRecorded) return OutcomeIntent.info;
    return OutcomeIntent.neutral;
  }

  IconData get icon => switch (action) {
        'time_in' => Icons.check_circle_rounded,
        'time_out' => Icons.logout_rounded,
        'already_signed_in' => Icons.task_alt_rounded,
        'already_signed_out' => Icons.task_alt_rounded,
        'liveness_failed' => Icons.gpp_bad_rounded,
        'out_of_scope' => Icons.do_not_disturb_on_rounded,
        'no_match' => Icons.help_outline_rounded,
        'duplicate_face' => Icons.filter_2_rounded,
        'cooldown_skipped' => Icons.av_timer_rounded,
        'rejected' => Icons.block_rounded,
        _ => Icons.info_outline_rounded,
      };
}

class MultiScanResult {
  const MultiScanResult({
    required this.eventId,
    this.eventPhase,
    this.message = '',
    this.scanCooldownSeconds = 5,
    this.outcomes = const [],
    this.geo,
  });

  final int eventId;
  final String? eventPhase;
  final String message;
  final int scanCooldownSeconds;
  final List<ScanOutcome> outcomes;
  final GeoStatus? geo;

  factory MultiScanResult.fromJson(Map<String, dynamic> j) => MultiScanResult(
        eventId: asInt(j['event_id']) ?? 0,
        eventPhase: asStr(j['event_phase']),
        message: asStr(j['message']) ?? '',
        scanCooldownSeconds: asInt(j['scan_cooldown_seconds']) ?? 5,
        outcomes:
            asMapList(j['outcomes']).map(ScanOutcome.fromJson).toList(),
        geo: j['geo'] is Map
            ? GeoStatus.fromJson((j['geo'] as Map).cast<String, dynamic>())
            : null,
      );
}
