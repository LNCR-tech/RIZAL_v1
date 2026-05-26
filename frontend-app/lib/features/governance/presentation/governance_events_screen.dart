import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/event_calendar.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/event.dart';
import '../../schoolit/presentation/event_editor_screen.dart';
import '../application/governance_providers.dart';
import 'governance_event_monitor_screen.dart';

/// Governance "Events" — a calendar scoped to the active unit (its college/org)
/// with search + create. Wrapped in an [AppScaffold] so it provides a Material
/// ancestor whether shown as a tab or pushed from the dashboard.
class GovernanceEventsScreen extends ConsumerWidget {
  const GovernanceEventsScreen({super.key});

  void _open(BuildContext context, AppEvent event) =>
      Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => GovernanceEventMonitorScreen(event: event)));

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final unit = ref.watch(effectiveUnitProvider);

    if (unit == null) {
      return const AppScaffold(
        title: 'Events',
        body: Center(
          child: EmptyState(
            icon: Icons.event_rounded,
            title: 'No unit selected',
            message: 'Governance access is required to view events.',
          ),
        ),
      );
    }

    final async = ref.watch(governanceEventsProvider(unit.type));
    return AppScaffold(
      title: 'Events',
      actions: unit.can('manage_events')
          ? [
              IconButton(
                tooltip: 'New event',
                icon: const Icon(Icons.add_rounded),
                onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) =>
                        EventEditorScreen(governanceContext: unit.type))),
              ),
            ]
          : null,
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(
                AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 0),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(unit.name,
                  style: textTheme.bodyLarge?.copyWith(color: t.textSecondary)),
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
                        : 'Could not load events.',
                    onRetry: () =>
                        ref.invalidate(governanceEventsProvider(unit.type)),
                  ),
                ),
              ),
              data: (events) =>
                  EventCalendar(events: events, onTap: (e) => _open(context, e)),
            ),
          ),
        ],
      ),
    );
  }
}
