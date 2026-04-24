# Chapter 8 — Event Generation and the Chaos Engine

[<- Back to index](./README.md)

---

## 8.1 Event Count

The number of events per school is drawn uniformly:

$$
n_e \sim \text{Uniform}(\text{min\_events},\ \text{max\_events})
$$

---

## 8.2 Event Date Generation

Each event's start datetime is drawn uniformly from the configured temporal window using `get_random_date_in_range()`.

The algorithm converts the window to a total number of seconds and draws a uniform random offset:

$$
\Delta t = t_\text{end} - t_\text{start} \quad \text{(in seconds)}
$$

$$
t_\text{event} = t_\text{start} + \text{Uniform}(0,\ \Delta t)
$$

In code:

```python
delta_seconds = int((end_dt - start_dt).total_seconds())
random_second = rng.randint(0, delta_seconds)
return start_dt + timedelta(seconds=random_second)
```

This produces a uniform distribution of events across the entire date range. With a 3-year window (2024–2026) and 100 events, events are spaced approximately 11 days apart on average, but with high variance.

Event duration is drawn uniformly:

$$
d \sim \text{Uniform}(1, 4) \quad \text{hours}
$$

So the end datetime is:

$$
t_\text{end} = t_\text{event} + d \times 3600 \text{ seconds}
$$

---

## 8.3 The Chaos Engine — Event Status Model

The chaos engine determines the status of each event based on its temporal relationship to the current wall-clock time $t_\text{now}$.

### Per-Run Chaos Parameters

At the start of `run_demo()`, two parameters are rolled once for the entire run:

$$
p_c \sim \text{Uniform}(0.02, 0.07) \quad \text{(base cancellation probability)}
$$

$$
p_e \sim \text{Uniform}(0.10, 0.25) \quad \text{(emergency cutoff probability, given cancellation)}
$$

These are fixed for the entire run. Every school in the same run shares the same chaos parameters, giving the dataset a consistent "climate."

### Status Assignment

For each event, status is assigned based on three temporal cases:

**Case 1: Past event** ($t_\text{end} < t_\text{now}$)

$$
\text{status} = \begin{cases}
\text{CANCELLED} & \text{with probability } p_c \\
\text{COMPLETED} & \text{with probability } 1 - p_c
\end{cases}
$$

If cancelled, a second trial determines whether it was an emergency cancellation (mid-event):

$$
\text{is\_emergency} = \begin{cases}
\text{True} & \text{with probability } p_e \\
\text{False} & \text{with probability } 1 - p_e
\end{cases}
$$

**Case 2: Active event** ($t_\text{start} \leq t_\text{now} \leq t_\text{end}$)

$$
\text{status} = \begin{cases}
\text{CANCELLED (emergency)} & \text{with probability } 0.02 \\
\text{ONGOING} & \text{with probability } 0.98
\end{cases}
$$

**Case 3: Future event** ($t_\text{start} > t_\text{now}$)

$$
\text{status} = \begin{cases}
\text{CANCELLED (pre-emptive)} & \text{with probability } 0.03 \\
\text{UPCOMING} & \text{with probability } 0.97
\end{cases}
$$

### Expected Status Distribution

With a 3-year window centered around the present and default chaos parameters ($p_c \approx 0.045$, $p_e \approx 0.175$):

Assuming roughly 60% of events are in the past, 5% are active, and 35% are future:

$$
E[\text{COMPLETED}] \approx 0.60 \times (1 - 0.045) \approx 57.3\%
$$

$$
E[\text{CANCELLED}] \approx 0.60 \times 0.045 + 0.05 \times 0.02 + 0.35 \times 0.03 \approx 3.9\%
$$

$$
E[\text{ONGOING}] \approx 0.05 \times 0.98 \approx 4.9\%
$$

$$
E[\text{UPCOMING}] \approx 0.35 \times 0.97 \approx 33.9\%
$$

These proportions shift as the wall-clock time moves relative to the seeded date window.

---

## 8.4 Event Scope

Each event is assigned a scope via weighted categorical sampling:

$$
P(\text{program-scoped}) = 0.60, \quad P(\text{department-scoped}) = 0.25, \quad P(\text{school-wide}) = 0.15
$$

- Program-scoped: one program is randomly selected from the school's program pool and linked via `event_program_association`
- Department-scoped: one department is randomly selected and linked via `event_department_association`
- School-wide: no association records are created

---

## 8.5 Event Attributes

Each event also gets stochastic grace period settings:

$$
\text{early\_check\_in\_minutes} \sim \text{Uniform}(15, 45)
$$

$$
\text{late\_threshold\_minutes} \sim \text{Uniform}(5, 20)
$$

These diversify the analytics data — different events have different windows for what counts as "on time."

---

## 8.6 Event Type

Each event is assigned a type by drawing uniformly from `EVENT_TYPES` in `data.py`:

```
["Regular Event", "Assembly", "Seminar", "Workshop", "Conference", "Meeting"]
```

These match the global `EventType` records seeded by `bootstrap.py`. The seeder resolves the name to an `event_type_id` FK via `resolve_event_type_id()`, which checks global types first (where `school_id IS NULL`) before falling back to school-scoped types.

---

## 8.7 Sanction Configuration

Every event gets a sanction config with two items:

| Item code | Item name | Description |
|-----------|-----------|-------------|
| `LETTER` | Apology Letter | Handwritten apology letter |
| `FINE` | Community Fine | 50 PHP community tax |

Additionally, 50% of events get a sanction delegation to a random SG unit:

$$
X \sim \text{Bernoulli}(0.50)
$$

If it fires, a `SanctionDelegation` record is created linking the event's sanction config to a randomly selected SG unit with `scope_type = UNIT`.
