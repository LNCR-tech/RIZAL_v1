/// Polling cadence for live-refreshing providers.
///
/// Three discrete paces instead of free-form Duration values so the rest of
/// the app can't accidentally pin a provider to "every 200 ms" and cook the
/// battery. Each value picks a sensible interval for that class of data.
enum PollingPace {
  /// 15s — for things the user just did somewhere else and is waiting to
  /// see (e.g. attendance just recorded on a kiosk, the kiosk's own live
  /// counters).
  fast,

  /// 30s — for things that change a few times a day (notifications, events
  /// the admin just created, a profile field a campus admin just edited).
  /// Default cadence for most live surfaces.
  medium,

  /// 60s — for slowly-changing aggregate data (sanctions, schoolit students
  /// list after a bulk import).
  slow,
}

extension PollingPaceInterval on PollingPace {
  Duration get interval => switch (this) {
        PollingPace.fast => const Duration(seconds: 15),
        PollingPace.medium => const Duration(seconds: 30),
        PollingPace.slow => const Duration(seconds: 60),
      };
}
