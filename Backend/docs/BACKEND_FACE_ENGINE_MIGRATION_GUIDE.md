# Backend Face Engine Migration Guide

This guide documents the backend migration from the legacy `face_recognition` / dlib runtime to the current unified InsightFace face-engine design:

- single-face enrollment and attendance: InsightFace + SCRFD + ArcFace
- public multi-face attendance: InsightFace + SCRFD + ArcFace
- admin face MFA: InsightFace + ArcFace with the strict MFA threshold
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
  - used by admin face MFA enrollment and verification
  - fixed to the InsightFace adapter with the stricter MFA threshold

The factory now standardizes all three modes on InsightFace directly. There is no remaining per-mode provider switch in environment configuration.

The adapter entry point lives in `Backend/app/services/face_engine/factory.py`.

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

### Admin face MFA

Routes:

- `GET /api/auth/security/face-status`
- `POST /api/auth/security/face-liveness`
- `POST /api/auth/security/face-reference`
- `POST /api/auth/security/face-verify`

Behavior:

- new MFA references are stored as canonical ArcFace embeddings
- legacy `face_recognition` references are rejected at verify time with `409`
- admins must re-enroll once to migrate their saved face reference
- `GET /api/auth/security/face-status` now reports face-engine readiness separately from anti-spoof readiness so the frontend can distinguish a missing InsightFace runtime from a missing MiniFASNet liveness model
- `GET /api/auth/security/face-status` no longer blocks on the first InsightFace `buffalo_l` download; it can temporarily report `insightface_model_download_pending` or `insightface_warming_up` while the backend prepares the runtime in the background
- repeated `GET /api/auth/security/face-status` calls stay non-blocking while that same background warmup thread is still running
- if a live status probe itself runs too long, the route now fails fast with bounded fallback reasons instead of waiting indefinitely for the slow runtime check to finish
- privileged users who are still on a temporary password can still access the four MFA face routes during onboarding so live face verification can complete before the forced password-change redirect

## Database migration

Migration file:

- `Backend/alembic/versions/c6e1f4a8b9d0_add_student_face_embedding_metadata.py`

What it does:

- adds student embedding metadata columns
- backfills existing enrolled student rows as legacy dlib metadata

## Dependencies

`Backend/requirements.txt` now contains the pinned runtime dependency set used by backend containers.

`Backend/requirements-dev.txt` now contains test tooling layered on top of runtime deps (for local/CI testing only).

Runtime requirements include:

- `insightface`
- `faiss-cpu`
- `onnxruntime`

Removed:

- `deepface`
- `dlib`
- `face-recognition`
- `face_recognition_models`

`faiss-cpu` is present for the future optional vector index helper in `Backend/app/services/face_engine/vector_store.py`. It is not required for the current request path because the main matching logic still falls back to numpy batch cosine search.

Container note:

- `Backend/Dockerfile.prod` now explicitly includes `libgl1` so the OpenCV runtime required by InsightFace can import successfully
- `Backend/Dockerfile.prod` now runs as non-root user `appuser` for tighter runtime isolation
- the backend container now starts without `uvicorn --reload` so long-running login and face-verification requests are not interrupted by live-reload restarts; restart or recreate the backend container manually after backend code changes

## Recommended rollout

1. Apply the Alembic migration.
2. Install the new runtime dependencies.
3. Confirm the MiniFASNet ONNX model exists at the configured path.
4. Re-enroll one student through the registration route and validate the stored metadata.
5. Test single attendance with that student.
6. Test one public kiosk event with multiple mock faces.
7. Re-enroll any student or admin faces that were captured during the earlier DeepFace-plus-InsightFace hybrid period so every stored template is generated by the current InsightFace runtime.
8. Test one privileged account with both `face_verification_pending=true` and `must_change_password=true`; confirm face verification succeeds first and the app redirects to `/change-password` immediately after.
9. On a fresh machine or container, load the admin face-verification page once and confirm it reports InsightFace warmup progress instead of staying on a permanent loading screen while the first model download runs.

Environment note:

- remove any leftover `FACE_PROVIDER_SINGLE` and `FACE_PROVIDER_GROUP` values from local or deployed environments because the backend no longer reads them
- the repo-root `.env.example` contains the current InsightFace-era environment keys and safe placeholder values for new local setups
- Alembic now loads repo-root `.env` first (then falls back to `Backend/.env` when present) so migration commands follow the shared env-file strategy

## Verification commands

Run tests:

```powershell
python -m pip install -r Backend/requirements-dev.txt
python -m pytest -q Backend/app/tests/test_face_recognition_schemas.py Backend/app/tests/test_face_engines.py Backend/app/tests/test_public_attendance.py Backend/app/tests/test_routes_face.py
```

Smoke-check production backend image requirements:

```powershell
docker build -t valid8-backend:latest -f Backend/Dockerfile.prod Backend
docker run --rm valid8-backend:latest python -c "import cv2, insightface; print('ok')"
```

Run compile checks:

```powershell
python -m py_compile Backend/app/core/config.py Backend/app/models/user.py Backend/app/models/platform_features.py Backend/app/services/face_recognition.py Backend/app/services/attendance_face_scan.py Backend/app/services/face_engine/base.py Backend/app/services/face_engine/liveness.py Backend/app/services/face_engine/insightface_adapter.py Backend/app/services/face_engine/factory.py Backend/app/services/face_engine/vector_store.py Backend/app/routers/face_recognition.py Backend/app/routers/public_attendance.py Backend/app/routers/security_center.py
```
