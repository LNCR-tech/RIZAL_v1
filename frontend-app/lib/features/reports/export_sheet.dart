import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/auth/session_controller.dart';
import '../../core/network/dio_client.dart';
import '../../core/network/media_url.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_tokens.dart';
import '../../shared/models/event.dart';
import '../../shared/models/governance.dart';
import '../../shared/utils/formatting.dart';
import '../governance/application/governance_providers.dart';
import '../governance/data/governance_repository.dart';
import 'event_report_service.dart';

String _titleCase(String s) =>
    s.isEmpty ? '-' : s[0].toUpperCase() + s.substring(1);

/// Bottom sheet to export an event attendance report as PDF / Excel / CSV, with
/// a real step-based progress bar (fetch -> match names -> branding -> build).
class ExportSheet extends ConsumerStatefulWidget {
  const ExportSheet({super.key, required this.event, this.collegeName});
  final AppEvent event;
  final String? collegeName;

  @override
  ConsumerState<ExportSheet> createState() => _ExportSheetState();
}

class _ExportSheetState extends ConsumerState<ExportSheet> {
  bool _busy = false;
  String? _error;
  double _progress = 0;
  String _stage = '';

  // Per-session caches so repeat exports skip the slow fetches (the logo + the
  // full student roster were re-fetched on every export).
  static final Map<String, Uint8List?> _logoCache = {};
  static Map<int, GovUserSummary>? _namesCache;

  void _set(double p, String stage) {
    if (!mounted) return;
    setState(() {
      _progress = p;
      _stage = stage;
    });
  }

  Future<Map<int, GovUserSummary>> _names() async {
    final cached = _namesCache;
    if (cached != null) return cached;
    final map = <int, GovUserSummary>{};
    try {
      final students =
          await ref.read(governanceRepositoryProvider).accessibleStudents();
      for (final s in students) {
        map[s.id] = s;
      }
      _namesCache = map; // roster is stable for the session
    } catch (_) {/* names are best-effort; fall back to IDs */}
    return map;
  }

  Future<Uint8List?> _logo(String? rawUrl) async {
    final url = mediaUrl(rawUrl);
    if (url == null) return null;
    if (_logoCache.containsKey(url)) return _logoCache[url];
    try {
      final res = await ref
          .read(dioClientProvider)
          .dio
          .get<List<int>>(url,
              options: Options(responseType: ResponseType.bytes))
          .timeout(const Duration(seconds: 3));
      final data = res.data;
      final bytes = data != null ? Uint8List.fromList(data) : null;
      _logoCache[url] = bytes; // reuse for the rest of the session
      return bytes;
    } catch (_) {
      return null; // don't cache a failure — allow a retry next export
    }
  }

  EventReportData _build(
    AppEvent e,
    Map<int, GovUserSummary> byId,
    EventStats stats,
    List attendees,
    Uint8List? logo,
  ) {
    final meta = ref.read(sessionControllerProvider).meta;
    final time = DateFormat('h:mm a');
    final start = e.startDatetime;
    final end = e.endDatetime;
    final timeLine = start == null
        ? 'Time: -'
        : 'Time: ${time.format(start)}'
            '${end != null ? ' - ${time.format(end)}' : ''}';

    return EventReportData(
      schoolName: meta?.schoolName ?? 'School',
      schoolCode: meta?.schoolCode,
      collegeName: widget.collegeName,
      logoBytes: logo,
      eventName: e.name,
      dateLine: 'Date: ${fmtFullDate(e.startDatetime)}',
      timeLine: timeLine,
      scheduleLine:
          'Schedule - check-in opens ${e.earlyCheckInMinutes}m before, '
          'late after ${e.lateThresholdMinutes}m, sign-out grace '
          '${e.signOutGraceMinutes}m',
      summary: {
        for (final s in stats.statuses.entries) _titleCase(s.key): s.value.count
      },
      attendeeHeader: const ['Name', 'Student ID', 'Time in', 'Time out',
        'Status'],
      attendees: [
        for (final a in attendees)
          [
            byId[a.studentId]?.displayName ?? 'Student #${a.studentId ?? '-'}',
            byId[a.studentId]?.studentNumber ??
                (a.studentId?.toString() ?? '-'),
            a.timeIn != null ? time.format(a.timeIn!) : '-',
            a.timeOut != null ? time.format(a.timeOut!) : '-',
            _titleCase(a.effectiveStatus),
          ],
      ],
    );
  }

  Future<void> _run(String format) async {
    setState(() {
      _busy = true;
      _error = null;
      _progress = 0; // indeterminate while we fetch everything in parallel
      _stage = 'Loading data...';
    });
    try {
      final e = widget.event;
      final meta = ref.read(sessionControllerProvider).meta;
      // Fetch stats, attendees, the student roster and the logo concurrently —
      // the logo is cached + no longer a blocking step at the end (the 60% stall).
      final results = await Future.wait<dynamic>([
        ref.read(eventStatsProvider(e.id).future),
        ref.read(eventAttendeesProvider(e.id).future),
        _names(),
        _logo(meta?.logoUrl),
      ]);
      final data = _build(
        e,
        results[2] as Map<int, GovUserSummary>,
        results[0] as EventStats,
        results[1] as List,
        results[3] as Uint8List?,
      );
      _set(0.7, 'Building $format...');
      const svc = EventReportService();
      switch (format) {
        case 'PDF':
          await svc.exportPdf(data);
        case 'Excel':
          await svc.exportXlsx(data);
        default:
          await svc.exportCsv(data);
      }
      _set(1.0, 'Opening share sheet...');
      if (mounted) Navigator.of(context).pop();
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Could not export the report. Please try again.';
          _busy = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.x20),
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius:
              const BorderRadius.vertical(top: Radius.circular(AppRadii.sheet)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                    color: t.border, borderRadius: BorderRadius.circular(2)),
              ),
            ),
            const SizedBox(height: AppSpacing.x16),
            Text('Export report', style: textTheme.headlineSmall),
            Text(widget.event.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: textTheme.bodyMedium?.copyWith(color: t.textSecondary)),
            const SizedBox(height: AppSpacing.x16),
            if (_busy)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: AppSpacing.x16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(_stage, style: textTheme.bodyMedium),
                        Text('${(_progress * 100).round()}%',
                            style: textTheme.bodyMedium
                                ?.copyWith(color: t.textSecondary)),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.x8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: LinearProgressIndicator(
                        value: _progress == 0 ? null : _progress,
                        minHeight: 8,
                        backgroundColor: t.surfaceAlt,
                        color: t.accent,
                      ),
                    ),
                  ],
                ),
              )
            else ...[
              _row(Icons.picture_as_pdf_rounded, 'PDF',
                  'Formatted report with logo', t.absent, () => _run('PDF')),
              _row(Icons.grid_on_rounded, 'Excel (XLSX)', 'Spreadsheet',
                  t.present, () => _run('Excel')),
              _row(Icons.description_rounded, 'CSV', 'Raw data', t.accentDark,
                  () => _run('CSV')),
            ],
            if (_error != null) ...[
              const SizedBox(height: AppSpacing.x12),
              Text(_error!,
                  style: textTheme.bodySmall?.copyWith(color: t.absent)),
            ],
            const SizedBox(height: AppSpacing.x8),
          ],
        ),
      ),
    );
  }

  Widget _row(IconData icon, String title, String sub, Color color,
      VoidCallback onTap) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadii.control),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.x8),
        child: Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                  color: color.withOpacity(0.16),
                  borderRadius: BorderRadius.circular(AppRadii.control)),
              child: Icon(icon, color: color),
            ),
            const SizedBox(width: AppSpacing.x16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: textTheme.titleLarge),
                  Text(sub,
                      style: textTheme.bodySmall
                          ?.copyWith(color: t.textSecondary)),
                ],
              ),
            ),
            Icon(Icons.chevron_right_rounded, color: t.textMuted),
          ],
        ),
      ),
    );
  }
}
