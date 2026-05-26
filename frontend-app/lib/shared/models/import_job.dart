import '../utils/json.dart';

class ImportPreviewRow {
  const ImportPreviewRow({required this.row, this.status = '', this.errors = const []});
  final int row;
  final String status; // valid | failed
  final List<String> errors;

  bool get isValid => status == 'valid';

  factory ImportPreviewRow.fromJson(Map<String, dynamic> j) => ImportPreviewRow(
        row: asInt(j['row']) ?? 0,
        status: asStr(j['status']) ?? '',
        errors: j['errors'] is List
            ? (j['errors'] as List).map((e) => e.toString()).toList()
            : const [],
      );
}

class ImportPreview {
  const ImportPreview({
    this.filename = '',
    this.totalRows = 0,
    this.validRows = 0,
    this.invalidRows = 0,
    this.canCommit = false,
    this.previewToken,
    this.rows = const [],
  });
  final String filename;
  final int totalRows;
  final int validRows;
  final int invalidRows;
  final bool canCommit;
  final String? previewToken;
  final List<ImportPreviewRow> rows;

  factory ImportPreview.fromJson(Map<String, dynamic> j) => ImportPreview(
        filename: asStr(j['filename']) ?? '',
        totalRows: asInt(j['total_rows']) ?? 0,
        validRows: asInt(j['valid_rows']) ?? 0,
        invalidRows: asInt(j['invalid_rows']) ?? 0,
        canCommit: asBool(j['can_commit']),
        previewToken: asStr(j['preview_token']),
        rows: asMapList(j['rows']).map(ImportPreviewRow.fromJson).toList(),
      );
}

class ImportError {
  const ImportError(this.row, this.error);
  final int row;
  final String error;
  factory ImportError.fromJson(Map<String, dynamic> j) =>
      ImportError(asInt(j['row']) ?? 0, asStr(j['error']) ?? '');
}

class ImportJobStatus {
  const ImportJobStatus({
    this.jobId = '',
    this.state = 'pending',
    this.totalRows = 0,
    this.processedRows = 0,
    this.successCount = 0,
    this.failedCount = 0,
    this.percentageCompleted = 0,
    this.etaSeconds,
    this.errors = const [],
  });
  final String jobId;
  final String state; // pending | processing | completed | failed
  final int totalRows;
  final int processedRows;
  final int successCount;
  final int failedCount;
  final double percentageCompleted;
  final int? etaSeconds;
  final List<ImportError> errors;

  bool get isDone => state == 'completed' || state == 'failed';
  bool get isFailed => state == 'failed';

  factory ImportJobStatus.fromJson(Map<String, dynamic> j) => ImportJobStatus(
        jobId: asStr(j['job_id']) ?? '',
        state: asStr(j['state']) ?? 'pending',
        totalRows: asInt(j['total_rows']) ?? 0,
        processedRows: asInt(j['processed_rows']) ?? 0,
        successCount: asInt(j['success_count']) ?? 0,
        failedCount: asInt(j['failed_count']) ?? 0,
        percentageCompleted: asDouble(j['percentage_completed']) ?? 0,
        etaSeconds: asInt(j['estimated_time_remaining_seconds']),
        errors: asMapList(j['errors']).map(ImportError.fromJson).toList(),
      );
}
