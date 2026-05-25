import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/states.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../shared/models/sanctions.dart';
import '../application/governance_providers.dart';
import '../data/sanctions_repository.dart';

class SanctionEventScreen extends ConsumerStatefulWidget {
  const SanctionEventScreen(
      {super.key, required this.eventId, required this.eventName});
  final int eventId;
  final String eventName;

  @override
  ConsumerState<SanctionEventScreen> createState() =>
      _SanctionEventScreenState();
}

class _SanctionEventScreenState extends ConsumerState<SanctionEventScreen> {
  final Set<int> _busy = {};

  Future<void> _approve(int userId) async {
    setState(() => _busy.add(userId));
    try {
      await ref
          .read(sanctionsRepositoryProvider)
          .approve(widget.eventId, userId);
      ref.invalidate(sanctionEventStudentsProvider(widget.eventId));
      ref.invalidate(sanctionsDashboardProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Compliance approved.')));
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Could not approve. Try again.')));
      }
    } finally {
      if (mounted) setState(() => _busy.remove(userId));
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final async = ref.watch(sanctionEventStudentsProvider(widget.eventId));

    return AppScaffold(
      title: widget.eventName,
      body: RefreshIndicator(
        color: t.accent,
        backgroundColor: t.surface,
        onRefresh: () =>
            ref.refresh(sanctionEventStudentsProvider(widget.eventId).future),
        child: async.when(
          loading: () => const Padding(
              padding: EdgeInsets.all(AppSpacing.x20),
              child: LoadingCardList(count: 4)),
          error: (e, _) => ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(AppSpacing.x20),
            children: [
              const SizedBox(height: 24),
              ErrorView(
                message: e is ApiException
                    ? e.message
                    : 'Could not load sanctioned students.',
                onRetry: () =>
                    ref.invalidate(sanctionEventStudentsProvider(widget.eventId)),
              ),
            ],
          ),
          data: (page) {
            if (page.items.isEmpty) {
              return ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(AppSpacing.x20),
                children: const [
                  SizedBox(height: 60),
                  EmptyState(
                    icon: Icons.verified_outlined,
                    title: 'No sanctioned students',
                    message: 'No one needs sanction review for this event.',
                  ),
                ],
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(AppSpacing.x20),
              itemCount: page.items.length,
              itemBuilder: (context, i) {
                final r = page.items[i];
                return Padding(
                  key: ValueKey(r.id),
                  padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                  child: _SanctionCard(
                    record: r,
                    busy: r.student?.userId != null &&
                        _busy.contains(r.student!.userId),
                    onApprove: r.status == 'pending' && r.student?.userId != null
                        ? () => _approve(r.student!.userId!)
                        : null,
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

class _SanctionCard extends StatelessWidget {
  const _SanctionCard(
      {required this.record, required this.busy, this.onApprove});
  final SanctionRecord record;
  final bool busy;
  final VoidCallback? onApprove;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final student = record.student;

    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(student?.displayName ?? 'Student',
                        style: textTheme.titleLarge),
                    if (student?.programName != null)
                      Text(student!.programName!,
                          style: textTheme.bodySmall
                              ?.copyWith(color: t.textSecondary)),
                  ],
                ),
              ),
              StatusChip.forStatus(context, record.status),
            ],
          ),
          if (record.items.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x12),
            for (final item in record.items)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  children: [
                    Icon(
                        item.status == 'complied'
                            ? Icons.check_circle_rounded
                            : Icons.radio_button_unchecked_rounded,
                        size: 16,
                        color: item.status == 'complied'
                            ? t.present
                            : t.textMuted),
                    const SizedBox(width: AppSpacing.x8),
                    Expanded(
                        child: Text(item.itemName,
                            style: textTheme.bodyMedium)),
                  ],
                ),
              ),
          ],
          if (onApprove != null) ...[
            const SizedBox(height: AppSpacing.x16),
            AuraButton(
              label: 'Approve compliance',
              icon: Icons.check_rounded,
              variant: AuraButtonVariant.tonal,
              loading: busy,
              onPressed: onApprove,
            ),
          ],
        ],
      ),
    );
  }
}
