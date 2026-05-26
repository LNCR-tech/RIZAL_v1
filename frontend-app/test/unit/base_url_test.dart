import 'package:aura_app/core/network/base_url.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('strips trailing slashes', () {
    expect(BackendBaseUrl.normalize('https://api.x.com/'), 'https://api.x.com');
  });
  test('drops a trailing /api', () {
    expect(BackendBaseUrl.normalize('https://api.x.com/api'), 'https://api.x.com');
  });
  test('keeps a non-/api path', () {
    expect(BackendBaseUrl.normalize('https://x.com/backend'), 'https://x.com/backend');
  });
  test('bare /api resolves to empty (same-origin)', () {
    expect(BackendBaseUrl.normalize('/api'), '');
  });
  test('keeps a relative proxy path', () {
    expect(BackendBaseUrl.normalize('/__backend__/'), '/__backend__');
  });
}
