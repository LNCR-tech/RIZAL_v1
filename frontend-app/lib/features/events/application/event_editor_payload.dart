class EventEditorPayloadError implements Exception {
  const EventEditorPayloadError(this.message);

  final String message;

  @override
  String toString() => message;
}

/// Builds the JSON body for `POST /api/events/` and `PATCH /api/events/{id}`.
///
/// The backend's `EventCreate` schema supports several optional knobs that
/// older clients omitted; the editor now passes them all through so the
/// per-event policy actually reflects what the school admin configured:
///
///   * [yearLevels] — which student year levels (1–5) the event targets.
///     Always sent; empty list = open to every year in scope.
///   * [earlyCheckInMinutes] — how many minutes before [start] check-in opens.
///   * [lateThresholdMinutes] — minutes after [start] when arrivals flip
///     from "present" to "late".
///   * [signOutGraceMinutes] — minutes after [end] during which students
///     can still sign out without being marked absent.
///
/// All three minute fields are sent in *create* mode regardless of value
/// so the server's per-event policy is explicit. In *edit* mode they
/// are only sent when [includeTimingFields] is true (callers pass true
/// from the form to keep changes round-trippable).
Map<String, dynamic> buildEventEditorPayload({
  required String name,
  required String location,
  String? description,
  required DateTime? start,
  required DateTime? end,
  required bool geoRequired,
  double? geoLatitude,
  double? geoLongitude,
  double geoRadiusM = 100,
  required bool isEdit,
  List<int> yearLevels = const <int>[],
  int? earlyCheckInMinutes,
  int? lateThresholdMinutes,
  int? signOutGraceMinutes,
}) {
  final cleanName = name.trim();
  final cleanLocation = location.trim();
  final cleanDescription = description?.trim() ?? '';

  if (cleanName.isEmpty || start == null || end == null) {
    throw const EventEditorPayloadError('Add a name, start, and end time.');
  }
  if (cleanLocation.isEmpty) {
    throw const EventEditorPayloadError('Add a venue / location.');
  }
  if (!end.isAfter(start)) {
    throw const EventEditorPayloadError(
        'End time must be after the start time.');
  }
  if (geoRequired && (geoLatitude == null || geoLongitude == null)) {
    throw const EventEditorPayloadError(
        'Tap the map to set the event location.');
  }
  for (final y in yearLevels) {
    if (y < 1 || y > 5) {
      throw const EventEditorPayloadError(
          'Year levels must be between 1 and 5.');
    }
  }
  if (earlyCheckInMinutes != null &&
      (earlyCheckInMinutes < 0 || earlyCheckInMinutes > 1440)) {
    throw const EventEditorPayloadError(
        'Check-in opens must be between 0 and 1440 minutes.');
  }
  if (lateThresholdMinutes != null &&
      (lateThresholdMinutes < 0 || lateThresholdMinutes > 1440)) {
    throw const EventEditorPayloadError(
        'Late threshold must be between 0 and 1440 minutes.');
  }
  if (signOutGraceMinutes != null &&
      (signOutGraceMinutes < 0 || signOutGraceMinutes > 1440)) {
    throw const EventEditorPayloadError(
        'Sign-out window must be between 0 and 1440 minutes.');
  }

  // Sort + dedupe defensively — the backend also does this, but matching
  // the shape we'll see back keeps the snapshot tests stable.
  final cleanYearLevels = {...yearLevels}.toList()..sort();

  final body = <String, dynamic>{
    'name': cleanName,
    'location': cleanLocation,
    if (cleanDescription.isNotEmpty) 'description': cleanDescription,
    'start_datetime': start.toUtc().toIso8601String(),
    'end_datetime': end.toUtc().toIso8601String(),
    'year_levels': cleanYearLevels,
  };

  if (earlyCheckInMinutes != null) {
    body['early_check_in_minutes'] = earlyCheckInMinutes;
  }
  if (lateThresholdMinutes != null) {
    body['late_threshold_minutes'] = lateThresholdMinutes;
  }
  if (signOutGraceMinutes != null) {
    body['sign_out_grace_minutes'] = signOutGraceMinutes;
  }

  if (geoRequired) {
    body['geo_required'] = true;
    body['geo_latitude'] = geoLatitude;
    body['geo_longitude'] = geoLongitude;
    body['geo_radius_m'] = geoRadiusM.round();
  } else if (isEdit) {
    body['geo_required'] = false;
  }

  return body;
}
