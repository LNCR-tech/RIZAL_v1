import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/attendance.dart';
import '../../../shared/models/event.dart';
import '../../../shared/models/governance.dart';
import '../../../shared/models/sanctions.dart';
import '../../../shared/models/school.dart';
import '../../events/data/events_repository.dart';
import '../../schoolit/data/schoolit_repository.dart';
import '../data/governance_repository.dart';
import '../data/sanctions_repository.dart';

/// The user's governance access (units + permissions). Drives the workspace.
final governanceAccessProvider =
    FutureProvider.autoDispose<GovernanceAccess>((ref) async {
  return ref.watch(governanceRepositoryProvider).accessMe();
});

/// Current student's own sanction records (`GET /api/sanctions/students/me`).
/// Returns an empty list when the student has no outstanding sanctions or
/// when their role doesn't include student profile (officer-only accounts).
final mySanctionsProvider =
    FutureProvider.autoDispose<List<SanctionRecord>>((ref) async {
  return ref.watch(sanctionsRepositoryProvider).mine();
});

/// School-wide active clearance deadline. Null when none is set.
final activeClearanceDeadlineProvider =
    FutureProvider.autoDispose<ClearanceDeadline?>((ref) async {
  return ref.watch(sanctionsRepositoryProvider).activeClearanceDeadline();
});

/// Explicitly selected active unit (overrides the preferred default).
class ActiveUnitController extends Notifier<GovUnitAccess?> {
  @override
  GovUnitAccess? build() => null;
  void select(GovUnitAccess unit) => state = unit;
  void clear() => state = null;
}

final activeUnitProvider =
    NotifierProvider<ActiveUnitController, GovUnitAccess?>(
        ActiveUnitController.new);

/// The unit to operate on: explicit selection, else the preferred default.
final effectiveUnitProvider = Provider.autoDispose<GovUnitAccess?>((ref) {
  final override = ref.watch(activeUnitProvider);
  if (override != null) return override;
  return ref.watch(governanceAccessProvider).valueOrNull?.preferred;
});

final unitDetailProvider =
    FutureProvider.autoDispose.family<GovernanceUnitDetail, int>((ref, id) {
  return ref.watch(governanceRepositoryProvider).unitDetail(id);
});

final dashboardOverviewProvider = FutureProvider.autoDispose
    .family<GovernanceDashboardOverview, int>((ref, id) {
  return ref.watch(governanceRepositoryProvider).dashboard(id);
});

/// Colleges (departments) for the SG-creation college picker. Reuses the
/// school-IT repository — `GET /api/departments/` is governance-accessible.
final govDepartmentsProvider =
    FutureProvider.autoDispose<List<Department>>((ref) {
  return ref.watch(schoolItRepositoryProvider).departments();
});

/// Programs for the ORG-creation program picker (filtered client-side to the
/// parent SG's department via [Program.departmentIds]).
final govProgramsProvider = FutureProvider.autoDispose<List<Program>>((ref) {
  return ref.watch(schoolItRepositoryProvider).programs();
});

/// Create a child governance unit (SG under an SSG, or ORG under an SG), then
/// refresh the user's access and the parent's dashboard so the new child shows
/// up. Returns the created unit's detail. Backend validation errors surface as
/// [ApiException] to the caller.
Future<GovernanceUnitDetail> createGovernanceUnit(
  WidgetRef ref, {
  required String code,
  required String name,
  required String type,
  required int parentUnitId,
  String? description,
  int? departmentId,
  int? programId,
}) async {
  final detail = await ref.read(governanceRepositoryProvider).createUnit(
        code: code,
        name: name,
        type: type,
        description: description,
        parentUnitId: parentUnitId,
        departmentId: departmentId,
        programId: programId,
      );
  ref.invalidate(governanceAccessProvider);
  ref.invalidate(dashboardOverviewProvider(parentUnitId));
  return detail;
}

final announcementsProvider = FutureProvider.autoDispose
    .family<List<GovernanceAnnouncement>, int>((ref, id) {
  return ref.watch(governanceRepositoryProvider).announcements(id);
});

/// Events visible in a governance context (SSG | SG | ORG).
final governanceEventsProvider =
    FutureProvider.autoDispose.family<List<AppEvent>, String>((ref, context) {
  return ref
      .watch(eventsRepositoryProvider)
      .list(limit: 200, governanceContext: context);
});

final eventStatsProvider =
    FutureProvider.autoDispose.family<EventStats, int>((ref, eventId) {
  return ref.watch(governanceRepositoryProvider).eventStats(eventId);
});

/// Polls event stats every 15s — drives the live attendance bar for ongoing
/// events.
final eventLiveStatsProvider =
    StreamProvider.autoDispose.family<EventStats, int>((ref, eventId) async* {
  final repo = ref.watch(governanceRepositoryProvider);
  while (true) {
    yield await repo.eventStats(eventId);
    await Future<void>.delayed(const Duration(seconds: 15));
  }
});

final eventAttendeesProvider = FutureProvider.autoDispose
    .family<List<AttendanceRecord>, int>((ref, eventId) {
  return ref.watch(governanceRepositoryProvider).eventAttendees(eventId);
});

final sanctionsDashboardProvider =
    FutureProvider.autoDispose<SanctionsDashboard>((ref) {
  return ref.watch(sanctionsRepositoryProvider).dashboard();
});

final sanctionEventStudentsProvider =
    FutureProvider.autoDispose.family<PaginatedSanctions, int>((ref, eventId) {
  return ref.watch(sanctionsRepositoryProvider).eventStudents(eventId);
});
