import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/public_attendance.dart';
import '../application/gather_providers.dart';
import 'gather_scan_screen.dart';

/// Kiosk entry: discover nearby events, then start a multi-face check-in.
class GatherScreen extends ConsumerWidget {
  const GatherScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40);

  void _open(BuildContext context, NearbyEvent event, int cooldown) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) =>
          GatherScanScreen(event: event, cooldownSeconds: cooldown),
    ));
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final async = ref.watch(gatherNearbyProvider);

    return AppScaffold(
      title: 'Gather',
      body: RefreshIndicator(
        color: t.accent,
        backgroundColor: t.surface,
        onRefresh: () => ref.refresh(gatherNearbyProvider.future),
        child: async.when(
          loading: () =>
              const Padding(padding: _pad, child: LoadingCardList(count: 3)),
          error: (e, _) => ListView(
            padding: _pad,
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              const SizedBox(height: 24),
              ErrorView(
                message: e is ApiException
                    ? e.message
                    : 'Could not find nearby events.',
                onRetry: () => ref.invalidate(gatherNearbyProvider),
              ),
            ],
          ),
          data: (res) {
            if (res.events.isEmpty) {
              return ListView(
                padding: _pad,
                physics: const AlwaysScrollableScrollPhysics(),
                children: const [
                  SizedBox(height: 48),
                  EmptyState(
                    icon: Icons.groups_rounded,
                    title: 'No nearby events',
                    message:
                        "Stand within an event's location to start a gather session.",
                  ),
                ],
              );
            }
            return ListView(
              padding: _pad,
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.x16),
                  child: Text(
                    'Pick an event, then point the camera at students to record attendance.',
                    style: textTheme.bodyMedium
                        ?.copyWith(color: t.textSecondary),
                  ),
                ),
                for (final e in res.events)
                  Padding(
                    padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                    child: _NearbyCard(
                        event: e,
                        onTap: () => _open(context, e, res.cooldownSeconds)),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _NearbyCard extends StatelessWidget {
  const _NearbyCard({required this.event, required this.onTap});
  final NearbyEvent event;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final phase = event.isSignOut ? 'Sign out' : 'Sign in';

    return AuraCard(
      onTap: onTap,
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: t.surfaceAlt,
              borderRadius: BorderRadius.circular(AppRadii.control),
            ),
            child: Icon(Icons.center_focus_strong_rounded,
                color: t.textSecondary),
          ),
          const SizedBox(width: AppSpacing.x16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(event.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: textTheme.titleLarge),
                if (event.location != null)
                  Text(event.location!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: textTheme.bodySmall
                          ?.copyWith(color: t.textSecondary)),
                const SizedBox(height: 6),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.x8, vertical: 2),
                      decoration: BoxDecoration(
                        color: t.accent.withOpacity(0.16),
                        borderRadius: BorderRadius.circular(AppRadii.pill),
                      ),
                      child: Text(phase,
                          style: textTheme.bodySmall
                              ?.copyWith(color: t.ink)),
                    ),
                    if (event.distanceM != null) ...[
                      const SizedBox(width: AppSpacing.x8),
                      Text('${event.distanceM!.round()} m away',
                          style: textTheme.bodySmall
                              ?.copyWith(color: t.textMuted)),
                    ],
                  ],
                ),
              ],
            ),
          ),
          Icon(Icons.chevron_right_rounded, color: t.textMuted),
        ],
      ),
    );
  }
}
