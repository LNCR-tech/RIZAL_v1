/// The four role-based surfaces of the app.
enum Workspace { student, schoolIt, admin, governance }

/// Role normalization + role→workspace mapping, ported from the web client
/// (`localAuth.js#normalizeRoleName` and `routeWorkspace.js`).
class Roles {
  Roles._();

  /// Lowercase, hyphenate, and fold the legacy `campus-admin` → `school-it`.
  static String normalize(String role) {
    final n = role.trim().toLowerCase().replaceAll('_', '-');
    return n == 'campus-admin' ? 'school-it' : n;
  }

  /// Accept `["student"]`, `[{name}]`, or `[{role:{name}}]` shapes.
  static List<String> normalizeList(dynamic roles) {
    if (roles is! List) return const [];
    return roles
        .map((r) {
          if (r is String) return r;
          if (r is Map) {
            final inner = r['role'];
            if (inner is Map && inner['name'] != null) {
              return inner['name'].toString();
            }
            return (r['name'] ?? '').toString();
          }
          return '';
        })
        .map((s) => s.trim())
        .where((s) => s.isNotEmpty)
        .toList();
  }

  static Set<String> _normalized(List<String> roles) =>
      roles.map(normalize).toSet();

  /// Initial workspace for a set of roles. Governance is usually layered on a
  /// student via membership (resolved later via API); a literal governance
  /// role is also honored here.
  static Workspace workspaceFor(List<String> roles) {
    final n = _normalized(roles);
    if (n.contains('admin')) return Workspace.admin;
    if (n.contains('school-it')) return Workspace.schoolIt;
    if (n.contains('governance') ||
        n.contains('sg') ||
        n.contains('ssg') ||
        n.contains('student-government')) {
      return Workspace.governance;
    }
    return Workspace.student;
  }

  static bool isPrivileged(List<String> roles) {
    final n = _normalized(roles);
    return n.contains('admin') || n.contains('school-it');
  }

  /// Privileged users (admin/school-it) whose session still owes a face check.
  static bool hasPrivilegedPendingFace({
    required List<String> roles,
    required String tokenType,
    required bool facePending,
    required bool faceRequired,
  }) {
    return isPrivileged(roles) &&
        (tokenType == 'face_pending' || facePending || faceRequired);
  }
}
