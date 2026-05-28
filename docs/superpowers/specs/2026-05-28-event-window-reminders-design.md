# Event window reminders — design

**Date:** 2026-05-28
**Scope:** Flutter app (`frontend-app/`) only. No backend changes.
**Status:** Draft awaiting user review.

## Problem

Students currently learn that an event's check-in or sign-out window has
opened only by opening the app and looking. The existing "Nearby event
check-in" feature (v1.19.0 / v1.20.0) fires a notification when the user
**arrives** at an event's geofence, but it does not fire when the **time
window** itself opens. A user who is already on site at start time, or
who needs to sign out at the end of the day, gets no reminder.

This feature adds time-based reminders that fire when the backend's
`check_in_opens_at` and `sign_out_opens_at` thresholds are reached, plus
short lead-time nudges so the user has a chance to move.

## Goal

Notify the user — accurately, on time — when an event they can attend
becomes ready for check-in or sign-out. The reminder must align exactly
with the backend's window logic: a notification claiming "check-in is
open" must coincide with the backend actually accepting a check-in scan.

## Non-goals

- Push notifications from the server (no FCM integration in this app).
- Reminders for events the user has no audience for (filtered server-side
  via `scheduleEventsProvider`).
- Reminding officers/admins to **manage** their own events (separate
  workflow; this feature targets the student attendance flow).
- Auto sign-in / sign-out without a face scan.

## Hard constraint: do not break the existing geofence feature

The existing **"Nearby event check-in"** location-based notification
(v1.19.0 / v1.20.0, controlled by `autoCheckInProvider`, fired via the
`nearby_checkin` channel and `NearbyEventBanner`) must keep working
exactly as it does today. This new feature runs **alongside** it, never
in place of it. Both toggles are independent. Both notification types
must fire correctly when both toggles are on. Specifically:

- The `nearby_checkin` Android channel is not renamed, re-described,
  or re-registered with different `importance` / `priority`.
- The existing `_initSettings` / `nearbyGeofenceCallback` /
  `pendingCheckInProvider` / `geofenceBackgroundProvider` symbols keep
  the same signatures.
- Changes to `geofence_background.dart` are **additive only**: a new
  channel registration call, a new payload format the dispatcher
  accepts in addition to the existing one. No refactor of the
  existing flow.
- The new `event_window` channel and `EventPhaseBanner` widget are
  new code, not replacements.
- The new toggle defaults ON, but the existing nearby toggle's default
  (OFF) is unchanged.
- `NearbyEventBanner` rendering and tap behavior are unchanged. The
  new `EventPhaseBanner` mounts **above** it on student Home; both
  can render simultaneously when both fire.

## Backend ground truth

All event-window logic lives in
`backend/app/services/event_time_status.py`. All times are computed in
**Asia/Manila** (`DEFAULT_EVENT_TIMEZONE`). The authoritative state
machine, in order of phase transitions:

| Phase | Begins when | Check-in allowed? | Sign-out allowed? |
|---|---|---|---|
| `before_check_in` | `start_datetime − early_check_in_minutes` not yet reached | No | No |
| `early_check_in` | `now ≥ check_in_opens_at` | Yes → **present** | No |
| `late_check_in` | `now ≥ start_time` | Yes → **late** | No |
| `absent_check_in` | `now > late_threshold_time` (and `now < end_time`) | Yes → **absent** | No |
| `sign_out_pending` | `now ≥ end_time` (and `now < sign_out_opens_at`) | No | No |
| `sign_out_open` | `now ≥ sign_out_opens_at` | No | Yes |
| `closed` | `now > effective_sign_out_closes_at` | No | No |

Computed timestamps returned by `GET /events/{id}/time-status`
(`EventTimeStatusInfo` schema):

| Field | Formula |
|---|---|
| `check_in_opens_at` | `start_datetime − early_check_in_minutes` |
| `late_threshold_time` | `start_datetime + late_threshold_minutes` |
| `sign_out_opens_at` | `end_datetime + sign_out_open_delay_minutes` |
| `normal_sign_out_closes_at` | `end_datetime + sign_out_grace_minutes` |
| `effective_sign_out_closes_at` | `min(normal_sign_out_closes_at, sign_out_override_until)` |
| `attendance_override_active` | true when present/late overrides shift cutoffs |

Constraint enforced server-side:
`sign_out_open_delay_minutes ≤ sign_out_grace_minutes`.

### Customization cascade

The four window fields cascade across four configuration layers (more
specific layers override less specific layers, all resolved at event
**creation**):

| Layer | Who controls it | Surface | Affects |
|---|---|---|---|
| Live overrides | Event manager | `POST /events/{id}/sign-out/open-early`, `PATCH /events/{id}/status` | This event only, mid-event |
| Per-event values | Campus admin / SG / ORG officer (whoever creates / edits the event) | `POST /events/`, `PATCH /events/{id}` | This event only |
| Governance unit defaults | SSG / SG / ORG officers | Governance unit settings | Future events created in this unit's scope |
| School defaults | Campus admin (school-IT) | `PUT /school/settings` (`event_default_early_check_in_minutes` etc.) | Future events without a more specific override |
| Hardcoded baseline | — | `event_defaults.py` (`30 / 10 / 20`) | When nothing else is set |

Once an event row exists, only the **per-event values** and **live
overrides** matter for that event. School and unit defaults are copied
in at creation time and do not retroactively apply. Hence the client
only needs to track per-event `EventTimeStatusInfo` snapshots — never
the cascade itself.

## Client design

### Source of truth

The client never derives `check_in_opens_at` or `sign_out_opens_at`
from raw `AppEvent` fields. It calls `GET /events/{id}/time-status` and
schedules notifications at the timestamps the server returns. Reasons:

1. `sign_out_opens_at` depends on `sign_out_open_delay_minutes`, a field
   not exposed on the current `AppEvent` model.
2. `effective_sign_out_closes_at` may be capped by `sign_out_override_until`.
3. The server's timezone is canonical; computing in the device's local
   time drifts when devices travel across zones.

### Sync semantics

A new `eventWindowSyncProvider` watches `scheduleEventsProvider` and a
30-second ticker. On each sync run:

1. Filter to events where `effective_sign_out_closes_at > now AND start_datetime < now + 48h`.
2. For each event, call `GET /events/{id}/time-status` in parallel via
   `Future.wait`. Cap concurrency at 6 to avoid socket exhaustion on
   slow networks.
3. Cache the response in `EventScheduleCache` (persisted with
   `shared_preferences` so it survives cold start).
4. For each event, schedule up to **five** local notifications:

   | # | Fire at | Body |
   |---|---|---|
   | 0 | `check_in_opens_at − 10m` | "Check-in opens in 10 min: <Event>" |
   | 1 | `check_in_opens_at` | "Check-in is open: <Event>" |
   | 2 | `sign_out_opens_at − 10m` | "Sign-out opens in 10 min: <Event>" |
   | 3 | `sign_out_opens_at` | "Sign-out is open: <Event>" |
   | 4 | `effective_sign_out_closes_at − 10m` | "Sign-out closes in 10 min: <Event>" |

   **Skip rules** (per slot, evaluated independently):
   - Skip if the computed fire time is already in the past.
   - Skip slot 0 if `check_in_opens_at − 10m ≤ now` (covered by slot 1).
   - Skip slot 2 if `sign_out_opens_at − 10m ≤ check_in_opens_at`
     (short-duration event collapses the windows).
   - Skip slot 4 if `effective_sign_out_closes_at − 10m ≤ sign_out_opens_at`
     (event uses `sign_out_grace_minutes < 10`).
   - Skip the entire event if `attendance_override_active` is true and
     the cached snapshot is older than 60 s — the override may have
     shifted things; defer until next sync brings a fresh snapshot.

   Use `flutter_local_notifications.zonedSchedule(...)` with
   `tz.TZDateTime` in `Asia/Manila` so DST and time-zone changes do not
   skew firing. `androidScheduleMode = AndroidScheduleMode.exactAllowWhileIdle`.

5. Notification IDs encode `event_id * 10 + phase_code` (phase_code ∈
   0..4). Stable IDs let re-sync cancel only the slots that need
   updating, instead of nuking and rebuilding the whole schedule.

6. After computing the desired schedule, diff against currently
   scheduled IDs (via `flutter_local_notifications.pendingNotificationRequests()`)
   and cancel any IDs that no longer belong to a tracked event.

### Re-sync triggers

| Trigger | Throttle |
|---|---|
| App resume (`AppLifecycleState.resumed`) | Skip if last sync < 5 min ago |
| `scheduleEventsProvider` data refresh | None — sync immediately |
| Pull-to-refresh on Schedule tab | None |
| Toggle flipped on | None |
| User logs out | Cancel all event-window notifications immediately |
| User logs in (new session) | Sync once at session start |

### In-app banner (`EventPhaseBanner`)

A new banner widget shown above `NearbyEventBanner` on the student
Home. Renders when one or more events are in an actionable phase
(`early_check_in`, `late_check_in`, `sign_out_open`) or just-transitioned
within the last 5 minutes.

- **Source:** `eventPhaseProvider` joins `scheduleEventsProvider`,
  the `EventScheduleCache`, and a 30-second ticker. Computes current
  phase per event purely from cached timestamps (no extra network
  calls).
- **Priority** if multiple events qualify: `sign_out_open` (highest) >
  `early_check_in` / `late_check_in` > `sign_out_closing_soon`.
- **Style:** gradient card matching the existing `NearbyEventBanner`
  visual family (accent → accentDark gradient, accent-tinted shadow,
  pulsing dot, 22 px radius). Distinct icon and copy per phase:
  - `early_check_in` / `late_check_in`: "CHECK-IN IS OPEN", `Icons.login_rounded`.
  - `sign_out_open`: "SIGN-OUT IS OPEN", `Icons.logout_rounded`.
  - `sign_out_closing_soon`: "LAST CALL: SIGN OUT NOW", same `logout` icon, amber tint.
- **Motion:** `SizeTransition` + `FadeTransition` enter (320 ms,
  `easeOutCubic`), matching `NearbyEventBanner`. Pulsing dot reused
  from the existing `_PulseDot`. Honors `MediaQuery.disableAnimations`.
- **Tap:** sets `pendingCheckInProvider` to the event's id (already
  wired to push `AttendanceScreen`).

### Toggle

New `eventWindowRemindersProvider` (parallel to `autoCheckInProvider`):

- Persisted via `SharedPreferences` (`aura_event_window_reminders`).
- **Default ON.** Justification: no continuous location access, no
  battery overhead beyond the OS's existing scheduled-alarm path.
- Account → Beta features tile: "Event window reminders" with subtitle
  "Notifies you when check-in or sign-out opens for events on your
  schedule."

### Notification channel

New Android channel `event_window` (importance: high). Separate from
the existing `nearby_checkin` channel so users can mute one without the
other. Channel description: "Reminders when check-in or sign-out opens
for events you can attend."

### Tap routing

Reuses the existing `pendingCheckInProvider` plumbing without changing
its type. Payload formats:

- `checkin:<event_id>` — existing, geofence flow (unchanged).
- `checkin:<event_id>:checkin` — new, check-in window open.
- `checkin:<event_id>:signout` — new, sign-out window open.

`GeofenceBackground._dispatch` is extended to parse `<event_id>` from
either form (split on `:` and parse the second segment). The existing
flow stays on `pendingCheckInProvider` (`StateProvider<int?>`); the new
flow writes to `pendingCheckInProvider` for the event id **and** to a
new sibling `pendingAttendanceActionProvider`
(`StateProvider<AttendanceAction?>`, where `AttendanceAction` is
`checkin` or `signout`). The student-home listener reads the action
hint to pre-select scan mode; `AttendanceScreen` already infers action
from event state, so the hint is informational and harmless if missing.
This keeps the existing geofence consumer's contract untouched.

## Failure modes and mitigations

| Failure | Mitigation |
|---|---|
| Admin edits event timing while student's app is closed; scheduled notification at old time | Re-sync on every app resume + pull-to-refresh; worst case is one wrong-time notification that the banner overrides within 30 s |
| Admin uses `open-sign-out-early` to move `end_datetime` to "now" while app is closed | Student misses the early sign-out unless they open the app. Acceptable: this is an exceptional admin action. Surfaced in settings copy. |
| `GET /events/{id}/time-status` errors during sync | Keep the cached snapshot from previous successful sync; retry on next trigger. Don't cancel existing scheduled notifications on transient failures. |
| Device denies notification permission | Sync still caches data so the in-app banner works; toggle UI surfaces an "enable notifications" prompt linking to settings |
| Android 12+ `SCHEDULE_EXACT_ALARM` revoked | Fall back to `AndroidScheduleMode.inexactAllowWhileIdle`; surface a settings prompt to re-enable |
| Time zone change (user travels) | `tz.TZDateTime` in `Asia/Manila` is absolute, so notifications fire at the correct wall-clock time regardless of device locale |
| Stale schedule survives logout | Logout handler calls `cancelAll()` on `event_window`-prefixed IDs |

## Files

### New
- `lib/features/events/application/event_window_reminders_controller.dart`
- `lib/features/events/application/event_schedule_cache.dart`
- `lib/features/events/application/event_window_scheduler.dart`
- `lib/features/events/application/event_window_sync.dart`
- `lib/features/events/application/event_phase_provider.dart`
- `lib/features/events/data/event_time_status_bulk.dart`
- `lib/features/events/presentation/widgets/event_phase_banner.dart`
- `test/unit/event_window_scheduler_test.dart`
- `test/unit/event_phase_provider_test.dart`
- `test/widget/event_phase_banner_test.dart`

### Modified
- `lib/main.dart` — `tz.initializeTimeZones()` + `tz.setLocalLocation(tz.getLocation('Asia/Manila'))` at boot.
- `lib/features/events/application/geofence_background.dart` — share the `FlutterLocalNotificationsPlugin` instance, register the `event_window` channel, extend tap-payload parsing.
- `lib/features/student/presentation/student_home.dart` — mount `EventPhaseBanner` above `NearbyEventBanner`.
- `lib/features/account/presentation/account_tab.dart` — add toggle tile to the Beta features section.
- `lib/app/app.dart` — watch `eventWindowSyncProvider` for the session.
- `frontend-app/pubspec.yaml` — version bump to 1.32.0; explicit dependency on `timezone` package.
- `frontend-app/CHANGELOG.md` — `[Unreleased]` entry describing the feature.

### Untouched
- All backend code.
- `docs/Backend Documentation.md` (no backend changes).
- Existing geofence flow (`NearbyEventBanner`, `nearby_checkin` channel) remains independent.

## Verification

- `flutter analyze` clean.
- `flutter test` passes (existing 120 tests + 3 new test files).
- Manual: with `eventWindowRemindersProvider` on, schedule a test event 2
  minutes ahead with `early_check_in_minutes = 0`; lock the device;
  confirm OS notification fires within ±5 s of the scheduled time.
- Manual: with the app foreground, observe `EventPhaseBanner` enter
  within 30 s of the phase transition.
- Manual: edit the event's `start_datetime` (via web admin), re-open
  the app, confirm the new schedule replaces the old.
- Manual: toggle off, confirm all `event_window`-prefixed pending
  notifications are cancelled.

### Regression checks for the existing nearby check-in feature

These must all still pass after the change is in:

- Toggle "Nearby event check-in" on, leave "Event window reminders"
  off. Enter a geofenced event's radius. OS notification fires from
  the `nearby_checkin` channel. Tap routes to `AttendanceScreen` for
  the right event.
- Same as above with `EventPhaseBanner` mounted: it does not block,
  hide, or override `NearbyEventBanner`. Both can render at once when
  both apply.
- Toggle "Nearby event check-in" off. Existing geofences are removed
  (`GeofenceBackground.stop`), no nearby notifications fire.
- Both toggles on, single event in geofence and in check-in window:
  both notification types fire on their respective channels; tapping
  either reaches `AttendanceScreen`.
- The `nearby_checkin` channel appears unchanged in Android settings
  (same name, same description, same importance level).

## Out of scope (future work)

- Server-side push (FCM/APNs) for last-minute admin edits.
- Reminding officers about events they manage (separate UX).
- Customizing lead-time (currently fixed at 10 min for all triggers).
- Per-event mute (e.g. "don't remind me about this one").
