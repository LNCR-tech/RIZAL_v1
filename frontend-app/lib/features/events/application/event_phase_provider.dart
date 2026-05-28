import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/event.dart';
import 'event_schedule_cache.dart';
import 'event_window_reminders_controller.dart';
import 'events_providers.dart';

/// Banner phase priorities, highest first.
enum BannerPhase {
  signOutOpen,
  checkInOpen,
  signOutClosingSoon,
}

class BannerCandidate {
  BannerCandidate({
    required this.eventId,
    required this.name,
    required this.status,
  });
  final int eventId;
  final String name;
  final EventTimeStatus status;
}

class BannerSelection {
  BannerSelection({
    required this.eventId,
    required this.name,
    required this.phase,
  });
  final int eventId;
  final String name;
  final BannerPhase phase;
}

/// Pure selection: pick the highest-priority candidate, if any.
BannerSelection? selectBannerPhase({
  required List<BannerCandidate> candidates,
  required DateTime now,
}) {
  BannerSelection? best;
  int bestRank = -1;

  for (final c in candidates) {
    final phase = _phaseFor(c.status, now);
    if (phase == null) continue;
    final rank = _rank(phase);
    if (rank > bestRank) {
      bestRank = rank;
      best = BannerSelection(eventId: c.eventId, name: c.name, phase: phase);
    }
  }
  return best;
}

BannerPhase? _phaseFor(EventTimeStatus s, DateTime now) {
  final state = s.eventStatus;
  if (state == 'sign_out_open') {
    final closes = s.effectiveSignOutClosesAt;
    if (closes != null &&
        closes.difference(now) <= const Duration(minutes: 10) &&
        closes.isAfter(now)) {
      return BannerPhase.signOutClosingSoon;
    }
    return BannerPhase.signOutOpen;
  }
  if (state == 'early_check_in' || state == 'late_check_in') {
    return BannerPhase.checkInOpen;
  }
  return null;
}

int _rank(BannerPhase p) => switch (p) {
      BannerPhase.signOutOpen => 3,
      BannerPhase.checkInOpen => 2,
      BannerPhase.signOutClosingSoon => 1,
    };

/// 30-second ticker so the banner re-evaluates on the wall clock.
final _bannerTickerProvider = StreamProvider.autoDispose<DateTime>((ref) {
  final controller = StreamController<DateTime>();
  controller.add(DateTime.now());
  final periodic =
      Stream.periodic(const Duration(seconds: 30), (_) => DateTime.now());
  final sub = periodic.listen(controller.add);
  ref.onDispose(() {
    sub.cancel();
    controller.close();
  });
  return controller.stream;
});

/// Reads the current banner selection from cache + a 30-second ticker.
/// Returns null when reminders are off, or no event qualifies.
final eventPhaseProvider = Provider.autoDispose<BannerSelection?>((ref) {
  final enabled = ref.watch(eventWindowRemindersProvider);
  if (!enabled) return null;
  final now = ref.watch(_bannerTickerProvider).valueOrNull ?? DateTime.now();
  final events = ref.watch(scheduleEventsProvider).valueOrNull ?? const [];

  final candidates = <BannerCandidate>[];
  for (final e in events) {
    final snap = eventScheduleCache.get(e.id);
    if (snap == null) continue;
    candidates.add(BannerCandidate(eventId: e.id, name: e.name, status: snap));
  }
  return selectBannerPhase(candidates: candidates, now: now);
});
