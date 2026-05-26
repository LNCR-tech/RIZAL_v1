import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/section_header.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/utils/formatting.dart';
import '../data/security_repository.dart';

/// Active sessions (devices) + recent sign-ins. All actions are self-service.
class SecurityScreen extends ConsumerStatefulWidget {
  const SecurityScreen({super.key});

  @override
  ConsumerState<SecurityScreen> createState() => _SecurityScreenState();
}

class _SecurityScreenState extends ConsumerState<SecurityScreen> {
  final Set<String> _revoking = {};
  bool _busyOthers = false;

  void _snack(String m) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(m)));
    }
  }

  String _device(String? ua) {
    final s = (ua ?? '').toLowerCase();
    if (s.contains('iphone')) return 'iPhone';
    if (s.contains('ipad')) return 'iPad';
    if (s.contains('android')) return 'Android device';
    if (s.contains('windows')) return 'Windows';
    if (s.contains('mac')) return 'Mac';
    if (s.contains('chrome')) return 'Chrome';
    if (s.contains('safari')) return 'Safari';
    return ua == null || ua.isEmpty ? 'Unknown device' : 'Browser';
  }

  Future<void> _revoke(String id) async {
    setState(() => _revoking.add(id));
    try {
      await ref.read(securityRepositoryProvider).revokeSession(id);
      ref.invalidate(sessionsProvider);
    } on ApiException catch (e) {
      _snack(e.message);
    } finally {
      if (mounted) setState(() => _revoking.remove(id));
    }
  }

  Future<void> _revokeOthers() async {
    setState(() => _busyOthers = true);
    try {
      final n = await ref.read(securityRepositoryProvider).revokeOthers();
      ref.invalidate(sessionsProvider);
      _snack(n > 0 ? 'Signed out $n other device${n == 1 ? '' : 's'}.' : 'No other sessions.');
    } on ApiException catch (e) {
      _snack(e.message);
    } finally {
      if (mounted) setState(() => _busyOthers = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final sessionsAsync = ref.watch(sessionsProvider);
    final historyAsync = ref.watch(loginHistoryProvider);

    return AppScaffold(
      title: 'Sign-in & devices',
      body: RefreshIndicator(
        color: t.accent,
        backgroundColor: t.surface,
        onRefresh: () async {
          ref.invalidate(sessionsProvider);
          ref.invalidate(loginHistoryProvider);
          await ref.read(sessionsProvider.future);
        },
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
              AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            const SectionHeader(title: 'Active sessions'),
            sessionsAsync.when(
              loading: () => const LoadingCardList(count: 2),
              error: (e, _) => ErrorView(
                message: e is ApiException ? e.message : 'Could not load sessions.',
                onRetry: () => ref.invalidate(sessionsProvider),
              ),
              data: (sessions) {
                final active = sessions.where((s) => s.isActive).toList();
                return Column(
                  children: [
                    for (final s in active)
                      Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                        child: AuraCard(
                          child: Row(
                            children: [
                              Icon(
                                  s.isCurrent
                                      ? Icons.smartphone_rounded
                                      : Icons.devices_rounded,
                                  color: s.isCurrent ? t.present : t.textSecondary),
                              const SizedBox(width: AppSpacing.x12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(_device(s.userAgent),
                                        style: textTheme.titleLarge),
                                    Text(
                                      [
                                        if (s.ipAddress != null) s.ipAddress!,
                                        if (s.lastSeenAt != null)
                                          'seen ${fmtFullDate(s.lastSeenAt)}',
                                      ].join(' · '),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: AppTypography.mono(
                                          size: 12, color: t.textSecondary),
                                    ),
                                  ],
                                ),
                              ),
                              if (s.isCurrent)
                                _Pill('This device', t.present)
                              else if (_revoking.contains(s.id))
                                const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2))
                              else
                                TextButton(
                                  onPressed: () => _revoke(s.id),
                                  child: Text('Revoke',
                                      style: TextStyle(color: t.absent)),
                                ),
                            ],
                          ),
                        ),
                      ),
                    const SizedBox(height: AppSpacing.x8),
                    AuraButton(
                      label: 'Sign out other devices',
                      variant: AuraButtonVariant.tonal,
                      loading: _busyOthers,
                      onPressed: _revokeOthers,
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: AppSpacing.x24),
            const SectionHeader(title: 'Recent sign-ins'),
            historyAsync.when(
              loading: () => const LoadingCardList(count: 3),
              error: (_, __) => Text('Could not load history.',
                  style: textTheme.bodySmall?.copyWith(color: t.textMuted)),
              data: (items) => Column(
                children: [
                  for (final h in items.take(20))
                    Padding(
                      padding: const EdgeInsets.only(bottom: AppSpacing.x8),
                      child: AuraCard(
                        padding: const EdgeInsets.all(AppSpacing.x12),
                        child: Row(
                          children: [
                            Icon(
                                h.success
                                    ? Icons.check_circle_rounded
                                    : Icons.cancel_rounded,
                                size: 18,
                                color: h.success ? t.present : t.absent),
                            const SizedBox(width: AppSpacing.x12),
                            Expanded(
                              child: Text(
                                [
                                  h.success ? 'Signed in' : 'Failed',
                                  if (h.authMethod != null) h.authMethod!,
                                  if (!h.success && h.failureReason != null)
                                    h.failureReason!,
                                ].join(' · '),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: textTheme.bodyMedium,
                              ),
                            ),
                            if (h.createdAt != null)
                              Text(fmtFullDate(h.createdAt),
                                  style: AppTypography.mono(
                                      size: 11, color: t.textMuted)),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill(this.label, this.color);
  final String label;
  final Color color;
  @override
  Widget build(BuildContext context) {
    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: AppSpacing.x12, vertical: 4),
      decoration: BoxDecoration(
          color: color.withOpacity(0.14),
          borderRadius: BorderRadius.circular(AppRadii.pill)),
      child: Text(label,
          style: Theme.of(context)
              .textTheme
              .labelMedium
              ?.copyWith(color: color)),
    );
  }
}
