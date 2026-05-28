"""
Before/After timing benchmark — face capture/validation pipeline.

Compares:
  BEFORE: original path (no image downscaling)
  AFTER:  optimized path (1280px cap on input + 640px cap on liveness crop)

Run: python test-pics/timing_benchmark.py
"""

import sys
import time
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

import numpy as np
from PIL import Image
import io

try:
    import cv2
except ImportError:
    print("ERROR: pip install opencv-python-headless")
    sys.exit(1)
try:
    import onnxruntime as ort
except ImportError:
    print("ERROR: pip install onnxruntime")
    sys.exit(1)
try:
    import insightface
except ImportError:
    print("ERROR: pip install insightface")
    sys.exit(1)

MODEL_PATH = BACKEND_ROOT / "models" / "MiniFASNetV2.onnx"
TEST_DIR   = Path(__file__).resolve().parent
RUNS       = 5

FACE_MAX_INPUT_DIM   = 1280   # backend default
FACE_LIVENESS_CROP_MAX = 640  # backend default


# ── model loading ─────────────────────────────────────────────────────────────

print("\nLoading models (one-time startup cost)...")

t0 = time.perf_counter()
fas_session = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
fas_input   = fas_session.get_inputs()[0]
fas_output  = fas_session.get_outputs()[0]
fas_size    = (int(fas_input.shape[2]), int(fas_input.shape[3]))
fas_load_ms = (time.perf_counter() - t0) * 1000
print(f"  MiniFASNet loaded        : {fas_load_ms:.0f} ms")

t0 = time.perf_counter()
face_app = insightface.app.FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"],
    allowed_modules=["detection", "recognition"],
)
face_app.prepare(ctx_id=-1, det_size=(640, 640))
insightface_load_ms = (time.perf_counter() - t0) * 1000
print(f"  InsightFace loaded+ready : {insightface_load_ms:.0f} ms")
print(f"  TOTAL startup cost       : {fas_load_ms + insightface_load_ms:.0f} ms")
print(f"  (One-time cost — already done before the first API request)\n")


# ── helpers ───────────────────────────────────────────────────────────────────

def softmax(logits):
    exp = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    return exp / exp.sum(axis=1, keepdims=True)


def liveness_score(crop_rgb, cap_dim=0):
    """Score a face crop. cap_dim=0 = old path; cap_dim>0 = optimized path."""
    h, w = fas_size
    bgr = crop_rgb[:, :, ::-1]
    if cap_dim > 0:
        ch, cw = bgr.shape[:2]
        if ch > cap_dim or cw > cap_dim:
            scale = cap_dim / max(ch, cw)
            bgr = cv2.resize(
                bgr,
                (max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))),
                interpolation=cv2.INTER_AREA,
            )
    resized = cv2.resize(bgr, (w, h))
    x = resized.astype(np.float32)
    x = np.transpose(x, (2, 0, 1))[np.newaxis]
    logits = fas_session.run([fas_output.name], {fas_input.name: x})[0]
    return float(softmax(logits)[0, 1])


def crop_with_context(frame, bbox, configured_scale=2.7):
    src_h, src_w = frame.shape[:2]
    left, top, right, bottom = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    box_w = max(1, right - left)
    box_h = max(1, bottom - top)
    eff = min((src_h - 1) / box_h, min((src_w - 1) / box_w, max(1.0, configured_scale)))
    if eff < 1.5:
        return frame.copy()
    new_w = box_w * eff
    new_h = box_h * eff
    cx = box_w / 2.0 + left
    cy = box_h / 2.0 + top
    x1 = max(0, int(round(cx - new_w / 2)))
    y1 = max(0, int(round(cy - new_h / 2)))
    x2 = min(src_w - 1, int(round(cx + new_w / 2)))
    y2 = min(src_h - 1, int(round(cy + new_h / 2)))
    return frame[y1:y2+1, x1:x2+1]


def load_frame(raw_bytes, max_dim=0):
    img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    arr = np.asarray(img, dtype=np.uint8)
    if max_dim > 0:
        h, w = arr.shape[:2]
        if w > max_dim or h > max_dim:
            scale = max_dim / max(w, h)
            arr = cv2.resize(
                arr,
                (max(1, int(round(w * scale))), max(1, int(round(h * scale)))),
                interpolation=cv2.INTER_AREA,
            )
    return arr


def run_pipeline(raw_bytes, *, max_input_dim=0, max_liveness_dim=0):
    """Full pipeline. Returns (result_dict, timing_dict)."""
    decode_times = []
    detect_times = []
    crop_times   = []
    live_times   = []
    total_times  = []
    result = {}

    for _ in range(RUNS):
        t_total = time.perf_counter()

        t = time.perf_counter()
        frame = load_frame(raw_bytes, max_dim=max_input_dim)
        decode_times.append((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        detections = face_app.get(frame)
        detect_times.append((time.perf_counter() - t) * 1000)

        if not detections:
            return None, None

        bbox = np.asarray(detections[0].bbox, dtype=np.float32)

        t = time.perf_counter()
        crop = crop_with_context(frame, bbox)
        crop_times.append((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        score = liveness_score(crop, cap_dim=max_liveness_dim)
        live_times.append((time.perf_counter() - t) * 1000)

        total_times.append((time.perf_counter() - t_total) * 1000)
        result = {
            "frame": f"{frame.shape[1]}x{frame.shape[0]}",
            "crop":  f"{crop.shape[1]}x{crop.shape[0]}",
            "score": score,
            "label": "Real [PASS]" if score >= 0.85 else ("OK(threshold)" if score >= 0.55 else "Fake [FAIL]"),
        }

    avg = lambda lst: sum(lst) / len(lst)
    times = {
        "decode_ms":   avg(decode_times),
        "detect_ms":   avg(detect_times),
        "crop_ms":     avg(crop_times),
        "liveness_ms": avg(live_times),
        "total_ms":    avg(total_times),
        "min_ms":      min(total_times),
        "max_ms":      max(total_times),
    }
    return result, times


# ── run benchmarks ────────────────────────────────────────────────────────────

for name, path in [
    ("orig.jpg  (real selfie)",          TEST_DIR / "orig.jpg"),
    ("spoog.jpg (spoof / photo on screen)", TEST_DIR / "spoog.jpg"),
]:
    raw = path.read_bytes()
    print(f"\n{'='*65}")
    print(f"  {name}  [{len(raw)//1024} KB]")
    print(f"{'='*65}")

    res_before, t_before = run_pipeline(raw, max_input_dim=0, max_liveness_dim=0)
    res_after,  t_after  = run_pipeline(raw, max_input_dim=FACE_MAX_INPUT_DIM, max_liveness_dim=FACE_LIVENESS_CROP_MAX)

    if res_before is None:
        print("  ERROR: No face detected.")
        continue

    print(f"\n  {'Phase':<28} {'BEFORE':>10}  {'AFTER':>10}  {'Saved':>10}")
    print(f"  {'-'*60}")
    for phase, key in [
        ("Image decode + resize",  "decode_ms"),
        ("Face detection (SCRFD)", "detect_ms"),
        ("Crop extraction",        "crop_ms"),
        ("Liveness check",         "liveness_ms"),
    ]:
        b = t_before[key]
        a = t_after[key]
        saved = b - a
        print(f"  {phase:<28} {b:>8.1f}ms  {a:>8.1f}ms  {saved:>+8.1f}ms")
    print(f"  {'-'*60}")
    b_tot = t_before["total_ms"]
    a_tot = t_after["total_ms"]
    pct   = (b_tot - a_tot) / b_tot * 100
    print(f"  {'TOTAL server-side':<28} {b_tot:>8.1f}ms  {a_tot:>8.1f}ms  {pct:>+8.1f}%")
    print(f"\n  Frame size:  BEFORE={res_before['frame']}  AFTER={res_after['frame']}")
    print(f"  Crop size:   BEFORE={res_before['crop']}  AFTER={res_after['crop']}")
    print(f"  Score:       BEFORE={res_before['score']:.4f} ({res_before['label']})  AFTER={res_after['score']:.4f} ({res_after['label']})")

print(f"\n{'='*65}")
print("  Network upload (mobile -> server): ~200-500ms on 4G (not included above)")
print(f"{'='*65}\n")
