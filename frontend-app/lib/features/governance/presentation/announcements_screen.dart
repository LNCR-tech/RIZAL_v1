import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/utils/formatting.dart';
import '../application/governance_providers.dart';
import '../data/governance_repository.dart';

class AnnouncementsScreen extends ConsumerWidget {
  const AnnouncementsScreen(
      {super.key, required this.unitId, this.canManage = false});
  final int unitId;
  final bool canManage;

  Future<void> _create(BuildContext context) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _AnnouncementForm(unitId: unitId),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final async = ref.watch(announcementsProvider(unitId));

    return AppScaffold(
      title: 'Announcements',
      actions: [
        if (canManage)
          IconButton(
            tooltip: 'New announcement',
            icon: const Icon(Icons.add_rounded),
            onPressed: () => _create(context),
          ),
      ],
      body: RefreshIndicator(
        color: t.accent,
        backgroundColor: t.surface,
        onRefresh: () => ref.refresh(announcementsProvider(unitId).future),
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
                    : 'Could not load announcements.',
                onRetry: () => ref.invalidate(announcementsProvider(unitId)),
              ),
            ],
          ),
          data: (items) {
            if (items.isEmpty) {
              return ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(AppSpacing.x20),
                children: const [
                  SizedBox(height: 60),
                  EmptyState(
                    icon: Icons.campaign_outlined,
                    title: 'No announcements',
                    message: 'Posts to this unit will appear here.',
                  ),
                ],
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(AppSpacing.x20),
              itemCount: items.length,
              itemBuilder: (context, i) {
                final a = items[i];
                final textTheme = Theme.of(context).textTheme;
                return Padding(
                  key: ValueKey(a.id),
                  padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                  child: AuraCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                                child: Text(a.title,
                                    style: textTheme.titleLarge)),
                            if (a.status != 'published')
                              Text(a.status,
                                  style: textTheme.bodySmall
                                      ?.copyWith(color: t.textMuted)),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(a.body,
                            style: textTheme.bodyMedium
                                ?.copyWith(color: t.textSecondary)),
                        const SizedBox(height: AppSpacing.x8),
                        Text(
                          [
                            if (a.authorName != null) a.authorName!,
                            if (a.updatedAt != null) fmtFullDate(a.updatedAt),
                          ].join(' · '),
                          style: textTheme.bodySmall
                              ?.copyWith(color: t.textMuted),
                        ),
                      ],
                    ),
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

class _AnnouncementForm extends ConsumerStatefulWidget {
  const _AnnouncementForm({required this.unitId});
  final int unitId;

  @override
  ConsumerState<_AnnouncementForm> createState() => _AnnouncementFormState();
}

class _AnnouncementFormState extends ConsumerState<_AnnouncementForm> {
  final _title = TextEditingController();
  final _body = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _title.dispose();
    _body.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_title.text.trim().isEmpty || _body.text.trim().isEmpty) {
      setState(() => _error = 'Add a title and a message.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(governanceRepositoryProvider).createAnnouncement(
            widget.unitId,
            title: _title.text.trim(),
            body: _body.text.trim(),
          );
      ref.invalidate(announcementsProvider(widget.unitId));
      ref.invalidate(dashboardOverviewProvider(widget.unitId));
      if (mounted) Navigator.of(context).pop();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not post. Please try again.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        decoration:
            BoxDecoration(color: t.surface, borderRadius: AppRadii.rSheet),
        padding: EdgeInsets.fromLTRB(AppSpacing.x24, AppSpacing.x16,
            AppSpacing.x24, AppSpacing.x24 + MediaQuery.of(context).padding.bottom),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                      color: t.border,
                      borderRadius: BorderRadius.circular(2))),
            ),
            const SizedBox(height: AppSpacing.x20),
            Text('New announcement', style: textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.x20),
            AuraTextField(label: 'Title', controller: _title),
            const SizedBox(height: AppSpacing.x16),
            AuraTextField(
                label: 'Message',
                controller: _body,
                hint: 'Write your announcement…'),
            if (_error != null) ...[
              const SizedBox(height: AppSpacing.x12),
              Text(_error!,
                  style: textTheme.bodySmall?.copyWith(color: t.absent)),
            ],
            const SizedBox(height: AppSpacing.x24),
            AuraButton(label: 'Post', loading: _busy, onPressed: _submit),
          ],
        ),
      ),
    );
  }
}
