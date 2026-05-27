import 'package:flutter/widgets.dart';

/// Layout breakpoints for the responsive app shell.
///
/// Threshold widths are exposed via [Breakpoints] constants and never
/// inlined into widgets — every consumer reads them through
/// [BreakpointContext.breakpoint] so a future tweak flows through one
/// place. Sidebar widths live here too so the layout work and the
/// animated container width can never disagree.
enum Breakpoint {
  /// Phones (and split-screen tablets narrower than [Breakpoints.mediumMin]).
  /// The mobile shell with bottom navigation runs here, unchanged.
  compact,

  /// Tablets in portrait, foldables. Sidebar shell with the rail
  /// collapsed to icons only.
  medium,

  /// Tablets in landscape and up, desktop. Sidebar shell with the
  /// rail fully expanded (icons + labels).
  expanded,
}

abstract final class Breakpoints {
  /// Minimum width (inclusive) for [Breakpoint.medium]. Anything narrower
  /// stays on the unchanged mobile UI.
  static const double mediumMin = 600;

  /// Minimum width (inclusive) for [Breakpoint.expanded].
  static const double expandedMin = 1024;

  /// Sidebar rail width at [Breakpoint.medium]. Icons only — wide enough
  /// for a 48dp tap target with comfortable horizontal padding.
  static const double sidebarCollapsedWidth = 76;

  /// Sidebar width at [Breakpoint.expanded]. Icons + labels with room
  /// for two-line school names without truncation.
  static const double sidebarExpandedWidth = 264;

  /// Resolves a width to the matching [Breakpoint]. Pure function so it
  /// can be unit-tested without a widget tree.
  static Breakpoint fromWidth(double width) {
    if (width >= expandedMin) return Breakpoint.expanded;
    if (width >= mediumMin) return Breakpoint.medium;
    return Breakpoint.compact;
  }
}

extension BreakpointContext on BuildContext {
  /// Current [Breakpoint] based on the nearest [MediaQuery] width.
  Breakpoint get breakpoint =>
      Breakpoints.fromWidth(MediaQuery.sizeOf(this).width);
}

extension BreakpointHelpers on Breakpoint {
  bool get isCompact => this == Breakpoint.compact;
  bool get isMedium => this == Breakpoint.medium;
  bool get isExpanded => this == Breakpoint.expanded;

  /// True at any tablet+ width where the sidebar shell renders.
  bool get hasSidebar => this != Breakpoint.compact;

  /// Sidebar width for this breakpoint. Zero at [Breakpoint.compact] —
  /// the sidebar is not painted at compact widths.
  double get sidebarWidth {
    switch (this) {
      case Breakpoint.compact:
        return 0;
      case Breakpoint.medium:
        return Breakpoints.sidebarCollapsedWidth;
      case Breakpoint.expanded:
        return Breakpoints.sidebarExpandedWidth;
    }
  }
}
