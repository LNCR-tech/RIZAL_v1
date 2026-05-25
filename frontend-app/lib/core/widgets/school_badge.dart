import 'package:flutter/material.dart';

import '../network/media_url.dart';
import '../theme/app_colors.dart';
import '../theme/app_tokens.dart';

/// A circular school logo inside a brand gradient ring (school primary →
/// secondary), falling back to the school's first initial. Resolves relative
/// `logo_url`s and uses the **secondary** brand colour so it's actually applied.
class SchoolBadge extends StatelessWidget {
  const SchoolBadge({
    super.key,
    required this.logoUrl,
    this.schoolName,
    this.size = 44,
    this.primaryHex,
    this.secondaryHex,
  });

  final String? logoUrl;
  final String? schoolName;
  final double size;
  final String? primaryHex;
  final String? secondaryHex;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final primary = AppColors.parseHex(primaryHex) ?? t.accent;
    final secondary = AppColors.parseHex(secondaryHex) ?? t.accentDark;
    final url = mediaUrl(logoUrl);
    final name = (schoolName ?? '').trim();
    final letter = name.isNotEmpty ? name[0].toUpperCase() : 'A';

    return Container(
      width: size,
      height: size,
      padding: const EdgeInsets.all(2.5),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [secondary, primary],
        ),
      ),
      child: Container(
        decoration: BoxDecoration(shape: BoxShape.circle, color: t.surface),
        clipBehavior: Clip.antiAlias,
        child: url != null
            ? Image.network(url,
                fit: BoxFit.cover,
                gaplessPlayback: true,
                // Show the letter while the logo loads, instead of a blank disc.
                loadingBuilder: (_, child, progress) =>
                    progress == null ? child : _Fallback(letter, primary, size),
                errorBuilder: (_, __, ___) => _Fallback(letter, primary, size))
            : _Fallback(letter, primary, size),
      ),
    );
  }
}

class _Fallback extends StatelessWidget {
  const _Fallback(this.letter, this.color, this.size);
  final String letter;
  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) => Center(
        child: Text(
          letter,
          style: TextStyle(
              color: color, fontWeight: FontWeight.w800, fontSize: size * 0.4),
        ),
      );
}
