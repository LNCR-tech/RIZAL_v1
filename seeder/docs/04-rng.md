# Chapter 4 — Deterministic Randomness and the RNG Model

[<- Back to index](./README.md)

---

## 4.1 The Core Principle

The seeder is deterministic. Every random decision — school selection, student names, program weights, event dates, attendance outcomes, sanction resolution — flows through a single `random.Random` instance:

```python
rng = random.Random(cfg.SEED_RANDOMIZER_KEY)
```

This instance is created once in `seed.py` and passed through to every function that needs randomness. No other source of randomness is used anywhere in the generation pipeline.


The consequence is total reproducibility:

```math
	text{output} = f(\text{SEED\_RANDOMIZER\_KEY},\ \text{config})
```

Given the same key and the same configuration, the seeder produces byte-for-byte identical data on every run, on any machine, regardless of Python version (within the same major version, as `random.Random` is deterministic within a version).

---

## 4.2 Why a Single RNG Instance

Using a single RNG instance rather than multiple independent ones is a deliberate design choice. It means the entire dataset is a single deterministic trajectory through the random number space. Changing any parameter — even one that seems unrelated — shifts the trajectory and produces a completely different dataset.

This is the intended behavior. If you want a different dataset, change `SEED_RANDOMIZER_KEY`. If you want the same dataset, keep it the same.

The alternative — multiple independent RNG instances per subsystem — would allow partial reproducibility (e.g., "same students, different events") but would make the overall dataset harder to reason about and harder to reproduce exactly.

---

## 4.3 Uniform Sampling


The most common operation in the seeder is uniform sampling from a list. Python's `random.Random.choice(seq)` draws uniformly:

```math
P(X = x_i) = \frac{1}{n}, \quad i \in \{1, \ldots, n\}
```

where math`n` is the length of the sequence. This is used for:

- Picking a first name, last name, middle name from the name pools
- Picking an event theme, location, event type
- Picking an announcement template
- Picking a compliance note

---

## 4.4 Uniform Integer Sampling


`rng.randint(a, b)` draws uniformly from the closed interval math`[a, b]`:

```math
P(X = k) = \frac{1}{b - a + 1}, \quad k \in \{a, a+1, \ldots, b\}
```

Used for:

- Number of colleges per school: math`k \sim \text{Uniform}(\text{min\_colleges},\ \text{max\_colleges})`
- Number of students per school: math`n \sim \text{Uniform}(\text{min\_students},\ \text{max\_students})`
- Number of events per school: math`e \sim \text{Uniform}(\text{min\_events},\ \text{max\_events})`
- Event duration in hours: math`d \sim \text{Uniform}(1, 4)`
- Student year level: math`y \sim \text{Uniform}(1, 4)`
- Student ID suffix: math`s \sim \text{Uniform}(10000, 99999)`
- Email number suffix: math`n \sim \text{Uniform}(1, 99)`
- Number of SSG officers: math`k \sim \text{Uniform}(3, 5)`
- Number of SG officers per unit: math`k \sim \text{Uniform}(1, 3)`
- Number of ORG officers per unit: math`k \sim \text{Uniform}(1, 2)`
- Number of ORG units per SG: math`k \sim \text{Uniform}(0, 2)`
- Number of SSG announcements: math`k \sim \text{Uniform}(2, 4)`
- Permission count per member: math`k \sim \text{Uniform}(1, |\text{permission\_set}|)`
- Program weight per program: math`w \sim \text{Uniform}(10, 100)`

---

## 4.5 Uniform Continuous Sampling


`rng.uniform(a, b)` draws from the continuous uniform distribution:

```math
X \sim \text{Uniform}(a, b), \quad f(x) = \frac{1}{b-a}, \quad x \in [a, b]
```

Used for:

- Chaos engine cancellation base probability: math`p_c \sim \text{Uniform}(0.02, 0.07)`
- Chaos engine emergency cutoff probability: math`p_e \sim \text{Uniform}(0.10, 0.25)`
- Attendance gate probability for ongoing events: math`p_g \sim \text{Uniform}(0.20, 0.70)`
- Attendance gate probability for emergency-cancelled events: math`p_g \sim \text{Uniform}(0.01, 0.15)`

---

## 4.6 Bernoulli Trials


`rng.random()` draws from math`\text{Uniform}(0, 1)`. Comparing it against a threshold math`p` gives a Bernoulli trial:

```math
X \sim \text{Bernoulli}(p): \quad P(X = 1) = p, \quad P(X = 0) = 1 - p
```

Used for:

- Suffix application: math`X \sim \text{Bernoulli}(\text{SEED\_USER\_SUFFIX\_PROBABILITY})`
- SG announcement generation: math`X \sim \text{Bernoulli}(0.70)` (fires when `rng.random() > 0.3`)
- Sanction delegation: math`X \sim \text{Bernoulli}(0.50)` (fires when `rng.random() > 0.5`)
- Event cancellation (past events): math`X \sim \text{Bernoulli}(p_c)`
- Emergency cancellation (given cancellation): math`X \sim \text{Bernoulli}(p_e)`
- Active event emergency cancellation: math`X \sim \text{Bernoulli}(0.02)`
- Future event pre-emptive cancellation: math`X \sim \text{Bernoulli}(0.03)`
- Student absence: math`X \sim \text{Bernoulli}(0.25)`
- Sanction compliance resolution: math`X \sim \text{Bernoulli}(0.30)`
- Student note unit assignment (SSG vs SG): math`X \sim \text{Bernoulli}(0.50)`

---

## 4.7 Weighted Sampling


`rng.choices(population, weights, k)` samples with replacement using a categorical distribution:

```math
P(X = x_i) = \frac{w_i}{\sum_{j=1}^{n} w_j}
```

Used for:

- **Program assignment for students** — each program gets a random weight math`w_i \sim \text{Uniform}(10, 100)`, then students are assigned via weighted sampling. This produces realistic enrollment skew where some programs are more popular than others.

- **Event scope assignment** — fixed weights `{"school": 15, "department": 25, "program": 60}` give:

```math
P(\text{program-scoped}) = \frac{60}{100} = 0.60, \quad P(\text{department-scoped}) = 0.25, \quad P(\text{school-wide}) = 0.15
```

- **Attendance status** — for present students, `rng.choices(["present", "late"], weights=[80, 20])` gives:

```math
P(\text{present}) = 0.80, \quad P(\text{late}) = 0.20
```

---

## 4.8 Sampling Without Replacement


`rng.sample(population, k)` draws math`k` items without replacement. Used for:

- Selecting school names (prevents duplicate schools)
- Selecting SSG officers from the leader pool
- Selecting announcement templates
- Selecting student note tags
- Selecting permission subsets for governance members

---

## 4.9 The Chaos Engine — Per-Run Variance

The chaos engine introduces a layer of variance that is consistent within a single run but varies between runs with different `SEED_RANDOMIZER_KEY` values.

At the start of `run_demo()`, two probabilities are rolled once for the entire run:

```math
p_c \sim \text{Uniform}(0.02, 0.07) \quad \text{(cancellation base probability)}
```

```math
p_e \sim \text{Uniform}(0.10, 0.25) \quad \text{(emergency cutoff probability)}
```

These govern event status and attendance gate probabilities across the entire dataset. Every seeded universe has a different "climate" — some universes have more cancellations, some have more emergency cutoffs. This is what makes the dataset feel like a real school system rather than a synthetic one.

See [Chapter 8](./08-events.md) for the full event status model.
