import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/analytics.dart';
import '../../../shared/models/notification_item.dart';
import '../../../shared/models/profile.dart';
import '../../notifications/data/notifications_repository.dart';
import '../data/profile_repository.dart';
import '../data/reports_repository.dart';

/// The signed-in user's full profile (`/users/me/`).
final myProfileProvider = FutureProvider.autoDispose<UserProfile>((ref) async {
  return ref.watch(profileRepositoryProvider).me();
});

/// The student's attendance analytics, keyed off their student-profile id.
final studentReportProvider =
    FutureProvider.autoDispose<StudentReport>((ref) async {
  final profile = await ref.watch(myProfileProvider.future);
  final pid = profile.studentProfile?.id;
  if (pid == null) {
    throw ApiException(
        'This account has no student profile, so analytics are unavailable.');
  }
  return ref.watch(reportsRepositoryProvider).studentReport(pid);
});

/// The user's notification inbox.
final notificationsProvider =
    FutureProvider.autoDispose<List<NotificationItem>>((ref) async {
  return ref.watch(notificationsRepositoryProvider).inbox();
});
