import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../../core/theme/app_motion.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_tokens.dart';
import '../../../../shared/models/school.dart';
import '../../application/student_filter.dart';

/// Horizontal chip row that drives a [StudentFilter]. Each chip either
/// toggles directly (Face) or opens a multi-select bottom sheet
/// (Program / Year / Status). Active chips fill with an accent-tinted
/// background; inactive chips read as muted surface tiles. Press
/// feedback follows the rest of the app (scale 0.97, selection haptic,
/// reduced-motion honoured).
class StudentFilterBar extends StatelessWidget {
  const StudentFilterBar({
    super.key,
    required this.filter,
    required this.onChanged,
    required this.programs,
  });

  /// Current filter state. Parent owns it; widget never mutates.
  final StudentFilter filter;

  /// Called with the new filter whenever the user toggles a chip.
  final ValueChanged<StudentFilter> onChanged;

  /// All programs available in the current scope. Empty → the Program
  /// chip stays disabled (greyed out) since there's nothing to pick.
  final List<Program> programs;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);

    return Wrap(
      spacing: AppSpacing.x8,
      runSpacing: AppSpacing.x8,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        _FilterChip(
          icon: Icons.menu_book_rounded,
          label: _programLabel(),
          active: filter.programIds.isNotEmpty,
          disabled: programs.isEmpty,
          onTap: () => _openProgramSheet(context),
        ),
        _FilterChip(
          icon: Icons.timeline_rounded,
          label: _yearLabel(),
          active: filter.yearLevels.isNotEmpty,
          onTap: () => _openYearSheet(context),
        ),
        _FilterChip(
          icon: Icons.flag_rounded,
          label: _statusLabel(),
          active: filter.statuses.isNotEmpty,
          onTap: () => _openStatusSheet(context),
        ),
        _FilterChip(
          icon: filter.faceEnrolledOnly
              ? Icons.verified_rounded
              : Icons.face_rounded,
          label: 'Face enrolled',
          active: filter.faceEnrolledOnly,
          onTap: () {
            HapticFeedback.selectionClick();
            onChanged(filter.copyWith(
                faceEnrolledOnly: !filter.faceEnrolledOnly));
          },
        ),
        if (filter.isActive)
          _ClearChip(
            color: t.absent,
            onTap: () {
              HapticFeedback.selectionClick();
              onChanged(filter.cleared());
            },
          ),
      ],
    );
  }

  // ─── Chip labels ───────────────────────────────────────────────────
  String _programLabel() {
    final n = filter.programIds.length;
    if (n == 0) return 'Program';
    if (n == 1) {
      final p = programs.where((p) => p.id == filter.programIds.first);
      if (p.isNotEmpty) return p.first.name;
    }
    return '$n programs';
  }

  String _yearLabel() {
    final n = filter.yearLevels.length;
    if (n == 0) return 'Year';
    if (n == 1) return 'Year ${filter.yearLevels.first}';
    return '$n years';
  }

  String _statusLabel() {
    final n = filter.statuses.length;
    if (n == 0) return 'Status';
    if (n == 1) return _statusFriendly(filter.statuses.first);
    return '$n statuses';
  }

  // ─── Bottom sheets ─────────────────────────────────────────────────
  Future<void> _openProgramSheet(BuildContext context) async {
    final picked = await _showMultiSelectSheet<int>(
      context: context,
      title: 'Filter by program',
      options: [
        for (final p in programs) (value: p.id, label: p.name),
      ],
      initial: filter.programIds,
    );
    if (picked != null) {
      onChanged(filter.copyWith(programIds: picked));
    }
  }

  Future<void> _openYearSheet(BuildContext context) async {
    final picked = await _showMultiSelectSheet<int>(
      context: context,
      title: 'Filter by year level',
      options: const [
        (value: 1, label: '1st year'),
        (value: 2, label: '2nd year'),
        (value: 3, label: '3rd year'),
        (value: 4, label: '4th year'),
        (value: 5, label: '5th year'),
      ],
      initial: filter.yearLevels,
    );
    if (picked != null) {
      onChanged(filter.copyWith(yearLevels: picked));
    }
  }

  Future<void> _openStatusSheet(BuildContext context) async {
    final picked = await _showMultiSelectSheet<String>(
      context: context,
      title: 'Filter by status',
      options: const [
        (value: 'ACTIVE', label: 'Active'),
        (value: 'GRADUATED', label: 'Graduated'),
        (value: 'INACTIVE', label: 'Inactive'),
        (value: 'TRANSFERRED', label: 'Transferred'),
        (value: 'ARCHIVED', label: 'Archived'),
      ],
      initial: filter.statuses,
    );
    if (picked != null) {
      onChanged(filter.copyWith(statuses: picked));
    }
  }
}

String _statusFriendly(String raw) => switch (raw.toUpperCase()) {
      'ACTIVE' => 'Active',
      'GRADUATED' => 'Graduated',
      'INACTIVE' => 'Inactive',
      'TRANSFERRED' => 'Transferred',
      'ARCHIVED' => 'Archived',
      _ => raw,
    };

// ─── Filter chip ─────────────────────────────────────────────────────
/// Pressable filter chip. Active state fills with an accent-tinted
/// background; inactive sits on the surface-alt tile. Press feedback
/// is a 120ms scale 0.97 (emil), and the bg-color transition is a
/// 180ms tween (never ease-in — that would feel sluggish on a
/// rapid-fire chip row).
class _FilterChip extends StatefulWidget {
  const _FilterChip({
    required this.icon,
    required this.label,
    required this.active,
    required this.onTap,
    this.disabled = false,
  });

  final IconData icon;
  final String label;
  final bool active;
  final bool disabled;
  final VoidCallback onTap;

  @override
  State<_FilterChip> createState() => _FilterChipState();
}

class _FilterChipState extends State<_FilterChip> {
  bool _down = false;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    final fg = widget.disabled
        ? t.textMuted
        : (widget.active ? t.accentDark : t.textSecondary);
    final bg = widget.active
        ? t.accent.withOpacity(t.isDark ? 0.28 : 0.18)
        : t.surfaceAlt;
    final borderColor = widget.active ? t.accentDark : t.border;

    final pressed =
        _down && !widget.disabled && !reduce ? AppMotion.pressScale : 1.0;

    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTapDown: widget.disabled ? null : (_) => setState(() => _down = true),
      onTapUp: widget.disabled ? null : (_) => setState(() => _down = false),
      onTapCancel:
          widget.disabled ? null : () => setState(() => _down = false),
      onTap: widget.disabled ? null : widget.onTap,
      child: AnimatedScale(
        scale: pressed,
        duration: AppMotion.press,
        curve: AppMotion.easeOut,
        child: AnimatedContainer(
          duration:
              reduce ? Duration.zero : const Duration(milliseconds: 180),
          curve: AppMotion.easeOut,
          padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.x12, vertical: 8),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.circular(AppRadii.pill),
            border: Border.all(
                color: borderColor, width: widget.active ? 1.5 : 1),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(widget.icon, size: 14, color: fg),
              const SizedBox(width: 6),
              Text(
                widget.label,
                style: textTheme.labelLarge?.copyWith(
                  color: fg,
                  fontWeight:
                      widget.active ? FontWeight.w700 : FontWeight.w600,
                ),
              ),
              if (widget.active) ...[
                const SizedBox(width: 4),
                Icon(Icons.expand_more_rounded, size: 14, color: fg),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// Red-ish "× Clear all" chip. Shows only when at least one filter is
/// active; tapping resets every axis at once.
class _ClearChip extends StatelessWidget {
  const _ClearChip({required this.color, required this.onTap});
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x12, vertical: 8),
        decoration: BoxDecoration(
          color: color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(AppRadii.pill),
          border: Border.all(color: color.withOpacity(0.4)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.close_rounded, size: 14, color: color),
            const SizedBox(width: 4),
            Text(
              'Clear',
              style: textTheme.labelLarge
                  ?.copyWith(color: color, fontWeight: FontWeight.w700),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Multi-select bottom sheet ───────────────────────────────────────
typedef _Opt<T> = ({T value, String label});

/// Generic multi-select bottom sheet. Returns the new selection on
/// "Done", or null on cancel / outside tap (filter is unchanged).
Future<Set<T>?> _showMultiSelectSheet<T>({
  required BuildContext context,
  required String title,
  required List<_Opt<T>> options,
  required Set<T> initial,
}) {
  return showModalBottomSheet<Set<T>>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (_) => _MultiSelectSheet<T>(
      title: title,
      options: options,
      initial: initial,
    ),
  );
}

class _MultiSelectSheet<T> extends StatefulWidget {
  const _MultiSelectSheet({
    required this.title,
    required this.options,
    required this.initial,
  });
  final String title;
  final List<_Opt<T>> options;
  final Set<T> initial;

  @override
  State<_MultiSelectSheet<T>> createState() => _MultiSelectSheetState<T>();
}

class _MultiSelectSheetState<T> extends State<_MultiSelectSheet<T>> {
  late final Set<T> _picked = {...widget.initial};

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return SafeArea(
      top: false,
      child: Container(
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius: AppRadii.rSheet,
        ),
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x24, AppSpacing.x12, AppSpacing.x24, AppSpacing.x16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Drag handle
            Center(
              child: Container(
                width: 38,
                height: 4,
                margin: const EdgeInsets.only(bottom: AppSpacing.x16),
                decoration: BoxDecoration(
                  color: t.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Text(widget.title, style: textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.x12),
            Flexible(
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: widget.options.length,
                itemBuilder: (context, i) {
                  final opt = widget.options[i];
                  final selected = _picked.contains(opt.value);
                  return InkWell(
                    onTap: () {
                      HapticFeedback.selectionClick();
                      setState(() {
                        if (selected) {
                          _picked.remove(opt.value);
                        } else {
                          _picked.add(opt.value);
                        }
                      });
                    },
                    borderRadius: BorderRadius.circular(AppRadii.control),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.x8,
                          vertical: AppSpacing.x12),
                      child: Row(
                        children: [
                          AnimatedContainer(
                            duration: const Duration(milliseconds: 180),
                            curve: AppMotion.easeOut,
                            width: 22,
                            height: 22,
                            decoration: BoxDecoration(
                              color:
                                  selected ? t.accentDark : Colors.transparent,
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(
                                color:
                                    selected ? t.accentDark : t.textMuted,
                                width: 1.5,
                              ),
                            ),
                            child: AnimatedSwitcher(
                              duration: const Duration(milliseconds: 180),
                              switchInCurve: AppMotion.easeOut,
                              transitionBuilder: (child, anim) =>
                                  ScaleTransition(
                                scale: Tween<double>(begin: 0.6, end: 1.0)
                                    .animate(anim),
                                child:
                                    FadeTransition(opacity: anim, child: child),
                              ),
                              child: selected
                                  ? const Icon(
                                      Icons.check_rounded,
                                      key: ValueKey(true),
                                      size: 16,
                                      color: Colors.white,
                                    )
                                  : const SizedBox.shrink(
                                      key: ValueKey(false)),
                            ),
                          ),
                          const SizedBox(width: AppSpacing.x12),
                          Expanded(
                            child: Text(opt.label, style: textTheme.bodyLarge),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: AppSpacing.x8),
            Row(
              children: [
                TextButton(
                  onPressed: () {
                    setState(() => _picked.clear());
                  },
                  child: Text('Clear',
                      style: textTheme.labelLarge
                          ?.copyWith(color: t.absent)),
                ),
                const Spacer(),
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Cancel'),
                ),
                const SizedBox(width: AppSpacing.x8),
                FilledButton(
                  onPressed: () => Navigator.of(context).pop(_picked),
                  child: const Text('Done'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
