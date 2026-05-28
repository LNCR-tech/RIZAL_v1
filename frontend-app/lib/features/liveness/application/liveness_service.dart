import 'dart:io' show Platform;
import 'dart:ui' show Rect, Size;

import 'package:face_anti_spoofing_detector/face_anti_spoofing_detector.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

import '../domain/liveness_models.dart';

/// Thin platform abstraction over the two plugins
/// ([FaceAntiSpoofingDetector] + ML Kit face detection) so the
/// [LivenessService] can be unit-tested without touching the real plugins.
abstract class LivenessBackend {
  /// Initialize the native liveness model. Returns false on failure rather
  /// than throwing; the service treats that as "pipeline unavailable".
  Future<bool> initialize();

  /// Release native resources. Idempotent.
  Future<void> destroy();

  /// Detect faces in an [InputImage]. Returns an empty list when nothing
  /// is detected; throws on platform errors.
  Future<List<Face>> detectFaces(InputImage image);

  /// Run the anti-spoof model on one face crop. Returns the plugin's raw
  /// confidence (`1.0` = real, `0.0` = fake) or null if the plugin returned
  /// nothing.
  Future<double?> detectLiveness({
    required Uint8List yuvBytes,
    required int previewWidth,
    required int previewHeight,
    required int orientation,
    required Rect faceBox,
  });
}

/// Production backend that wires up the real plugins.
class PluginLivenessBackend implements LivenessBackend {
  FaceDetector? _detector;

  @override
  Future<bool> initialize() async {
    // Plugin's iOS side is a stub at v0.0.4 (only `getPlatformVersion`
    // implemented). On iOS we bail before touching the plugin so we never
    // surface a `FlutterMethodNotImplemented` to the user.
    if (!_androidOnly()) return false;
    try {
      final ok = await FaceAntiSpoofingDetector.initialize();
      if (!ok) return false;
      _detector ??= FaceDetector(
        options: FaceDetectorOptions(
          // Fast mode is enough for liveness gating — we only need bounding
          // boxes, not landmarks or expressions, and frame rate matters more
          // than 1-2px precision on the box edges.
          performanceMode: FaceDetectorMode.fast,
          enableLandmarks: false,
          enableContours: false,
          enableTracking: false,
          enableClassification: false,
          minFaceSize: 0.15,
        ),
      );
      return true;
    } catch (e, st) {
      debugPrint('LivenessService init failed: $e\n$st');
      return false;
    }
  }

  @override
  Future<void> destroy() async {
    try {
      await _detector?.close();
    } catch (_) {}
    _detector = null;
    if (!_androidOnly()) return;
    try {
      await FaceAntiSpoofingDetector.destroy();
    } catch (_) {}
  }

  @override
  Future<List<Face>> detectFaces(InputImage image) async {
    final det = _detector;
    if (det == null) return const <Face>[];
    return det.processImage(image);
  }

  @override
  Future<double?> detectLiveness({
    required Uint8List yuvBytes,
    required int previewWidth,
    required int previewHeight,
    required int orientation,
    required Rect faceBox,
  }) =>
      FaceAntiSpoofingDetector.detect(
        yuvBytes: yuvBytes,
        previewWidth: previewWidth,
        previewHeight: previewHeight,
        orientation: orientation,
        faceContour: faceBox,
      );

  bool _androidOnly() {
    if (kIsWeb) return false;
    try {
      return Platform.isAndroid;
    } catch (_) {
      // Platform.isAndroid throws on web — kIsWeb above covers it, but be
      // defensive in case we run in any other unfamiliar environment.
      return false;
    }
  }
}

/// On-device passive liveness detection. Two-stage pipeline:
///
/// 1. ML Kit face detection produces bounding boxes for every face in the
///    frame.
/// 2. The Silent-Face-Anti-Spoof model (via [FaceAntiSpoofingDetector]) runs
///    on the **largest** face only — running it on every face per frame would
///    blow the per-frame budget in the multi-face kiosk case, and the largest
///    face is the strong signal of an attack anyway (a held-up phone or
///    printed photo would fill more of the frame than bystanders).
///
/// Failure handling: any failure (iOS, plugin init error, ML Kit throw,
/// plugin throw, transient OOM) returns a [LivenessFrameResult] with
/// `usable: false`. Callers MUST NOT hard-gate on `usable: false`; the
/// backend's MiniFASNet stays the authoritative check in that case.
class LivenessService {
  LivenessService({
    LivenessBackend? backend,
    this.threshold = 0.85,
  }) : _backend = backend ?? PluginLivenessBackend();

  final LivenessBackend _backend;

  /// Plugin score cutoff for "real". Matches the backend's
  /// `liveness_threshold = 0.85` (the self-scan default — the kiosk's
  /// stricter `public_attendance_liveness_threshold = 0.92` is enforced
  /// server-side regardless of what we do here).
  final double threshold;

  bool _initialized = false;
  bool _usable = false;

  /// `true` once [initialize] has been awaited at least once and the
  /// pipeline is ready to gate captures. Becomes `false` again after
  /// [dispose].
  bool get usable => _usable;

  /// Idempotent. Safe to call multiple times — only the first call hits the
  /// platform. Returns the current usability after the call.
  Future<bool> initialize() async {
    if (_initialized) return _usable;
    _initialized = true;
    _usable = await _backend.initialize();
    return _usable;
  }

  /// Run the pipeline against one camera frame. Returns
  /// [LivenessFrameResult.unavailable] (the safe default) when the pipeline
  /// isn't ready or anything throws. **Never throws** — the camera loop
  /// can't afford uncaught errors per frame.
  Future<LivenessFrameResult> analyze(
    Nv21Frame frame, {
    InputImageFormat format = InputImageFormat.nv21,
  }) async {
    if (!_usable) return const LivenessFrameResult.unavailable();
    if (frame.bytes.isEmpty) return const LivenessFrameResult.unavailable();

    List<Face> faces;
    try {
      faces = await _backend.detectFaces(_buildInputImage(frame, format));
    } catch (e, st) {
      debugPrint('LivenessService detectFaces failed: $e\n$st');
      return const LivenessFrameResult.transientError('Face detection failed');
    }

    if (faces.isEmpty) {
      return const LivenessFrameResult.empty();
    }

    // Pick the largest face — fastest path + strongest spoof signal.
    Face largest = faces.first;
    double largestArea = _area(largest.boundingBox);
    for (final f in faces.skip(1)) {
      final a = _area(f.boundingBox);
      if (a > largestArea) {
        largest = f;
        largestArea = a;
      }
    }

    double? score;
    try {
      score = await _backend.detectLiveness(
        yuvBytes: frame.bytes,
        previewWidth: frame.width,
        previewHeight: frame.height,
        orientation: frame.orientationDegrees,
        faceBox: largest.boundingBox,
      );
    } catch (e, st) {
      debugPrint('LivenessService detect failed: $e\n$st');
      return const LivenessFrameResult.transientError('Liveness check failed');
    }

    final isReal = score != null && score >= threshold;
    return LivenessFrameResult(
      usable: true,
      faces: [
        FaceCheck(
          boundingBox: largest.boundingBox,
          score: score,
          isReal: isReal,
          isLargest: true,
        ),
      ],
    );
  }

  /// Tear down the model. Safe to call without [initialize].
  Future<void> dispose() async {
    if (!_initialized) return;
    await _backend.destroy();
    _initialized = false;
    _usable = false;
  }

  InputImage _buildInputImage(Nv21Frame frame, InputImageFormat format) {
    return InputImage.fromBytes(
      bytes: frame.bytes,
      metadata: InputImageMetadata(
        size: Size(frame.width.toDouble(), frame.height.toDouble()),
        rotation: _rotationFor(frame.orientationDegrees),
        format: format,
        // NV21 has no explicit per-row stride — the Y plane is densely packed
        // at `width` bytes per row.
        bytesPerRow: frame.width,
      ),
    );
  }

  InputImageRotation _rotationFor(int degrees) {
    switch (degrees % 360) {
      case 0:
        return InputImageRotation.rotation0deg;
      case 90:
        return InputImageRotation.rotation90deg;
      case 180:
        return InputImageRotation.rotation180deg;
      case 270:
        return InputImageRotation.rotation270deg;
      default:
        return InputImageRotation.rotation0deg;
    }
  }

  double _area(Rect b) => (b.width.abs()) * (b.height.abs());
}

/// App-scoped instance. The native model holds ~10 MB and takes ~500 ms to
/// load on a cold start, so we keep it around for the session rather than
/// re-loading on every screen mount. Manual `dispose` only at app shutdown
/// (not currently wired — the OS reclaims it on process exit).
final livenessServiceProvider = Provider<LivenessService>((ref) {
  final service = LivenessService();
  ref.onDispose(() => service.dispose());
  return service;
});
