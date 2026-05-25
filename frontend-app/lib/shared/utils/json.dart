// Lenient JSON field coercion helpers shared by all model `fromJson`s.
// The backend mixes numeric/string types and ISO-8601 datetimes with offsets.

int? asInt(dynamic v) =>
    v is num ? v.toInt() : (v is String ? int.tryParse(v) : null);

double? asDouble(dynamic v) =>
    v is num ? v.toDouble() : (v is String ? double.tryParse(v) : null);

bool asBool(dynamic v) => v == true || v == 'true' || v == 1;

String? asStr(dynamic v) {
  final s = v?.toString().trim();
  return (s == null || s.isEmpty) ? null : s;
}

/// Parse an ISO-8601 datetime (with `+08:00`/`Z`) into local time.
DateTime? asDate(dynamic v) {
  if (v == null) return null;
  if (v is DateTime) return v.toLocal();
  return DateTime.tryParse(v.toString())?.toLocal();
}

/// Coerce a dynamic into a `List<Map<String, dynamic>>`, dropping non-maps.
List<Map<String, dynamic>> asMapList(dynamic v) => v is List
    ? v.whereType<Map>().map((e) => e.cast<String, dynamic>()).toList()
    : const [];
