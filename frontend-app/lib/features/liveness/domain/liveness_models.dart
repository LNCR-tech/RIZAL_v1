import 'dart:typed_data';
import 'dart:ui' show Rect;

/// One face's liveness verdict for a single frame.
class FaceCheck {
  const FaceCheck({
    required this.boundingBox,
    required this.score,
    required this.isReal,
    this.isLargest = false,
  });

  /// Face bounding box in the source image's coordinate space.
  final Rect boundingBox;

  /// Plugin's raw confidence score in `[0, 1]` (1.0 = real, 0.0 = fake), or
  /// null if the plugin returned no score (treat as unknown — don't gate on
  /// null).
  final double? score;

  /// Convenience: `score != null && score >= threshold`. Threshold lives in
  /// [LivenessService], not here, so the model stays a pure data class.
  final bool isReal;

  /// True when this face is the largest detected face in the frame. The
  /// attendance preflight gates on this face only; the kiosk also uses it
  /// to choose which face to scan on (avoids 10× plugin calls per frame).
  final bool isLargest;
}

/// Outcome of running on-device face detection + liveness on a single camera
/// frame. The [usable] flag distinguishes "I ran the check and have an
/// answer" from "I couldn't run the check, fall through to backend" — the
/// caller treats those differently (hard-gate only when `usable == true`).
class LivenessFrameResult {
  const LivenessFrameResult({
    required this.usable,
    required this.faces,
    this.error,
  });

  /// Empty result, ready to send to backend: the on-device pipeline isn't
  /// available (iOS, plugin init failed, model unavailable, etc.). Caller
  /// MUST NOT block on this — backend stays the authoritative check.
  const LivenessFrameResult.unavailable()
      : usable = false,
        faces = const [],
        error = null;

  /// We ran the pipeline but no face was detected in the frame.
  const LivenessFrameResult.empty()
      : usable = true,
        faces = const [],
        error = null;

  /// We attempted the pipeline but a transient error fired (ML Kit or plugin
  /// throw on this frame). Treated identically to [unavailable] for gating
  /// purposes — the backend takes over.
  const LivenessFrameResult.transientError(String message)
      : usable = false,
        faces = const [],
        error = message;

  /// True only when the on-device pipeline ran successfully. UI gates and
  /// counters must check this before trusting [faces].
  final bool usable;

  /// One entry per detected face (currently we only run the liveness model
  /// on the largest face for perf — other faces are detected but their
  /// `score` is null and `isReal` is false). May be empty even when
  /// [usable] is true: that means "no face seen here".
  final List<FaceCheck> faces;

  /// Diagnostic message when the pipeline errored on this frame. Never
  /// surfaced to end users — only useful for debug logging.
  final String? error;

  /// Convenience accessors.
  bool get hasAnyFace => faces.isNotEmpty;

  bool get anyReal => faces.any((f) => f.isReal);

  FaceCheck? get largest =>
      faces.firstWhere((f) => f.isLargest, orElse: () => faces.isEmpty
          ? const FaceCheck(
              boundingBox: Rect.fromLTWH(0, 0, 0, 0),
              score: null,
              isReal: false,
            )
          : faces.first);

  /// True when the on-device pipeline ran AND we have a verdict that says
  /// "this frame contains at least one face AND none of the checked faces
  /// looks real" — i.e. the frame should be blocked. When [usable] is false,
  /// always returns false (we have no opinion).
  bool get isSpoof {
    if (!usable) return false;
    if (faces.isEmpty) return false;
    return !anyReal;
  }
}

/// NV21 frame ingest payload. Decoupled from the `CameraImage` type so the
/// service can be tested without a real camera plugin in the picture.
class Nv21Frame {
  const Nv21Frame({
    required this.bytes,
    required this.width,
    required this.height,
    required this.orientationDegrees,
  });

  /// NV21-packed luma + interleaved VU bytes. Must equal `width * height *
  /// 3 / 2` bytes exactly (the plugin validates this size and throws on a
  /// mismatch).
  final Uint8List bytes;

  final int width;
  final int height;

  /// Rotation in degrees (0 / 90 / 180 / 270). For most Android phones the
  /// back camera reports 90; the front camera reports 270.
  final int orientationDegrees;
}
