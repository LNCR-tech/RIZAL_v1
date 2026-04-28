# Face Scan Debugging Guide

## Common Errors

### 1. "Face detection is not ready. Please keep the camera open and try scanning again."

**Cause**: Face recognition runtime (InsightFace) is still initializing or failed to load.

**Debug Steps**:

1. **Check runtime status**:
   ```bash
   curl http://localhost:8000/api/face/runtime-status \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. **Check backend logs**:
   ```bash
   docker compose logs backend | grep -i "face"
   ```

   Look for:
   - `Face runtime check`: Shows if runtime is ready
   - `Face runtime NOT ready`: Shows why it's not ready
   - `state=failed`: Runtime initialization failed
   - `state=initializing`: Still warming up (wait 30-60 seconds)

3. **Common causes**:
   - **First request after startup**: InsightFace models take 30-60 seconds to load
   - **Memory issues**: Not enough RAM (needs ~2GB for models)
   - **Missing models**: Models not downloaded to `backend/.insightface/`
   - **ONNX runtime issues**: Check ONNX installation

**Solutions**:

- **Wait**: If `state=initializing`, wait 1 minute and try again
- **Restart backend**: `docker compose restart backend`
- **Check memory**: `docker stats` - ensure backend has enough RAM
- **Force initialization**: Call `/api/face/runtime-status` to trigger warmup

### 2. "Internal Server Error" (500)

**Cause**: Unexpected error during face processing.

**Debug Steps**:

1. **Check backend logs for stack trace**:
   ```bash
   docker compose logs backend --tail=100
   ```

2. **Look for specific errors**:
   - `Unexpected error during face extraction`: Image processing failed
   - `Failed to load reference encoding`: Student's face encoding is corrupted
   - `Face extraction failed`: Face detection or encoding failed

3. **Check student face registration**:
   - Verify student has registered face: Check `student_profile.face_encoding` is not NULL
   - Check embedding metadata matches current system

**Solutions**:

- **Re-register face**: Student should re-register their face
- **Check image quality**: Ensure camera provides clear, well-lit images
- **Verify database**: Check `student_profile` table for corrupted encodings

### 3. "Face not match"

**Cause**: Face verification failed - captured face doesn't match registered face.

**Debug Steps**:

1. **Check match details in logs**:
   ```bash
   docker compose logs backend | grep "Face match result"
   ```

   Look for:
   - `distance`: How different the faces are (lower is better)
   - `threshold`: Maximum allowed distance (default 0.4)
   - `confidence`: Match confidence (higher is better)

2. **Example log**:
   ```
   Face match result: matched=False, distance=0.5234, confidence=0.4766, threshold=0.4000
   ```
   This shows distance (0.52) > threshold (0.40), so match failed.

**Solutions**:

- **Re-register face**: If distance is very high (>0.6), re-register
- **Improve lighting**: Ensure good lighting during scan
- **Face camera directly**: Look straight at camera
- **Adjust threshold**: Lower threshold in `.env` if too strict (not recommended for production)

## Logging Details

The system now logs:

1. **Runtime checks**: Every time face runtime is checked
2. **Face scan attempts**: Event ID, student ID, bypass status
3. **Image processing**: Image size, face detection results
4. **Face extraction**: Liveness results, encoding shape
5. **Face matching**: Distance, confidence, threshold, match result
6. **Errors**: Detailed error messages with context

## Diagnostic Endpoint

**GET** `/api/face/runtime-status`

Returns:
```json
{
  "single_mode": {
    "state": "ready",
    "ready": true,
    "reason": null,
    "last_error": null,
    "provider_target": "CPUExecutionProvider",
    "mode": "single",
    "initialized_at": "2024-01-15T10:30:00",
    "warmup_duration_ms": 45000
  },
  "liveness": {
    "ready": true,
    "reason": null
  },
  "settings": {
    "face_threshold_single": 0.4,
    "liveness_threshold": 0.5,
    "face_embedding_dim": 512,
    "face_embedding_dtype": "float32"
  }
}
```

## Production Monitoring

**Key metrics to monitor**:

1. **Runtime ready status**: Should be `true` after startup
2. **Face scan success rate**: Track failed vs successful scans
3. **Average match distance**: Monitor for drift over time
4. **Initialization time**: Should be <60 seconds on startup

**Alerts to set up**:

- Alert if `state=failed` for >5 minutes
- Alert if face scan error rate >10%
- Alert if initialization takes >2 minutes

## Environment Variables

Relevant settings in `.env`:

```bash
# Face recognition thresholds
FACE_THRESHOLD_SINGLE=0.4          # Lower = stricter matching
LIVENESS_THRESHOLD=0.5             # Anti-spoofing threshold

# Bypass for testing (DO NOT use in production)
FACE_SCAN_BYPASS_ALL=false
FACE_SCAN_BYPASS_EMAILS=test@example.com

# Model settings
FACE_EMBEDDING_DIM=512
FACE_EMBEDDING_DTYPE=float32
```

## Quick Fixes

### Face runtime stuck in "initializing"

```bash
# Restart backend
docker compose restart backend

# Check if models are downloaded
docker compose exec backend ls -lh /app/.insightface/models/

# Force re-download models (if missing)
docker compose exec backend rm -rf /app/.insightface/
docker compose restart backend
```

### All face scans failing

```bash
# Check backend health
curl http://localhost:8000/health

# Check face runtime
curl http://localhost:8000/api/face/runtime-status -H "Authorization: Bearer TOKEN"

# View recent logs
docker compose logs backend --tail=50 --follow
```

### Student can't scan after re-registering

```bash
# Check student face encoding in database
docker compose exec postgres psql -U aura_user -d aura_db -c \
  "SELECT student_id, is_face_registered, embedding_provider, embedding_dimension 
   FROM student_profile WHERE student_id = 'STUDENT_ID';"

# Should show:
# - is_face_registered: true
# - embedding_provider: arcface
# - embedding_dimension: 512
```

## Contact Support

If issues persist after following this guide:

1. Collect logs: `docker compose logs backend > backend_logs.txt`
2. Include runtime status output
3. Describe exact steps to reproduce
4. Note any recent changes (updates, config changes, etc.)
