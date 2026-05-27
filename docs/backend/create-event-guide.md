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
