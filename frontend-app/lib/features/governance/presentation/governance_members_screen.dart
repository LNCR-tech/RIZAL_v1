import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/governance.dart';
import '../application/governance_providers.dart';
import '../data/governance_repository.dart';
import 'officer_editor.dart';

/// Governance "Members" tab — officers of the active unit (add/remove).
class GovernanceMembersScreen extends ConsumerWidget {
  const GovernanceMembersScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x24, AppSpacing.x20, 120);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final unit = ref.watch(effectiveUnitProvider);

    if (unit == null) {
      return const AppScaffold(
        title: 'Members',
        body: Center(
          child: EmptyState(
            icon: Icons.groups_rounded,
            title: 'No unit selected',
            message: 'Governance access is required to view members.',
          ),
        ),
      );
    }

    final canManage = unit.can('manage_members');
    final async = ref.watch(unitDetailProvider(unit.id));

    void addOfficer({GovernanceMember? member}) =>
        Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => OfficerEditor(
            unitId: unit.id,
            unitType: unit.type,
            member: member,
            onSaved: () => ref.invalidate(unitDetailProvider(unit.id)),
          ),
        ));

    // The active unit (which can be a child we drilled into); the app bar shows
    // "Members" + back, so the in-list header is just the unit name.
    Widget contextLine() => Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.x16),
          child: Text(unit.name,
              style: textTheme.bodyLarge?.copyWith(color: t.textSecondary)),
        );

    return AppScaffold(
      title: 'Members',
      actions: canManage
          ? [
              IconButton(
                tooltip: 'Add officer',
                icon: const Icon(Icons.person_add_alt_1_rounded),
                onPressed: () => addOfficer(),
              ),
            ]
          : null,
      body: RefreshIndicator(
        color: t.accent,
        backgroundColor: t.surface,
        onRefresh: () => ref.refresh(unitDetailProvider(unit.id).future),
        child: async.when(
          loading: () => ListView(padding: _pad, children: [
            contextLine(),
            const LoadingCardList(count: 5),
          ]),
          error: (e, _) => ListView(
            padding: _pad,
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              contextLine(),
              const SizedBox(height: 24),
              ErrorView(
                message:
                    e is ApiException ? e.message : 'Could not load members.',
                onRetry: () => ref.invalidate(unitDetailProvider(unit.id)),
              ),
            ],
          ),
          data: (detail) {
            final members = detail.members;
            return ListView(
              padding: _pad,
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                contextLine(),
                if (members.isEmpty)
                  const Padding(
                    padding: EdgeInsets.only(top: 40),
                    child: EmptyState(
                      icon: Icons.groups_rounded,
                      title: 'No members yet',
                      message: 'Add officers to this unit to get started.',
                    ),
                  )
                else
                  for (final m in members)
                    Padding(
                      key: ValueKey(m.id),
                      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                      child: _MemberCard(
                        member: m,
                        canManage: canManage,
                        onEdit: () => addOfficer(member: m),
                        onRemove: () => _confirmRemove(context, ref, unit.id, m),
                      ),
                    ),
              ],
            );
          },
        ),
      ),
    );
  }

  Future<void> _confirmRemove(
      BuildContext context, WidgetRef ref, int unitId, GovernanceMember m) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Remove member?'),
        content: Text('${m.user?.displayName ?? 'This member'} will be removed '
            'from the unit.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel')),
          TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Remove')),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(governanceRepositoryProvider).removeMember(m.id);
      ref.invalidate(unitDetailProvider(unitId));
    } on ApiException catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }
}

class _MemberCard extends StatelessWidget {
  const _MemberCard(
      {required this.member,
      required this.canManage,
      required this.onEdit,
      required this.onRemove});
  final GovernanceMember member;
  final bool canManage;
  final VoidCallback onEdit;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final u = member.user;
    return AuraCard(
      child: Row(
        children: [
          CircleAvatar(
            radius: 22,
            backgroundColor: t.surfaceAlt,
            child: Text(u?.initials ?? '?',
                style: textTheme.titleLarge?.copyWith(color: t.ink)),
          ),
          const SizedBox(width: AppSpacing.x16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(u?.displayName ?? 'Member', style: textTheme.titleLarge),
                Text(member.positionTitle ?? (u?.programName ?? 'Member'),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style:
                        textTheme.bodySmall?.copyWith(color: t.textSecondary)),
                if (member.permissionCodes.isNotEmpty)
                  Text(
                      '${member.permissionCodes.length} permission'
                      '${member.permissionCodes.length == 1 ? '' : 's'}',
                      style:
                          textTheme.bodySmall?.copyWith(color: t.textMuted)),
              ],
            ),
          ),
          if (canManage)
            PopupMenuButton<String>(
              icon: Icon(Icons.more_vert_rounded, color: t.textMuted),
              onSelected: (v) => v == 'edit' ? onEdit() : onRemove(),
              itemBuilder: (_) => const [
                PopupMenuItem(value: 'edit', child: Text('Edit')),
                PopupMenuItem(value: 'remove', child: Text('Remove')),
              ],
            ),
        ],
      ),
    );
  }
}

