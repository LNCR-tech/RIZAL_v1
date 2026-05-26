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
}
