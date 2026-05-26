import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/notification_item.dart';
import '../../../shared/utils/formatting.dart';
import '../../student/application/student_providers.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final async = ref.watch(notificationsProvider);

    return AppScaffold(
      title: 'Notifications',
      body: RefreshIndicator(
        color: t.accent,
        backgroundColor: t.surface,
        onRefresh: () => ref.refresh(notificationsProvider.future),
        child: async.when(
          loading: () => const Padding(
              padding: _pad, child: LoadingCardList(count: 5)),
          error: (e, _) => ListView(
            padding: _pad,
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              const SizedBox(height: 24),
              ErrorView(
                message: e is ApiException
                    ? e.message
                    : 'Could not load notifications.',
                onRetry: () => ref.invalidate(notificationsProvider),
              ),
            ],
          ),
          data: (items) {
            if (items.isEmpty) {
              return ListView(
                padding: _pad,
                physics: const AlwaysScrollableScrollPhysics(),
                children: const [
                  SizedBox(height: 60),
                  EmptyState(
                    icon: Icons.notifications_none_rounded,
                    title: 'No notifications',
                    message: "You're all caught up.",
                  ),
                ],
              );
            }
            return ListView.builder(
              padding: _pad,
              physics: const AlwaysScrollableScrollPhysics(),
              itemCount: items.length,
              itemBuilder: (context, i) => Padding(
                key: ValueKey(items[i].id),
                padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                child: _NotificationCard(item: items[i]),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _NotificationCard extends StatelessWidget {
  const _NotificationCard({required this.item});
  final NotificationItem item;

  IconData get _icon {
    final c = (item.category ?? '').toLowerCase();
    if (c.contains('late')) return Icons.schedule_rounded;
    if (c.contains('attendance') || c.contains('sign')) {
      return Icons.check_circle_rounded;
    }
    if (c.contains('security')) return Icons.shield_outlined;
    if (c.contains('missed') || c.contains('low')) {
      return Icons.warning_amber_rounded;
    }
    return Icons.notifications_rounded;
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AuraCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: t.surfaceAlt,
              borderRadius: BorderRadius.circular(AppRadii.control),
            ),
            child: Icon(_icon, size: 20, color: t.textSecondary),
          ),
          const SizedBox(width: AppSpacing.x12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Text(item.subject.isEmpty ? 'Notification' : item.subject,
                          style: textTheme.titleLarge),
                    ),
                    if (item.createdAt != null)
                      Text(fmtFullDate(item.createdAt),
                          style: textTheme.bodySmall
                              ?.copyWith(color: t.textMuted)),
                  ],
                ),
                if (item.message.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(item.message,
                      style: textTheme.bodyMedium
                          ?.copyWith(color: t.textSecondary)),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
