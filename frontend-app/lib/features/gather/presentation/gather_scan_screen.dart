import 'dart:convert';

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/services/geolocation_service.dart';
import '../../../core/theme/app_motion.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../shared/models/public_attendance.dart';
import '../../liveness/application/liveness_service.dart';
import '../../liveness/application/nv21_codec.dart';
import '../../liveness/domain/liveness_models.dart';
import '../data/public_attendance_repository.dart';
import 'widgets/gather_outcome_tile.dart';
import 'widgets/gather_phase_pill.dart';
import 'widgets/gather_scanning_ring.dart';
import 'widgets/gather_status_chip.dart';
import 'widgets/gather_summary_sheet.dart';

/// Multi-face check-in kiosk. The operator points the back camera at the
/// room; the loop captures a frame every cooldown-many seconds, posts it to
/// the public face attendance endpoint, and renders every outcome (successes
/// and rejections) in a live log.
class GatherScanScreen extends ConsumerStatefulWidget {
  const GatherScanScreen(
      {super.key, required this.event, required this.cooldownSeconds});

  final NearbyEvent event;

  /// Server-suggested cooldown between scans. Clamped at the loop boundary so
  /// a misbehaving backend can't burn the camera at 0s.
  final int cooldownSeconds;

  @override
  ConsumerState<GatherScanScreen> createState() => _GatherScanScreenState();
}

class _GatherScanScreenState extends ConsumerState<GatherScanScreen>
    with WidgetsBindingObserver {
  // Pipeline state
  CameraController? _controller;
  CameraDescription? _cameraDesc;
  bool _initializing = true;
  String? _cameraError;
  String? _locationError;
  GeoFix? _fix;

  // On-device liveness
  bool _livenessUsable = false;
  bool _streaming = false;
  Nv21Frame? _latestFrame;

  // Loop state
  bool _running = false;
  bool _busy = false;
  String? _error;
  GatherStatus _status = GatherStatus.standby;
  GeoStatus? _serverGeo;

  // Session state
  final Set<String> _seen = {};
  final List<ScanOutcome> _log = [];
  ScanOutcome? _lastSuccess;
  DateTime? _sessionStart;
  int _signIns = 0;
  int _signOuts = 0;
  int _spoofs = 0;
  int _outOfScope = 0;

  int get _count => _signIns + _signOuts;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _init();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _running = false;
    _stopStreamIfRunning();
    _controller?.dispose();
    // Best-effort: if wakelock was on, release it. Errors swallowed since the
    // user is leaving the screen anyway and we can't show a snackbar.
    WakelockPlus.disable().catchError((_) {});
    super.dispose();
  }

  Future<void> _stopStreamIfRunning() async {
    final controller = _controller;
    if (controller == null || !_streaming) return;
    _streaming = false;
    try {
      await controller.stopImageStream();
    } catch (_) {
      // Already stopped or disposed mid-stream — both recoverable.
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    // If the app is backgrounded while running, pause the loop. We can't
    // resume the camera reliably without a re-init, so on resume the operator
    // taps Start again.
    if (state != AppLifecycleState.resumed && _running) {
      _stopLoop(showSummary: false);
    }
  }

  Future<void> _init() async {
    try {
      final livenessReady =
          await ref.read(livenessServiceProvider).initialize();
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
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cams.first,
      );

      // When on-device liveness is available we stream NV21 frames straight
      // out of the camera; otherwise we keep the historical JPEG/takePicture
      // path so the kiosk still functions (iOS, devices without the model,
      // anything that fails plugin init).
      final fmt = livenessReady
          ? ImageFormatGroup.nv21
          : ImageFormatGroup.jpeg;
      final preset = livenessReady
          // Medium is enough for face matching at conference distances and
          // halves stream throughput vs high — the backend auto-downscales
          // to 1280 px regardless.
          ? ResolutionPreset.medium
          : ResolutionPreset.high;

      final controller = CameraController(
        desc,
        preset,
        enableAudio: false,
        imageFormatGroup: fmt,
      );
      await controller.initialize();
      final fix = await ref.read(geolocationServiceProvider).current();
      if (!mounted) {
        await controller.dispose();
        return;
      }
      setState(() {
        _controller = controller;
        _cameraDesc = desc;
        _fix = fix;
        _livenessUsable = livenessReady;
        _initializing = false;
        _locationError = fix == null
            ? 'Location unavailable. Enable Location Services and re-open Gather.'
            : null;
      });

      if (livenessReady) {
        await _startStream();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _cameraError =
              'Camera unavailable. Grant camera permission and try again.';
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
      debugPrint('Gather startImageStream failed: $e\n$st');
      // Fall through to takePicture mode — the kiosk still works without
      // the on-device gate, the backend stays authoritative.
      if (mounted) setState(() => _livenessUsable = false);
    }
  }

  /// Stream callback — keep only the latest frame, drop older ones. This is
  /// hot path: do as little work as possible here; the heavy lifting
  /// (face detect + liveness + encode) happens in `_scanOnce`.
  void _onFrame(CameraImage image) {
    final desc = _cameraDesc;
    if (desc == null) return;
    final frame = buildNv21FrameFromCamera(
      image,
      sensorOrientationDegrees: desc.sensorOrientation,
    );
    if (frame == null) {
      // Device handed us a non-NV21 frame (some OEMs ignore the format
      // hint). Disable the on-device gate but leave the stream running for
      // smoother preview — `_scanOnce` will fall back to takePicture-like
      // behavior via the !_livenessUsable branch.
      if (_livenessUsable && mounted) {
        setState(() => _livenessUsable = false);
      }
      return;
    }
    _latestFrame = frame;
  }

  void _toggle() {
    if (_running) {
      _stopLoop(showSummary: true);
    } else {
      _startLoop();
    }
  }

  void _startLoop() {
    if (_fix == null) {
      setState(() => _locationError =
          'Location unavailable. Enable Location Services and re-open Gather.');
      return;
    }
    setState(() {
      _running = true;
      _error = null;
      _status = GatherStatus.scanning;
      _sessionStart ??= DateTime.now();
    });
    WakelockPlus.enable().catchError((_) {});
    _loop();
  }

  Future<void> _stopLoop({required bool showSummary}) async {
    setState(() {
      _running = false;
      _status = GatherStatus.standby;
    });
    await WakelockPlus.disable().catchError((_) {});
    if (showSummary && _count > 0 && mounted) {
      await GatherSummarySheet.show(
        context,
        eventName: widget.event.name,
        stats: _stats(),
        onDone: () {
          if (mounted) Navigator.of(context).maybePop();
        },
        onResume: () {
          if (mounted) _startLoop();
        },
      );
    }
  }

  GatherSessionStats _stats() {
    final start = _sessionStart ?? DateTime.now();
    return GatherSessionStats(
      signIns: _signIns,
      signOuts: _signOuts,
      spoofs: _spoofs,
      outOfScope: _outOfScope,
      duration: DateTime.now().difference(start),
      recent:
          _log.where((o) => o.isSuccess).toList(growable: false),
    );
  }

  Future<void> _loop() async {
    while (_running && mounted) {
      await _scanOnce();
      if (!_running || !mounted) break;
      await Future.delayed(
          Duration(seconds: widget.cooldownSeconds.clamp(2, 15)));
    }
  }

  Future<void> _scanOnce() async {
    final controller = _controller;
    final fix = _fix;
    if (controller == null || !controller.value.isInitialized || _busy) return;
    if (fix == null) {
      setState(() => _locationError = 'Location unavailable.');
      return;
    }
    _busy = true;
    try {
      final bytes = await _gateAndCaptureBytes(controller);
      if (bytes == null) return; // Local fast-fail handled inside the helper.

      final res = await ref.read(publicAttendanceRepositoryProvider).multiScan(
            eventId: widget.event.id,
            imageBase64: base64Encode(bytes),
            latitude: fix.latitude,
            longitude: fix.longitude,
            accuracyM: fix.accuracy,
            cooldownStudentIds: _seen.toList(),
          );
      if (!mounted) return;
      _ingest(res);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Scan failed — retrying…');
    } finally {
      _busy = false;
    }
  }

  /// Returns the JPEG bytes to POST for this cycle, or `null` when the
  /// on-device gate decided this frame shouldn't be sent (spoof detected
  /// locally, or no face visible in the frame). Side effects: updates the
  /// status chip and the local spoof counter for the spoof case so the UI
  /// reflects the local rejection.
  Future<Uint8List?> _gateAndCaptureBytes(CameraController controller) async {
    // Path A — on-device gate available: analyse the latest streamed frame,
    // skip the POST on spoof / empty frame, otherwise encode YUV → JPEG and
    // send.
    if (_livenessUsable) {
      final frame = _latestFrame;
      if (frame == null) {
        // Stream hasn't produced a frame yet (the loop fired faster than the
        // camera warm-up). Skip this cycle — next one will hit.
        return null;
      }
      final check = await ref.read(livenessServiceProvider).analyze(frame);

      if (check.isSpoof) {
        _logLocalSpoof(check);
        return null;
      }
      if (check.usable && !check.hasAnyFace) {
        // No face on-device → no point hitting the backend. Quietly skip.
        return null;
      }
      // Real face (or pipeline returned `unavailable` for this frame — treat
      // as "send and let backend decide"). Encode and send.
      return encodeNv21ToJpeg(frame);
    }

    // Path B — pipeline unavailable (iOS / model load failed). Fall back to
    // the original takePicture flow; backend stays authoritative.
    final shot = await controller.takePicture();
    return shot.readAsBytes();
  }

  /// Synthesize a local-spoof outcome so the live log + bento + status chip
  /// reflect that the frame was rejected before it ever left the device.
  /// Mirrors the backend's `liveness_failed` action so the rest of the UI
  /// pipeline ([_log], [_spoofs], summary sheet) needs no special cases.
  void _logLocalSpoof(LivenessFrameResult check) {
    final score = check.faces.isEmpty ? null : check.faces.first.score;
    final outcome = ScanOutcome(
      action: 'liveness_failed',
      reasonCode: 'spoof_detected_on_device',
      message: 'Local on-device anti-spoof rejected this frame.',
      liveness: Liveness(
        label: 'Fake',
        score: score,
        reason: 'on_device_check',
      ),
    );
    setState(() {
      _spoofs++;
      _status = GatherStatus.spoof;
      _log.insert(0, outcome);
      if (_log.length > 40) _log.removeRange(40, _log.length);
    });
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    SystemSound.play(SystemSoundType.alert);
    if (!reduce) HapticFeedback.heavyImpact();
  }

  void _ingest(MultiScanResult res) {
    GatherStatus next = _running ? GatherStatus.scanning : GatherStatus.standby;
    final additions = <ScanOutcome>[];
    var madeSuccess = false;
    var madeSpoof = false;

    for (final o in res.outcomes) {
      // Don't pollute the log with frame-internal noise; "duplicate_face" and
      // "cooldown_skipped" are the loop doing its job, not user-facing events.
      if (o.isDuplicate || o.isCooldownSkipped) continue;

      // Counters first (every outcome counts toward session stats).
      if (o.isSignIn) {
        _signIns++;
        madeSuccess = true;
        if (o.studentId != null) _seen.add(o.studentId!);
        _lastSuccess = o;
      } else if (o.isSignOut) {
        _signOuts++;
        madeSuccess = true;
        if (o.studentId != null) _seen.add(o.studentId!);
        _lastSuccess = o;
      } else if (o.isLivenessFailed) {
        _spoofs++;
        madeSpoof = true;
      } else if (o.isOutOfScope || o.isNoMatch) {
        _outOfScope++;
      }

      additions.add(o);
    }

    // Pick the most "important" status for the chip — verified beats spoof
    // beats bypassed beats out-of-scope. (A frame with a real verified match
    // shouldn't be downgraded by a spoof attempt in the same frame; the
    // attendance result is what matters.)
    final hasReal = res.outcomes.any((o) =>
        o.isSuccess && (o.liveness?.isReal ?? false));
    final hasBypassed = res.outcomes
        .any((o) => o.isSuccess && (o.liveness?.isBypassed ?? false));
    final hasSpoof = res.outcomes.any((o) => o.isLivenessFailed);
    final hasOOS = res.outcomes
        .every((o) => o.isOutOfScope || o.isNoMatch || o.isDuplicate);
    if (hasReal) {
      next = GatherStatus.verified;
    } else if (hasBypassed) {
      next = GatherStatus.bypassed;
    } else if (hasSpoof) {
      next = GatherStatus.spoof;
    } else if (res.outcomes.isNotEmpty && hasOOS) {
      next = GatherStatus.outOfScope;
    }

    setState(() {
      _error = null;
      _serverGeo = res.geo;
      _status = next;
      for (final o in additions.reversed) {
        // Newest first; the list head is shown.
        _log.insert(0, o);
      }
      if (_log.length > 40) _log.removeRange(40, _log.length);
    });

    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (madeSuccess) {
      SystemSound.play(SystemSoundType.click);
      if (!reduce) HapticFeedback.lightImpact();
    } else if (madeSpoof) {
      SystemSound.play(SystemSoundType.alert);
      if (!reduce) HapticFeedback.heavyImpact();
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light.copyWith(
        statusBarColor: Colors.transparent,
        systemNavigationBarColor: Colors.black,
        systemNavigationBarIconBrightness: Brightness.light,
      ),
      child: Scaffold(
        backgroundColor: Colors.black,
        body: SafeArea(
          bottom: false,
          child: _body(t),
        ),
      ),
    );
  }

  Widget _body(AppTokens t) {
    if (_initializing) {
      return Center(child: CircularProgressIndicator(color: t.accent));
    }
    if (_cameraError != null) {
      return _ErrorState(
        title: 'Camera unavailable',
        message: _cameraError!,
        onPop: () => Navigator.of(context).maybePop(),
      );
    }

    return Column(
      children: [
        _KioskHeader(
          event: widget.event,
          onPop: () async {
            if (_running) {
              await _stopLoop(showSummary: true);
            } else if (mounted) {
              Navigator.of(context).maybePop();
            }
          },
        ),
        Expanded(
          flex: 6,
          child: Stack(
            fit: StackFit.expand,
            children: [
              _cameraFill(_controller!),
              GatherFramingBrackets(
                color: Colors.white.withOpacity(0.55),
              ),
              GatherScanningRing(
                color: _status == GatherStatus.spoof
                    ? t.absent
                    : t.accent,
                active: _running,
                size: 240,
              ),
              // Status chip — top centre, animated state swap
              Positioned(
                top: AppSpacing.x16,
                left: 0,
                right: 0,
                child: Center(
                  child: GatherStatusChip(status: _status),
                ),
              ),
              // Geofence + accuracy — top right, mono
              if (_serverGeo != null)
                Positioned(
                  top: AppSpacing.x16,
                  right: AppSpacing.x16,
                  child: _GeoBadge(geo: _serverGeo!),
                ),
              // Last recognized — bottom left, fades while still visible
              if (_lastSuccess != null)
                Positioned(
                  left: AppSpacing.x16,
                  right: AppSpacing.x16,
                  bottom: AppSpacing.x16,
                  child: _LastRecognized(outcome: _lastSuccess!),
                ),
            ],
          ),
        ),
        _BottomBento(
          running: _running,
          count: _count,
          signIns: _signIns,
          signOuts: _signOuts,
          spoofs: _spoofs,
          outOfScope: _outOfScope,
          log: _log,
          error: _error ?? _locationError,
          onToggle: _toggle,
        ),
      ],
    );
  }

  Widget _cameraFill(CameraController c) {
    final size = c.value.previewSize ?? const Size(720, 1280);
    return ClipRect(
      child: FittedBox(
        fit: BoxFit.cover,
        child: SizedBox(
          width: size.height,
          height: size.width,
          child: CameraPreview(c),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Kiosk top header — back chevron, event name, phase pill, scope chip.
// Reads on a dark surface (the camera fills the rest), so tokens that
// normally render on light surface are swapped for white-on-black here.
// ─────────────────────────────────────────────────────────────────────────
class _KioskHeader extends StatelessWidget {
  const _KioskHeader({required this.event, required this.onPop});
  final NearbyEvent event;
  final VoidCallback onPop;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.fromLTRB(
          AppSpacing.x8, AppSpacing.x8, AppSpacing.x16, AppSpacing.x12),
      child: Row(
        children: [
          IconButton(
            tooltip: 'Close kiosk',
            icon: const Icon(Icons.arrow_back_ios_new_rounded,
                color: Colors.white),
            onPressed: onPop,
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  event.name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: textTheme.titleLarge
                      ?.copyWith(color: Colors.white, height: 1.1),
                ),
                if (event.location != null)
                  Text(
                    event.location!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: textTheme.bodySmall
                        ?.copyWith(color: Colors.white.withOpacity(0.7)),
                  ),
              ],
            ),
          ),
          GatherPhasePill(event: event, dense: true),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Top-right geofence indicator. Inside = small green dot + "in"; outside
// shows the reason from the server (e.g. "outside_geofence").
// ─────────────────────────────────────────────────────────────────────────
class _GeoBadge extends StatelessWidget {
  const _GeoBadge({required this.geo});
  final GeoStatus geo;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final ok = geo.ok;
    final label = ok
        ? 'In geofence'
        : (geo.reason ?? 'Outside geofence').replaceAll('_', ' ');
    final accuracy = geo.accuracyM;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.55),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: ok ? t.present : t.absent,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            label,
            style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w600,
                fontSize: 12),
          ),
          if (accuracy != null) ...[
            const SizedBox(width: 8),
            Text(
              '±${accuracy.round()}m',
              style: AppTypography.mono(
                  size: 11,
                  weight: FontWeight.w600,
                  color: Colors.white.withOpacity(0.8)),
            ),
          ],
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Bottom-left "last recognized" feedback. Fades in via AnimatedSwitcher
// when the value changes.
// ─────────────────────────────────────────────────────────────────────────
class _LastRecognized extends StatelessWidget {
  const _LastRecognized({required this.outcome});
  final ScanOutcome outcome;

  @override
  Widget build(BuildContext context) {
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return AnimatedSwitcher(
      duration: reduce ? Duration.zero : AppMotion.modal,
      reverseDuration: AppMotion.exit,
      switchInCurve: AppMotion.easeOut,
      transitionBuilder: (child, anim) {
        // Asymmetric: scale from 0.94 (not 0) + fade — emil.
        return FadeTransition(
          opacity: anim,
          child: ScaleTransition(
            scale: Tween<double>(begin: 0.94, end: 1.0).animate(anim),
            child: child,
          ),
        );
      },
      child: GatherOutcomeTile(
        key: ValueKey(outcome.attendanceId ?? outcome.studentId),
        outcome: outcome,
        onSurfaceColor: Colors.white,
        dense: true,
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Bottom bento — big count, breakdown chips, recent log, start/stop CTA.
// ─────────────────────────────────────────────────────────────────────────
class _BottomBento extends StatelessWidget {
  const _BottomBento({
    required this.running,
    required this.count,
    required this.signIns,
    required this.signOuts,
    required this.spoofs,
    required this.outOfScope,
    required this.log,
    required this.error,
    required this.onToggle,
  });

  final bool running;
  final int count;
  final int signIns;
  final int signOuts;
  final int spoofs;
  final int outOfScope;
  final List<ScanOutcome> log;
  final String? error;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius:
            const BorderRadius.vertical(top: Radius.circular(AppRadii.sheet)),
      ),
      padding: const EdgeInsets.fromLTRB(
          AppSpacing.x20, AppSpacing.x20, AppSpacing.x20, AppSpacing.x16),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 280,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Hero counter + CTA
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '$count',
                    style: AppTypography.mono(
                        size: 44,
                        weight: FontWeight.w800,
                        color: t.ink),
                  ),
                  const SizedBox(width: AppSpacing.x8),
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Text(
                      count == 1 ? 'recorded' : 'recorded',
                      style: textTheme.bodyMedium
                          ?.copyWith(color: t.textSecondary),
                    ),
                  ),
                  const Spacer(),
                  AuraButton(
                    label: running ? 'Stop' : 'Start kiosk',
                    icon: running
                        ? Icons.stop_rounded
                        : Icons.play_arrow_rounded,
                    variant: running
                        ? AuraButtonVariant.destructive
                        : AuraButtonVariant.filled,
                    expand: false,
                    onPressed: onToggle,
                  ),
                ],
              ),

              const SizedBox(height: AppSpacing.x8),

              // Breakdown
              Wrap(
                spacing: AppSpacing.x8,
                runSpacing: AppSpacing.x4,
                children: [
                  if (signIns > 0)
                    _MiniStat(
                        icon: Icons.login_rounded,
                        label: '$signIns checked in',
                        tint: t.present),
                  if (signOuts > 0)
                    _MiniStat(
                        icon: Icons.logout_rounded,
                        label: '$signOuts signed out',
                        tint: t.sg),
                  if (spoofs > 0)
                    _MiniStat(
                        icon: Icons.gpp_bad_rounded,
                        label: '$spoofs spoof${spoofs == 1 ? '' : 's'}',
                        tint: t.absent),
                  if (outOfScope > 0)
                    _MiniStat(
                        icon: Icons.do_not_disturb_on_rounded,
                        label: '$outOfScope rejected',
                        tint: t.atRisk),
                ],
              ),

              if (error != null) ...[
                const SizedBox(height: AppSpacing.x8),
                Row(
                  children: [
                    Icon(Icons.error_outline_rounded,
                        size: 14, color: t.absent),
                    const SizedBox(width: 4),
                    Flexible(
                      child: Text(
                        error!,
                        style: textTheme.bodySmall?.copyWith(color: t.absent),
                      ),
                    ),
                  ],
                ),
              ],

              const SizedBox(height: AppSpacing.x12),
              Text('Recent',
                  style: textTheme.labelMedium
                      ?.copyWith(color: t.textSecondary, letterSpacing: 0.4)),
              const SizedBox(height: AppSpacing.x8),

              Expanded(
                child: log.isEmpty
                    ? Center(
                        child: Text(
                          running
                              ? 'Looking for faces…'
                              : 'Tap Start to begin scanning.',
                          style: textTheme.bodyMedium
                              ?.copyWith(color: t.textMuted),
                        ),
                      )
                    : ListView.separated(
                        physics: const BouncingScrollPhysics(),
                        itemCount: log.length.clamp(0, 12),
                        separatorBuilder: (_, __) =>
                            const SizedBox(height: AppSpacing.x8),
                        itemBuilder: (context, i) => GatherOutcomeTile(
                          // Stable key — use attendance id when we have it, fall
                          // back to (action+studentId+index) for non-success rows
                          // so the AnimatedSwitcher in OutcomeTile doesn't
                          // mistake adjacent failures for the same row.
                          key: ValueKey(
                            log[i].attendanceId ??
                                '${log[i].action}-${log[i].studentId ?? 'anon'}-$i',
                          ),
                          outcome: log[i],
                          dense: true,
                        ),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  const _MiniStat({required this.icon, required this.label, required this.tint});
  final IconData icon;
  final String label;
  final Color tint;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: tint.withOpacity(0.16),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: tint),
          const SizedBox(width: 4),
          Text(label,
              style: textTheme.bodySmall
                  ?.copyWith(color: tint, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Camera/location error — full-bleed fallback inside the kiosk surface.
// ─────────────────────────────────────────────────────────────────────────
class _ErrorState extends StatelessWidget {
  const _ErrorState({
    required this.title,
    required this.message,
    required this.onPop,
  });
  final String title;
  final String message;
  final VoidCallback onPop;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.x24),
      child: Column(
        children: [
          Align(
            alignment: Alignment.centerLeft,
            child: IconButton(
              icon: const Icon(Icons.arrow_back_ios_new_rounded,
                  color: Colors.white),
              onPressed: onPop,
            ),
          ),
          const Spacer(),
          Icon(Icons.videocam_off_rounded,
              size: 56, color: Colors.white.withOpacity(0.6)),
          const SizedBox(height: AppSpacing.x16),
          Text(title,
              style: textTheme.headlineSmall
                  ?.copyWith(color: Colors.white)),
          const SizedBox(height: 6),
          Text(
            message,
            textAlign: TextAlign.center,
            style: textTheme.bodyMedium
                ?.copyWith(color: Colors.white.withOpacity(0.7)),
          ),
          const SizedBox(height: AppSpacing.x24),
          AuraButton(
            label: 'Back',
            icon: Icons.arrow_back_rounded,
            variant: AuraButtonVariant.tonal,
            expand: false,
            onPressed: onPop,
          ),
          const Spacer(flex: 2),
        ],
      ),
    );
  }
}
