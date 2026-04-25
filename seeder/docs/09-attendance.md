# Chapter 9 — Attendance Generation

[<- Back to index](./README.md)

---

## 9.1 The Attendance Gate

Not every event generates attendance records. The chaos engine assigns a gate probability to each event based on its status:

| Event status | Gate probability `p_g` |
|---|---|
| `COMPLETED` | `1.0` (all students eligible) |
| `ONGOING` | `p_g ~ Uniform(0.20, 0.70)` |
| `CANCELLED` (emergency) | `p_g ~ Uniform(0.01, 0.15)` |
| `CANCELLED` (pre-emptive) | `0.0` (no attendance) |
| `UPCOMING` | `0.0` (no attendance — hallucination protection) |

The gate probability represents the fraction of students who "managed to record" attendance for that event. For a completed event, all students are eligible. For an ongoing event, only a partial snapshot exists. For an emergency cancellation, only a tiny fraction recorded before the event was cut short.

---

## 9.2 Per-Student Attendance Decision

For each eligible event, the seeder iterates over all student profiles. Each student independently passes or fails the gate:

```math
\text{student passes gate} \iff U(0,1) \leq p_g
```

For students who pass the gate, an absence decision is made:

```math
\text{absent} = \begin{cases}
\text{True} & \text{if } U(0,1) \leq 0.25 \\
\text{False} & \text{otherwise}
\end{cases}
```

The base absence probability is fixed at 25%. This is a simplification — in a real system, absence probability would vary per student based on their history. The seeder uses a uniform rate for all students.

For present students, the status is further split:

```math
\text{status} = \begin{cases}
\text{present} & \text{with probability } 0.80 \\
\text{late} & \text{with probability } 0.20
\end{cases}
```

---

## 9.3 Expected Attendance Volume


For a school with `n_s` students and `n_e` events, the expected number of attendance records is:

```math
E[\text{records}] = n_s \times \sum_{i=1}^{n_e} p_{g,i}
```

where `p_{g,i}` is the gate probability for event i.

For a completed event, `p_{g,i} = 1.0`, so it contributes `n_s` records. For an ongoing event with `p_{g,i} = 0.45` (midpoint of the range), it contributes `0.45 * n_s` records.

With default settings (1,000–2,000 students, 30–100 events, ~57% completed), the expected attendance volume per school is approximately:

```math
E[\text{records}] \approx 1500 \times (0.573 \times 65 \times 1.0 + 0.049 \times 65 \times 0.45 + 0.039 \times 65 \times 0.08)
```

```math
\approx 1500 \times (37.2 + 1.4 + 0.2) \approx 1500 \times 38.8 \approx 58{,}200 \text{ records per school}
```

With 5 schools, this is approximately 291,000 attendance records total.

---

## 9.4 Batch Insertion

Attendance records are accumulated in memory and flushed in chunks of 2,000:

```python
for chunk in chunked(attendance_batch, 2000):
    atts = [x[0] for x in chunk]
    db.add_all(atts)
    db.flush()
    # ... process sanctions for this chunk
    db.commit()
```

This bounds memory usage and transaction size. Flushing before committing ensures that `att.id` is populated (assigned by Postgres) before the sanction records that reference it are created.

The chunk size of 2,000 is a balance between memory efficiency and transaction overhead. Smaller chunks mean more round-trips to the database; larger chunks mean more memory held in Python before commit.

---

## 9.5 Attendance Status Encoding

The `Attendance.status` column uses a PostgreSQL native enum (`PG_ENUM`) with lowercase string values. The seeder uses `.value` to extract the raw string:

```python
status = AttendanceStatus.ABSENT.value if absent else rng.choices(
    [AttendanceStatus.PRESENT.value, AttendanceStatus.LATE.value],
    weights=[80, 20], k=1
)[0]
```

This is necessary because the backend model uses `PG_ENUM` with `create_type=True`, which stores raw strings rather than Python enum objects.
