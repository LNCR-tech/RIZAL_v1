# Branching Strategy

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Source of truth:** Local git branch state and `docs/changelog/branch-updates.md`.

---

## Purpose

This document defines how the team creates branches, collaborates through pull requests, and promotes changes to stable releases.

## Strategy Summary

VALID8 uses an integration-branch workflow with short-lived feature branches.

- `main`: release-ready branch
- `Aura/Public-Face-Attendance`: active integration branch in current repo state
- Feature branches: created from integration branch, merged back through PR

Historical branch context remains in [branch-updates.md](../changelog/branch-updates.md).

## Branch Types

| Branch type | Purpose | Pattern |
|---|---|---|
| Release branch | Stable deployment target | `main` |
| Integration branch | Ongoing team integration | `Aura/Public-Face-Attendance` |
| Feature branch | New feature work | `feature/<area>-<short-topic>` |
| Fix branch | Bug fixes | `fix/<area>-<short-topic>` |
| Docs branch | Documentation-only updates | `docs/<topic>` |
| Chore branch | Tooling or maintenance | `chore/<topic>` |
| Hotfix branch | Critical production fix | `hotfix/<topic>` |

## Workflow

```text
1. Pull latest integration branch
2. Create a short-lived branch from integration branch
3. Commit in small, reviewable chunks
4. Open PR to integration branch
5. Pass review and quality gates
6. Merge integration branch to main on release milestone
```

## Merge Rules

- Do not commit directly to `main`.
- Use pull requests for integration branch merges.
- Keep PR scope focused to one feature/fix area.
- Include migration files for schema changes.
- Include docs updates in the same PR for behavior changes.

## Changelog and Documentation Rules

- Follow changelog SSOT rule:
  - raw update first in [branch-updates.md](../changelog/branch-updates.md)
  - filtered final summary in backend or frontend changelog docs
- For backend changes, also update `Backend/docs/BACKEND_CHANGELOG.md` as required by `AGENTS.md`.

## Quality Gates Before Merge

1. Build or startup checks pass.
2. Critical tests or smoke checks pass.
3. Migration path is valid for DB changes.
4. Docs impacted by the change are updated.

## Branch Hygiene

- Rebase or merge integration branch regularly to reduce drift.
- Delete merged feature/fix branches.
- Avoid long-lived branches with mixed unrelated work.
- Use branch names that reflect domain and intent.

## Update Rule

If integration branch naming or release workflow changes, update this file and [branch-updates.md](../changelog/branch-updates.md) in the same change set.
