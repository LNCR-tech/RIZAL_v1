---
sidebar_position: 2
title: Database
---

# Database Schema

**Restricted**: Technical documentation

## Overview

Aura uses PostgreSQL with pgvector support for face embeddings. The database stores users, schools, governance structure, events, attendance records, sanctions, notifications, and supporting audit data.

## Core tables

### Users

- `id` - Primary key.
- `username` - Unique login identifier, usually an email.
- `role` - User role such as `student`, `ssg`, `sg`, `org`, `admin`, `campus_admin`, or `school_it`.
- `school_id` - Foreign key to the assigned school.
- `face_embedding` - Vector used for face recognition matching when enrolled.

### Events

- `id` - Primary key.
- `name` - Event name.
- `start_time` - Event start timestamp.
- `end_time` - Event end timestamp.
- `location` - Human-readable event location.
- `geofence` - Geographic boundary used to validate check-in location.

### Attendance

- `id` - Primary key.
- `user_id` - Foreign key to users.
- `event_id` - Foreign key to events.
- `check_in_time` - Timestamp for the recorded attendance event.
- `check_in_method` - Current methods are `face_scan` and `manual`.
- `status` - Attendance result such as present, late, absent, or excused.

## Relationship summary

```text
Schools
  -> Users
     -> Attendance
        -> Events
```

## Migrations

Run migrations with Alembic from the backend workspace:

```bash
alembic upgrade head
```

## Seeding

For demo data seeding, use the seeder service documentation in the main project repository. Keep seeder-specific files only on the pilot branch.
