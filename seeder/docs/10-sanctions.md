# Chapter 10 — Sanctions and Compliance Generation

<!--nav-->
[← Ch.9 Attendance](09-attendance.md) | [🏠 Home](/README.md) | [Ch.11 Running →](11-running.md)

---
<!--/nav-->

---

## 10.1 Sanction Record Creation

A sanction record is created for every absent attendance record that has a sanction config ID. Since every event gets a sanction config (see [Chapter 8](./08-events.md)), the condition simplifies to: every absent attendance record generates a sanction record.

The sanction record links:
- The school
- The event
- The sanction config
- The student profile
- The attendance record (via `attendance_id` FK)

---

## 10.2 Compliance Simulation

Each sanction record is independently resolved with probability 0.30:

```math
\text{resolved} = \begin{cases}
\text{True} & \text{if } U(0,1) < 0.30 \\
\text{False} & \text{otherwise}
\end{cases}
```

This means approximately 30% of sanctions are `COMPLIED` and 70% remain `PENDING`. This ratio is intentional — it reflects a realistic scenario where most sanctions are still outstanding at any given time, which makes the sanctions dashboard non-trivial to look at.

---

## 10.3 Sanction Items

Each sanction record gets two items:

| Item code | Item name |
|-----------|-----------|
| `LETTER` | Apology Letter |
| `FINE` | Community Fine |

Both items inherit the compliance status of their parent record — if the record is `COMPLIED`, both items are `COMPLIED`; if `PENDING`, both are `PENDING`.

For resolved records, `complied_at` is set to `t_\text{now}` (the wall-clock time at the start of the seeder run).

---

## 10.4 Compliance History

For each resolved sanction record, a `SanctionComplianceHistory` entry is created for each item:

- `complied_by_user_id`: a random leader from the school's leader pool
- `notes`: drawn uniformly from `COMPLIANCE_NOTES` in `data.py`
- `school_year`: `"2024-2025"` (default)
- `semester`: `"1st Semester"` (default)

---

## 10.5 Expected Sanction Volume

The expected number of sanction records is:


```math
E[\text{sanctions}] = E[\text{attendance records}] \times P(\text{absent}) = E[\text{attendance records}] \times 0.25
```

Using the estimate from [Chapter 9](./09-attendance.md):


```math
E[\text{sanctions}] \approx 291{,}000 \times 0.25 \approx 72{,}750 \text{ records}
```

Of these, approximately 30% are resolved:


```math
E[\text{complied}] \approx 72{,}750 \times 0.30 \approx 21{,}825
```

```math
E[\text{pending}] \approx 72{,}750 \times 0.70 \approx 50{,}925
```

Each sanction record has 2 items, so:

```math
E[\text{sanction items}] \approx 72{,}750 \times 2 = 145{,}500
```

```math
E[\text{compliance history entries}] \approx 21{,}825 \times 2 = 43{,}650
```

---

## 10.6 The `_seeder_sanction_config_id` Pattern

The `Event` model has no `sanction_config_id` column — the relationship is one-to-one but navigated from the `EventSanctionConfig` side. After creating the sanction config for an event, the seeder stores the config ID as a transient Python attribute on the ORM object:

```python
conf = create_sanction_config(db, school_id=school.id, event_id=ev.id, ...)
ev._seeder_sanction_config_id = conf.id
```

Later, during the attendance loop:

```python
conf = ev._seeder_sanction_config_id if hasattr(ev, '_seeder_sanction_config_id') else None
```

This is a seeder-internal handoff pattern. The attribute is not persisted to the database — it exists only in memory during the seeder run. SQLAlchemy does not complain about extra attributes on ORM objects.
