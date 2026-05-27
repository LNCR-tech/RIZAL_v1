# Frontend Implementation Guide — "Officers Only" Event Toggle

## Overview

When a governance officer (SSG, SG, or ORG) creates an event, they can restrict it
to active members of their governance unit using an **"Officers only"** toggle. When
enabled, only members of that governance unit will see and be able to attend the event.
When disabled, the event follows normal year-level targeting (open to all students in
scope).

The backend already fully supports this. This guide describes the exact frontend
changes needed in the Flutter app.

---

## How the Backend Works

### With Officers Only ON
The event is created with the `governance_context` query parameter:

```
POST /api/events/?governance_context=SSG
```

The backend:
- Sets `governance_unit_id` on the event (FK to the governance unit)
- At attendance check-in, verifies the student is an active `GovernanceMember` of
  that unit — `NOT_A_GOVERNANCE_MEMBER` error if not
- At event list (`GET /api/events/`), hides the event from students who are not
  members of that unit

### With Officers Only OFF
The event is created **without** the `governance_context` query parameter:

```
POST /api/events/
```

The backend:
- `governance_unit_id` is null — no membership restriction
- `year_levels` in the request body controls which year levels can attend
- Empty `year_levels` array (`[]`) means all year levels

---

## Files to Change

### 1. `lib/shared/models/event.dart`

Add `governanceUnitId` field so edit mode can pre-populate the toggle:

```dart
// In constructor named params:
this.governanceUnitId,

// As a field:
final int? governanceUnitId;

// In fromJson factory:
governanceUnitId: asInt(j['governance_unit_id']),
```

---

### 2. `lib/features/events/application/event_editor_payload.dart`

Add `yearLevels` parameter so the create/update body sends year level targeting:

```dart
Map<String, dynamic> buildEventEditorPayload({
  // ... existing params ...
  List<int> yearLevels = const [],   // <-- ADD THIS
}) {
  // ...
  final body = <String, dynamic>{
    'name': cleanName,
    'location': cleanLocation,
    if (cleanDescription.isNotEmpty) 'description': cleanDescription,
    'start_datetime': start.toUtc().toIso8601String(),
    'end_datetime': end.toUtc().toIso8601String(),
    'year_levels': yearLevels,       // <-- ADD THIS
  };
  // ...
}
```

---

### 3. `lib/features/schoolit/presentation/event_editor_screen.dart`

#### State additions

```dart
bool _officersOnly = false;
List<int> _yearLevels = const [];
```

#### `initState` — initialise from widget/existing event

```dart
if (e != null) {
  // ... existing field population ...
  _officersOnly = e.governanceUnitId != null;
} else {
  _officersOnly = widget.governanceContext != null;  // default ON when in governance context
}
```

#### `_save()` — conditionally pass governance_context and year_levels

```dart
final effectiveContext =
    (_hasGovContext && _officersOnly) ? widget.governanceContext : null;
final effectiveYearLevels = _officersOnly ? const <int>[] : _yearLevels;

body = buildEventEditorPayload(
  // ... existing params ...
  yearLevels: effectiveYearLevels,
);

// pass effectiveContext instead of widget.governanceContext:
await repo.create(body, governanceContext: effectiveContext);
// or for edit:
await repo.update(widget.event!.id, body, governanceContext: effectiveContext);
```

#### Build — Audience section (only when in governance context)

Insert after the **Schedule** section and before **Location & geofence**:

```dart
if (_hasGovContext) ...[
  const SectionHeader(title: 'Audience'),
  _OfficersOnlyCard(
    officersOnly: _officersOnly,
    onChanged: (v) => setState(() => _officersOnly = v),
  ),
  const SizedBox(height: AppSpacing.x24),
],
if (!_officersOnly) ...[
  const SectionHeader(title: 'Year levels'),
  _YearLevelCard(
    selected: _yearLevels,
    onToggle: _toggleYearLevel,
  ),
  const SizedBox(height: AppSpacing.x24),
],
```

#### Helper method for year level chip toggling

```dart
void _toggleYearLevel(int level) {
  setState(() {
    if (_yearLevels.contains(level)) {
      _yearLevels = _yearLevels.where((y) => y != level).toList();
    } else {
      _yearLevels = [..._yearLevels, level]..sort();
    }
  });
}
```

#### Widget — `_OfficersOnlyCard`

```dart
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
                Text(
                  officersOnly
                      ? 'Only active governance members can see and attend'
                      : 'All students in the event scope can attend',
                  style: textTheme.bodySmall
                      ?.copyWith(color: t.textSecondary),
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
```

#### Widget — `_YearLevelCard`

```dart
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
          Text(
            selected.isEmpty ? 'All year levels' : 'Year ${selected.join(', ')}',
            style: textTheme.bodySmall?.copyWith(color: t.textMuted),
          ),
          const SizedBox(height: AppSpacing.x8),
          Wrap(
            spacing: AppSpacing.x8,
            children: List.generate(5, (i) {
              final level = i + 1;
              final active = selected.contains(level);
              return FilterChip(
                label: Text('Year $level'),
                selected: active,
                onSelected: (_) => onToggle(level),
                selectedColor: t.accent.withOpacity(0.2),
                checkmarkColor: t.accentDark,
                side: BorderSide(
                  color: active ? t.accentDark : t.border,
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}
```

---

### 4. `test/unit/event_editor_payload_test.dart`

Update the existing snapshot test to include `year_levels`:

```dart
expect(payload, {
  'name': 'Assembly',
  'location': 'Main Hall',
  'description': 'Welcome program',
  'start_datetime': start.toIso8601String(),
  'end_datetime': end.toIso8601String(),
  'year_levels': <int>[],            // <-- ADD THIS
  'geo_required': true,
  'geo_latitude': 8.1552,
  'geo_longitude': 123.8421,
  'geo_radius_m': 150,
});
```

---

## Behaviour Summary

| Context | Toggle | What happens |
|---|---|---|
| Governance (SSG/SG/ORG) | Officers only ON *(default)* | `governance_context` sent → only members see/attend. Year level section hidden. |
| Governance (SSG/SG/ORG) | Officers only OFF | No `governance_context`. Year level chips shown (default = all). |
| Campus admin / no governance | — | No toggle shown. Year level chips shown (default = all). |

## Edit mode

When editing an existing event, the toggle pre-populates from `event.governanceUnitId`:
- `governanceUnitId != null` → toggle ON
- `governanceUnitId == null` → toggle OFF

---

## Notes

- The governance unit is **automatically resolved by the backend** from the creator's
  role and the `governance_context` param. The frontend never needs to send a unit ID.
- `year_levels: []` is the backend sentinel for "all year levels" — always send the
  field, never omit it.
- `flutter analyze` and all 141 tests pass with these changes applied.
