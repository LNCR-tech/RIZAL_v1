import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/services/geolocation_service.dart';
import '../../../core/theme/app_motion.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../../../core/widgets/section_header.dart';
import '../../../shared/models/event.dart';
import '../../../shared/utils/formatting.dart';
import '../../events/application/event_editor_payload.dart';
import '../../events/application/events_providers.dart';
import '../../events/data/events_repository.dart';
import '../../governance/application/governance_providers.dart';
import '../application/schoolit_providers.dart';

/// Create / edit an event with a clean, sectioned form. The layout
/// trades column density for breathing room — every backend knob the
/// editor exposes has plain-English labels, no jargon, and a one-line
/// description so the user understands what the value does.
///
/// Backend fields covered:
///   * name, location (venue), description, start_datetime, end_datetime
///   * year_levels (chips; empty = open to all years)
///   * governance_context query param (the "Officers only" switch — only
///     visible when the editor is launched inside a governance unit)
///   * early_check_in_minutes, late_threshold_minutes,
///     sign_out_grace_minutes — prefilled from the school's defaults
///     (`SchoolBranding`), never hardcoded
///   * geo_required, geo_latitude/longitude, geo_radius_m
///
/// UI motion follows the AppMotion contract (ease-out only, ≤ 300 ms for
/// UI changes), honours reduced motion, and never causes a layout
/// thrash on the parent ListView.
class EventEditorScreen extends ConsumerStatefulWidget {
  const EventEditorScreen({super.key, this.governanceContext, this.event});

  /// When set (SSG|SG|ORG), the event is created in this governance
  /// unit's scope. Drives the visibility of the "Officers only" switch.
  final String? governanceContext;

  /// When set, edit this existing event instead of creating a new one.
  final AppEvent? event;

  @override
  ConsumerState<EventEditorScreen> createState() => _EventEditorScreenState();
}

class _EventEditorScreenState extends ConsumerState<EventEditorScreen> {
  // Text controllers
  final _name = TextEditingController();
  final _location = TextEditingController();
  final _description = TextEditingController();

  // Map
  final _mapController = MapController();

  // Schedule
  DateTime? _startDate;
  TimeOfDay? _startTime;
  DateTime? _endDate;
  TimeOfDay? _endTime;

  // Audience
  bool _officersOnly = false;
  List<int> _yearLevels = const <int>[];

  // Timing windows — initialised from the school's defaults (or the
  // existing event's per-event override on edit).
  int _earlyCheckIn = 15;
  int _lateThreshold = 10;
  int _signOutGrace = 15;

  // Geofence
  bool _geoRequired = false;
  double? _geoLat;
  double? _geoLng;
  double _geoRadius = 100;

  // Form state
  bool _busy = false;
  String? _error;

  bool get _isEdit => widget.event != null;
  bool get _hasGovContext => widget.governanceContext != null;

  @override
  void initState() {
    super.initState();
    final e = widget.event;
    if (e != null) {
      _name.text = e.name;
      _location.text = e.location ?? '';
      _description.text = e.description ?? '';
      final s = e.startDatetime?.toLocal();
      if (s != null) {
        _startDate = DateTime(s.year, s.month, s.day);
        _startTime = TimeOfDay(hour: s.hour, minute: s.minute);
      }
      final en = e.endDatetime?.toLocal();
      if (en != null) {
        _endDate = DateTime(en.year, en.month, en.day);
        _endTime = TimeOfDay(hour: en.hour, minute: en.minute);
      }
      _geoRequired = e.geoRequired;
      if (e.hasGeo) {
        _geoLat = e.geoLatitude;
        _geoLng = e.geoLongitude;
        _geoRadius = (e.geoRadiusM ?? 100).clamp(25, 500).toDouble();
      }
      // Audience: officers-only iff backend stamped the event with a
      // governance_unit_id. Year level chips pre-populate from existing
      // targets.
      _officersOnly = e.isOfficersOnly;
      _yearLevels = List<int>.from(e.yearLevels);
      _earlyCheckIn = e.earlyCheckInMinutes;
      _lateThreshold = e.lateThresholdMinutes;
      _signOutGrace = e.signOutGraceMinutes;
    } else if (_hasGovContext) {
      // Sensible default for a governance officer creating a new event:
      // their unit is the audience. They can flip it off to broaden.
      _officersOnly = true;
    }
  }

  @override
  void dispose() {
    _name.dispose();
    _location.dispose();
    _description.dispose();
    _mapController.dispose();
    super.dispose();
  }

  DateTime? _combine(DateTime? d, TimeOfDay? t) => (d == null || t == null)
      ? null
      : DateTime(d.year, d.month, d.day, t.hour, t.minute);

  Future<void> _onGeoToggle(bool v) async {
    setState(() => _geoRequired = v);
    if (v && _geoLat == null) await _useMyLocation();
  }

  Future<void> _useMyLocation() async {
    final fix = await ref.read(geolocationServiceProvider).current();
    if (fix != null && mounted) {
      setState(() {
        _geoLat = fix.latitude;
        _geoLng = fix.longitude;
      });
      _mapController.move(LatLng(fix.latitude, fix.longitude), 16);
    }
  }

  Future<void> _pickDate({required bool start}) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: (start ? _startDate : _endDate) ?? now,
      firstDate: now.subtract(const Duration(days: 1)),
      lastDate: now.add(const Duration(days: 365)),
    );
    if (picked == null) return;
    setState(() => start ? _startDate = picked : _endDate = picked);
  }

  Future<void> _pickTime({required bool start}) async {
    final picked = await showTimePicker(
      context: context,
      initialTime: (start ? _startTime : _endTime) ?? TimeOfDay.now(),
    );
    if (picked == null) return;
    setState(() => start ? _startTime = picked : _endTime = picked);
  }

  void _toggleYearLevel(int level) {
    setState(() {
      if (_yearLevels.contains(level)) {
        _yearLevels = _yearLevels.where((y) => y != level).toList();
      } else {
        _yearLevels = [..._yearLevels, level]..sort();
      }
    });
  }

  Future<void> _save() async {
    final start = _combine(_startDate, _startTime);
    final end = _combine(_endDate, _endTime);

    // When the event is officers-only, year-level chips are hidden and
    // the audience is fully defined by the governance membership — so
    // send an empty year_levels list (the backend's "no extra filter"
    // sentinel) regardless of any leftover chip state.
    final effectiveYearLevels =
        (_hasGovContext && _officersOnly) ? const <int>[] : _yearLevels;

    late final Map<String, dynamic> body;
    try {
      body = buildEventEditorPayload(
        name: _name.text,
        location: _location.text,
        description: _description.text,
        start: start,
        end: end,
        geoRequired: _geoRequired,
        geoLatitude: _geoLat,
        geoLongitude: _geoLng,
        geoRadiusM: _geoRadius,
        isEdit: _isEdit,
        yearLevels: effectiveYearLevels,
        earlyCheckInMinutes: _earlyCheckIn,
        lateThresholdMinutes: _lateThreshold,
        signOutGraceMinutes: _signOutGrace,
      );
    } on EventEditorPayloadError catch (e) {
      setState(() => _error = e.message);
      return;
    }

    // Governance context is only attached when the user kept the
    // "Officers only" switch on. Flipping it off broadens the event to
    // the school audience scope, and the backend rejects an event that
    // has both governance_context AND empty membership, so dropping the
    // query param is what we want.
    final effectiveContext =
        (_hasGovContext && _officersOnly) ? widget.governanceContext : null;

    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final repo = ref.read(eventsRepositoryProvider);
      if (_isEdit) {
        await repo.update(widget.event!.id, body,
            governanceContext: effectiveContext);
      } else {
        await repo.create(body, governanceContext: effectiveContext);
      }
      if (widget.governanceContext != null) {
        ref.invalidate(governanceEventsProvider(widget.governanceContext!));
      } else {
        ref.invalidate(scheduleEventsProvider);
      }
      if (mounted) {
        final messenger = ScaffoldMessenger.of(context);
        Navigator.of(context).pop(true);
        messenger.showSnackBar(SnackBar(
          content: Text(_isEdit ? 'Event updated.' : 'Event created.'),
        ));
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = _isEdit
            ? 'Could not save changes. Please try again.'
            : 'Could not create the event. Please try again.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// Pull the school's defaults once on the first build. We don't
  /// `ref.watch` schoolProvider in `build` because the form would reset
  /// every time the school payload refreshes; instead we read it once
  /// and seed the local state.
  void _applySchoolDefaultsIfFresh() {
    if (_isEdit) return; // existing values already loaded
    final s = ref.read(schoolProvider).valueOrNull;
    if (s == null) return;
    var changed = false;
    if (_earlyCheckIn == 15 && s.earlyCheckInMinutes > 0) {
      _earlyCheckIn = s.earlyCheckInMinutes;
      changed = true;
    }
    if (_lateThreshold == 10 && s.lateThresholdMinutes > 0) {
      _lateThreshold = s.lateThresholdMinutes;
      changed = true;
    }
    if (_signOutGrace == 15 && s.signOutGraceMinutes > 0) {
      _signOutGrace = s.signOutGraceMinutes;
      changed = true;
    }
    if (changed) {
      // Pump a microtask so we don't setState mid-build.
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) setState(() {});
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    _applySchoolDefaultsIfFresh();
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return AppScaffold(
      title: _isEdit ? 'Edit event' : 'New event',
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
        children: [
          // ── About ─────────────────────────────────────────────
          const SectionHeader(title: 'About'),
          const _SectionHint(
            text: 'What people will see in their schedule.',
          ),
          const SizedBox(height: AppSpacing.x12),
          AuraTextField(label: 'Event name', controller: _name),
          const SizedBox(height: AppSpacing.x12),
          AuraTextField(
            label: 'Venue',
            controller: _location,
            hint: 'e.g. Main gym',
          ),
          const SizedBox(height: AppSpacing.x12),
          AuraTextField(
            label: 'Description',
            controller: _description,
            hint: 'Optional — what is the event about?',
          ),
          const SizedBox(height: AppSpacing.x24),

          // ── When ──────────────────────────────────────────────
          const SectionHeader(title: 'When'),
          const _SectionHint(
            text: 'Start and end times are local to your school.',
          ),
          const SizedBox(height: AppSpacing.x12),
          _PickerTile(
            label: 'Starts',
            value: _startDate == null
                ? 'Pick date & time'
                : '${fmtFullDate(_combine(_startDate, _startTime) ?? _startDate)}'
                    '${_startTime != null ? ' · ${_startTime!.format(context)}' : ''}',
            onDate: () => _pickDate(start: true),
            onTime: () => _pickTime(start: true),
          ),
          const SizedBox(height: AppSpacing.x12),
          _PickerTile(
            label: 'Ends',
            value: _endDate == null
                ? 'Pick date & time'
                : '${fmtFullDate(_combine(_endDate, _endTime) ?? _endDate)}'
                    '${_endTime != null ? ' · ${_endTime!.format(context)}' : ''}',
            onDate: () => _pickDate(start: false),
            onTime: () => _pickTime(start: false),
          ),
          const SizedBox(height: AppSpacing.x24),

          // ── Who can attend ────────────────────────────────────
          const SectionHeader(title: 'Who can attend'),
          if (_hasGovContext) ...[
            const _SectionHint(
              text:
                  'Limit this event to your officers, or open it up to '
                  'students you choose.',
            ),
            const SizedBox(height: AppSpacing.x12),
            _OfficersOnlyCard(
              officersOnly: _officersOnly,
              onChanged: (v) => setState(() => _officersOnly = v),
            ),
            const SizedBox(height: AppSpacing.x12),
          ] else ...[
            const _SectionHint(
              text:
                  'Pick the year levels invited. Leave empty to invite '
                  'every year.',
            ),
            const SizedBox(height: AppSpacing.x12),
          ],
          // Year-level chips slide in when officers-only is OFF (or
          // always shown outside governance context).
          AnimatedSize(
            duration: const Duration(milliseconds: 240),
            curve: AppMotion.easeOut,
            alignment: Alignment.topCenter,
            child: (!_hasGovContext || !_officersOnly)
                ? _YearLevelCard(
                    selected: _yearLevels,
                    onToggle: _toggleYearLevel,
                  )
                : const SizedBox.shrink(),
          ),
          const SizedBox(height: AppSpacing.x24),

          // ── Timing ────────────────────────────────────────────
          const SectionHeader(title: 'Timing'),
          const _SectionHint(
            text:
                'When check-in opens, when late starts, and how long '
                'sign-out stays open.',
          ),
          const SizedBox(height: AppSpacing.x12),
          AuraCard(
            child: Column(
              children: [
                _MinuteStepper(
                  title: 'Check-in opens',
                  subtitle:
                      _earlyCheckIn == 0
                          ? 'Exactly at start time'
                          : '$_earlyCheckIn minutes before start',
                  value: _earlyCheckIn,
                  min: 0,
                  max: 120,
                  step: 5,
                  onChanged: (v) => setState(() => _earlyCheckIn = v),
                ),
                Divider(height: 1, color: t.border),
                _MinuteStepper(
                  title: 'Marked late after start',
                  subtitle: _lateThreshold == 0
                      ? 'Late immediately'
                      : 'Late after $_lateThreshold minutes',
                  value: _lateThreshold,
                  min: 0,
                  max: 120,
                  step: 5,
                  onChanged: (v) => setState(() => _lateThreshold = v),
                ),
                Divider(height: 1, color: t.border),
                _MinuteStepper(
                  title: 'Sign-out window after end',
                  subtitle: _signOutGrace == 0
                      ? 'Closes at end time'
                      : 'Closes $_signOutGrace minutes after end',
                  value: _signOutGrace,
                  min: 0,
                  max: 120,
                  step: 5,
                  onChanged: (v) => setState(() => _signOutGrace = v),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.x24),

          // ── Where ─────────────────────────────────────────────
          const SectionHeader(title: 'Where'),
          const _SectionHint(
            text:
                'Optional. When on, students have to be inside the '
                'circle to check in.',
          ),
          const SizedBox(height: AppSpacing.x12),
          AuraCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Require location',
                              style: textTheme.titleLarge),
                          Text(
                            'Block check-ins outside the circle',
                            style: textTheme.bodySmall
                                ?.copyWith(color: t.textSecondary),
                          ),
                        ],
                      ),
                    ),
                    Switch(value: _geoRequired, onChanged: _onGeoToggle),
                  ],
                ),
                AnimatedSize(
                  duration: const Duration(milliseconds: 240),
                  curve: AppMotion.easeOut,
                  alignment: Alignment.topCenter,
                  child: _geoRequired
                      ? Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: AppSpacing.x12),
                            Text('Tap the map to set the centre.',
                                style: textTheme.bodySmall
                                    ?.copyWith(color: t.textMuted)),
                            const SizedBox(height: AppSpacing.x8),
                            ClipRRect(
                              borderRadius:
                                  BorderRadius.circular(AppRadii.control),
                              child: SizedBox(
                                height: 220,
                                child: FlutterMap(
                                  mapController: _mapController,
                                  options: MapOptions(
                                    initialCenter: LatLng(
                                        _geoLat ?? 14.5995,
                                        _geoLng ?? 120.9842),
                                    initialZoom: 16,
                                    onTap: (_, p) => setState(() {
                                      _geoLat = p.latitude;
                                      _geoLng = p.longitude;
                                    }),
                                  ),
                                  children: [
                                    TileLayer(
                                      urlTemplate:
                                          'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                                      userAgentPackageName:
                                          'com.aura.aura_app',
                                    ),
                                    if (_geoLat != null && _geoLng != null) ...[
                                      CircleLayer(
                                        circles: [
                                          CircleMarker(
                                            point: LatLng(_geoLat!, _geoLng!),
                                            radius: _geoRadius,
                                            useRadiusInMeter: true,
                                            color: t.accent.withOpacity(0.18),
                                            borderColor: t.accentDark,
                                            borderStrokeWidth: 2,
                                          ),
                                        ],
                                      ),
                                      MarkerLayer(
                                        markers: [
                                          Marker(
                                            point: LatLng(_geoLat!, _geoLng!),
                                            width: 40,
                                            height: 40,
                                            child: Icon(Icons.location_on,
                                                color: t.accentDark, size: 36),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                            ),
                            const SizedBox(height: AppSpacing.x12),
                            Row(
                              children: [
                                Text('Radius', style: textTheme.bodyMedium),
                                Expanded(
                                  child: Slider(
                                    value: _geoRadius,
                                    min: 25,
                                    max: 500,
                                    divisions: 19,
                                    label: '${_geoRadius.round()} m',
                                    onChanged: (v) =>
                                        setState(() => _geoRadius = v),
                                  ),
                                ),
                                Text('${_geoRadius.round()} m',
                                    style: AppTypography.mono(
                                      size: 14,
                                      weight: FontWeight.w600,
                                      color: t.ink,
                                    )),
                              ],
                            ),
                            Align(
                              alignment: Alignment.centerLeft,
                              child: TextButton.icon(
                                onPressed: _useMyLocation,
                                icon: const Icon(Icons.my_location_rounded,
                                    size: 18),
                                label: const Text('Use my location'),
                              ),
                            ),
                          ],
                        )
                      : const SizedBox.shrink(),
                ),
              ],
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.x16),
            _ErrorText(message: _error!),
          ],
          const SizedBox(height: AppSpacing.x24),
          AuraButton(
            label: _isEdit ? 'Save changes' : 'Create event',
            loading: _busy,
            onPressed: _save,
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────
// Sub-widgets
// ─────────────────────────────────────────────────────────────────────

/// One-line caption that sits below a section header. Plain English,
/// muted colour — explains the section without crowding it.
class _SectionHint extends StatelessWidget {
  const _SectionHint({required this.text});
  final String text;
  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(left: AppSpacing.x4, top: 2),
      child: Text(
        text,
        style: textTheme.bodySmall?.copyWith(color: t.textMuted, height: 1.4),
      ),
    );
  }
}

class _PickerTile extends StatelessWidget {
  const _PickerTile({
    required this.label,
    required this.value,
    required this.onDate,
    required this.onTime,
  });
  final String label;
  final String value;
  final VoidCallback onDate;
  final VoidCallback onTime;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final subject = label == 'Starts' ? 'start' : 'end';
    return AuraCard(
      padding: const EdgeInsets.all(AppSpacing.x16),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: textTheme.bodySmall?.copyWith(color: t.textMuted)),
                const SizedBox(height: 2),
                Text(value, style: textTheme.bodyLarge),
              ],
            ),
          ),
          IconButton(
            tooltip: 'Pick $subject date',
            icon: const Icon(Icons.event_rounded),
            onPressed: onDate,
          ),
          IconButton(
            tooltip: 'Pick $subject time',
            icon: const Icon(Icons.schedule_rounded),
            onPressed: onTime,
          ),
        ],
      ),
    );
  }
}

/// "Officers only" switch. Subtitle dynamically describes what the
/// switch does in the current state — no jargon, no governance unit IDs.
class _OfficersOnlyCard extends StatelessWidget {
  const _OfficersOnlyCard({
    required this.officersOnly,
    required this.onChanged,
  });

  final bool officersOnly;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AuraCard(
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Officers only', style: textTheme.titleLarge),
                const SizedBox(height: 2),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 180),
                  switchInCurve: AppMotion.easeOut,
                  switchOutCurve: AppMotion.easeOut,
                  child: Text(
                    officersOnly
                        ? 'Only your officers can see and join this event.'
                        : 'Open to students you pick by year below.',
                    key: ValueKey<bool>(officersOnly),
                    style: textTheme.bodySmall
                        ?.copyWith(color: t.textSecondary, height: 1.4),
                  ),
                ),
              ],
            ),
          ),
          Switch(value: officersOnly, onChanged: onChanged),
        ],
      ),
    );
  }
}

/// Year-level chip selector. "Empty = all years" is shown as a small
/// hint above the chips so the empty state isn't a mystery.
class _YearLevelCard extends StatelessWidget {
  const _YearLevelCard({
    required this.selected,
    required this.onToggle,
  });

  final List<int> selected;
  final ValueChanged<int> onToggle;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Year levels', style: textTheme.titleLarge),
          const SizedBox(height: 2),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 180),
            switchInCurve: AppMotion.easeOut,
            switchOutCurve: AppMotion.easeOut,
            child: Text(
              selected.isEmpty
                  ? 'Tap a year to invite just that level. Leave empty for everyone.'
                  : 'Inviting Year ${selected.join(", ")}.',
              key: ValueKey<String>(
                  selected.isEmpty ? 'empty' : selected.join(',')),
              style: textTheme.bodySmall
                  ?.copyWith(color: t.textSecondary, height: 1.4),
            ),
          ),
          const SizedBox(height: AppSpacing.x12),
          Wrap(
            spacing: AppSpacing.x8,
            runSpacing: AppSpacing.x8,
            children: List.generate(5, (i) {
              final level = i + 1;
              final active = selected.contains(level);
              return FilterChip(
                label: Text('Year $level'),
                selected: active,
                onSelected: (_) => onToggle(level),
                selectedColor: t.accent.withOpacity(0.18),
                checkmarkColor: t.accentDark,
                labelStyle: textTheme.labelLarge?.copyWith(
                  color: active ? t.ink : t.textSecondary,
                  fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                ),
                side: BorderSide(
                  color: active ? t.accentDark : t.border,
                  width: active ? 1.2 : 1.0,
                ),
                backgroundColor: t.surface,
                showCheckmark: true,
                visualDensity: VisualDensity.compact,
              );
            }),
          ),
        ],
      ),
    );
  }
}

/// Row with a label + subtitle on the left and a minus/value/plus
/// stepper on the right. Used for the three minute-window settings —
/// concrete numbers feel more confident than a slider for "5 minutes",
/// and each tap is a well-defined step. The value text cross-fades on
/// change (no jumpy resize).
class _MinuteStepper extends StatelessWidget {
  const _MinuteStepper({
    required this.title,
    required this.subtitle,
    required this.value,
    required this.min,
    required this.max,
    required this.step,
    required this.onChanged,
  });

  final String title;
  final String subtitle;
  final int value;
  final int min;
  final int max;
  final int step;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final canDec = value > min;
    final canInc = value < max;
    return Padding(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x16, vertical: AppSpacing.x12),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(title, style: textTheme.titleMedium),
                const SizedBox(height: 2),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 180),
                  switchInCurve: AppMotion.easeOut,
                  switchOutCurve: AppMotion.easeOut,
                  child: Text(
                    subtitle,
                    key: ValueKey<String>(subtitle),
                    style: textTheme.bodySmall
                        ?.copyWith(color: t.textSecondary, height: 1.4),
                  ),
                ),
              ],
            ),
          ),
          _StepperButton(
            icon: Icons.remove_rounded,
            enabled: canDec,
            tooltip: 'Decrease',
            onPressed: () =>
                onChanged((value - step).clamp(min, max).toInt()),
          ),
          SizedBox(
            width: 56,
            child: Center(
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 180),
                switchInCurve: AppMotion.easeOut,
                switchOutCurve: AppMotion.easeOut,
                child: Text(
                  '$value',
                  key: ValueKey<int>(value),
                  style: AppTypography.mono(
                    size: 18,
                    weight: FontWeight.w700,
                    color: t.ink,
                  ),
                ),
              ),
            ),
          ),
          _StepperButton(
            icon: Icons.add_rounded,
            enabled: canInc,
            tooltip: 'Increase',
            onPressed: () =>
                onChanged((value + step).clamp(min, max).toInt()),
          ),
        ],
      ),
    );
  }
}

class _StepperButton extends StatelessWidget {
  const _StepperButton({
    required this.icon,
    required this.enabled,
    required this.tooltip,
    required this.onPressed,
  });
  final IconData icon;
  final bool enabled;
  final String tooltip;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return SizedBox(
      width: 44,
      height: 44,
      child: IconButton(
        tooltip: tooltip,
        icon: Icon(icon, size: 20),
        color: enabled ? t.ink : t.textMuted,
        onPressed: enabled ? onPressed : null,
        splashRadius: 22,
      ),
    );
  }
}

class _ErrorText extends StatelessWidget {
  const _ErrorText({required this.message});
  final String message;
  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.all(AppSpacing.x12),
      decoration: BoxDecoration(
        color: t.absent.withOpacity(0.12),
        borderRadius: AppRadii.rControl,
        border: Border.all(color: t.absent.withOpacity(0.35)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.error_outline_rounded, size: 18, color: t.absent),
          const SizedBox(width: AppSpacing.x8),
          Expanded(
            child: Text(
              message,
              style: textTheme.bodyMedium?.copyWith(color: t.absent),
            ),
          ),
        ],
      ),
    );
  }
}
