import 'package:intl/intl.dart';

String fmtTime(DateTime? d) => d == null ? '—' : DateFormat('h:mm a').format(d);

String fmtFullDate(DateTime? d) =>
    d == null ? '' : DateFormat('EEE, MMM d, y').format(d);

String fmtDateRange(DateTime? start, DateTime? end) {
  if (start == null) return '';
  if (end == null) return fmtTime(start);
  return '${fmtTime(start)} – ${fmtTime(end)}';
}

/// Today / Tomorrow / Yesterday, else "Mon, Jan 6".
String fmtDayLabel(DateTime d) {
  final now = DateTime.now();
  final today = DateTime(now.year, now.month, now.day);
  final that = DateTime(d.year, d.month, d.day);
  final diff = that.difference(today).inDays;
  if (diff == 0) return 'Today';
  if (diff == 1) return 'Tomorrow';
  if (diff == -1) return 'Yesterday';
  return DateFormat('EEE, MMM d').format(d);
}

String dayNumber(DateTime d) => DateFormat('d').format(d);
String monthShort(DateTime d) => DateFormat('MMM').format(d).toUpperCase();
