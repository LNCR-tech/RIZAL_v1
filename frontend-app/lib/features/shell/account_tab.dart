import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/role.dart';
import '../../core/auth/session_controller.dart';
import '../../core/data/school_directory_repository.dart';
import '../../core/theme/app_branding_controller.dart';
import '../../core/theme/app_motion.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_tokens.dart';
import '../../core/theme/app_typography.dart';
import '../../core/theme/beta_controller.dart';
import '../../core/theme/motion_controller.dart';
import '../../core/theme/theme_controller.dart';
import '../../core/widgets/aura_button.dart';
import '../../core/widgets/aura_card.dart';
import '../../core/widgets/pressable.dart';
import '../../core/widgets/rise_in.dart';
import '../../core/widgets/school_badge.dart';
import '../../core/widgets/settings_tile.dart';
import '../student/application/student_providers.dart';
import '../assistant/presentation/chat_screen.dart';
import '../auth/presentation/change_password_screen.dart';
import '../auth/presentation/security_screen.dart';
import '../auth/presentation/update_face_screen.dart';
import '../events/application/auto_checkin_controller.dart';
import '../gather/presentation/gather_screen.dart';
import '../governance/application/governance_providers.dart';
import '../help/presentation/help_center_screen.dart';
import '../sanctions/presentation/my_sanctions_screen.dart';
import '../notifications/presentation/notifications_screen.dart';
import '../student/presentation/edit_profile_screen.dart';
import '../student/presentation/profile_screen.dart';
import 'app_appearance_screen.dart';
import 'app_shell.dart';

/// Account & settings — an iOS-style grouped surface with soft colored icon
/// tiles, preference controls, and sign-out.
class AccountTab extends ConsumerWidget {
  const AccountTab({super.key});

  static const _blue = Color(0xFF3B82F6);
  static const _violet = Color(0xFF8B5CF6);
  static const _indigo = Color(0xFF6366F1);
  static const _teal = Color(0xFF14B8A6);
  static const _rose = Color(0xFFEC4899);

  void _push(BuildContext context, Widget screen) =>
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final meta = ref.watch(sessionControllerProvider).meta;
    final themeMode = ref.watch(themeControllerProvider).mode;
    final motionPref = ref.watch(motionControllerProvider);
    final betaNav = ref.watch(betaNavProvider);
    final autoCheckIn = ref.watch(autoCheckInProvider);
    final autoCheckFull = ref.watch(autoCheckFullProvider);
    final govAccess = ref.watch(governanceAccessProvider).valueOrNull;
    final branding = ref.watch(appBrandingProvider);

    // Compact one-liner that summarizes the current branding choice for the
    // Account tile — keeps the row terse while still telling the user what's
    // on without opening the screen.
    String brandingSummary() {
      final logoOn = branding.effectiveUseSchoolLogo;
      final codeOn = branding.useSchoolCodeAsName && branding.hasCode;
      if (logoOn && codeOn) return 'School logo & code';
      if (logoOn) return 'School logo';
      if (codeOn) return 'School code';
      return 'Aura defaults';
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(
          AppSpacing.x20, AppSpacing.x24, AppSpacing.x20, 130),
      children: staggered([
        Text('Account', style: textTheme.displaySmall),
        const SizedBox(height: AppSpacing.x20),

        // Profile summary (tappable → profile).
        Pressable(
          scale: 0.99,
          onTap: () => _push(context, const ProfileScreen()),
          child: AuraCard(
            child: Row(
              children: [
                if (Roles.workspaceFor(meta?.roles ?? const []) ==
                    Workspace.schoolIt)
                  SchoolBadge(
                    logoUrl: meta?.logoUrl,
                    schoolName: meta?.schoolName,
                    primaryHex: meta?.primaryColor,
                    secondaryHex: meta?.secondaryColor,
                    schoolId: meta?.schoolId,
                    size: 56,
                  )
                else
                  CircleAvatar(
                    radius: 28,
                    backgroundColor: t.accent,
                    child: Text(meta?.initials ?? '?',
                        style: textTheme.titleLarge
                            ?.copyWith(color: t.onAccent)),
                  ),
                const SizedBox(width: AppSpacing.x16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(meta?.displayName ?? 'User',
                          style: textTheme.titleLarge),
                      if (meta?.email != null)
                        Text(meta!.email!,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: textTheme.bodyMedium
                                ?.copyWith(color: t.textSecondary)),
                      const _AcademicSubtitle(),
                      if (meta?.schoolName != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 4),
                          child: Row(
                            children: [
                              if (meta?.logoUrl?.isNotEmpty == true) ...[
                                SchoolBadge(
                                  logoUrl: meta?.logoUrl,
                                  schoolName: meta?.schoolName,
                                  primaryHex: meta?.primaryColor,
                                  secondaryHex: meta?.secondaryColor,
                                  schoolId: meta?.schoolId,
                                  size: 18,
                                ),
                                const SizedBox(width: 6),
                              ],
                              Expanded(
                                child: Text(
                                  meta!.schoolName!,
                                  style: textTheme.bodySmall?.copyWith(color: t.textMuted),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
                Icon(Icons.chevron_right_rounded, color: t.textMuted),
              ],
            ),
          ),
        ),
        const SizedBox(height: AppSpacing.x24),

        // APPEARANCE — instant look-and-feel (theme, motion) plus deeper
        // brand customization (App appearance) and the experimental glass
        // nav. One section so the user finds every "how it looks" knob in
        // one place instead of three.
        SettingsSection(
          header: 'Appearance',
          tiles: [
            _PreferenceRow(
              icon: Icons.brightness_6_rounded,
              iconColor: _indigo,
              title: 'Theme',
              control: SegmentedButton<ThemeMode>(
                segments: const [
                  ButtonSegment(
                      value: ThemeMode.system, label: Text('System')),
                  ButtonSegment(
                      value: ThemeMode.light, label: Text('Light')),
                  ButtonSegment(
                      value: ThemeMode.dark, label: Text('Dark')),
                ],
                selected: {themeMode},
                showSelectedIcon: false,
                onSelectionChanged: (s) => ref
                    .read(themeControllerProvider.notifier)
                    .setMode(s.first),
              ),
            ),
            _PreferenceRow(
              icon: Icons.motion_photos_paused_rounded,
              iconColor: t.textSecondary,
              title: 'Reduce motion',
              control: SegmentedButton<MotionPref>(
                segments: const [
                  ButtonSegment(
                      value: MotionPref.system, label: Text('System')),
                  ButtonSegment(value: MotionPref.on, label: Text('On')),
                  ButtonSegment(value: MotionPref.off, label: Text('Off')),
                ],
                selected: {motionPref},
                showSelectedIcon: false,
                onSelectionChanged: (s) => ref
                    .read(motionControllerProvider.notifier)
                    .set(s.first),
              ),
            ),
            SettingsTile(
              icon: Icons.palette_outlined,
              iconColor: _violet,
              title: 'App appearance',
              subtitle: brandingSummary(),
              onTap: () => _push(context, const AppAppearanceScreen()),
            ),
            _BetaSwitchTile(
              icon: Icons.blur_on_rounded,
              iconColor: _violet,
              title: 'Liquid glass tab bar',
              subtitle: 'iOS-style glass navigation.',
              value: betaNav,
              onChanged: (v) => ref.read(betaNavProvider.notifier).set(v),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.x24),

        // ACCOUNT — identity, auth, biometrics. Was "Security" but the
        // first row is "Edit profile" so naming it Account reads more
        // naturally for the user. The redundant "General > Profile" tile
        // is gone — the top profile card is the canonical entry point.
        SettingsSection(
          header: 'Account',
          tiles: [
            SettingsTile(
              icon: Icons.manage_accounts_rounded,
              iconColor: _blue,
              title: 'Edit profile',
              subtitle: 'Name & email',
              onTap: () => _push(context, const EditProfileScreen()),
            ),
            SettingsTile(
              icon: Icons.lock_rounded,
              iconColor: _indigo,
              title: 'Change password',
              onTap: () => _push(context, const ChangePasswordScreen()),
            ),
            SettingsTile(
              icon: Icons.devices_rounded,
              iconColor: _teal,
              title: 'Sign-in & devices',
              subtitle: 'Active sessions & recent sign-ins',
              onTap: () => _push(context, const SecurityScreen()),
            ),
            SettingsTile(
              icon: Icons.face_rounded,
              iconColor: _violet,
              title: 'Face ID',
              subtitle: (meta?.faceReferenceEnrolled ?? false)
                  ? 'Enrolled'
                  : 'Not enrolled',
              onTap: () => _push(context, const UpdateFaceScreen()),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.x24),

        // NOTIFICATIONS — alerts + the attendance-prompt toggles (which
        // previously lived under "Beta features" but conceptually belong
        // with notifications since that's what they emit).
        SettingsSection(
          header: 'Notifications',
          tiles: [
            SettingsTile(
              icon: Icons.notifications_rounded,
              iconColor: t.absent,
              title: 'Inbox',
              subtitle: 'Reminders, results, system messages',
              onTap: () => _push(context, const NotificationsScreen()),
            ),
            _BetaSwitchTile(
              icon: Icons.location_on_rounded,
              iconColor: _teal,
              title: 'Nearby event check-in',
              subtitle: 'Prompt me when I reach an event.',
              value: autoCheckIn,
              onChanged: (v) =>
                  ref.read(autoCheckInProvider.notifier).set(v),
            ),
            _BetaSwitchTile(
              icon: Icons.bolt_rounded,
              iconColor: _blue,
              title: 'Auto check-in',
              subtitle:
                  autoCheckFull ? 'Coming soon.' : 'Hands-free, no scan.',
              value: autoCheckFull,
              onChanged: (v) {
                ref.read(autoCheckFullProvider.notifier).set(v);
                if (v) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                        content: Text('Auto check-in is coming soon.')),
                  );
                }
              },
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.x24),

        // TOOLS — utilities beside the main workspace (AI chat, kiosk).
        SettingsSection(
          header: 'Tools',
          tiles: [
            SettingsTile(
              icon: Icons.auto_awesome_rounded,
              iconColor: _violet,
              title: 'Aura AI',
              subtitle: 'Ask about attendance, schedule, sanctions',
              onTap: () => _push(context, const ChatScreen()),
            ),
            SettingsTile(
              icon: Icons.center_focus_strong_rounded,
              iconColor: t.present,
              title: 'Gather (kiosk)',
              subtitle: 'Multi-face scan for events',
              onTap: () => _push(context, const GatherScreen()),
            ),
          ],
        ),

        // COMPLIANCE — students see "My sanctions"; other roles use the
        // governance dashboard for the same data so it's hidden there.
        if (Roles.workspaceFor(meta?.roles ?? const []) ==
            Workspace.student) ...[
          const SizedBox(height: AppSpacing.x24),
          SettingsSection(
            header: 'Compliance',
            tiles: [
              SettingsTile(
                icon: Icons.gavel_rounded,
                iconColor: t.tardy,
                title: 'My sanctions',
                subtitle: 'Outstanding penalties & clearance deadline',
                onTap: () => _push(context, const MySanctionsScreen()),
              ),
            ],
          ),
        ],

        const SizedBox(height: AppSpacing.x24),

        // SUPPORT — public-facing help.
        SettingsSection(
          header: 'Support',
          tiles: [
            SettingsTile(
              icon: Icons.help_outline_rounded,
              iconColor: _rose,
              title: 'Help Center',
              subtitle: 'Guides, FAQ, troubleshooting & contact',
              onTap: () => _push(context, const HelpCenterScreen()),
            ),
          ],
        ),

        // WORKSPACES — visible only when the signed-in user has
        // governance access (officer roles).
        if (govAccess != null && govAccess.hasAccess) ...[
          const SizedBox(height: AppSpacing.x24),
          SettingsSection(
            header: 'Workspaces',
            tiles: [
              SettingsTile(
                icon: Icons.account_balance_rounded,
                iconColor: _indigo,
                title: 'Governance',
                subtitle:
                    '${govAccess.units.length} unit${govAccess.units.length == 1 ? '' : 's'}',
                onTap: () => _push(
                    context, const AppShell(workspace: Workspace.governance)),
              ),
            ],
          ),
        ],

        const SizedBox(height: AppSpacing.x32),
        AuraButton(
          label: 'Sign out',
          icon: Icons.logout_rounded,
          variant: AuraButtonVariant.destructive,
          onPressed: () => ref.read(sessionControllerProvider.notifier).logout(),
        ),
      ]),
    );
  }
}

/// Settings row with a colored icon tile + title above a full-width
/// control widget. Designed to drop into a [SettingsSection]'s tile list
/// so segmented preference pickers (Theme, Reduce motion) sit in the
/// same card as adjacent SettingsTile rows — no nested AuraCards, no
/// visual rhythm break.
class _PreferenceRow extends StatelessWidget {
  const _PreferenceRow({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.control,
  });
  final IconData icon;
  final Color iconColor;
  final String title;
  final Widget control;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x16, vertical: AppSpacing.x16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Container(
                width: 30,
                height: 30,
                decoration: BoxDecoration(
                  color: iconColor,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: Colors.white, size: 18),
              ),
              const SizedBox(width: AppSpacing.x12),
              Expanded(child: Text(title, style: textTheme.bodyLarge)),
            ],
          ),
          const SizedBox(height: AppSpacing.x12),
          control,
        ],
      ),
    );
  }
}

/// A grouped settings row (icon · title + BETA pill · subtitle · switch) for the
/// "Beta features" section — gives an iOS-Settings feel for the experimental toggles.
class _BetaSwitchTile extends StatelessWidget {
  const _BetaSwitchTile({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
  });
  final IconData icon;
  final Color iconColor;
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x16, vertical: AppSpacing.x12),
      child: Row(
        children: [
          Container(
            width: 30,
            height: 30,
            decoration: BoxDecoration(
                color: iconColor, borderRadius: BorderRadius.circular(8)),
            child: Icon(icon, color: Colors.white, size: 18),
          ),
          const SizedBox(width: AppSpacing.x12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Flexible(child: Text(title, style: textTheme.bodyLarge)),
                    const SizedBox(width: AppSpacing.x8),
                    _BetaPill(color: iconColor),
                  ],
                ),
                const SizedBox(height: 2),
                Text(subtitle,
                    style:
                        textTheme.bodySmall?.copyWith(color: t.textSecondary)),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.x12),
          Switch(value: value, onChanged: onChanged),
        ],
      ),
    );
  }
}

/// One-line academic summary under the email on the account-tab profile
/// card — e.g. `BSCS · 2nd year`. Only renders when the signed-in user has
/// a student profile AND at least one of (program short code, year level)
/// resolves. No placeholder while loading; the line just fades in once the
/// directory lookup lands, so the header doesn't reflow or flicker.
class _AcademicSubtitle extends ConsumerWidget {
  const _AcademicSubtitle();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppTokens.of(context);
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    final profile = ref.watch(myProfileProvider).valueOrNull;
    final sp = profile?.studentProfile;
    if (sp == null) return const SizedBox.shrink();

    final yearOrdinal =
        sp.yearLevel != null ? _ordinalYear(sp.yearLevel!) : null;

    String? programCode;
    if (sp.programId != null) {
      final p = ref.watch(programByIdProvider(sp.programId!)).valueOrNull;
      if (p != null && p.name.isNotEmpty) {
        programCode = _programShortCode(p.name);
      }
    }

    final parts = <String>[
      if (programCode != null && programCode.isNotEmpty) programCode,
      if (yearOrdinal != null) yearOrdinal,
    ];
    if (parts.isEmpty) return const SizedBox.shrink();
    final text = parts.join(' · ');

    return Padding(
      padding: const EdgeInsets.only(top: 2),
      child: AnimatedSwitcher(
        duration:
            reduce ? Duration.zero : const Duration(milliseconds: 220),
        switchInCurve: AppMotion.easeOut,
        transitionBuilder: (child, anim) => FadeTransition(
          opacity: anim,
          child: child,
        ),
        child: Text(
          text,
          key: ValueKey(text),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: AppTypography.mono(
            size: 12,
            weight: FontWeight.w600,
            color: t.textMuted,
          ),
        ),
      ),
    );
  }
}

/// "BS Computer Science" → "BSCS"; "BS Information Technology" → "BSIT".
/// All-caps tokens (acronyms like "BS", "BSIT") are kept verbatim;
/// title-case words contribute their first letter; lowercase tokens like
/// "of" / "in" are dropped. Returns the input verbatim when no
/// abbreviation is derivable (e.g. an all-lowercase name).
String _programShortCode(String name) {
  final buf = StringBuffer();
  for (final word in name.split(RegExp(r'\s+'))) {
    final letters = word.replaceAll(RegExp(r'[^A-Za-z]'), '');
    if (letters.isEmpty) continue;
    if (letters == letters.toUpperCase()) {
      buf.write(letters);
    } else if (letters[0] == letters[0].toUpperCase()) {
      buf.write(letters[0]);
    }
  }
  final out = buf.toString();
  return out.isEmpty ? name : out;
}

String _ordinalYear(int year) {
  final suffix = switch (year) {
    1 => 'st',
    2 => 'nd',
    3 => 'rd',
    _ => 'th',
  };
  return '$year$suffix year';
}

/// Small "BETA" pill used to flag experimental settings.
class _BetaPill extends StatelessWidget {
  const _BetaPill({required this.color});
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.14),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        'BETA',
        style: TextStyle(
          color: color,
          fontSize: 10,
          height: 1,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.6,
        ),
      ),
    );
  }
}
