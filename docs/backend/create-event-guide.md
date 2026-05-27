# Create Event — API Guide

**Endpoint:** `POST /api/events/`
**Auth required:** Yes — `campus_admin` or governance officer role
**Response:** `201 Created` — returns the full event object

---

## Required Fields

| Field | Type | Rules |
|-------|------|-------|
| `name` | `string` | 1–100 characters |
| `start_datetime` | `datetime` | ISO 8601. Naive datetimes are auto-assigned **Philippine Time (UTC+8)**. |
| `end_datetime` | `datetime` | Must be **after** `start_datetime` |

---

## Optional Fields

| Field | Type | Default | Rules |
|-------|------|---------|-------|
| `status` | `enum` | `"upcoming"` | `upcoming` / `ongoing` / `completed` / `cancelled` |
| `location` | `string` | `null` | Max 200 chars |
| `description` | `string` | `null` | Free text |
| `venue` | `string` | `null` | Free text |
| `notes` | `string` | `null` | Free text |
| `banner_url` | `string` | `null` | URL string |
| `event_type_id` | `integer` | `null` | Must exist in the school |
| `year_levels` | `int[]` | `[]` | Values 1–5. Empty array = all year levels. **Always send this field — never omit it.** |
| `early_check_in_minutes` | `integer` | school default | 0–1440 |
| `late_threshold_minutes` | `integer` | school default | 0–1440 |
| `sign_out_grace_minutes` | `integer` | school default | 0–1440 |
| `sign_out_open_delay_minutes` | `integer` | `0` | 0–1440, must be ≤ `sign_out_grace_minutes` |

---

## Geolocation Fields (all optional, but linked)

| Field | Type | Rules |
|-------|------|-------|
| `geo_latitude` | `float` | -90 to 90 |
| `geo_longitude` | `float` | -180 to 180 |
| `geo_radius_m` | `float` | 0–5000 m |
| `geo_required` | `bool` | Default `false`. If `true`, lat/lon/radius must all be set. |
| `geo_max_accuracy_m` | `float` | 0–1000 m |

---

## Optional Request Header

| Header | Description |
|--------|-------------|
| `X-Idempotency-Key` | String ≤128 chars. If the same key is sent twice by the same user, the backend returns the first created event instead of creating a duplicate. Safe to use for retry logic. |

---

## Attendance Timing Windows (Sign-In & Sign-Out)

When an event is created, the system calculates precise times for when attendance (sign-in and sign-out) is open, late, absent, or closed based on the event's start/end times and the window configuration fields.

### Formula & Timing Statuses

| Event Status | Time Range | Result / Check-In Eligibility |
| :--- | :--- | :--- |
| **`before_check_in`** | Before `check_in_opens_at` | Check-in is **closed**. |
| **`early_check_in`** | `check_in_opens_at` to `start_datetime` | Check-in is **open**. Marked as **`present`**. |
| **`late_check_in`** | `start_datetime` to `late_threshold_time` | Check-in is **open**. Marked as **`late`**. |
| **`absent_check_in`** | `late_threshold_time` to `end_datetime` | Check-in is **open**. Marked as **`absent`**. |
| **`sign_out_pending`** | `end_datetime` to `sign_out_opens_at` | Check-in is **closed**; sign-out not yet open. |
| **`sign_out_open`** | `sign_out_opens_at` to `effective_sign_out_closes_at` | Check-in is **closed**. Sign-out is **open**. |
| **`closed`** | After `effective_sign_out_closes_at` | All attendance windows are **closed**. |

### Key Boundaries Calculation

*   **`check_in_opens_at`** = `start_datetime - early_check_in_minutes`
*   **`late_threshold_time`** = `start_datetime + late_threshold_minutes`
*   **`sign_out_opens_at`** = `end_datetime + sign_out_open_delay_minutes`
*   **`effective_sign_out_closes_at`** = `end_datetime + sign_out_grace_minutes` (capped by any active `sign_out_override_until` datetime, if set)

---

### Timing Example

Let's say an event has:
*   **`start_datetime`**: `09:00 AM`
*   **`end_datetime`**: `11:00 AM`
*   **`early_check_in_minutes`**: `30`
*   **`late_threshold_minutes`**: `10`
*   **`sign_out_open_delay_minutes`**: `0`
*   **`sign_out_grace_minutes`**: `20`

Here is the exact schedule generated:

*   **`08:30 AM`**: Sign-in **opens** (`09:00 AM - 30 minutes`). Status is `early_check_in` (marked **`present`**).
*   **`09:00 AM`**: Event starts. Status changes to `late_check_in` (marked **`late`**).
*   **`09:10 AM`**: Late threshold passed (`09:00 AM + 10 minutes`). Status changes to `absent_check_in` (marked **`absent`**).
*   **`11:00 AM`**: Event ends. Sign-in closes. Sign-out **opens** immediately. Status is `sign_out_open`.
*   **`11:20 AM`**: Sign-out **closes** (`11:00 AM + 20 minutes`). Status is `closed`. All windows are now shut.

---

## Audience Targeting

### For Campus Admins (no governance context)

Use `year_levels` in the request body to control who can attend:

- `"year_levels": []` → all year levels (default, no restriction)
- `"year_levels": [1, 2, 3]` → only Year 1, 2, and 3 students

### For Governance Officers (SSG / SG / ORG)

Governance officers have two modes controlled by the `governance_context` **query parameter**:

---

#### Mode 1 — Officers Only (restricted to governance members)

Add `?governance_context=SSG` (or `SG` / `ORG`) to the URL:

```
POST /api/events/?governance_context=SSG
```

- The backend sets `governance_unit_id` on the event
- Only **active members** of that governance unit can see and attend
- Students who are not members get a `NOT_A_GOVERNANCE_MEMBER` error at check-in
- The event is hidden from non-members in the event list
- Send `"year_levels": []` in the body (year level targeting is ignored in this mode)

---

#### Mode 2 — Open to all (normal targeting, no member restriction)

Omit the `governance_context` query parameter:

```
POST /api/events/
```

- `governance_unit_id` is null — no membership restriction
- `year_levels` in the body controls the audience normally
- `"year_levels": []` = all year levels

---

#### Governance Context Values

| Value | Governance Unit |
|-------|----------------|
| `SSG` | Supreme Student Government |
| `SG` | Student Government |
| `ORG` | Organization |

> **Note:** The backend automatically resolves which governance unit to use from the creator's role and the `governance_context` param. The frontend **never needs to send a unit ID**.

---

## Audience Behavior Summary

| Who creates | `governance_context` param | `year_levels` body | Who can attend |
|---|---|---|---|
| Campus admin | — (not applicable) | `[]` | All students |
| Campus admin | — (not applicable) | `[1, 2]` | Year 1 & 2 only |
| Governance officer | `?governance_context=SSG` | `[]` | Active SSG members only |
| Governance officer | *(omitted)* | `[]` | All students |
| Governance officer | *(omitted)* | `[3]` | Year 3 students only |

---

## Examples

### Minimal — Campus Admin (all students)

```json
POST /api/events/

{
  "name": "JS201 Final Exam",
  "start_datetime": "2026-06-01T08:00:00+08:00",
  "end_datetime": "2026-06-01T10:00:00+08:00",
  "year_levels": []
}
```

### Full — Campus Admin (specific year levels + geolocation)

```json
POST /api/events/

{
  "name": "Department Assembly",
  "start_datetime": "2026-06-05T09:00:00+08:00",
  "end_datetime": "2026-06-05T11:00:00+08:00",
  "status": "upcoming",
  "location": "Main Auditorium",
  "description": "Monthly department assembly.",
  "event_type_id": 2,
  "year_levels": [1, 2, 3],
  "early_check_in_minutes": 15,
  "late_threshold_minutes": 10,
  "sign_out_grace_minutes": 30,
  "geo_latitude": 8.1552,
  "geo_longitude": 123.8421,
  "geo_radius_m": 150,
  "geo_required": true
}
```

### Officers Only — SSG event (members only)

```
POST /api/events/?governance_context=SSG
```
```json
{
  "name": "SSG Officer Meeting",
  "start_datetime": "2026-06-10T09:00:00+08:00",
  "end_datetime": "2026-06-10T11:00:00+08:00",
  "year_levels": []
}
```

### Governance-organized but open — SSG event (all students, specific year levels)

```
POST /api/events/
```
```json
{
  "name": "SSG-Organized General Assembly",
  "start_datetime": "2026-06-10T09:00:00+08:00",
  "end_datetime": "2026-06-10T11:00:00+08:00",
  "year_levels": [1, 2, 3, 4]
}
```

---

## Common Errors

| Status | Detail | Cause |
|--------|--------|-------|
| `400` | `End datetime must be after start datetime` | `end_datetime` ≤ `start_datetime` |
| `400` | `sign_out_open_delay_minutes cannot be greater than sign_out_grace_minutes` | Delay exceeds grace window |
| `400` | `Department ID X not found in this school` | `department_id` does not belong to this school |
| `400` | `Program ID X not found in this school` | `course_id` does not belong to this school |
| `400` | `Event creation failed (possible duplicate)` | DB integrity error — check idempotency key |
| `403` | `NOT_A_GOVERNANCE_MEMBER` | Student tried to check in to a members-only event they don't belong to |

---

## Related Docs

- [`year-level-event-targeting.md`](year-level-event-targeting.md) — detailed targeting model internals
- [`docs/frontend/governance-officers-only-event.md`](../../docs/frontend/governance-officers-only-event.md) — Flutter UI implementation guide for the Officers Only toggle
