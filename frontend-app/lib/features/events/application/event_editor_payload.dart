class EventEditorPayloadError implements Exception {
  const EventEditorPayloadError(this.message);

  final String message;

  @override
  String toString() => message;
}

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

  final body = <String, dynamic>{
    'name': cleanName,
    'location': cleanLocation,
    if (cleanDescription.isNotEmpty) 'description': cleanDescription,
    'start_datetime': start.toUtc().toIso8601String(),
    'end_datetime': end.toUtc().toIso8601String(),
  };

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
