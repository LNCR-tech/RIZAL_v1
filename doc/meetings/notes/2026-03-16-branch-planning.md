# Meeting Notes — 2026-03-16: STUDENT-HIERARCHY Branch Planning

> **Date:** 2026-03-16
> **Attendees:** Development Team
> **Type:** Sprint Planning / Architecture Review

---

## Agenda

1. Review of FACE-AUTOMATION-TEST branch output
2. Plan governance hierarchy implementation
3. Campus Admin role renaming
4. ERD versioning strategy

## Key Decisions

- **Governance hierarchy** (SSG → SG → ORG) to be implemented as `governance_units` with `parent_unit_id` self-reference.
- **Campus Admin** officially replaces "School IT" in all routes and UI labels. Legacy `/school_it_*` routes will redirect.
- **ERD versioning:** `ERDv1.md` (legacy baseline) and `ERDv2.md` (current live schema) to be maintained under `docs/technical/ERD/`.
- **`user_face_profiles`** to be separated from `student_profiles` to keep face data isolated.
- **Production Docker path** to be added: `Dockerfile.prod` + `nginx.prod.conf`.

## Action Items

| Item | Owner | Due |
|---|---|---|
| Implement governance_units + governance_members models | Backend Dev | 2026-03-17 |
| Implement governance_hierarchy router + service | Backend Dev | 2026-03-18 |
| Update frontend to Campus Admin naming | Frontend Dev | 2026-03-18 |
| Write ERDv2.md | Documentation Specialist | 2026-03-18 |
| Add production Docker files | DevOps | 2026-03-17 |
