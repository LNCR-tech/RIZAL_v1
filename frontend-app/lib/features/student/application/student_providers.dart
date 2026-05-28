import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/realtime/live_ticker.dart';
import '../../../core/realtime/polling_pace.dart';
import '../../../shared/models/analytics.dart';
import '../../../shared/models/notification_item.dart';
import '../../../shared/models/profile.dart';
import '../../notifications/data/notifications_repository.dart';
import '../data/profile_repository.dart';
import '../data/reports_repository.dart';

/// The signed-in user's full profile (`/users/me/`).
///
/// Live: refetches every 30s while the app is foregrounded so that
/// fields a campus admin edited from another device (status, year
/// level, college, program) show up without the student touching
/// pull-to-refresh. Pauses when the app is backgrounded; resumes
/// immediately on foreground.
final myProfileProvider = FutureProvider.autoDispose<UserProfile>((ref) async {
  ref.watch(livePollingTickerProvider(PollingPace.medium));
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
///
/// Live: refetches every 30s. Backend doesn't push, so this is how
/// new notifications surface without a manual refresh.
final notificationsProvider =
    FutureProvider.autoDispose<List<NotificationItem>>((ref) async {
  ref.watch(livePollingTickerProvider(PollingPace.medium));
  return ref.watch(notificationsRepositoryProvider).inbox();
});
