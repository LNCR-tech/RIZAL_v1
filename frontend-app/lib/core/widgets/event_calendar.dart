import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:table_calendar/table_calendar.dart';

import '../../shared/models/event.dart';
import '../../shared/utils/formatting.dart';
import '../theme/app_spacing.dart';
import '../theme/app_tokens.dart';
import 'aura_card.dart';
import 'states.dart';

enum _CalFilter { all, today, upcoming, past }

Color _statusColor(AppTokens t, String status) =>
    switch (status.toLowerCase()) {
      'ongoing' => t.accent,
      'completed' => t.present,
      'cancelled' => t.absent,
      _ => t.accentDark,
    };

/// Reusable events calendar: filter pills (All / Today / Upcoming / Past), a
/// month view with status-colored day markers + selected-day list, and search.
class EventCalendar extends StatefulWidget {
  const EventCalendar({super.key, required this.events, required this.onTap});
  final List<AppEvent> events;
  final void Function(AppEvent event) onTap;

  @override
  State<EventCalendar> createState() => _EventCalendarState();
}

class _EventCalendarState extends State<EventCalendar> {
  final _query = TextEditingController();
  DateTime _focused = DateTime.now();
  DateTime _selected = DateTime.now();
  _CalFilter _filter = _CalFilter.all;

  static const _pad =
      EdgeInsets.fromLTRB(AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 120);

  @override
  void dispose() {
    _query.dispose();
    super.dispose();
  }

  List<AppEvent> _forDay(DateTime day) => widget.events
      .where((e) => e.startDatetime != null && isSameDay(e.startDatetime!, day))
      .toList();

  String _label(_CalFilter f) => switch (f) {
        _CalFilter.all => 'All',
        _CalFilter.today => 'Today',
        _CalFilter.upcoming => 'Upcoming',
        _CalFilter.past => 'Past',
      };

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final q = _query.text.trim().toLowerCase();
    final now = DateTime.now();

    final filters = Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
      child: Wrap(
        spacing: AppSpacing.x8,
        children: [
          for (final f in _CalFilter.values)
            ChoiceChip(
              label: Text(_label(f)),
              selected: _filter == f,
              onSelected: (_) => setState(() => _filter = f),
            ),
        ],
      ),
    );

    final search = Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.x16),
      child: TextField(
        controller: _query,
        onChanged: (_) => setState(() {}),
        decoration: const InputDecoration(
          hintText: 'Search events',
          prefixIcon: Icon(Icons.search_rounded, size: 20),
        ),
      ),
    );

    final base = switch (_filter) {
      _CalFilter.all => widget.events,
      _CalFilter.today => widget.events
          .where((e) =>
              e.startDatetime != null && isSameDay(e.startDatetime!, now))
          .toList(),
      _CalFilter.upcoming => widget.events
          .where((e) =>
              e.isUpcoming || (e.startDatetime?.isAfter(now) ?? false))
          .toList(),
      _CalFilter.past => widget.events
          .where((e) =>
              e.isCompleted ||
              ((e.endDatetime ?? e.startDatetime)?.isBefore(now) ?? false))
          .toList(),
    };

    // Flat list when filtering or searching; calendar otherwise.
    if (_filter != _CalFilter.all || q.isNotEmpty) {
      final list = base
          .where((e) => q.isEmpty || e.name.toLowerCase().contains(q))
          .toList()
        ..sort((a, b) => (b.startDatetime ?? DateTime(0))
            .compareTo(a.startDatetime ?? DateTime(0)));
      return ListView(
        padding: _pad,
        children: [
          filters,
          search,
          if (list.isEmpty)
            const Padding(
              padding: EdgeInsets.only(top: 40),
              child: EmptyState(
                icon: Icons.event_busy_rounded,
                title: 'No events',
                message: 'Nothing matches this filter.',
              ),
            )
          else
            for (final e in list) _tile(t, textTheme, e),
        ],
      );
    }

    final dayEvents = _forDay(_selected);
    return ListView(
      padding: _pad,
      children: [
        filters,
        search,
        AuraCard(
          padding: const EdgeInsets.all(AppSpacing.x8),
          child: TableCalendar<AppEvent>(
            firstDay: DateTime(now.year - 1),
            lastDay: DateTime(now.year + 1, 12, 31),
            focusedDay: _focused,
            selectedDayPredicate: (d) => isSameDay(d, _selected),
            calendarFormat: CalendarFormat.month,
            availableGestures: AvailableGestures.horizontalSwipe,
            eventLoader: _forDay,
            onDaySelected: (sel, foc) =>
                setState(() { _selected = sel; _focused = foc; }),
            headerStyle: const HeaderStyle(
                formatButtonVisible: false, titleCentered: true),
            calendarStyle: CalendarStyle(
              todayDecoration: BoxDecoration(
                  color: t.accent.withOpacity(0.30), shape: BoxShape.circle),
              selectedDecoration:
                  BoxDecoration(color: t.accent, shape: BoxShape.circle),
              selectedTextStyle:
                  TextStyle(color: t.onAccent, fontWeight: FontWeight.w700),
              markersMaxCount: 3,
            ),
            calendarBuilders: CalendarBuilders<AppEvent>(
              markerBuilder: (context, day, events) {
                if (events.isEmpty) return null;
                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    for (final e in events.take(3))
                      Container(
                        width: 6,
                        height: 6,
                        margin: const EdgeInsets.symmetric(horizontal: 1),
                        decoration: BoxDecoration(
                            color: _statusColor(t, e.status),
                            shape: BoxShape.circle),
                      ),
                  ],
                );
              },
            ),
          ),
        ),
        const SizedBox(height: AppSpacing.x16),
        Text(fmtFullDate(_selected), style: textTheme.titleLarge),
        const SizedBox(height: AppSpacing.x8),
        if (dayEvents.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: AppSpacing.x16),
            child: Text('No events on this day.',
                style: textTheme.bodyMedium?.copyWith(color: t.textMuted)),
          )
        else
          for (final e in dayEvents) _tile(t, textTheme, e),
      ],
    );
  }

  Widget _tile(AppTokens t, TextTheme tt, AppEvent e) {
    final color = _statusColor(t, e.status);
    final time = e.startDatetime != null
        ? DateFormat('h:mm a').format(e.startDatetime!)
        : '';
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.x12),
      child: AuraCard(
        onTap: () => widget.onTap(e),
        child: Row(
          children: [
            Container(
              width: 4,
              height: 40,
              decoration: BoxDecoration(
                  color: color, borderRadius: BorderRadius.circular(2)),
            ),
            const SizedBox(width: AppSpacing.x12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(e.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: tt.titleLarge),
                  Text([if (time.isNotEmpty) time, e.status].join(' · '),
                      style: tt.bodySmall?.copyWith(color: t.textSecondary)),
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
