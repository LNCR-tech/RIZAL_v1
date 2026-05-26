import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/admin.dart';
import '../application/admin_providers.dart';
import 'create_school_screen.dart';
import 'school_detail_screen.dart';

class AdminSchoolsScreen extends ConsumerWidget {
  const AdminSchoolsScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x24, AppSpacing.x20, 120);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final async = ref.watch(adminSchoolsProvider);

    Widget header() => Row(
          children: [
            Expanded(child: Text('Schools', style: textTheme.displaySmall)),
            IconButton.filledTonal(
              tooltip: 'New school',
              icon: const Icon(Icons.add_rounded),
              onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                  builder: (_) => const CreateSchoolScreen())),
            ),
          ],
        );

    return RefreshIndicator(
      color: t.accent,
      backgroundColor: t.surface,
      onRefresh: () => ref.refresh(adminSchoolsProvider.future),
      child: async.when(
        loading: () => ListView(padding: _pad, children: [
          header(),
          const SizedBox(height: AppSpacing.x16),
          const LoadingCardList(count: 5),
        ]),
        error: (e, _) => ListView(
          padding: _pad,
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            header(),
            const SizedBox(height: 24),
            ErrorView(
              message: e is ApiException ? e.message : 'Could not load schools.',
              onRetry: () => ref.invalidate(adminSchoolsProvider),
            ),
          ],
        ),
        data: (schools) => ListView(
          padding: _pad,
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            header(),
            const SizedBox(height: AppSpacing.x16),
            if (schools.isEmpty)
              const Padding(
                padding: EdgeInsets.only(top: 40),
                child: EmptyState(
                  icon: Icons.apartment_rounded,
                  title: 'No schools yet',
                  message: 'Tap + to onboard your first school.',
                ),
              )
            else
              for (final s in schools)
                Padding(
                  key: ValueKey(s.schoolId),
                  padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                  child: _SchoolCard(school: s),
                ),
          ],
        ),
      ),
    );
  }
}

class _SchoolCard extends StatelessWidget {
  const _SchoolCard({required this.school});
  final SchoolSummary school;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final color = school.activeStatus ? t.present : t.textMuted;
    return AuraCard(
      onTap: () => Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => SchoolDetailScreen(school: school),
      )),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
                color: color.withOpacity(0.14),
                borderRadius: BorderRadius.circular(AppRadii.control)),
            child: Icon(Icons.apartment_rounded, color: color),
          ),
          const SizedBox(width: AppSpacing.x16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(school.schoolName ?? 'School',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: textTheme.titleLarge),
                Text(
                  [
                    if (school.schoolCode != null) school.schoolCode!,
                    if (school.subscriptionStatus != null)
                      school.subscriptionStatus!,
                  ].join(' · '),
                  style: textTheme.bodySmall?.copyWith(color: t.textSecondary),
                ),
              ],
            ),
          ),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: AppSpacing.x12, vertical: 4),
            decoration: BoxDecoration(
              color: color.withOpacity(0.14),
              borderRadius: BorderRadius.circular(AppRadii.pill),
            ),
            child: Text(school.activeStatus ? 'Active' : 'Inactive',
                style: textTheme.labelMedium?.copyWith(color: color)),
          ),
          Icon(Icons.chevron_right_rounded, color: t.textMuted),
        ],
      ),
    );
  }
}
