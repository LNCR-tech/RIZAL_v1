import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/admin.dart';
import '../application/admin_providers.dart';
import '../data/admin_repository.dart';

class AdminAccountsScreen extends ConsumerStatefulWidget {
  const AdminAccountsScreen({super.key});

  @override
  ConsumerState<AdminAccountsScreen> createState() =>
      _AdminAccountsScreenState();
}

class _AdminAccountsScreenState extends ConsumerState<AdminAccountsScreen> {
  final Set<int> _busy = {};

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x24, AppSpacing.x20, 120);

  Future<void> _toggle(SchoolItAccount a) async {
    setState(() => _busy.add(a.userId));
    try {
      await ref
          .read(adminRepositoryProvider)
          .updateAccountStatus(a.userId, !a.isActive);
      ref.invalidate(adminAccountsProvider);
    } on ApiException catch (e) {
      _snack(e.message);
    } finally {
      if (mounted) setState(() => _busy.remove(a.userId));
    }
  }

  Future<void> _reset(SchoolItAccount a) async {
    setState(() => _busy.add(a.userId));
    try {
      final pw =
          await ref.read(adminRepositoryProvider).resetAccountPassword(a.userId);
      if (mounted) _showPassword(a, pw);
    } on ApiException catch (e) {
      _snack(e.message);
    } finally {
      if (mounted) setState(() => _busy.remove(a.userId));
    }
  }

  void _snack(String msg) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
    }
  }

  void _showPassword(SchoolItAccount a, String? pw) {
    showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Temporary password'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(a.email ?? a.displayName),
            const SizedBox(height: AppSpacing.x12),
            SelectableText(pw ?? '(sent to the user)',
                style: Theme.of(context).textTheme.titleLarge),
          ],
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Done')),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final async = ref.watch(adminAccountsProvider);

    Widget header() => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Accounts', style: textTheme.displaySmall),
            Text('Campus administrators',
                style: textTheme.bodyLarge?.copyWith(color: t.textSecondary)),
            const SizedBox(height: AppSpacing.x16),
          ],
        );

    return RefreshIndicator(
      color: t.accent,
      backgroundColor: t.surface,
      onRefresh: () => ref.refresh(adminAccountsProvider.future),
      child: async.when(
        loading: () => ListView(
            padding: _pad,
            children: [header(), const LoadingCardList(count: 5)]),
        error: (e, _) => ListView(
          padding: _pad,
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            header(),
            ErrorView(
              message:
                  e is ApiException ? e.message : 'Could not load accounts.',
              onRetry: () => ref.invalidate(adminAccountsProvider),
            ),
          ],
        ),
        data: (accounts) => ListView(
          padding: _pad,
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            header(),
            if (accounts.isEmpty)
              const Padding(
                padding: EdgeInsets.only(top: 40),
                child: EmptyState(
                  icon: Icons.admin_panel_settings_outlined,
                  title: 'No campus admins',
                  message: 'Create a school to add its first campus admin.',
                ),
              )
            else
              for (final a in accounts)
                Padding(
                  key: ValueKey(a.userId),
                  padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                  child: AuraCard(
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(a.displayName, style: textTheme.titleLarge),
                              Text(
                                [
                                  if (a.email != null) a.email!,
                                  if (a.schoolName != null) a.schoolName!,
                                ].join(' · '),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: textTheme.bodySmall
                                    ?.copyWith(color: t.textSecondary),
                              ),
                            ],
                          ),
                        ),
                        if (_busy.contains(a.userId))
                          const SizedBox(
                              width: 24,
                              height: 24,
                              child: CircularProgressIndicator(strokeWidth: 2))
                        else ...[
                          IconButton(
                            tooltip: 'Reset password',
                            icon: Icon(Icons.key_rounded, color: t.textMuted),
                            onPressed: () => _reset(a),
                          ),
                          Switch(
                              value: a.isActive,
                              onChanged: (_) => _toggle(a)),
                        ],
                      ],
                    ),
                  ),
                ),
          ],
        ),
      ),
    );
  }
}
