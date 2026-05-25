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
import '../../../shared/models/profile.dart';
import '../application/schoolit_providers.dart';
import '../data/schoolit_repository.dart';
import 'add_student_screen.dart';
import 'import_students_screen.dart';
import 'student_detail_screen.dart';

/// Small dialog to capture a college name (create or rename).
Future<String?> _promptCollegeName(BuildContext context,
    {required String title, required String initial}) {
  final c = TextEditingController(text: initial);
  return showDialog<String>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: Text(title),
      content: TextField(
        controller: c,
        autofocus: true,
        textCapitalization: TextCapitalization.words,
        decoration: const InputDecoration(hintText: 'College name'),
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
        TextButton(
            onPressed: () => Navigator.pop(ctx, c.text),
            child: const Text('Save')),
      ],
    ),
  );
}

/// Users tab — browse students **by college** (department); search jumps to a
/// flat result list. Tap a college to manage its students.
class SchoolItUsersScreen extends ConsumerStatefulWidget {
  const SchoolItUsersScreen({super.key});

  @override
  ConsumerState<SchoolItUsersScreen> createState() =>
      _SchoolItUsersScreenState();
}

class _SchoolItUsersScreenState extends ConsumerState<SchoolItUsersScreen> {
  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x24, AppSpacing.x20, 120);

  Future<void> _addCollege() async {
    final name =
        await _promptCollegeName(context, title: 'New college', initial: '');
    if (!mounted || name == null || name.trim().isEmpty) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(schoolItRepositoryProvider).createDepartment(name.trim());
      ref.invalidate(departmentsProvider);
      messenger.showSnackBar(
          SnackBar(content: Text('College "${name.trim()}" added.')));
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  Future<void> _renameCollege(int id, String current) async {
    final name = await _promptCollegeName(context,
        title: 'Rename college', initial: current);
    if (!mounted || name == null || name.trim().isEmpty) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(schoolItRepositoryProvider).renameDepartment(id, name.trim());
      ref.invalidate(departmentsProvider);
      messenger
          .showSnackBar(const SnackBar(content: Text('College renamed.')));
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  Future<void> _deleteCollege(int id, String name) async {
    final t = AppTokens.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete college?'),
        content: Text(
            '"$name" will be removed. This can\'t be undone, and it will fail '
            'if students are still assigned to it.'),
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
    if (ok != true || !mounted) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(schoolItRepositoryProvider).deleteDepartment(id);
      ref.invalidate(departmentsProvider);
      messenger
          .showSnackBar(const SnackBar(content: Text('College deleted.')));
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final studentsAsync = ref.watch(studentsProvider);
    final depts = ref.watch(departmentsProvider).valueOrNull ?? [];

    Widget header(int total) => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Users by College', style: textTheme.displaySmall),
                      Text('$total students total',
                          style: textTheme.bodyLarge
                              ?.copyWith(color: t.textSecondary)),
                    ],
                  ),
                ),
                IconButton.filledTonal(
                  tooltip: 'Add college',
                  icon: const Icon(Icons.domain_add_rounded),
                  onPressed: _addCollege,
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.x24),
          ],
        );

    return RefreshIndicator(
      color: t.accent,
      backgroundColor: t.surface,
      onRefresh: () => ref.refresh(studentsProvider.future),
      child: studentsAsync.when(
        loading: () => ListView(
            padding: _pad,
            children: [header(0), const LoadingCardList(count: 5)]),
        error: (e, _) => ListView(
          padding: _pad,
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            header(0),
            ErrorView(
              message: e is ApiException ? e.message : 'Could not load users.',
              onRetry: () => ref.invalidate(studentsProvider),
            ),
          ],
        ),
        data: (students) {
          final counts = <int, int>{};
          var unassigned = 0;
          for (final s in students) {
            if (s.studentProfile == null) continue; // students only
            final did = s.studentProfile?.departmentId;
            if (did == null) {
              unassigned++;
            } else {
              counts[did] = (counts[did] ?? 0) + 1;
            }
          }
          final colleges = <Widget>[
            for (final d in depts)
              _CollegeCard(
                name: d.name,
                count: counts[d.id] ?? 0,
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) =>
                        CollegeStudentsScreen(deptId: d.id, deptName: d.name))),
                onEdit: () => _renameCollege(d.id, d.name),
                onDelete: () => _deleteCollege(d.id, d.name),
              ),
            if (unassigned > 0)
              _CollegeCard(
                name: 'Unassigned',
                count: unassigned,
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => const CollegeStudentsScreen(
                        deptId: null, deptName: 'Unassigned'))),
              ),
          ];

          return ListView(
            padding: _pad,
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              header(students.length),
              if (colleges.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: 40),
                  child: EmptyState(
                    icon: Icons.account_balance_outlined,
                    title: 'No colleges yet',
                    message: 'Add departments, then students will group here.',
                  ),
                )
              else
                ...staggered([
                  for (final c in colleges)
                    Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                        child: c),
                ]),
            ],
          );
        },
      ),
    );
  }
}

class _CollegeCard extends StatelessWidget {
  const _CollegeCard(
      {required this.name,
      required this.count,
      required this.onTap,
      this.onEdit,
      this.onDelete});
  final String name;
  final int count;
  final VoidCallback onTap;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Pressable(
      onTap: onTap,
      child: AuraCard(
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                  color: t.accent.withOpacity(0.16),
                  borderRadius: BorderRadius.circular(AppRadii.control)),
              child: Icon(Icons.account_balance_rounded, color: t.accentDark),
            ),
            const SizedBox(width: AppSpacing.x16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: textTheme.titleLarge),
                  Text('$count student${count == 1 ? '' : 's'}',
                      style:
                          textTheme.bodySmall?.copyWith(color: t.textSecondary)),
                ],
              ),
            ),
            if (onEdit != null)
              PopupMenuButton<String>(
                tooltip: 'College options',
                icon: Icon(Icons.more_vert_rounded, color: t.textMuted),
                onSelected: (v) =>
                    v == 'edit' ? onEdit!() : onDelete?.call(),
                itemBuilder: (_) => const [
                  PopupMenuItem(value: 'edit', child: Text('Rename')),
                  PopupMenuItem(value: 'delete', child: Text('Delete')),
                ],
              )
            else
              Icon(Icons.chevron_right_rounded, color: t.textMuted),
          ],
        ),
      ),
    );
  }
}

/// Students within one college (department), with search + add.
class CollegeStudentsScreen extends ConsumerStatefulWidget {
  const CollegeStudentsScreen(
      {super.key, required this.deptId, required this.deptName});
  final int? deptId;
  final String deptName;

  @override
  ConsumerState<CollegeStudentsScreen> createState() =>
      _CollegeStudentsScreenState();
}

class _CollegeStudentsScreenState extends ConsumerState<CollegeStudentsScreen> {
  final _query = TextEditingController();

  @override
  void dispose() {
    _query.dispose();
    super.dispose();
  }

  Future<void> _rename() async {
    final name = await _promptCollegeName(context,
        title: 'Rename college', initial: widget.deptName);
    if (!mounted ||
        widget.deptId == null ||
        name == null ||
        name.trim().isEmpty) {
      return;
    }
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    try {
      await ref
          .read(schoolItRepositoryProvider)
          .renameDepartment(widget.deptId!, name.trim());
      ref.invalidate(departmentsProvider);
      navigator.pop();
      messenger
          .showSnackBar(const SnackBar(content: Text('College renamed.')));
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  Future<void> _delete() async {
    final t = AppTokens.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete college?'),
        content: Text(
            '"${widget.deptName}" will be removed. This can\'t be undone, and '
            'it will fail if students are still assigned to it.'),
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
    if (ok != true || widget.deptId == null || !mounted) return;
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    try {
      await ref
          .read(schoolItRepositoryProvider)
          .deleteDepartment(widget.deptId!);
      ref.invalidate(departmentsProvider);
      navigator.pop();
      messenger
          .showSnackBar(const SnackBar(content: Text('College deleted.')));
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final studentsAsync = ref.watch(studentsProvider);
    final deptMap = {
      for (final d in ref.watch(departmentsProvider).valueOrNull ?? []) d.id: d.name
    };
    final progMap = {
      for (final p in ref.watch(programsProvider).valueOrNull ?? []) p.id: p.name
    };
    final q = _query.text.trim().toLowerCase();

    return AppScaffold(
      title: widget.deptName,
      actions: widget.deptId == null
          ? null
          : [
              PopupMenuButton<String>(
                onSelected: (v) => v == 'rename' ? _rename() : _delete(),
                itemBuilder: (_) => const [
                  PopupMenuItem(value: 'rename', child: Text('Rename college')),
                  PopupMenuItem(value: 'delete', child: Text('Delete college')),
                ],
              ),
            ],
      body: studentsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: ErrorView(
            message: e is ApiException ? e.message : 'Could not load students.',
            onRetry: () => ref.invalidate(studentsProvider),
          ),
        ),
        data: (all) {
          final inCollege = all
              .where((u) =>
                  u.studentProfile != null &&
                  u.studentProfile?.departmentId == widget.deptId)
              .where((u) {
            if (q.isEmpty) return true;
            final sp = u.studentProfile;
            return u.displayName.toLowerCase().contains(q) ||
                (u.email ?? '').toLowerCase().contains(q) ||
                (sp?.studentNumber ?? '').toLowerCase().contains(q);
          }).toList();

          return ListView(
            padding: const EdgeInsets.fromLTRB(
                AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
            children: [
              Row(
                children: [
                  Expanded(
                    child: AuraButton(
                      label: 'Manual Add',
                      icon: Icons.person_add_alt_1_rounded,
                      variant: AuraButtonVariant.tonal,
                      onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                          builder: (_) =>
                              AddStudentScreen(departmentId: widget.deptId))),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.x12),
                  Expanded(
                    child: AuraButton(
                      label: 'Bulk Import',
                      icon: Icons.upload_file_rounded,
                      variant: AuraButtonVariant.tonal,
                      onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                          builder: (_) => const ImportStudentsScreen())),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.x16),
              TextField(
                controller: _query,
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  hintText: 'Search this college',
                  prefixIcon: Icon(Icons.search_rounded, size: 20),
                ),
              ),
              const SizedBox(height: AppSpacing.x16),
              if (inCollege.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: 40),
                  child: EmptyState(
                    icon: Icons.people_outline_rounded,
                    title: 'No students',
                    message: 'Tap "Add student" to enroll one here.',
                  ),
                )
              else
                for (final u in inCollege)
                  Padding(
                    key: ValueKey(u.id),
                    padding: const EdgeInsets.only(bottom: AppSpacing.x12),
                    child: StudentCard(
                      user: u,
                      department: deptMap[u.studentProfile?.departmentId],
                      program: progMap[u.studentProfile?.programId],
                    ),
                  ),
            ],
          );
        },
      ),
    );
  }
}

class StudentCard extends StatelessWidget {
  const StudentCard({super.key, required this.user, this.department, this.program});
  final UserProfile user;
  final String? department;
  final String? program;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final sp = user.studentProfile;
    return AuraCard(
      onTap: () => Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => StudentDetailScreen(
            user: user, departmentName: department, programName: program),
      )),
      child: Row(
        children: [
          CircleAvatar(
            radius: 22,
            backgroundColor: t.surfaceAlt,
            child: Text(user.initials,
                style: textTheme.titleLarge?.copyWith(color: t.ink)),
          ),
          const SizedBox(width: AppSpacing.x16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(user.displayName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: textTheme.titleLarge),
                Text(
                  [
                    if (sp?.studentNumber != null) sp!.studentNumber!,
                    if (program != null) program!,
                  ].join(' · '),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: textTheme.bodySmall?.copyWith(color: t.textSecondary),
                ),
              ],
            ),
          ),
          Icon(Icons.chevron_right_rounded, color: t.textMuted),
        ],
      ),
    );
  }
}
