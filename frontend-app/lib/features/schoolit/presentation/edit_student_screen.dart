import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_motion.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/rise_in.dart';
import '../../../shared/models/profile.dart';
import '../../student/data/profile_repository.dart';
import '../application/edit_student_form.dart';
import '../application/schoolit_providers.dart';

/// Edit-student surface. Two independent save sections (Identity ↔ Academics)
/// so a partial failure on one doesn't lose the other's work. Saves
/// transition through a confirmation dialog when status is being moved
/// into a destructive bucket (INACTIVE / TRANSFERRED / ARCHIVED).
class EditStudentScreen extends ConsumerStatefulWidget {
  const EditStudentScreen({super.key, required this.user});
  final UserProfile user;

  @override
  ConsumerState<EditStudentScreen> createState() => _EditStudentScreenState();
}

class _EditStudentScreenState extends ConsumerState<EditStudentScreen> {
  late final EditStudentForm _form;

  late final TextEditingController _firstName;
  late final TextEditingController _middleName;
  late final TextEditingController _lastName;
  late final TextEditingController _email;
  late final TextEditingController _studentNumber;

  bool _savingIdentity = false;
  bool _savingAcademics = false;
  String? _identityError;
  String? _academicsError;

  @override
  void initState() {
    super.initState();
    _form = EditStudentForm.fromUser(widget.user);
    _firstName = TextEditingController(text: _form.firstName)
      ..addListener(() {
        _form.firstName = _firstName.text;
        setState(() {});
      });
    _middleName = TextEditingController(text: _form.middleName)
      ..addListener(() {
        _form.middleName = _middleName.text;
        setState(() {});
      });
    _lastName = TextEditingController(text: _form.lastName)
      ..addListener(() {
        _form.lastName = _lastName.text;
        setState(() {});
      });
    _email = TextEditingController(text: _form.email)
      ..addListener(() {
        _form.email = _email.text;
        setState(() {});
      });
    _studentNumber = TextEditingController(text: _form.studentNumber)
      ..addListener(() {
        _form.studentNumber = _studentNumber.text;
        setState(() {});
      });
  }

  @override
  void dispose() {
    _firstName.dispose();
    _middleName.dispose();
    _lastName.dispose();
    _email.dispose();
    _studentNumber.dispose();
    super.dispose();
  }

  Future<void> _onPop() async {
    if (!_form.anyDirty) {
      Navigator.of(context).pop();
      return;
    }
    final go = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Discard changes?'),
        content:
            const Text('Edits to this student will be lost if you leave now.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Keep editing')),
          TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Discard')),
        ],
      ),
    );
    if (go == true && mounted) Navigator.of(context).pop();
  }

  Future<void> _saveIdentity() async {
    final err = _form.validateIdentity();
    if (err != null) {
      setState(() => _identityError = err);
      return;
    }
    final patch = _form.identityPatch();
    if (patch.isEmpty) return;
    setState(() {
      _savingIdentity = true;
      _identityError = null;
    });
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(profileRepositoryProvider).updateUser(
            widget.user.id,
            patch,
          );
      if (!mounted) return;
      // Refresh list so the new name/email shows up on pop.
      ref.invalidate(studentsProvider);
      // Re-seed the form's "original" with the saved values so dirty
      // tracking flips off after save. Cleanest path: pop and let the
      // detail screen refetch — but we want partial saves to feel
      // immediate, so we manually clear dirtiness by rebuilding the form
      // from the patched user. Simplest impl: pop on full success below;
      // for partial (only identity saved), refresh state by re-creating
      // the underlying controllers' baseline values.
      // For v1 we keep it simple: keep the user on-screen with the new
      // values; dirtiness now reads as clean because the controllers
      // hold the values that equal the patch we just sent.
      _refreshBaselineFromControllers();
      messenger.showSnackBar(
        const SnackBar(content: Text('Identity updated.')),
      );
    } on ApiException catch (e) {
      if (mounted) setState(() => _identityError = e.message);
    } catch (_) {
      if (mounted) setState(() => _identityError = 'Could not save identity.');
    } finally {
      if (mounted) setState(() => _savingIdentity = false);
    }
  }

  Future<void> _saveAcademics() async {
    final err = _form.validateAcademics();
    if (err != null) {
      setState(() => _academicsError = err);
      return;
    }
    final patch = _form.academicsPatch();
    if (patch.isEmpty) return;

    // Capture the messenger BEFORE the first async gap (the confirm dialog).
    // Otherwise the use-after-await analyzer trips on later `context` reads.
    final messenger = ScaffoldMessenger.of(context);

    if (_form.statusChangeIsDestructive) {
      final ok = await _confirmDestructiveStatus();
      if (ok != true) return;
    }

    final profileId = widget.user.studentProfile?.id;
    if (profileId == null) {
      setState(() => _academicsError =
          'This account has no student profile to edit.');
      return;
    }

    setState(() {
      _savingAcademics = true;
      _academicsError = null;
    });
    try {
      await ref
          .read(profileRepositoryProvider)
          .updateStudentProfile(profileId, patch);
      if (!mounted) return;
      ref.invalidate(studentsProvider);
      _refreshBaselineFromControllers();
      messenger.showSnackBar(
        const SnackBar(content: Text('Student profile updated.')),
      );
    } on ApiException catch (e) {
      if (mounted) setState(() => _academicsError = e.message);
    } catch (_) {
      if (mounted) {
        setState(() => _academicsError = 'Could not save academic details.');
      }
    } finally {
      if (mounted) setState(() => _savingAcademics = false);
    }
  }

  /// After a successful save, snap the form's "initial" to the current
  /// in-memory values so further edits compute dirtiness against the
  /// saved state, not the screen-open state.
  void _refreshBaselineFromControllers() {
    // Re-seed by constructing a fresh form from a UserProfile reflecting
    // the saved values. We don't have the server's returned object handy
    // (we'd need to thread it through), so build a synthetic snapshot
    // from the current in-memory values. Good enough for dirty tracking;
    // on next pop the studentsProvider invalidation forces a real refetch.
    final snapshot = UserProfile(
      id: widget.user.id,
      email: _form.email,
      firstName: _form.firstName,
      middleName: _form.middleName.trim().isEmpty
          ? null
          : _form.middleName,
      lastName: _form.lastName,
      schoolId: widget.user.schoolId,
      isActive: widget.user.isActive,
      roles: widget.user.roles,
      studentProfile: widget.user.studentProfile == null
          ? null
          : StudentProfile(
              id: widget.user.studentProfile!.id,
              userId: widget.user.studentProfile!.userId,
              schoolId: widget.user.studentProfile!.schoolId,
              studentNumber: _form.studentNumber,
              departmentId: _form.departmentId,
              programId: _form.programId,
              yearLevel: _form.yearLevel,
              studentStatus: _form.studentStatus,
              promotionLocked: _form.promotionLocked,
              isFaceRegistered:
                  widget.user.studentProfile!.isFaceRegistered,
              registrationComplete:
                  widget.user.studentProfile!.registrationComplete,
            ),
    );
    final fresh = EditStudentForm.fromUser(snapshot);
    // Carry over the current values (which now equal initial == clean).
    _form.firstName = fresh.firstName;
    _form.middleName = fresh.middleName;
    _form.lastName = fresh.lastName;
    _form.email = fresh.email;
    _form.studentNumber = fresh.studentNumber;
    _form.departmentId = fresh.departmentId;
    _form.programId = fresh.programId;
    _form.yearLevel = fresh.yearLevel;
    _form.studentStatus = fresh.studentStatus;
    _form.promotionLocked = fresh.promotionLocked;
    // Re-point the form's `_initial` by replacing the form entirely.
    // We can't mutate the form's _initial directly, so swap the whole
    // object via `setState` and re-bind controllers.
    setState(() {
      _formOverride = fresh;
    });
  }

  /// When the underlying [_form] is rebuilt after a save, we keep
  /// dirtiness false by pointing the UI at this fresh snapshot.
  EditStudentForm? _formOverride;
  EditStudentForm get _f => _formOverride ?? _form;

  Future<bool?> _confirmDestructiveStatus() => showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text('Confirm status change'),
          content: Text(
            'Setting status to ${_friendlyStatus(_f.studentStatus)} will '
            'block sign-in for this student and remove them from active '
            'rosters. Continue?',
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Cancel')),
            TextButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Continue')),
          ],
        ),
      );

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final f = _f;
    return PopScope(
      canPop: !f.anyDirty,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _onPop();
      },
      child: AppScaffold(
        title: 'Edit student',
        actions: [
          if (f.anyDirty)
            TextButton(
              onPressed: _onPop,
              child: Text('Discard', style: TextStyle(color: t.absent)),
            ),
        ],
        body: ListView(
          padding: const EdgeInsets.fromLTRB(
              AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
          children: staggered([
            _IdentityCard(
              firstName: _firstName,
              middleName: _middleName,
              lastName: _lastName,
              email: _email,
              error: _identityError,
              saving: _savingIdentity,
              dirty: f.identityDirty,
              onSave: _saveIdentity,
            ),
            const SizedBox(height: AppSpacing.x12),
            _AcademicsCard(
              studentNumber: _studentNumber,
              departmentId: f.departmentId,
              programId: f.programId,
              yearLevel: f.yearLevel,
              status: f.studentStatus,
              promotionLocked: f.promotionLocked,
              onDepartmentChanged: (v) => setState(() {
                f.departmentId = v;
                // Reset program when college changes — the program list is
                // filtered by department.
                f.programId = null;
              }),
              onProgramChanged: (v) => setState(() => f.programId = v),
              onYearChanged: (v) => setState(() => f.yearLevel = v),
              onStatusChanged: (v) => setState(() => f.studentStatus = v),
              onPromotionLockChanged: (v) =>
                  setState(() => f.promotionLocked = v),
              error: _academicsError,
              saving: _savingAcademics,
              dirty: f.academicsDirty,
              onSave: _saveAcademics,
            ),
          ]),
        ),
      ),
    );
  }
}

// ─── Identity card ───────────────────────────────────────────────────────
class _IdentityCard extends StatelessWidget {
  const _IdentityCard({
    required this.firstName,
    required this.middleName,
    required this.lastName,
    required this.email,
    required this.error,
    required this.saving,
    required this.dirty,
    required this.onSave,
  });
  final TextEditingController firstName;
  final TextEditingController middleName;
  final TextEditingController lastName;
  final TextEditingController email;
  final String? error;
  final bool saving;
  final bool dirty;
  final VoidCallback onSave;

  @override
  Widget build(BuildContext context) {
    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionHeader(label: 'IDENTITY'),
          const SizedBox(height: AppSpacing.x12),
          _FormField(
            controller: firstName,
            label: 'First name',
            textInputAction: TextInputAction.next,
          ),
          const SizedBox(height: AppSpacing.x12),
          _FormField(
            controller: middleName,
            label: 'Middle name (optional)',
            textInputAction: TextInputAction.next,
          ),
          const SizedBox(height: AppSpacing.x12),
          _FormField(
            controller: lastName,
            label: 'Last name',
            textInputAction: TextInputAction.next,
          ),
          const SizedBox(height: AppSpacing.x12),
          _FormField(
            controller: email,
            label: 'Email',
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.done,
          ),
          if (error != null) ...[
            const SizedBox(height: AppSpacing.x12),
            _ErrorPill(message: error!),
          ],
          const SizedBox(height: AppSpacing.x16),
          AuraButton(
            label: 'Save identity',
            icon: Icons.save_rounded,
            onPressed: dirty && !saving ? onSave : null,
            loading: saving,
          ),
        ],
      ),
    );
  }
}

// ─── Academics card ──────────────────────────────────────────────────────
class _AcademicsCard extends ConsumerWidget {
  const _AcademicsCard({
    required this.studentNumber,
    required this.departmentId,
    required this.programId,
    required this.yearLevel,
    required this.status,
    required this.promotionLocked,
    required this.onDepartmentChanged,
    required this.onProgramChanged,
    required this.onYearChanged,
    required this.onStatusChanged,
    required this.onPromotionLockChanged,
    required this.error,
    required this.saving,
    required this.dirty,
    required this.onSave,
  });

  final TextEditingController studentNumber;
  final int? departmentId;
  final int? programId;
  final int yearLevel;
  final String status;
  final bool promotionLocked;

  final ValueChanged<int?> onDepartmentChanged;
  final ValueChanged<int?> onProgramChanged;
  final ValueChanged<int> onYearChanged;
  final ValueChanged<String> onStatusChanged;
  final ValueChanged<bool> onPromotionLockChanged;

  final String? error;
  final bool saving;
  final bool dirty;
  final VoidCallback onSave;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    final depts = ref.watch(departmentsProvider).valueOrNull ?? const [];
    final allProgs = ref.watch(programsProvider).valueOrNull ?? const [];
    // Filter programs by the selected department, matching the existing
    // _AssignSheet behaviour in student_detail_screen (pre-redesign).
    final progs = departmentId == null
        ? allProgs
        : allProgs
            .where((p) =>
                p.departmentIds.isEmpty || p.departmentIds.contains(departmentId))
            .toList();
    final progValid = progs.any((p) => p.id == programId) ? programId : null;

    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionHeader(label: 'ACADEMICS'),
          const SizedBox(height: AppSpacing.x12),
          _FormField(
            controller: studentNumber,
            label: 'Student number',
            mono: true,
            textInputAction: TextInputAction.next,
          ),
          const SizedBox(height: AppSpacing.x16),
          DropdownButtonFormField<int>(
            value: departmentId,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'College'),
            items: [
              for (final d in depts)
                DropdownMenuItem(value: d.id, child: Text(d.name)),
            ],
            onChanged: onDepartmentChanged,
          ),
          const SizedBox(height: AppSpacing.x16),
          DropdownButtonFormField<int>(
            value: progValid,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Program'),
            items: [
              for (final p in progs)
                DropdownMenuItem(value: p.id, child: Text(p.name)),
            ],
            onChanged: onProgramChanged,
          ),
          const SizedBox(height: AppSpacing.x20),
          Text('YEAR LEVEL',
              style: textTheme.labelMedium?.copyWith(
                color: t.textSecondary,
                letterSpacing: 0.8,
              )),
          const SizedBox(height: AppSpacing.x8),
          _YearSegmented(value: yearLevel, onChanged: onYearChanged),
          const SizedBox(height: AppSpacing.x20),
          Text('STATUS',
              style: textTheme.labelMedium?.copyWith(
                color: t.textSecondary,
                letterSpacing: 0.8,
              )),
          const SizedBox(height: AppSpacing.x8),
          _StatusChipSelector(value: status, onChanged: onStatusChanged),
          const SizedBox(height: AppSpacing.x20),
          _PromotionLockRow(
            value: promotionLocked,
            onChanged: onPromotionLockChanged,
          ),
          if (error != null) ...[
            const SizedBox(height: AppSpacing.x12),
            _ErrorPill(message: error!),
          ],
          const SizedBox(height: AppSpacing.x16),
          AuraButton(
            label: 'Save academics',
            icon: Icons.save_rounded,
            onPressed: dirty && !saving ? onSave : null,
            loading: saving,
          ),
        ],
      ),
    );
  }
}

// ─── Year segmented control ──────────────────────────────────────────────
class _YearSegmented extends StatelessWidget {
  const _YearSegmented({required this.value, required this.onChanged});
  final int value;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return Row(
      children: [
        for (var i = 1; i <= 5; i++)
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(right: i == 5 ? 0 : 4),
              child: GestureDetector(
                onTap: () {
                  if (i != value) HapticFeedback.selectionClick();
                  onChanged(i);
                },
                child: AnimatedContainer(
                  duration: reduce ? Duration.zero : AppMotion.press,
                  curve: AppMotion.easeOut,
                  height: 44,
                  decoration: BoxDecoration(
                    color: i == value ? t.accent : t.surfaceAlt,
                    borderRadius: BorderRadius.circular(AppRadii.control),
                    border: Border.all(color: t.border),
                  ),
                  alignment: Alignment.center,
                  child: Text(
                    '$i',
                    style: AppTypography.mono(
                      size: 16,
                      weight: FontWeight.w700,
                      color: i == value ? t.onAccent : t.ink,
                    ),
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

// ─── Status chip selector ────────────────────────────────────────────────
class _StatusChipSelector extends StatelessWidget {
  const _StatusChipSelector({required this.value, required this.onChanged});
  final String value;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: AppSpacing.x8,
      runSpacing: AppSpacing.x8,
      children: [
        for (final s in EditStudentForm.statuses)
          _StatusChip(
            status: s,
            selected: s == value,
            onTap: () {
              if (s != value) HapticFeedback.selectionClick();
              onChanged(s);
            },
          ),
      ],
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({
    required this.status,
    required this.selected,
    required this.onTap,
  });
  final String status;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final (label, color, icon) = _statusVisual(t, status);
    final bg = selected
        ? color.withOpacity(t.isDark ? 0.30 : 0.18)
        : t.surfaceAlt;
    final fg = selected ? color : t.textSecondary;

    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: reduce ? Duration.zero : const Duration(milliseconds: 180),
        curve: AppMotion.easeOut,
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x12, vertical: 8),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(AppRadii.pill),
          border: Border.all(
            color: selected ? color : t.border,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: fg),
            const SizedBox(width: 6),
            Text(
              label,
              style: textTheme.labelLarge?.copyWith(
                color: fg,
                fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
              ),
            ),
            if (selected) ...[
              const SizedBox(width: 4),
              Icon(Icons.check_rounded, size: 14, color: fg),
            ],
          ],
        ),
      ),
    );
  }
}

String _friendlyStatus(String raw) => switch (raw) {
      'ACTIVE' => 'Active',
      'GRADUATED' => 'Graduated',
      'INACTIVE' => 'Inactive',
      'TRANSFERRED' => 'Transferred',
      'ARCHIVED' => 'Archived',
      _ => raw,
    };

(String, Color, IconData) _statusVisual(t, String raw) {
  return switch (raw) {
    'ACTIVE' => ('Active', t.present, Icons.check_circle_rounded),
    'GRADUATED' =>
      ('Graduated', t.accentDark, Icons.workspace_premium_rounded),
    'INACTIVE' => ('Inactive', t.textMuted, Icons.pause_circle_rounded),
    'TRANSFERRED' => ('Transferred', t.sg, Icons.swap_horiz_rounded),
    'ARCHIVED' => ('Archived', t.absent, Icons.archive_rounded),
    _ => (raw, t.textMuted, Icons.help_outline_rounded),
  };
}

// ─── Promotion lock row ──────────────────────────────────────────────────
class _PromotionLockRow extends StatelessWidget {
  const _PromotionLockRow({required this.value, required this.onChanged});
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x12, vertical: AppSpacing.x8),
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: BorderRadius.circular(AppRadii.control),
      ),
      child: Row(
        children: [
          Icon(Icons.lock_clock_rounded, size: 20, color: t.textSecondary),
          const SizedBox(width: AppSpacing.x12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Promotion lock', style: textTheme.titleLarge),
                Text(
                  'When on, this student stays in the current year level '
                  'when the school promotes everyone else.',
                  style: textTheme.bodySmall
                      ?.copyWith(color: t.textSecondary),
                ),
              ],
            ),
          ),
          Switch(value: value, onChanged: onChanged),
        ],
      ),
    );
  }
}

// ─── Small reusables ─────────────────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Text(
      label,
      style: textTheme.labelMedium?.copyWith(
        color: t.textMuted,
        letterSpacing: 1.2,
        fontWeight: FontWeight.w700,
      ),
    );
  }
}

class _FormField extends StatelessWidget {
  const _FormField({
    required this.controller,
    required this.label,
    this.keyboardType,
    this.textInputAction,
    this.mono = false,
  });
  final TextEditingController controller;
  final String label;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final bool mono;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      textInputAction: textInputAction,
      style: mono
          ? AppTypography.mono(size: 16, weight: FontWeight.w600, color: t.ink)
          : null,
      decoration: InputDecoration(labelText: label),
    );
  }
}

class _ErrorPill extends StatelessWidget {
  const _ErrorPill({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x12, vertical: AppSpacing.x8),
      decoration: BoxDecoration(
        color: t.absent.withOpacity(0.14),
        borderRadius: BorderRadius.circular(AppRadii.control),
        border: Border.all(color: t.absent.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline_rounded, size: 16, color: t.absent),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              message,
              style: textTheme.bodySmall?.copyWith(color: t.absent),
            ),
          ),
        ],
      ),
    );
  }
}
