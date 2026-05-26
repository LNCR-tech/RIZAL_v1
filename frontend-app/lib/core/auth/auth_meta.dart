import 'role.dart';

/// Decoded login metadata returned alongside the access token by `/token`.
/// Mirrors `normalizeTokenPayload` / `storeAuthMeta` in the web client.
class AuthMeta {
  const AuthMeta({
    this.email,
    this.roles = const [],
    this.tokenType = 'bearer',
    this.userId,
    this.firstName,
    this.lastName,
    this.mustChangePassword = false,
    this.faceVerificationRequired = false,
    this.faceVerificationPending = false,
    this.faceReferenceEnrolled = false,
    this.schoolId,
    this.schoolName,
    this.schoolCode,
    this.logoUrl,
    this.primaryColor,
    this.secondaryColor,
    this.accentColor,
    this.sessionId,
    this.isAdmin = false,
  });

  final String? email;
  final List<String> roles;
  final String tokenType;
  final int? userId;
  final String? firstName;
  final String? lastName;
  final bool mustChangePassword;
  final bool faceVerificationRequired;
  final bool faceVerificationPending;
  final bool faceReferenceEnrolled;
  final int? schoolId;
  final String? schoolName;
  final String? schoolCode;
  final String? logoUrl;
  final String? primaryColor;
  final String? secondaryColor;
  final String? accentColor;
  final String? sessionId;
  final bool isAdmin;

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

  /// Privileged session still owing a face verification gate.
  bool get pendingPrivilegedFace => Roles.hasPrivilegedPendingFace(
        roles: roles,
        tokenType: tokenType,
        facePending: faceVerificationPending,
        faceRequired: faceVerificationRequired,
      );

  factory AuthMeta.fromJson(Map<String, dynamic> json) {
    bool b(dynamic v) => v == true;
    int? i(dynamic v) =>
        v is num ? v.toInt() : (v is String ? int.tryParse(v) : null);
    String? s(dynamic v) {
      final str = v?.toString().trim();
      return (str == null || str.isEmpty) ? null : str;
    }

    final roles = Roles.normalizeList(json['roles']);
    return AuthMeta(
      email: s(json['email']),
      roles: roles,
      tokenType: s(json['token_type']) ?? 'bearer',
      userId: i(json['user_id']),
      firstName: s(json['first_name']),
      lastName: s(json['last_name']),
      mustChangePassword: b(json['must_change_password']),
      faceVerificationRequired: b(json['face_verification_required']),
      faceVerificationPending: b(json['face_verification_pending']),
      faceReferenceEnrolled: b(json['face_reference_enrolled']),
      schoolId: i(json['school_id']),
      schoolName: s(json['school_name']),
      schoolCode: s(json['school_code']),
      logoUrl: s(json['logo_url']),
      primaryColor: s(json['primary_color']),
      secondaryColor: s(json['secondary_color']),
      accentColor: s(json['accent_color']),
      sessionId: s(json['session_id']),
      isAdmin: json['is_admin'] is bool
          ? json['is_admin'] as bool
          : roles.map(Roles.normalize).contains('admin'),
    );
  }

  Map<String, dynamic> toJson() => {
        'email': email,
        'roles': roles,
        'token_type': tokenType,
        'user_id': userId,
        'first_name': firstName,
        'last_name': lastName,
        'must_change_password': mustChangePassword,
        'face_verification_required': faceVerificationRequired,
        'face_verification_pending': faceVerificationPending,
        'face_reference_enrolled': faceReferenceEnrolled,
        'school_id': schoolId,
        'school_name': schoolName,
        'school_code': schoolCode,
        'logo_url': logoUrl,
        'primary_color': primaryColor,
        'secondary_color': secondaryColor,
        'accent_color': accentColor,
        'session_id': sessionId,
        'is_admin': isAdmin,
      };

  AuthMeta copyWith({
    bool? mustChangePassword,
    bool? faceVerificationPending,
    bool? faceReferenceEnrolled,
    String? tokenType,
  }) {
    return AuthMeta(
      email: email,
      roles: roles,
      tokenType: tokenType ?? this.tokenType,
      userId: userId,
      firstName: firstName,
      lastName: lastName,
      mustChangePassword: mustChangePassword ?? this.mustChangePassword,
      faceVerificationRequired: faceVerificationRequired,
      faceVerificationPending:
          faceVerificationPending ?? this.faceVerificationPending,
      faceReferenceEnrolled:
          faceReferenceEnrolled ?? this.faceReferenceEnrolled,
      schoolId: schoolId,
      schoolName: schoolName,
      schoolCode: schoolCode,
      logoUrl: logoUrl,
      primaryColor: primaryColor,
      secondaryColor: secondaryColor,
      accentColor: accentColor,
      sessionId: sessionId,
      isAdmin: isAdmin,
    );
  }
}
