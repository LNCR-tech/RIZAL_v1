import 'package:aura_app/core/theme/contrast.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('chooses dark text on the bright lime accent', () {
    expect(contrastText(const Color(0xFFAAFF00)).computeLuminance() < 0.5, isTrue);
  });

  test('chooses light text on near-black ink', () {
    expect(contrastText(const Color(0xFF0A0A0A)).computeLuminance() > 0.5, isTrue);
  });
}
