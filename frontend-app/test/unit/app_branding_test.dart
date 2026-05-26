import 'package:aura_app/core/auth/auth_meta.dart';
import 'package:aura_app/core/theme/app_branding_controller.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // Drains the microtask queue + SharedPreferences future chain so the
  // controller's async `_restore()` has finished by the time the assertion
  // runs. A single `Duration.zero` delay isn't always enough — _restore
  // itself awaits getInstance().
  Future<void> settle() async {
    for (var i = 0; i < 3; i++) {
      await Future<void>.delayed(Duration.zero);
    }
  }

  group('AppBrandingPref', () {
    test('defaults are off and snapshot fields are null', () {
      const p = AppBrandingPref();
      expect(p.useSchoolLogo, isFalse);
      expect(p.useSchoolCodeAsName, isFalse);
      expect(p.schoolCode, isNull);
      expect(p.schoolLogoUrl, isNull);
      expect(p.hasLogo, isFalse);
      expect(p.hasCode, isFalse);
    });

    test('resolvedAppName falls back to "Aura" by default', () {
      expect(const AppBrandingPref().resolvedAppName(), 'Aura');
    });

    test('resolvedAppName uses school code when opted in and present', () {
      const p = AppBrandingPref(
        useSchoolCodeAsName: true,
        schoolCode: 'JRMSU',
      );
      expect(p.resolvedAppName(), 'JRMSU');
    });

    test('resolvedAppName falls back when opted in but code missing', () {
      const p = AppBrandingPref(useSchoolCodeAsName: true);
      expect(p.resolvedAppName(), 'Aura');
      expect(p.resolvedAppName(fallback: 'Campus'), 'Campus');
    });

    test('effectiveUseSchoolLogo requires opt-in AND a non-empty url', () {
      expect(const AppBrandingPref().effectiveUseSchoolLogo, isFalse);
      expect(const AppBrandingPref(useSchoolLogo: true).effectiveUseSchoolLogo,
          isFalse);
      expect(
        const AppBrandingPref(
                useSchoolLogo: true, schoolLogoUrl: '/school-logos/x.png')
            .effectiveUseSchoolLogo,
        isTrue,
      );
    });

    test('JSON round-trip preserves toggles and snapshot', () {
      const p = AppBrandingPref(
        useSchoolLogo: true,
        useSchoolCodeAsName: true,
        schoolId: 42,
        schoolCode: 'JRMSU',
        schoolName: 'Jose Rizal MSU',
        schoolLogoUrl: '/school-logos/jrmsu.png',
        schoolPrimaryHex: '#AAFF00',
        schoolSecondaryHex: '#8B5CF6',
      );
      final round = AppBrandingPref.fromJson(p.toJson());
      expect(round.useSchoolLogo, isTrue);
      expect(round.useSchoolCodeAsName, isTrue);
      expect(round.schoolId, 42);
      expect(round.schoolCode, 'JRMSU');
      expect(round.schoolName, 'Jose Rizal MSU');
      expect(round.schoolLogoUrl, '/school-logos/jrmsu.png');
      expect(round.schoolPrimaryHex, '#AAFF00');
      expect(round.schoolSecondaryHex, '#8B5CF6');
    });

    test('copyWith(clearSnapshot: true) keeps toggles, clears school fields',
        () {
      const p = AppBrandingPref(
        useSchoolLogo: true,
        useSchoolCodeAsName: true,
        schoolId: 1,
        schoolCode: 'X',
        schoolLogoUrl: '/x.png',
      );
      final cleared = p.copyWith(clearSnapshot: true);
      expect(cleared.useSchoolLogo, isTrue);
      expect(cleared.useSchoolCodeAsName, isTrue);
      expect(cleared.schoolId, isNull);
      expect(cleared.schoolCode, isNull);
      expect(cleared.schoolLogoUrl, isNull);
    });
  });

  group('AppBrandingController', () {
    setUp(() {
      SharedPreferences.setMockInitialValues({});
    });

    test('starts at defaults when prefs are empty', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);
      container.read(appBrandingProvider); // trigger build
      await settle();
      final pref = container.read(appBrandingProvider);
      expect(pref.useSchoolLogo, isFalse);
      expect(pref.useSchoolCodeAsName, isFalse);
      expect(pref.schoolCode, isNull);
    });

    test('setters persist; a fresh container restores the values', () async {
      // First container — write toggles.
      final c1 = ProviderContainer();
      c1.read(appBrandingProvider);
      await settle();
      await c1.read(appBrandingProvider.notifier).setUseSchoolLogo(true);
      await c1
          .read(appBrandingProvider.notifier)
          .setUseSchoolCodeAsName(true);
      c1.dispose();

      // Second container — restore should see what c1 persisted.
      final c2 = ProviderContainer();
      addTearDown(c2.dispose);
      c2.read(appBrandingProvider);
      await settle();
      final pref = c2.read(appBrandingProvider);
      expect(pref.useSchoolLogo, isTrue);
      expect(pref.useSchoolCodeAsName, isTrue);
    });

    test('captureSchoolSnapshot populates fields from AuthMeta', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);
      container.read(appBrandingProvider);
      await settle();

      final meta = AuthMeta.fromJson({
        'school_id': 7,
        'school_name': 'JRMSU',
        'school_code': 'JRMSU',
        'logo_url': '/school-logos/jrmsu.png',
        'primary_color': '#AAFF00',
        'secondary_color': '#8B5CF6',
      });
      await container
          .read(appBrandingProvider.notifier)
          .captureSchoolSnapshot(meta);

      final pref = container.read(appBrandingProvider);
      expect(pref.schoolId, 7);
      expect(pref.schoolCode, 'JRMSU');
      expect(pref.schoolLogoUrl, '/school-logos/jrmsu.png');
      expect(pref.schoolPrimaryHex, '#AAFF00');
      expect(pref.schoolSecondaryHex, '#8B5CF6');
    });

    test('clearSnapshot wipes the school fields but keeps toggles', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);
      container.read(appBrandingProvider);
      await settle();

      final ctrl = container.read(appBrandingProvider.notifier);
      await ctrl.setUseSchoolLogo(true);
      await ctrl.captureSchoolSnapshot(AuthMeta.fromJson({
        'school_id': 3,
        'school_code': 'X',
        'logo_url': '/x.png',
      }));
      await ctrl.clearSnapshot();

      final pref = container.read(appBrandingProvider);
      expect(pref.useSchoolLogo, isTrue,
          reason: 'toggle is a personal preference, not session state');
      expect(pref.schoolId, isNull);
      expect(pref.schoolCode, isNull);
      expect(pref.schoolLogoUrl, isNull);
    });
  });
}
