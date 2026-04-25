# Chapter 6 — User and Identity Generation

[<- Back to index](./README.md)

---

## 6.1 Name Generation

Student names are drawn independently from three pools in `data.py`:

- `FIRST_NAMES` — 119 entries, multicultural (English, Spanish, Japanese, Arabic, Indian, Filipino)
- `LAST_NAMES` — 96 entries, similarly multicultural with Filipino surnames weighted higher
- `MIDDLE_NAMES` — 54 entries

Each draw is independent and uniform:

```math
\text{first} \sim \text{Uniform}(\text{FIRST\_NAMES}), \quad \text{last} \sim \text{Uniform}(\text{LAST\_NAMES}), \quad \text{middle} \sim \text{Uniform}(\text{MIDDLE\_NAMES})
```

### Suffix Application

After the first name is drawn, a suffix may be stored in the `User.suffix` column:

```math
\text{suffix\_applied} = \begin{cases} \text{True} & \text{if } U(0,1) \leq p_\text{suffix} \\ \text{False} & \text{otherwise} \end{cases}
```

where $p_\text{suffix}$ = `SEED_USER_SUFFIX_PROBABILITY` (default 0.3). If applied, a suffix is drawn uniformly from `["Jr.", "Sr.", "II", "III", "IV"]` and stored in `User.suffix`. The first name itself is left unmodified.

With the default probability, approximately 30% of students will have a non-null `suffix` column.

---

## 6.2 Email Generation

Student emails are derived deterministically from the generated name and school domain:

```
{first_name_part}.{last_name_part}{number}@{school_domain}
```

Where:
- `first_name_part` = first token of the first name, lowercased (handles suffixes like "Jr.")
- `last_name_part` = last token of the last name, lowercased (handles compound surnames like "Dela Cruz")
- `number` = $n \sim \text{Uniform}(1, 99)$

Example: `james.smith42@aurauniversity.edu.ph`

This scheme can produce collisions. The seeder does not check for email uniqueness — the database `UNIQUE` constraint on `users.email` will raise an error if a collision occurs. In practice, with 119 first names × 96 last names × 99 number suffixes = 1,131,264 possible combinations, collisions are extremely rare at the scale the seeder operates at.

---

## 6.3 Student ID Generation

Student IDs follow the format `{year}-{5-digit-number}`:

```
{start_year}-{rng.randint(10000, 99999)}
```

Where `start_year` is the year component of `SEED_START_MMDDYY`.

The seeder maintains a `used_student_ids` set per school and retries until a unique ID is found:

```python
while True:
    sid = f"{start_date[2]}-{rng.randint(10000, 99999)}"
    if sid not in used_student_ids:
        used_student_ids.add(sid)
        break
```

The probability of needing a retry is:

```math
P(\text{collision on attempt } k) = \frac{k-1}{90000}
```

At 2,000 students, the expected number of retries is approximately:

```math
E[\text{retries}] = \sum_{k=1}^{2000} \frac{k-1}{90000} \approx \frac{2000 \times 1999}{2 \times 90000} \approx 22
```

This is negligible.

---

## 6.4 Password Hashing

### Uniform passwords

When `SEED_UNIQUE_PASSWORDS = False`, all students get the password `Student123!`. A single bcrypt hash is computed and reused for all students. This is fast.

### Unique passwords

When `SEED_UNIQUE_PASSWORDS = True`, a unique 12-character password is generated per student:

```python
pw = "".join(rng.choices(string.ascii_letters + string.digits, k=10)) + "1!"
```

The `"1!"` suffix ensures the password meets the minimum complexity requirement (at least one digit, at least one special character).

All passwords are hashed in parallel using `ThreadPoolExecutor`:

```python
def hash_passwords_parallel(passwords, rounds=6, workers=10):
    def _hash(pw):
        return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(_hash, passwords))
```

The bcrypt cost factor is set to `rounds=6` for students (fast, suitable for demo data) and `rounds=12` for the platform admin (production-grade security).

### bcrypt cost comparison

The bcrypt work factor doubles with each increment:

```math
\text{time}(r) \approx 2^{r-6} \times \text{time}(6)
```

| rounds | Relative cost |
|--------|--------------|
| 6 | 1× (baseline) |
| 8 | 4× |
| 10 | 16× |
| 12 | 64× |

At `rounds=6` with 10 parallel workers, hashing 2,000 passwords takes approximately 2–5 seconds depending on hardware. At `rounds=12`, the same operation would take 128–320 seconds — which is why the seeder uses `rounds=6` for bulk student generation.

---

## 6.5 Program Assignment and Enrollment Skew

Students are not distributed uniformly across programs. Before student generation begins, each program in the school's program pool is assigned a random weight:

```math
w_i \sim \text{Uniform}(10, 100), \quad i \in \{1, \ldots, |\text{program\_pool}|\}
```

Students are then assigned via weighted sampling with replacement:

```math
P(\text{student assigned to program } i) = \frac{w_i}{\sum_{j} w_j}
```

This produces realistic enrollment skew. In a school with 5 programs, one program might have weight 95 and another weight 12, resulting in roughly 8× more students in the popular program.

The weights are drawn once per school and reused for all students in that school. This means the enrollment distribution is consistent within a school but varies between schools.

---

## 6.6 Campus Admin

Each school gets exactly one campus admin user:

- Email: `admin@{school_domain}`
- Password: `CampusAdmin123!` (hashed at `rounds=6`)
- Role: `campus_admin`

The campus admin is created with get-or-create semantics — if a user with that email already exists, it is reused.
