import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/pressable.dart';
import '../../../core/widgets/rise_in.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/school.dart';
import '../application/schoolit_providers.dart';
import '../data/schoolit_repository.dart';

/// Campus-admin (School IT) screen to manage academic **programs** — list, add,
/// rename, reassign colleges, and delete. Mirrors the college manager in
/// `schoolit_users_screen.dart`; backed by `/api/programs/`.
class ProgramsScreen extends ConsumerWidget {
  const ProgramsScreen({super.key});

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x12, AppSpacing.x20, 120);

  void _openEditor(BuildContext context, {Program? existing}) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _ProgramEditorSheet(existing: existing),
    );
  }

  Future<void> _delete(BuildContext context, WidgetRef ref, Program p) async {
    final t = AppTokens.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete program?'),
        content: Text(
            '"${p.name}" will be removed. This can\'t be undone, and it will '
            'fail if students are still assigned to it.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: Text('Delete', style: TextStyle(color: t.absent))),
        ],
      ),
    );
    if (ok != true || !context.mounted) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(schoolItRepositoryProvider).deleteProgram(p.id);
      ref.invalidate(programsProvider);
      messenger.showSnackBar(const SnackBar(content: Text('Program deleted.')));
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final programsAsync = ref.watch(programsProvider);
    final deptName = {
      for (final d in ref.watch(departmentsProvider).valueOrNull ?? []) d.id: d.name
    };

    Widget countLine(int n) => Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.x16),
          child: Text(n == 1 ? '1 program' : '$n programs',
              style: textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
        );

    return AppScaffold(
      title: 'Programs',
      actions: [
        IconButton(
          tooltip: 'Add program',
          icon: const Icon(Icons.add_rounded),
          onPressed: () => _openEditor(context),
        ),
      ],
      body: RefreshIndicator(
        color: t.accent,
        backgroundColor: t.surface,
        onRefresh: () => ref.refresh(programsProvider.future),
        child: programsAsync.when(
          loading: () => ListView(
            padding: _pad,
            children: const [LoadingCardList(count: 5)],
          ),
          error: (e, _) => ListView(
            padding: _pad,
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              ErrorView(
                message:
                    e is ApiException ? e.message : 'Could not load programs.',
                onRetry: () => ref.invalidate(programsProvider),
              ),
            ],
          ),
          data: (programs) => ListView(
            padding: _pad,
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              countLine(programs.length),
              if (programs.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: 40),
                  child: EmptyState(
                    icon: Icons.menu_book_outlined,
                    title: 'No programs yet',
                    message: 'Tap + to add your first academic program.',
                  ),
                )
              else
                ...staggered([
                  for (final p in programs)
                    Padding(
                      key: ValueKey(p.id),
                      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                      child: _ProgramCard(
                        program: p,
                        colleges: [
                          for (final id in p.departmentIds)
                            if (deptName[id] != null) deptName[id]!,
                        ],
                        onEdit: () => _openEditor(context, existing: p),
                        onDelete: () => _delete(context, ref, p),
                      ),
                    ),
                ]),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProgramCard extends StatelessWidget {
  const _ProgramCard({
    required this.program,
    required this.colleges,
    required this.onEdit,
    required this.onDelete,
  });

  final Program program;
  final List<String> colleges;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final subtitle = colleges.isEmpty
        ? 'No college assigned'
        : (colleges.length <= 2
            ? colleges.join(' · ')
            : '${colleges.take(2).join(' · ')} +${colleges.length - 2}');

    return Pressable(
      onTap: onEdit,
      child: AuraCard(
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                  color: t.sg.withOpacity(0.16),
                  borderRadius: BorderRadius.circular(AppRadii.control)),
              child: Icon(Icons.menu_book_rounded, color: t.sg),
            ),
            const SizedBox(width: AppSpacing.x16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(program.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: textTheme.titleLarge),
                  Text(subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style:
                          textTheme.bodySmall?.copyWith(color: t.textSecondary)),
                ],
              ),
            ),
            PopupMenuButton<String>(
              tooltip: 'Program options',
              icon: Icon(Icons.more_vert_rounded, color: t.textMuted),
              onSelected: (v) => v == 'edit' ? onEdit() : onDelete(),
              itemBuilder: (_) => const [
                PopupMenuItem(value: 'edit', child: Text('Edit')),
                PopupMenuItem(value: 'delete', child: Text('Delete')),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Bottom-sheet editor to add or edit a program: name + college multi-select.
class _ProgramEditorSheet extends ConsumerStatefulWidget {
  const _ProgramEditorSheet({this.existing});
  final Program? existing;

  @override
  ConsumerState<_ProgramEditorSheet> createState() =>
      _ProgramEditorSheetState();
}

class _ProgramEditorSheetState extends ConsumerState<_ProgramEditorSheet> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _name;
  late final Set<int> _selected;
  bool _saving = false;

  bool get _isEdit => widget.existing != null;

  @override
  void initState() {
    super.initState();
    _name = TextEditingController(text: widget.existing?.name ?? '');
    _selected = {...?widget.existing?.departmentIds};
  }

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    final repo = ref.read(schoolItRepositoryProvider);
    final name = _name.text.trim();
    final ids = _selected.toList();
    try {
      if (_isEdit) {
        await repo.updateProgram(widget.existing!.id,
            name: name, departmentIds: ids);
      } else {
        await repo.createProgram(name, departmentIds: ids);
      }
      ref.invalidate(programsProvider);
      navigator.pop();
      messenger.showSnackBar(SnackBar(
          content:
              Text(_isEdit ? 'Program updated.' : 'Program "$name" added.')));
    } on ApiException catch (e) {
      if (mounted) setState(() => _saving = false);
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    } catch (_) {
      if (mounted) setState(() => _saving = false);
      messenger.showSnackBar(
          const SnackBar(content: Text('Could not save program.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final depts = ref.watch(departmentsProvider).valueOrNull ?? [];

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        ),
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x12, AppSpacing.x20, AppSpacing.x24),
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 36,
                    height: 4,
                    margin: const EdgeInsets.only(bottom: AppSpacing.x16),
                    decoration: BoxDecoration(
                        color: t.border,
                        borderRadius: BorderRadius.circular(2)),
                  ),
                ),
                Text(_isEdit ? 'Edit program' : 'New program',
                    style: textTheme.titleLarge),
                const SizedBox(height: AppSpacing.x16),
                TextFormField(
                  controller: _name,
                  autofocus: true,
                  enabled: !_saving,
                  textCapitalization: TextCapitalization.words,
                  textInputAction: TextInputAction.done,
                  decoration: const InputDecoration(
                    labelText: 'Program name',
                    hintText: 'e.g. BS Computer Science',
                  ),
                  validator: (v) {
                    final s = (v ?? '').trim();
                    if (s.length < 2) return 'Enter at least 2 characters.';
                    if (s.length > 100) return 'Keep it under 100 characters.';
                    return null;
                  },
                  onFieldSubmitted: (_) {
                    if (!_saving) _save();
                  },
                ),
                const SizedBox(height: AppSpacing.x20),
                Text('Colleges', style: textTheme.titleSmall),
                const SizedBox(height: AppSpacing.x4),
                Text('Which college(s) offer this program? (optional)',
                    style: textTheme.bodySmall?.copyWith(color: t.textSecondary)),
                const SizedBox(height: AppSpacing.x12),
                if (depts.isEmpty)
                  Text('No colleges yet — add one in Users by College first.',
                      style: textTheme.bodySmall?.copyWith(color: t.textMuted))
                else
                  Wrap(
                    spacing: AppSpacing.x8,
                    runSpacing: AppSpacing.x8,
                    children: [
                      for (final d in depts)
                        FilterChip(
                          label: Text(d.name),
                          selected: _selected.contains(d.id),
                          onSelected: _saving
                              ? null
                              : (sel) => setState(() {
                                    if (sel) {
                                      _selected.add(d.id);
                                    } else {
                                      _selected.remove(d.id);
                                    }
                                  }),
                        ),
                    ],
                  ),
                const SizedBox(height: AppSpacing.x24),
                AuraButton(
                  label: _isEdit ? 'Save changes' : 'Add program',
                  icon: _isEdit ? Icons.check_rounded : Icons.add_rounded,
                  loading: _saving,
                  onPressed: _saving ? null : _save,
                ),
                const SizedBox(height: AppSpacing.x8),
                AuraButton(
                  label: 'Cancel',
                  variant: AuraButtonVariant.ghost,
                  onPressed: _saving ? null : () => Navigator.of(context).pop(),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
