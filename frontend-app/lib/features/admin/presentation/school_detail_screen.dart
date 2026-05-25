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
import '../../../shared/models/admin.dart';
import '../../../shared/models/subscription.dart';
import '../../../shared/utils/formatting.dart';
import '../application/admin_providers.dart';
import '../application/ai_access.dart';
import '../data/admin_repository.dart';

/// School detail — rendered from the [SchoolSummary] already loaded by the list
/// (the deployed backend has no per-school detail GET). Admin can toggle active
/// status and the subscription (the capability lever).
class SchoolDetailScreen extends ConsumerStatefulWidget {
  const SchoolDetailScreen({super.key, required this.school});
  final SchoolSummary school;

  @override
  ConsumerState<SchoolDetailScreen> createState() => _SchoolDetailScreenState();
}

class _SchoolDetailScreenState extends ConsumerState<SchoolDetailScreen> {
  static const _subStatuses = ['active', 'trial', 'suspended'];

  late bool _active = widget.school.activeStatus;
  late String _subscription =
      (widget.school.subscriptionStatus ?? 'trial').toLowerCase();
  bool _busy = false;

  void _snack(String m) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(m)));
    }
  }

  Future<void> _patch({bool? active, String? subscription}) async {
    setState(() => _busy = true);
    try {
      final r = await ref.read(adminRepositoryProvider).updateSchoolStatus(
            widget.school.schoolId,
            active: active,
            subscription: subscription,
          );
      setState(() {
        _active = r.activeStatus;
        if (r.subscriptionStatus != null) {
          _subscription = r.subscriptionStatus!.toLowerCase();
        }
      });
      ref.invalidate(adminSchoolsProvider);
    } on ApiException catch (e) {
      _snack(e.message);
    } catch (_) {
      _snack('Could not update. Please try again.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final s = widget.school;
    final sub = _subStatuses.contains(_subscription) ? _subscription : 'trial';

    return AppScaffold(
      title: s.schoolName ?? 'School',
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
        children: [
          AuraCard(
            child: Column(
              children: [
                _KV('School', s.schoolName ?? '—'),
                const Divider(height: AppSpacing.x24),
                _KV('Code', s.schoolCode ?? '—'),
                if (s.createdAt != null) ...[
                  const Divider(height: AppSpacing.x24),
                  _KV('Created', fmtFullDate(s.createdAt)),
                ],
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.x16),
          AuraCard(
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Active', style: textTheme.titleLarge),
                      Text(
                        _active
                            ? 'School is enabled'
                            : 'Disabled — its campus admins are locked out',
                        style: textTheme.bodySmall?.copyWith(
                            color: _active ? t.textSecondary : t.absent),
                      ),
                    ],
                  ),
                ),
                if (_busy)
                  const SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(strokeWidth: 2))
                else
                  Switch(
                    value: _active,
                    activeColor: t.present,
                    inactiveThumbColor: t.absent,
                    onChanged: (v) => _patch(active: v),
                  ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Subscription'),
          AuraCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Status',
                    style: textTheme.bodyMedium
                        ?.copyWith(color: t.textSecondary)),
                const SizedBox(height: AppSpacing.x12),
                SizedBox(
                  width: double.infinity,
                  child: SegmentedButton<String>(
                    segments: const [
                      ButtonSegment(value: 'active', label: Text('Active')),
                      ButtonSegment(value: 'trial', label: Text('Trial')),
                      ButtonSegment(
                          value: 'suspended', label: Text('Suspended')),
                    ],
                    selected: {sub},
                    showSelectedIcon: false,
                    onSelectionChanged:
                        _busy ? null : (sel) => _patch(subscription: sel.first),
                  ),
                ),
                if (sub == 'suspended') ...[
                  const SizedBox(height: AppSpacing.x8),
                  Text('Suspended schools cannot sign in.',
                      style:
                          textTheme.bodySmall?.copyWith(color: t.absent)),
                ],
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Aura AI'),
          _AiAccessCard(schoolId: s.schoolId),
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Plan & limits'),
          _PlanCard(schoolId: s.schoolId),
        ],
      ),
    );
  }
}

class _AiAccessCard extends ConsumerWidget {
  const _AiAccessCard({required this.schoolId});
  final int schoolId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final enabled = ref.watch(aiAccessProvider(schoolId)).valueOrNull ?? true;
    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                    color: const Color(0xFF8B5CF6),
                    borderRadius: BorderRadius.circular(10)),
                child: const Icon(Icons.auto_awesome_rounded,
                    color: Colors.white, size: 20),
              ),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Aura AI access', style: textTheme.titleLarge),
                    Text('Let this school use the AI assistant',
                        style: textTheme.bodySmall
                            ?.copyWith(color: t.textSecondary)),
                  ],
                ),
              ),
              Switch(
                value: enabled,
                activeColor: t.accent,
                onChanged: (v) async {
                  await ref
                      .read(aiAccessStoreProvider)
                      .setEnabled(schoolId, v);
                  ref.invalidate(aiAccessProvider(schoolId));
                },
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.x8),
          Text(
            'Saved on this device — platform-wide enforcement is a backend follow-up.',
            style: textTheme.bodySmall?.copyWith(color: t.textMuted),
          ),
        ],
      ),
    );
  }
}

class _PlanCard extends ConsumerWidget {
  const _PlanCard({required this.schoolId});
  final int schoolId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final async = ref.watch(subscriptionProvider(schoolId));
    return async.when(
      loading: () => const AuraCard(
        child: Center(
          child: Padding(
            padding: EdgeInsets.all(AppSpacing.x8),
            child: SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(strokeWidth: 2)),
          ),
        ),
      ),
      error: (e, _) => AuraCard(
        child: Text('Plan details unavailable.',
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: t.textMuted)),
      ),
      data: (s) => AuraCard(
        child: Column(
          children: [
            _KV('Plan', s.planName ?? '—'),
            const Divider(height: AppSpacing.x24),
            _KV('User limit', s.userLimit?.toString() ?? '—'),
            const Divider(height: AppSpacing.x24),
            _KV('Events / month', s.eventLimitMonthly?.toString() ?? '—'),
            const Divider(height: AppSpacing.x24),
            _KV('Imports / month', s.importLimitMonthly?.toString() ?? '—'),
            const Divider(height: AppSpacing.x24),
            _KV('Auto-renew', s.autoRenew ? 'On' : 'Off'),
            const SizedBox(height: AppSpacing.x16),
            AuraButton(
              label: 'Edit plan',
              variant: AuraButtonVariant.tonal,
              onPressed: () => showModalBottomSheet<void>(
                context: context,
                isScrollControlled: true,
                backgroundColor: Colors.transparent,
                builder: (_) =>
                    _PlanEditSheet(schoolId: schoolId, current: s),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PlanEditSheet extends ConsumerStatefulWidget {
  const _PlanEditSheet({required this.schoolId, required this.current});
  final int schoolId;
  final SchoolSubscription current;

  @override
  ConsumerState<_PlanEditSheet> createState() => _PlanEditSheetState();
}

class _PlanEditSheetState extends ConsumerState<_PlanEditSheet> {
  late final _plan =
      TextEditingController(text: widget.current.planName ?? '');
  late final _users = TextEditingController(
      text: widget.current.userLimit?.toString() ?? '');
  late final _events = TextEditingController(
      text: widget.current.eventLimitMonthly?.toString() ?? '');
  late final _imports = TextEditingController(
      text: widget.current.importLimitMonthly?.toString() ?? '');
  late bool _autoRenew = widget.current.autoRenew;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    for (final c in [_plan, _users, _events, _imports]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(adminRepositoryProvider).updateSubscription(
            widget.schoolId,
            planName: _plan.text.trim().isEmpty ? null : _plan.text.trim(),
            userLimit: int.tryParse(_users.text.trim()),
            eventLimitMonthly: int.tryParse(_events.text.trim()),
            importLimitMonthly: int.tryParse(_imports.text.trim()),
            autoRenew: _autoRenew,
          );
      ref.invalidate(subscriptionProvider(widget.schoolId));
      if (mounted) Navigator.of(context).pop();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not save the plan.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius:
              const BorderRadius.vertical(top: Radius.circular(AppRadii.sheet)),
        ),
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x16, AppSpacing.x20, AppSpacing.x24),
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
                    borderRadius: BorderRadius.circular(2)),
              ),
            ),
            Text('Edit plan', style: textTheme.titleLarge),
            const SizedBox(height: AppSpacing.x16),
            AuraTextField(label: 'Plan name', controller: _plan),
            const SizedBox(height: AppSpacing.x12),
            AuraTextField(
                label: 'User limit',
                controller: _users,
                keyboardType: TextInputType.number),
            const SizedBox(height: AppSpacing.x12),
            AuraTextField(
                label: 'Events / month',
                controller: _events,
                keyboardType: TextInputType.number),
            const SizedBox(height: AppSpacing.x12),
            AuraTextField(
                label: 'Imports / month',
                controller: _imports,
                keyboardType: TextInputType.number),
            const SizedBox(height: AppSpacing.x8),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Auto-renew'),
              value: _autoRenew,
              activeColor: t.accent,
              onChanged: (v) => setState(() => _autoRenew = v),
            ),
            if (_error != null) ...[
              const SizedBox(height: AppSpacing.x8),
              Text(_error!,
                  style: textTheme.bodySmall?.copyWith(color: t.absent)),
            ],
            const SizedBox(height: AppSpacing.x16),
            AuraButton(label: 'Save plan', loading: _busy, onPressed: _save),
          ],
        ),
      ),
    );
  }
}

class _KV extends StatelessWidget {
  const _KV(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label,
            style: textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
        Flexible(
            child: Text(value,
                textAlign: TextAlign.right, style: textTheme.bodyLarge)),
      ],
    );
  }
}
