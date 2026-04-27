# Chapter 5 — Academic Structure Generation

<!--nav-->
[← Ch.4 RNG Model](04-rng.md) | [🏠 Home](/README.md) | [Ch.6 Users →](06-users.md)

---
<!--/nav-->

---

## 5.1 School Selection

Schools are selected from a fixed pool of 21 names in `data.py` using `rng.sample()` — sampling without replacement. This guarantees no duplicate school names regardless of how many schools are requested.

```math
	ext{selected\_schools} = \text{sample}(\text{SCHOOL\_NAMES},\ k = \min(N_s,\ 21))
```

where `N_s` is `SEED_N_SCHOOLS`. If you request more than 21 schools, the seeder silently caps at 21.

Each school gets:
- A `school_name` (the full name from the pool)
- A `school_code` derived as the first 3 characters uppercased + `"U"` (e.g., `"Aura University"` → `"AURU"`)
- A `school_domain` derived by stripping non-alpha characters and appending `.edu.ph` (e.g., `"Aura University"` → `"aurauniversity.edu.ph"`)
- Default branding colors: primary `#162F65`, secondary `#2C5F9E`, accent `#4A90E2`

---

## 5.2 College and Program Selection

The college/program dataset in `data.py` contains 15 colleges, each with a list of programs. For each school, the seeder:

1. Draws the number of colleges:
   ```math
   n_c \sim \text{Uniform}(\text{min\_colleges},\ \text{max\_colleges})
   ```
2. Samples `n_c` colleges without replacement from the 15 available
3. For each selected college, draws the number of programs:

```math
n_p \sim \text{Uniform}(\max(1,\ \text{min\_programs}),\ |\text{programs for this college}|)
```

4. Samples `n_p` programs without replacement from that college's program list

The result is a dict `{college_name: [program_names]}` that is unique per school. Two schools will rarely have the same academic structure.

### Why this matters

The program pool per school directly affects student distribution (see [Chapter 6](./06-users.md)) and event scope (see [Chapter 8](./08-events.md)). A school with more programs has more granular event targeting and more diverse student enrollment patterns.

---

## 5.3 Department and Program Records

Each college becomes a `Department` record. Each program becomes a `Program` record. The many-to-many link between them is created via the `program_department_association` table.

All operations use get-or-create semantics — if a department or program with the same name already exists for that school, it is reused rather than duplicated. This makes the seeder safe to run with `SEED_WIPE_EXISTING = False`.

---

## 5.4 Academic Periods

For each school, the seeder seeds `academic_periods` rows covering every school year in the configured date range (`SEED_START_MMDDYY` to `SEED_END_MMDDYY`). Each year gets three periods:

| Semester | Months (approximate) |
|---|---|
| 1st Semester | August – December |
| 2nd Semester | January – May |
| Summer | June – July |

For example, with a 2024–2026 range, each school gets 9 academic period rows (3 years × 3 semesters). These are used to link `sanction_compliance_history` records to a realistic academic term based on the event date (see [Chapter 10](./10-sanctions.md)).

---

## 5.5 School Settings

Each school gets a `SchoolSetting` record created alongside it, with the same branding colors. This is required by the backend — the settings record is expected to exist for any school that has users.

---

## 5.5 Data Integrity Constraints

The seeder respects the following schema constraints:

- `UniqueConstraint("school_id", "name")` on `departments` — enforced by get-or-create
- `UniqueConstraint("school_id", "name")` on `programs` — enforced by get-or-create
- `UniqueConstraint("school_id", "unit_code")` on `governance_units` — unit codes are derived from IDs, which are unique
- `UniqueConstraint("school_id", "student_id")` on `student_profiles` — enforced by a collision-resistant loop (see [Chapter 6](./06-users.md))
