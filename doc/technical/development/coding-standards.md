# Coding Standards

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Scope:** Backend, frontend, docs, and collaboration workflow.

---

## Purpose

This document defines enforceable coding and collaboration standards to keep the codebase consistent, readable, and reviewable.

## Risk Controls

| Risk | Standard control |
|---|---|
| Inconsistent coding practices | Shared naming, structure, and API-contract rules per stack layer. |
| Outdated or unenforced standards | Definition-of-done checklist and PR enforcement requirements. |
| Poor collaboration quality | Branch, commit, and documentation update requirements. |

## Global Rules

- Use English for identifiers, comments, and documentation.
- Do not commit secrets or credentials.
- Keep changes scoped: avoid unrelated refactors in feature PRs.
- Prefer explicit, typed contracts over implicit payload shapes.

## Backend Standards (Python/FastAPI/SQLAlchemy)

### Naming and Structure

| Element | Rule | Example |
|---|---|---|
| Files | `snake_case.py` | `governance_hierarchy.py` |
| Functions and variables | `snake_case` | `get_current_governance_route_user` |
| Classes | `PascalCase` | `GovernanceMemberPermission` |
| Constants | `UPPER_SNAKE_CASE` | `FORGOT_PASSWORD_GENERIC_MESSAGE` |

### API and Router Rules

- Keep validation in schemas and service layers, not ad hoc inline logic.
- Use explicit HTTP status codes and meaningful error details.
- Keep role and scope checks in dependency functions and shared security helpers.
- When endpoint behavior changes, update API docs in `docs/technical/api/`.

### Database and Migrations

- Never edit production schema manually; use Alembic migrations.
- Keep migration and model changes in the same branch.
- Maintain tenant scoping (`school_id`) where applicable.
- Update database docs when schema or relationship behavior changes.

### Runtime and Worker Rules

- Active worker runtime path is `Backend/app/workers/`.
- `Backend/app/worker/` is compatibility only; do not build new logic there.
- Keep background tasks idempotent where possible and log failure context.

## Frontend Standards (React/TypeScript)

### Naming and File Conventions

| Element | Rule | Example |
|---|---|---|
| Components/pages | `PascalCase.tsx` | `StudentFaceEnrollment.tsx` |
| Hooks | `camelCase` with `use` prefix | `useSomething.ts` |
| API modules | `camelCase` + `Api.ts` | `authApi.ts`, `eventsApi.ts` |
| Utility modules | `camelCase.ts` | `apiUrl.ts` |

### UI and State Rules

- Keep route access control in `ProtectedRoute` flow, not duplicated in each page.
- Keep data fetching in `src/api/` modules rather than scattered request code.
- Use shared context (`UserContext`) for cross-page user state.
- Preserve route compatibility aliases only when needed for migration/backward support.

## Documentation Standards

- Code changes that affect behavior must update related docs in the same PR.
- Keep technical docs aligned with current code, not planned or legacy structure.
- Use source-of-truth references (real file paths) in docs.
- Remove or mark obsolete guidance when behavior is retired.

Required rule from `AGENTS.md`:

- Any backend code change under `Backend/` must update `Backend/docs/BACKEND_CHANGELOG.md` and affected backend feature documentation.

## Git and PR Standards

### Commit Messages

Use Conventional Commits:

```text
<type>(<scope>): <short description>
```

Examples:

- `feat(governance): add unit permission audit fields`
- `fix(attendance): correct face-scan timeout handling`
- `docs(development): align setup guide with compose flow`

### Pull Request Checklist

1. Code follows naming and structure standards.
2. Tests or smoke validation were run for changed behavior.
3. Migrations included for schema changes.
4. Docs updated for API, DB, architecture, deployment, or development behavior changes.
5. Changelog entries updated according to SSOT rule.

## Definition of Done

A task is done only when:

- implementation is complete
- review feedback is addressed
- affected documentation is updated
- migration impact is handled (if any)
- feature is reproducible by another developer following docs
