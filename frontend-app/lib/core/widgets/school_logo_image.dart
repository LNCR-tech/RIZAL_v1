import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../cache/school_logo_cache.dart';

/// Disk-cached `Image.network` replacement for the signed-in school's logo.
///
/// On mount: looks in [SchoolLogoCache] first, renders [Image.memory] from
/// disk bytes if hit. On miss: fetches over HTTP, writes through to disk,
/// then renders. After the first cold start the logo is essentially free —
/// no network round-trip, no flash of the fallback letter.
///
/// Pass [placeholder] for the first-paint shimmer (typically the school's
/// initial inside the gradient ring) and [errorBuilder] for the offline /
/// 404 case.
class SchoolLogoImage extends ConsumerStatefulWidget {
  const SchoolLogoImage({
    super.key,
    required this.url,
    this.schoolId,
    this.fit = BoxFit.cover,
    this.placeholder,
    this.errorBuilder,
  });

  /// Absolute URL — caller should resolve via `mediaUrl(...)` first.
  final String url;
  final int? schoolId;
  final BoxFit fit;
  final Widget? placeholder;
  final WidgetBuilder? errorBuilder;

  @override
  ConsumerState<SchoolLogoImage> createState() => _SchoolLogoImageState();
}

class _SchoolLogoImageState extends ConsumerState<SchoolLogoImage> {
  Uint8List? _bytes;
  bool _failed = false;

  @override
  void initState() {
    super.initState();
    _resolve();
  }

  @override
  void didUpdateWidget(SchoolLogoImage old) {
    super.didUpdateWidget(old);
    if (old.url != widget.url || old.schoolId != widget.schoolId) {
      _bytes = null;
      _failed = false;
      _resolve();
    }
  }

  Future<void> _resolve() async {
    final cache = ref.read(schoolLogoCacheProvider);
    final cached = await cache.read(widget.url, widget.schoolId);
    if (!mounted) return;
    if (cached != null) {
      setState(() => _bytes = cached);
      return;
    }
    final fetched = await cache.fetchAndStore(widget.url, widget.schoolId);
    if (!mounted) return;
    setState(() {
      _bytes = fetched;
      _failed = fetched == null;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_bytes != null) {
      return Image.memory(
        _bytes!,
        fit: widget.fit,
        gaplessPlayback: true,
        errorBuilder: (c, _, __) =>
            widget.errorBuilder?.call(c) ?? const SizedBox.shrink(),
      );
    }
    if (_failed) {
      return widget.errorBuilder?.call(context) ?? const SizedBox.shrink();
    }
    return widget.placeholder ?? const SizedBox.shrink();
  }
}
