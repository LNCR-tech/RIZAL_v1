import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/realtime/live_ticker.dart';
import '../../../core/realtime/polling_pace.dart';
import '../../../shared/models/profile.dart';
import '../../../shared/models/school.dart';
import '../data/schoolit_repository.dart';

/// Live: refetches every 60s while the schoolit dashboard / users
/// tab is foregrounded so bulk-import completions and accounts
/// added from another device appear without manual refresh.
final studentsProvider = FutureProvider.autoDispose<List<UserProfile>>((ref) {
  ref.watch(livePollingTickerProvider(PollingPace.slow));
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
