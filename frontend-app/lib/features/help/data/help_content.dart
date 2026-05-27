import 'package:flutter/material.dart';

/// Tiered viewer of the help center. The screen filters categories and
/// articles to whichever set matches the current viewer.
///
/// Audience mapping from session:
///   - not signed in           → [public]
///   - student workspace       → [student]
///   - school-IT / campus admin→ [campusAdmin]
///   - governance / SSG        → [governance]
///   - platform / super admin  → [admin]
enum HelpAudience { public, student, campusAdmin, governance, admin }

/// Convenience sets used when tagging categories + articles. Articles
/// default to [allAuthed] (post-signin only) — flag content that's safe to
/// expose on the login screen with [withPublic].
const Set<HelpAudience> allAudiences = <HelpAudience>{
  HelpAudience.public,
  HelpAudience.student,
  HelpAudience.campusAdmin,
  HelpAudience.governance,
  HelpAudience.admin,
};

const Set<HelpAudience> allAuthed = <HelpAudience>{
  HelpAudience.student,
  HelpAudience.campusAdmin,
  HelpAudience.governance,
  HelpAudience.admin,
};

const Set<HelpAudience> staffOnly = <HelpAudience>{
  HelpAudience.campusAdmin,
  HelpAudience.governance,
  HelpAudience.admin,
};

const Set<HelpAudience> adminOnly = <HelpAudience>{HelpAudience.admin};

/// A single help article: a short body paragraph plus numbered steps and an
/// optional tip. Pure data so the catalogue stays trivially searchable.
@immutable
class HelpArticle {
  const HelpArticle({
    required this.id,
    required this.title,
    required this.body,
    this.steps = const <String>[],
    this.tip,
    this.keywords = const <String>[],
    this.audiences = allAudiences,
  });

  final String id;
  final String title;
  final String body;
  final List<String> steps;
  final String? tip;
  final List<String> keywords;

  /// Roles allowed to see this article. Defaults to **everyone**; tighten
  /// when an article is role-specific. Effective visibility is the
  /// intersection with the parent category's [HelpCategory.audiences].
  final Set<HelpAudience> audiences;

  bool visibleFor(HelpAudience viewer) => audiences.contains(viewer);

  /// Plain-text haystack used by [HelpContent.search]. Lower-cased once.
  String get _haystack => '$title $body ${steps.join(' ')} ${keywords.join(' ')}'
      .toLowerCase();

  bool matches(String query) => _haystack.contains(query);
}

/// A grouping of related articles surfaced as an accordion card.
@immutable
class HelpCategory {
  const HelpCategory({
    required this.id,
    required this.title,
    required this.summary,
    required this.icon,
    required this.color,
    required this.articles,
    this.audiences = allAuthed,
  });

  final String id;
  final String title;
  final String summary;
  final IconData icon;
  final Color color;
  final List<HelpArticle> articles;

  /// Roles allowed to see this category. Default is [allAuthed] — the
  /// category disappears on the login screen unless explicitly opened up.
  /// Effective article visibility is the intersection of category + article
  /// audiences, so narrowing the category narrows everything inside it.
  final Set<HelpAudience> audiences;

  /// Returns the articles visible to [viewer]. Empty when the category
  /// itself is hidden or none of its articles allow [viewer].
  List<HelpArticle> visibleArticlesFor(HelpAudience viewer) {
    if (!audiences.contains(viewer)) return const [];
    return [for (final a in articles) if (a.visibleFor(viewer)) a];
  }
}

/// Static catalogue of help content. Source of truth lives in
/// `C:/Users/DjMhel/Documents/doc/user-guide/*.md` — keep them in sync.
class HelpContent {
  HelpContent._();

  /// Aura platform support inbox. School-specific issues (account access,
  /// password resets you can't self-serve) go to the user's campus admin —
  /// see the Contact card on the Help Center.
  static const String auraSupportEmail = 'auraautomessage@gmail.com';
  static const String appVersion = '1.24.0';
  static const String appBuild = '55';
  static const String docsHomepage = 'https://docs.aura.school';

  static final List<HelpCategory> categories = <HelpCategory>[
    _gettingStarted,
    _attendance,
    _account,
    _schedule,
    _assistant,
    _workspaces,
    _troubleshooting,
    _security,
    _about,
    _developerDocs,
  ];

  /// Returns categories filtered to those visible to [viewer], each with
  /// its visible-only article list.
  static List<HelpCategory> categoriesFor(HelpAudience viewer) {
    final out = <HelpCategory>[];
    for (final c in categories) {
      final visible = c.visibleArticlesFor(viewer);
      if (visible.isEmpty) continue;
      out.add(HelpCategory(
        id: c.id,
        title: c.title,
        summary: c.summary,
        icon: c.icon,
        color: c.color,
        articles: visible,
        audiences: c.audiences,
      ));
    }
    return out;
  }

  /// Audience-aware search. Only articles visible to [viewer] are returned.
  static List<({HelpCategory category, HelpArticle article})> searchFor(
      HelpAudience viewer, String rawQuery) {
    final q = rawQuery.trim().toLowerCase();
    if (q.isEmpty) return const [];
    final hits = <({HelpCategory category, HelpArticle article})>[];
    for (final c in categories) {
      for (final a in c.visibleArticlesFor(viewer)) {
        if (a.matches(q)) hits.add((category: c, article: a));
      }
    }
    return hits;
  }

  /// Quick-help chips at the top of the screen. Each entry deep-links into a
  /// specific article so a user is one tap away from the answer. The screen
  /// further filters this list by the current audience so chips never link
  /// to articles the viewer cannot open.
  static final List<({String label, String categoryId, String articleId})>
      quickHelp = <({String label, String categoryId, String articleId})>[
    (label: 'Forgot password', categoryId: 'account', articleId: 'ac-forgot-password'),
    (label: 'Cannot log in', categoryId: 'troubleshooting', articleId: 'tb-login'),
    (label: 'Face scan failed', categoryId: 'troubleshooting', articleId: 'tb-face'),
    (label: 'Grant permissions', categoryId: 'getting-started', articleId: 'gs-permissions'),
    (label: 'Install the app', categoryId: 'getting-started', articleId: 'gs-device-requirements'),
  ];

  /// Flat search across every article. Returns matches with their parent
  /// category so the result row can show a breadcrumb.
  static List<({HelpCategory category, HelpArticle article})> search(
      String rawQuery) {
    final q = rawQuery.trim().toLowerCase();
    if (q.isEmpty) return const [];
    final hits = <({HelpCategory category, HelpArticle article})>[];
    for (final c in categories) {
      for (final a in c.articles) {
        if (a.matches(q)) hits.add((category: c, article: a));
      }
    }
    return hits;
  }

  static HelpArticle? findArticle(String categoryId, String articleId) {
    for (final c in categories) {
      if (c.id != categoryId) continue;
      for (final a in c.articles) {
        if (a.id == articleId) return a;
      }
    }
    return null;
  }

  static HelpCategory? findCategory(String categoryId) {
    for (final c in categories) {
      if (c.id == categoryId) return c;
    }
    return null;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Category palette — distributed hues so categories are visually distinct.
// ─────────────────────────────────────────────────────────────────────────────
const _rose = Color(0xFFEC4899);
const _emerald = Color(0xFF22C55E);
const _blue = Color(0xFF3B82F6);
const _violet = Color(0xFF8B5CF6);
const _indigo = Color(0xFF6366F1);
const _teal = Color(0xFF14B8A6);
const _amber = Color(0xFFF59E0B);
const _red = Color(0xFFEF4444);
const _slate = Color(0xFF64748B);

// ─────────────────────────────────────────────────────────────────────────────
// Categories
// ─────────────────────────────────────────────────────────────────────────────

const HelpCategory _gettingStarted = HelpCategory(
  id: 'getting-started',
  title: 'Getting started',
  summary: 'First login, permissions, and face registration.',
  icon: Icons.rocket_launch_rounded,
  color: _rose,
  audiences: allAudiences,
  articles: [
    HelpArticle(
      id: 'gs-first-login',
      title: 'Sign in for the first time',
      body:
          'Use the school account your Campus Admin gave you. If your account is brand new, Aura will ask you to set a permanent password before it lets you in.',
      steps: [
        'Open Aura. The Sign in screen loads automatically.',
        'Enter your school email and the temporary password you were given.',
        'Tap Sign in.',
        'If prompted, set a new password (Account → Change password style screen).',
        'You are taken to your role-specific home: students → /student, school IT → /workspace, governance → /governance, platform admin → /admin.',
      ],
      tip:
          'Forgot your password? Ask your Campus Admin to reset it — Aura does not yet expose a self-serve reset.',
      keywords: ['login', 'sign in', 'first login', 'temporary password'],
    ),
    HelpArticle(
      id: 'gs-change-temp-password',
      title: 'Change your temporary password',
      body:
          'Accounts created with temporary credentials must set a fresh password on first sign-in. This is a one-time hard gate — you cannot reach any other screen until it is done.',
      steps: [
        'After signing in with your temporary password Aura routes you to Change password.',
        'Enter a new password that you have not used before.',
        'Confirm it in the second field.',
        'Tap Save. Aura returns you to the workspace home.',
      ],
      tip: 'Use a password manager. Never reuse a password from another service.',
      keywords: ['change password', 'temporary', 'reset', 'first time'],
    ),
    HelpArticle(
      id: 'gs-permissions',
      title: 'Grant the permissions Aura needs',
      body:
          'Aura needs the camera for face attendance, location for geofenced event check-in, and (on supported builds) notifications to alert you when you arrive at an event.',
      steps: [
        'When prompted on first launch, allow Camera — required for face registration and scanning.',
        'Allow Location — required for events that use geofenced check-in.',
        'Allow Notifications — receive school alerts and nearby-event prompts.',
        'If you denied one by mistake, open Android Settings → Apps → Aura → Permissions and re-enable it.',
      ],
      tip:
          'On Android 14+ Aura asks for background location separately. Decline if your school does not use background check-in.',
      keywords: ['permissions', 'camera', 'location', 'notifications', 'android'],
    ),
    HelpArticle(
      id: 'gs-register-face',
      title: 'Register your face',
      body:
          'Face attendance only works after you have enrolled a clear, well-lit reference photo. The reference is stored encrypted and is only used to verify your own scans.',
      steps: [
        'Open Account → Security → Face ID.',
        'Tap Set up Face ID. The front camera opens.',
        'Position your face inside the oval. Hold still in even light.',
        'Wait for the capture confirmation.',
        'The Face ID row in Settings will now read Enrolled.',
      ],
      tip:
          'Re-enroll if your appearance changes significantly (haircut, glasses, facial hair) so attendance keeps working smoothly.',
      keywords: ['face id', 'register', 'enroll', 'face recognition'],
    ),
    HelpArticle(
      id: 'gs-device-requirements',
      title: 'Device requirements (Android APK)',
      body:
          'Aura runs on most modern Android phones, but face scanning depends on a working front camera and decent lighting.',
      steps: [
        'Android 7.0 (API 24) or newer.',
        'A working front camera for face attendance and registration.',
        'A stable internet connection — Wi-Fi or mobile data.',
        'Enough free storage for app install and updates.',
        'Allow installs from unknown sources if you side-load the APK.',
      ],
      keywords: ['android', 'apk', 'requirements', 'device', 'camera'],
    ),
    HelpArticle(
      id: 'gs-update-apk',
      title: 'Update Aura on Android',
      body:
          'When your school distributes a new APK, install it the same way you installed the first one. Your account session and local data are preserved when the package name matches.',
      steps: [
        'Download the newer app-release.apk from your school IT or deployment admin.',
        'Open the file from your Downloads or Files app.',
        'Tap Install — Android offers Update because the package name (com.aura.aura_app) already exists.',
        'Open Aura. Sign in again if the session expired.',
      ],
      tip:
          'Always install from the channel your school IT trusts. APKs from unknown sources can be modified.',
      keywords: ['update', 'apk', 'install', 'new version'],
    ),
  ],
);

const HelpCategory _attendance = HelpCategory(
  id: 'attendance',
  title: 'Attendance & events',
  summary: 'Face scans, on-time vs late, and what to do when it fails.',
  icon: Icons.fact_check_rounded,
  color: _emerald,
  articles: [
    HelpArticle(
      id: 'at-how-face-works',
      title: 'How face attendance works',
      body:
          'When an event is open and you are inside its geofence (if one is set), Aura compares a fresh face scan against the reference photo you enrolled. A match marks you Present (or Late if you scanned after the on-time window closed).',
      steps: [
        'Open the event from Schedule, Home, or the Nearby event banner.',
        'Tap Scan to check in.',
        'Allow the camera if Aura asks.',
        'Center your face in the oval under even lighting and hold still.',
        'Wait for the result chip — Present, Late, or a retry prompt.',
      ],
      tip:
          'Liveness is on — Aura blocks photos of photos. Use your real face, not a screen.',
      keywords: ['face scan', 'check-in', 'attendance', 'how does'],
    ),
    HelpArticle(
      id: 'at-present-vs-late',
      title: 'PRESENT vs LATE — what is the difference?',
      body:
          'PRESENT means your check-in landed inside the event\'s on-time window. LATE means the check-in happened after that window closed but while the event is still accepting attendance.',
      steps: [
        'Each event has an on-time window set by the organizer.',
        'A scan during that window → status PRESENT.',
        'A scan after the window but inside the late window → status LATE.',
        'A scan after the late window closes → no attendance recorded.',
      ],
      tip:
          'You can usually still check in when late — but only while the event window is open and your school\'s late policy allows it.',
      keywords: ['present', 'late', 'status', 'on time'],
    ),
    HelpArticle(
      id: 'at-late-checkin',
      title: 'Can I still check in when I am late?',
      body:
          'Yes — as long as the event\'s attendance window is open and the late policy allows it, you can still scan and be marked LATE.',
      steps: [
        'Open the event from Schedule.',
        'If the attendance window is still open you will see Scan available.',
        'Tap Scan and complete the face check.',
        'Your status will read LATE instead of PRESENT.',
      ],
      tip:
          'If Scan is greyed out, the late window has closed. Ask the event officer to record manual attendance.',
      keywords: ['late', 'check-in', 'window', 'still open'],
    ),
    HelpArticle(
      id: 'at-face-fails',
      title: 'My face scan fails — what now?',
      body:
          'A failed scan almost always comes down to one of three things: poor lighting, a missing or low-quality face profile, or a denied camera permission.',
      steps: [
        'Move to even, bright light. Avoid back-lighting and harsh shadows.',
        'Remove glasses or hats only if the scan keeps failing.',
        'Re-enroll your face from Account → Security → Face ID if the profile is old.',
        'Check Android Settings → Apps → Aura → Permissions → Camera is allowed.',
        'If it still fails after two retries, ask an officer for manual attendance.',
      ],
      tip:
          'Aura logs failed scans for rate-limiting. After several failures in a row Aura will pause scans for a short cool-down.',
      keywords: ['face scan', 'fails', 'not working', 'rejected'],
    ),
    HelpArticle(
      id: 'at-manual',
      title: 'Officer-assisted manual attendance',
      body:
          'When face scanning is not an option — broken camera, repeated failures, or a student without an enrolled face — the event officer can record attendance manually from the same event screen.',
      steps: [
        'Approach the event officer or School IT staff on duty.',
        'They open the event from their /governance or /workspace shell.',
        'They tap Manual mark-in and pick your name (or student ID).',
        'They select your status (PRESENT or LATE) and save.',
        'Your attendance appears in your own analytics within seconds.',
      ],
      tip:
          'Manual marks are logged. Repeated manual entries trigger an audit flag, so officers should only use them when face scan is not feasible.',
      keywords: ['manual', 'officer', 'staff', 'mark in', 'audit'],
    ),
    HelpArticle(
      id: 'at-incorrect',
      title: 'Attendance looks wrong for an event',
      body:
          'If a status seems off, three things usually explain it: the event\'s attendance window was different than expected, the scan happened outside the geofence, or the record came from a manual override.',
      steps: [
        'Open the event detail and read the on-time and late windows carefully.',
        'Confirm whether the event uses a geofence — your location must have been inside it.',
        'Check whether your attendance row says scanned or manual.',
        'If something still looks wrong, contact the event officer or your Campus Admin — they can review and adjust.',
      ],
      keywords: ['wrong', 'incorrect', 'attendance', 'late', 'dispute'],
    ),
  ],
);

const HelpCategory _account = HelpCategory(
  id: 'account',
  title: 'Your account',
  summary: 'Profile, password, sign-in history, and face ID.',
  icon: Icons.person_rounded,
  color: _blue,
  articles: [
    HelpArticle(
      id: 'ac-profile',
      title: 'Edit your profile',
      body:
          'Your display name and contact email come from your school record. You can update them from Account → Edit profile — changes apply immediately to your sign-in.',
      steps: [
        'Open Account.',
        'Tap Edit profile under Security.',
        'Update your name and email.',
        'Tap Save.',
      ],
      tip:
          'Your email is your sign-in identifier. Changing it will require signing in again with the new address.',
      keywords: ['profile', 'edit', 'name', 'email'],
    ),
    HelpArticle(
      id: 'ac-password',
      title: 'Change your password',
      body:
          'You can change your password any time from the Security section. You will be signed out of other devices for safety.',
      steps: [
        'Open Account → Change password.',
        'Enter your current password.',
        'Enter a new password and confirm it.',
        'Tap Save. Other active sessions are signed out.',
      ],
      tip:
          'Pick a unique password you do not use anywhere else. A password manager helps.',
      keywords: ['change password', 'reset', 'forgot', 'security'],
    ),
    HelpArticle(
      id: 'ac-forgot-password',
      title: 'Forgot your password? Reset it',
      // Visible on the login screen too — this is the article people will
      // actually be hunting for.
      audiences: allAudiences,
      body:
          'Aura sends you a 6-digit code by email so you can reset your password yourself — no admin approval needed. The code is good for 15 minutes from the moment it is sent.',
      steps: [
        'On the Sign in screen, tap "Forgot your password?" under the buttons.',
        'Enter your school email and tap Send reset code. The response is intentionally generic — Aura never confirms whether an account exists.',
        'Check your email for the 6-digit code from Aura. It can take a minute to arrive — also check Spam/Junk.',
        'Back in the app, type the 6 digits into the code field, then set a new password (at least 8 characters) and re-type it to confirm.',
        'Tap Reset password. Aura signs you out and returns you to the Sign in screen.',
        'Sign in with your school email and the new password.',
      ],
      tip:
          'If the code expires (15 minutes) or never arrives, use "Resend code" — it unlocks after a short cooldown.',
      keywords: [
        'forgot password',
        'forgot',
        'reset',
        'password reset',
        'cannot sign in',
        '6-digit code',
        'verification code',
        'email code',
        'resend code',
      ],
    ),
    HelpArticle(
      id: 'ac-sessions',
      title: 'Sign-in & devices',
      body:
          'See every device currently signed in, plus a history of recent sign-ins. Sign out remote devices you do not recognize.',
      steps: [
        'Open Account → Sign-in & devices.',
        'Active sessions appear at the top with device + last activity.',
        'Tap Sign out next to a session to revoke it.',
        'Recent sign-ins below show the audit trail.',
      ],
      tip:
          'If you spot an unknown device, sign it out immediately and change your password.',
      keywords: ['sessions', 'devices', 'sign out', 'login history'],
    ),
    HelpArticle(
      id: 'ac-face-id',
      title: 'Update or re-enroll Face ID',
      body:
          'Re-take your reference photo if your face scan starts failing, or if your appearance has changed.',
      steps: [
        'Open Account → Face ID.',
        'Tap Update Face ID. The front camera opens.',
        'Position your face in the oval and hold still in even light.',
        'Wait for confirmation. The new reference replaces the old one.',
      ],
      tip:
          'You only need to re-enroll if scans keep failing. A correct profile keeps working for months.',
      keywords: ['face id', 'update', 're-enroll', 'face recognition'],
    ),
  ],
);

const HelpCategory _schedule = HelpCategory(
  id: 'schedule',
  title: 'Schedule & events',
  summary: 'Find today\'s events, upcoming ones, and event details.',
  icon: Icons.event_note_rounded,
  color: _violet,
  articles: [
    HelpArticle(
      id: 'sc-today',
      title: 'See today\'s events',
      body:
          'The Home tab shows what is happening right now and what is next today, including ongoing geofenced events you might be near.',
      steps: [
        'Open Home (the first tab).',
        'Now & Next shows the event you should focus on.',
        'Tap a card to open the event detail and check in.',
        'A Nearby event banner appears when you reach an event\'s geofence (if enabled).',
      ],
      keywords: ['today', 'home', 'events', 'now next'],
    ),
    HelpArticle(
      id: 'sc-upcoming',
      title: 'Find upcoming events',
      body:
          'Schedule is the calendar view across the school year. Filter by All / Today / Upcoming / Past, and search by event title.',
      steps: [
        'Open Schedule.',
        'Use the filter chips at the top to narrow the list.',
        'Tap the calendar dots to see events on specific days.',
        'Tap an event card to see details, geofence, and policy.',
      ],
      keywords: ['schedule', 'upcoming', 'calendar', 'events'],
    ),
    HelpArticle(
      id: 'sc-detail',
      title: 'Read an event detail',
      body:
          'Every event shows its on-time and late windows, geofence (if any), targeted year levels, and the action you can take right now (scan, view, no attendance).',
      steps: [
        'Tap the event card from Home or Schedule.',
        'Header: title, date, and status (Upcoming · Ongoing · Past).',
        'Windows: on-time and late check-in cut-offs.',
        'Map: the geofence centre and radius (when geofenced).',
        'Action button: Scan, View attendance, or Closed.',
      ],
      keywords: ['event detail', 'geofence', 'window', 'scan'],
    ),
    HelpArticle(
      id: 'sc-analytics',
      title: 'Review your attendance history',
      body:
          'Analytics rolls up your overall compliance, monthly trends, and a breakdown by event type.',
      steps: [
        'Open Analytics from the bottom nav.',
        'Compliance arc shows your present + on-time rate.',
        'Now & Next surfaces what to focus on.',
        'Scroll down for monthly trend and event-type pie.',
      ],
      keywords: ['analytics', 'history', 'compliance', 'trend'],
    ),
  ],
);

const HelpCategory _assistant = HelpCategory(
  id: 'assistant',
  title: 'Aura AI assistant',
  summary: 'Chat for questions, charts, and quick data look-ups.',
  icon: Icons.auto_awesome_rounded,
  color: _indigo,
  articles: [
    HelpArticle(
      id: 'ai-use',
      title: 'When to use Aura AI',
      body:
          'Aura AI is a chat assistant powered by Jose. It can answer attendance questions, explain school policies it has access to, and draw quick charts from your data.',
      steps: [
        'Open Aura AI from the bottom nav or Account.',
        'Type a question — e.g. "How many events did I miss this month?".',
        'It streams an answer, and may render a chart if the question is quantitative.',
        'Tap a chart bar to see the underlying period.',
      ],
      keywords: ['ai', 'chat', 'assistant', 'jose', 'questions'],
    ),
    HelpArticle(
      id: 'ai-scope',
      title: 'What Aura AI can and cannot see',
      body:
          'Aura AI follows the same school-level isolation as the rest of the app. It can read your own records and the records of your school. It cannot see other schools.',
      steps: [
        'Your school context is attached to every request automatically.',
        'Aura AI cannot read other schools\' students, events, or sanctions.',
        'Privileged data (other students\' personal info) is gated by your role.',
        'All AI requests are logged for audit.',
      ],
      keywords: ['privacy', 'scope', 'isolation', 'data', 'school'],
    ),
    HelpArticle(
      id: 'ai-fast-vs-think',
      title: 'Fast vs Think mode',
      body:
          'Fast skips heavy tools and returns a short answer in seconds. Think uses tools (search, charts) and is slower but better for complex questions.',
      steps: [
        'Find the segmented control above the chat input.',
        'Tap Fast for short factual questions ("when does the assembly end?").',
        'Tap Think for analytical questions ("compare my attendance to last term").',
        'Your choice is remembered between sessions.',
      ],
      tip:
          'Think can take up to a minute on a slow local model — that is normal.',
      keywords: ['fast', 'think', 'mode', 'speed', 'tools'],
    ),
  ],
);

const HelpCategory _workspaces = HelpCategory(
  id: 'workspaces',
  title: 'For staff & officers',
  summary: 'Daily flows for Campus Admin, Governance, and Platform admin.',
  icon: Icons.workspaces_rounded,
  color: _teal,
  articles: [
    HelpArticle(
      id: 'ws-student',
      title: 'Student workflow',
      audiences: {HelpAudience.student, HelpAudience.admin},
      body:
          'The student workspace lives at /student. Home, Schedule, Analytics, Notifications, and Aura AI cover the daily flow.',
      steps: [
        'Open Home — see today\'s events and current status.',
        'Open Schedule — browse upcoming and past events.',
        'Open an event card → Scan to check in.',
        'Open Analytics — review your compliance trend.',
        'Open Aura AI for questions and quick look-ups.',
      ],
      keywords: ['student', 'dashboard', 'home', 'flow'],
    ),
    HelpArticle(
      id: 'ws-school-it',
      title: 'Campus Admin / School IT workflow',
      audiences: {HelpAudience.campusAdmin, HelpAudience.admin},
      body:
          'School IT and Campus Admin operate under /workspace. You manage users, run bulk imports, edit school settings, and oversee student government.',
      steps: [
        'Open Users — manage students by college, assign departments.',
        'Open Import — bulk-onboard students from a spreadsheet.',
        'Open Student Government — set up SSG, add officers, grant permissions.',
        'Open School settings — name, code, primary + secondary colours, logo.',
        'Open Schedule and Reports to monitor attendance health.',
      ],
      keywords: ['campus admin', 'school it', 'workspace', 'users', 'import'],
    ),
    HelpArticle(
      id: 'ws-governance',
      title: 'Governance / SSG officer workflow',
      audiences: {HelpAudience.governance, HelpAudience.admin},
      body:
          'Officers run events under /governance. The dashboard shows compliance at a glance and gates actions by permission.',
      steps: [
        'Open Events — list of ongoing and upcoming events.',
        'Tap New event (requires manage_events) to create one with policy + geofence.',
        'During the event, run manual or face attendance as students arrive.',
        'Open Members to add officers and grant permissions (one level of hierarchy: SSG → SG → ORG).',
        'Open Reports to export PDF/Excel/CSV for any event.',
      ],
      tip:
          'Greyed-out quick actions mean your role does not have that permission. Ask the unit owner to grant it.',
      keywords: ['governance', 'ssg', 'officer', 'events', 'manage'],
    ),
    HelpArticle(
      id: 'ws-admin',
      audiences: adminOnly,
      title: 'Platform admin workflow',
      body:
          'Platform admins manage schools and accounts across the deployment from /admin. Access is permission-gated.',
      steps: [
        'Open Schools — review school health, branding, and status.',
        'Open Accounts — manage admin accounts and roles.',
        'Open Logs — audit trail across the platform.',
        'Open Aura AI for analytical questions across the deployment.',
      ],
      keywords: ['admin', 'platform', 'schools', 'accounts'],
    ),
  ],
);

const HelpCategory _troubleshooting = HelpCategory(
  id: 'troubleshooting',
  title: 'Troubleshooting',
  summary: 'Common issues and what to do.',
  icon: Icons.build_circle_rounded,
  color: _amber,
  audiences: allAudiences,
  articles: [
    HelpArticle(
      id: 'tb-login',
      title: 'I cannot log in',
      body:
          'Usually one of three things: a typo, an inactive account, or an outage. Work through these in order.',
      steps: [
        'Double-check your email and password — Caps Lock on?',
        'Try a different network — a stale Wi-Fi is sometimes the culprit.',
        'If the screen says your account or school is inactive, contact your Campus Admin.',
        'If it just spins, the backend may be down — wait a minute and try again.',
      ],
      keywords: ['login', 'cannot sign in', 'wrong password', 'inactive'],
    ),
    HelpArticle(
      id: 'tb-no-data',
      title: 'Pages open but data is missing',
      body:
          'This is almost always a network issue or a brief backend outage. The app loads, but list queries return empty.',
      steps: [
        'Pull the page down to refresh.',
        'Check your connection — toggle Wi-Fi or mobile data.',
        'Sign out and back in if it persists.',
        'If only one screen is empty, the underlying data may simply not exist yet — confirm with your Campus Admin.',
      ],
      keywords: ['no data', 'empty', 'not loading', 'blank'],
    ),
    HelpArticle(
      id: 'tb-camera',
      title: 'The camera does not open',
      body:
          'Aura needs the camera permission for face attendance. If a prior denial is sticking, you need to flip the permission in Android Settings.',
      steps: [
        'Open Android Settings → Apps → Aura → Permissions.',
        'Tap Camera and select Allow only while using the app.',
        'Return to Aura and retry the scan.',
        'If the camera still refuses, restart the phone — a stuck camera service is fixed by a reboot.',
      ],
      keywords: ['camera', 'denied', 'permission', 'not opening'],
    ),
    HelpArticle(
      id: 'tb-face',
      title: 'Face scan fails often',
      body:
          'Most failures come from lighting, alignment, or a stale reference photo.',
      steps: [
        'Stand under even light — avoid bright windows behind you.',
        'Hold the phone at eye level. Fit your face inside the oval.',
        'Hold still until the result chip appears.',
        'If it still fails twice, re-enroll Face ID from Account → Security → Face ID.',
        'If it still fails after re-enrolment, ask the officer for manual attendance.',
      ],
      keywords: ['face scan', 'rejected', 'liveness', 'failed'],
    ),
    HelpArticle(
      id: 'tb-unexpected-late',
      title: 'I was marked LATE unexpectedly',
      body:
          'The most common cause is that the event\'s on-time window closed earlier than you assumed.',
      steps: [
        'Open the event and read the on-time window.',
        'Compare it to when you actually scanned (visible in Analytics → event detail).',
        'If the window is wrong, ask the event officer to review it.',
        'Officers can adjust the policy and re-evaluate attendance for the event.',
      ],
      keywords: ['late', 'unexpected', 'wrong', 'window'],
    ),
    HelpArticle(
      id: 'tb-apk-install',
      title: 'The APK will not install on Android',
      body:
          'Android blocks side-loaded installs by default. You need to allow the source app (Files, Chrome, or whatever you opened the APK from) to install unknown apps.',
      steps: [
        'Open Android Settings → Security (or Apps → Special access).',
        'Tap Install unknown apps.',
        'Find the app you opened the APK from (e.g. Files or Chrome).',
        'Toggle Allow from this source.',
        'Re-open the APK and tap Install.',
      ],
      tip:
          'Only allow this for trusted source apps. Disable it again afterwards if you prefer.',
      keywords: ['apk', 'install', 'unknown sources', 'blocked', 'android'],
    ),
    HelpArticle(
      id: 'tb-late-load',
      title: 'A specific screen loads slowly',
      body:
          'Reports and exports do more work than other screens. Brief delays are expected.',
      steps: [
        'Reports compute in the background — the progress bar reflects real work.',
        'PDF and Excel exports run in an isolate so the UI stays responsive.',
        'A second export of the same event uses cached data and is near-instant.',
        'If a screen consistently takes >10s, capture a screenshot and share it with IT.',
      ],
      keywords: ['slow', 'report', 'export', 'pdf', 'excel'],
    ),
    HelpArticle(
      id: 'tb-cleartext',
      title: 'The app refuses to reach the server',
      body:
          'Production deployments use HTTPS. Pre-prod staging may use an IP-only HTTP endpoint. The Android build enables cleartext for dev — release builds do not.',
      steps: [
        'Confirm with your Campus Admin which endpoint Aura should point at.',
        'In dev builds, an HTTP IP address is allowed.',
        'In release builds Aura blocks HTTP — only HTTPS works.',
        'If your endpoint is wrong, ask IT to rebuild Aura with the correct AURA_API_BASE_URL.',
      ],
      keywords: ['network', 'http', 'server', 'cannot reach', 'cleartext'],
    ),
  ],
);

const HelpCategory _security = HelpCategory(
  id: 'security',
  title: 'Security & good practice',
  summary: 'Habits that keep your account and school data safe.',
  icon: Icons.shield_rounded,
  color: _red,
  audiences: allAudiences,
  articles: [
    HelpArticle(
      id: 'sec-credentials',
      title: 'Never share your credentials',
      body:
          'Your account is the audit trail of everything you do in Aura. Sharing it muddies that trail and weakens the whole school\'s security.',
      steps: [
        'Do not share your password with classmates, friends, or family.',
        'Do not share over Messenger, email, or screenshots.',
        'If you suspect someone has your password, change it right away.',
      ],
      keywords: ['credentials', 'password', 'sharing', 'security'],
    ),
    HelpArticle(
      id: 'sec-shared-device',
      title: 'Sign out on shared devices',
      body:
          'If you used a shared phone, lab computer, or a borrowed device — always sign out before you walk away.',
      steps: [
        'Open Account.',
        'Scroll down to the Sign out button.',
        'Confirm. The session is revoked server-side too.',
        'On a shared computer, also clear the browser session.',
      ],
      keywords: ['sign out', 'shared device', 'logout', 'session'],
    ),
    HelpArticle(
      id: 'sec-update',
      title: 'Keep the app up to date',
      body:
          'Every Aura release ships security fixes alongside features. Stay current.',
      steps: [
        'When your school distributes a new APK, install it within a week.',
        'Restart the app once after an update.',
        'Check the version in Help Center → About Aura.',
      ],
      keywords: ['update', 'version', 'security', 'fixes'],
    ),
    HelpArticle(
      id: 'sec-lost-device',
      title: 'Report a lost or stolen device',
      body:
          'A lost phone with an active Aura session is a real risk. Revoke the session immediately so the thief cannot impersonate you.',
      steps: [
        'On any other device, sign in to Aura.',
        'Open Account → Sign-in & devices.',
        'Find the lost device in the list and tap Sign out.',
        'Change your password as an extra precaution.',
        'Tell your Campus Admin so they can disable the account if needed.',
      ],
      keywords: ['lost', 'stolen', 'phone', 'revoke', 'sessions'],
    ),
    HelpArticle(
      id: 'sec-data',
      title: 'How Aura protects your data',
      body:
          'Data is isolated by school. Your records are encrypted in transit (HTTPS in production) and at rest. AI assistant access follows the same school-level isolation.',
      steps: [
        'Every API call is bound to your school context.',
        'Face references are stored encrypted, separately from your profile.',
        'Sessions can be revoked at any time from Sign-in & devices.',
        'All sensitive actions are logged for audit.',
      ],
      keywords: ['data', 'privacy', 'encryption', 'isolation', 'audit'],
    ),
  ],
);

const HelpCategory _about = HelpCategory(
  id: 'about',
  title: 'About Aura',
  summary: 'What Aura is, who runs it, and how to reach support.',
  icon: Icons.info_rounded,
  color: _slate,
  audiences: allAudiences,
  articles: [
    HelpArticle(
      id: 'ab-what',
      title: 'What is Aura?',
      body:
          'Aura is a school-grade attendance platform. It tracks attendance with face recognition, QR or RFID, and geolocation; runs reporting and analytics; and offers an AI assistant for fast questions. Each school\'s data is fully isolated from every other school.',
      keywords: ['aura', 'what is', 'platform', 'rizal'],
    ),
    HelpArticle(
      id: 'ab-isolation',
      title: 'Data isolation across schools',
      body:
          'Every record in Aura — students, events, sanctions, AI queries — is scoped by school_id at the backend. There is no path for one school to read another school\'s data.',
      keywords: ['isolation', 'data', 'school', 'multi-tenant'],
    ),
    HelpArticle(
      id: 'ab-version',
      title: 'Version, build, and credits',
      body:
          'You are running Aura v${HelpContent.appVersion} (build ${HelpContent.appBuild}). The assistant is powered by Jose AI, a local model served by the school\'s assistant service.',
      keywords: ['version', 'build', 'credits', 'jose'],
    ),
    HelpArticle(
      id: 'ab-services',
      title: 'Services that make up Aura',
      body:
          'Aura is a small set of cooperating services: a FastAPI backend, this Flutter mobile client, a Vue web app, an assistant service (Aura · Jose AI), PostgreSQL for data, Redis + Celery for background jobs.',
      keywords: ['services', 'architecture', 'backend', 'frontend'],
    ),
  ],
);

// ─────────────────────────────────────────────────────────────────────────────
// Developer Docs — surfaced only to platform admin (super admin / SaaS owner)
// who manages payments + infrastructure. Each article is a quick-reference;
// the canonical source-of-truth lives in `docs/technical/...`.
// ─────────────────────────────────────────────────────────────────────────────
const HelpCategory _developerDocs = HelpCategory(
  id: 'developer-docs',
  title: 'Developer docs',
  summary: 'Architecture, API, database, deployment — for admins running Aura.',
  icon: Icons.code_rounded,
  color: _indigo,
  audiences: adminOnly,
  articles: [
    HelpArticle(
      id: 'dev-architecture',
      audiences: adminOnly,
      title: 'System architecture at a glance',
      body:
          'Aura is split into five long-running services orchestrated by Docker Compose: backend (FastAPI), frontend-web (Vue 3 + Vite), frontend-app (this Flutter client), assistant (Python service serving Aura · Jose AI), and storage (Postgres + Redis). Migrations and bootstrap run as one-shot jobs on `docker compose up`.',
      steps: [
        'backend → FastAPI on :8001 (dev) / :8000 (prod). Alembic migrations, Celery worker + beat.',
        'frontend-web → Vue 3 SPA on :5173 (dev) / :80 (prod), wrapped by Capacitor for Android.',
        'frontend-app → Flutter (Android + iOS). Talks to backend ROOT (no /api prefix); login at POST /token.',
        'assistant → FastAPI on :8500. Streams SSE; serves Aura · Jose AI either via centralized Jose gateway or a local llama-server.',
        'database → Postgres 16; redis → Redis 7. Both internal-only in prod compose.',
      ],
      tip:
          'Full diagrams + dependency graph live in `docs/technical/architecture/system-architecture.md` and `architecture/diagrams.md`.',
      keywords: ['architecture', 'system', 'services', 'compose', 'overview'],
    ),
    HelpArticle(
      id: 'dev-tech-stack',
      audiences: adminOnly,
      title: 'Tech stack',
      body:
          'Backend: FastAPI · SQLAlchemy · Alembic · Pydantic v2 · Celery · Redis · Postgres 16 · ONNX runtime (face recognition). Frontend-web: Vue 3 · Vite · Pinia · Vue Router · Tailwind · Playwright. Frontend-app: Flutter · Riverpod · go_router · Dio · fl_chart · Manrope/JetBrainsMono. Assistant: FastAPI · MCP · llama.cpp (Jose).',
      steps: [
        'See `docs/technical/architecture/tech-stack.md` for pinned versions + rationale.',
        'Pre-1.0 SemVer is enforced separately for each service; service folders track their own CHANGELOG.',
      ],
      keywords: ['tech stack', 'dependencies', 'versions', 'frameworks'],
    ),
    HelpArticle(
      id: 'dev-api-reference',
      audiences: adminOnly,
      title: 'API reference — auth, attendance, governance',
      body:
          'The backend exposes ~90 REST endpoints, all bearer-token authenticated. The Token contract is in `backend/app/schemas/auth.py` and includes brand + role meta so a single login fully bootstraps a session.',
      steps: [
        'Auth: POST /token (OAuth2 form), POST /login (JSON), POST /auth/google, POST /auth/forgot-password, POST /auth/change-password.',
        'Events: POST /api/events, PATCH /api/events/{id}, GET /api/events with scope filters; `governance_context=SSG|SG|ORG` for officers.',
        'Attendance: POST /api/face/scan (face + liveness), POST /api/attendance/manual.',
        'Governance: SSG/SG/ORG CRUD + member + permission endpoints under /api/governance/*.',
        'List endpoints use the {data, page, total, total_pages} envelope — `Paginated.dart` unwraps both bare lists and the envelope.',
      ],
      tip:
          'Comprehensive reference: `docs/technical/api/reference.md` + `endpoints.md`. Error contract: `api/error-contract.md`.',
      keywords: ['api', 'endpoints', 'rest', 'reference', 'oauth', 'token'],
    ),
    HelpArticle(
      id: 'dev-database',
      audiences: adminOnly,
      title: 'Database schema + migrations',
      body:
          'Postgres 16. All schema changes go through Alembic migrations in `backend/alembic/versions/`. `schema.sql` is informational only — do not rely on it without a matching migration.',
      steps: [
        'Core tables: users, schools, departments, programs, events, event_targets, attendance_records, governance_units, governance_members, governance_member_permissions, school_audit_logs.',
        'School isolation is enforced via `school_id` on every domain table; cross-school reads are gated in the service layer.',
        'Migrations run on every `docker compose up` via the `migrate` service. Migration ID is bounded to alembic_version.VARCHAR(32).',
        'ERD diagrams: `docs/technical/database/erd/ERDv2.md`. Relationships: `database/relationships.md`. Per-table notes: `database/tables.md`.',
      ],
      tip:
          'Event_target_scope simplification (year_levels only) landed on main today — Flutter client side already supports it via Phase 11 contract.',
      keywords: ['database', 'postgres', 'schema', 'migrations', 'alembic'],
    ),
    HelpArticle(
      id: 'dev-deployment',
      audiences: adminOnly,
      title: 'Deployment + CI/CD',
      body:
          'Three GitHub Actions workflows: `ci.yml` runs on all PRs (lint + unit + Playwright + Flutter test), `staging-cd.yml` deploys to staging on push to `develop`, `production-cd.yml` deploys to prod on push to `main`. `aura-app-ci.yml` runs Flutter-specific gates on `frontend-app/**` changes.',
      steps: [
        'Production stack: docker-compose.prod.yml on AWS EC2 (Ubuntu). Frontend on port 80, backend on 8000, assistant on 8500.',
        'Deploy flow: `deploy.sh` pulls latest, runs migrations, restarts changed services, then `rollback.sh` fires on failure with a Postgres backup snapshot.',
        '.env.production holds secrets (SECRET_KEY, DB_PASSWORD, AI_API_KEY, AI_API_BASE, AI_MODEL, MAILJET keys). Never commit them.',
        'Linux deploy runbook: `backend/docs/getting-started/linux-deploy.md`. Detailed CD pipeline: `docs/technical/deployment/ci-cd-pipeline.md`.',
      ],
      keywords: ['deployment', 'ci', 'cd', 'docker', 'github actions', 'aws'],
    ),
    HelpArticle(
      id: 'dev-setup',
      audiences: adminOnly,
      title: 'Local development setup',
      body:
          'Clone, copy each service\'s `.env.example` to `.env`, fill in AI provider + SECRET_KEY, then `docker compose up --build`. The full dev stack (incl. pgAdmin + Mailpit) comes up in one command. Flutter client runs separately via `flutter run --dart-define-from-file=config/cloud.json`.',
      steps: [
        'Repo root: `Copy-Item .env.example .env`, fill required values.',
        'Backend, frontend, assistant, db: `docker compose up --build`. Wait for the `bootstrap` service to finish — that\'s when the admin seed lands.',
        'Frontend-app: `flutter pub get`, then run via the script at `scripts/run-web-dev.ps1` for web preview against the cloud backend.',
        'Tests: `cd frontend-app && flutter analyze && flutter test`; `cd backend && pytest`.',
      ],
      tip:
          'Full guide: `docs/technical/development/setup-guide.md`. Coding standards: `development/coding-standards.md`.',
      keywords: ['setup', 'development', 'local', 'dev', 'docker compose'],
    ),
    HelpArticle(
      id: 'dev-testing',
      audiences: adminOnly,
      title: 'Testing strategy',
      body:
          'Three test layers run independently on every PR: backend pytest (unit + integration with a real Postgres in CI), Flutter `flutter test` (unit + widget) plus `integration_test/`, and frontend-web Playwright (E2E workflows). UI-quality tests run via `test/ui_quality_test.dart` to mirror the Playwright suite.',
      steps: [
        'Backend: `pytest -q`. Markers: `unit`, `integration`, `slow`.',
        'Flutter: `flutter analyze && flutter test`. The UI-quality suite asserts layout safety + accessibility labels across viewports.',
        'Web E2E: `cd frontend-web && npm run e2e`. CI gates the suite to PRs that touch `frontend-web/**` or workflows that depend on it.',
        'Coverage targets: backend ≥80% line, Flutter ≥70% line, Playwright = workflow coverage rather than line %.',
      ],
      tip:
          'Test plan: `docs/technical/testing/test-plan.md`. QA workflow: `testing/qa-toolchain-workflow.md`.',
      keywords: ['testing', 'pytest', 'flutter test', 'playwright', 'qa'],
    ),
    HelpArticle(
      id: 'dev-billing',
      audiences: adminOnly,
      title: 'Billing & subscription (SaaS owner)',
      body:
          'Aura is delivered to schools as a managed SaaS. The platform admin (you) owns billing, school onboarding/offboarding, and the subscription state on the Admin → Schools panel.',
      steps: [
        'Each School row has `subscription_status` (`active` / `trial` / `paused` / `cancelled`).',
        'A school in `paused` or `cancelled` falls into limited-mode at the frontend (read-only).',
        'Use `/admin/schools/{id}` to flip subscription state. Audit log records the actor + reason.',
        'Stripe / payment-gateway integration lives in the backend\'s `subscription` router — not yet exposed end-to-end; the panel currently flips state manually.',
      ],
      tip:
          'When the gateway integration ships, the panel will surface payment links + invoice history per school.',
      keywords: ['billing', 'subscription', 'saas', 'admin', 'payments'],
    ),
  ],
);
