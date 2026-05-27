# Sync Face Recognition Spoofing Code from aura_ci_cd to main

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the face-recognition spoofing improvements from `origin/aura_ci_cd` into `main` — logging, datetime serialization fix, user-friendly 503 error, and the debug `/face/runtime-status` endpoint — without touching any unrelated code.

**Architecture:** Three files change. `face_recognition.py` (service) gains structured logging inside `ensure_face_runtime_ready` and `extract_encoding_from_bytes`. `face_recognition.py` (router) gains logging throughout the attendance scan flow, a `_serialize_error_detail` datetime-safety helper, better 503 error wrapping, and a new debug endpoint. `Backend Documentation.md` gains the new endpoint entry.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Python `logging` stdlib.

---

## Scope & Isolation

These changes are **additive** (logging + new endpoint) plus a **bug fix** (`_serialize_error_detail` prevents datetime serialisation crashes in HTTP error bodies).  
No business logic is altered. No other files are touched.

---

## Task 1: Add logging to `backend/app/services/face_recognition.py`

**Files:**
- Modify: `backend/app/services/face_recognition.py`

The diff adds `import logging`, a module-level logger, and log lines inside two methods.

### Step 1.1 — Add `import logging`

- [ ] In `backend/app/services/face_recognition.py`, insert `import logging` after `import io`:

```python
import base64
import hashlib
import io
import logging          # ← add this line
from dataclasses import dataclass
```

### Step 1.2 — Add module-level logger

- [ ] After the last import line (line 19, `from app.services.face_engine import FaceCrop, LivenessChecker, get_engine`), add:

```python
logger = logging.getLogger(__name__)
```

So the block becomes:

```python
from app.core.config import get_settings
from app.services.face_engine import FaceCrop, LivenessChecker, get_engine

logger = logging.getLogger(__name__)
```

### Step 1.3 — Log inside `ensure_face_runtime_ready`

- [ ] Find the `ensure_face_runtime_ready` method (currently ~line 223). Replace the entire method body with the logged version:

**Before:**
```python
    def ensure_face_runtime_ready(
        self,
        *,
        mode: str = "single",
        context: str | None = None,
    ) -> dict[str, object]:
        runtime_status = self.face_runtime_status(mode)
        if runtime_status["ready"]:
            return runtime_status

        reason = str(runtime_status.get("reason") or "insightface_warming_up")
        state = str(runtime_status.get("state") or "initializing")
        if reason == "unsupported_mode":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "unsupported_face_mode",
                    "message": f"Unsupported face mode: {mode}.",
                    "face_runtime": runtime_status,
                },
            )

        if state == "failed":
            code = "face_runtime_failed"
            message = "Face runtime initialization failed."
        else:
            code = "face_runtime_initializing"
            message = "Face runtime is still initializing."

        detail: dict[str, object] = {
            "code": code,
            "message": message,
            "face_runtime": runtime_status,
        }
        if context:
            detail["context"] = context
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
```

**After:**
```python
    def ensure_face_runtime_ready(
        self,
        *,
        mode: str = "single",
        context: str | None = None,
    ) -> dict[str, object]:
        runtime_status = self.face_runtime_status(mode)
        logger.info(
            f"ensure_face_runtime_ready [{context}]: mode={mode}, ready={runtime_status['ready']}, "
            f"state={runtime_status['state']}, reason={runtime_status.get('reason')}, "
            f"last_error={runtime_status.get('last_error')}"
        )

        if runtime_status["ready"]:
            return runtime_status

        reason = str(runtime_status.get("reason") or "insightface_warming_up")
        state = str(runtime_status.get("state") or "initializing")

        logger.warning(
            f"Face runtime NOT ready [{context}]: state={state}, reason={reason}, "
            f"last_error={runtime_status.get('last_error')}"
        )

        if reason == "unsupported_mode":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "unsupported_face_mode",
                    "message": f"Unsupported face mode: {mode}.",
                    "face_runtime": runtime_status,
                },
            )

        if state == "failed":
            code = "face_runtime_failed"
            message = "Face runtime initialization failed."
            logger.error(f"Face runtime FAILED [{context}]: {runtime_status}")
        else:
            code = "face_runtime_initializing"
            message = "Face runtime is still initializing."
            logger.info(f"Face runtime INITIALIZING [{context}]: {runtime_status}")

        detail: dict[str, object] = {
            "code": code,
            "message": message,
            "face_runtime": runtime_status,
        }
        if context:
            detail["context"] = context
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
```

### Step 1.4 — Log inside `extract_encoding_from_bytes`

- [ ] Find `extract_encoding_from_bytes` (the method body starts with `"""Load an image, optionally run liveness...`). Replace the body with the logged version:

**Before:**
```python
        """Load an image, optionally run liveness, then return one face embedding."""
        probes = self.analyze_faces_from_bytes(
            image_bytes,
            enforce_liveness=enforce_liveness,
            mode=mode,
        )
        if require_single_face and len(probes) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image must contain exactly one face.",
            )

        probe = probes[0]
        if probe.error_code == "spoof_detected":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Spoof detected. label={probe.liveness.label} score={probe.liveness.score:.3f}",
            )
        if probe.encoding is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to compute a face encoding from the image.",
            )
        return np.asarray(probe.encoding, dtype=np.float32), probe.liveness
```

**After:**
```python
        """Load an image, optionally run liveness, then return one face embedding."""
        logger.info(
            f"extract_encoding_from_bytes: size={len(image_bytes)}, "
            f"require_single={require_single_face}, enforce_liveness={enforce_liveness}, mode={mode}"
        )

        probes = self.analyze_faces_from_bytes(
            image_bytes,
            enforce_liveness=enforce_liveness,
            mode=mode,
        )
        logger.info(f"Detected {len(probes)} face(s) in image")

        if require_single_face and len(probes) != 1:
            logger.warning(f"Expected 1 face, found {len(probes)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image must contain exactly one face.",
            )

        probe = probes[0]
        if probe.error_code == "spoof_detected":
            logger.warning(f"Spoof detected: label={probe.liveness.label}, score={probe.liveness.score:.3f}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Spoof detected. label={probe.liveness.label} score={probe.liveness.score:.3f}",
            )
        if probe.encoding is None:
            logger.error("Failed to compute face encoding")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to compute a face encoding from the image.",
            )
        return np.asarray(probe.encoding, dtype=np.float32), probe.liveness
```

### Step 1.5 — Verify the service file compiles

- [ ] Run:
```powershell
cd backend; python -c "from app.services.face_recognition import FaceRecognitionService; print('OK')"
```
Expected output: `OK`

### Step 1.6 — Commit

- [ ] Commit:
```powershell
git add backend/app/services/face_recognition.py
git commit -m "feat(face): add structured logging to face recognition service"
```

---

## Task 2: Add logging, datetime fix, 503 handling, and debug endpoint to `backend/app/routers/face_recognition.py`

**Files:**
- Modify: `backend/app/routers/face_recognition.py`

### Step 2.1 — Add `import logging`

- [ ] In `backend/app/routers/face_recognition.py`, insert `import logging` after `from datetime import datetime`:

```python
from datetime import datetime
import logging
import math
```

### Step 2.2 — Add module-level logger

- [ ] After `face_service = FaceRecognitionService()` (line 67), add the logger:

**Before:**
```python
router = APIRouter(prefix="/face", tags=["face-recognition"])
face_service = FaceRecognitionService()


def _enforce_face_endpoint_rate_limit(
```

**After:**
```python
router = APIRouter(prefix="/face", tags=["face-recognition"])
face_service = FaceRecognitionService()
logger = logging.getLogger(__name__)


def _enforce_face_endpoint_rate_limit(
```

### Step 2.3 — Add `_serialize_error_detail` helper

- [ ] After the `_serialize_attendance_decision` function (ends around line 139), add the new helper **before** `_attendance_time_window_detail`:

```python
def _serialize_error_detail(detail: dict[str, object]) -> dict[str, object]:
    """Recursively convert datetime objects to ISO strings in error detail dicts."""
    result = {}
    for key, value in detail.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = _serialize_error_detail(value)
        else:
            result[key] = value
    return result
```

So the order becomes:
1. `_serialize_attendance_decision` (existing)
2. `_serialize_error_detail` (new — added here)
3. `_attendance_time_window_detail` (existing)

### Step 2.4 — Fix `_attendance_scan_error_detail` return

- [ ] In `_attendance_scan_error_detail`, change the final `return detail` to `return _serialize_error_detail(detail)`:

**Before:**
```python
    detail.update(extra)
    return detail
```

**After:**
```python
    detail.update(extra)
    return _serialize_error_detail(detail)
```

### Step 2.5 — Add logging to `_ensure_face_runtime_ready`

- [ ] Replace the current one-liner body of `_ensure_face_runtime_ready` with the logging version:

**Before:**
```python
def _ensure_face_runtime_ready(mode: str, *, context: str) -> None:
    face_service.ensure_face_runtime_ready(mode=mode, context=context)
```

**After:**
```python
def _ensure_face_runtime_ready(mode: str, *, context: str) -> None:
    """Ensure face runtime is ready and log detailed status for debugging."""
    runtime_status = face_service.face_runtime_status(mode)
    logger.info(
        f"Face runtime check [{context}]: mode={mode}, ready={runtime_status['ready']}, "
        f"state={runtime_status['state']}, reason={runtime_status.get('reason')}"
    )
    if not runtime_status["ready"]:
        logger.error(
            f"Face runtime NOT ready [{context}]: {runtime_status}"
        )
    face_service.ensure_face_runtime_ready(mode=mode, context=context)
```

### Step 2.6 — Add `GET /face/runtime-status` debug endpoint

- [ ] Immediately after the `_ensure_face_runtime_ready` function, add the new endpoint (before `@router.post("/register", ...)`):

```python
@router.get("/runtime-status")
def get_face_runtime_status(
    current_user: UserModel = Depends(get_current_application_user),
):
    """Get detailed face recognition runtime status for debugging."""
    single_status = face_service.face_runtime_status("single")
    liveness_ready, liveness_reason = face_service.anti_spoof_status()

    logger.info(f"Runtime status check by user {current_user.email}: single={single_status['ready']}, liveness={liveness_ready}")

    return {
        "single_mode": single_status,
        "liveness": {
            "ready": liveness_ready,
            "reason": liveness_reason,
        },
        "settings": {
            "face_threshold_single": face_service.settings.face_threshold_single,
            "liveness_threshold": face_service.settings.liveness_threshold,
            "face_embedding_dim": face_service.settings.face_embedding_dim,
            "face_embedding_dtype": face_service.settings.face_embedding_dtype,
        },
    }
```

### Step 2.7 — Add logging and better error handling in `record_attendance_from_face_scan`

The `else` branch (non-bypass path) starting at line ~422 needs these changes. The existing code around line 429 is:

```python
        _ensure_face_runtime_ready(mode="single", context="face_attendance_scan")
        image_bytes = face_service.decode_base64_image(payload.image_base64)
        try:
            encoding, liveness = face_service.extract_encoding_from_bytes(
                image_bytes,
                require_single_face=True,
                enforce_liveness=True,
                mode="single",
            )
        except HTTPException as exc:
            normalized_error = resolve_face_verification_error_message(exc.detail)
            if normalized_error is None:
                _record_face_failure(current_user, "face-attendance")
                raise
            status_code, message = normalized_error
            _record_face_failure(current_user, "face-attendance")
            raise HTTPException(status_code=status_code, detail=message) from exc
        try:
            reference_encoding = face_service.encoding_from_bytes(
                bytes(current_student_profile.face_encoding),
                dtype=current_student_profile.embedding_dtype,
                dimension=current_student_profile.embedding_dimension,
                normalized=bool(current_student_profile.embedding_normalized),
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Re-register your student face with the current ArcFace enrollment "
                    "before using face attendance."
                ),
            ) from exc

        match = face_service.compare_encodings(
            encoding,
            reference_encoding,
            threshold=payload.threshold,
            mode="single",
        )
        if not match.matched:
            _record_face_failure(current_user, "face-attendance")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Face not match.",
            )
```

- [ ] Replace that entire block with:

```python
        logger.info(
            f"Face scan attempt: event_id={payload.event_id}, student={current_student_profile.student_id}, "
            f"has_image={bool(payload.image_base64)}, bypass={bypass_face_scan}"
        )

        try:
            _ensure_face_runtime_ready(mode="single", context="face_attendance_scan")
        except HTTPException as runtime_exc:
            logger.error(
                f"Face runtime not ready for student {current_student_profile.student_id}: {runtime_exc.detail}"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Face detection is not ready. Please keep the camera open and try scanning again.",
            ) from runtime_exc

        image_bytes = face_service.decode_base64_image(payload.image_base64)
        logger.info(f"Image decoded: size={len(image_bytes)} bytes")

        try:
            encoding, liveness = face_service.extract_encoding_from_bytes(
                image_bytes,
                require_single_face=True,
                enforce_liveness=True,
                mode="single",
            )
            logger.info(
                f"Face extracted: liveness={liveness.label}, score={liveness.score:.3f}, "
                f"encoding_shape={encoding.shape if encoding is not None else None}"
            )
        except HTTPException as exc:
            logger.warning(f"Face extraction failed: {exc.status_code} - {exc.detail}")
            normalized_error = resolve_face_verification_error_message(exc.detail)
            if normalized_error is None:
                _record_face_failure(current_user, "face-attendance")
                raise
            status_code, message = normalized_error
            _record_face_failure(current_user, "face-attendance")
            raise HTTPException(status_code=status_code, detail=message) from exc
        except Exception as exc:
            logger.exception(f"Unexpected error during face extraction: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during face processing.",
            ) from exc

        try:
            reference_encoding = face_service.encoding_from_bytes(
                bytes(current_student_profile.face_encoding),
                dtype=current_student_profile.embedding_dtype,
                dimension=current_student_profile.embedding_dimension,
                normalized=bool(current_student_profile.embedding_normalized),
            )
            logger.info(f"Reference encoding loaded for student {current_student_profile.student_id}")
        except ValueError as exc:
            logger.error(f"Failed to load reference encoding: {exc}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Re-register your student face with the current ArcFace enrollment "
                    "before using face attendance."
                ),
            ) from exc

        match = face_service.compare_encodings(
            encoding,
            reference_encoding,
            threshold=payload.threshold,
            mode="single",
        )
        logger.info(
            f"Face match result: matched={match.matched}, distance={match.distance:.4f}, "
            f"confidence={match.confidence:.4f}, threshold={match.threshold:.4f}"
        )
        if not match.matched:
            logger.warning(
                f"Face verification failed for student {current_student_profile.student_id}: "
                f"distance {match.distance:.4f} > threshold {match.threshold:.4f}"
            )
            _record_face_failure(current_user, "face-attendance")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Face not match.",
            )
```

> **Important:** The `_record_face_failure(current_user, "face-attendance")` calls that were already inside the except blocks must remain in place — do not remove them. The new `logger.warning` for `not match.matched` is added **before** the existing `_record_face_failure` call.

### Step 2.8 — Verify the router compiles

- [ ] Run:
```powershell
cd backend; python -c "from app.routers.face_recognition import router; print('OK')"
```
Expected output: `OK`

### Step 2.9 — Commit

- [ ] Commit:
```powershell
git add backend/app/routers/face_recognition.py
git commit -m "feat(face): add logging, datetime fix, 503 handling, and debug runtime-status endpoint"
```

---

## Task 3: Document `GET /face/runtime-status` in Backend Documentation

**Files:**
- Modify: `docs/Backend Documentation.md`

### Step 3.1 — Add endpoint entry

- [ ] In `docs/Backend Documentation.md`, find the `### GET /face/status` section (around line 1612). Add the new endpoint **before** it (so it sits between `_ensure_face_runtime_ready` and the existing status endpoint in doc order):

Insert immediately before `### GET \`/face/status\``:

```markdown
### GET `/face/runtime-status`

Get detailed face recognition engine runtime status for debugging. Returns readiness of the single-face detection model and the anti-spoof liveness model, plus key configuration thresholds.

**Auth:** Any authenticated user

**Response 200:**
```json
{
  "single_mode": {
    "ready": true,
    "state": "ready",
    "reason": null,
    "last_error": null
  },
  "liveness": {
    "ready": true,
    "reason": null
  },
  "settings": {
    "face_threshold_single": 0.5,
    "liveness_threshold": 0.5,
    "face_embedding_dim": 512,
    "face_embedding_dtype": "float32"
  }
}
```

---

```

### Step 3.2 — Commit

- [ ] Commit:
```powershell
git add "docs/Backend Documentation.md"
git commit -m "docs: add GET /face/runtime-status endpoint to backend documentation"
```

---

## Self-Review

**Spec coverage:**
- ✅ `import logging` + `logger` in service — Task 1.1, 1.2
- ✅ Logging in `ensure_face_runtime_ready` — Task 1.3
- ✅ Logging in `extract_encoding_from_bytes` — Task 1.4
- ✅ `import logging` + `logger` in router — Task 2.1, 2.2
- ✅ `_serialize_error_detail` helper — Task 2.3
- ✅ `_attendance_scan_error_detail` return fix — Task 2.4
- ✅ Logging in `_ensure_face_runtime_ready` wrapper — Task 2.5
- ✅ New `GET /face/runtime-status` endpoint — Task 2.6
- ✅ Logging + 503 wrapping in `record_attendance_from_face_scan` — Task 2.7
- ✅ Backend docs updated — Task 3.1

**Unchanged code (no side effects):**
- All other routers, models, schemas, migrations, workers — untouched
- Existing business logic (geolocation, sanction checks, time window checks, rate limiting) — untouched
- `face_engine.py` and `attendance_face_scan.py` — untouched
- Frontend files — untouched (per CLAUDE.md mandate)

**Placeholder scan:** No TBDs, no "similar to Task N" shortcuts. All code blocks are complete and exact.

**Type consistency:** `_serialize_error_detail` takes and returns `dict[str, object]`, consistent with `_attendance_scan_error_detail`'s existing type annotation. The `logger` variable name is identical in both files.
