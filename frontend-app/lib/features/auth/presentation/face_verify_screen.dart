import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/aura_button.dart';

/// Placeholder gate for privileged accounts that still owe a face check.
/// The real camera-based verification is implemented in Phase 1.
class FaceVerifyScreen extends ConsumerWidget {
  const FaceVerifyScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      backgroundColor: t.bg,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.x24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.face_retouching_natural_rounded,
                      size: 40, color: t.accent),
                  const SizedBox(height: AppSpacing.x16),
                  Text('Face verification required',
                      textAlign: TextAlign.center,
                      style: textTheme.headlineSmall),
                  const SizedBox(height: AppSpacing.x8),
                  Text(
                    'This privileged account needs a face check to continue. '
                    'Camera verification arrives in Phase 1.',
                    textAlign: TextAlign.center,
                    style:
                        textTheme.bodyMedium?.copyWith(color: t.textSecondary),
                  ),
                  const SizedBox(height: AppSpacing.x32),
                  AuraButton(
                    label: 'Sign out',
                    icon: Icons.logout_rounded,
                    variant: AuraButtonVariant.ghost,
                    onPressed: () =>
                        ref.read(sessionControllerProvider.notifier).logout(),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
