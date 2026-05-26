import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/widgets/event_calendar.dart';
import '../../../core/widgets/states.dart';
import '../application/events_providers.dart';
import 'event_detail_screen.dart';

/// Student "Schedule" — a calendar of the student's events with search; tap an
/// event to see its detail + their status.
class ScheduleScreen extends ConsumerWidget {
  const ScheduleScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(scheduleEventsProvider);
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(
              AppSpacing.x20, AppSpacing.x24, AppSpacing.x20, AppSpacing.x8),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text('Schedule',
                style: Theme.of(context).textTheme.displaySmall),
          ),
        ),
        Expanded(
          child: async.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.x20),
                child: ErrorView(
                  message: e is ApiException
                      ? e.message
                      : 'Could not load your schedule.',
                  onRetry: () => ref.invalidate(scheduleEventsProvider),
                ),
              ),
            ),
            data: (events) => EventCalendar(
              events: events,
              onTap: (event) => Navigator.of(context).push(MaterialPageRoute(
                  builder: (_) => EventDetailScreen(eventId: event.id))),
            ),
          ),
        ),
      ],
    );
  }
}
