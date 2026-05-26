import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../shared/models/import_job.dart';
import '../application/schoolit_providers.dart';
import '../data/schoolit_repository.dart';

class ImportStudentsScreen extends ConsumerStatefulWidget {
  const ImportStudentsScreen({super.key});

  @override
  ConsumerState<ImportStudentsScreen> createState() =>
      _ImportStudentsScreenState();
}

class _ImportStudentsScreenState extends ConsumerState<ImportStudentsScreen> {
  ImportPreview? _preview;
  String? _fileName;
  String? _jobId;
  ImportJobStatus? _status;
  bool _busy = false;
  String? _error;

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
    });
    try {
      final preview = await ref
          .read(schoolItRepositoryProvider)
          .previewImport(file!.path!, file.name);
      if (mounted) setState(() => _preview = preview);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not read that file.');
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
      final jobId =
          await ref.read(schoolItRepositoryProvider).commitImport(token);
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
        padding: const EdgeInsets.all(AppSpacing.x20),
        children: [_content(context)],
      ),
    );
  }

  Widget _content(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    if (_status != null) {
      return _StatusView(status: _status!);
    }

    if (_preview != null) {
      final p = _preview!;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AuraCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_fileName ?? p.filename, style: textTheme.titleLarge),
                const SizedBox(height: AppSpacing.x12),
                Row(
                  children: [
                    _Pill('${p.validRows} valid', t.present),
                    const SizedBox(width: AppSpacing.x8),
                    if (p.invalidRows > 0)
                      _Pill('${p.invalidRows} invalid', t.absent),
                  ],
                ),
                if (p.invalidRows > 0) ...[
                  const SizedBox(height: AppSpacing.x12),
                  Text('Fix invalid rows and re-upload to import everyone.',
                      style: textTheme.bodySmall
                          ?.copyWith(color: t.textSecondary)),
                ],
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.x16),
          if (_error != null) ...[
            Text(_error!,
                style: textTheme.bodySmall?.copyWith(color: t.absent)),
            const SizedBox(height: AppSpacing.x12),
          ],
          AuraButton(
            label: p.canCommit ? 'Import ${p.validRows} students' : 'Choose another file',
            loading: _busy,
            onPressed: p.canCommit ? _commit : _pick,
          ),
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AuraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Bulk import', style: textTheme.titleLarge),
              const SizedBox(height: AppSpacing.x8),
              Text(
                'Upload a CSV or XLSX with columns: Student_ID, Email, Last_Name, '
                'First_Name, Middle_Name, Department, Course, Year_Level, Status.',
                style:
                    textTheme.bodyMedium?.copyWith(color: t.textSecondary),
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.x16),
        if (_error != null) ...[
          Text(_error!, style: textTheme.bodySmall?.copyWith(color: t.absent)),
          const SizedBox(height: AppSpacing.x12),
        ],
        AuraButton(
          label: 'Choose file',
          icon: Icons.upload_file_rounded,
          loading: _busy,
          onPressed: _pick,
        ),
      ],
    );
  }
}

class _StatusView extends StatelessWidget {
  const _StatusView({required this.status});
  final ImportJobStatus status;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final done = status.isDone;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
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
                  value: done ? 1 : (status.percentageCompleted / 100).clamp(0, 1),
                  minHeight: 8,
                  backgroundColor: t.surfaceAlt,
                  color: t.accent,
                ),
              ),
              const SizedBox(height: AppSpacing.x12),
              Row(
                children: [
                  _Pill('${status.successCount} added', t.present),
                  const SizedBox(width: AppSpacing.x8),
                  if (status.failedCount > 0)
                    _Pill('${status.failedCount} failed', t.absent),
                  const Spacer(),
                  Text('${status.processedRows}/${status.totalRows}',
                      style: AppTypography.mono(
                          size: 14, color: t.textSecondary)),
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
                  style:
                      textTheme.bodySmall?.copyWith(color: t.textSecondary)),
            ),
        ],
      ],
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill(this.label, this.color);
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x12, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.14),
        borderRadius: BorderRadius.circular(AppRadii.pill),
      ),
      child: Text(label,
          style: Theme.of(context)
              .textTheme
              .labelMedium
              ?.copyWith(color: color)),
    );
  }
}
