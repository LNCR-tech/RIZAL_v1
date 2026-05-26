import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/rise_in.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/sanctions.dart';
import '../../governance/application/governance_providers.dart';

/// Student-facing "My sanctions" screen.
///
/// Surfaces the data exposed by `GET /api/sanctions/students/me` — every
/// sanction record (one per event) the signed-in student currently has,
/// with the per-record items (per-officer-defined penalties) and their
/// individual statuses.
///
/// Design (emil + ui-ux-pro-max + frontend-design):
///   • Editorial Manrope display headline + body. No emoji icons —
///     Material rounded throughout, status uses colour + icon.
///   • Two summary chips ("Pending" / "Cleared") top the screen so the
///     student knows where they stand at a glance.
///   • An optional clearance-deadline banner appears when the school has
///     declared one — colour intensifies as the deadline approaches.
///   • Each record renders as a single AuraCard with a coloured status
///     bar at the top — pending = tardy/amber, cleared = present/green.
///   • Item rows are quietly indented with mono numbers; pending items
///     show a checkbox shape (unchecked), cleared items show a filled
///     check + cleared-at timestamp.
///   • Stagger entrance reuses [staggered] (50ms, ease-out, reduced-motion
///     honoured). All colours from [AppTokens] — nothing hardcoded.
class MySanctionsScreen extends ConsumerWidget {
  const MySanctionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final recordsAsync = ref.watch(mySanctionsProvider);
    final deadlineAsync = ref.watch(activeClearanceDeadlineProvider);

    return AppScaffold(
      title: 'My sanctions',
      onRefresh: () async {
        ref.invalidate(mySanctionsProvider);
        ref.invalidate(activeClearanceDeadlineProvider);
        await ref.read(mySanctionsProvider.future);
      },
      body: recordsAsync.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(AppSpacing.x20),
          child: LoadingCardList(count: 4),
        ),
        error: (e, _) => ListView(
          padding: const EdgeInsets.all(AppSpacing.x20),
          children: [
            const SizedBox(height: 24),
            ErrorView(
              message: e is ApiException
                  ? e.message
                  : 'Could not load your sanctions.',
              onRetry: () => ref.invalidate(mySanctionsProvider),
            ),
          ],
        ),
        data: (records) => ListView(
          padding: const EdgeInsets.fromLTRB(
              AppSpacing.x20, AppSpacing.x16, AppSpacing.x20, 140),
          children: staggered([
            _IntroHeader(records: records),
            const SizedBox(height: AppSpacing.x20),
            _SummaryRow(records: records),
            const SizedBox(height: AppSpacing.x16),
            ...switch (deadlineAsync) {
              AsyncData(:final value) when value != null && value.isUpcoming =>
                [
                  _DeadlineBanner(deadline: value),
                  const SizedBox(height: AppSpacing.x16),
                ],
              _ => const <Widget>[SizedBox.shrink()],
            },
            if (records.isEmpty)
              Padding(
                padding: const EdgeInsets.only(top: AppSpacing.x24),
                child: AuraCard(
                  child: Column(
                    children: [
                      Container(
                        width: 56,
                        height: 56,
                        decoration: BoxDecoration(
                          color: t.present.withOpacity(0.14),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(Icons.check_circle_rounded,
                            color: t.present, size: 30),
                      ),
                      const SizedBox(height: AppSpacing.x16),
                      Text('All clear',
                          style: textTheme.titleLarge,
                          textAlign: TextAlign.center),
                      const SizedBox(height: AppSpacing.x8),
                      Text(
                        'No outstanding sanctions. Keep attending events on time to stay clear.',
                        style: textTheme.bodyMedium
                            ?.copyWith(color: t.textSecondary),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              )
            else ...[
              for (final r in records) ...[
                _SanctionCard(record: r),
                const SizedBox(height: AppSpacing.x12),
              ],
            ],
          ]),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Intro + summary
// ─────────────────────────────────────────────────────────────────────────────

class _IntroHeader extends StatelessWidget {
  const _IntroHeader({required this.records});
  final List<SanctionRecord> records;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final pending = records.where((r) => r.status == 'pending').length;
    final subtitle = pending == 0
        ? 'You\'re clear for now — nothing pending.'
        : pending == 1
            ? '1 sanction needs your attention.'
            : '$pending sanctions need your attention.';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('My sanctions', style: textTheme.displaySmall),
        const SizedBox(height: AppSpacing.x8),
        Text(subtitle,
            style: textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
      ],
    );
  }
}

class _SummaryRow extends StatelessWidget {
  const _SummaryRow({required this.records});
  final List<SanctionRecord> records;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final pending = records.where((r) => r.status == 'pending').length;
    final complied = records.where((r) => r.status == 'complied').length;
    return Row(
      children: [
        Expanded(
          child: _SummaryChip(
            label: 'Pending',
            value: pending,
            color: t.tardy,
            icon: Icons.hourglass_top_rounded,
          ),
        ),
        const SizedBox(width: AppSpacing.x12),
        Expanded(
          child: _SummaryChip(
            label: 'Cleared',
            value: complied,
            color: t.present,
            icon: Icons.task_alt_rounded,
          ),
        ),
      ],
    );
  }
}

class _SummaryChip extends StatelessWidget {
  const _SummaryChip({
    required this.label,
    required this.value,
    required this.color,
    required this.icon,
  });
  final String label;
  final int value;
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AuraCard(
      padding: const EdgeInsets.all(AppSpacing.x16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 30,
                height: 30,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.14),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: color, size: 18),
              ),
              const Spacer(),
              Text(
                '$value',
                style: AppTypography.mono(
                  size: 26,
                  weight: FontWeight.w800,
                  color: t.ink,
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.x8),
          Text(label,
              style:
                  textTheme.labelMedium?.copyWith(color: t.textSecondary)),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Clearance-deadline banner
// ─────────────────────────────────────────────────────────────────────────────

class _DeadlineBanner extends StatelessWidget {
  const _DeadlineBanner({required this.deadline});
  final ClearanceDeadline deadline;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final hoursLeft = deadline.hoursRemaining;
    // Heat the banner as the deadline approaches: >72h muted, 24-72h tardy,
    // <24h absent (red).
    final Color tone;
    final String urgency;
    if (hoursLeft >= 72) {
      tone = t.textSecondary;
      urgency = 'Heads up';
    } else if (hoursLeft >= 24) {
      tone = t.tardy;
      urgency = 'Closing soon';
    } else {
      tone = t.absent;
      urgency = 'Deadline today';
    }
    final df = DateFormat('EEE d MMM · h:mm a');
    return AuraCard(
      color: tone.withOpacity(0.08),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: tone.withOpacity(0.18),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(Icons.event_busy_rounded, color: tone, size: 20),
          ),
          const SizedBox(width: AppSpacing.x12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  urgency.toUpperCase(),
                  style: textTheme.labelSmall?.copyWith(
                    color: tone,
                    letterSpacing: 0.8,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 2),
                Text('Clearance deadline ${df.format(deadline.deadlineAt)}',
                    style: textTheme.titleMedium),
                if (deadline.message != null && deadline.message!.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      deadline.message!,
                      style: textTheme.bodySmall
                          ?.copyWith(color: t.textSecondary, height: 1.45),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Sanction record card
// ─────────────────────────────────────────────────────────────────────────────

class _SanctionCard extends StatelessWidget {
  const _SanctionCard({required this.record});
  final SanctionRecord record;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final cleared = record.status == 'complied';
    final accent = cleared ? t.present : t.tardy;
    final df = DateFormat('EEE d MMM');

    return AuraCard(
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Status bar at top — instantly readable colour signal.
          Container(
            height: 4,
            decoration: BoxDecoration(
              color: accent,
              borderRadius: const BorderRadius.vertical(
                top: Radius.circular(AppRadii.card),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(AppSpacing.x16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        record.eventId == null
                            ? 'Event'
                            : 'Event #${record.eventId}',
                        style: textTheme.titleLarge,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.x8),
                    _StatusPill(cleared: cleared, color: accent),
                  ],
                ),
                if (record.compliedAt != null) ...[
                  const SizedBox(height: 6),
                  Text(
                    'Cleared on ${df.format(record.compliedAt!)}',
                    style: textTheme.bodySmall
                        ?.copyWith(color: t.textSecondary),
                  ),
                ],
                if (record.items.isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.x16),
                  Divider(height: 1, thickness: 1, color: t.border),
                  const SizedBox(height: AppSpacing.x16),
                  Text(
                    'PENALTIES',
                    style: textTheme.labelSmall?.copyWith(
                      color: t.textMuted,
                      letterSpacing: 0.8,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.x8),
                  for (var i = 0; i < record.items.length; i++) ...[
                    if (i != 0) const SizedBox(height: AppSpacing.x12),
                    _ItemRow(item: record.items[i], number: i + 1),
                  ],
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.cleared, required this.color});
  final bool cleared;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: AppSpacing.x12, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.14),
        borderRadius: AppRadii.rPill,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            cleared
                ? Icons.check_circle_rounded
                : Icons.hourglass_top_rounded,
            size: 14,
            color: color,
          ),
          const SizedBox(width: 6),
          Text(
            cleared ? 'Cleared' : 'Pending',
            style: textTheme.labelMedium?.copyWith(
              color: color,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

class _ItemRow extends StatelessWidget {
  const _ItemRow({required this.item, required this.number});
  final SanctionItem item;
  final int number;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final cleared = item.status == 'complied';
    final tone = cleared ? t.present : t.tardy;
    final df = DateFormat('d MMM h:mm a');

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Numbered tile mirrors Help Center step style.
        Container(
          width: 26,
          height: 26,
          decoration: BoxDecoration(
            color: tone.withOpacity(0.14),
            borderRadius: BorderRadius.circular(8),
          ),
          alignment: Alignment.center,
          child: cleared
              ? Icon(Icons.check_rounded, color: tone, size: 16)
              : Text(
                  '$number',
                  style: AppTypography.mono(
                    size: 12,
                    weight: FontWeight.w800,
                    color: tone,
                  ),
                ),
        ),
        const SizedBox(width: AppSpacing.x12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                item.itemName,
                style: textTheme.bodyLarge?.copyWith(
                  decoration:
                      cleared ? TextDecoration.lineThrough : null,
                  color: cleared ? t.textMuted : t.ink,
                ),
              ),
              if (item.itemDescription != null &&
                  item.itemDescription!.isNotEmpty) ...[
                const SizedBox(height: 2),
                Text(
                  item.itemDescription!,
                  style: textTheme.bodySmall?.copyWith(
                    color: t.textSecondary,
                    height: 1.45,
                  ),
                ),
              ],
              if (cleared && item.compliedAt != null) ...[
                const SizedBox(height: 4),
                Text(
                  'Cleared ${df.format(item.compliedAt!)}',
                  style: textTheme.labelSmall
                      ?.copyWith(color: t.textMuted, letterSpacing: 0.2),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}
