import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/auth_meta.dart';
import '../../core/auth/role.dart';
import '../../core/auth/session_controller.dart';
import '../../core/layout/breakpoints.dart';
import '../../core/theme/app_motion.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_tokens.dart';
import '../../core/widgets/school_badge.dart';
import 'navigation_items.dart';

/// Vertical navigation rail for tablet & desktop layouts. Reads the same
/// [ShellTabSpec]s as the mobile bottom nav, so adding a tab once updates
/// both surfaces. Works for every [Workspace] without any per-role logic.
///
/// Layout has three zones, top to bottom:
///   1. **Brand header** — school logo + name from the login meta.
///   2. **Nav list** — items from [tabs] with a single animated pill
///      indicator that *slides* between rows on selection change.
///   3. **Account card** — user identity that taps into the Account tab.
///
/// Width is driven by the parent ([DesktopShell]) via [isExpanded]. All
/// colours are read from [AppTokens.of] — the active pill paints the
/// school's primary brand colour (`t.accent`, customised at login by
/// `theme_controller.setBrandPrimaryHex`). Never hardcoded.
class SidebarNav extends ConsumerStatefulWidget {
  const SidebarNav({
    super.key,
    required this.workspace,
    required this.tabs,
    required this.selectedIndex,
    required this.onSelect,
    required this.isExpanded,
  });

  final Workspace workspace;
  final List<ShellTabSpec> tabs;
  final int selectedIndex;
  final ValueChanged<int> onSelect;
  final bool isExpanded;

  @override
  ConsumerState<SidebarNav> createState() => _SidebarNavState();
}

class _SidebarNavState extends ConsumerState<SidebarNav>
    with SingleTickerProviderStateMixin {
  late final AnimationController _entry = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 340),
  )..forward();

  /// Fixed item geometry — used both for laying out the rows and for
  /// pre-computing the active-indicator y position without measuring
  /// individual rows with GlobalKeys.
  static const double _itemHeight = 48;
  static const double _itemGap = 4;
  static const double _itemSpacing = _itemHeight + _itemGap;
  static const EdgeInsets _navListPadding = EdgeInsets.symmetric(
    horizontal: AppSpacing.x12,
    vertical: AppSpacing.x8,
  );

  @override
  void dispose() {
    _entry.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final meta = ref.watch(sessionControllerProvider).meta;

    // Indicator top in the nav-list inner coordinate space (after the
    // outer Padding strips _navListPadding.top).
    final indicatorTop = widget.selectedIndex * _itemSpacing;

    final width = widget.isExpanded
        ? Breakpoints.sidebarExpandedWidth
        : Breakpoints.sidebarCollapsedWidth;

    final slide = Tween<Offset>(
      begin: const Offset(-0.06, 0),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _entry, curve: AppMotion.easeOut));
    final fade = CurvedAnimation(parent: _entry, curve: Curves.easeOut);

    return AnimatedContainer(
      duration: reduce ? Duration.zero : const Duration(milliseconds: 320),
      curve: AppMotion.easeInOut,
      width: width,
      decoration: BoxDecoration(
        color: t.surface,
        border: Border(right: BorderSide(color: t.border)),
      ),
      child: SlideTransition(
        position: reduce ? const AlwaysStoppedAnimation(Offset.zero) : slide,
        child: FadeTransition(
          opacity: reduce ? const AlwaysStoppedAnimation(1) : fade,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _BrandHeader(isExpanded: widget.isExpanded, meta: meta),
              const SizedBox(height: AppSpacing.x8),
              Expanded(
                child: Padding(
                  padding: _navListPadding,
                  child: Stack(
                    children: [
                      // Sliding active pill — single instance, animated y.
                      // Painting it under the rows means the row's icon and
                      // label sit on top of the pill, not vice versa.
                      AnimatedPositioned(
                        duration: reduce ? Duration.zero : AppMotion.modal,
                        curve: AppMotion.easeOut,
                        top: indicatorTop,
                        left: 0,
                        right: 0,
                        height: _itemHeight,
                        child: _ActiveIndicator(accent: t.accent),
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          for (var i = 0; i < widget.tabs.length; i++) ...[
                            if (i > 0) const SizedBox(height: _itemGap),
                            _NavRow(
                              tab: widget.tabs[i],
                              isActive: i == widget.selectedIndex,
                              isExpanded: widget.isExpanded,
                              height: _itemHeight,
                              onTap: () => widget.onSelect(i),
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              if (meta != null)
                _AccountCard(
                  meta: meta,
                  workspace: widget.workspace,
                  isExpanded: widget.isExpanded,
                  // Account is conventionally the last tab in every
                  // workspace; route there when the card is tapped.
                  onTap: () => widget.onSelect(widget.tabs.length - 1),
                ),
              const SizedBox(height: AppSpacing.x16),
            ],
          ),
        ),
      ),
    );
  }
}

/// The single sliding pill that marks the active row. Background +
/// border opacity are tuned for both light and dark themes — the
/// accent comes from [AppTokens], never a literal.
class _ActiveIndicator extends StatelessWidget {
  const _ActiveIndicator({required this.accent});
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: accent.withOpacity(0.14),
        borderRadius: AppRadii.rControl,
        border: Border.all(color: accent.withOpacity(0.28)),
      ),
    );
  }
}

class _BrandHeader extends StatelessWidget {
  const _BrandHeader({required this.isExpanded, this.meta});
  final bool isExpanded;
  final AuthMeta? meta;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final tt = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.x16,
        AppSpacing.x20,
        AppSpacing.x16,
        AppSpacing.x12,
      ),
      child: Row(
        children: [
          SchoolBadge(
            logoUrl: meta?.logoUrl,
            schoolName: meta?.schoolName,
            schoolId: meta?.schoolId,
            primaryHex: meta?.primaryColor,
            secondaryHex: meta?.secondaryColor,
            size: 40,
          ),
          if (isExpanded) ...[
            const SizedBox(width: AppSpacing.x12),
            Expanded(
              child: AnimatedSwitcher(
                duration: AppMotion.dropdown,
                child: Text(
                  meta?.schoolName ?? 'Aura',
                  key: ValueKey(meta?.schoolName ?? 'aura'),
                  style: tt.titleMedium?.copyWith(
                    color: t.ink,
                    fontWeight: FontWeight.w700,
                    letterSpacing: -0.2,
                    height: 1.2,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _NavRow extends StatelessWidget {
  const _NavRow({
    required this.tab,
    required this.isActive,
    required this.isExpanded,
    required this.height,
    required this.onTap,
  });

  final ShellTabSpec tab;
  final bool isActive;
  final bool isExpanded;
  final double height;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final tt = Theme.of(context).textTheme;
    final iconColor = isActive ? t.accent : t.textSecondary;
    final labelColor = isActive ? t.ink : t.textSecondary;

    return SizedBox(
      height: height,
      child: Material(
        color: Colors.transparent,
        borderRadius: AppRadii.rControl,
        child: InkWell(
          onTap: onTap,
          borderRadius: AppRadii.rControl,
          splashColor: t.accent.withOpacity(0.08),
          highlightColor: t.accent.withOpacity(0.06),
          hoverColor: t.accent.withOpacity(0.06),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x12),
            child: Row(
              children: [
                Icon(tab.icon, color: iconColor, size: 22),
                if (isExpanded) ...[
                  const SizedBox(width: AppSpacing.x12),
                  Expanded(
                    child: AnimatedDefaultTextStyle(
                      duration: AppMotion.dropdown,
                      curve: AppMotion.easeOut,
                      style: tt.bodyMedium!.copyWith(
                        color: labelColor,
                        fontWeight:
                            isActive ? FontWeight.w700 : FontWeight.w500,
                      ),
                      child: Text(tab.label, overflow: TextOverflow.ellipsis),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _AccountCard extends StatelessWidget {
  const _AccountCard({
    required this.meta,
    required this.workspace,
    required this.isExpanded,
    required this.onTap,
  });

  final AuthMeta meta;
  final Workspace workspace;
  final bool isExpanded;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final tt = Theme.of(context).textTheme;
    final initials = meta.initials.isNotEmpty ? meta.initials : 'A';

    final avatar = Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        color: t.accent.withOpacity(0.16),
        shape: BoxShape.circle,
      ),
      alignment: Alignment.center,
      child: Text(
        initials,
        style: tt.labelLarge?.copyWith(
          color: t.accent,
          fontWeight: FontWeight.w800,
        ),
      ),
    );

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x12),
      child: Material(
        color: t.surfaceAlt,
        borderRadius: AppRadii.rCard,
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          splashColor: t.accent.withOpacity(0.08),
          highlightColor: t.accent.withOpacity(0.06),
          hoverColor: t.accent.withOpacity(0.05),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.x12),
            child: isExpanded
                ? Row(
                    children: [
                      avatar,
                      const SizedBox(width: AppSpacing.x12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              meta.displayName,
                              style: tt.bodyMedium?.copyWith(
                                color: t.ink,
                                fontWeight: FontWeight.w700,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 2),
                            Text(
                              _workspaceLabel(workspace),
                              style: tt.bodySmall?.copyWith(
                                color: t.textMuted,
                                letterSpacing: 0.4,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Icon(
                        Icons.chevron_right_rounded,
                        color: t.textMuted,
                        size: 18,
                      ),
                    ],
                  )
                : Center(child: avatar),
          ),
        ),
      ),
    );
  }

  static String _workspaceLabel(Workspace w) {
    switch (w) {
      case Workspace.student:
        return 'Student';
      case Workspace.schoolIt:
        return 'Campus Admin';
      case Workspace.governance:
        return 'Officer';
      case Workspace.admin:
        return 'Administrator';
    }
  }
}
