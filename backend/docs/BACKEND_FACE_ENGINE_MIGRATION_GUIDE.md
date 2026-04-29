# Backend Face Engine Migration Guide

<!--nav-->
[Previous](BACKEND_FACE_ATTENDANCE_MODE_POLICY.md) | [Next](BACKEND_RAILWAY_DEPLOYMENT_GUIDE.md) | [Home](/README.md)

---
<!--/nav-->

This guide documents the backend migration from the legacy `face_recognition` / dlib runtime to the current unified InsightFace face-engine design:

- single-face enrollment and attendance: InsightFace + SCRFD + ArcFace
- public multi-face attendance: InsightFace + SCRFD + ArcFace
- privileged face security profile operations: InsightFace + ArcFace with the strict security threshold
- anti-spoofing: MiniFASNetV2 through the checked-in ONNX model path

## Canonical embedding contract

All new face enrollments now use one canonical embedding format:

- provider: `arcface`
- dtype: `float32`
- dimension: `512`
- normalized: `true`

This contract is stored on `student_profiles` through:

- `face_encoding`
- `embedding_provider`
- `embedding_dtype`
- `embedding_dimension`
- `embedding_normalized`

Legacy student rows are marked during migration as:

- provider: `dlib`
- dtype: `float64`
- dimension: `128`
- normalized: `false`

That legacy metadata is intentional. It prevents the backend from silently comparing old dlib embeddings against new ArcFace probe vectors.

## Runtime selection

The backend now routes face flows by mode:

- `single`:
  - used by student face registration
  - used by single-student attendance scans
- `group`:
  - used by `POST /public-attendance/events/{event_id}/multi-face-scan`
- `mfa`:
  - used by privileged face security reference enrollment and verification
  - fixed to the InsightFace adapter with the stricter security threshold

The factory now standardizes all three modes on InsightFace directly. There is no remaining per-mode provider switch in environment configuration.

The adapter entry point lives in `Backend/app/services/face_engine/factory.py`.

## Runtime lifecycle state model

InsightFace runtime state is now tracked explicitly in the shared adapter runtime service (per process / per worker):

- `initializing`
- `ready`
- `failed`

Tracked lifecycle metadata:

- `warmup_started_at`
- `warmup_finished_at`
- `initialized_at`
- `last_error`
- `model_construction_duration_ms`
- `prepare_duration_ms`
- `warmup_duration_ms`
- `init_duration_ms`

Runtime status payload now exposes at least:

- `state`
- `ready`
- `reason`
- `last_error`
- `provider_target` (currently `CPUExecutionProvider`)
- `mode`

Initialization now includes an explicit warm-up inference stage:

1. build `FaceAnalysis(...)`
2. run `prepare(ctx_id=-1, det_size=(640, 640))`
3. run one safe dummy-frame `face_analysis.get(...)` warm-up call
4. mark runtime `ready` only after warm-up succeeds

To reduce startup memory pressure, the adapter now requests only the required InsightFace modules during `FaceAnalysis(...)` construction:

- `detection`
- `recognition`

Compatibility fallback:

- if the installed InsightFace build does not support `allowed_modules`, the adapter falls back to default module loading and logs a warning.

Startup logs now include phase timings (ms):

- model construction
- `prepare(...)`
- warm-up inference
- total initialization

Important behavior change:

- request paths no longer silently start InsightFace warm-up as a side effect
- startup now explicitly requests runtime initialization through the lifecycle API
- face routes return structured `503` runtime-state details when runtime is still `initializing` or has `failed`

## Matching rules

The backend no longer compares embeddings with raw Euclidean distance. It now:

1. deserializes canonical embeddings as `float32`
2. L2-normalizes embeddings before comparison
3. computes cosine distance
4. matches with per-mode thresholds

Default thresholds:

- `FACE_THRESHOLD_SINGLE=0.40`
- `FACE_THRESHOLD_GROUP=0.40`
- `FACE_THRESHOLD_MFA=0.35`

The response payload still exposes `distance`, `confidence`, and `threshold`:

- `distance` is cosine distance, so lower is better
- `confidence` is cosine similarity, so higher is better
- `threshold` is the maximum allowed cosine distance for a match

## Liveness behavior

MiniFASNetV2 anti-spoofing is now centralized in `Backend/app/services/face_engine/liveness.py`.

Relevant config:

- `FACE_THRESHOLD_SINGLE=0.40`
- `FACE_THRESHOLD_GROUP=0.40`
- `FACE_THRESHOLD_MFA=0.35`
- `FACE_EMBEDDING_DIM=512`
- `FACE_EMBEDDING_DTYPE=float32`
- `LIVENESS_THRESHOLD=0.85`
- `ANTI_SPOOF_MODEL_PATH`
- `ANTI_SPOOF_SCALE`
- `ALLOW_LIVENESS_BYPASS_WHEN_MODEL_MISSING`

Deprecated local env names to remove:

- `FACE_MATCH_THRESHOLD`
- `LIVENESS_MIN_SCORE`

Note:

- The backend implements the official Silent-Face-Anti-Spoofing MiniFASNetV2 model family through direct `onnxruntime` inference in `Backend/app/services/face_engine/liveness.py`.
- The repo keeps the checked-in `Backend/models/MiniFASNetV2.onnx` model as the runtime artifact instead of depending on a package literally named `silent-face-anti-spoofing`.
- `ANTI_SPOOF_SCALE` now adds surrounding context padding before liveness inference so preprocessing stays closer to the upstream Silent-Face patch-style flow.
- MiniFASNet now crops from the original detector frame plus the detected bbox and scale, instead of scoring a face-only crop with synthetic edge padding. This matches the upstream Silent-Face patch flow more closely and fixes common false spoof detections on live webcam faces.

## Route behavior changes

### Student registration

Routes:

- `POST /api/face/register`
- `POST /api/face/register-upload`

Behavior:

- registration now stores canonical ArcFace metadata on the student profile
- registration still requires one face and liveness success
- while InsightFace is still warming up on a cold start, registration can temporarily return `503` with a warm-up message; retry after warm-up completes

### Single attendance

Route:

- `POST /api/face/face-scan-with-recognition`

Behavior:

- matching now uses canonical ArcFace embeddings plus cosine distance
- self-scan students with legacy dlib face data receive `409` and must re-register
- event scope, geolocation, sign-in, and sign-out rules are unchanged

### Public attendance kiosk

Route:

- `POST /public-attendance/events/{event_id}/multi-face-scan`

Behavior:

- public scans now run through the group-mode engine
- candidate matching still respects event, department, and program scope
- duplicate, cooldown, no-match, and liveness outcomes keep the same response shape

### Privileged face security profile

Routes:

- `GET /api/auth/security/face-status`
- `POST /api/auth/security/face-liveness`
- `POST /api/auth/security/face-reference`
- `POST /api/auth/security/face-verify`

Behavior:

- new privileged face references are stored as canonical ArcFace embeddings
- legacy `face_recognition` references are rejected at verify time with `409`
- privileged users must re-enroll once to migrate their saved face reference
- `GET /api/auth/security/face-status` now reports face-engine readiness separately from anti-spoof readiness so the frontend can distinguish a missing InsightFace runtime from a missing MiniFASNet liveness model
- `GET /api/auth/security/face-status` now reports `face_verification_required` from the stored privileged security setting (`user_security_settings.mfa_enabled`)
- `GET /api/auth/security/face-status` now also returns structured runtime lifecycle fields:
  - `face_runtime_state`
  - `face_runtime_last_error`
  - `face_runtime_provider_target`
  - `face_runtime_mode`
  - `face_runtime_initialized_at`
  - `face_runtime_warmup_started_at`
  - `face_runtime_warmup_finished_at`
  - `face_runtime_model_construction_duration_ms`
  - `face_runtime_prepare_duration_ms`
  - `face_runtime_warmup_duration_ms`
  - `face_runtime_init_duration_ms`
- if startup warm-up is still running, face-status reports `state=initializing` with warm-up reasons instead of kicking off hidden request-time initialization
- if a live status probe itself runs too long, the route now fails fast with bounded fallback reasons instead of waiting indefinitely for the slow runtime check to finish
- privileged login is now gated behind face verification again when the account has `mfa_enabled=true`
- privileged password login first returns a face-pending token, and `POST /api/auth/security/face-verify` upgrades that pending token into a full-access session after a successful live face match

## Database migration

Migration file:

- `Backend/alembic/versions/c6e1f4a8b9d0_add_student_face_embedding_metadata.py`

What it does:

- adds student embedding metadata columns
- backfills existing enrolled student rows as legacy dlib metadata

## Dependencies

`Backend/requirements.txt` now contains the pinned runtime dependency set used by backend containers.



Runtime requirements include:

- `insightface`
- `faiss-cpu`
- `onnxruntime`

Removed:

- `deepface`
- `dlib`
- `face-recognition`
- `face_recognition_models`

`faiss-cpu` is still present for the optional in-process vector helper in `Backend/app/services/face_engine/vector_store.py`, but the preferred scalable multi-school attendance search path is now PostgreSQL `pgvector` because it keeps school/event filtering and persistence in the same database.

## Scalable attendance face search

Large multi-school deployments should use the PostgreSQL `pgvector` path added for attendance matching. The backend now supports an optional `student_face_embeddings` table that mirrors active registered student embeddings from `student_profiles`.

When the table and extension exist, and the school's vector rows cover all current canonical registered faces, these paths use vector nearest-neighbor search before falling back to ORM candidate loading:

- `POST /api/face/verify`
- `POST /public-attendance/events/{event_id}/multi-face-scan`

The public kiosk flow searches in this order:

1. event-scoped vector rows for eligible department/program/campus-wide students
2. school-wide vector rows only when an event has scope restrictions and the backend needs to distinguish a known but out-of-scope student from an unknown face
3. existing ORM plus numpy matching when the vector index is unavailable or incomplete

New student face registrations call `sync_student_face_embedding_index()` after the profile row is saved. For existing databases, apply the migration and run:

```bash
cd Backend
python scripts/backfill_student_face_embeddings.py
```

The migration is PostgreSQL-only and creates:

- `student_face_embeddings`
- a school active-row index
- a school/department/program active-row index
- a cosine vector index on `embedding`, preferring HNSW and falling back to IVFFlat on older pgvector installs

If `pgvector` is not installed on the PostgreSQL server, install it before running `alembic upgrade head`.

Container note:

- `Backend/Dockerfile.prod` now explicitly includes `libgl1` so the OpenCV runtime required by InsightFace can import successfully
- `Backend/Dockerfile.prod` now runs as non-root user `appuser` for tighter runtime isolation
- the backend container now starts without `uvicorn --reload` so long-running login and face-verification requests are not interrupted by live-reload restarts; restart or recreate the backend container manually after backend code changes
- app startup now explicitly requests non-blocking InsightFace initialization via the face-runtime lifecycle API
- face requests now consume runtime state and return structured runtime errors instead of silently triggering warm-up
- Docker compose stacks should mount a persistent InsightFace cache volume:
  - local backend: `/root/.insightface`
  - production backend (`appuser`): `/home/appuser/.insightface`
  - this avoids re-downloading `buffalo_l` on every container recreate and reduces first-login face-registration 503 errors

## Recommended rollout

1. Apply the Alembic migration.
2. Install the new runtime dependencies.
3. Confirm the MiniFASNet ONNX model exists at the configured path.
4. Re-enroll one student through the registration route and validate the stored metadata.
5. Test single attendance with that student.
6. Test one public kiosk event with multiple mock faces.
7. Re-enroll any student or admin faces that were captured during the earlier DeepFace-plus-InsightFace hybrid period so every stored template is generated by the current InsightFace runtime.
8. Test one privileged account login and confirm the API returns a face-pending token (`face_verification_required=true`, `session_id=null`) until `POST /api/auth/security/face-verify` succeeds.
9. On a fresh machine or container, call:
   - `GET /health`
   - `GET /health/readiness`
   and confirm DB and face-runtime readiness are both clearly reported.
10. On a fresh machine or container, load the admin face-verification page once and confirm it reports InsightFace runtime state/reason progress instead of staying on a permanent loading screen during first warm-up.

Environment note:

- remove any leftover `FACE_PROVIDER_SINGLE` and `FACE_PROVIDER_GROUP` values from local or deployed environments because the backend no longer reads them
- the repo-root `.env.example` contains the current InsightFace-era environment keys and safe placeholder values for new local setups
- Alembic now loads repo-root `.env` first (then falls back to `Backend/.env` when present) so migration commands follow the shared env-file strategy

## Verification commands

Smoke-check production backend image requirements:

```powershell
docker build -t aura-backend:latest -f Backend/Dockerfile.prod Backend
docker run --rm aura-backend:latest python -c "import cv2, insightface; print('ok')"
```

Run compile checks:

```powershell
python -m py_compile Backend/app/core/config.py Backend/app/models/user.py Backend/app/models/platform_features.py Backend/app/services/face_recognition.py Backend/app/services/attendance_face_scan.py Backend/app/services/face_engine/base.py Backend/app/services/face_engine/liveness.py Backend/app/services/face_engine/insightface_adapter.py Backend/app/services/face_engine/factory.py Backend/app/services/face_engine/vector_store.py Backend/app/routers/face_recognition.py Backend/app/routers/public_attendance.py Backend/app/routers/security_center.py
```


