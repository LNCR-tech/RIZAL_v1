import 'package:aura_app/core/network/paginated.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('unwraps a bare list', () {
    final p = Paginated.from([1, 2, 3], (e) => e as int);
    expect(p.data, [1, 2, 3]);
    expect(p.total, 3);
    expect(p.page, 1);
    expect(p.totalPages, 1);
  });

  test('unwraps the {data,...} envelope', () {
    final p = Paginated.from({
      'data': [
        {'id': 1}
      ],
      'page': 2,
      'total': 10,
      'total_pages': 5,
      'limit': 2,
      'next': '/x',
    }, (e) => (e as Map)['id'] as int);
    expect(p.data, [1]);
    expect(p.page, 2);
    expect(p.total, 10);
    expect(p.hasNext, isTrue);
  });

  test('falls back to empty for unexpected payloads', () {
    expect(Paginated.from(42, (e) => e).isEmpty, isTrue);
    expect(Paginated.from(null, (e) => e).isEmpty, isTrue);
  });
}
