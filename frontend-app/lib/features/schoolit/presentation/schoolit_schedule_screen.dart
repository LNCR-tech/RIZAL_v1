import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/widgets/event_calendar.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/event.dart';
import '../../events/application/events_providers.dart';
import '../../governance/presentation/governance_event_monitor_screen.dart';
import 'event_editor_screen.dart';

/// School-IT "Schedule" — calendar of all school events (upcoming/ongoing/done)
/// with search; create new events.
class SchoolItScheduleScreen extends ConsumerWidget {
  const SchoolItScheduleScreen({super.key});

  void _monitor(BuildContext context, AppEvent event) =>
      Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => GovernanceEventMonitorScreen(event: event)));

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(scheduleEventsProvider);
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(
              AppSpacing.x20, AppSpacing.x24, AppSpacing.x20, AppSpacing.x8),
          child: Row(
            children: [
              Expanded(
                  child: Text('Schedule',
                      style: Theme.of(context).textTheme.displaySmall)),
              IconButton.filledTonal(
                tooltip: 'New event',
                icon: const Icon(Icons.add_rounded),
                onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => const EventEditorScreen())),
              ),
            ],
          ),
        ),
        Expanded(
          child: async.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.x20),
                child: ErrorView(
                  message:
                      e is ApiException ? e.message : 'Could not load events.',
                  onRetry: () => ref.invalidate(scheduleEventsProvider),
                ),
              ),
            ),
            data: (events) => EventCalendar(
                events: events, onTap: (e) => _monitor(context, e)),
          ),
        ),
      ],
    );
  }
}
