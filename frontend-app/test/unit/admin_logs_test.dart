import 'package:aura_app/shared/models/logs.dart';
import 'package:aura_app/shared/models/subscription.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('AuditLogPage parses the {total, items} envelope', () {
    final p = AuditLogPage.from({
      'total': 2,
      'items': [
        {
          'id': 1,
          'school_id': 5,
          'actor_user_id': 9,
          'action': 'school_create',
          'status': 'success',
          'created_at': '2026-05-22T01:00:00Z',
        },
        {'id': 2, 'action': 'school_status_update', 'status': 'failed', 'details': 'nope'},
      ],
    });
    expect(p.total, 2);
    expect(p.items.length, 2);
    expect(p.items.first.action, 'school_create');
    expect(p.items.first.status, 'success');
    expect(p.items[1].details, 'nope');
  });

  test('AuditLogPage also accepts a plain list', () {
    final p = AuditLogPage.from([
      {'id': 1, 'action': 'x'}
    ]);
    expect(p.total, 1);
    expect(p.items.first.id, 1);
  });

  test('NotificationLogItem parses', () {
    final n = NotificationLogItem.fromJson({
      'id': 3,
      'category': 'missed_events',
      'channel': 'email',
      'status': 'sent',
      'subject': 'Hi',
    });
    expect(n.category, 'missed_events');
    expect(n.status, 'sent');
    expect(n.subject, 'Hi');
  });

  test('SchoolSubscription parses plan + limits', () {
    final s = SchoolSubscription.fromJson({
      'school_id': 5,
      'plan_name': 'Pro',
      'user_limit': 500,
      'event_limit_monthly': 100,
      'import_limit_monthly': 20,
      'auto_renew': true,
      'renewal_date': '2026-12-01',
    });
    expect(s.planName, 'Pro');
    expect(s.userLimit, 500);
    expect(s.autoRenew, isTrue);
    expect(s.renewalDate?.year, 2026);
  });
}
