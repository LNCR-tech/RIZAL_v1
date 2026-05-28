import '../../../shared/models/profile.dart';

/// Pure-Dart, immutable filter state for the schoolit "Users" surface.
///
/// Composes a free-text query with four orthogonal predicates
/// (programs, year levels, statuses, face-enrolled-only). All predicates
/// are joined with **AND**: a student passes only if they match every
/// active filter. Empty sets / blank query are treated as "no constraint
/// on this axis".
///
/// Pure-Dart on purpose — no Flutter widget imports — so the contract is
/// unit-testable without a binding.
class StudentFilter {
  const StudentFilter({
    this.query = '',
    this.programIds = const <int>{},
    this.yearLevels = const <int>{},
    this.statuses = const <String>{},
    this.faceEnrolledOnly = false,
  });

  /// Free-text search across `displayName`, `email`, and `studentNumber`
  /// (case-insensitive, trimmed). Empty / whitespace-only means "any".
  final String query;

  /// Selected program ids. Empty means "any program". A student matches
  /// when their `student_profile.program_id` is in this set.
  final Set<int> programIds;

  /// Selected year levels (1–5). Empty means "any year".
  final Set<int> yearLevels;

  /// Selected status strings (uppercase: `ACTIVE`, `GRADUATED`,
  /// `INACTIVE`, `TRANSFERRED`, `ARCHIVED`). Empty means "any status".
  final Set<String> statuses;

  /// When true, only students with `is_face_registered == true` pass.
  final bool faceEnrolledOnly;

  /// True when at least one filter axis is constraining.
  bool get isActive =>
      query.trim().isNotEmpty ||
      programIds.isNotEmpty ||
      yearLevels.isNotEmpty ||
      statuses.isNotEmpty ||
      faceEnrolledOnly;

  /// Number of active filter axes (used to render the "n of total"
  /// summary line under the chip row).
  int get activeCount {
    var n = 0;
    if (query.trim().isNotEmpty) n++;
    if (programIds.isNotEmpty) n++;
    if (yearLevels.isNotEmpty) n++;
    if (statuses.isNotEmpty) n++;
    if (faceEnrolledOnly) n++;
    return n;
  }

  StudentFilter copyWith({
    String? query,
    Set<int>? programIds,
    Set<int>? yearLevels,
    Set<String>? statuses,
    bool? faceEnrolledOnly,
  }) {
    return StudentFilter(
      query: query ?? this.query,
      programIds: programIds ?? this.programIds,
      yearLevels: yearLevels ?? this.yearLevels,
      statuses: statuses ?? this.statuses,
      faceEnrolledOnly: faceEnrolledOnly ?? this.faceEnrolledOnly,
    );
  }

  /// Returns the empty filter (everything passes — equivalent to
  /// `const StudentFilter()`). Provided for clarity at call sites
  /// where a "Clear all" action wants to be obvious.
  StudentFilter cleared() => const StudentFilter();

  /// Apply the filter to a list of users. Only accounts with a
  /// `studentProfile` ever pass — faculty/admin/school-IT rows drop
  /// out at the very first check, matching the rest of the
  /// schoolit users-by-college surface.
  List<UserProfile> apply(List<UserProfile> users) {
    final q = query.trim().toLowerCase();
    return users.where((u) => _matches(u, q)).toList(growable: false);
  }

  bool _matches(UserProfile u, String q) {
    final sp = u.studentProfile;
    if (sp == null) return false;

    if (q.isNotEmpty) {
      final hits = u.displayName.toLowerCase().contains(q) ||
          (u.email ?? '').toLowerCase().contains(q) ||
          (sp.studentNumber ?? '').toLowerCase().contains(q);
      if (!hits) return false;
    }

    if (programIds.isNotEmpty &&
        (sp.programId == null || !programIds.contains(sp.programId))) {
      return false;
    }

    if (yearLevels.isNotEmpty &&
        (sp.yearLevel == null || !yearLevels.contains(sp.yearLevel))) {
      return false;
    }

    if (statuses.isNotEmpty) {
      final status = sp.studentStatus;
      if (status == null || !statuses.contains(status.toUpperCase())) {
        return false;
      }
    }

    if (faceEnrolledOnly && !sp.isFaceRegistered) {
      return false;
    }

    return true;
  }

  @override
  bool operator ==(Object other) =>
      other is StudentFilter &&
      other.query == query &&
      _setEq(other.programIds, programIds) &&
      _setEq(other.yearLevels, yearLevels) &&
      _setEq(other.statuses, statuses) &&
      other.faceEnrolledOnly == faceEnrolledOnly;

  @override
  int get hashCode => Object.hash(
        query,
        Object.hashAllUnordered(programIds),
        Object.hashAllUnordered(yearLevels),
        Object.hashAllUnordered(statuses),
        faceEnrolledOnly,
      );

  static bool _setEq<T>(Set<T> a, Set<T> b) =>
      a.length == b.length && a.containsAll(b);
}
