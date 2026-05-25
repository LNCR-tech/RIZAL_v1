import 'package:flutter/material.dart';

import '../theme/app_tokens.dart';

/// Standard screen scaffold: themed background, optional app bar, optional
/// pull-to-refresh, and a floating bottom nav (body extends behind it).
class AppScaffold extends StatelessWidget {
  const AppScaffold({
    super.key,
    required this.body,
    this.bottomNav,
    this.title,
    this.titleWidget,
    this.actions,
    this.onRefresh,
    this.padding,
    this.leading,
  });

  final Widget body;
  final Widget? bottomNav;
  final String? title;
  final Widget? titleWidget;
  final List<Widget>? actions;
  final Future<void> Function()? onRefresh;
  final EdgeInsetsGeometry? padding;
  final Widget? leading;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);

    Widget content = body;
    if (padding != null) content = Padding(padding: padding!, child: content);
    if (onRefresh != null) {
      content = RefreshIndicator(
        onRefresh: onRefresh!,
        color: t.accent,
        backgroundColor: t.surface,
        child: content,
      );
    }

    final hasBar = title != null || titleWidget != null || leading != null;

    return Scaffold(
      backgroundColor: t.bg,
      extendBody: true,
      appBar: hasBar
          ? AppBar(
              leading: leading,
              title: titleWidget ?? (title != null ? Text(title!) : null),
              actions: actions,
            )
          : null,
      body: SafeArea(bottom: false, child: content),
      bottomNavigationBar: bottomNav,
    );
  }
}
