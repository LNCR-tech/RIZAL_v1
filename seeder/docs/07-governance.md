# Chapter 7 — Governance Hierarchy Generation

[<- Back to index](./README.md)

---

## 7.1 Hierarchy Structure

Each school gets a three-level governance hierarchy:

```
SSG (Supreme Student Government)          — 1 per school
  └── SG (Student Government)             — 1 per department
        └── ORG (Student Organization)    — 0–2 per SG
```

This mirrors the real-world governance structure that Aura is designed to manage.

---

## 7.2 SSG Unit

One SSG unit is created per school:

- `unit_code`: `SSG-{school.id}`
- `unit_name`: `"Supreme Student Government"`
- `unit_type`: `GovernanceUnitType.SSG`
- `parent_unit_id`: `None` (root of the hierarchy)

The SSG is assigned the full set of all governance permissions (`SSG_PERMISSIONS = [p for p in PermissionCode]`).

---

## 7.3 SG Units

One SG unit is created per department in the school:

- `unit_code`: `SG-{dept.id}`
- `unit_name`: `"{dept.name} Student Gov"`
- `unit_type`: `GovernanceUnitType.SG`
- `parent_unit_id`: `ssg_unit.id`
- `department_id`: `dept.id`

SG units are assigned a subset of permissions:

```python
SG_PERMISSIONS = [
    CREATE_ORG, MANAGE_STUDENTS, VIEW_STUDENTS,
    MANAGE_EVENTS, MANAGE_ATTENDANCE,
    VIEW_SANCTIONED_STUDENTS_LIST,
    APPROVE_SANCTION_COMPLIANCE,
    VIEW_SANCTIONS_DASHBOARD
]
```

---

## 7.4 ORG Units

For each SG unit, 0–2 ORG units are created:

```math
n_\text{org} \sim \text{Uniform}(0, 2)
```

- `unit_code`: `ORG-{sg.id}-{j}`
- `unit_name`: `"{dept_code} Sub-Org {j+1}"`
- `unit_type`: `GovernanceUnitType.ORG`
- `parent_unit_id`: `sg.id`
- `department_id`: `dept.id`

ORG units are assigned a minimal permission set:

```python
ORG_PERMISSIONS = [VIEW_STUDENTS, MANAGE_EVENTS, MANAGE_ATTENDANCE]
```

---

## 7.5 Announcements

Announcements are generated for governance units using templates from `data.py`.

**SSG announcements:** $k \sim \text{Uniform}(2, 4)$ announcements are sampled without replacement from the 5 announcement templates and created for the SSG unit.

**SG announcements:** Each SG unit has a 70% probability of getting one announcement:

```math
X \sim \text{Bernoulli}(0.70)
```

If it fires, one announcement template is drawn uniformly and prefixed with the department code.

---

## 7.6 Governance Officers — The Leader Pool

Officers are drawn from the student body using a two-stage process.

### Stage 1: Leader Pool Selection

The top ~15% of students are designated as the leader pool:

```math
n_\text{leaders} = \max\left(5,\ \lfloor 0.15 \times n_\text{students} \rfloor\right)
```

The floor of 5 ensures there are always enough leaders even for very small student counts. Leaders are sampled without replacement from the full student list.

The leader pool is a fixed subset for the duration of the school's generation. All officer assignments draw from this same pool.

### Stage 2: Officer Assignment

Officers are assigned per governance unit by sampling from the leader pool **with replacement** (i.e., the same student can be assigned to multiple units). This is the "hybrid overlay" — a student can simultaneously be an SSG officer, an SG officer for one department, and an ORG officer for another.

| Unit type | Officers per unit |
|-----------|------------------|
| SSG | $k \sim \text{Uniform}(3, 5)$ |
| SG | $k \sim \text{Uniform}(1, 3)$ per SG unit |
| ORG | $k \sim \text{Uniform}(1, 2)$ per ORG unit |

Each officer is assigned:
- The appropriate role (`ssg`, `sg`, or `org`) via `assign_role()`
- A `GovernanceMember` record linking them to the unit
- A random subset of the unit's permission set

### Permission Subset per Member

For each officer, the number of permissions granted is:

```math
k_\text{perms} \sim \text{Uniform}(1,\ |\text{unit\_permission\_set}|)
```

Then $k_\text{perms}$ permissions are sampled without replacement from the unit's permission set. This means:

- Some officers have nearly full permissions
- Some officers have minimal permissions
- The distribution is uniform over all possible subset sizes

---

## 7.7 Student Notes

After officer assignment, ~10% of students receive a governance note:

```math
n_\text{notes} = \max\left(1,\ \lfloor 0.10 \times n_\text{students} \rfloor\right)
```

Students are sampled without replacement. For each noted student:

- A random leader is chosen as the note creator
- The note is assigned to either the SSG unit (50% probability) or a random SG unit (50%)
- 1–2 tags are sampled from `MOCK_NOTE_TAGS`
- The note body is drawn uniformly from `MOCK_NOTES_POOL`
