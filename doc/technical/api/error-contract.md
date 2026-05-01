# Frontend-Backend Error Contract

> **Status:** ACTIVE
> **Last Updated:** 2026-04-18

## Purpose

This page defines the MVP runtime error contract the frontend should use when handling backend failures.

The recommended contract is:

1. use the HTTP status code for the error category
2. use `error_code` for exact frontend behavior
3. use `message` for display text only

## Recommended Response Shape

```json
{
  "error_code": "AUTH_FACE_REQUIRED",
  "message": "Face verification is required for this account."
}
```

The frontend should not make routing or state decisions from raw message text alone.

## MVP Handling Rule

For MVP, the frontend should always:

1. read the HTTP status
2. read the `error_code`
3. trigger the matching UI behavior
4. show `message` only as user-facing feedback

## Authentication

| HTTP Status | Error Code | Meaning | Frontend Action |
|---|---|---|---|
| `400` | `AUTH_INVALID_CREDENTIALS` | Login credentials are wrong | Show login error message |
| `401` | `AUTH_TOKEN_MISSING` | No access token was provided | Redirect to login |
| `401` | `AUTH_TOKEN_EXPIRED` | Session expired | Redirect to login and show session-expired message |
| `403` | `AUTH_INACTIVE_SCHOOL` | User belongs to an inactive school | Block access and show notice |
| `403` | `AUTH_PASSWORD_CHANGE_REQUIRED` | User must change password before continuing | Redirect to change-password page |
| `403` | `AUTH_FACE_REQUIRED` | Privileged login requires face verification | Redirect to face verification flow |
| `403` | `AUTH_FACE_ENROLLMENT_REQUIRED` | Face enrollment is required before access | Redirect to face registration flow |

## Authorization

| HTTP Status | Error Code | Meaning | Frontend Action |
|---|---|---|---|
| `403` | `ACCESS_DENIED` | User does not have permission | Show access denied state |
| `403` | `OUT_OF_SCOPE_ACCESS` | User is outside the allowed governance or school scope | Show restricted-access message |

## Validation And Forms

| HTTP Status | Error Code | Meaning | Frontend Action |
|---|---|---|---|
| `400` | `BAD_REQUEST` | Request body or format is invalid | Show general request error |
| `422` | `VALIDATION_ERROR` | Submitted fields failed validation | Highlight invalid inputs |
| `409` | `DUPLICATE_RECORD` | Record already exists or action already happened | Show duplicate/conflict warning |

## Import

| HTTP Status | Error Code | Meaning | Frontend Action |
|---|---|---|---|
| `400` | `IMPORT_EMPTY_FILE` | Uploaded file has no usable rows | Show file-empty warning |
| `422` | `IMPORT_INVALID_FORMAT` | Import template or column format is invalid | Show template guidance |
| `409` | `IMPORT_CONFLICT_DETECTED` | Import found duplicate or conflicting rows | Show conflict summary |
| `403` | `IMPORT_PREVIEW_REQUIRED` | Import cannot continue until preview approval is completed | Force preview-first flow |

## Attendance And Face Scan

| HTTP Status | Error Code | Meaning | Frontend Action |
|---|---|---|---|
| `404` | `EVENT_NOT_FOUND` | Requested event does not exist | Show event-missing message |
| `403` | `ATTENDANCE_OUT_OF_SCOPE` | User cannot manage that attendance record | Show permission warning |
| `409` | `ATTENDANCE_DUPLICATE` | Attendance already exists | Show already-recorded message |
| `422` | `FACE_NOT_RECOGNIZED` | Face match failed | Ask user to retry scan |
| `422` | `LIVENESS_CHECK_FAILED` | Liveness or anti-spoof check failed | Ask user to rescan |
| `422` | `GEOFENCE_VIOLATION` | User is outside the allowed location | Show location warning |
| `409` | `SIGN_OUT_PENDING` | Sign-out was attempted too early | Show try-again-later message |

## System And Service

| HTTP Status | Error Code | Meaning | Frontend Action |
|---|---|---|---|
| `500` | `INTERNAL_SERVER_ERROR` | Unexpected backend failure | Show generic error fallback |
| `503` | `SERVICE_UNAVAILABLE` | Service is temporarily unavailable | Show retry-later message |
| `503` | `FACE_RUNTIME_NOT_READY` | Face engine is still warming up or unavailable | Show retry-after-warmup message |
| `503` | `EMAIL_SERVICE_UNAVAILABLE` | Email delivery service is unavailable | Show warning and continue only if the flow is non-blocking |

## Frontend Action Groups

To keep frontend logic simple, group handling into these behaviors:

- redirect to login
  - `AUTH_TOKEN_MISSING`
  - `AUTH_TOKEN_EXPIRED`
- redirect to gated auth flow
  - `AUTH_PASSWORD_CHANGE_REQUIRED`
  - `AUTH_FACE_REQUIRED`
  - `AUTH_FACE_ENROLLMENT_REQUIRED`
- show permission or access block
  - `ACCESS_DENIED`
  - `OUT_OF_SCOPE_ACCESS`
  - `AUTH_INACTIVE_SCHOOL`
- show validation feedback
  - `BAD_REQUEST`
  - `VALIDATION_ERROR`
- show conflict warning
  - `DUPLICATE_RECORD`
  - `IMPORT_CONFLICT_DETECTED`
  - `ATTENDANCE_DUPLICATE`
  - `SIGN_OUT_PENDING`
- show retry guidance
  - `FACE_NOT_RECOGNIZED`
  - `LIVENESS_CHECK_FAILED`
  - `FACE_RUNTIME_NOT_READY`
  - `SERVICE_UNAVAILABLE`

## What Not To Do

- Do not make frontend logic depend only on raw response message text.
- Do not treat different `403` cases as the same user flow.
- Do not use Qodana inspection IDs as runtime API error codes.
- Do not create too many custom codes for edge cases during MVP.

## Qodana Relation

Qodana matters for quality control, but it is not part of the runtime frontend-backend contract.

Use Qodana for:

- broken import and reference detection
- wrong function arguments
- async misuse
- dead code detection
- vulnerable dependency detection

Do not use Qodana IDs such as `PyTypeChecker`, `JSUnresolvedReference`, or `VueMissingComponentImportInspection` as frontend runtime error codes.

The frontend should rely on:

- HTTP status
- backend `error_code`
- optional display `message`

## Related Docs

- [overview.md](./overview.md)
- [frontend-integration.md](./frontend-integration.md)
- [request-response.md](./request-response.md)
- [qodana-error-reference.md](../testing/qodana-error-reference.md)
