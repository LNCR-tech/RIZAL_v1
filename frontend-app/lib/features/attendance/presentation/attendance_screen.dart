import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/services/geolocation_service.dart';
import '../../../core/theme/app_motion.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/event.dart';
import '../../liveness/application/liveness_service.dart';
import '../../liveness/application/nv21_codec.dart';
import '../../liveness/domain/liveness_models.dart';
import '../application/attendance_scan_flow.dart';
import '../data/attendance_repository.dart';
import 'attendance_result_sheet.dart';

/// Face-scan attendance: front-camera capture + geolocation → backend.
///
/// When on-device liveness is available (Android, model loaded) this screen
/// also runs a continuous preflight in image-stream mode: every ~160 ms a
/// frame is fed through ML Kit + the Silent-Face-Anti-Spoof model and the
/// capture button is **disabled** while the model says the visible face is
/// a spoof. When the pipeline is unavailable (iOS, model load failure,
/// transient errors), the screen falls back to the original
/// `takePicture`-only flow and the backend stays the source of truth.
class AttendanceScreen extends ConsumerStatefulWidget {
  const AttendanceScreen({super.key, required this.event});
  final AppEvent event;

  @override
  ConsumerState<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends ConsumerState<AttendanceScreen>
    with WidgetsBindingObserver {
  CameraController? _controller;
  CameraDescription? _cameraDesc;
  bool _initializing = true;
  bool _submitting = false;
  bool _livenessUsable = false;
  bool _streaming = false;
  String? _error;
  String? _cameraError;

  LivenessFrameResult _lastCheck = const LivenessFrameResult.unavailable();
  DateTime _lastAnalyzedAt = DateTime.fromMillisecondsSinceEpoch(0);
  bool _analyzing = false;

  // Throttle on-device preflight to ~6 fps. The native model can run faster
  // but a higher rate doesn't change the UX (the status pill only flips
  // every few hundred ms anyway) and burns CPU/battery for nothing.
  static const Duration _analyzePeriod = Duration(milliseconds: 160);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initCamera();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _stopStreamIfRunning();
    _controller?.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    // Pause the stream when the user backgrounds the app. Letting the
    // camera + ML Kit run unobserved in the background wastes battery and
    // can trip OEM "app drained battery" warnings.
    if (state != AppLifecycleState.resumed && _streaming) {
      _stopStreamIfRunning();
    }
  }

  Future<void> _initCamera() async {
    try {
      final livenessReady = await ref
          .read(livenessServiceProvider)
          .initialize();
      if (!mounted) return;

      final cams = await availableCameras();
      if (cams.isEmpty) {
        setState(() {
          _cameraError = 'No camera found on this device.';
          _initializing = false;
        });
        return;
      }
      final desc = cams.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => cams.first,
      );

      // On Android we need NV21 directly to feed both ML Kit and the
      // anti-spoof plugin. On iOS / when liveness isn't usable, the JPEG
      // path matches the historical capture mode and saves a stream we
      // wouldn't use anyway.
      final fmt = livenessReady
          ? ImageFormatGroup.nv21
          : ImageFormatGroup.jpeg;

      final controller = CameraController(
        desc,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: fmt,
      );
      await controller.initialize();
      if (!mounted) {
        await controller.dispose();
        return;
      }

      setState(() {
        _controller = controller;
        _cameraDesc = desc;
        _livenessUsable = livenessReady;
        _initializing = false;
      });

      if (livenessReady) {
        await _startStream();
      }
    } catch (e, st) {
      debugPrint('Attendance camera init failed: $e\n$st');
      if (mounted) {
        setState(() {
          _cameraError =
              'Camera unavailable. Please grant camera permission and try again.';
          _initializing = false;
        });
      }
    }
  }

  Future<void> _startStream() async {
    final controller = _controller;
    if (controller == null || _streaming) return;
    try {
      await controller.startImageStream(_onFrame);
      _streaming = true;
    } catch (e, st) {
      debugPrint('Attendance startImageStream failed: $e\n$st');
      // Live preflight is now unavailable but the camera still works for
      // takePicture. Fall through to backend-only.
      if (mounted) setState(() => _livenessUsable = false);
    }
  }

  Future<void> _stopStreamIfRunning() async {
    final controller = _controller;
    if (controller == null || !_streaming) return;
    _streaming = false;
    try {
      await controller.stopImageStream();
    } catch (_) {
      // Plugin throws if it's already stopped or if we disposed mid-stream
      // — both are recoverable, ignore.
    }
  }

  void _onFrame(CameraImage image) {
    if (_analyzing || _submitting) return;
    final now = DateTime.now();
    if (now.difference(_lastAnalyzedAt) < _analyzePeriod) return;
    _lastAnalyzedAt = now;
    _analyzing = true;
    _analyze(image);
  }

  Future<void> _analyze(CameraImage image) async {
    try {
      final desc = _cameraDesc;
      if (desc == null) return;
      final frame = buildNv21FrameFromCamera(
        image,
        sensorOrientationDegrees: desc.sensorOrientation,
      );
      if (frame == null) {
        if (mounted) {
          setState(() =>
              _lastCheck = const LivenessFrameResult.unavailable());
        }
        return;
      }
      final result =
          await ref.read(livenessServiceProvider).analyze(frame);
      if (mounted) setState(() => _lastCheck = result);
    } catch (e, st) {
      debugPrint('Attendance analyze failed: $e\n$st');
    } finally {
      _analyzing = false;
    }
  }

  bool get _blockedBySpoof =>
      _livenessUsable &&
      _lastCheck.usable &&
      _lastCheck.hasAnyFace &&
      !_lastCheck.anyReal;

  Future<void> _capture() async {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized || _submitting) {
      return;
    }
    if (_blockedBySpoof) {
      setState(() => _error =
          'Looks like a photo or video — hold a real face steady, then try again.');
      HapticFeedback.heavyImpact();
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      // Stop the live preflight stream before takePicture (the camera plugin
      // requires exclusive mode on Android). We don't restart it after —
      // capture succeeds or fails, then we pop back.
      await _stopStreamIfRunning();

      final geo = await ref.read(geolocationServiceProvider).current();
      validateAttendanceScanLocation(event: widget.event, geo: geo);
      final shot = await controller.takePicture();
      final bytes = await shot.readAsBytes();
      final request = buildAttendanceScanRequest(
        event: widget.event,
        imageBytes: bytes,
        geo: geo,
      );
      final result = await ref.read(attendanceRepositoryProvider).faceScan(
            eventId: request.eventId,
            imageBase64: request.imageBase64,
            latitude: request.latitude,
            longitude: request.longitude,
            accuracyM: request.accuracyM,
          );
      if (!mounted) return;
      HapticFeedback.mediumImpact();
      await showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        backgroundColor: Colors.transparent,
        builder: (_) => AttendanceResultSheet(result: result),
      );
      if (mounted) Navigator.of(context).pop();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } on AttendanceScanFlowError catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Could not record attendance. Please try again.');
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        foregroundColor: Colors.white,
        elevation: 0,
        title: Text(widget.event.name,
            maxLines: 1, overflow: TextOverflow.ellipsis),
      ),
      body: _body(),
    );
  }

  Widget _body() {
    if (_initializing) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_cameraError != null) {
      return Center(
        child: ErrorView(
          message: _cameraError!,
          onRetry: () {
            setState(() {
              _initializing = true;
              _cameraError = null;
            });
            _initCamera();
          },
        ),
      );
    }

    final t = AppTokens.of(context);
    return Stack(
      fit: StackFit.expand,
      children: [
        _CameraFill(controller: _controller!),
        Container(color: Colors.black.withOpacity(0.18)),
        Center(
          child: AnimatedContainer(
            duration: AppMotion.modal,
            curve: AppMotion.easeOut,
            width: 240,
            height: 300,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(150),
              border: Border.all(
                color: _ringColor(t),
                width: 3,
              ),
            ),
          ),
        ),
        SafeArea(
          child: Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(
                  AppSpacing.x24, 0, AppSpacing.x24, AppSpacing.x32),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (_error != null) ...[
                    _ErrorPill(_error!),
                    const SizedBox(height: AppSpacing.x16),
                  ],
                  if (_livenessUsable) ...[
                    _LivenessStatusPill(check: _lastCheck),
                    const SizedBox(height: AppSpacing.x12),
                  ],
                  Text(
                    _livenessUsable
                        ? 'Hold steady — we verify before sending'
                        : 'Center your face, then tap to scan',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white, fontSize: 15),
                  ),
                  const SizedBox(height: AppSpacing.x16),
                  _CaptureButton(
                    accent: t.accent,
                    busy: _submitting,
                    disabled: _blockedBySpoof,
                    onTap: _capture,
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Color _ringColor(AppTokens t) {
    if (!_livenessUsable || !_lastCheck.usable) {
      return Colors.white.withOpacity(0.85);
    }
    if (!_lastCheck.hasAnyFace) return Colors.white.withOpacity(0.5);
    if (_lastCheck.anyReal) return t.present;
    return t.absent;
  }
}

class _CameraFill extends StatelessWidget {
  const _CameraFill({required this.controller});
  final CameraController controller;

  @override
  Widget build(BuildContext context) {
    final size = controller.value.previewSize ?? const Size(720, 1280);
    return ClipRect(
      child: FittedBox(
        fit: BoxFit.cover,
        child: SizedBox(
          width: size.height,
          height: size.width,
          child: CameraPreview(controller),
        ),
      ),
    );
  }
}

/// Real-time on-device liveness status. Cross-fades between states with a
/// short ease-out (never ease-in — feels sluggish). Doesn't render when
/// the pipeline is unavailable — the operator never sees a confusing
/// "Looking…" with no follow-up.
class _LivenessStatusPill extends StatelessWidget {
  const _LivenessStatusPill({required this.check});
  final LivenessFrameResult check;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final spec = _spec(t, check);
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    return AnimatedSwitcher(
      duration: reduce ? Duration.zero : const Duration(milliseconds: 220),
      switchInCurve: AppMotion.easeOut,
      transitionBuilder: (child, anim) {
        // Scale from 0.94 (not 0) + fade — emil.
        return FadeTransition(
          opacity: anim,
          child: ScaleTransition(
            scale: Tween<double>(begin: 0.94, end: 1.0).animate(anim),
            child: child,
          ),
        );
      },
      child: Container(
        key: ValueKey(spec.label),
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x16, vertical: AppSpacing.x8),
        decoration: BoxDecoration(
          color: spec.bg,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: Colors.white.withOpacity(0.08)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(spec.icon, size: 16, color: spec.fg),
            const SizedBox(width: 6),
            Text(
              spec.label,
              style: TextStyle(
                color: spec.fg,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.1,
              ),
            ),
          ],
        ),
      ),
    );
  }

  _PillSpec _spec(AppTokens t, LivenessFrameResult c) {
    if (!c.usable) {
      return const _PillSpec(
        label: 'Verifying…',
        icon: Icons.hourglass_top_rounded,
        fg: Colors.white,
        bg: Color(0x99000000),
      );
    }
    if (!c.hasAnyFace) {
      return _PillSpec(
        label: 'Looking for your face',
        icon: Icons.center_focus_weak_rounded,
        fg: Colors.white,
        bg: Colors.black.withOpacity(0.55),
      );
    }
    if (c.anyReal) {
      return _PillSpec(
        label: 'Real face — ready to scan',
        icon: Icons.verified_rounded,
        fg: Colors.white,
        bg: t.present,
      );
    }
    return _PillSpec(
      label: 'Possible spoof — adjust',
      icon: Icons.gpp_bad_rounded,
      fg: Colors.white,
      bg: t.absent,
    );
  }
}

class _PillSpec {
  const _PillSpec({
    required this.label,
    required this.icon,
    required this.fg,
    required this.bg,
  });
  final String label;
  final IconData icon;
  final Color fg;
  final Color bg;
}

class _CaptureButton extends StatelessWidget {
  const _CaptureButton({
    required this.accent,
    required this.busy,
    required this.disabled,
    required this.onTap,
  });
  final Color accent;
  final bool busy;
  final bool disabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isBlocked = disabled && !busy;
    return Semantics(
      button: true,
      label: 'Capture',
      enabled: !busy && !disabled,
      child: AnimatedOpacity(
        duration: AppMotion.modal,
        opacity: isBlocked ? 0.55 : 1.0,
        child: GestureDetector(
          onTap: busy ? null : onTap,
          child: Container(
            width: 78,
            height: 78,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.white,
              border: Border.all(
                color: isBlocked ? Colors.white.withOpacity(0.4) : accent,
                width: 5,
              ),
            ),
            child: busy
                ? Padding(
                    padding: const EdgeInsets.all(20),
                    child: CircularProgressIndicator(
                        strokeWidth: 3, color: accent),
                  )
                : Icon(
                    isBlocked
                        ? Icons.lock_outline_rounded
                        : Icons.camera_alt_rounded,
                    color: Colors.black,
                    size: 30,
                  ),
          ),
        ),
      ),
    );
  }
}

class _ErrorPill extends StatelessWidget {
  const _ErrorPill(this.message);
  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x16, vertical: AppSpacing.x12),
      decoration: BoxDecoration(
        color: const Color(0xFFEF4444).withOpacity(0.92),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Text(
        message,
        textAlign: TextAlign.center,
        style: const TextStyle(color: Colors.white, fontSize: 14),
      ),
    );
  }
}
