import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/school_badge.dart';
import '../../../core/widgets/states.dart';
import '../application/student_providers.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final meta = ref.watch(sessionControllerProvider).meta;
    final async = ref.watch(myProfileProvider);

    return AppScaffold(
      title: 'Profile',
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: ErrorView(
            message: e is ApiException ? e.message : 'Could not load profile.',
            onRetry: () => ref.invalidate(myProfileProvider),
          ),
        ),
        data: (u) {
          final sp = u.studentProfile;
          return ListView(
            padding: const EdgeInsets.fromLTRB(
                AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
            children: [
              Center(
                child: Column(
                  children: [
                    CircleAvatar(
                      radius: 38,
                      backgroundColor: t.accent,
                      child: Text(u.initials,
                          style: textTheme.headlineSmall
                              ?.copyWith(color: t.onAccent)),
                    ),
                    const SizedBox(height: AppSpacing.x12),
                    Text(u.displayName, style: textTheme.headlineSmall),
                    if (u.email != null)
                      Text(u.email!,
                          style: textTheme.bodyMedium
                              ?.copyWith(color: t.textSecondary)),
                    if (meta?.schoolName != null) ...[
                      const SizedBox(height: AppSpacing.x12),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          SchoolBadge(
                            logoUrl: meta?.logoUrl,
                            schoolName: meta?.schoolName,
                            primaryHex: meta?.primaryColor,
                            secondaryHex: meta?.secondaryColor,
                            size: 30,
                          ),
                          const SizedBox(width: AppSpacing.x8),
                          Flexible(
                            child: Text(meta!.schoolName!,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: textTheme.bodyMedium
                                    ?.copyWith(color: t.textSecondary)),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.x24),
              AuraCard(
                child: Column(
                  children: [
                    _KV('Student no.', sp?.studentNumber ?? '—'),
                    const Divider(height: AppSpacing.x24),
                    _KV('Year level', sp?.yearLevel?.toString() ?? '—'),
                    const Divider(height: AppSpacing.x24),
                    _KV('Status', sp?.studentStatus ?? '—'),
                    const Divider(height: AppSpacing.x24),
                    _KV('Face enrolled',
                        (sp?.isFaceRegistered ?? false) ? 'Yes' : 'No'),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _KV extends StatelessWidget {
  const _KV(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label,
            style: textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
        Text(value, style: textTheme.bodyLarge),
      ],
    );
  }
}
