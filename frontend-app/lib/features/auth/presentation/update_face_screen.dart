import 'dart:convert';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../attendance/data/attendance_repository.dart';
import '../data/security_repository.dart';

/// Re-enroll the signed-in user's face from a front-camera capture. Routes to
/// the right backend endpoint by role: privileged accounts use
/// `/auth/security/face-reference`; students use `/api/face/register`.
class UpdateFaceScreen extends ConsumerStatefulWidget {
  const UpdateFaceScreen({super.key});

  @override
  ConsumerState<UpdateFaceScreen> createState() => _UpdateFaceScreenState();
}

class _UpdateFaceScreenState extends ConsumerState<UpdateFaceScreen> {
  CameraController? _controller;
  bool _initializing = true;
  bool _busy = false;
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
    setState(() {
      _initializing = true;
      _cameraError = null;
    });
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
              'Camera unavailable. Grant camera permission and try again.';
          _initializing = false;
        });
      }
    }
  }

  bool get _privileged {
    final meta = ref.read(sessionControllerProvider).meta;
    if (meta == null) return false;
    if (meta.isAdmin) return true;
    return meta.roles
        .map((r) => r.toLowerCase())
        .any((r) =>
            r.contains('admin') || r.contains('campus') || r.contains('school'));
  }

  Future<void> _capture() async {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized || _busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final shot = await controller.takePicture();
      final bytes = await shot.readAsBytes();
      final b64 = base64Encode(bytes);
      String message;
      if (_privileged) {
        await ref.read(securityRepositoryProvider).setFaceReference(b64);
        message = 'Face updated.';
      } else {
        message = await ref.read(attendanceRepositoryProvider).registerFace(b64);
      }
      if (!mounted) return;
      HapticFeedback.mediumImpact();
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(message)));
    } on ApiException catch (e) {
      if (mounted) {
        setState(() => _error = e.statusCode == 503
            ? 'Face service is starting — try again in a moment.'
            : e.message);
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Could not update your face. Please try again.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: Colors.white,
        title: const Text('Update face'),
      ),
      body: _body(t),
    );
  }

  Widget _body(AppTokens t) {
    if (_initializing) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_cameraError != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.x24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.no_photography_rounded,
                  color: Colors.white54, size: 44),
              const SizedBox(height: AppSpacing.x16),
              Text(_cameraError!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white)),
              const SizedBox(height: AppSpacing.x20),
              TextButton(
                onPressed: _initCamera,
                child: Text('Try again', style: TextStyle(color: t.accent)),
              ),
            ],
          ),
        ),
      );
    }

    return Stack(
      children: [
        Positioned.fill(child: _CameraFill(controller: _controller!)),
        Positioned.fill(
          child: Center(
            child: Container(
              width: 240,
              height: 300,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.white54, width: 2),
                borderRadius: BorderRadius.circular(28),
              ),
            ),
          ),
        ),
        Positioned(
          left: 0,
          right: 0,
          bottom: 0,
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.x24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (_error != null) ...[
                    _ErrorPill(_error!, color: t.absent),
                    const SizedBox(height: AppSpacing.x16),
                  ],
                  const Text(
                    'Center your face, look straight, good lighting',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.white, fontSize: 14),
                  ),
                  const SizedBox(height: AppSpacing.x16),
                  _CaptureButton(
                      accent: t.accent, busy: _busy, onTap: _capture),
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
                  child:
                      CircularProgressIndicator(strokeWidth: 3, color: accent),
                )
              : const Icon(Icons.camera_alt_rounded,
                  color: Colors.black, size: 30),
        ),
      ),
    );
  }
}

class _ErrorPill extends StatelessWidget {
  const _ErrorPill(this.message, {required this.color});
  final String message;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x16, vertical: AppSpacing.x12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.92),
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
