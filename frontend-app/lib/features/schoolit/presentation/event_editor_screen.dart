import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/services/geolocation_service.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
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

/// Create a new event with a clean, sectioned form and an interactive map +
/// radius picker for the geofence.
class EventEditorScreen extends ConsumerStatefulWidget {
  const EventEditorScreen({super.key, this.governanceContext, this.event});

  /// When set (SSG|SG|ORG), the event is created in this governance unit's scope.
  final String? governanceContext;

  /// When set, edit this existing event instead of creating a new one.
  final AppEvent? event;

  @override
  ConsumerState<EventEditorScreen> createState() => _EventEditorScreenState();
}

class _EventEditorScreenState extends ConsumerState<EventEditorScreen> {
  final _name = TextEditingController();
  final _location = TextEditingController();
  final _description = TextEditingController();
  final _mapController = MapController();
  DateTime? _startDate;
  TimeOfDay? _startTime;
  DateTime? _endDate;
  TimeOfDay? _endTime;
  bool _geoRequired = false;
  double? _geoLat;
  double? _geoLng;
  double _geoRadius = 100;
  bool _busy = false;
  String? _error;

  bool get _isEdit => widget.event != null;

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

  Future<void> _save() async {
    final start = _combine(_startDate, _startTime);
    final end = _combine(_endDate, _endTime);

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
      );
    } on EventEditorPayloadError catch (e) {
      setState(() => _error = e.message);
      return;
    }

    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final repo = ref.read(eventsRepositoryProvider);
      if (_isEdit) {
        await repo.update(widget.event!.id, body,
            governanceContext: widget.governanceContext);
      } else {
        await repo.create(body, governanceContext: widget.governanceContext);
      }
      if (widget.governanceContext != null) {
        ref.invalidate(governanceEventsProvider(widget.governanceContext!));
      } else {
        ref.invalidate(scheduleEventsProvider);
      }
      if (mounted) {
        Navigator.of(context).pop(true);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(_isEdit ? 'Event updated.' : 'Event created.')));
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

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return AppScaffold(
      title: _isEdit ? 'Edit event' : 'New event',
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 40),
        children: [
          const SectionHeader(title: 'Details'),
          AuraTextField(label: 'Event name', controller: _name),
          const SizedBox(height: AppSpacing.x12),
          AuraTextField(
              label: 'Venue', controller: _location, hint: 'e.g. Main gym'),
          const SizedBox(height: AppSpacing.x12),
          AuraTextField(
              label: 'Description', controller: _description, hint: 'Optional'),
          const SizedBox(height: AppSpacing.x24),
          const SectionHeader(title: 'Schedule'),
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
          const SectionHeader(title: 'Location & geofence'),
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
                          Text('Require location', style: textTheme.titleLarge),
                          Text('Students must be inside the radius to check in',
                              style: textTheme.bodySmall
                                  ?.copyWith(color: t.textSecondary)),
                        ],
                      ),
                    ),
                    Switch(value: _geoRequired, onChanged: _onGeoToggle),
                  ],
                ),
                if (_geoRequired) ...[
                  const SizedBox(height: AppSpacing.x12),
                  Text('Tap the map to set the centre.',
                      style: textTheme.bodySmall
                          ?.copyWith(color: t.textMuted)),
                  const SizedBox(height: AppSpacing.x8),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(AppRadii.control),
                    child: SizedBox(
                      height: 220,
                      child: FlutterMap(
                        mapController: _mapController,
                        options: MapOptions(
                          initialCenter:
                              LatLng(_geoLat ?? 14.5995, _geoLng ?? 120.9842),
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
                            userAgentPackageName: 'com.aura.aura_app',
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
                          onChanged: (v) => setState(() => _geoRadius = v),
                        ),
                      ),
                      Text('${_geoRadius.round()} m',
                          style: textTheme.bodyMedium),
                    ],
                  ),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: TextButton.icon(
                      onPressed: _useMyLocation,
                      icon: const Icon(Icons.my_location_rounded, size: 18),
                      label: const Text('Use my location'),
                    ),
                  ),
                ],
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
              label: _isEdit ? 'Save changes' : 'Create event',
              loading: _busy,
              onPressed: _save),
        ],
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
          IconButton(icon: const Icon(Icons.event_rounded), onPressed: onDate),
          IconButton(
              icon: const Icon(Icons.schedule_rounded), onPressed: onTime),
        ],
      ),
    );
  }
}
