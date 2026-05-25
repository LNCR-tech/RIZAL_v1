import '../utils/json.dart';

class StudentProfile {
  const StudentProfile({
    required this.id,
    this.userId,
    this.schoolId,
    this.studentNumber,
    this.departmentId,
    this.programId,
    this.yearLevel,
    this.studentStatus,
    this.isFaceRegistered = false,
    this.registrationComplete = false,
  });

  final int id;
  final int? userId;
  final int? schoolId;
  final String? studentNumber;
  final int? departmentId;
  final int? programId;
  final int? yearLevel;
  final String? studentStatus;
  final bool isFaceRegistered;
  final bool registrationComplete;

  factory StudentProfile.fromJson(Map<String, dynamic> j) => StudentProfile(
        id: asInt(j['id']) ?? 0,
        userId: asInt(j['user_id']),
        schoolId: asInt(j['school_id']),
        studentNumber: asStr(j['student_id']) ?? asStr(j['student_number']),
        departmentId: asInt(j['department_id']),
        programId: asInt(j['program_id']),
        yearLevel: asInt(j['year_level']),
        studentStatus: asStr(j['student_status']),
        isFaceRegistered: asBool(j['is_face_registered']),
        registrationComplete: asBool(j['registration_complete']),
      );
}

/// The signed-in user (`/users/me/`), including the student profile if present.
class UserProfile {
  const UserProfile({
    required this.id,
    this.email,
    this.firstName,
    this.middleName,
    this.lastName,
    this.schoolId,
    this.isActive = true,
    this.roles = const [],
    this.studentProfile,
  });

  final int id;
  final String? email;
  final String? firstName;
  final String? middleName;
  final String? lastName;
  final int? schoolId;
  final bool isActive;
  final List<String> roles;
  final StudentProfile? studentProfile;

  String get displayName {
    final n = [firstName, lastName]
        .where((e) => e != null && e.trim().isNotEmpty)
        .join(' ')
        .trim();
    return n.isNotEmpty ? n : (email ?? 'User');
  }

  String get initials {
    final a = (firstName ?? '').trim();
    final b = (lastName ?? '').trim();
    final x = a.isNotEmpty ? a[0] : (email ?? '?')[0];
    final y = b.isNotEmpty ? b[0] : '';
    return (x + y).toUpperCase();
  }

  factory UserProfile.fromJson(Map<String, dynamic> j) {
    final roles = <String>[];
    final rolesRaw = j['roles'];
    if (rolesRaw is List) {
      for (final r in rolesRaw) {
        if (r is Map) {
          final role = r['role'];
          if (role is Map && role['name'] != null) {
            roles.add(role['name'].toString());
          } else if (r['name'] != null) {
            roles.add(r['name'].toString());
          }
        } else if (r is String) {
          roles.add(r);
        }
      }
    }
    final sp = j['student_profile'];
    return UserProfile(
      id: asInt(j['id']) ?? 0,
      email: asStr(j['email']),
      firstName: asStr(j['first_name']),
      middleName: asStr(j['middle_name']),
      lastName: asStr(j['last_name']),
      schoolId: asInt(j['school_id']),
      isActive: asBool(j['is_active']),
      roles: roles,
      studentProfile:
          sp is Map ? StudentProfile.fromJson(sp.cast<String, dynamic>()) : null,
    );
  }
}
