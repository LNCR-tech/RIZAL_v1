# CI/CD Pipeline

> **Status:** Active
> **Last Updated:** 2026-04-27
>
> **Source of truth:**
> - `.github/workflows/ci.yml`
> - `.github/workflows/deploy-ec2.yml`

---

## Purpose

This page tracks the actual committed CI/CD behavior after the April 26 to April 27 pipeline updates.

It replaces the old manual-only assumption and documents:

- workflow files now present in-repo
- trigger branches and deployment guardrails
- validate/build/test/deploy job sequencing

See also:
- [deployment-guide.md](./deployment-guide.md)
- [environment-variables.md](./environment-variables.md)

## Workflow Inventory

| Workflow file | Primary role |
|---|---|
| `.github/workflows/ci.yml` | Main CI with compose validation, backend/frontend checks, docker build, and branch-gated deploy job. |
| `.github/workflows/deploy-ec2.yml` | Integration-branch backend-focused deploy workflow with explicit migration-first steps. |

## Trigger Matrix

### `ci.yml`

- `push` branches:
  - `main`
  - `master`
  - `integrate/pilot-merge`
  - `Pre-Production-v1`
  - `aura_ci_cd`
- `pull_request`: all branches

Deployment guard in this workflow:

- Deploy job runs only when:
  - event is `push`
  - branch is `main` or `aura_ci_cd`

### `deploy-ec2.yml`

- `push` to `integrate/pilot-merge`
- `pull_request` to `integrate/pilot-merge`
- `workflow_dispatch`

Deployment guard in this workflow:

- Deploy job runs only when `github.ref == refs/heads/integrate/pilot-merge`.

## Job Flow

### `ci.yml`

1. `compose-config`
2. `backend-checks`
3. `frontend-checks`
4. `docker-build` (depends on 1 to 3)
5. `deploy` (depends on 4 and branch guard)

### `deploy-ec2.yml`

1. `validate-compose`
2. `backend-checks`
3. `docker-build` (depends on 1 and 2)
4. `deploy` (depends on 3 and integration-branch guard)

## Implemented Controls

- Compose validation for both local and production compose definitions.
- Merge-conflict marker scan before build.
- Backend compile/test checks and frontend build checks.
- Docker production build test before deploy stage.
- SSH-based remote deployment with forced branch sync and deterministic compose execution.
- Explicit migration-first deploy step in integration deployment workflow.

## Secrets and Environment Dependencies

### `ci.yml` deploy job uses:

- `AWS_HOST`
- `AWS_USER`
- `AWS_SSH_PRIVATE_KEY`
- `AWS_PROJECT_PATH`

### `deploy-ec2.yml` deploy job uses:

- `SERVER_HOST`
- `SERVER_USER`
- `SERVER_SSH_KEY`
- `SERVER_PORT`
- `SERVER_APP_DIR`

Both workflows rely on a generated `.env` in CI for compose validation/build stages.

## Deploy Behavior Notes

- Integration deploy workflow explicitly runs migration service before starting backend/db services.
- Main CI deploy workflow performs full compose rebuild/restart and health polling.
- Deployment scripts and workflows now expect the assistant service under `assistant/`.

## Operational Risks Still Present

- Auto-deploy in `ci.yml` is intentionally limited but still active for production branches; verify branch protection rules match release policy.
- Integration and production deploy logic live in separate workflow files; keep them synchronized when compose service names or migration strategy changes.
- Any future schema cutover must include migration idempotency checks and matching deploy workflow updates in the same change set.

## Documentation Rules

- Update this page whenever workflow files, triggers, deploy conditions, or required secrets change.
- Keep branch names and guard conditions exact.
- Do not claim stages that are not present in committed workflows.
