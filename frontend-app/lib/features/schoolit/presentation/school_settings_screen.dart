import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/network/media_url.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../core/theme/theme_controller.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_button.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/aura_text_field.dart';
import '../../../core/widgets/section_header.dart';
import '../application/schoolit_providers.dart';
import '../data/schoolit_repository.dart';

/// University customization — logo, name/code, brand colours (with a live
/// preview), and the default event policy. Saving applies the primary colour to
/// the app theme immediately.
class SchoolSettingsScreen extends ConsumerStatefulWidget {
  const SchoolSettingsScreen({super.key});

  @override
  ConsumerState<SchoolSettingsScreen> createState() =>
      _SchoolSettingsScreenState();
}

class _SchoolSettingsScreenState extends ConsumerState<SchoolSettingsScreen> {
  static const _palette = <String>[
    '#AAFF00', '#22C55E', '#14B8A6', '#0EA5E9', '#3B82F6', '#6366F1',
    '#8B5CF6', '#EC4899', '#F43F5E', '#F59E0B', '#162F65', '#0A0A0A',
  ];

  final _name = TextEditingController();
  final _code = TextEditingController();
  final _early = TextEditingController();
  final _late = TextEditingController();
  final _signOut = TextEditingController();
  String? _primaryHex;
  String? _secondaryHex;
  Uint8List? _logoBytes;
  String? _logoName;
  bool _initialized = false;
  bool _busy = false;
  String? _error;
  String? _ok;

  @override
  void dispose() {
    for (final c in [_name, _code, _early, _late, _signOut]) {
      c.dispose();
    }
    super.dispose();
  }

  void _initOnce({
    String? name,
    String? code,
    required int early,
    required int late,
    required int signOut,
    String? primary,
    String? secondary,
  }) {
    if (_initialized) return;
    _initialized = true;
    _name.text = name ?? '';
    _code.text = code ?? '';
    _early.text = '$early';
    _late.text = '$late';
    _signOut.text = '$signOut';
    _primaryHex = (primary ?? '').trim().isEmpty ? null : primary;
    _secondaryHex = (secondary ?? '').trim().isEmpty ? null : secondary;
    _name.addListener(() {
      if (mounted) setState(() {});
    });
  }

  Future<void> _pickLogo() async {
    final res = await FilePicker.platform
        .pickFiles(type: FileType.image, withData: true);
    final file = res?.files.isNotEmpty == true ? res!.files.first : null;
    if (file?.bytes != null) {
      setState(() {
        _logoBytes = file!.bytes;
        _logoName = file.name;
      });
    }
  }

  Future<void> _save() async {
    setState(() {
      _busy = true;
      _error = null;
      _ok = null;
    });
    try {
      await ref.read(schoolItRepositoryProvider).updatePolicy(
            name: _name.text.trim().isEmpty ? null : _name.text.trim(),
            schoolCode: _code.text.trim().isEmpty ? null : _code.text.trim(),
            primaryColor: _primaryHex,
            secondaryColor: _secondaryHex,
            logoBytes: _logoBytes,
            logoName: _logoName,
            early: int.tryParse(_early.text.trim()),
            late: int.tryParse(_late.text.trim()),
            signOut: int.tryParse(_signOut.text.trim()),
          );
      ref.invalidate(schoolProvider);
      if (_primaryHex != null) {
        ref
            .read(themeControllerProvider.notifier)
            .setBrandPrimaryHex(_primaryHex);
      }
      if (mounted) setState(() => _ok = 'Saved — branding applied.');
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not save settings.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final meta = ref.watch(sessionControllerProvider).meta;
    final s = ref.watch(schoolProvider).valueOrNull;
    final schoolName = s?.schoolName ?? meta?.schoolName;
    final logoUrl = mediaUrl(s?.logoUrl ?? meta?.logoUrl);
    _initOnce(
      name: schoolName,
      code: s?.schoolCode ?? meta?.schoolCode,
      early: s?.earlyCheckInMinutes ?? 15,
      late: s?.lateThresholdMinutes ?? 10,
      signOut: s?.signOutGraceMinutes ?? 15,
      primary: s?.primaryColor ?? meta?.primaryColor,
      secondary: s?.secondaryColor ?? meta?.secondaryColor,
    );
    final primary = AppColors.parseHex(_primaryHex) ?? t.accent;
    final secondary = AppColors.parseHex(_secondaryHex) ?? t.accentDark;
    final name = _name.text.trim().isEmpty
        ? (schoolName ?? 'Your school')
        : _name.text.trim();

    return AppScaffold(
      title: 'University settings',
      body: ListView(
            padding: const EdgeInsets.fromLTRB(
                AppSpacing.x20, AppSpacing.x16, AppSpacing.x20, 48),
            children: [
              Center(
                child: _BrandPreview(
                  logoBytes: _logoBytes,
                  logoUrl: logoUrl,
                  name: name,
                  primary: primary,
                  secondary: secondary,
                ),
              ),
              const SizedBox(height: AppSpacing.x12),
              Center(
                child: Text('Live preview',
                    style: textTheme.bodySmall?.copyWith(color: t.textMuted)),
              ),
              const SizedBox(height: AppSpacing.x24),
              const SectionHeader(title: 'Logo'),
              AuraCard(
                child: Row(
                  children: [
                    _LogoThumb(logoBytes: _logoBytes, logoUrl: logoUrl),
                    const SizedBox(width: AppSpacing.x16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('School logo', style: textTheme.titleLarge),
                          Text(_logoName ?? 'PNG or JPG, square works best',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: textTheme.bodySmall
                                  ?.copyWith(color: t.textSecondary)),
                        ],
                      ),
                    ),
                    const SizedBox(width: AppSpacing.x12),
                    SizedBox(
                      width: 116,
                      child: AuraButton(
                        label: 'Choose',
                        variant: AuraButtonVariant.tonal,
                        onPressed: _pickLogo,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.x24),
              const SectionHeader(title: 'Identity'),
              AuraTextField(label: 'School name', controller: _name),
              const SizedBox(height: AppSpacing.x12),
              AuraTextField(label: 'School code', controller: _code),
              const SizedBox(height: AppSpacing.x24),
              const SectionHeader(title: 'Brand colours'),
              _ColorRow(
                label: 'Primary',
                palette: _palette,
                selected: _primaryHex,
                onPick: (h) => setState(() => _primaryHex = h),
              ),
              const SizedBox(height: AppSpacing.x12),
              _ColorRow(
                label: 'Secondary',
                palette: _palette,
                selected: _secondaryHex,
                onPick: (h) => setState(() => _secondaryHex = h),
              ),
              const SizedBox(height: AppSpacing.x24),
              const SectionHeader(title: 'Default event policy (minutes)'),
              Row(
                children: [
                  Expanded(
                      child: _NumField(label: 'Early', controller: _early)),
                  const SizedBox(width: AppSpacing.x12),
                  Expanded(child: _NumField(label: 'Late', controller: _late)),
                  const SizedBox(width: AppSpacing.x12),
                  Expanded(
                      child:
                          _NumField(label: 'Sign-out', controller: _signOut)),
                ],
              ),
              if (_error != null) ...[
                const SizedBox(height: AppSpacing.x16),
                Text(_error!,
                    style: textTheme.bodySmall?.copyWith(color: t.absent)),
              ],
              if (_ok != null) ...[
                const SizedBox(height: AppSpacing.x16),
                Text(_ok!,
                    style: textTheme.bodySmall?.copyWith(color: t.present)),
              ],
              const SizedBox(height: AppSpacing.x24),
              AuraButton(
                  label: 'Save changes', loading: _busy, onPressed: _save),
            ],
          ),
    );
  }
}

/// A small phone mock that reflects the chosen logo + colours in real time.
class _BrandPreview extends StatelessWidget {
  const _BrandPreview({
    required this.logoBytes,
    required this.logoUrl,
    required this.name,
    required this.primary,
    required this.secondary,
  });
  final Uint8List? logoBytes;
  final String? logoUrl;
  final String name;
  final Color primary;
  final Color secondary;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final onPrimary =
        primary.computeLuminance() > 0.6 ? Colors.black : Colors.white;

    Widget logo() {
      if (logoBytes != null) {
        return Image.memory(logoBytes!, fit: BoxFit.cover);
      }
      if ((logoUrl ?? '').startsWith('http')) {
        return Image.network(logoUrl!,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => _letter(textTheme, onPrimary));
      }
      return _letter(textTheme, onPrimary);
    }

    return Container(
      width: 186,
      height: 332,
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: t.border),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withOpacity(0.10),
              blurRadius: 28,
              offset: const Offset(0, 12)),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(30),
        child: Column(
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 250),
              curve: Curves.easeOut,
              padding: const EdgeInsets.all(AppSpacing.x12),
              color: primary.withOpacity(0.14),
              child: Row(
                children: [
                  Container(
                    width: 30,
                    height: 30,
                    clipBehavior: Clip.antiAlias,
                    decoration: BoxDecoration(
                        color: primary.withOpacity(0.25),
                        shape: BoxShape.circle),
                    child: Center(child: logo()),
                  ),
                  const SizedBox(width: AppSpacing.x8),
                  Expanded(
                    child: Text(name,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: textTheme.labelLarge),
                  ),
                ],
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.x12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 250),
                      curve: Curves.easeOut,
                      height: 72,
                      width: double.infinity,
                      decoration: BoxDecoration(
                          color: primary,
                          borderRadius: BorderRadius.circular(18)),
                      child: Center(
                        child: Text('92%',
                            style: AppTypography.mono(
                                size: 24,
                                weight: FontWeight.w800,
                                color: onPrimary)),
                      ),
                    ),
                    const SizedBox(height: AppSpacing.x8),
                    Row(
                      children: [
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 250),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                              color: secondary.withOpacity(0.20),
                              borderRadius:
                                  BorderRadius.circular(AppRadii.pill)),
                          child: Text('Compliant',
                              style: textTheme.bodySmall
                                  ?.copyWith(color: secondary)),
                        ),
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                              color: t.surfaceAlt,
                              borderRadius:
                                  BorderRadius.circular(AppRadii.pill)),
                          child: Text('Details',
                              style: textTheme.bodySmall
                                  ?.copyWith(color: t.textMuted)),
                        ),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.x12),
                    for (final w in [120.0, 90.0, 140.0])
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Container(
                            width: w,
                            height: 8,
                            decoration: BoxDecoration(
                                color: t.surfaceAlt,
                                borderRadius: BorderRadius.circular(4))),
                      ),
                  ],
                ),
              ),
            ),
            Container(
              height: 44,
              decoration: BoxDecoration(
                  border: Border(top: BorderSide(color: t.border))),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  Icon(Icons.home_rounded, size: 18, color: primary),
                  Icon(Icons.calendar_today_rounded,
                      size: 16, color: t.textMuted),
                  Icon(Icons.notifications_rounded,
                      size: 16, color: t.textMuted),
                  Icon(Icons.person_rounded, size: 16, color: t.textMuted),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _letter(TextTheme tt, Color color) => Center(
        child: Text(name.isNotEmpty ? name[0].toUpperCase() : 'A',
            style: tt.labelLarge?.copyWith(color: color)),
      );
}

class _LogoThumb extends StatelessWidget {
  const _LogoThumb({required this.logoBytes, required this.logoUrl});
  final Uint8List? logoBytes;
  final String? logoUrl;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    Widget child;
    if (logoBytes != null) {
      child = Image.memory(logoBytes!, fit: BoxFit.cover);
    } else if ((logoUrl ?? '').startsWith('http')) {
      child = Image.network(logoUrl!,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) =>
              Icon(Icons.image_outlined, color: t.textMuted));
    } else {
      child = Icon(Icons.add_photo_alternate_outlined, color: t.textMuted);
    }
    return Container(
      width: 52,
      height: 52,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
          color: t.surfaceAlt,
          borderRadius: BorderRadius.circular(AppRadii.control),
          border: Border.all(color: t.border)),
      child: Center(child: child),
    );
  }
}

class _ColorRow extends StatelessWidget {
  const _ColorRow({
    required this.label,
    required this.palette,
    required this.selected,
    required this.onPick,
  });
  final String label;
  final List<String> palette;
  final String? selected;
  final ValueChanged<String> onPick;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final swatches = [...palette];
    final c = selected;
    if (c != null &&
        !swatches.map((e) => e.toUpperCase()).contains(c.toUpperCase())) {
      swatches.insert(0, c);
    }
    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x12),
          Wrap(
            spacing: AppSpacing.x12,
            runSpacing: AppSpacing.x12,
            children: [
              for (final hex in swatches)
                _Swatch(
                  hex: hex,
                  selected: selected?.toUpperCase() == hex.toUpperCase(),
                  onTap: () => onPick(hex),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Swatch extends StatelessWidget {
  const _Swatch(
      {required this.hex, required this.selected, required this.onTap});
  final String hex;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final color = AppColors.parseHex(hex) ?? t.surfaceAlt;
    final inner = Container(
      width: 34,
      height: 34,
      decoration: BoxDecoration(
        color: color,
        shape: BoxShape.circle,
        border: Border.all(color: Colors.black.withOpacity(0.06)),
      ),
    );
    return GestureDetector(
      onTap: onTap,
      child: selected
          ? Container(
              padding: const EdgeInsets.all(3),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: t.ink, width: 2),
              ),
              child: inner,
            )
          : Padding(padding: const EdgeInsets.all(5), child: inner),
    );
  }
}

class _NumField extends StatelessWidget {
  const _NumField({required this.label, required this.controller});
  final String label;
  final TextEditingController controller;

  @override
  Widget build(BuildContext context) {
    return AuraTextField(
        label: label,
        controller: controller,
        keyboardType: TextInputType.number);
  }
}
