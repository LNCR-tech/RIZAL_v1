import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/event.dart';
import '../../attendance/presentation/attendance_screen.dart';
import '../application/events_providers.dart';
import 'widgets/event_card.dart';

/// Quick check-in: lists ongoing events; tapping one opens the face scan.
class ScanEntryScreen extends ConsumerWidget {
  const ScanEntryScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x24, AppSpacing.x20, 120);

  void _open(BuildContext context, AppEvent event) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => AttendanceScreen(event: event)),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final async = ref.watch(ongoingEventsProvider);

    Widget header() => Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.x16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Scan', style: textTheme.displaySmall),
              const SizedBox(height: 4),
              Text('Check in to a live event',
                  style: textTheme.bodyLarge?.copyWith(color: t.textSecondary)),
            ],
          ),
        );

    return RefreshIndicator(
      color: t.accent,
      backgroundColor: t.surface,
      onRefresh: () => ref.refresh(ongoingEventsProvider.future),
      child: async.when(
        loading: () => ListView(
          padding: _pad,
          physics: const AlwaysScrollableScrollPhysics(),
          children: [header(), const LoadingCardList(count: 3)],
        ),
        error: (e, _) => ListView(
          padding: _pad,
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            header(),
            const SizedBox(height: 24),
            ErrorView(
              message:
                  e is ApiException ? e.message : 'Could not load live events.',
              onRetry: () => ref.invalidate(ongoingEventsProvider),
            ),
          ],
        ),
        data: (events) {
          if (events.isEmpty) {
            return ListView(
              padding: _pad,
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                header(),
                const SizedBox(height: 48),
                const EmptyState(
                  icon: Icons.center_focus_strong_rounded,
                  title: 'No live events',
                  message:
                      'Check-in becomes available when an event is ongoing.',
                ),
              ],
            );
          }
          return ListView(
            padding: _pad,
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              header(),
              for (final e in events)
                Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                  child: EventCard(event: e, onTap: () => _open(context, e)),
                ),
            ],
          );
        },
      ),
    );
  }
}
