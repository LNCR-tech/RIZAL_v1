import 'dart:typed_data';
import 'dart:ui' show Rect;

import 'package:aura_app/features/liveness/application/liveness_service.dart';
import 'package:aura_app/features/liveness/domain/liveness_models.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

class _FakeBackend implements LivenessBackend {
  _FakeBackend({
    this.initResult = true,
    this.facesByCall = const <List<Face>>[],
    this.scoresByCall = const <double?>[],
    this.throwOnDetectFaces = false,
    this.throwOnDetectLiveness = false,
  });

  final bool initResult;
  final List<List<Face>> facesByCall;
  final List<double?> scoresByCall;
  final bool throwOnDetectFaces;
  final bool throwOnDetectLiveness;

  int initCalls = 0;
  int destroyCalls = 0;
  int detectFacesCalls = 0;
  int detectLivenessCalls = 0;

  @override
  Future<bool> initialize() async {
    initCalls++;
    return initResult;
  }

  @override
  Future<void> destroy() async {
    destroyCalls++;
  }

  @override
  Future<List<Face>> detectFaces(InputImage image) async {
    detectFacesCalls++;
    if (throwOnDetectFaces) throw Exception('boom');
    if (facesByCall.isEmpty) return const <Face>[];
    final idx = (detectFacesCalls - 1).clamp(0, facesByCall.length - 1);
    return facesByCall[idx];
  }

  @override
  Future<double?> detectLiveness({
    required Uint8List yuvBytes,
    required int previewWidth,
    required int previewHeight,
    required int orientation,
    required Rect faceBox,
  }) async {
    detectLivenessCalls++;
    if (throwOnDetectLiveness) throw Exception('boom');
    if (scoresByCall.isEmpty) return null;
    final idx = (detectLivenessCalls - 1).clamp(0, scoresByCall.length - 1);
    return scoresByCall[idx];
  }
}

Face _makeFace(Rect box) => Face(
      boundingBox: box,
      landmarks: const <FaceLandmarkType, FaceLandmark?>{},
      contours: const <FaceContourType, FaceContour?>{},
    );

Nv21Frame _makeFrame({int width = 64, int height = 48}) {
  // NV21: width*height Y bytes + (width*height)/2 interleaved VU bytes.
  return Nv21Frame(
    bytes: Uint8List(width * height * 3 ~/ 2),
    width: width,
    height: height,
    orientationDegrees: 90,
  );
}

void main() {
  group('LivenessService', () {
    test('initialize is idempotent and reflects backend availability', () async {
      final backend = _FakeBackend(initResult: false);
      final service = LivenessService(backend: backend);

      expect(service.usable, isFalse);
      expect(await service.initialize(), isFalse);
      expect(await service.initialize(), isFalse);
      expect(backend.initCalls, 1,
          reason: 'Second initialize() must NOT re-touch the platform.');
      expect(service.usable, isFalse);
    });

    test('initialize flips usable=true when the backend reports ready',
        () async {
      final service = LivenessService(backend: _FakeBackend(initResult: true));
      expect(await service.initialize(), isTrue);
      expect(service.usable, isTrue);
    });

    test('analyze returns unavailable when not initialized', () async {
      final service = LivenessService(backend: _FakeBackend());
      final result = await service.analyze(_makeFrame());
      expect(result.usable, isFalse);
      expect(result.faces, isEmpty);
    });

    test(
        'analyze returns unavailable when bytes are empty (defensive — '
        'caller should never pass zero-length frames)', () async {
      final backend = _FakeBackend(initResult: true);
      final service = LivenessService(backend: backend);
      await service.initialize();
      final result = await service.analyze(Nv21Frame(
        bytes: Uint8List(0),
        width: 0,
        height: 0,
        orientationDegrees: 0,
      ));
      expect(result.usable, isFalse);
      expect(backend.detectFacesCalls, 0,
          reason: 'Empty frames must short-circuit before hitting the plugin.');
    });

    test('analyze returns empty when no faces detected', () async {
      final backend = _FakeBackend(initResult: true);
      final service = LivenessService(backend: backend);
      await service.initialize();

      final result = await service.analyze(_makeFrame());
      expect(result.usable, isTrue);
      expect(result.hasAnyFace, isFalse);
      expect(result.isSpoof, isFalse,
          reason:
              'isSpoof must be false when usable=true but no faces are present.');
      expect(backend.detectLivenessCalls, 0,
          reason:
              'Liveness must NOT run when the detector returned zero faces.');
    });

    test('analyze picks the largest face and only runs liveness on it',
        () async {
      final small = _makeFace(const Rect.fromLTWH(10, 10, 20, 20));
      final large = _makeFace(const Rect.fromLTWH(100, 50, 200, 250));
      final tiny = _makeFace(const Rect.fromLTWH(5, 5, 8, 8));

      final backend = _FakeBackend(
        initResult: true,
        facesByCall: [
          [small, large, tiny]
        ],
        scoresByCall: const [0.91],
      );
      final service = LivenessService(backend: backend, threshold: 0.85);
      await service.initialize();

      final result = await service.analyze(_makeFrame());
      expect(result.usable, isTrue);
      expect(result.faces, hasLength(1),
          reason:
              'Multi-face frames return a single FaceCheck for the largest face.');
      expect(result.faces.first.isLargest, isTrue);
      expect(result.faces.first.boundingBox, large.boundingBox);
      expect(result.anyReal, isTrue);
      expect(result.isSpoof, isFalse);
      expect(backend.detectLivenessCalls, 1,
          reason: 'Multi-face frames must NOT fan out one liveness call per face.');
    });

    test('score below threshold flags the frame as spoof', () async {
      final face = _makeFace(const Rect.fromLTWH(50, 50, 200, 200));
      final backend = _FakeBackend(
        initResult: true,
        facesByCall: [
          [face]
        ],
        scoresByCall: const [0.42],
      );
      final service = LivenessService(backend: backend, threshold: 0.85);
      await service.initialize();

      final result = await service.analyze(_makeFrame());
      expect(result.anyReal, isFalse);
      expect(result.isSpoof, isTrue,
          reason:
              'A face in the frame with a low confidence MUST be reported as spoof so the caller can hard-gate.');
    });

    test('score equal to threshold counts as real (>= comparison)', () async {
      final face = _makeFace(const Rect.fromLTWH(50, 50, 200, 200));
      final backend = _FakeBackend(
        initResult: true,
        facesByCall: [
          [face]
        ],
        scoresByCall: const [0.85],
      );
      final service = LivenessService(backend: backend, threshold: 0.85);
      await service.initialize();

      final result = await service.analyze(_makeFrame());
      expect(result.anyReal, isTrue);
    });

    test('null score does NOT flag as spoof (treat as unknown)', () async {
      final face = _makeFace(const Rect.fromLTWH(50, 50, 200, 200));
      final backend = _FakeBackend(
        initResult: true,
        facesByCall: [
          [face]
        ],
        scoresByCall: const [null],
      );
      final service = LivenessService(backend: backend, threshold: 0.85);
      await service.initialize();

      final result = await service.analyze(_makeFrame());
      expect(result.faces.single.score, isNull);
      expect(result.faces.single.isReal, isFalse);
      expect(result.isSpoof, isTrue,
          reason:
              'Null score with a face present means we have no real signal — '
              'the frame should be blocked rather than nodded through. Backend '
              'still validates server-side either way.');
    });

    test('detectFaces throw becomes a transient error, not a thrown exception',
        () async {
      final service = LivenessService(
        backend: _FakeBackend(initResult: true, throwOnDetectFaces: true),
      );
      await service.initialize();
      final result = await service.analyze(_makeFrame());
      expect(result.usable, isFalse,
          reason:
              'Transient error → usable=false so the caller does NOT hard-gate '
              'on stale data (backend stays the authoritative check).');
      expect(result.error, isNotNull);
    });

    test('detectLiveness throw becomes a transient error', () async {
      final face = _makeFace(const Rect.fromLTWH(50, 50, 200, 200));
      final service = LivenessService(
        backend: _FakeBackend(
          initResult: true,
          facesByCall: [
            [face]
          ],
          throwOnDetectLiveness: true,
        ),
      );
      await service.initialize();
      final result = await service.analyze(_makeFrame());
      expect(result.usable, isFalse);
      expect(result.error, isNotNull);
    });

    test('dispose is safe without prior initialize', () async {
      final backend = _FakeBackend();
      final service = LivenessService(backend: backend);
      await service.dispose();
      expect(backend.destroyCalls, 0,
          reason:
              'dispose() without initialize() must NOT touch the platform — '
              'otherwise it leaves the plugin in a confused state.');
    });

    test('dispose flips usable=false and releases the backend', () async {
      final backend = _FakeBackend(initResult: true);
      final service = LivenessService(backend: backend);
      await service.initialize();
      expect(service.usable, isTrue);
      await service.dispose();
      expect(service.usable, isFalse);
      expect(backend.destroyCalls, 1);
    });
  });

  group('LivenessFrameResult', () {
    test('isSpoof requires usable=true AND at least one face', () {
      expect(const LivenessFrameResult.unavailable().isSpoof, isFalse);
      expect(const LivenessFrameResult.empty().isSpoof, isFalse,
          reason:
              'No face on-device is NOT a spoof — the operator may be framing.');
    });
  });
}
