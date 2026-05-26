import 'package:aura_app/features/help/data/help_content.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('HelpContent catalogue', () {
    test('every category has a unique id', () {
      final ids = HelpContent.categories.map((c) => c.id).toList();
      expect(ids.toSet().length, ids.length,
          reason: 'category ids must be unique');
    });

    test('articles inside a category have unique ids', () {
      for (final c in HelpContent.categories) {
        final ids = c.articles.map((a) => a.id).toList();
        expect(ids.toSet().length, ids.length,
            reason: 'article ids in ${c.id} must be unique');
      }
    });

    test('every category exposes at least one article', () {
      for (final c in HelpContent.categories) {
        expect(c.articles, isNotEmpty, reason: 'category ${c.id} is empty');
      }
    });

    test('article bodies and steps are non-empty', () {
      for (final c in HelpContent.categories) {
        for (final a in c.articles) {
          expect(a.title.trim(), isNotEmpty);
          expect(a.body.trim(), isNotEmpty);
          for (final step in a.steps) {
            expect(step.trim(), isNotEmpty,
                reason: 'step in ${c.id}/${a.id} is blank');
          }
        }
      }
    });
  });

  group('HelpContent.search', () {
    test('returns empty list for blank query', () {
      expect(HelpContent.search(''), isEmpty);
      expect(HelpContent.search('   '), isEmpty);
    });

    test('finds an article by a keyword', () {
      final hits = HelpContent.search('face scan');
      expect(hits, isNotEmpty);
      expect(
          hits.any((h) =>
              h.article.id == 'at-face-fails' || h.article.id == 'tb-face'),
          isTrue);
    });

    test('matches case-insensitively', () {
      final lower = HelpContent.search('password');
      final upper = HelpContent.search('PASSWORD');
      expect(lower.length, upper.length);
    });

    test('matches against the keywords list, not just body text', () {
      final hits = HelpContent.search('lost');
      expect(hits.any((h) => h.article.id == 'sec-lost-device'), isTrue);
    });
  });

  group('HelpContent lookups', () {
    test('findArticle returns the expected article', () {
      final a = HelpContent.findArticle('account', 'ac-password');
      expect(a, isNotNull);
      expect(a!.title, contains('password'));
    });

    test('findArticle returns null when missing', () {
      expect(HelpContent.findArticle('account', 'does-not-exist'), isNull);
      expect(HelpContent.findArticle('nope', 'ac-password'), isNull);
    });

    test('findCategory returns the expected category', () {
      final c = HelpContent.findCategory('troubleshooting');
      expect(c, isNotNull);
      expect(c!.title, 'Troubleshooting');
    });

    test('quick-help entries all point to real articles', () {
      for (final q in HelpContent.quickHelp) {
        final article = HelpContent.findArticle(q.categoryId, q.articleId);
        expect(article, isNotNull,
            reason: 'quickHelp "${q.label}" points to a missing article');
      }
    });
  });

  group('Audience filtering', () {
    test('developer-docs is admin-only', () {
      final adminCats = HelpContent.categoriesFor(HelpAudience.admin);
      final studentCats = HelpContent.categoriesFor(HelpAudience.student);
      final publicCats = HelpContent.categoriesFor(HelpAudience.public);

      expect(adminCats.any((c) => c.id == 'developer-docs'), isTrue);
      expect(studentCats.any((c) => c.id == 'developer-docs'), isFalse);
      expect(publicCats.any((c) => c.id == 'developer-docs'), isFalse);
    });

    test('workspaces articles are filtered to their role', () {
      final student =
          HelpContent.categoriesFor(HelpAudience.student).firstWhere(
        (c) => c.id == 'workspaces',
        orElse: () => throw 'workspaces missing for student',
      );
      expect(student.articles.map((a) => a.id), contains('ws-student'));
      expect(
          student.articles.map((a) => a.id), isNot(contains('ws-school-it')));
      expect(student.articles.map((a) => a.id), isNot(contains('ws-admin')));

      final campusAdmin = HelpContent.categoriesFor(HelpAudience.campusAdmin)
          .firstWhere((c) => c.id == 'workspaces');
      expect(
          campusAdmin.articles.map((a) => a.id), contains('ws-school-it'));
      expect(campusAdmin.articles.map((a) => a.id),
          isNot(contains('ws-student')));

      final admin = HelpContent.categoriesFor(HelpAudience.admin)
          .firstWhere((c) => c.id == 'workspaces');
      // Admin sees everything.
      expect(admin.articles.map((a) => a.id),
          containsAll(['ws-student', 'ws-school-it', 'ws-governance', 'ws-admin']));
    });

    test('public viewer sees a trimmed catalogue', () {
      final publicCats = HelpContent.categoriesFor(HelpAudience.public);
      final ids = publicCats.map((c) => c.id).toSet();
      // Public-friendly categories survive.
      expect(ids, containsAll([
        'getting-started',
        'troubleshooting',
        'security',
        'about',
      ]));
      // Authed-only categories are hidden.
      expect(ids, isNot(contains('attendance')));
      expect(ids, isNot(contains('schedule')));
      expect(ids, isNot(contains('assistant')));
      expect(ids, isNot(contains('developer-docs')));
    });

    test('forgot-password article is public-visible', () {
      final publicCats = HelpContent.categoriesFor(HelpAudience.public);
      final account =
          publicCats.where((c) => c.id == 'account').toList();
      // Account category itself is authed-only, but the forgot-password
      // article opts in via its own audiences — categoriesFor still
      // skips the category since articles must pass both filters. Verify
      // the article visibility flag directly.
      final article =
          HelpContent.findArticle('account', 'ac-forgot-password');
      expect(article, isNotNull);
      expect(article!.visibleFor(HelpAudience.public), isTrue);
      expect(article.visibleFor(HelpAudience.student), isTrue);
      // The article remains addressable via searchFor when its parent
      // category permits the viewer. Since `account.audiences` is
      // allAuthed, the public viewer won't see it via categoriesFor.
      expect(account, isEmpty);
    });

    test('searchFor respects audience', () {
      final adminHits = HelpContent.searchFor(HelpAudience.admin, 'api');
      // Admin sees dev-api-reference (developer-docs is admin-only).
      expect(
          adminHits.any((h) => h.article.id == 'dev-api-reference'), isTrue);

      final studentHits = HelpContent.searchFor(HelpAudience.student, 'api');
      // Student does not.
      expect(studentHits.any((h) => h.article.id == 'dev-api-reference'),
          isFalse);
    });
  });
}
