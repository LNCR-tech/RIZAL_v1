import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/section_header.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/governance.dart';
import '../../governance/data/governance_repository.dart';
import '../../governance/presentation/officer_editor.dart';

/// SSG (auto-created if missing) + its members, for the campus admin.
final campusSsgProvider = FutureProvider.autoDispose<GovernanceUnitDetail>(
    (ref) => ref.watch(governanceRepositoryProvider).ssgSetup());


/// Campus-admin "Student Government" panel — set up the SSG and add / edit /
/// remove the President & officers with their positions and permissions.
class CampusGovernanceScreen extends ConsumerWidget {
  const CampusGovernanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final async = ref.watch(campusSsgProvider);

    return AppScaffold(
      title: 'Student Government',
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.x20),
            child: ErrorView(
              message: e is ApiException
                  ? e.message
                  : 'Could not load student government.',
              onRetry: () => ref.invalidate(campusSsgProvider),
            ),
          ),
        ),
        data: (unit) {
          final members = unit.members.where((m) => m.isActive).toList();
          return RefreshIndicator(
            color: t.accent,
            backgroundColor: t.surface,
            onRefresh: () => ref.refresh(campusSsgProvider.future),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(
                  AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                AuraCard(
                  color: t.accent.withOpacity(0.12),
                  child: Row(
                    children: [
                      Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                            color: t.accent.withOpacity(0.2),
                            borderRadius:
                                BorderRadius.circular(AppRadii.control)),
                        child:
                            Icon(Icons.account_balance_rounded, color: t.accentDark),
                      ),
                      const SizedBox(width: AppSpacing.x16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(unit.summary.name, style: textTheme.titleLarge),
                            Text(
                                '${members.length} officer${members.length == 1 ? '' : 's'}',
                                style: textTheme.bodySmall
                                    ?.copyWith(color: t.textSecondary)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.x16),
                AuraButton(
                  label: 'Add officer',
                  icon: Icons.person_add_alt_1_rounded,
                  onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => OfficerEditor(
                            unitId: unit.summary.id,
                            unitType: 'SSG',
                            onSaved: () => ref.invalidate(campusSsgProvider),
                          ))),
                ),
                const SizedBox(height: AppSpacing.x24),
                const SectionHeader(title: 'Officers'),
                if (members.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: AppSpacing.x24),
                    child: EmptyState(
                      icon: Icons.groups_rounded,
                      title: 'No officers yet',
                      message:
                          'Add a President and officers to run the student government.',
                    ),
                  )
                else
                  for (final m in members)
                    _MemberCard(
                      member: m,
                      unitId: unit.summary.id,
                      onChanged: () => ref.invalidate(campusSsgProvider),
                    ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _MemberCard extends ConsumerWidget {
  const _MemberCard(
      {required this.member, required this.unitId, required this.onChanged});
  final GovernanceMember member;
  final int unitId;
  final VoidCallback onChanged;

  Future<void> _remove(BuildContext context, WidgetRef ref) async {
    final t = AppTokens.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Remove officer?'),
        content: Text('${govMemberName(member.user)} will lose their position '
            'and permissions.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: Text('Remove', style: TextStyle(color: t.absent))),
        ],
      ),
    );
    if (ok != true || !context.mounted) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(governanceRepositoryProvider).removeMember(member.id);
      onChanged();
      messenger.showSnackBar(const SnackBar(content: Text('Officer removed.')));
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
      child: AuraCard(
        child: Row(
          children: [
            CircleAvatar(
              radius: 20,
              backgroundColor: t.surfaceAlt,
              child: Text(govMemberName(member.user)[0].toUpperCase(),
                  style: textTheme.titleLarge?.copyWith(color: t.ink)),
            ),
            const SizedBox(width: AppSpacing.x12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(member.positionTitle ?? 'Officer',
                      style: textTheme.titleLarge),
                  Text(govMemberName(member.user),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: textTheme.bodySmall
                          ?.copyWith(color: t.textSecondary)),
                  Text(
                      '${member.permissionCodes.length} permission${member.permissionCodes.length == 1 ? '' : 's'}',
                      style:
                          textTheme.bodySmall?.copyWith(color: t.textMuted)),
                ],
              ),
            ),
            PopupMenuButton<String>(
              icon: Icon(Icons.more_vert_rounded, color: t.textMuted),
              onSelected: (v) {
                if (v == 'edit') {
                  Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => OfficerEditor(
                            unitId: unitId,
                            unitType: 'SSG',
                            member: member,
                            onSaved: onChanged,
                          )));
                } else {
                  _remove(context, ref);
                }
              },
              itemBuilder: (_) => const [
                PopupMenuItem(value: 'edit', child: Text('Edit')),
                PopupMenuItem(value: 'remove', child: Text('Remove')),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

