import '../config/app_config.dart';
import 'base_url.dart';

/// Resolves a possibly-relative media path to an absolute URL against the
/// backend root. The backend returns school `logo_url` as a relative path
/// (e.g. `/school-logos/abc.png`), so callers that render it directly must
/// resolve it first. Returns null for empty input.
String? mediaUrl(String? raw) {
  if (raw == null) return null;
  final s = raw.trim();
  if (s.isEmpty) return null;
  if (s.startsWith('http://') || s.startsWith('https://')) return s;
  final root = BackendBaseUrl.normalize(AppConfig.apiBaseUrl);
  if (root.isEmpty) return null;
  return s.startsWith('/') ? '$root$s' : '$root/$s';
}
