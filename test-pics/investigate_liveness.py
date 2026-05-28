"""
Deeper investigation: why does the live server fail with mobile camera frames?

This script tests multiple hypotheses:
1. JPEG quality / compression artifacts
2. Image size / resolution effects
3. The actual crop size the model sees (are mobile faces too small?)
4. Simulating what the mobile app actually sends (a full frame vs a tight crop)
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

import numpy as np
from PIL import Image

try:
    import cv2
except ImportError:
    print("ERROR: cv2 not found.")
    sys.exit(1)

try:
    import onnxruntime as ort
except ImportError:
    print("ERROR: onnxruntime not found.")
    sys.exit(1)

MODEL_PATH = BACKEND_ROOT / "models" / "MiniFASNetV2.onnx"
TEST_DIR   = Path(__file__).resolve().parent

def load_model():
    session = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
    inp  = session.get_inputs()[0]
    out  = session.get_outputs()[0]
    return session, inp.name, out.name, (int(inp.shape[2]), int(inp.shape[3]))

def softmax(logits):
    exp = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    return exp / exp.sum(axis=1, keepdims=True)

def infer_raw(session, input_name, output_name, input_size, rgb_image):
    h, w = input_size
    bgr = rgb_image[:, :, ::-1]
    resized = cv2.resize(bgr, (w, h))
    x = resized.astype(np.float32)
    x = np.transpose(x, (2, 0, 1))[np.newaxis]
    logits = session.run([output_name], {input_name: x})[0]
    return float(softmax(logits)[0, 1])

def try_insightface_detect_and_score(session, input_name, output_name, input_size, rgb_image, scale=2.7):
    """
    Simulate exactly what the backend does:
    1. Use InsightFace to detect the face bbox
    2. Expand with scale factor (anti_spoof_scale)
    3. Crop from the ORIGINAL frame (not just the face crop)
    4. Score that expanded crop
    """
    try:
        import insightface
    except ImportError:
        print("  [SKIP] insightface not installed, skipping bbox-based test")
        return None

    app = insightface.app.FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"],
        allowed_modules=["detection"],
    )
    app.prepare(ctx_id=-1, det_size=(640, 640))

    frame_uint8 = np.asarray(rgb_image, dtype=np.uint8)
    detections = app.get(frame_uint8)
    if not detections:
        print("  [WARN] InsightFace found no face in this image")
        return None

    det = detections[0]
    bbox = np.asarray(det.bbox, dtype=np.float32)
    left, top, right, bottom = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    src_h, src_w = frame_uint8.shape[:2]

    print(f"  Detected bbox: left={left}, top={top}, right={right}, bottom={bottom}")
    print(f"  Frame size: {src_w}x{src_h}")
    print(f"  Face size in frame: {right-left}x{bottom-top} px")

    # Replicate the _crop_from_frame_with_context logic
    box_w = max(1, right - left)
    box_h = max(1, bottom - top)
    effective_scale = max(1.0, scale)
    effective_scale = min((src_h - 1) / box_h, min((src_w - 1) / box_w, effective_scale))

    new_width  = box_w * effective_scale
    new_height = box_h * effective_scale
    center_x   = box_w / 2.0 + left
    center_y   = box_h / 2.0 + top

    ltx = center_x - new_width / 2.0
    lty = center_y - new_height / 2.0
    rbx = center_x + new_width / 2.0
    rby = center_y + new_height / 2.0

    if ltx < 0:
        rbx -= ltx; ltx = 0
    if lty < 0:
        rby -= lty; lty = 0
    if rbx > src_w - 1:
        ltx -= rbx - src_w + 1; rbx = src_w - 1
    if rby > src_h - 1:
        lty -= rby - src_h + 1; rby = src_h - 1

    x1 = max(0, int(round(ltx)))
    y1 = max(0, int(round(lty)))
    x2 = min(src_w - 1, int(round(rbx)))
    y2 = min(src_h - 1, int(round(rby)))

    crop = frame_uint8[y1:y2+1, x1:x2+1]
    print(f"  Expanded crop (scale={scale}): {x2-x1}x{y2-y1} px")

    score = infer_raw(session, input_name, output_name, input_size, crop)
    return score


def run(name, path):
    print(f"\n{'='*65}")
    print(f"  {name}")
    print(f"{'='*65}")

    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)
    print(f"  Image dimensions: {rgb.shape[1]}x{rgb.shape[0]} px")

    # Score the full image (no crop — simulates what JPEG upload sends)
    score_full = infer_raw(session, input_name, output_name, input_size, rgb)
    print(f"  Full-image score  (no bbox): {score_full:.4f}  -> {'Real [PASS]' if score_full >= 0.55 else 'Fake [FAIL]'}")

    # Score with InsightFace bbox + scale
    for scale in [1.0, 2.0, 2.7]:
        score_bbox = try_insightface_detect_and_score(
            session, input_name, output_name, input_size, rgb, scale=scale
        )
        if score_bbox is not None:
            print(f"  Bbox crop score (scale={scale}): {score_bbox:.4f}  -> {'Real [PASS]' if score_bbox >= 0.55 else 'Fake [FAIL]'}")


if __name__ == "__main__":
    print(f"Model: {MODEL_PATH}")
    session, input_name, output_name, input_size = load_model()
    print(f"Input size: {input_size}")

    run("orig.jpg  (real selfie)", TEST_DIR / "orig.jpg")
    run("spoog.jpg (spoof: photo on screen)", TEST_DIR / "spoog.jpg")
    print()
