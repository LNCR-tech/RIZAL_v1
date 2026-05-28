import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/role.dart';
import '../../../core/auth/session_controller.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/arc_gauge.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/dashboard.dart';
import '../../../core/widgets/pressable.dart';
import '../../../core/widgets/rise_in.dart';
import '../../../core/widgets/school_badge.dart';
import '../../../core/widgets/section_header.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/event.dart';
import '../../../shared/models/governance.dart';
import '../../../shared/utils/formatting.dart';
import '../../gather/presentation/gather_screen.dart';
import '../../reports/export_sheet.dart';
import '../../shell/app_shell.dart';
import '../application/governance_providers.dart';
import 'announcements_screen.dart';
import 'governance_events_screen.dart';
import 'governance_event_monitor_screen.dart';
import 'governance_members_screen.dart';
import 'sanctions_screen.dart';
import 'unit_creator_screen.dart';

/// Governance "Home" — an event-management dashboard: compliance gauge, metrics,
/// permission-aware quick actions, and a live event list with export.
class GovernanceHomeScreen extends ConsumerWidget {
  const GovernanceHomeScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x24, AppSpacing.x20, 130);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final accessAsync = ref.watch(governanceAccessProvider);

    return accessAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => ListView(
        padding: _pad,
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          const SizedBox(height: 24),
          ErrorView(
            message:
                e is ApiException ? e.message : 'Could not load governance.',
            onRetry: () => ref.invalidate(governanceAccessProvider),
          ),
        ],
      ),
      data: (access) {
        if (!access.hasAccess) {
          return ListView(
            padding: _pad,
            physics: const AlwaysScrollableScrollPhysics(),
            children: const [
              SizedBox(height: 60),
              EmptyState(
                icon: Icons.account_balance_rounded,
                title: 'No governance access',
                message: "You don't manage any governance unit yet.",
              ),
            ],
          );
        }
        final unit = ref.watch(effectiveUnitProvider) ?? access.units.first;
        return _Dashboard(unit: unit, units: access.units);
      },
    );
  }
}

class _Dashboard extends ConsumerWidget {
  const _Dashboard({required this.unit, required this.units});
  final GovUnitAccess unit;
  final List<GovUnitAccess> units;

  Color _typeColor(String type) {
    switch (type) {
      case 'SSG':
        return AppColors.ssg;
      case 'SG':
        return AppColors.sg;
      default:
        return AppColors.accentDark;
    }
  }

  String? _position(WidgetRef ref) {
    final detail = ref.watch(unitDetailProvider(unit.id)).valueOrNull;
    final myId = ref.watch(sessionControllerProvider).meta?.userId;
    if (detail == null || myId == null) return null;
    for (final m in detail.members) {
      if (m.userId == myId) return m.positionTitle;
    }
    return null;
  }

  /// Switch the active unit to a child we tapped. Effective permissions = our
  /// direct membership in the child (if any) plus the management permissions the
  /// backend propagates from a *direct* parent membership
  /// (`_can_manage_members` / `_can_assign_permissions`). Propagation is a
  /// single level only — we don't propagate through an already-drilled parent.
  void _openChild(WidgetRef ref, GovernanceUnitSummary child) {
    final perms = <String>{};
    for (final u in units) {
      if (u.id == child.id) perms.addAll(u.permissionCodes);
    }
    final parentIsDirect = units.any((u) => u.id == unit.id);
    if (parentIsDirect) {
      if (unit.can('manage_members')) perms.add('manage_members');
      if (unit.can('assign_permissions')) perms.add('assign_permissions');
    }
    ref.read(activeUnitProvider.notifier).select(
          GovUnitAccess.fromSummary(child, permissionCodes: perms.toList()),
        );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final typeColor = _typeColor(unit.type);
    final o = ref.watch(dashboardOverviewProvider(unit.id)).valueOrNull;
    final sanctions = ref.watch(sanctionsDashboardProvider).valueOrNull;
    final compliance =
        sanctions != null ? (100 - sanctions.overallAbsenceRate) : null;
    final position = _position(ref);
    final meta = ref.watch(sessionControllerProvider).meta;
    // The active unit is a child we drilled into (not one of our direct
    // memberships) — show a back affordance to return to the parent.
    final isDrilled = !units.any((u) => u.id == unit.id);

    final events = [...?ref.watch(governanceEventsProvider(unit.type)).valueOrNull];
    int rank(AppEvent e) =>
        e.isOngoing ? 0 : (e.isUpcoming ? 1 : (e.isCompleted ? 2 : 3));
    events.sort((a, b) {
      final r = rank(a).compareTo(rank(b));
      if (r != 0) return r;
      return (a.startDatetime ?? DateTime(2100))
          .compareTo(b.startDatetime ?? DateTime(2100));
    });

    return RefreshIndicator(
      color: t.accent,
      backgroundColor: t.surface,
      onRefresh: () async {
        ref.invalidate(sanctionsDashboardProvider);
        ref.invalidate(governanceEventsProvider(unit.type));
        ref.invalidate(dashboardOverviewProvider(unit.id));
        await ref.read(dashboardOverviewProvider(unit.id).future);
      },
      child: ListView(
        padding: GovernanceHomeScreen._pad,
        physics: const AlwaysScrollableScrollPhysics(),
        children: staggered([
          // Header
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (isDrilled)
                Padding(
                  padding: const EdgeInsets.only(right: AppSpacing.x8),
                  child: IconButton.filledTonal(
                    tooltip: 'Back to parent unit',
                    icon: const Icon(Icons.arrow_back_rounded),
                    onPressed: () =>
                        ref.read(activeUnitProvider.notifier).clear(),
                  ),
                ),
              SchoolBadge(
                logoUrl: meta?.logoUrl,
                schoolName: meta?.schoolName,
                primaryHex: meta?.primaryColor,
                secondaryHex: meta?.secondaryColor,
                size: 48,
              ),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Governance', style: textTheme.displaySmall),
                    Text(
                      position != null
                          ? '$position · ${unit.name}'
                          : unit.name,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style:
                          textTheme.bodyLarge?.copyWith(color: t.textSecondary),
                    ),
                  ],
                ),
              ),
              IconButton(
                tooltip: 'Switch to student view',
                icon: const Icon(Icons.switch_account_rounded),
                onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) =>
                        const AppShell(workspace: Workspace.student))),
              ),
              if (units.length > 1)
                PopupMenuButton<GovUnitAccess>(
                  onSelected: (u) =>
                      ref.read(activeUnitProvider.notifier).select(u),
                  itemBuilder: (context) => [
                    for (final u in units)
                      PopupMenuItem(
                          value: u, child: Text('${u.name} (${u.type})')),
                  ],
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.x12, vertical: AppSpacing.x8),
                    decoration: BoxDecoration(
                        color: t.surfaceAlt,
                        borderRadius: BorderRadius.circular(AppRadii.pill)),
                    child: Row(mainAxisSize: MainAxisSize.min, children: [
                      Text(unit.code, style: textTheme.labelLarge),
                      Icon(Icons.expand_more_rounded,
                          size: 18, color: t.textMuted),
                    ]),
                  ),
                ),
            ],
          ),
          const SizedBox(height: AppSpacing.x20),

          // Hero — compliance gauge (or students fallback)
          if (compliance != null)
            AuraCard(
              color: t.accent.withOpacity(0.14),
              child: Column(
                children: [
                  ArcGauge(
                    percent: compliance,
                    color: typeColor,
                    trackColor: t.surface,
                    size: 220,
                    stroke: 18,
                    center: Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('${compliance.round()}%',
                              style: AppTypography.mono(
                                  size: 34,
                                  weight: FontWeight.w800,
                                  color: t.ink)),
                          Text('Compliance',
                              style: textTheme.bodyMedium
                                  ?.copyWith(color: t.textSecondary)),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.x8),
                  Text(
                    '${sanctions!.totalPending} pending sanctions · '
                    '${o?.totalStudents ?? 0} students',
                    style:
                        textTheme.bodySmall?.copyWith(color: t.textSecondary),
                  ),
                ],
              ),
            )
          else
            HeroRingCard(
              title: 'Students',
              value: o?.totalStudents.toString() ?? '—',
              footnote: '${unit.type} · ${unit.name}',
              icon: Icons.account_balance_rounded,
              ringColor: typeColor,
            ),
          const SizedBox(height: AppSpacing.x12),

          // Metrics
          Row(
            children: [
              Expanded(
                  child: MetricChipCard(
                      icon: Icons.groups_rounded,
                      label: 'Students',
                      value: o?.totalStudents.toString() ?? '—',
                      tint: typeColor)),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                  child: MetricChipCard(
                      icon: Icons.event_rounded,
                      label: 'Events',
                      value: events.isEmpty ? '—' : '${events.length}',
                      tint: t.accentDark)),
            ],
          ),
          const SizedBox(height: AppSpacing.x12),
          Row(
            children: [
              Expanded(
                  child: MetricChipCard(
                      icon: Icons.campaign_rounded,
                      label: 'Published',
                      value: o?.publishedAnnouncementCount.toString() ?? '—',
                      tint: AppColors.sg)),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                  child: MetricChipCard(
                      icon: Icons.gavel_rounded,
                      label: 'Pending',
                      value: sanctions?.totalPending.toString() ?? '—',
                      tint: t.absent)),
            ],
          ),
          const SizedBox(height: AppSpacing.x24),

          // Quick actions (greyed when not permitted)
          const SectionHeader(title: 'Quick actions'),
          Row(
            children: [
              Expanded(
                child: _QuickAction(
                  icon: Icons.campaign_rounded,
                  label: 'Announce',
                  color: AppColors.sg,
                  enabled: unit.can('manage_announcements'),
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => AnnouncementsScreen(
                          unitId: unit.id, canManage: true))),
                ),
              ),
              Expanded(
                child: _QuickAction(
                  icon: Icons.event_rounded,
                  label: 'Events',
                  color: t.accentDark,
                  enabled: unit.can('manage_events'),
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => const GovernanceEventsScreen())),
                ),
              ),
              Expanded(
                child: _QuickAction(
                  icon: Icons.gavel_rounded,
                  label: 'Sanctions',
                  color: t.absent,
                  enabled: unit.can('view_sanctions_dashboard'),
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => const SanctionsScreen())),
                ),
              ),
              Expanded(
                child: _QuickAction(
                  icon: Icons.badge_rounded,
                  label: 'Members',
                  color: AppColors.ssg,
                  enabled: unit.can('manage_members'),
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => const GovernanceMembersScreen())),
                ),
              ),
              Expanded(
                child: _QuickAction(
                  icon: Icons.center_focus_strong_rounded,
                  label: 'Kiosk',
                  color: t.accent,
                  enabled: unit.can('manage_events'),
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => const GatherScreen())),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.x24),

          // Build the hierarchy: SSG → SG, SG → ORG (gated by create_sg /
          // create_org). ORG units are leaves, so this block is hidden for them.
          if (unit.type == 'SSG' || unit.type == 'SG') ...[
            SectionHeader(
                title: unit.type == 'SSG'
                    ? 'College governments'
                    : 'Program organizations'),
            _CreateChildButton(unit: unit),
            const SizedBox(height: AppSpacing.x12),
            if (o == null)
              const LoadingCardList(count: 2)
            else if (o.childUnits.isEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.x8),
                child: Text(
                    unit.type == 'SSG'
                        ? 'No college SG units yet.'
                        : 'No program ORG units yet.',
                    style:
                        textTheme.bodyMedium?.copyWith(color: t.textMuted)),
              )
            else
              for (final c in o.childUnits)
                _ChildUnitRow(
                  key: ValueKey(c.id),
                  summary: c,
                  color: _typeColor(c.type),
                  onTap: () => _openChild(ref, c),
                ),
            const SizedBox(height: AppSpacing.x24),
          ],

          // Events with live progress + export
          const SectionHeader(title: 'Manage events'),
          if (events.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: AppSpacing.x24),
              child: Text('No events in this scope yet.',
                  style: textTheme.bodyMedium?.copyWith(color: t.textMuted)),
            )
          else
            for (final e in events.take(8))
              _EventRow(key: ValueKey(e.id), event: e),

          if (o != null && o.recentAnnouncements.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x12),
            const SectionHeader(title: 'Recent announcements'),
            for (final a in o.recentAnnouncements)
              Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                child: AuraCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(a.title, style: textTheme.titleLarge),
                      if (a.updatedAt != null)
                        Text(fmtFullDate(a.updatedAt),
                            style: textTheme.bodySmall
                                ?.copyWith(color: t.textMuted)),
                    ],
                  ),
                ),
              ),
          ],
        ]),
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({
    required this.icon,
    required this.label,
    required this.color,
    required this.enabled,
    required this.onTap,
  });
  final IconData icon;
  final String label;
  final Color color;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final chip = Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 52,
          height: 52,
          decoration: BoxDecoration(
            color: enabled ? color.withOpacity(0.16) : t.surfaceAlt,
            borderRadius: BorderRadius.circular(AppRadii.control),
          ),
          child: Icon(enabled ? icon : Icons.lock_rounded,
              color: enabled ? color : t.textMuted),
        ),
        const SizedBox(height: 6),
        Text(label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: textTheme.bodySmall
                ?.copyWith(color: enabled ? t.ink : t.textMuted)),
      ],
    );
    return enabled
        ? Pressable(onTap: onTap, child: chip)
        : Tooltip(message: 'Not permitted', child: Opacity(opacity: 0.65, child: chip));
  }
}

/// "Create college SG" / "Create program ORG" — enabled when the active unit
/// grants the matching child-creation permission, otherwise a locked button.
class _CreateChildButton extends StatelessWidget {
  const _CreateChildButton({required this.unit});
  final GovUnitAccess unit;

  @override
  Widget build(BuildContext context) {
    final isSsg = unit.type == 'SSG';
    final canCreate = isSsg ? unit.can('create_sg') : unit.can('create_org');
    final label = isSsg ? 'Create college SG' : 'Create program ORG';
    if (canCreate) {
      return AuraButton(
        label: label,
        icon: Icons.add_rounded,
        variant: AuraButtonVariant.tonal,
        onPressed: () => Navigator.of(context).push(MaterialPageRoute(
            builder: (_) => UnitCreatorScreen(parent: unit))),
      );
    }
    return Tooltip(
      message: 'Not permitted',
      child: AuraButton(
        label: label,
        icon: Icons.lock_rounded,
        variant: AuraButtonVariant.ghost,
        onPressed: null,
      ),
    );
  }
}

/// A child unit row on a parent's dashboard. Tapping it switches the workspace
/// into that child (see `_Dashboard._openChild`).
class _ChildUnitRow extends StatelessWidget {
  const _ChildUnitRow({
    super.key,
    required this.summary,
    required this.color,
    required this.onTap,
  });
  final GovernanceUnitSummary summary;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
      child: AuraCard(
        onTap: onTap,
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                  color: color.withOpacity(0.16),
                  borderRadius: BorderRadius.circular(AppRadii.control)),
              child: Icon(
                  summary.type == 'SG'
                      ? Icons.account_balance_rounded
                      : Icons.workspaces_rounded,
                  color: color),
            ),
            const SizedBox(width: AppSpacing.x12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(summary.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: textTheme.titleLarge),
                  Text(
                      '${summary.code} · ${summary.memberCount} member'
                      '${summary.memberCount == 1 ? '' : 's'}',
                      style:
                          textTheme.bodySmall?.copyWith(color: t.textMuted)),
                ],
              ),
            ),
            Icon(Icons.chevron_right_rounded, color: t.textMuted),
          ],
        ),
      ),
    );
  }
}

class _EventRow extends ConsumerWidget {
  const _EventRow({super.key, required this.event});
  final AppEvent event;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final stats = (event.isOngoing
            ? ref.watch(eventLiveStatsProvider(event.id))
            : ref.watch(eventStatsProvider(event.id)))
        .valueOrNull;
    final total = stats?.total ?? 0;
    final present =
        (stats?.countOf('present') ?? 0) + (stats?.countOf('late') ?? 0);
    final pct = total > 0 ? present / total : 0.0;
    final statusColor = switch (event.status.toLowerCase()) {
      'ongoing' => t.accentDark,
      'completed' => t.present,
      'cancelled' => t.absent,
      _ => t.textMuted,
    };

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
      child: AuraCard(
        onTap: () => Navigator.of(context).push(MaterialPageRoute(
            builder: (_) => GovernanceEventMonitorScreen(event: event))),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(event.name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: textTheme.titleLarge),
                      Text(fmtFullDate(event.startDatetime),
                          style: textTheme.bodySmall
                              ?.copyWith(color: t.textMuted)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                      color: statusColor.withOpacity(0.16),
                      borderRadius: BorderRadius.circular(AppRadii.pill)),
                  child: Text(event.status,
                      style: textTheme.labelSmall?.copyWith(color: statusColor)),
                ),
                IconButton(
                  tooltip: 'Export report',
                  icon: const Icon(Icons.ios_share_rounded),
                  onPressed: () => showModalBottomSheet<void>(
                    context: context,
                    isScrollControlled: true,
                    backgroundColor: Colors.transparent,
                    builder: (_) => ExportSheet(event: event),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.x8),
            Row(
              children: [
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: LinearProgressIndicator(
                      value: pct.clamp(0.0, 1.0),
                      minHeight: 8,
                      backgroundColor: t.surfaceAlt,
                      color: event.isOngoing ? t.accent : t.present,
                    ),
                  ),
                ),
                const SizedBox(width: AppSpacing.x12),
                Text('${(pct * 100).round()}%',
                    style: AppTypography.mono(
                        size: 13, weight: FontWeight.w700, color: t.ink)),
              ],
            ),
            if (event.isOngoing)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text('● Live · $present of $total checked in',
                    style: textTheme.bodySmall?.copyWith(color: t.accentDark)),
              ),
          ],
        ),
      ),
    );
  }
}
