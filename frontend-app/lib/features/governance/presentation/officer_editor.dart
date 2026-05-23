import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../../../core/widgets/section_header.dart';
import '../../../shared/models/governance.dart';
import '../data/governance_repository.dart';

/// Human labels for every governance permission code (mirrors the backend
/// `PermissionCode` catalog). Ordered so the hierarchy-building permission for
/// the unit comes first, then management, then sanctions.
const govPermissionLabels = <String, String>{
  'create_sg': 'Create college SG units',
  'create_org': 'Create program ORG units',
  'manage_members': 'Manage members / officers',
  'assign_permissions': 'Assign permissions',
  'manage_announcements': 'Post announcements',
  'manage_events': 'Manage events',
  'manage_attendance': 'Manage attendance',
  'view_students': 'View students',
  'manage_students': 'Manage students',
  'view_sanctions_dashboard': 'View sanctions dashboard',
  'view_sanctioned_students_list': 'View sanctioned students',
  'view_student_sanction_detail': 'View sanction details',
  'approve_sanction_compliance': 'Approve sanction compliance',
  'configure_event_sanctions': 'Configure event sanctions',
  'export_sanctioned_students': 'Export sanctioned students',
};

/// Permission codes assignable to an officer of [unitType], matching the
/// backend whitelist (`UNIT_MEMBER_PERMISSION_WHITELIST`): only SSG may grant
/// `create_sg`, only SG may grant `create_org`; ORG grants neither.
List<String> permsForType(String unitType) {
  final base = govPermissionLabels.keys
      .where((c) => c != 'create_sg' && c != 'create_org')
      .toList();
  switch (unitType) {
    case 'SSG':
      return ['create_sg', ...base];
    case 'SG':
      return ['create_org', ...base];
    default:
      return base;
  }
}

/// Best-effort display name for a governance member's user.
String govMemberName(GovUserSummary? u) {
  final n = [u?.firstName, u?.lastName]
      .where((e) => (e ?? '').trim().isNotEmpty)
      .join(' ')
      .trim();
  return n.isNotEmpty ? n : (u?.email ?? 'Member');
}

/// Add or edit a governance officer: pick a student (add only), set a position
/// title, and grant the permissions valid for [unitType]. Reused by the
/// campus-admin SSG panel and the governance Members screen so the SSG → SG →
/// ORG chain can be empowered at every level. [onSaved] refreshes the caller's
/// data after a successful save.
class OfficerEditor extends ConsumerStatefulWidget {
  const OfficerEditor({
    super.key,
    required this.unitId,
    required this.unitType,
    this.member,
    this.onSaved,
  });

  final int unitId;
  final String unitType; // SSG | SG | ORG
  final GovernanceMember? member;
  final VoidCallback? onSaved;

  @override
  ConsumerState<OfficerEditor> createState() => _OfficerEditorState();
}

class _OfficerEditorState extends ConsumerState<OfficerEditor> {
  final _position = TextEditingController();
  final _query = TextEditingController();
  final Set<String> _perms = {};
  int? _userId;
  String? _userName;
  List<GovUserSummary> _results = const [];
  bool _searching = false;
  bool _busy = false;
  String? _error;

  bool get _editing => widget.member != null;

  @override
  void initState() {
    super.initState();
    final m = widget.member;
    if (m != null) {
      _userId = m.userId;
      _userName = govMemberName(m.user);
      _position.text = m.positionTitle ?? '';
      _perms.addAll(m.permissionCodes);
    }
  }

  @override
  void dispose() {
    _position.dispose();
    _query.dispose();
    super.dispose();
  }

  Future<void> _search(String q) async {
    if (q.trim().length < 2) {
      setState(() => _results = const []);
      return;
    }
    setState(() => _searching = true);
    try {
      final r = await ref
          .read(governanceRepositoryProvider)
          .searchStudents(q.trim(), unitId: widget.unitId);
      if (mounted) setState(() => _results = r);
    } catch (_) {
      // ignore search errors — show no results
    } finally {
      if (mounted) setState(() => _searching = false);
    }
  }

  Future<void> _save() async {
    if (_userId == null) {
      setState(() => _error = 'Pick a student first.');
      return;
    }
    if (_position.text.trim().isEmpty) {
      setState(() => _error = 'Enter a position (e.g. President).');
      return;
    }
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final repo = ref.read(governanceRepositoryProvider);
      // Only persist codes valid for this unit type (defensive: the checkboxes
      // already restrict to the whitelist).
      final allowed = permsForType(widget.unitType).toSet();
      final codes = _perms.where(allowed.contains).toList();
      if (_editing) {
        await repo.updateMember(widget.member!.id,
            positionTitle: _position.text.trim(), permissionCodes: codes);
      } else {
        await repo.assignMember(widget.unitId,
            userId: _userId!,
            positionTitle: _position.text.trim(),
            permissionCodes: codes);
      }
      widget.onSaved?.call();
      navigator.pop();
      messenger.showSnackBar(SnackBar(
          content: Text(_editing ? 'Officer updated.' : 'Officer added.')));
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not save the officer.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final codes = permsForType(widget.unitType);

    return AppScaffold(
      title: _editing ? 'Edit officer' : 'Add officer',
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
        children: [
          const SectionHeader(title: 'Student'),
          if (_userId != null)
            AuraCard(
              child: Row(
                children: [
                  Icon(Icons.person_rounded, color: t.accentDark),
                  const SizedBox(width: AppSpacing.x12),
                  Expanded(
                      child: Text(_userName ?? 'Selected',
                          style: textTheme.titleLarge)),
                  if (!_editing)
                    TextButton(
                      onPressed: () => setState(() {
                        _userId = null;
                        _userName = null;
                      }),
                      child: const Text('Change'),
                    ),
                ],
              ),
            )
          else ...[
            TextField(
              controller: _query,
              onChanged: _search,
              decoration: const InputDecoration(
                hintText: 'Search students — name, ID, or email',
                prefixIcon: Icon(Icons.search_rounded, size: 20),
              ),
            ),
            if (_searching)
              const Padding(
                padding: EdgeInsets.all(AppSpacing.x16),
                child: Center(child: CircularProgressIndicator()),
              ),
            for (final u in _results)
              Padding(
                padding: const EdgeInsets.only(top: AppSpacing.x8),
                child: AuraCard(
                  onTap: () => setState(() {
                    _userId = u.id;
                    _userName = govMemberName(u);
                    _results = const [];
                    _query.clear();
                  }),
                  child: Row(
                    children: [
                      Expanded(
                          child:
                              Text(govMemberName(u), style: textTheme.titleLarge)),
                      Icon(Icons.add_circle_outline_rounded,
                          color: t.accentDark),
                    ],
                  ),
                ),
              ),
          ],
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Position'),
          AuraTextField(
              label: 'Position title',
              controller: _position,
              hint: 'e.g. President'),
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Permissions'),
          AuraCard(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                for (final code in codes)
                  CheckboxListTile(
                    dense: true,
                    title: Text(govPermissionLabels[code] ?? code,
                        style: textTheme.bodyLarge),
                    value: _perms.contains(code),
                    activeColor: t.accent,
                    onChanged: (v) => setState(() {
                      if (v == true) {
                        _perms.add(code);
                      } else {
                        _perms.remove(code);
                      }
                    }),
                  ),
              ],
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.x16),
            Text(_error!,
                style: textTheme.bodySmall?.copyWith(color: t.absent)),
          ],
          const SizedBox(height: AppSpacing.x24),
          AuraButton(
              label: _editing ? 'Save changes' : 'Add officer',
              loading: _busy,
              onPressed: _save),
        ],
      ),
    );
  }
}
