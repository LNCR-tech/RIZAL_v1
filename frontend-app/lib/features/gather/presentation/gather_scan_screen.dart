import 'dart:convert';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/services/geolocation_service.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/public_attendance.dart';
import '../data/public_attendance_repository.dart';

/// Kiosk multi-face check-in. Runs an auto-scan loop while active; recorded
/// students go on a cooldown set so they're not double-counted.
class GatherScanScreen extends ConsumerStatefulWidget {
  const GatherScanScreen(
      {super.key, required this.event, required this.cooldownSeconds});
  final NearbyEvent event;
  final int cooldownSeconds;

  @override
  ConsumerState<GatherScanScreen> createState() => _GatherScanScreenState();
}

class _GatherScanScreenState extends ConsumerState<GatherScanScreen> {
  CameraController? _controller;
  bool _initializing = true;
  String? _cameraError;
  GeoFix? _fix;
  bool _running = false;
  bool _busy = false;
  String? _error;

  final Set<String> _seen = {};
  final List<ScanOutcome> _log = [];
  int _count = 0;

  @override
  void initState() {
    super.initState();
    _init();
  }

  @override
  void dispose() {
    _running = false;
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _init() async {
    try {
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
      final controller = CameraController(desc, ResolutionPreset.high,
          enableAudio: false, imageFormatGroup: ImageFormatGroup.jpeg);
      await controller.initialize();
      final fix = await ref.read(geolocationServiceProvider).current();
      if (!mounted) {
        controller.dispose();
        return;
      }
      setState(() {
        _controller = controller;
        _fix = fix;
        _initializing = false;
        if (fix == null) _error = 'Location unavailable — enable location.';
      });
    } catch (_) {
      if (mounted) {
        setState(() {
          _cameraError = 'Camera unavailable. Please grant camera permission.';
          _initializing = false;
        });
      }
    }
  }

  void _toggle() {
    setState(() => _running = !_running);
    if (_running) _loop();
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
      setState(() => _error = 'Location unavailable — enable location.');
      return;
    }
    _busy = true;
    try {
      final shot = await controller.takePicture();
      final bytes = await shot.readAsBytes();
      final res =
          await ref.read(publicAttendanceRepositoryProvider).multiScan(
                eventId: widget.event.id,
                imageBase64: base64Encode(bytes),
                latitude: fix.latitude,
                longitude: fix.longitude,
                accuracyM: fix.accuracy,
                cooldownStudentIds: _seen.toList(),
              );
      if (!mounted) return;
      setState(() {
        _error = null;
        for (final o in res.outcomes) {
          if (o.isSuccess && o.studentId != null) {
            if (_seen.add(o.studentId!)) _count++;
            _log.insert(0, o);
          }
        }
        if (_log.length > 40) _log.removeRange(40, _log.length);
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Scan failed — retrying…');
    } finally {
      _busy = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text(widget.event.name,
            maxLines: 1, overflow: TextOverflow.ellipsis),
      ),
      body: _body(t),
    );
  }

  Widget _body(AppTokens t) {
    if (_initializing) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_cameraError != null) {
      return Center(child: ErrorView(message: _cameraError!));
    }
    return Column(
      children: [
        Expanded(
          flex: 5,
          child: Stack(
            fit: StackFit.expand,
            children: [
              _cameraFill(_controller!),
              if (_running)
                Positioned(
                  top: AppSpacing.x12,
                  left: 0,
                  right: 0,
                  child: Center(child: _ScanningChip(accent: t.accent)),
                ),
            ],
          ),
        ),
        Expanded(
          flex: 4,
          child: Container(
            color: t.surface,
            padding: const EdgeInsets.all(AppSpacing.x20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text('$_count',
                        style: AppTypography.mono(
                            size: 28, weight: FontWeight.w700, color: t.ink)),
                    const SizedBox(width: AppSpacing.x8),
                    Text('recorded',
                        style: Theme.of(context)
                            .textTheme
                            .bodyMedium
                            ?.copyWith(color: t.textSecondary)),
                    const Spacer(),
                    AuraButton(
                      label: _running ? 'Stop' : 'Start',
                      icon: _running
                          ? Icons.stop_rounded
                          : Icons.play_arrow_rounded,
                      variant: _running
                          ? AuraButtonVariant.destructive
                          : AuraButtonVariant.filled,
                      expand: false,
                      onPressed: _toggle,
                    ),
                  ],
                ),
                if (_error != null) ...[
                  const SizedBox(height: AppSpacing.x12),
                  Text(_error!,
                      style: Theme.of(context)
                          .textTheme
                          .bodySmall
                          ?.copyWith(color: t.absent)),
                ],
                const SizedBox(height: AppSpacing.x16),
                Expanded(
                  child: _log.isEmpty
                      ? Center(
                          child: Text(
                            _running
                                ? 'Point the camera at students…'
                                : 'Tap Start to begin scanning.',
                            style: Theme.of(context)
                                .textTheme
                                .bodyMedium
                                ?.copyWith(color: t.textMuted),
                          ),
                        )
                      : ListView.builder(
                          itemCount: _log.length,
                          itemBuilder: (context, i) {
                            final o = _log[i];
                            return Padding(
                              padding:
                                  const EdgeInsets.only(bottom: AppSpacing.x12),
                              child: Row(
                                children: [
                                  Icon(
                                      o.action == 'time_out'
                                          ? Icons.logout_rounded
                                          : Icons.check_circle_rounded,
                                      size: 18,
                                      color: t.present),
                                  const SizedBox(width: AppSpacing.x8),
                                  Expanded(
                                    child: Text(
                                        o.studentName ??
                                            o.studentId ??
                                            'Student',
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style:
                                            Theme.of(context).textTheme.bodyLarge),
                                  ),
                                  Text(
                                      o.action == 'time_out'
                                          ? 'Signed out'
                                          : 'Checked in',
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodySmall
                                          ?.copyWith(color: t.textSecondary)),
                                ],
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
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

class _ScanningChip extends StatelessWidget {
  const _ScanningChip({required this.accent});
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x16, vertical: AppSpacing.x8),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.55),
        borderRadius: BorderRadius.circular(AppRadii.pill),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
              width: 12,
              height: 12,
              child:
                  CircularProgressIndicator(strokeWidth: 2, color: accent)),
          const SizedBox(width: AppSpacing.x8),
          const Text('Scanning…', style: TextStyle(color: Colors.white)),
        ],
      ),
    );
  }
}
