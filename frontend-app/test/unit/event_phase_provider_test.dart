import 'package:aura_app/features/events/application/event_phase_provider.dart';
import 'package:aura_app/shared/models/event.dart';
import 'package:flutter_test/flutter_test.dart';

EventTimeStatus _status({
  required String state,
  DateTime? signOutClosesAt,
}) =>
    EventTimeStatus(
      eventStatus: state,
      effectiveSignOutClosesAt: signOutClosesAt,
      timezoneName: 'Asia/Manila',
    );

void main() {
  group('selectBannerPhase', () {
    final now = DateTime(2026, 5, 28, 10, 0);

    test('sign_out_open beats early_check_in', () {
      final r = selectBannerPhase(
        candidates: [
          BannerCandidate(
              eventId: 1, name: 'A', status: _status(state: 'early_check_in')),
          BannerCandidate(
              eventId: 2, name: 'B', status: _status(state: 'sign_out_open')),
        ],
        now: now,
      );
      expect(r?.eventId, 2);
      expect(r?.phase, BannerPhase.signOutOpen);
    });

    test('closing-soon shown when within 10 min of close', () {
      final closes = now.add(const Duration(minutes: 5));
      final r = selectBannerPhase(
        candidates: [
          BannerCandidate(
              eventId: 9,
              name: 'C',
              status:
                  _status(state: 'sign_out_open', signOutClosesAt: closes)),
        ],
        now: now,
      );
      expect(r?.phase, BannerPhase.signOutClosingSoon);
    });

    test('returns null when no candidate is in an actionable phase', () {
      final r = selectBannerPhase(
        candidates: [
          BannerCandidate(
              eventId: 1, name: 'A', status: _status(state: 'before_check_in')),
          BannerCandidate(
              eventId: 2, name: 'B', status: _status(state: 'closed')),
        ],
        now: now,
      );
      expect(r, isNull);
    });

    test('late_check_in surfaces as checkInOpen', () {
      final r = selectBannerPhase(
        candidates: [
          BannerCandidate(
              eventId: 4, name: 'D', status: _status(state: 'late_check_in')),
        ],
        now: now,
      );
      expect(r?.phase, BannerPhase.checkInOpen);
    });

    test('signOutClosingSoon beats checkInOpen but loses to signOutOpen', () {
      final closes = now.add(const Duration(minutes: 5));
      final r = selectBannerPhase(
        candidates: [
          BannerCandidate(
              eventId: 1,
              name: 'A',
              status:
                  _status(state: 'sign_out_open', signOutClosesAt: closes)),
          BannerCandidate(
              eventId: 2,
              name: 'B',
              status: _status(state: 'early_check_in')),
        ],
        now: now,
      );
      expect(r?.eventId, 2);
      expect(r?.phase, BannerPhase.checkInOpen);
    });
  });
}
