import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/utils/formatting.dart';
import '../application/admin_providers.dart';

class AdminLogsScreen extends ConsumerStatefulWidget {
  const AdminLogsScreen({super.key});

  @override
  ConsumerState<AdminLogsScreen> createState() => _AdminLogsScreenState();
}

class _AdminLogsScreenState extends ConsumerState<AdminLogsScreen> {
  final _query = TextEditingController();
  int _tab = 0; // 0 = audit, 1 = notifications
  String _q = '';
  String _status = '';

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x24, AppSpacing.x20, 120);

  @override
  void dispose() {
    _query.dispose();
    super.dispose();
  }

  List<String> get _statusOptions =>
      _tab == 0 ? const ['', 'success', 'failed'] : const ['', 'sent', 'failed', 'queued'];

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    final header = <Widget>[
      Text('Logs', style: textTheme.displaySmall),
      const SizedBox(height: AppSpacing.x16),
      SizedBox(
        width: double.infinity,
        child: SegmentedButton<int>(
          segments: const [
            ButtonSegment(value: 0, label: Text('Audit')),
            ButtonSegment(value: 1, label: Text('Notifications')),
          ],
          selected: {_tab},
          showSelectedIcon: false,
          onSelectionChanged: (s) => setState(() {
            _tab = s.first;
            _status = '';
          }),
        ),
      ),
      const SizedBox(height: AppSpacing.x12),
      if (_tab == 0)
        TextField(
          controller: _query,
          textInputAction: TextInputAction.search,
          onSubmitted: (v) => setState(() => _q = v.trim()),
          decoration: const InputDecoration(
            hintText: 'Search actions, details…',
            prefixIcon: Icon(Icons.search_rounded, size: 20),
          ),
        ),
      const SizedBox(height: AppSpacing.x12),
      Wrap(
        spacing: AppSpacing.x8,
        children: [
          for (final opt in _statusOptions)
            ChoiceChip(
              label: Text(opt.isEmpty ? 'All' : opt),
              selected: _status == opt,
              onSelected: (_) => setState(() => _status = opt),
            ),
        ],
      ),
      const SizedBox(height: AppSpacing.x16),
    ];

    return RefreshIndicator(
      color: t.accent,
      backgroundColor: t.surface,
      onRefresh: () async {
        if (_tab == 0) {
          ref.invalidate(auditLogsProvider((q: _q, status: _status)));
        } else {
          ref.invalidate(notificationLogsProvider(_status));
        }
      },
      child: _tab == 0 ? _auditList(header) : _notifList(header),
    );
  }

  Widget _auditList(List<Widget> header) {
    final async = ref.watch(auditLogsProvider((q: _q, status: _status)));
    return ListView(
      padding: _pad,
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        ...header,
        ...async.when(
          loading: () => [const LoadingCardList(count: 6)],
          error: (e, _) => [
            ErrorView(
              message: e is ApiException ? e.message : 'Could not load logs.',
              onRetry: () =>
                  ref.invalidate(auditLogsProvider((q: _q, status: _status))),
            ),
          ],
          data: (page) => page.items.isEmpty
              ? [
                  const Padding(
                    padding: EdgeInsets.only(top: 40),
                    child: EmptyState(
                      icon: Icons.history_rounded,
                      title: 'No audit logs',
                      message: 'Nothing matches these filters.',
                    ),
                  )
                ]
              : [
                  for (final a in page.items)
                    Padding(
                      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                      child: _LogTile(
                        title: a.action.isEmpty ? 'event' : a.action,
                        subtitle: [
                          if (a.schoolId != null) 'school ${a.schoolId}',
                          if (a.actorUserId != null) 'by #${a.actorUserId}',
                          if (a.createdAt != null) fmtFullDate(a.createdAt),
                        ].join(' · '),
                        status: a.status,
                        details: a.details,
                      ),
                    ),
                ],
        ),
      ],
    );
  }

  Widget _notifList(List<Widget> header) {
    final async = ref.watch(notificationLogsProvider(_status));
    return ListView(
      padding: _pad,
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        ...header,
        ...async.when(
          loading: () => [const LoadingCardList(count: 6)],
          error: (e, _) => [
            ErrorView(
              message: e is ApiException ? e.message : 'Could not load logs.',
              onRetry: () => ref.invalidate(notificationLogsProvider(_status)),
            ),
          ],
          data: (items) => items.isEmpty
              ? [
                  const Padding(
                    padding: EdgeInsets.only(top: 40),
                    child: EmptyState(
                      icon: Icons.notifications_off_rounded,
                      title: 'No notifications',
                      message: 'Nothing matches these filters.',
                    ),
                  )
                ]
              : [
                  for (final n in items)
                    Padding(
                      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                      child: _LogTile(
                        title: (n.subject?.isNotEmpty ?? false)
                            ? n.subject!
                            : (n.category.isEmpty ? 'notification' : n.category),
                        subtitle: [
                          n.channel,
                          if (n.schoolId != null) 'school ${n.schoolId}',
                          if (n.createdAt != null) fmtFullDate(n.createdAt),
                        ].where((e) => e.isNotEmpty).join(' · '),
                        status: n.status,
                        details: n.message,
                      ),
                    ),
                ],
        ),
      ],
    );
  }
}

class _LogTile extends StatelessWidget {
  const _LogTile({
    required this.title,
    required this.subtitle,
    required this.status,
    this.details,
  });
  final String title;
  final String subtitle;
  final String status;
  final String? details;

  Color _statusColor(AppTokens t) {
    switch (status.toLowerCase()) {
      case 'success':
      case 'sent':
      case 'delivered':
        return t.present;
      case 'failed':
      case 'error':
        return t.absent;
      case 'queued':
      case 'pending':
        return t.tardy;
      default:
        return t.textMuted;
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final color = _statusColor(t);
    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: textTheme.titleLarge),
              ),
              if (status.isNotEmpty)
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.x12, vertical: 4),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.14),
                    borderRadius: BorderRadius.circular(AppRadii.pill),
                  ),
                  child: Text(status,
                      style: textTheme.labelMedium?.copyWith(color: color)),
                ),
            ],
          ),
          const SizedBox(height: 4),
          Text(subtitle,
              style: AppTypography.mono(size: 12, color: t.textSecondary)),
          if (details != null && details!.trim().isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(details!,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: textTheme.bodySmall?.copyWith(color: t.textMuted)),
          ],
        ],
      ),
    );
  }
}
