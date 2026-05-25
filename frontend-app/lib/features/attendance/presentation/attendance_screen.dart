import 'dart:convert';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/services/geolocation_service.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/states.dart';
import '../../../shared/models/event.dart';
import '../data/attendance_repository.dart';
import 'attendance_result_sheet.dart';

class _AttendanceError {
  const _AttendanceError(this.message);
  final String message;
}

/// Face-scan attendance: front-camera capture + geolocation → backend.
class AttendanceScreen extends ConsumerStatefulWidget {
  const AttendanceScreen({super.key, required this.event});
  final AppEvent event;

  @override
  ConsumerState<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends ConsumerState<AttendanceScreen> {
  CameraController? _controller;
  bool _initializing = true;
  bool _submitting = false;
  String? _error;
  String? _cameraError;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _initCamera() async {
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
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => cams.first,
      );
      final controller = CameraController(
        desc,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );
      await controller.initialize();
      if (!mounted) {
        controller.dispose();
        return;
      }
      setState(() {
        _controller = controller;
        _initializing = false;
      });
    } catch (_) {
      if (mounted) {
        setState(() {
          _cameraError =
              'Camera unavailable. Please grant camera permission and try again.';
          _initializing = false;
        });
      }
    }
  }

  Future<void> _capture() async {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized || _submitting) {
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final geo = await ref.read(geolocationServiceProvider).current();
      if (widget.event.geoRequired && geo == null) {
        throw const _AttendanceError(
            'Location is required for this event. Enable location access and try again.');
      }
      final shot = await controller.takePicture();
      final bytes = await shot.readAsBytes();
      final result = await ref.read(attendanceRepositoryProvider).faceScan(
            eventId: widget.event.id,
            imageBase64: base64Encode(bytes),
            latitude: geo?.latitude,
            longitude: geo?.longitude,
            accuracyM: geo?.accuracy,
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
    } on _AttendanceError catch (e) {
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
          child: Container(
            width: 240,
            height: 300,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(150),
              border: Border.all(color: Colors.white.withOpacity(0.85), width: 3),
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
                  const Text(
                    'Center your face, then tap to scan',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.white, fontSize: 15),
                  ),
                  const SizedBox(height: AppSpacing.x16),
                  _CaptureButton(
                    accent: t.accent,
                    busy: _submitting,
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

class _CaptureButton extends StatelessWidget {
  const _CaptureButton(
      {required this.accent, required this.busy, required this.onTap});
  final Color accent;
  final bool busy;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: 'Capture',
      child: GestureDetector(
        onTap: busy ? null : onTap,
        child: Container(
          width: 78,
          height: 78,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.white,
            border: Border.all(color: accent, width: 5),
          ),
          child: busy
              ? Padding(
                  padding: const EdgeInsets.all(20),
                  child: CircularProgressIndicator(
                      strokeWidth: 3, color: accent),
                )
              : const Icon(Icons.camera_alt_rounded,
                  color: Colors.black, size: 30),
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
