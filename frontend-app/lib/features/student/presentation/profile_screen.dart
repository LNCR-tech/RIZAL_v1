import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/data/school_directory_repository.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_motion.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/aura_skeleton.dart';
import '../../../core/widgets/pressable.dart';
import '../../../core/widgets/rise_in.dart';
import '../../../core/widgets/school_badge.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/profile.dart';
import '../application/student_providers.dart';

/// Read-only profile screen for the signed-in student. The two cards split
/// the data along a clean axis: **Academics** (what you study) on top,
/// **Identity** (who the school knows you as) underneath. Department and
/// program names load asynchronously and cross-fade in once the directory
/// resolves — no `"—"` placeholder snapping to text.
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
        data: (u) => RefreshIndicator(
          color: AppTokens.of(context).accent,
          onRefresh: () async {
            ref.invalidate(myProfileProvider);
            ref.invalidate(allDepartmentsProvider);
            ref.invalidate(allProgramsProvider);
            await ref.read(myProfileProvider.future);
          },
          child: ListView(
            padding: const EdgeInsets.fromLTRB(
                AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
            physics: const AlwaysScrollableScrollPhysics(),
            children: staggered([
              _HeroHeader(profile: u),
              const SizedBox(height: AppSpacing.x24),
              if (u.studentProfile != null) ...[
                _AcademicsCard(student: u.studentProfile!),
                const SizedBox(height: AppSpacing.x12),
              ],
              _IdentityCard(student: u.studentProfile),
            ]),
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Hero header — avatar, name, email, school chip. Same shape as before but
// tightened spacing.
// ─────────────────────────────────────────────────────────────────────────
class _HeroHeader extends ConsumerWidget {
  const _HeroHeader({required this.profile});
  final UserProfile profile;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final meta = ref.watch(sessionControllerProvider).meta;

    return Center(
      child: Column(
        children: [
          CircleAvatar(
            radius: 42,
            backgroundColor: t.accent,
            child: Text(
              profile.initials,
              style:
                  textTheme.headlineSmall?.copyWith(color: t.onAccent),
            ),
          ),
          const SizedBox(height: AppSpacing.x12),
          Text(profile.displayName,
              textAlign: TextAlign.center, style: textTheme.headlineSmall),
          if (profile.email != null)
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                profile.email!,
                textAlign: TextAlign.center,
                style:
                    textTheme.bodyMedium?.copyWith(color: t.textSecondary),
              ),
            ),
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
                  size: 28,
                ),
                const SizedBox(width: AppSpacing.x8),
                Flexible(
                  child: Text(
                    meta!.schoolName!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: textTheme.bodyMedium
                        ?.copyWith(color: t.textSecondary),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Academics card — Program, College, Year level. Names resolve via the
// directory providers; placeholders are short skeletons (real reserved
// space) and the real value cross-fades in once it arrives.
// ─────────────────────────────────────────────────────────────────────────
class _AcademicsCard extends ConsumerWidget {
  const _AcademicsCard({required this.student});
  final StudentProfile student;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    final programAsync = student.programId != null
        ? ref.watch(programByIdProvider(student.programId!))
        : null;
    final departmentAsync = student.departmentId != null
        ? ref.watch(departmentByIdProvider(student.departmentId!))
        : null;

    final programName = programAsync?.valueOrNull?.name;
    final departmentName = departmentAsync?.valueOrNull?.name;
    final programLoading = programAsync?.isLoading ?? false;
    final departmentLoading = departmentAsync?.isLoading ?? false;

    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.x16),
            child: Text(
              'ACADEMICS',
              style: textTheme.labelMedium?.copyWith(
                color: t.textMuted,
                letterSpacing: 1.2,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          _AcademicRow(
            icon: Icons.menu_book_rounded,
            tint: t.accentDark,
            label: 'Program',
            value: programName,
            missingLabel: 'Not assigned',
            loading: programLoading,
          ),
          const _RowDivider(),
          _AcademicRow(
            icon: Icons.account_tree_rounded,
            tint: t.sg,
            label: 'College',
            value: departmentName,
            missingLabel: 'Not assigned',
            loading: departmentLoading,
          ),
          const _RowDivider(),
          _AcademicRow(
            icon: Icons.school_rounded,
            tint: t.ssg,
            label: 'Year level',
            value: student.yearLevel != null
                ? _ordinalYear(student.yearLevel!)
                : null,
            missingLabel: 'Not set',
            loading: false,
            mono: true,
          ),
        ],
      ),
    );
  }
}

String _ordinalYear(int year) {
  final suffix = switch (year) {
    1 => 'st',
    2 => 'nd',
    3 => 'rd',
    _ => 'th',
  };
  return '$year$suffix year';
}

/// One row in the academics / identity cards: tinted icon chip + uppercase
/// label + value (or skeleton while loading, or muted "missing" label when
/// the field is null). The value cross-fades from skeleton → text once
/// async data lands (220 ms scale 0.96 → 1.0 + fade — emil).
class _AcademicRow extends StatelessWidget {
  const _AcademicRow({
    required this.icon,
    required this.tint,
    required this.label,
    required this.value,
    required this.missingLabel,
    required this.loading,
    this.mono = false,
  });

  final IconData icon;
  final Color tint;
  final String label;
  final String? value;
  final String missingLabel;
  final bool loading;
  final bool mono;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    Widget valueWidget;
    if (loading) {
      valueWidget = const Padding(
        key: ValueKey('skeleton'),
        padding: EdgeInsets.only(top: 4, bottom: 2),
        child: AuraSkeleton(width: 160, height: 18),
      );
    } else if (value == null) {
      valueWidget = Text(
        missingLabel,
        key: const ValueKey('missing'),
        style: textTheme.titleLarge?.copyWith(color: t.textMuted),
      );
    } else {
      valueWidget = Text(
        value!,
        key: ValueKey(value),
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        style: mono
            ? AppTypography.mono(
                size: 18, weight: FontWeight.w700, color: t.ink)
            : textTheme.titleLarge,
      );
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: tint.withOpacity(t.isDark ? 0.22 : 0.16),
            borderRadius: BorderRadius.circular(AppRadii.control),
          ),
          child: Icon(icon, color: tint, size: 20),
        ),
        const SizedBox(width: AppSpacing.x16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                label.toUpperCase(),
                style: textTheme.labelMedium?.copyWith(
                  color: t.textSecondary,
                  letterSpacing: 0.8,
                ),
              ),
              const SizedBox(height: 2),
              AnimatedSwitcher(
                duration:
                    reduce ? Duration.zero : const Duration(milliseconds: 220),
                switchInCurve: AppMotion.easeOut,
                transitionBuilder: (child, anim) {
                  // Scale from 0.96 (not 0) + opacity. Honors emil's "never
                  // animate from scale(0)" rule.
                  return FadeTransition(
                    opacity: anim,
                    child: ScaleTransition(
                      scale: Tween<double>(begin: 0.96, end: 1.0)
                          .animate(anim),
                      child: child,
                    ),
                  );
                },
                child: valueWidget,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _RowDivider extends StatelessWidget {
  const _RowDivider();

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.x12),
      child: Divider(height: 1, color: t.border),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Identity card — Student no (tap to copy), Status chip, Face ID chip.
// ─────────────────────────────────────────────────────────────────────────
class _IdentityCard extends StatelessWidget {
  const _IdentityCard({required this.student});
  final StudentProfile? student;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    if (student == null) {
      return AuraCard(
        child: Text(
          'No student profile linked to this account.',
          style: textTheme.bodyMedium?.copyWith(color: t.textSecondary),
        ),
      );
    }
    final sp = student!;

    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.x16),
            child: Text(
              'IDENTITY',
              style: textTheme.labelMedium?.copyWith(
                color: t.textMuted,
                letterSpacing: 1.2,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          _StudentNumberRow(studentNumber: sp.studentNumber),
          const _RowDivider(),
          _ChipRow(
            icon: Icons.task_alt_rounded,
            label: 'Status',
            chip: _StatusChip(status: sp.studentStatus),
          ),
          const _RowDivider(),
          _ChipRow(
            icon: Icons.face_rounded,
            label: 'Face ID',
            chip: _FaceChip(enrolled: sp.isFaceRegistered),
          ),
        ],
      ),
    );
  }
}

/// Student number row — tap to copy. Long touch target (the whole row is
/// pressable, not just the text) to make it discoverable. Haptic confirms
/// the copy; a snackbar gives a visible cue too.
class _StudentNumberRow extends StatelessWidget {
  const _StudentNumberRow({required this.studentNumber});
  final String? studentNumber;

  Future<void> _copy(BuildContext context) async {
    final value = studentNumber;
    if (value == null) return;
    await Clipboard.setData(ClipboardData(text: value));
    HapticFeedback.selectionClick();
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Student number copied — $value'),
        duration: const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final hasValue = (studentNumber ?? '').trim().isNotEmpty;

    final body = Row(
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: t.accent.withOpacity(t.isDark ? 0.22 : 0.16),
            borderRadius: BorderRadius.circular(AppRadii.control),
          ),
          child: Icon(Icons.badge_rounded, color: t.accentDark, size: 20),
        ),
        const SizedBox(width: AppSpacing.x16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'STUDENT NUMBER',
                style: textTheme.labelMedium?.copyWith(
                  color: t.textSecondary,
                  letterSpacing: 0.8,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                hasValue ? studentNumber! : 'Not assigned',
                style: hasValue
                    ? AppTypography.mono(
                        size: 18, weight: FontWeight.w700, color: t.ink)
                    : textTheme.titleLarge
                        ?.copyWith(color: t.textMuted),
              ),
            ],
          ),
        ),
        if (hasValue)
          Icon(Icons.copy_rounded, color: t.textMuted, size: 18),
      ],
    );

    if (!hasValue) return body;
    return Semantics(
      button: true,
      label: 'Copy student number',
      child: Pressable(onTap: () => _copy(context), child: body),
    );
  }
}

class _ChipRow extends StatelessWidget {
  const _ChipRow({
    required this.icon,
    required this.label,
    required this.chip,
  });
  final IconData icon;
  final String label;
  final Widget chip;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Row(
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: t.surfaceAlt,
            borderRadius: BorderRadius.circular(AppRadii.control),
          ),
          child: Icon(icon, color: t.textSecondary, size: 20),
        ),
        const SizedBox(width: AppSpacing.x16),
        Expanded(
          child: Text(
            label.toUpperCase(),
            style: textTheme.labelMedium?.copyWith(
              color: t.textSecondary,
              letterSpacing: 0.8,
            ),
          ),
        ),
        chip,
      ],
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});
  final String? status;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    final raw = (status ?? '').trim().toUpperCase();
    final (label, color, icon) = switch (raw) {
      'ACTIVE' => ('Active', t.present, Icons.check_circle_rounded),
      'INACTIVE' => ('Inactive', t.absent, Icons.do_not_disturb_on_rounded),
      'GRADUATED' => ('Graduated', t.accentDark, Icons.workspace_premium_rounded),
      'WITHDRAWN' => ('Withdrawn', t.textMuted, Icons.exit_to_app_rounded),
      'SUSPENDED' => ('Suspended', t.tardy, Icons.pause_circle_rounded),
      _ => (
          raw.isEmpty ? 'Unknown' : _titleCase(raw),
          t.textMuted,
          Icons.help_outline_rounded,
        ),
    };

    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x12, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(t.isDark ? 0.22 : 0.14),
        borderRadius: BorderRadius.circular(AppRadii.pill),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: textTheme.labelMedium?.copyWith(
              color: color,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

String _titleCase(String s) {
  if (s.isEmpty) return s;
  return s[0].toUpperCase() + s.substring(1).toLowerCase();
}

class _FaceChip extends StatelessWidget {
  const _FaceChip({required this.enrolled});
  final bool enrolled;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final color = enrolled ? t.present : t.textMuted;
    final label = enrolled ? 'Enrolled' : 'Not enrolled';
    final icon = enrolled
        ? Icons.verified_rounded
        : Icons.face_retouching_off_rounded;

    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x12, vertical: 5),
      decoration: BoxDecoration(
        color: enrolled
            ? color.withOpacity(t.isDark ? 0.22 : 0.14)
            : t.surfaceAlt,
        borderRadius: BorderRadius.circular(AppRadii.pill),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: textTheme.labelMedium?.copyWith(
              color: color,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}
