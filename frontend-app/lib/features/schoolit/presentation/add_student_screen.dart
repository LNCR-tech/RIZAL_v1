import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_text_field.dart';
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
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(schoolItRepositoryProvider).createStudent(
            email: _email.text.trim(),
            firstName: _first.text.trim(),
            lastName: _last.text.trim(),
            studentId: _studentId.text.trim(),
            departmentId: _deptId!,
            programId: _progId!,
            yearLevel: _year,
            status: _status,
          );
      ref.invalidate(studentsProvider);
      navigator.pop(true);
      messenger
          .showSnackBar(const SnackBar(content: Text('Student added.')));
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
