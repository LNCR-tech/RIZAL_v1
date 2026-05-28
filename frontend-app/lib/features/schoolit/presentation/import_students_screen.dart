import 'package:file_picker/file_picker.dart';
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
import '../../../core/widgets/pressable.dart';
import '../../../core/widgets/rise_in.dart';
import '../../../shared/models/import_job.dart';
import '../application/schoolit_providers.dart';
import '../data/schoolit_repository.dart';

/// Bulk-import surface. Three states:
///   * **Pick** — initial upload card + "Choose file" CTA + spec text.
///   * **Preview** — header card (filename + valid/invalid counters) +
///     filter chips (All / Invalid only) + per-row list (status icon,
///     student identity, errors, server-suggested fixes) + either an
///     "Import N students" button (when can_commit) or "Skip invalid
///     rows · import M valid" + "Choose another file" pair.
///   * **Job** — progress bar + counts + error list as the worker runs.
class ImportStudentsScreen extends ConsumerStatefulWidget {
  const ImportStudentsScreen({super.key});

  @override
  ConsumerState<ImportStudentsScreen> createState() =>
      _ImportStudentsScreenState();
}

enum _PreviewFilter { all, invalid }

class _ImportStudentsScreenState extends ConsumerState<ImportStudentsScreen> {
  ImportPreview? _preview;
  String? _fileName;
  String? _jobId;
  ImportJobStatus? _status;
  bool _busy = false;
  String? _error;
  _PreviewFilter _filter = _PreviewFilter.all;

  Future<void> _pick() async {
    setState(() => _error = null);
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['csv', 'xlsx'],
    );
    final file = result?.files.single;
    if (file?.path == null) return;
    setState(() {
      _busy = true;
      _fileName = file!.name;
      _preview = null;
      _status = null;
      _jobId = null;
      _filter = _PreviewFilter.all;
    });
    try {
      final preview = await ref
          .read(schoolItRepositoryProvider)
          .previewImport(file!.path!, file.name);
      if (!mounted) return;
      setState(() {
        _preview = preview;
        // If there are invalid rows, default the filter to "Invalid only"
        // so the operator sees the problems first — that's why they came.
        _filter = preview.invalidRows > 0
            ? _PreviewFilter.invalid
            : _PreviewFilter.all;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not read that file.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _skipInvalidAndCommit() async {
    final p = _preview;
    if (p?.previewToken == null) return;
    final token = p!.previewToken!;
    setState(() {
      _busy = true;
      _error = null;
    });
    final messenger = ScaffoldMessenger.of(context);
    try {
      // Step 1: strip invalid rows on the backend (sets can_commit=true).
      final cleaned = await ref
          .read(schoolItRepositoryProvider)
          .removeInvalidPreviewRows(token);
      if (!mounted) return;
      setState(() => _preview = cleaned);
      messenger.showSnackBar(SnackBar(
        content: Text(
          'Skipped ${p.invalidRows} invalid row${p.invalidRows == 1 ? '' : 's'}. '
          'Importing ${cleaned.validRows} valid…',
        ),
      ));
      // Step 2: queue the now-commit-eligible job. Fall through to _commit.
      await _commit();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Could not skip invalid rows.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _commit() async {
    final token = _preview?.previewToken;
    if (token == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final jobId = await ref
          .read(schoolItRepositoryProvider)
          .commitImport(token);
      if (jobId.isEmpty) throw ApiException('No job id was returned.');
      _jobId = jobId;
      await _poll();
      if (mounted &&
          _status != null &&
          !_status!.isFailed &&
          _status!.successCount > 0) {
        ref.invalidate(studentsProvider);
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not start the import.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _poll() async {
    final jobId = _jobId!;
    while (mounted) {
      final status =
          await ref.read(schoolItRepositoryProvider).importStatus(jobId);
      if (!mounted) return;
      setState(() => _status = status);
      if (status.isDone) break;
      await Future.delayed(const Duration(milliseconds: 1500));
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: 'Import students',
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x16, AppSpacing.x20, 40),
        children: [_content(context)],
      ),
    );
  }

  Widget _content(BuildContext context) {
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final child = _status != null
        ? _StatusView(key: const ValueKey('status'), status: _status!)
        : _preview != null
            ? _previewView(_preview!)
            : _pickerView();

    return AnimatedSwitcher(
      duration: reduce ? Duration.zero : const Duration(milliseconds: 220),
      switchInCurve: AppMotion.easeOut,
      transitionBuilder: (child, anim) => FadeTransition(
        opacity: anim,
        child: ScaleTransition(
          scale: Tween<double>(begin: 0.97, end: 1.0).animate(anim),
          child: child,
        ),
      ),
      child: child,
    );
  }

  // ─── Picker (initial state) ───────────────────────────────────────
  Widget _pickerView() {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Column(
      key: const ValueKey('picker'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: staggered([
        AuraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: t.accent.withOpacity(0.16),
                      borderRadius: BorderRadius.circular(AppRadii.control),
                    ),
                    child: Icon(Icons.upload_file_rounded,
                        color: t.accentDark, size: 22),
                  ),
                  const SizedBox(width: AppSpacing.x12),
                  Expanded(
                    child: Text('Bulk import students',
                        style: textTheme.titleLarge),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.x12),
              Text(
                'Upload a CSV or XLSX. We\'ll preview every row before '
                'anything is written, then you can fix or skip invalid '
                'rows and import the rest.',
                style: textTheme.bodyMedium?.copyWith(color: t.textSecondary),
              ),
              const SizedBox(height: AppSpacing.x12),
              Text('REQUIRED COLUMNS',
                  style: textTheme.labelMedium?.copyWith(
                      color: t.textMuted, letterSpacing: 0.8)),
              const SizedBox(height: 4),
              const Wrap(
                spacing: AppSpacing.x4,
                runSpacing: AppSpacing.x4,
                children: [
                  _ColumnPill('Student_ID'),
                  _ColumnPill('Email'),
                  _ColumnPill('Last Name'),
                  _ColumnPill('First Name'),
                  _ColumnPill('Middle Name', optional: true),
                  _ColumnPill('Department'),
                  _ColumnPill('Course'),
                  _ColumnPill('Year Level', optional: true),
                  _ColumnPill('Status', optional: true),
                ],
              ),
            ],
          ),
        ),
        if (_error != null) ...[
          const SizedBox(height: AppSpacing.x12),
          _ErrorBanner(_error!),
        ],
        const SizedBox(height: AppSpacing.x16),
        AuraButton(
          label: 'Choose file',
          icon: Icons.folder_open_rounded,
          loading: _busy,
          onPressed: _pick,
        ),
      ]),
    );
  }

  // ─── Preview (the centerpiece) ────────────────────────────────────
  Widget _previewView(ImportPreview p) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    final shownRows = _filter == _PreviewFilter.invalid
        ? p.rows.where((r) => !r.isValid).toList()
        : p.rows;
    final totalInList = p.rows.length;

    return Column(
      key: const ValueKey('preview'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: staggered([
        // ── Summary header ──
        AuraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.description_outlined,
                      size: 18, color: t.textSecondary),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(_fileName ?? p.filename,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: textTheme.titleLarge),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.x16),
              Row(
                children: [
                  _BigCounter(
                    label: 'VALID',
                    value: p.validRows,
                    color: t.present,
                  ),
                  const SizedBox(width: AppSpacing.x12),
                  _BigCounter(
                    label: 'INVALID',
                    value: p.invalidRows,
                    color: p.invalidRows > 0 ? t.absent : t.textMuted,
                  ),
                  const SizedBox(width: AppSpacing.x12),
                  _BigCounter(
                    label: 'TOTAL',
                    value: p.totalRows,
                    color: t.textSecondary,
                  ),
                ],
              ),
              if (p.invalidRows > 0) ...[
                const SizedBox(height: AppSpacing.x12),
                Container(
                  padding: const EdgeInsets.all(AppSpacing.x12),
                  decoration: BoxDecoration(
                    color: t.absent.withOpacity(0.10),
                    borderRadius: BorderRadius.circular(AppRadii.control),
                    border: Border.all(color: t.absent.withOpacity(0.25)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.error_outline_rounded,
                          size: 16, color: t.absent),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          '${p.invalidRows} row${p.invalidRows == 1 ? '' : 's'} '
                          'can\'t be imported as-is. Fix and re-upload, '
                          'or skip the invalid rows and import the rest.',
                          style: textTheme.bodySmall
                              ?.copyWith(color: t.absent),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.x12),

        // ── Filter chips (only when both buckets have rows) ──
        if (p.invalidRows > 0 && p.validRows > 0)
          Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.x12),
            child: Row(
              children: [
                _FilterChip(
                  label: 'All',
                  count: totalInList,
                  selected: _filter == _PreviewFilter.all,
                  onTap: () =>
                      setState(() => _filter = _PreviewFilter.all),
                ),
                const SizedBox(width: AppSpacing.x8),
                _FilterChip(
                  label: 'Invalid only',
                  count: p.invalidRows,
                  selected: _filter == _PreviewFilter.invalid,
                  color: t.absent,
                  onTap: () =>
                      setState(() => _filter = _PreviewFilter.invalid),
                ),
              ],
            ),
          ),

        // ── Row list (per-row preview — the headline fix) ──
        if (shownRows.isNotEmpty) ...[
          Padding(
            padding:
                const EdgeInsets.only(bottom: AppSpacing.x8, left: 4),
            child: Text(
              _filter == _PreviewFilter.invalid
                  ? 'INVALID ROWS'
                  : 'ROW PREVIEW (first ${shownRows.length})',
              style: textTheme.labelMedium?.copyWith(
                color: t.textMuted,
                letterSpacing: 0.8,
              ),
            ),
          ),
          for (final row in shownRows)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.x8),
              child: _RowCard(row: row),
            ),
        ] else if (_filter == _PreviewFilter.invalid && p.invalidRows == 0)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: AppSpacing.x32),
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.check_circle_rounded,
                      size: 40, color: t.present),
                  const SizedBox(height: AppSpacing.x8),
                  Text('No invalid rows',
                      style: textTheme.titleLarge),
                ],
              ),
            ),
          ),

        // ── Error banner (transient) ──
        if (_error != null) ...[
          const SizedBox(height: AppSpacing.x12),
          _ErrorBanner(_error!),
        ],

        // ── Action buttons ──
        const SizedBox(height: AppSpacing.x16),
        if (p.canCommit)
          AuraButton(
            label: 'Import ${p.validRows} student'
                '${p.validRows == 1 ? '' : 's'}',
            icon: Icons.cloud_upload_rounded,
            loading: _busy,
            onPressed: _commit,
          )
        else if (p.invalidRows > 0 && p.validRows > 0) ...[
          // Two-button mode: skip-invalid is the primary path now that
          // the operator has seen the details and decided to proceed.
          AuraButton(
            label: 'Skip ${p.invalidRows} invalid · import '
                '${p.validRows} valid',
            icon: Icons.skip_next_rounded,
            loading: _busy,
            onPressed: _skipInvalidAndCommit,
          ),
          const SizedBox(height: AppSpacing.x8),
          AuraButton(
            label: 'Choose another file',
            icon: Icons.folder_open_rounded,
            variant: AuraButtonVariant.tonal,
            onPressed: _busy ? null : _pick,
          ),
        ] else
          // No valid rows at all — only path is to fix and re-upload.
          AuraButton(
            label: 'Choose another file',
            icon: Icons.folder_open_rounded,
            loading: _busy,
            onPressed: _pick,
          ),
      ]),
    );
  }
}

// ─── Per-row card (the missing UI piece) ─────────────────────────────
class _RowCard extends StatelessWidget {
  const _RowCard({required this.row});
  final ImportPreviewRow row;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final valid = row.isValid;
    final tone = valid ? t.present : t.absent;

    return AuraCard(
      padding: const EdgeInsets.all(AppSpacing.x12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 30,
            height: 30,
            decoration: BoxDecoration(
              color: tone.withOpacity(0.18),
              borderRadius: BorderRadius.circular(AppRadii.control),
            ),
            child: Icon(
              valid ? Icons.check_rounded : Icons.error_outline_rounded,
              size: 18,
              color: tone,
            ),
          ),
          const SizedBox(width: AppSpacing.x12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Row(
                  children: [
                    Text(
                      'ROW ${row.row}',
                      style: AppTypography.mono(
                        size: 11,
                        weight: FontWeight.w800,
                        color: t.textMuted,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        row.displayLabel,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: textTheme.titleLarge,
                      ),
                    ),
                  ],
                ),
                if (row.rowData['Email']?.isNotEmpty ?? false) ...[
                  const SizedBox(height: 2),
                  Text(
                    row.rowData['Email']!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: textTheme.bodySmall
                        ?.copyWith(color: t.textSecondary),
                  ),
                ],
                if (row.errors.isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.x8),
                  for (final e in row.errors)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 2),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('• ',
                              style: textTheme.bodySmall
                                  ?.copyWith(color: t.absent)),
                          Expanded(
                            child: Text(
                              e,
                              style: textTheme.bodySmall
                                  ?.copyWith(color: t.absent),
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
                if (row.suggestions.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  for (final s in row.suggestions)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 2),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.lightbulb_outline_rounded,
                              size: 12, color: t.textMuted),
                          const SizedBox(width: 4),
                          Expanded(
                            child: Text(
                              s,
                              style: textTheme.bodySmall?.copyWith(
                                color: t.textMuted,
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Big counter (mono number + label) ───────────────────────────────
class _BigCounter extends StatelessWidget {
  const _BigCounter({
    required this.label,
    required this.value,
    required this.color,
  });
  final String label;
  final int value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.x12),
        decoration: BoxDecoration(
          color: color.withOpacity(t.isDark ? 0.18 : 0.12),
          borderRadius: BorderRadius.circular(AppRadii.control),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label,
                style: textTheme.labelMedium?.copyWith(
                  color: color,
                  letterSpacing: 0.8,
                )),
            const SizedBox(height: 2),
            Text(
              '$value',
              style: AppTypography.mono(
                size: 22,
                weight: FontWeight.w800,
                color: t.ink,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Filter chip ─────────────────────────────────────────────────────
class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.count,
    required this.selected,
    required this.onTap,
    this.color,
  });
  final String label;
  final int count;
  final bool selected;
  final VoidCallback onTap;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final accent = color ?? t.accentDark;
    final fg = selected ? accent : t.textSecondary;
    final bg = selected
        ? accent.withOpacity(t.isDark ? 0.28 : 0.18)
        : t.surfaceAlt;

    return Pressable(
      scale: 0.97,
      haptic: true,
      onTap: () {
        HapticFeedback.selectionClick();
        onTap();
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        curve: AppMotion.easeOut,
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x12, vertical: 6),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(AppRadii.pill),
          border: Border.all(
            color: selected ? accent : t.border,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: textTheme.labelLarge?.copyWith(
                color: fg,
                fontWeight: selected ? FontWeight.w800 : FontWeight.w600,
              ),
            ),
            const SizedBox(width: 6),
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
              decoration: BoxDecoration(
                color: fg.withOpacity(0.20),
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(
                '$count',
                style: AppTypography.mono(
                  size: 11,
                  weight: FontWeight.w800,
                  color: fg,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Column pill (initial picker doc) ────────────────────────────────
class _ColumnPill extends StatelessWidget {
  const _ColumnPill(this.label, {this.optional = false});
  final String label;
  final bool optional;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: optional ? t.surfaceAlt : t.accent.withOpacity(0.18),
        borderRadius: BorderRadius.circular(AppRadii.pill),
        border: Border.all(
          color: optional ? t.border : t.accentDark.withOpacity(0.3),
        ),
      ),
      child: Text(
        optional ? '$label (optional)' : label,
        style: AppTypography.mono(
          size: 11,
          weight: FontWeight.w700,
          color: optional ? t.textSecondary : t.accentDark,
        ),
      ),
    );
  }
}

// ─── Error banner ────────────────────────────────────────────────────
class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner(this.message);
  final String message;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.all(AppSpacing.x12),
      decoration: BoxDecoration(
        color: t.absent.withOpacity(0.14),
        borderRadius: BorderRadius.circular(AppRadii.control),
        border: Border.all(color: t.absent.withOpacity(0.35)),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline_rounded, size: 16, color: t.absent),
          const SizedBox(width: AppSpacing.x8),
          Expanded(
            child: Text(message,
                style:
                    textTheme.bodySmall?.copyWith(color: t.absent)),
          ),
        ],
      ),
    );
  }
}

// ─── Job status view (unchanged shape, tightened spacing) ────────────
class _StatusView extends StatelessWidget {
  const _StatusView({super.key, required this.status});
  final ImportJobStatus status;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final done = status.isDone;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: staggered([
        AuraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                done
                    ? (status.isFailed ? 'Import failed' : 'Import complete')
                    : 'Importing…',
                style: textTheme.titleLarge,
              ),
              const SizedBox(height: AppSpacing.x12),
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: LinearProgressIndicator(
                  value: done
                      ? 1
                      : (status.percentageCompleted / 100).clamp(0, 1),
                  minHeight: 8,
                  backgroundColor: t.surfaceAlt,
                  color: t.accent,
                ),
              ),
              const SizedBox(height: AppSpacing.x12),
              Row(
                children: [
                  _BigCounter(
                    label: 'ADDED',
                    value: status.successCount,
                    color: t.present,
                  ),
                  const SizedBox(width: AppSpacing.x8),
                  _BigCounter(
                    label: 'FAILED',
                    value: status.failedCount,
                    color: status.failedCount > 0 ? t.absent : t.textMuted,
                  ),
                  const SizedBox(width: AppSpacing.x8),
                  _BigCounter(
                    label: 'OF',
                    value: status.totalRows,
                    color: t.textSecondary,
                  ),
                ],
              ),
            ],
          ),
        ),
        if (status.errors.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.x16),
          Text('Errors', style: textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x8),
          for (final e in status.errors.take(50))
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text('Row ${e.row}: ${e.error}',
                  style: textTheme.bodySmall
                      ?.copyWith(color: t.textSecondary)),
            ),
        ],
      ]),
    );
  }
}
