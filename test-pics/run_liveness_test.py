"""
Local test script — compares MiniFASNet liveness scores for:
  - orig.jpg  : real selfie (should score HIGH / "Real")
  - spoog.jpg : photo of photo on screen (should score LOW / "Fake")

Runs BOTH the old (no normalization) and new (ImageNet-normalized) preprocessing
so we can compare the effect of the fix.
"""

import sys
import os
from pathlib import Path

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

import numpy as np
from PIL import Image

try:
    import cv2
except ImportError:
    print("ERROR: cv2 not found. Install: pip install opencv-python-headless")
    sys.exit(1)

try:
    import onnxruntime as ort
except ImportError:
    print("ERROR: onnxruntime not found. Install: pip install onnxruntime")
    sys.exit(1)


MODEL_PATH = BACKEND_ROOT / "models" / "MiniFASNetV2.onnx"
TEST_DIR   = Path(__file__).resolve().parent

IMAGENET_MEAN = np.array([0.406, 0.456, 0.485], dtype=np.float32)  # BGR order
IMAGENET_STD  = np.array([0.225, 0.224, 0.229], dtype=np.float32)  # BGR order


def load_model():
    if not MODEL_PATH.exists():
        print(f"ERROR: Model not found at {MODEL_PATH}")
        sys.exit(1)
    session = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
    input_meta  = session.get_inputs()[0]
    output_meta = session.get_outputs()[0]
    input_size  = (int(input_meta.shape[2]), int(input_meta.shape[3]))
    return session, input_meta.name, output_meta.name, input_size


def softmax(logits):
    exp = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    return exp / exp.sum(axis=1, keepdims=True)


def load_image_rgb(path):
    img = Image.open(path).convert("RGB")
    return np.asarray(img, dtype=np.uint8)


def infer_OLD(session, input_name, output_name, input_size, rgb_image):
    """Old preprocessing — raw float32 0-255 (the bug)."""
    h, w = input_size
    bgr   = rgb_image[:, :, ::-1]
    resized = cv2.resize(bgr, (w, h))
    x = resized.astype(np.float32)           # BUG: no normalization
    x = np.transpose(x, (2, 0, 1))
    x = np.expand_dims(x, axis=0)
    logits = session.run([output_name], {input_name: x})[0]
    probs  = softmax(logits)
    return float(probs[0, 1])               # index 1 = Real


def infer_NEW(session, input_name, output_name, input_size, rgb_image):
    """New preprocessing — ImageNet-normalized (the fix)."""
    h, w = input_size
    bgr   = rgb_image[:, :, ::-1]
    resized = cv2.resize(bgr, (w, h))
    x = resized.astype(np.float32) / 255.0  # FIX: scale to [0,1]
    x = (x - IMAGENET_MEAN) / IMAGENET_STD  # FIX: ImageNet normalization
    x = np.transpose(x, (2, 0, 1))
    x = np.expand_dims(x, axis=0)
    logits = session.run([output_name], {input_name: x})[0]
    probs  = softmax(logits)
    return float(probs[0, 1])


def run_test(name, image_path, session, input_name, output_name, input_size, threshold=0.55):
    rgb = load_image_rgb(image_path)
    score_old = infer_OLD(session, input_name, output_name, input_size, rgb)
    score_new = infer_NEW(session, input_name, output_name, input_size, rgb)

    label_old = "Real [PASS]" if score_old >= threshold else "Fake [FAIL]"
    label_new = "Real [PASS]" if score_new >= threshold else "Fake [FAIL]"

    print(f"\n{'='*60}")
    print(f"  Image : {name}")
    print(f"{'='*60}")
    print(f"  OLD (no normalization) : score={score_old:.4f}  -> {label_old}")
    print(f"  NEW (ImageNet-normed)  : score={score_new:.4f}  -> {label_new}")
    print(f"  Threshold used         : {threshold}")


if __name__ == "__main__":
    print(f"\nLoading MiniFASNetV2 from: {MODEL_PATH}")
    session, input_name, output_name, input_size = load_model()
    print(f"Model loaded. Input size: {input_size}")

    run_test(
        "orig.jpg  (real selfie — should be REAL)",
        TEST_DIR / "orig.jpg",
        session, input_name, output_name, input_size,
    )

    run_test(
        "spoog.jpg (photo-of-photo on screen — should be FAKE)",
        TEST_DIR / "spoog.jpg",
        session, input_name, output_name, input_size,
    )

    print("\n")
