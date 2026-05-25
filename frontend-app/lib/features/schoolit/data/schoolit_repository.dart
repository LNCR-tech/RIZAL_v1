import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_paths.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/network/paginated.dart';
import '../../../shared/models/import_job.dart';
import '../../../shared/models/profile.dart';
import '../../../shared/models/school.dart';
import '../../../shared/utils/json.dart';

class SchoolItRepository {
  SchoolItRepository(this._client);
  final DioClient _client;

  /// Loads ALL users. The backend paginates by **page** (it ignores `skip`) and
  /// caps a page at 500, so we walk `page=1..total_pages` and de-duplicate by id.
  Future<List<UserProfile>> students() async {
    final all = <UserProfile>[];
    final seen = <int>{};
    var page = 1;
    while (page <= 50) {
      final r =
          await _client.get(Api.users, query: {'page': page, 'limit': 500});
      final data = r.data;
      final List rawItems;
      final int totalPages;
      if (data is Map) {
        rawItems = (data['data'] as List?) ?? const [];
        totalPages = asInt(data['total_pages']) ?? 1;
      } else if (data is List) {
        rawItems = data;
        totalPages = 1;
      } else {
        break;
      }
      for (final e in rawItems) {
        if (e is Map) {
          final u = UserProfile.fromJson(e.cast<String, dynamic>());
          if (seen.add(u.id)) all.add(u);
        }
      }
      if (page >= totalPages || rawItems.isEmpty) break;
      page += 1;
    }
    return all;
  }

  Future<UserProfile> user(int id) async {
    final r = await _client.get(Api.user(id));
    return UserProfile.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<List<Department>> departments() async {
    final r = await _client.get(Api.departments);
    return Paginated.from(
      r.data,
      (e) => Department.fromJson((e as Map).cast<String, dynamic>()),
    ).data;
  }

  Future<List<Program>> programs() async {
    final r = await _client.get(Api.programs);
    return Paginated.from(
      r.data,
      (e) => Program.fromJson((e as Map).cast<String, dynamic>()),
    ).data;
  }

  Future<void> createDepartment(String name) =>
      _client.post(Api.departments, data: {'name': name});

  Future<void> renameDepartment(int id, String name) =>
      _client.patch('${Api.departments}$id', data: {'name': name});

  Future<void> deleteDepartment(int id) =>
      _client.delete('${Api.departments}$id');

  Future<SchoolBranding> school() async {
    final r = await _client.get(Api.schoolMe);
    return SchoolBranding.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<SchoolBranding> updatePolicy({
    String? name,
    String? schoolCode,
    String? primaryColor,
    String? secondaryColor,
    List<int>? logoBytes,
    String? logoName,
    int? early,
    int? late,
    int? signOut,
  }) async {
    final map = <String, dynamic>{
      if (name != null) 'school_name': name,
      if (schoolCode != null) 'school_code': schoolCode,
      if (primaryColor != null) 'primary_color': primaryColor,
      if (secondaryColor != null) 'secondary_color': secondaryColor,
      if (early != null) 'event_default_early_check_in_minutes': early,
      if (late != null) 'event_default_late_threshold_minutes': late,
      if (signOut != null) 'event_default_sign_out_grace_minutes': signOut,
    };
    if (logoBytes != null) {
      map['logo'] =
          MultipartFile.fromBytes(logoBytes, filename: logoName ?? 'logo.png');
    }
    final r = await _client.put(Api.schoolUpdate, data: FormData.fromMap(map));
    return SchoolBranding.fromJson((r.data as Map).cast<String, dynamic>());
  }

  /// Create a single student account (`POST /api/users/students/`).
  Future<void> createStudent({
    required String email,
    required String firstName,
    String? middleName,
    required String lastName,
    String? studentId,
    required int departmentId,
    required int programId,
    int yearLevel = 1,
    String status = 'ACTIVE',
  }) async {
    await _client.post('${Api.users}students/', data: {
      'email': email,
      'first_name': firstName,
      if (middleName != null && middleName.isNotEmpty) 'middle_name': middleName,
      'last_name': lastName,
      if (studentId != null && studentId.isNotEmpty) 'student_id': studentId,
      'department_id': departmentId,
      'program_id': programId,
      'year_level': yearLevel,
      'student_status': status,
    });
  }

  Future<ImportPreview> previewImport(String path, String filename) async {
    final form = FormData.fromMap(
        {'file': await MultipartFile.fromFile(path, filename: filename)});
    final r = await _client.post(
      Api.importPreview,
      data: form,
      options: Options(
        sendTimeout: const Duration(seconds: 60),
        receiveTimeout: const Duration(seconds: 60),
      ),
    );
    return ImportPreview.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<String> commitImport(String previewToken) async {
    final form = FormData.fromMap({'preview_token': previewToken});
    final r = await _client.post(Api.importCommit, data: form);
    final data = r.data;
    return (data is Map ? asStr(data['job_id']) : null) ?? '';
  }

  Future<ImportJobStatus> importStatus(String jobId) async {
    final r = await _client.get(Api.importStatus(jobId));
    return ImportJobStatus.fromJson((r.data as Map).cast<String, dynamic>());
  }
}

final schoolItRepositoryProvider = Provider<SchoolItRepository>(
  (ref) => SchoolItRepository(ref.watch(dioClientProvider)),
);
