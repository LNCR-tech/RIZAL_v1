import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/profile.dart';
import '../../../shared/models/school.dart';
import '../data/schoolit_repository.dart';

final studentsProvider = FutureProvider.autoDispose<List<UserProfile>>((ref) {
  return ref.watch(schoolItRepositoryProvider).students();
});

final departmentsProvider = FutureProvider.autoDispose<List<Department>>((ref) {
  return ref.watch(schoolItRepositoryProvider).departments();
});

final programsProvider = FutureProvider.autoDispose<List<Program>>((ref) {
  return ref.watch(schoolItRepositoryProvider).programs();
});

final schoolProvider = FutureProvider.autoDispose<SchoolBranding>((ref) {
  return ref.watch(schoolItRepositoryProvider).school();
});
