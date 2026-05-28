import 'dart:async';

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
import '../../../core/widgets/aura_text_field.dart';
import '../../../core/widgets/pressable.dart';
import '../../../core/widgets/rise_in.dart';
import '../application/schoolit_providers.dart';
import '../data/schoolit_repository.dart';

/// Create one student account (no bulk import). Optionally preselect a college.
class AddStudentScreen extends ConsumerStatefulWidget {
  const AddStudentScreen({super.key, this.departmentId});
  final int? departmentId;

  @override
  ConsumerState<AddStudentScreen> createState() => _AddStudentScreenState();
}

class _AddStudentScreenState extends ConsumerState<AddStudentScreen> {
  static const _statuses = [
    'ACTIVE',
    'INACTIVE',
    'GRADUATED',
    'TRANSFERRED',
    'ARCHIVED'
  ];

  final _email = TextEditingController();
  final _first = TextEditingController();
  final _last = TextEditingController();
  final _studentId = TextEditingController();
  int? _deptId;
  int? _progId;
  int _year = 1;
  String _status = 'ACTIVE';
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _deptId = widget.departmentId;
  }

  @override
  void dispose() {
    for (final c in [_email, _first, _last, _studentId]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    if (_email.text.trim().isEmpty ||
        _first.text.trim().isEmpty ||
        _last.text.trim().isEmpty) {
      setState(() => _error = 'Name and email are required.');
      return;
    }
    if (_deptId == null || _progId == null) {
      setState(() => _error = 'Pick a college and a program.');
      return;
    }
    final navigator = Navigator.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });

    final email = _email.text.trim();
    final firstName = _first.text.trim();
    final lastName = _last.text.trim();

    try {
      await ref.read(schoolItRepositoryProvider).createStudent(
            email: email,
            firstName: firstName,
            lastName: lastName,
            studentId: _studentId.text.trim(),
            departmentId: _deptId!,
            programId: _progId!,
            yearLevel: _year,
            status: _status,
          );
      // Await the refetch so the dashboard / college screen below already
      // shows the new student when the credentials sheet opens.
      ref.invalidate(studentsProvider);
      try {
        await ref.read(studentsProvider.future);
      } catch (_) {
        // refetch errors surface on the screen below via its own state
      }
      if (!mounted) return;

      // Mirrors the backend rule in
      // `backend/app/routers/users/students.py` (`create_student_account`):
      //   issued_password = student.last_name.strip().lower() or "password"
      // Computed client-side so the IT admin sees the password instantly
      // without an extra round-trip; backend stays authoritative on the hash.
      final lowerLast = lastName.toLowerCase();
      final defaultPassword = lowerLast.isEmpty ? 'password' : lowerLast;
      final displayName =
          [firstName, lastName].where((s) => s.isNotEmpty).join(' ');

      final addAnother = await _showCredentialsSheet(
        context,
        studentName: displayName.isEmpty ? email : displayName,
        email: email,
        defaultPassword: defaultPassword,
      );
      if (!mounted) return;

      if (addAnother == true) {
        // Keep college + program selected — the IT admin almost always wants
        // to add another student to the same group, so don't make them
        // re-pick. Year level + status persist too (they default to the most
        // common combination already).
        _email.clear();
        _first.clear();
        _last.clear();
        _studentId.clear();
      } else {
        navigator.pop(true);
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not add the student.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final depts = ref.watch(departmentsProvider).valueOrNull ?? [];
    final allProgs = ref.watch(programsProvider).valueOrNull ?? [];
    final progs = _deptId == null
        ? allProgs
        : allProgs
            .where((p) =>
                p.departmentIds.isEmpty || p.departmentIds.contains(_deptId))
            .toList();
    final progValid = progs.any((p) => p.id == _progId) ? _progId : null;

    return AppScaffold(
      title: 'Add student',
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
        children: [
          AuraTextField(
              label: 'Email',
              controller: _email,
              keyboardType: TextInputType.emailAddress),
          const SizedBox(height: AppSpacing.x16),
          Row(
            children: [
              Expanded(child: AuraTextField(label: 'First name', controller: _first)),
              const SizedBox(width: AppSpacing.x12),
              Expanded(child: AuraTextField(label: 'Last name', controller: _last)),
            ],
          ),
          const SizedBox(height: AppSpacing.x16),
          AuraTextField(
              label: 'Student ID', controller: _studentId, hint: 'Optional'),
          const SizedBox(height: AppSpacing.x16),
          _Dropdown<int>(
            label: 'College',
            value: _deptId,
            hint: 'Select college',
            items: [
              for (final d in depts)
                DropdownMenuItem(value: d.id, child: Text(d.name)),
            ],
            onChanged: (v) => setState(() {
              _deptId = v;
              _progId = null;
            }),
          ),
          const SizedBox(height: AppSpacing.x16),
          _Dropdown<int>(
            label: 'Program',
            value: progValid,
            hint: 'Select program',
            items: [
              for (final p in progs)
                DropdownMenuItem(value: p.id, child: Text(p.name)),
            ],
            onChanged: (v) => setState(() => _progId = v),
          ),
          const SizedBox(height: AppSpacing.x16),
          Row(
            children: [
              Expanded(
                child: _Dropdown<int>(
                  label: 'Year level',
                  value: _year,
                  items: [
                    for (final y in [1, 2, 3, 4, 5])
                      DropdownMenuItem(value: y, child: Text('Year $y')),
                  ],
                  onChanged: (v) => setState(() => _year = v ?? 1),
                ),
              ),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: _Dropdown<String>(
                  label: 'Status',
                  value: _status,
                  items: [
                    for (final s in _statuses)
                      DropdownMenuItem(value: s, child: Text(s)),
                  ],
                  onChanged: (v) => setState(() => _status = v ?? 'ACTIVE'),
                ),
              ),
            ],
          ),
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.x16),
            Text(_error!, style: textTheme.bodySmall?.copyWith(color: t.absent)),
          ],
          const SizedBox(height: AppSpacing.x24),
          AuraButton(label: 'Add student', loading: _busy, onPressed: _save),
        ],
      ),
    );
  }
}

class _Dropdown<T> extends StatelessWidget {
  const _Dropdown({
    required this.label,
    required this.value,
    required this.items,
    required this.onChanged,
    this.hint,
  });
  final String label;
  final T? value;
  final List<DropdownMenuItem<T>> items;
  final ValueChanged<T?> onChanged;
  final String? hint;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: textTheme.labelMedium?.copyWith(color: t.textSecondary)),
        const SizedBox(height: 6),
        DropdownButtonFormField<T>(
          value: value,
          isExpanded: true,
          hint: hint == null ? null : Text(hint!),
          items: items,
          onChanged: onChanged,
        ),
      ],
    );
  }
}

/// Modal bottom sheet that reveals the freshly-created student's sign-in
/// credentials. The IT admin needs both pieces (email + temp password) to
/// hand over verbally or in writing; the backend doesn't send a welcome
/// email for the student-create path, so without this sheet the admin would
/// have to *know* the convention.
///
/// Returns `true` when the admin chose "Add another", `false` for "Done",
/// `null` if dismissed by backdrop tap / swipe.
Future<bool?> _showCredentialsSheet(
  BuildContext context, {
  required String studentName,
  required String email,
  required String defaultPassword,
}) {
  return showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    barrierColor: Colors.black54,
    builder: (ctx) => _CredentialsSheet(
      studentName: studentName,
      email: email,
      defaultPassword: defaultPassword,
    ),
  );
}

class _CredentialsSheet extends StatelessWidget {
  const _CredentialsSheet({
    required this.studentName,
    required this.email,
    required this.defaultPassword,
  });

  final String studentName;
  final String email;
  final String defaultPassword;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final brightness = Theme.of(context).brightness;

    return Container(
      constraints: const BoxConstraints(maxWidth: 520),
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: AppRadii.rSheet,
        boxShadow: AppElevation.card(brightness),
      ),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
              AppSpacing.x20, AppSpacing.x12, AppSpacing.x20, AppSpacing.x20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 36,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: AppSpacing.x16),
                  decoration: BoxDecoration(
                    color: t.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              ...staggered([
                Row(
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: t.present.withOpacity(0.16),
                        shape: BoxShape.circle,
                      ),
                      child:
                          Icon(Icons.check_rounded, color: t.present, size: 22),
                    ),
                    const SizedBox(width: AppSpacing.x12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Student created', style: textTheme.titleLarge),
                          Text(
                            studentName,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: textTheme.bodyMedium
                                ?.copyWith(color: t.textSecondary),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.x20),
                Text(
                  'SIGN-IN CREDENTIALS',
                  style: textTheme.labelMedium?.copyWith(
                      color: t.textMuted, letterSpacing: 1.0, fontSize: 11),
                ),
                const SizedBox(height: AppSpacing.x8),
                _CredentialRow(label: 'Email', value: email),
                const SizedBox(height: AppSpacing.x8),
                _CredentialRow(
                    label: 'Temporary password', value: defaultPassword),
                const SizedBox(height: AppSpacing.x12),
                Container(
                  padding: const EdgeInsets.all(AppSpacing.x12),
                  decoration: BoxDecoration(
                    color: t.surfaceAlt,
                    borderRadius: AppRadii.rControl,
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.info_outline_rounded,
                          size: 16, color: t.textSecondary),
                      const SizedBox(width: AppSpacing.x8),
                      Expanded(
                        child: Text(
                          "Password is the student's last name in lowercase. "
                          "They'll be prompted to change it on first sign-in.",
                          style: textTheme.bodySmall
                              ?.copyWith(color: t.textSecondary),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.x20),
                Row(
                  children: [
                    Expanded(
                      child: AuraButton(
                        label: 'Add another',
                        variant: AuraButtonVariant.tonal,
                        onPressed: () => Navigator.of(context).pop(true),
                      ),
                    ),
                    const SizedBox(width: AppSpacing.x12),
                    Expanded(
                      child: AuraButton(
                        label: 'Done',
                        onPressed: () => Navigator.of(context).pop(false),
                      ),
                    ),
                  ],
                ),
              ]),
            ],
          ),
        ),
      ),
    );
  }
}

/// One row in the credentials block: small label, mono value (so the password
/// is unambiguous — no confusion between l/I/1 or 0/O), tappable copy icon
/// that cross-fades to a check for ~1.4s on copy. Press scale + selection
/// haptic come from [Pressable].
class _CredentialRow extends StatefulWidget {
  const _CredentialRow({required this.label, required this.value});
  final String label;
  final String value;

  @override
  State<_CredentialRow> createState() => _CredentialRowState();
}

class _CredentialRowState extends State<_CredentialRow> {
  bool _copied = false;
  Timer? _resetTimer;

  @override
  void dispose() {
    _resetTimer?.cancel();
    super.dispose();
  }

  Future<void> _copy() async {
    await Clipboard.setData(ClipboardData(text: widget.value));
    if (!mounted) return;
    setState(() => _copied = true);
    _resetTimer?.cancel();
    _resetTimer = Timer(const Duration(milliseconds: 1400), () {
      if (mounted) setState(() => _copied = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return Container(
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: AppRadii.rControl,
        border: Border.all(color: t.border),
      ),
      padding: const EdgeInsets.fromLTRB(
          AppSpacing.x16, AppSpacing.x12, AppSpacing.x4, AppSpacing.x12),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.label,
                  style: textTheme.labelMedium
                      ?.copyWith(color: t.textSecondary, fontSize: 12),
                ),
                const SizedBox(height: 2),
                Text(
                  widget.value,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppTypography.mono(
                      size: 15, weight: FontWeight.w600, color: t.ink),
                ),
              ],
            ),
          ),
          Pressable(
            onTap: _copy,
            child: SizedBox(
              width: 48,
              height: 48,
              child: Center(
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 200),
                  switchInCurve: AppMotion.easeOut,
                  switchOutCurve: AppMotion.easeOut,
                  transitionBuilder: (child, anim) => FadeTransition(
                    opacity: anim,
                    child: ScaleTransition(
                      scale:
                          Tween<double>(begin: 0.85, end: 1).animate(anim),
                      child: child,
                    ),
                  ),
                  child: _copied
                      ? Icon(Icons.check_rounded,
                          key: const ValueKey('copied'),
                          color: t.present,
                          size: 20)
                      : Icon(Icons.copy_rounded,
                          key: const ValueKey('copy'),
                          color: t.textSecondary,
                          size: 18),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
