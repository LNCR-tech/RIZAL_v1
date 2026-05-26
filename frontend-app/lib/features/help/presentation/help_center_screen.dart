import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/role.dart';
import '../../../core/auth/session_controller.dart';
import '../../../core/theme/app_motion.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/widgets/app_scaffold.dart';
import '../../../core/widgets/aura_card.dart';
import '../../../core/widgets/pressable.dart';
import '../../../core/widgets/rise_in.dart';
import '../data/help_content.dart';

/// Maps the current session to a [HelpAudience]. Public viewers (login
/// screen, no session) see the trimmed-down public help; staff and platform
/// admins see their role-specific + dev docs section.
HelpAudience audienceForSession(SessionState session) {
  if (!session.isAuthenticated) return HelpAudience.public;
  switch (session.workspace) {
    case Workspace.student:
      return HelpAudience.student;
    case Workspace.schoolIt:
      return HelpAudience.campusAdmin;
    case Workspace.governance:
      return HelpAudience.governance;
    case Workspace.admin:
      return HelpAudience.admin;
  }
}

/// In-app Help Center — a single, searchable surface for guides,
/// troubleshooting, and contact. Source content lives in [HelpContent], which
/// mirrors `docs/user-guide/*.md` and `docs/technical/*` for admins.
///
/// Pass [audience] to force a specific tier (used by the login screen for the
/// public catalogue). When omitted, the audience is derived from the current
/// session so each role sees a tailored set: students get attendance + AI,
/// campus admins get user/import/governance, super admins get developer docs.
///
/// Design notes (ui-ux-pro-max + emil + frontend-design):
///   • Editorial type hierarchy (Manrope display + body).
///   • Search is the hero — a soft pill that filters articles live.
///   • Categories are accordion cards with stagger-on-mount.
///   • Articles open in a draggable bottom sheet so users stay in context.
///   • Motion follows [AppMotion]: ease-out under 300ms, respect reduced motion.
class HelpCenterScreen extends ConsumerStatefulWidget {
  const HelpCenterScreen({super.key, this.audience});

  /// Explicit viewer tier. When null, derived from the current session.
  final HelpAudience? audience;

  @override
  ConsumerState<HelpCenterScreen> createState() => _HelpCenterScreenState();
}

class _HelpCenterScreenState extends ConsumerState<HelpCenterScreen> {
  final TextEditingController _query = TextEditingController();
  final FocusNode _focus = FocusNode();
  String _trimmed = '';

  @override
  void initState() {
    super.initState();
    _query.addListener(_onQueryChanged);
  }

  void _onQueryChanged() {
    final next = _query.text.trim();
    if (next == _trimmed) return;
    setState(() => _trimmed = next);
  }

  @override
  void dispose() {
    _query.removeListener(_onQueryChanged);
    _query.dispose();
    _focus.dispose();
    super.dispose();
  }

  void _openArticle(HelpCategory category, HelpArticle article) {
    _focus.unfocus();
    _showArticleSheet(context, category: category, article: article);
  }

  void _runSearch(String text) {
    _query.text = text;
    _query.selection = TextSelection.collapsed(offset: text.length);
    setState(() => _trimmed = text);
    _focus.requestFocus();
  }

  @override
  Widget build(BuildContext context) {
    final searching = _trimmed.isNotEmpty;
    final viewer = widget.audience ??
        audienceForSession(ref.watch(sessionControllerProvider));
    final visibleCategories = HelpContent.categoriesFor(viewer);
    final hits =
        searching ? HelpContent.searchFor(viewer, _trimmed) : const [];
    // Quick-help chips only deep-link into articles the viewer can see.
    final quickHelp = [
      for (final q in HelpContent.quickHelp)
        if (HelpContent.findArticle(q.categoryId, q.articleId)
                ?.visibleFor(viewer) ??
            false)
          q,
    ];

    return AppScaffold(
      title: 'Help Center',
      body: ListView(
        keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.x20, AppSpacing.x8, AppSpacing.x20, 130),
        children: staggered([
          _IntroHeader(audience: viewer),
          const SizedBox(height: AppSpacing.x16),
          _SearchField(
            controller: _query,
            focusNode: _focus,
            onClear: () {
              _query.clear();
              setState(() => _trimmed = '');
            },
          ),
          const SizedBox(height: AppSpacing.x16),
          if (!searching) ...[
            if (quickHelp.isNotEmpty)
              _QuickHelpRow(
                entries: quickHelp,
                onPick: (label, categoryId, articleId) {
                  final cat = HelpContent.findCategory(categoryId);
                  final art = HelpContent.findArticle(categoryId, articleId);
                  if (cat != null && art != null) _openArticle(cat, art);
                },
              ),
            if (quickHelp.isNotEmpty)
              const SizedBox(height: AppSpacing.x24),
            _CategoryHeader(
                label: 'BROWSE BY TOPIC', count: visibleCategories.length),
            const SizedBox(height: AppSpacing.x8),
            for (final c in visibleCategories) ...[
              _CategoryCard(
                category: c,
                onOpenArticle: (a) => _openArticle(c, a),
              ),
              const SizedBox(height: AppSpacing.x12),
            ],
            const SizedBox(height: AppSpacing.x12),
            const _ContactCard(),
            const SizedBox(height: AppSpacing.x16),
            const _Footer(),
          ] else ...[
            _ResultsHeader(query: _trimmed, count: hits.length),
            const SizedBox(height: AppSpacing.x8),
            if (hits.isEmpty)
              _EmptyResults(query: _trimmed, onPick: _runSearch)
            else
              for (final hit in hits) ...[
                _SearchResultRow(
                  category: hit.category,
                  article: hit.article,
                  query: _trimmed,
                  onTap: () => _openArticle(hit.category, hit.article),
                ),
                const SizedBox(height: AppSpacing.x8),
              ],
          ],
        ]),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Header
// ─────────────────────────────────────────────────────────────────────────────

class _IntroHeader extends StatelessWidget {
  const _IntroHeader({required this.audience});

  final HelpAudience audience;

  String get _subtitle {
    switch (audience) {
      case HelpAudience.public:
        return 'Signing in, getting started, and reaching support — everything you need before your first session.';
      case HelpAudience.student:
        return 'Attendance, schedule, your account — everything you need to run your day in Aura.';
      case HelpAudience.campusAdmin:
        return 'Managing users, imports, school settings, and student government — your daily campus-admin playbook.';
      case HelpAudience.governance:
        return 'Running events, managing officers, and exporting reports — your governance toolkit.';
      case HelpAudience.admin:
        return 'Operations, developer docs, and SaaS billing — everything to run Aura across schools.';
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('How can we help?', style: textTheme.displaySmall),
        const SizedBox(height: AppSpacing.x8),
        Text(
          _subtitle,
          style: textTheme.bodyMedium?.copyWith(color: t.textSecondary),
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Search field — pill, surfaceAlt fill, leading search icon, clear button.
// ─────────────────────────────────────────────────────────────────────────────

class _SearchField extends StatelessWidget {
  const _SearchField({
    required this.controller,
    required this.focusNode,
    required this.onClear,
  });

  final TextEditingController controller;
  final FocusNode focusNode;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AnimatedBuilder(
      animation: Listenable.merge([controller, focusNode]),
      builder: (context, _) {
        final hasText = controller.text.isNotEmpty;
        final focused = focusNode.hasFocus;
        return AnimatedContainer(
          duration: AppMotion.popover,
          curve: AppMotion.easeOut,
          height: 56,
          decoration: BoxDecoration(
            color: focused ? t.surface : t.surfaceAlt,
            borderRadius: AppRadii.rPill,
            border: Border.all(
              color: focused
                  ? t.accent.withOpacity(0.55)
                  : t.border.withOpacity(0.6),
              width: focused ? 1.5 : 1,
            ),
            boxShadow: focused
                ? [
                    BoxShadow(
                      color: t.accent.withOpacity(0.18),
                      blurRadius: 18,
                      offset: const Offset(0, 6),
                    ),
                  ]
                : t.brightness == Brightness.light
                    ? const [
                        BoxShadow(
                          color: Color(0x0A000000),
                          blurRadius: 14,
                          offset: Offset(0, 6),
                        ),
                      ]
                    : const [],
          ),
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x16),
          child: Row(
            children: [
              AnimatedScale(
                duration: AppMotion.popover,
                curve: AppMotion.easeOut,
                scale: focused ? 1.08 : 1.0,
                child: Icon(
                  Icons.search_rounded,
                  color: focused ? t.accent : t.textMuted,
                  size: 22,
                ),
              ),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: TextField(
                  controller: controller,
                  focusNode: focusNode,
                  textInputAction: TextInputAction.search,
                  cursorColor: t.accent,
                  cursorWidth: 1.8,
                  decoration: InputDecoration(
                    border: InputBorder.none,
                    isCollapsed: true,
                    contentPadding: const EdgeInsets.symmetric(
                        vertical: AppSpacing.x16),
                    hintText: 'Search guides, FAQ, troubleshooting…',
                    hintStyle: textTheme.bodyLarge
                        ?.copyWith(color: t.textMuted),
                  ),
                  style: textTheme.bodyLarge,
                ),
              ),
              AnimatedSwitcher(
                duration: AppMotion.popover,
                switchInCurve: AppMotion.easeOut,
                switchOutCurve: AppMotion.easeOut,
                transitionBuilder: (child, animation) => FadeTransition(
                  opacity: animation,
                  child: ScaleTransition(scale: animation, child: child),
                ),
                child: hasText
                    ? Pressable(
                        key: const ValueKey('clear'),
                        scale: 0.9,
                        haptic: false,
                        onTap: onClear,
                        child: Container(
                          margin: const EdgeInsets.only(left: AppSpacing.x4),
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(
                            color: t.surfaceAlt,
                            shape: BoxShape.circle,
                            border: Border.all(color: t.border),
                          ),
                          child: Icon(Icons.close_rounded,
                              color: t.textSecondary, size: 16),
                        ),
                      )
                    : const SizedBox.shrink(key: ValueKey('empty')),
              ),
            ],
          ),
        );
      },
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Quick help row — chips for the most-asked questions.
// ─────────────────────────────────────────────────────────────────────────────

class _QuickHelpRow extends StatelessWidget {
  const _QuickHelpRow({required this.entries, required this.onPick});

  final List<({String label, String categoryId, String articleId})> entries;
  final void Function(String label, String categoryId, String articleId) onPick;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: AppSpacing.x4),
          child: Text(
            'QUICK HELP',
            style: textTheme.labelSmall
                ?.copyWith(color: t.textMuted, letterSpacing: 0.8),
          ),
        ),
        const SizedBox(height: AppSpacing.x8),
        SizedBox(
          height: 40,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: entries.length,
            separatorBuilder: (_, __) => const SizedBox(width: AppSpacing.x8),
            itemBuilder: (context, i) {
              final q = entries[i];
              return _QuickHelpChip(
                label: q.label,
                onTap: () => onPick(q.label, q.categoryId, q.articleId),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _QuickHelpChip extends StatelessWidget {
  const _QuickHelpChip({required this.label, required this.onTap});
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Pressable(
      onTap: onTap,
      scale: 0.97,
      child: Container(
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x16, vertical: AppSpacing.x8),
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius: AppRadii.rPill,
          border: Border.all(color: t.border),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.bolt_rounded, size: 16, color: t.accent),
            const SizedBox(width: AppSpacing.x8),
            Text(label,
                style: textTheme.bodyMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Section + Result headers
// ─────────────────────────────────────────────────────────────────────────────

class _CategoryHeader extends StatelessWidget {
  const _CategoryHeader({required this.label, required this.count});
  final String label;
  final int count;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(left: AppSpacing.x4),
      child: Row(
        children: [
          Text(label,
              style: textTheme.labelSmall
                  ?.copyWith(color: t.textMuted, letterSpacing: 0.8)),
          const SizedBox(width: AppSpacing.x8),
          Text('$count topics',
              style: textTheme.labelSmall
                  ?.copyWith(color: t.textMuted, letterSpacing: 0.4)),
        ],
      ),
    );
  }
}

class _ResultsHeader extends StatelessWidget {
  const _ResultsHeader({required this.query, required this.count});
  final String query;
  final int count;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(left: AppSpacing.x4),
      child: Text(
        count == 0
            ? 'No matches for "$query"'
            : '$count result${count == 1 ? '' : 's'} for "$query"',
        style: textTheme.labelSmall
            ?.copyWith(color: t.textMuted, letterSpacing: 0.4),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Category accordion card
// ─────────────────────────────────────────────────────────────────────────────

class _CategoryCard extends StatefulWidget {
  const _CategoryCard({required this.category, required this.onOpenArticle});
  final HelpCategory category;
  final ValueChanged<HelpArticle> onOpenArticle;

  @override
  State<_CategoryCard> createState() => _CategoryCardState();
}

class _CategoryCardState extends State<_CategoryCard> {
  bool _open = false;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    final c = widget.category;
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    return AuraCard(
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Pressable(
            scale: 0.99,
            onTap: () => setState(() => _open = !_open),
            child: Padding(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.x16, vertical: AppSpacing.x16),
              child: Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: c.color,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(c.icon, color: Colors.white, size: 20),
                  ),
                  const SizedBox(width: AppSpacing.x12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(c.title, style: textTheme.titleLarge),
                        const SizedBox(height: 2),
                        Text(c.summary,
                            style: textTheme.bodySmall
                                ?.copyWith(color: t.textSecondary)),
                      ],
                    ),
                  ),
                  const SizedBox(width: AppSpacing.x8),
                  _CountPill(count: c.articles.length, color: c.color),
                  const SizedBox(width: AppSpacing.x8),
                  AnimatedRotation(
                    turns: _open ? 0.5 : 0,
                    duration:
                        reduce ? Duration.zero : AppMotion.dropdown,
                    curve: AppMotion.easeOut,
                    child: Icon(Icons.keyboard_arrow_down_rounded,
                        color: t.textMuted),
                  ),
                ],
              ),
            ),
          ),
          AnimatedSize(
            duration: reduce ? Duration.zero : AppMotion.dropdown,
            curve: AppMotion.easeOut,
            alignment: Alignment.topCenter,
            child: ClipRect(
              child: !_open
                  ? const SizedBox(width: double.infinity)
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Divider(
                            height: 1,
                            thickness: 1,
                            indent: 64,
                            color: t.border),
                        for (var i = 0; i < c.articles.length; i++) ...[
                          _ArticleRow(
                            article: c.articles[i],
                            accent: c.color,
                            onTap: () => widget.onOpenArticle(c.articles[i]),
                          ),
                          if (i != c.articles.length - 1)
                            Divider(
                                height: 1,
                                thickness: 1,
                                indent: 64,
                                color: t.border),
                        ],
                      ],
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CountPill extends StatelessWidget {
  const _CountPill({required this.count, required this.color});
  final int count;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: AppSpacing.x8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.14),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        '$count',
        style: TextStyle(
          color: color,
          fontFamily: 'JetBrainsMono',
          fontSize: 12,
          height: 1,
          fontWeight: FontWeight.w800,
          fontFeatures: const [FontFeature.tabularFigures()],
        ),
      ),
    );
  }
}

class _ArticleRow extends StatelessWidget {
  const _ArticleRow({
    required this.article,
    required this.accent,
    required this.onTap,
  });
  final HelpArticle article;
  final Color accent;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Pressable(
      scale: 0.99,
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x16, vertical: AppSpacing.x12),
        child: Row(
          children: [
            // A thin tinted bar mirrors the category colour without repeating
            // the full icon tile — keeps the list scannable.
            Container(
              width: 4,
              height: 28,
              decoration: BoxDecoration(
                color: accent,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(width: AppSpacing.x16),
            Expanded(
              child: Text(article.title, style: textTheme.bodyLarge),
            ),
            const SizedBox(width: AppSpacing.x8),
            Icon(Icons.arrow_forward_ios_rounded,
                color: t.textMuted, size: 14),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Search results
// ─────────────────────────────────────────────────────────────────────────────

class _SearchResultRow extends StatelessWidget {
  const _SearchResultRow({
    required this.category,
    required this.article,
    required this.query,
    required this.onTap,
  });
  final HelpCategory category;
  final HelpArticle article;
  final String query;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AuraCard(
      padding: EdgeInsets.zero,
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x16, vertical: AppSpacing.x16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: category.color,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(category.icon, color: Colors.white, size: 20),
            ),
            const SizedBox(width: AppSpacing.x12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(category.title.toUpperCase(),
                          style: textTheme.labelSmall?.copyWith(
                              color: category.color,
                              letterSpacing: 0.8,
                              fontWeight: FontWeight.w700)),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(article.title, style: textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text(
                    _snippet(article.body, query),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: textTheme.bodySmall
                        ?.copyWith(color: t.textSecondary, height: 1.45),
                  ),
                ],
              ),
            ),
            const SizedBox(width: AppSpacing.x8),
            Icon(Icons.arrow_forward_ios_rounded,
                color: t.textMuted, size: 14),
          ],
        ),
      ),
    );
  }

  /// Returns a ~120-char snippet centered around the first match of [query].
  String _snippet(String body, String query) {
    if (query.isEmpty) return body;
    final lower = body.toLowerCase();
    final i = lower.indexOf(query.toLowerCase());
    if (i < 0) return body;
    const radius = 60;
    final start = (i - radius).clamp(0, body.length);
    final end = (i + query.length + radius).clamp(0, body.length);
    final prefix = start > 0 ? '… ' : '';
    final suffix = end < body.length ? ' …' : '';
    return '$prefix${body.substring(start, end)}$suffix';
  }
}

class _EmptyResults extends StatelessWidget {
  const _EmptyResults({required this.query, required this.onPick});
  final String query;
  final ValueChanged<String> onPick;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return AuraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: t.surfaceAlt,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.search_off_rounded,
                    color: t.textSecondary, size: 22),
              ),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('No results',
                        style: textTheme.titleMedium),
                    const SizedBox(height: 2),
                    Text(
                      'We could not find help for "$query". Try one of these:',
                      style: textTheme.bodySmall
                          ?.copyWith(color: t.textSecondary),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.x16),
          Wrap(
            spacing: AppSpacing.x8,
            runSpacing: AppSpacing.x8,
            children: [
              for (final q in const [
                'login',
                'face',
                'password',
                'permissions',
                'late',
                'reset',
              ])
                Pressable(
                  scale: 0.97,
                  onTap: () => onPick(q),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.x12, vertical: AppSpacing.x8),
                    decoration: BoxDecoration(
                      color: t.surfaceAlt,
                      borderRadius: AppRadii.rPill,
                      border: Border.all(color: t.border),
                    ),
                    child: Text(q,
                        style: textTheme.bodyMedium
                            ?.copyWith(fontWeight: FontWeight.w600)),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Contact card + footer
// ─────────────────────────────────────────────────────────────────────────────

class _ContactCard extends StatelessWidget {
  const _ContactCard();

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: AppSpacing.x4),
          child: Text('CONTACT SUPPORT',
              style: textTheme.labelSmall
                  ?.copyWith(color: t.textMuted, letterSpacing: 0.8)),
        ),
        const SizedBox(height: AppSpacing.x8),
        AuraCard(
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              const _ContactRow(
                icon: Icons.support_agent_rounded,
                iconColor: Color(0xFF6366F1),
                label: 'Campus Admin',
                value: HelpContent.supportEmail,
              ),
              Divider(height: 1, thickness: 1, indent: 64, color: t.border),
              const _ContactRow(
                icon: Icons.terminal_rounded,
                iconColor: Color(0xFF14B8A6),
                label: 'IT support',
                value: HelpContent.itEmail,
              ),
              Divider(height: 1, thickness: 1, indent: 64, color: t.border),
              const _ContactRow(
                icon: Icons.menu_book_rounded,
                iconColor: Color(0xFFEC4899),
                label: 'Full documentation',
                value: HelpContent.docsHomepage,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ContactRow extends StatelessWidget {
  const _ContactRow({
    required this.icon,
    required this.iconColor,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final Color iconColor;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Pressable(
      scale: 0.99,
      onTap: () async {
        await Clipboard.setData(ClipboardData(text: value));
        if (!context.mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Copied $value')),
        );
      },
      child: Padding(
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x16, vertical: AppSpacing.x12),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: iconColor,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: Colors.white, size: 20),
            ),
            const SizedBox(width: AppSpacing.x12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: textTheme.bodyLarge),
                  const SizedBox(height: 2),
                  Text(value,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: textTheme.bodySmall?.copyWith(
                        color: t.textSecondary,
                        fontFamily: 'JetBrainsMono',
                      )),
                ],
              ),
            ),
            const SizedBox(width: AppSpacing.x8),
            Icon(Icons.copy_rounded, color: t.textMuted, size: 18),
          ],
        ),
      ),
    );
  }
}

class _Footer extends StatelessWidget {
  const _Footer();

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(top: AppSpacing.x8),
      child: Center(
        child: Text(
          'Aura v${HelpContent.appVersion} · build ${HelpContent.appBuild} · powered by Jose AI',
          style: textTheme.labelSmall?.copyWith(
            color: t.textMuted,
            fontFamily: 'JetBrainsMono',
            letterSpacing: 0.2,
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Article bottom sheet
// ─────────────────────────────────────────────────────────────────────────────

void _showArticleSheet(
  BuildContext context, {
  required HelpCategory category,
  required HelpArticle article,
}) {
  final t = AppTokens.of(context);
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: t.surface,
    barrierColor: Colors.black.withOpacity(0.40),
    shape: const RoundedRectangleBorder(borderRadius: AppRadii.rSheet),
    builder: (sheetCtx) {
      return DraggableScrollableSheet(
        initialChildSize: 0.75,
        minChildSize: 0.45,
        maxChildSize: 0.95,
        expand: false,
        builder: (context, scrollController) {
          return _ArticleSheet(
            category: category,
            article: article,
            scrollController: scrollController,
          );
        },
      );
    },
  );
}

class _ArticleSheet extends StatelessWidget {
  const _ArticleSheet({
    required this.category,
    required this.article,
    required this.scrollController,
  });

  final HelpCategory category;
  final HelpArticle article;
  final ScrollController scrollController;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Drag handle.
        Center(
          child: Container(
            margin: const EdgeInsets.only(top: AppSpacing.x12),
            width: 38,
            height: 4,
            decoration: BoxDecoration(
              color: t.border,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ),
        Expanded(
          child: ListView(
            controller: scrollController,
            padding: const EdgeInsets.fromLTRB(AppSpacing.x20,
                AppSpacing.x20, AppSpacing.x20, AppSpacing.x32),
            children: [
              _CategoryChip(category: category),
              const SizedBox(height: AppSpacing.x16),
              Text(article.title, style: textTheme.headlineSmall),
              const SizedBox(height: AppSpacing.x16),
              Text(
                article.body,
                style: textTheme.bodyLarge?.copyWith(height: 1.55),
              ),
              if (article.steps.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.x24),
                _StepsBlock(steps: article.steps, accent: category.color),
              ],
              if (article.tip != null) ...[
                const SizedBox(height: AppSpacing.x24),
                _TipCallout(text: article.tip!, accent: category.color),
              ],
              const SizedBox(height: AppSpacing.x32),
              _SheetFooter(category: category),
            ],
          ),
        ),
      ],
    );
  }
}

class _CategoryChip extends StatelessWidget {
  const _CategoryChip({required this.category});
  final HelpCategory category;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x12, vertical: 6),
        decoration: BoxDecoration(
          color: category.color.withOpacity(0.14),
          borderRadius: AppRadii.rPill,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(category.icon, color: category.color, size: 14),
            const SizedBox(width: AppSpacing.x8),
            Text(
              category.title.toUpperCase(),
              style: textTheme.labelSmall?.copyWith(
                color: category.color,
                letterSpacing: 0.8,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StepsBlock extends StatelessWidget {
  const _StepsBlock({required this.steps, required this.accent});
  final List<String> steps;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('STEPS',
            style: textTheme.labelSmall
                ?.copyWith(color: t.textMuted, letterSpacing: 0.8)),
        const SizedBox(height: AppSpacing.x12),
        for (var i = 0; i < steps.length; i++) ...[
          if (i != 0) const SizedBox(height: AppSpacing.x12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 26,
                height: 26,
                decoration: BoxDecoration(
                  color: accent.withOpacity(0.14),
                  borderRadius: BorderRadius.circular(8),
                ),
                alignment: Alignment.center,
                child: Text(
                  '${i + 1}',
                  style: TextStyle(
                    color: accent,
                    fontFamily: 'JetBrainsMono',
                    fontSize: 12,
                    height: 1,
                    fontWeight: FontWeight.w800,
                    fontFeatures: const [FontFeature.tabularFigures()],
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.x12),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(top: 3),
                  child: Text(steps[i],
                      style: textTheme.bodyMedium?.copyWith(height: 1.55)),
                ),
              ),
            ],
          ),
        ],
      ],
    );
  }
}

class _TipCallout extends StatelessWidget {
  const _TipCallout({required this.text, required this.accent});
  final String text;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.all(AppSpacing.x16),
      decoration: BoxDecoration(
        color: t.surfaceAlt,
        borderRadius: AppRadii.rControl,
        border: Border(
          left: BorderSide(color: accent, width: 3),
          top: BorderSide(color: t.border),
          right: BorderSide(color: t.border),
          bottom: BorderSide(color: t.border),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.lightbulb_outline_rounded,
              color: accent, size: 18),
          const SizedBox(width: AppSpacing.x12),
          Expanded(
            child: Text(
              text,
              style: textTheme.bodyMedium?.copyWith(
                color: t.ink,
                height: 1.5,
                fontStyle: FontStyle.italic,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SheetFooter extends StatelessWidget {
  const _SheetFooter({required this.category});
  final HelpCategory category;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;
    return Center(
      child: Text(
        'Need more? Contact support from the Help Center.',
        style: textTheme.labelSmall
            ?.copyWith(color: t.textMuted, letterSpacing: 0.2),
      ),
    );
  }
}
