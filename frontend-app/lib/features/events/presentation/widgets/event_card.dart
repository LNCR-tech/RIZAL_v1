import 'package:flutter/material.dart';

import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_tokens.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/widgets/aura_card.dart';
import '../../../../core/widgets/status_chip.dart';
import '../../../../shared/models/event.dart';
import '../../../../shared/utils/formatting.dart';

class EventCard extends StatelessWidget {
  const EventCard({super.key, required this.event, this.onTap});
  final AppEvent event;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final location = event.location ?? event.venue;

    return AuraCard(
      onTap: onTap,
      heroTag: 'event-${event.id}',
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _DateBadge(date: event.startDatetime),
          const SizedBox(width: AppSpacing.x16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(event.name,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: textTheme.titleLarge),
                const SizedBox(height: 6),
                _MetaRow(
                    icon: Icons.schedule_rounded,
                    text: fmtDateRange(event.startDatetime, event.endDatetime)),
                if (location != null) ...[
                  const SizedBox(height: 2),
                  _MetaRow(icon: Icons.place_outlined, text: location),
                ],
                const SizedBox(height: AppSpacing.x12),
                StatusChip.forStatus(context, event.status),
              ],
            ),
          ),
          Icon(Icons.chevron_right_rounded, color: t.textMuted),
        ],
      ),
    );
  }
}

class _DateBadge extends StatelessWidget {
  const _DateBadge({this.date});
  final DateTime? date;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Container(
      width: 54,
      height: 60,
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: BorderRadius.circular(AppRadii.control),
      ),
      child: date == null
          ? Icon(Icons.event_rounded, color: t.textSecondary)
          : Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(dayNumber(date!),
                    style: AppTypography.mono(
                        size: 22, weight: FontWeight.w700, color: t.ink)),
                Text(monthShort(date!),
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: t.textSecondary, letterSpacing: 1)),
              ],
            ),
    );
  }
}

class _MetaRow extends StatelessWidget {
  const _MetaRow({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Row(
      children: [
        Icon(icon, size: 14, color: t.textMuted),
        const SizedBox(width: 6),
        Expanded(
          child: Text(text,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context)
                  .textTheme
                  .bodySmall
                  ?.copyWith(color: t.textSecondary)),
        ),
      ],
    );
  }
}
