import 'dart:convert';

import 'package:excel/excel.dart' as xls;
import 'package:flutter/foundation.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:share_plus/share_plus.dart';

/// Everything needed to render an event attendance report. The caller assembles
/// this from the event detail + `/{id}/stats` + `/{id}/attendees` + branding.
class EventReportData {
  const EventReportData({
    required this.schoolName,
    required this.eventName,
    required this.dateLine,
    required this.timeLine,
    required this.scheduleLine,
    required this.summary,
    required this.attendeeHeader,
    required this.attendees,
    this.schoolCode,
    this.collegeName,
    this.logoBytes,
  });

  final String schoolName;
  final String? schoolCode;
  final String? collegeName;
  final Uint8List? logoBytes;
  final String eventName;
  final String dateLine;
  final String timeLine;
  final String scheduleLine;
  final Map<String, int> summary; // status label -> count
  final List<String> attendeeHeader;
  final List<List<String>> attendees;

  String get fileBase {
    final slug = eventName
        .toLowerCase()
        .replaceAll(RegExp(r'[^a-z0-9]+'), '_')
        .replaceAll(RegExp(r'^_+|_+$'), '');
    return slug.isEmpty ? 'event_report' : '${slug}_report';
  }
}

/// Generates and shares an event report as PDF / CSV / XLSX. The heavy byte
/// generation runs in a background isolate (`compute`) so it never freezes the
/// UI; `printing`/`share_plus` then run on the main isolate.
class EventReportService {
  const EventReportService();

  Future<void> exportPdf(EventReportData d) async {
    final bytes = await compute(buildEventPdf, d);
    await Printing.sharePdf(bytes: bytes, filename: '${d.fileBase}.pdf');
  }

  Future<void> exportCsv(EventReportData d) async {
    final bytes = await compute(buildEventCsv, d);
    await _share(bytes, '${d.fileBase}.csv', 'text/csv');
  }

  Future<void> exportXlsx(EventReportData d) async {
    final bytes = await compute(buildEventXlsx, d);
    if (bytes != null) {
      await _share(bytes, '${d.fileBase}.xlsx',
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    }
  }

  Future<void> _share(Uint8List bytes, String name, String mime) async {
    await SharePlus.instance.share(
      ShareParams(
        files: [XFile.fromData(bytes, mimeType: mime, name: name)],
        fileNameOverrides: [name],
      ),
    );
  }
}

// --- Isolate-friendly top-level generators (pure Dart, no Flutter bindings) ---

Uint8List buildEventCsv(EventReportData d) {
  final rows = <List<dynamic>>[
    [d.schoolName, if (d.schoolCode != null) d.schoolCode!],
    if (d.collegeName != null) [d.collegeName!],
    [d.eventName],
    [d.dateLine],
    [d.timeLine],
    [d.scheduleLine],
    <dynamic>[],
    ['Attendance summary'],
    ...d.summary.entries.map((e) => [e.key, e.value]),
    <dynamic>[],
    d.attendeeHeader,
    ...d.attendees,
  ];
  String cell(dynamic v) {
    final s = '$v';
    return (s.contains(',') || s.contains('"') || s.contains('\n'))
        ? '"${s.replaceAll('"', '""')}"'
        : s;
  }

  final csv = rows.map((r) => r.map(cell).join(',')).join('\r\n');
  return Uint8List.fromList(utf8.encode(csv));
}

Uint8List? buildEventXlsx(EventReportData d) {
  final book = xls.Excel.createExcel();
  final sheet = book[book.getDefaultSheet() ?? 'Sheet1'];
  void row(List<String> cells) =>
      sheet.appendRow(cells.map((c) => xls.TextCellValue(c)).toList());

  row([d.schoolName, if (d.schoolCode != null) d.schoolCode!]);
  if (d.collegeName != null) row([d.collegeName!]);
  row([d.eventName]);
  row([d.dateLine]);
  row([d.timeLine]);
  row([d.scheduleLine]);
  row([]);
  row(['Attendance summary']);
  d.summary.forEach((k, v) => row([k, '$v']));
  row([]);
  row(d.attendeeHeader);
  for (final r in d.attendees) {
    row(r);
  }
  final bytes = book.encode();
  return bytes != null ? Uint8List.fromList(bytes) : null;
}

/// The PDF's built-in Helvetica only covers Latin-1, so map common typographic
/// glyphs (en/em dash, smart quotes, ellipsis, bullet) to ASCII and drop
/// anything else outside Latin-1 — otherwise rendering throws on "–"/"—".
String _pdfSafe(String s) {
  const repl = {
    '–': '-',
    '—': '-',
    '‘': "'",
    '’': "'",
    '“': '"',
    '”': '"',
    '…': '...',
    '•': '-',
    ' ': ' ',
  };
  final buf = StringBuffer();
  for (final r in s.runes) {
    final ch = String.fromCharCode(r);
    if (repl.containsKey(ch)) {
      buf.write(repl[ch]);
    } else if (r <= 0xFF) {
      buf.write(ch);
    } else {
      buf.write('?');
    }
  }
  return buf.toString();
}

Future<Uint8List> buildEventPdf(EventReportData d) async {
  final doc = pw.Document();
  final logo = d.logoBytes != null ? pw.MemoryImage(d.logoBytes!) : null;

  // Sanitize everything that goes to Helvetica.
  final schoolName = _pdfSafe(d.schoolName);
  final schoolCode = d.schoolCode != null ? _pdfSafe(d.schoolCode!) : null;
  final collegeName = d.collegeName != null ? _pdfSafe(d.collegeName!) : null;
  final eventName = _pdfSafe(d.eventName);
  final dateLine = _pdfSafe(d.dateLine);
  final timeLine = _pdfSafe(d.timeLine);
  final scheduleLine = _pdfSafe(d.scheduleLine);
  final summary = {
    for (final e in d.summary.entries) _pdfSafe(e.key): e.value
  };
  final attendeeHeader = d.attendeeHeader.map(_pdfSafe).toList();
  final attendees = d.attendees.map((r) => r.map(_pdfSafe).toList()).toList();

  doc.addPage(
    pw.MultiPage(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.all(28),
      build: (context) => [
        pw.Row(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            if (logo != null)
              pw.Container(
                  width: 46,
                  height: 46,
                  margin: const pw.EdgeInsets.only(right: 12),
                  child: pw.Image(logo, fit: pw.BoxFit.contain)),
            pw.Expanded(
              child: pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text(schoolName,
                      style: pw.TextStyle(
                          fontSize: 16, fontWeight: pw.FontWeight.bold)),
                  if (schoolCode != null)
                    pw.Text(schoolCode,
                        style: const pw.TextStyle(
                            fontSize: 10, color: PdfColors.grey700)),
                  if (collegeName != null)
                    pw.Text(collegeName,
                        style: const pw.TextStyle(fontSize: 11)),
                ],
              ),
            ),
            pw.Text('Attendance report',
                style:
                    const pw.TextStyle(fontSize: 10, color: PdfColors.grey700)),
          ],
        ),
        pw.Divider(height: 24),
        pw.Text(eventName,
            style: pw.TextStyle(fontSize: 20, fontWeight: pw.FontWeight.bold)),
        pw.SizedBox(height: 4),
        pw.Text(dateLine),
        pw.Text(timeLine),
        pw.Text(scheduleLine,
            style: const pw.TextStyle(color: PdfColors.grey700)),
        pw.SizedBox(height: 16),
        pw.Text('Attendance summary',
            style: pw.TextStyle(fontWeight: pw.FontWeight.bold)),
        pw.SizedBox(height: 6),
        pw.Wrap(
          spacing: 18,
          runSpacing: 6,
          children: summary.entries
              .map((e) => pw.Text('${e.key}: ${e.value}'))
              .toList(),
        ),
        pw.SizedBox(height: 16),
        pw.Text('Attendees',
            style: pw.TextStyle(fontWeight: pw.FontWeight.bold)),
        pw.SizedBox(height: 6),
        if (attendees.isEmpty)
          pw.Text('No attendee records.',
              style: const pw.TextStyle(color: PdfColors.grey700))
        else
          pw.TableHelper.fromTextArray(
            headers: attendeeHeader,
            data: attendees,
            headerStyle: pw.TextStyle(fontWeight: pw.FontWeight.bold),
            cellStyle: const pw.TextStyle(fontSize: 9),
            headerDecoration: const pw.BoxDecoration(color: PdfColors.grey200),
            cellAlignment: pw.Alignment.centerLeft,
          ),
        pw.SizedBox(height: 18),
        pw.Text('Generated by Aura',
            style: const pw.TextStyle(fontSize: 9, color: PdfColors.grey600)),
      ],
    ),
  );
  return doc.save();
}
