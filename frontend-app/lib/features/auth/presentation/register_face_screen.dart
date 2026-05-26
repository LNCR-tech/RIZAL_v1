import 'dart:convert';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/aura_button.dart';
import '../../attendance/data/attendance_repository.dart';

/// First-login face-registration gate for students.
///
/// Reached via the router when [SessionState.needsFaceRegistration] is
/// true (authenticated student with no face reference enrolled yet).
/// Two stages:
///   1. **Intro** — explains *why* before pointing a camera at the user.
///      Privacy lines, one-time-setup framing, "Continue" CTA. Sign-out
///      escape hatch in the top-right for users who landed here by
///      mistake.
///   2. **Capture** — front-camera capture with face frame overlay.
///      Reuses the same plumbing as `UpdateFaceScreen` but with onboarding
///      copy and a tighter error-mapping for backend rejections
///      (no-face / spoof / oversized / 503 startup).
///
/// On success, [SessionController.markFaceRegistered] flips
/// `meta.faceReferenceEnrolled` to true and persists. The router's
/// redirect listener immediately routes the student to their workspace.
class RegisterFaceScreen extends ConsumerStatefulWidget {
  const RegisterFaceScreen({super.key});

  @override
  ConsumerState<RegisterFaceScreen> createState() =>
      _RegisterFaceScreenState();
}

enum _Stage { intro, capture }

class _RegisterFaceScreenState extends ConsumerState<RegisterFaceScreen> {
  _Stage _stage = _Stage.intro;
  CameraController? _controller;
  bool _initializing = false;
  bool _busy = false;
  String? _error;
  String? _cameraError;

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _goToCapture() async {
    setState(() {
      _stage = _Stage.capture;
      _initializing = true;
      _cameraError = null;
    });
    try {
      final cams = await availableCameras();
      if (cams.isEmpty) {
        if (!mounted) return;
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
      await ref.read(attendanceRepositoryProvider).registerFace(b64);
      await ref.read(sessionControllerProvider.notifier).markFaceRegistered();
      if (!mounted) return;
      HapticFeedback.mediumImpact();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Face saved. Welcome to Aura.')),
      );
      // The router redirect listener picks up the cleared gate and routes
      // the student to their workspace — no explicit nav here.
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = _friendlyError(e));
    } catch (_) {
      if (mounted) {
        setState(() =>
            _error = 'Could not register your face. Please try again.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// Map backend status codes from `POST /api/face/register` to copy a
  /// student can act on. The backend doc (face_recognition.py) defines
  /// the exact response shapes — see CHANGELOG for the contract trace.
  String _friendlyError(ApiException e) {
    switch (e.statusCode) {
      case 400:
        // "Image must contain exactly one face." | bad base64 | etc.
        return e.message;
      case 403:
        // Spoof detected (anti-spoof model rejected the frame).
        return 'We couldn’t confirm it was a real face. '
            'Avoid printed photos or screens.';
      case 413:
        return 'Image is too large — try better lighting and a closer shot.';
      case 415:
        return 'Unsupported image format. Try again.';
      case 429:
        return 'Too many attempts. Wait a moment and try again.';
      case 503:
        return 'Face service is starting — try again in a moment.';
      default:
        if (e.statusCode > 0) {
          return e.message.isEmpty
              ? 'HTTP ${e.statusCode}'
              : '${e.message} (HTTP ${e.statusCode})';
        }
        return e.message.isEmpty
            ? 'Could not register your face. Please try again.'
            : e.message;
    }
  }

  Future<void> _signOut() async =>
      ref.read(sessionControllerProvider.notifier).logout();

  @override
  Widget build(BuildContext context) {
    return _stage == _Stage.intro ? _buildIntro(context) : _buildCapture(context);
  }

  Widget _buildIntro(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Scaffold(
      backgroundColor: t.bg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
              AppSpacing.x24, AppSpacing.x8, AppSpacing.x24, AppSpacing.x24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Sign-out escape hatch — top-right, low-emphasis. Lets a
              // user who landed here by accident bail without forcing
              // them through a process they don't want.
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: _signOut,
                  child: Text('Sign out',
                      style: textTheme.bodyMedium?.copyWith(
                        color: t.textSecondary,
                        fontWeight: FontWeight.w600,
                      )),
                ),
              ),
              const SizedBox(height: AppSpacing.x8),
              _IntroHero(t: t),
              const SizedBox(height: AppSpacing.x24),
              Text('Set up your face', style: textTheme.displaySmall),
              const SizedBox(height: AppSpacing.x8),
              Text(
                'We use this to mark you present at events. Quick, one-time, '
                'and kept on your school’s secure server.',
                style: textTheme.bodyLarge?.copyWith(color: t.textSecondary),
              ),
              const SizedBox(height: AppSpacing.x32),
              _Bullet(
                icon: Icons.lock_outline_rounded,
                color: t.accent,
                title: 'Stays with your school',
                subtitle:
                    'Your face is stored only on your school’s server. '
                    'Never sold or shared.',
              ),
              const SizedBox(height: AppSpacing.x16),
              _Bullet(
                icon: Icons.event_available_rounded,
                color: t.accent,
                title: 'One-time setup',
                subtitle:
                    'You won’t have to do this every time you sign in.',
              ),
              const SizedBox(height: AppSpacing.x16),
              _Bullet(
                icon: Icons.refresh_rounded,
                color: t.accent,
                title: 'Re-take any time',
                subtitle:
                    'Update from Account → Account → Face ID whenever you need to.',
              ),
              const Spacer(),
              AuraButton(
                label: 'Continue',
                icon: Icons.arrow_forward_rounded,
                onPressed: _goToCapture,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCapture(BuildContext context) {
    final t = AppTokens.of(context);
    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: Colors.white,
        title: const Text('Set up your face'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          tooltip: 'Back',
          onPressed: _busy
              ? null
              : () {
                  _controller?.dispose();
                  _controller = null;
                  setState(() => _stage = _Stage.intro);
                },
        ),
      ),
      body: _captureBody(t),
    );
  }

  Widget _captureBody(AppTokens t) {
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
                onPressed: _goToCapture,
                child: Text('Try again', style: TextStyle(color: t.accent)),
              ),
            ],
          ),
        ),
      );
    }
    final controller = _controller;
    if (controller == null) {
      return const Center(child: CircularProgressIndicator());
    }

    return Stack(
      children: [
        Positioned.fill(child: _CameraFill(controller: controller)),
        // Soft vignette so the face frame and bottom instructions read
        // cleanly over arbitrary camera content.
        Positioned.fill(
          child: IgnorePointer(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.black.withOpacity(0.45),
                    Colors.transparent,
                    Colors.transparent,
                    Colors.black.withOpacity(0.65),
                  ],
                  stops: const [0.0, 0.18, 0.6, 1.0],
                ),
              ),
            ),
          ),
        ),
        Positioned.fill(
          child: Center(
            child: Container(
              width: 240,
              height: 300,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.white70, width: 2.5),
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
                    accent: t.accent,
                    busy: _busy,
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

class _IntroHero extends StatelessWidget {
  const _IntroHero({required this.t});
  final AppTokens t;
  @override
  Widget build(BuildContext context) {
    return Container(
      height: 150,
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: t.border),
      ),
      child: Center(
        child: Container(
          width: 88,
          height: 88,
          decoration: BoxDecoration(
            color: t.accent.withOpacity(0.18),
            shape: BoxShape.circle,
          ),
          child: Icon(Icons.face_retouching_natural_rounded,
              size: 48, color: t.accent),
        ),
      ),
    );
  }
}

class _Bullet extends StatelessWidget {
  const _Bullet({
    required this.icon,
    required this.color,
    required this.title,
    required this.subtitle,
  });
  final IconData icon;
  final Color color;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            color: color.withOpacity(0.16),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: color, size: 18),
        ),
        const SizedBox(width: AppSpacing.x16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: textTheme.titleLarge),
              const SizedBox(height: 2),
              Text(subtitle,
                  style: textTheme.bodyMedium
                      ?.copyWith(color: t.textSecondary, height: 1.45)),
            ],
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
