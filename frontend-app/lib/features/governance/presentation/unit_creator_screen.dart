import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../../../core/widgets/pressable.dart';
import '../../../core/widgets/section_header.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/governance.dart';
import '../../../shared/models/school.dart';
import '../application/governance_providers.dart';

/// Create a child governance unit under [parent]:
/// - parent SSG → create an **SG** scoped to a college (department), or
/// - parent SG  → create an **ORG** scoped to a program (the college is
///   inherited from the SG).
///
/// Mirrors the backend hierarchy rules so officers can build SSG → SG → ORG
/// from inside the app.
class UnitCreatorScreen extends ConsumerStatefulWidget {
  const UnitCreatorScreen({super.key, required this.parent});

  /// The unit the new child hangs under (its type decides what we create).
  final GovUnitAccess parent;

  @override
  ConsumerState<UnitCreatorScreen> createState() => _UnitCreatorScreenState();
}

class _UnitCreatorScreenState extends ConsumerState<UnitCreatorScreen> {
  final _code = TextEditingController();
  final _name = TextEditingController();
  int? _departmentId; // chosen college (SG mode)
  int? _programId; // chosen program (ORG mode)
  bool _busy = false;
  String? _error;

  String get _childType => widget.parent.type == 'SSG' ? 'SG' : 'ORG';
  bool get _isSg => _childType == 'SG';

  Color get _accent => _isSg ? AppColors.sg : AppColors.accentDark;

  @override
  void dispose() {
    _code.dispose();
    _name.dispose();
    super.dispose();
  }

  /// Gently prefill the name + code from a picked college/program when the
  /// fields are still empty — the officer can always edit them.
  void _prefillFrom(String label) {
    if (_name.text.trim().isEmpty) {
      _name.text = _isSg ? '$label Student Government' : '$label Organization';
    }
    if (_code.text.trim().isEmpty) {
      final slug = label
          .toUpperCase()
          .replaceAll(RegExp('[^A-Z0-9]+'), '')
          .padRight(2, 'X');
      final n = slug.length > 8 ? 8 : slug.length;
      _code.text = '${slug.substring(0, n)}-$_childType';
    }
    setState(() {});
  }

  Future<void> _submit() async {
    final code = _code.text.trim();
    final name = _name.text.trim();
    if (code.length < 2 || code.length > 50) {
      setState(() => _error = 'Unit code must be 2–50 characters.');
      return;
    }
    if (name.length < 2 || name.length > 255) {
      setState(() => _error = 'Unit name must be 2–255 characters.');
      return;
    }
    if (_isSg && _departmentId == null) {
      setState(() => _error = 'Pick a college for this SG.');
      return;
    }
    if (!_isSg && _programId == null) {
      setState(() => _error = 'Pick a program for this ORG.');
      return;
    }

    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await createGovernanceUnit(
        ref,
        code: code,
        name: name,
        type: _childType,
        parentUnitId: widget.parent.id,
        departmentId: _isSg ? _departmentId : null,
        programId: _isSg ? null : _programId,
      );
      navigator.pop();
      messenger.showSnackBar(SnackBar(
          content: Text(_isSg ? 'College SG created.' : 'Program ORG created.')));
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not create the unit.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return AppScaffold(
      title: _isSg ? 'Create college SG' : 'Create program ORG',
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
        children: [
          AuraCard(
            color: _accent.withOpacity(0.12),
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                      color: _accent.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(AppRadii.control)),
                  child: Icon(
                      _isSg
                          ? Icons.account_balance_rounded
                          : Icons.workspaces_rounded,
                      color: _accent),
                ),
                const SizedBox(width: AppSpacing.x16),
                Expanded(
                  child: Text(
                    _isSg
                        ? 'A college Student Government under ${widget.parent.name}, scoped to one college.'
                        : 'A program organization under ${widget.parent.name}, scoped to one program.',
                    style:
                        textTheme.bodyMedium?.copyWith(color: t.textSecondary),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.x24),

          // Scope picker
          if (_isSg)
            _CollegePicker(
              selectedId: _departmentId,
              accent: _accent,
              onSelect: (d) {
                _departmentId = d.id;
                _prefillFrom(d.name);
              },
            )
          else
            _OrgScope(
              parentSgId: widget.parent.id,
              selectedProgramId: _programId,
              accent: _accent,
              onSelect: (p) {
                _programId = p.id;
                _prefillFrom(p.name);
              },
            ),
          const SizedBox(height: AppSpacing.x24),

          // Identity
          const SectionHeader(title: 'Details'),
          AuraTextField(
              label: 'Unit code',
              controller: _code,
              hint: _isSg ? 'e.g. COE-SG' : 'e.g. BSCS-ORG'),
          const SizedBox(height: AppSpacing.x16),
          AuraTextField(
              label: 'Unit name',
              controller: _name,
              hint: _isSg
                  ? 'e.g. College of Engineering SG'
                  : 'e.g. Computer Science Organization'),

          if (_error != null) ...[
            const SizedBox(height: AppSpacing.x16),
            Text(_error!,
                style: textTheme.bodySmall?.copyWith(color: t.absent)),
          ],
          const SizedBox(height: AppSpacing.x24),
          AuraButton(
            label: _isSg ? 'Create SG' : 'Create ORG',
            icon: Icons.add_rounded,
            loading: _busy,
            onPressed: _submit,
          ),
        ],
      ),
    );
  }
}

/// College (department) picker for SG creation.
class _CollegePicker extends ConsumerWidget {
  const _CollegePicker(
      {required this.selectedId, required this.accent, required this.onSelect});
  final int? selectedId;
  final Color accent;
  final ValueChanged<Department> onSelect;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(govDepartmentsProvider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SectionHeader(title: 'College'),
        async.when(
          loading: () => const LoadingCardList(count: 4),
          error: (e, _) => ErrorView(
            message: e is ApiException ? e.message : 'Could not load colleges.',
            onRetry: () => ref.invalidate(govDepartmentsProvider),
          ),
          data: (departments) {
            if (departments.isEmpty) {
              return const EmptyState(
                icon: Icons.account_balance_rounded,
                title: 'No colleges yet',
                message: 'Ask the campus admin to add colleges first.',
              );
            }
            return Column(
              children: [
                for (final d in departments)
                  _PickRow(
                    label: d.name,
                    selected: d.id == selectedId,
                    accent: accent,
                    onTap: () => onSelect(d),
                  ),
              ],
            );
          },
        ),
      ],
    );
  }
}

/// ORG scope: shows the inherited college (from the parent SG) and a program
/// picker filtered to that college.
class _OrgScope extends ConsumerWidget {
  const _OrgScope({
    required this.parentSgId,
    required this.selectedProgramId,
    required this.accent,
    required this.onSelect,
  });
  final int parentSgId;
  final int? selectedProgramId;
  final Color accent;
  final ValueChanged<Program> onSelect;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final detailAsync = ref.watch(unitDetailProvider(parentSgId));
    final deptId = detailAsync.valueOrNull?.summary.departmentId;

    final departments =
        ref.watch(govDepartmentsProvider).valueOrNull ?? const <Department>[];
    String collegeName() {
      for (final d in departments) {
        if (d.id == deptId) return d.name;
      }
      return 'the parent SG college';
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SectionHeader(title: 'College'),
        AuraCard(
          child: Row(
            children: [
              Icon(Icons.account_balance_rounded, color: t.textSecondary),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: Text(
                  deptId == null
                      ? 'Inherited from the parent SG'
                      : collegeName(),
                  style: textTheme.titleMedium,
                ),
              ),
              Text('Inherited',
                  style: textTheme.labelSmall?.copyWith(color: t.textMuted)),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.x24),
        const SectionHeader(title: 'Program'),
        if (detailAsync.isLoading)
          const LoadingCardList(count: 4)
        else if (deptId == null)
          ErrorView(
            message: 'Could not resolve the parent SG college.',
            onRetry: () => ref.invalidate(unitDetailProvider(parentSgId)),
          )
        else
          Consumer(builder: (context, ref, _) {
            final async = ref.watch(govProgramsProvider);
            return async.when(
              loading: () => const LoadingCardList(count: 4),
              error: (e, _) => ErrorView(
                message:
                    e is ApiException ? e.message : 'Could not load programs.',
                onRetry: () => ref.invalidate(govProgramsProvider),
              ),
              data: (programs) {
                final scoped = programs
                    .where((p) => p.departmentIds.contains(deptId))
                    .toList();
                if (scoped.isEmpty) {
                  return const EmptyState(
                    icon: Icons.workspaces_rounded,
                    title: 'No programs in this college',
                    message:
                        'Add programs to this college before creating an ORG.',
                  );
                }
                return Column(
                  children: [
                    for (final p in scoped)
                      _PickRow(
                        label: p.name,
                        selected: p.id == selectedProgramId,
                        accent: accent,
                        onTap: () => onSelect(p),
                      ),
                  ],
                );
              },
            );
          }),
      ],
    );
  }
}

/// A single selectable scope row (college or program).
class _PickRow extends StatelessWidget {
  const _PickRow({
    required this.label,
    required this.selected,
    required this.accent,
    required this.onTap,
  });
  final String label;
  final bool selected;
  final Color accent;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.x8),
      child: Pressable(
        onTap: onTap,
        child: AuraCard(
          color: selected ? accent.withOpacity(0.12) : null,
          child: Row(
            children: [
              Expanded(
                child: Text(label,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: textTheme.titleMedium),
              ),
              Icon(
                selected
                    ? Icons.radio_button_checked_rounded
                    : Icons.radio_button_unchecked_rounded,
                color: selected ? accent : t.textMuted,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
