import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/event_location_map.dart';
import '../../../core/widgets/states.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../shared/models/event.dart';
import '../../../shared/utils/formatting.dart';
import '../../attendance/presentation/attendance_screen.dart';
import '../application/events_providers.dart';

class EventDetailScreen extends ConsumerWidget {
  const EventDetailScreen({super.key, required this.eventId});
  final int eventId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final eventAsync = ref.watch(eventDetailProvider(eventId));
    return AppScaffold(
      title: 'Event',
      body: eventAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: ErrorView(
            message:
                e is ApiException ? e.message : 'Could not load this event.',
            onRetry: () => ref.invalidate(eventDetailProvider(eventId)),
          ),
        ),
        data: (event) => _DetailBody(event: event),
      ),
    );
  }
}

class _DetailBody extends ConsumerWidget {
  const _DetailBody({required this.event});
  final AppEvent event;

  Future<void> _scan(BuildContext context) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => AttendanceScreen(event: event)),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final statusAsync = ref.watch(eventTimeStatusProvider(event.id));
    final location = event.location ?? event.venue;

    return ListView(
      padding: const EdgeInsets.fromLTRB(
          AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
      children: [
        Hero(
          tag: 'event-${event.id}',
          child: Material(
            type: MaterialType.transparency,
            child: AuraCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(event.name, style: textTheme.headlineMedium),
                  if (event.eventTypeName != null) ...[
                    const SizedBox(height: 4),
                    Text(event.eventTypeName!,
                        style: textTheme.bodyMedium
                            ?.copyWith(color: t.textSecondary)),
                  ],
                  const SizedBox(height: AppSpacing.x12),
                  StatusChip.forStatus(context, event.status),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: AppSpacing.x16),
        AuraCard(
          child: Column(
            children: [
              _InfoRow(
                  icon: Icons.calendar_today_rounded,
                  label: 'Date',
                  value: fmtFullDate(event.startDatetime)),
              const SizedBox(height: AppSpacing.x16),
              _InfoRow(
                  icon: Icons.schedule_rounded,
                  label: 'Time',
                  value: fmtDateRange(event.startDatetime, event.endDatetime)),
              if (location != null) ...[
                const SizedBox(height: AppSpacing.x16),
                _InfoRow(
                    icon: Icons.place_outlined,
                    label: 'Location',
                    value: location),
              ],
              if (event.geoRequired) ...[
                const SizedBox(height: AppSpacing.x16),
                const _InfoRow(
                    icon: Icons.my_location_rounded,
                    label: 'Geofence',
                    value: 'Location check required to attend'),
              ],
            ],
          ),
        ),
        if (event.hasGeo) ...[
          const SizedBox(height: AppSpacing.x16),
          EventLocationMap(
            lat: event.geoLatitude!,
            lng: event.geoLongitude!,
            radiusM: event.geoRadiusM ?? 100,
          ),
        ],
        if (event.description != null) ...[
          const SizedBox(height: AppSpacing.x16),
          AuraCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('About', style: textTheme.titleLarge),
                const SizedBox(height: AppSpacing.x8),
                Text(event.description!,
                    style:
                        textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
              ],
            ),
          ),
        ],
        const SizedBox(height: AppSpacing.x24),
        statusAsync.when(
          loading: () =>
              const AuraButton(label: 'Checking availability', loading: true),
          error: (e, _) => AuraButton(
              label: 'Scan to check in',
              icon: Icons.center_focus_strong_rounded,
              onPressed: () => _scan(context)),
          data: (st) =>
              _Cta(event: event, status: st, onScan: () => _scan(context)),
        ),
      ],
    );
  }
}

class _Cta extends StatelessWidget {
  const _Cta(
      {required this.event, required this.status, required this.onScan});
  final AppEvent event;
  final EventTimeStatus status;
  final VoidCallback onScan;

  @override
  Widget build(BuildContext context) {
    if (event.isCancelled) {
      return const AuraButton(
          label: 'Event cancelled',
          variant: AuraButtonVariant.tonal,
          onPressed: null);
    }
    if (status.checkInOpen) {
      return AuraButton(
          label: 'Scan to check in',
          icon: Icons.center_focus_strong_rounded,
          variant: AuraButtonVariant.success,
          onPressed: onScan);
    }
    if (status.signOutOpen) {
      return AuraButton(
          label: 'Scan to sign out',
          icon: Icons.logout_rounded,
          variant: AuraButtonVariant.destructive,
          onPressed: onScan);
    }
    final label = status.checkInOpensAt != null
        ? 'Check-in opens ${fmtTime(status.checkInOpensAt)}'
        : 'Check-in is closed';
    return AuraButton(
        label: label, variant: AuraButtonVariant.tonal, onPressed: null);
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow(
      {required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: t.textSecondary),
        const SizedBox(width: AppSpacing.x12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: textTheme.bodySmall?.copyWith(color: t.textMuted)),
              const SizedBox(height: 2),
              Text(value.isEmpty ? '—' : value, style: textTheme.bodyLarge),
            ],
          ),
        ),
      ],
    );
  }
}
