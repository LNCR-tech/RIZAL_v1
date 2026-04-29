# Seeder Service

<!--nav-->
[Previous](../README.md) | [Next](docs/01-purpose.md) | [Home](/README.md)

---
<!--/nav-->

The seeder generates deterministic demo data for Aura (schools, users, governance, events, attendance, and sanctions).

## Docs

- [Chapter 1 - Purpose and Design Philosophy](docs/01-purpose.md)
- [Chapter 11 - Running the Seeder](docs/11-running.md)
- [Chapter 12 - Output Files](docs/12-output.md)

## Quick Start

```bash
cd seeder
cp .env.example .env
python seed.py demo
```

## Key Paths

- `seed.py` - entry point
- `modules/` - generation modules
- `docs/` - full technical documentation
- `storage/seeder_outputs/` - generated artifacts
