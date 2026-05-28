import '../../../shared/models/profile.dart';

/// Pure-Dart state holder for the "Edit student" surface. Seeds from a
/// [UserProfile] snapshot, tracks per-field changes, and exposes **two
/// independent** patch maps — one for the user PATCH endpoint (name,
/// email) and one for the student-profile PATCH endpoint (academics +
/// status). Builds patches with only dirty fields so a save that touches
/// just the year level doesn't re-send the email (which would re-trigger
/// the backend's uniqueness check unnecessarily).
///
/// Validation methods return `null` on success or a one-sentence error
/// suitable for surfacing in an inline error pill. The screen layer is
/// expected to call them before invoking [identityPatch] / [academicsPatch].
class EditStudentForm {
  EditStudentForm.fromUser(this._initial) {
    final sp = _initial.studentProfile;
    firstName = _initial.firstName ?? '';
    middleName = _initial.middleName ?? '';
    lastName = _initial.lastName ?? '';
    email = _initial.email ?? '';

    studentNumber = sp?.studentNumber ?? '';
    departmentId = sp?.departmentId;
    programId = sp?.programId;
    yearLevel = sp?.yearLevel ?? 1;
    studentStatus = (sp?.studentStatus != null &&
            statuses.contains(sp!.studentStatus))
        ? sp.studentStatus!
        : statuses.first;
    promotionLocked = sp?.promotionLocked ?? false;
  }

  final UserProfile _initial;

  // Identity fields
  late String firstName;
  late String middleName;
  late String lastName;
  late String email;

  // Academics fields
  late String studentNumber;
  int? departmentId;
  int? programId;
  late int yearLevel;
  late String studentStatus;
  late bool promotionLocked;

  /// Allowed backend status values (`student_status` enum, see
  /// Backend Documentation line 969).
  static const List<String> statuses = [
    'ACTIVE',
    'GRADUATED',
    'INACTIVE',
    'TRANSFERRED',
    'ARCHIVED',
  ];

  /// Status transitions that block sign-in / drop the student from
  /// workspaces. Used by the screen layer to require an explicit confirm
  /// dialog before saving the academics section.
  static const Set<String> destructiveStatuses = {
    'INACTIVE',
    'TRANSFERRED',
    'ARCHIVED',
  };

  // ─── Dirty tracking ─────────────────────────────────────────────────

  bool get identityDirty {
    final o = _initial;
    return firstName.trim() != (o.firstName ?? '').trim() ||
        middleName.trim() != (o.middleName ?? '').trim() ||
        lastName.trim() != (o.lastName ?? '').trim() ||
        email.trim() != (o.email ?? '').trim();
  }

  bool get academicsDirty {
    final sp = _initial.studentProfile;
    if (sp == null) return false;
    final origStatus =
        (sp.studentStatus != null && statuses.contains(sp.studentStatus))
            ? sp.studentStatus!
            : statuses.first;
    return studentNumber.trim() != (sp.studentNumber ?? '').trim() ||
        departmentId != sp.departmentId ||
        programId != sp.programId ||
        yearLevel != (sp.yearLevel ?? 1) ||
        studentStatus != origStatus ||
        promotionLocked != sp.promotionLocked;
  }

  bool get anyDirty => identityDirty || academicsDirty;

  /// True when the academics save would transition the student INTO a
  /// destructive status (loss of access). Returning to / staying in an
  /// already-destructive status is **not** flagged — the screen only
  /// confirms the actual transition.
  bool get statusChangeIsDestructive {
    final origStatus = _initial.studentProfile?.studentStatus ?? statuses.first;
    return studentStatus != origStatus &&
        destructiveStatuses.contains(studentStatus);
  }

  // ─── Patch builders — only dirty fields ─────────────────────────────

  /// Patch for `PATCH /api/users/{id}`. Returns an empty map when no
  /// identity field has changed (caller should skip the request entirely).
  Map<String, dynamic> identityPatch() {
    final o = _initial;
    final patch = <String, dynamic>{};
    if (firstName.trim() != (o.firstName ?? '').trim()) {
      patch['first_name'] = firstName.trim();
    }
    if (middleName.trim() != (o.middleName ?? '').trim()) {
      // Empty middle-name string → explicit null so the backend can clear it.
      final t = middleName.trim();
      patch['middle_name'] = t.isEmpty ? null : t;
    }
    if (lastName.trim() != (o.lastName ?? '').trim()) {
      patch['last_name'] = lastName.trim();
    }
    if (email.trim() != (o.email ?? '').trim()) {
      patch['email'] = email.trim();
    }
    return patch;
  }

  /// Patch for `PATCH /api/users/student-profiles/{profile_id}`. Returns
  /// an empty map when no academics field has changed.
  Map<String, dynamic> academicsPatch() {
    final sp = _initial.studentProfile;
    if (sp == null) return const <String, dynamic>{};
    final origStatus =
        (sp.studentStatus != null && statuses.contains(sp.studentStatus))
            ? sp.studentStatus!
            : statuses.first;
    final patch = <String, dynamic>{};
    if (studentNumber.trim() != (sp.studentNumber ?? '').trim()) {
      patch['student_id'] = studentNumber.trim();
    }
    if (departmentId != sp.departmentId) {
      patch['department_id'] = departmentId;
    }
    if (programId != sp.programId) {
      patch['program_id'] = programId;
    }
    if (yearLevel != (sp.yearLevel ?? 1)) {
      patch['year_level'] = yearLevel;
    }
    if (studentStatus != origStatus) {
      patch['student_status'] = studentStatus;
    }
    if (promotionLocked != sp.promotionLocked) {
      patch['promotion_locked'] = promotionLocked;
    }
    return patch;
  }

  // ─── Validation ─────────────────────────────────────────────────────

  /// `null` when the identity section is valid; otherwise a one-sentence
  /// error message ready to surface inline.
  String? validateIdentity() {
    if (firstName.trim().isEmpty) return 'First name is required.';
    if (firstName.trim().length > 60) return 'First name is too long.';
    if (middleName.trim().length > 60) return 'Middle name is too long.';
    if (lastName.trim().isEmpty) return 'Last name is required.';
    if (lastName.trim().length > 60) return 'Last name is too long.';
    final e = email.trim();
    if (e.isEmpty) return 'Email is required.';
    if (!_emailRegExp.hasMatch(e)) return 'Enter a valid email address.';
    return null;
  }

  String? validateAcademics() {
    final n = studentNumber.trim();
    if (n.isEmpty) return 'Student number is required.';
    if (n.length < 3 || n.length > 50) {
      return 'Student number must be 3–50 characters.';
    }
    if (!_studentIdRegExp.hasMatch(n)) {
      return 'Student number can only contain letters, numbers, and hyphens.';
    }
    if (departmentId == null) return 'Pick a college.';
    if (programId == null) return 'Pick a program.';
    if (yearLevel < 1 || yearLevel > 5) {
      return 'Year level must be between 1 and 5.';
    }
    if (!statuses.contains(studentStatus)) {
      return 'Pick a valid status.';
    }
    return null;
  }

  static final RegExp _emailRegExp =
      RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$');
  static final RegExp _studentIdRegExp = RegExp(r'^[A-Za-z0-9-]+$');
}
