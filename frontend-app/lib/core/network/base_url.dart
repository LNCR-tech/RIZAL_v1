/// Backend root URL normalization — ported from
/// `frontend-web/src/services/backendBaseUrl.js`.
class BackendBaseUrl {
  BackendBaseUrl._();

  /// Trim trailing slashes and drop a trailing `/api`, so callers may pass
  /// either the bare origin (`https://api.host`) or an `.../api` URL. Returns
  /// the backend ROOT; request paths then carry `/api/v1/...` or `/token`.
  static String normalize(String value) {
    final v = value.trim().replaceAll(RegExp(r'/+$'), '');
    if (v.isEmpty) return v;

    final uri = Uri.tryParse(v);
    if (uri != null && uri.hasScheme && uri.host.isNotEmpty) {
      final path = uri.path == '/api' ? '' : uri.path;
      return uri.replace(path: path).toString().replaceAll(RegExp(r'/+$'), '');
    }

    if (v == '/api') return '';
    if (v.endsWith('/api')) return v.substring(0, v.length - '/api'.length);
    return v;
  }
}
