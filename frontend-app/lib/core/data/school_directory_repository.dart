import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/school.dart';
import '../network/api_paths.dart';
import '../network/dio_client.dart';
import '../network/paginated.dart';

/// Read-only directory lookups for academic units (departments + programs).
/// Backed by `/api/departments/` and `/api/programs/` which the backend
/// exposes to any authenticated user (per Backend Documentation lines 1049,
/// 1129). Mutating endpoints (create / update / delete) stay in
/// `SchoolItRepository` — this surface is the lowest common denominator
/// for student / governance screens that just need to render names by id.
class SchoolDirectoryRepository {
  SchoolDirectoryRepository(this._client);
  final DioClient _client;

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
}

final schoolDirectoryRepositoryProvider = Provider<SchoolDirectoryRepository>(
  (ref) => SchoolDirectoryRepository(ref.watch(dioClientProvider)),
);

/// Session-cached list of every department in the signed-in school.
/// **Not** `autoDispose` — the list is small (typically <30 entries) and we
/// don't want to refetch on every screen mount that needs to render a name.
/// Refresh manually with `ref.invalidate(allDepartmentsProvider)` (e.g. from
/// a pull-to-refresh).
final allDepartmentsProvider = FutureProvider<List<Department>>(
  (ref) => ref.watch(schoolDirectoryRepositoryProvider).departments(),
);

final allProgramsProvider = FutureProvider<List<Program>>(
  (ref) => ref.watch(schoolDirectoryRepositoryProvider).programs(),
);

/// Resolve one department by id. Returns `null` (not an error) when the
/// directory has loaded but doesn't contain the id — happens if a
/// department was deleted while the user was offline. The `AsyncValue`
/// stays in `loading` while the underlying directory is in flight.
final departmentByIdProvider = FutureProvider.family<Department?, int>(
  (ref, id) async {
    final all = await ref.watch(allDepartmentsProvider.future);
    for (final d in all) {
      if (d.id == id) return d;
    }
    return null;
  },
);

final programByIdProvider = FutureProvider.family<Program?, int>(
  (ref, id) async {
    final all = await ref.watch(allProgramsProvider.future);
    for (final p in all) {
      if (p.id == id) return p;
    }
    return null;
  },
);
