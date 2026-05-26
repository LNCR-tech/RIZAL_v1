import 'package:aura_app/features/events/application/event_editor_draft.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('event audience scope predicates', () {
    test('scopeNeedsYearLevel matches year-based scopes', () {
      for (final scope in ['YEAR_LEVEL', 'DEPARTMENT_YEAR', 'COURSE_YEAR']) {
        expect(scopeNeedsYearLevel(scope), isTrue);
      }
      for (final scope in ['ALL', 'DEPARTMENT', 'COURSE']) {
        expect(scopeNeedsYearLevel(scope), isFalse);
      }
    });

    test('scopeNeedsDepartment matches department-based scopes', () {
      for (final scope in ['DEPARTMENT', 'DEPARTMENT_YEAR']) {
        expect(scopeNeedsDepartment(scope), isTrue);
      }
      for (final scope in ['ALL', 'YEAR_LEVEL', 'COURSE', 'COURSE_YEAR']) {
        expect(scopeNeedsDepartment(scope), isFalse);
      }
    });

    test('scopeNeedsCourse matches course-based scopes', () {
      for (final scope in ['COURSE', 'COURSE_YEAR']) {
        expect(scopeNeedsCourse(scope), isTrue);
      }
      for (final scope in ['ALL', 'YEAR_LEVEL', 'DEPARTMENT', 'DEPARTMENT_YEAR']) {
        expect(scopeNeedsCourse(scope), isFalse);
      }
    });
  });

  group('event audience option shape', () {
    test('contains all six scope values', () {
      final values = audienceScopeOptions.map((option) => option.value);
      expect(
        values,
        containsAll([
          'ALL',
          'YEAR_LEVEL',
          'DEPARTMENT',
          'COURSE',
          'DEPARTMENT_YEAR',
          'COURSE_YEAR',
        ]),
      );
      expect(values.length, 6);
    });

    test('every audience option has a non-empty label', () {
      for (final option in audienceScopeOptions) {
        expect(option.label, isNotEmpty);
      }
    });

    test('has exactly five year-level options', () {
      expect(yearLevelOptions.length, 5);
      for (var i = 0; i < yearLevelOptions.length; i++) {
        expect(yearLevelOptions[i].value, i + 1);
        expect(yearLevelOptions[i].label, isNotEmpty);
      }
    });
  });

  group('buildEventTargetsFromDraft', () {
    test('ALL scope returns an ALL event target', () {
      expect(
        buildEventTargetsFromDraft(
            const EventEditorDraft(audienceScope: 'ALL')),
        [
          {'scope_type': 'ALL'},
        ],
      );
    });

    test('defaults to ALL when audienceScope is absent', () {
      expect(
        buildEventTargetsFromDraft(const EventEditorDraft()),
        [
          {'scope_type': 'ALL'},
        ],
      );
    });

    test('YEAR_LEVEL scope includes year_level', () {
      expect(
        buildEventTargetsFromDraft(
          const EventEditorDraft(
              audienceScope: 'YEAR_LEVEL', audienceYearLevel: 3),
        ),
        [
          {'scope_type': 'YEAR_LEVEL', 'year_level': 3},
        ],
      );
    });

    test('YEAR_LEVEL scope rejects missing years', () {
      expect(
        () => buildEventTargetsFromDraft(
          const EventEditorDraft(
            audienceScope: 'YEAR_LEVEL',
            audienceYearLevel: null,
          ),
        ),
        throwsArgumentError,
      );
    });

    test('YEAR_LEVEL scope rejects out-of-range years', () {
      expect(
        () => buildEventTargetsFromDraft(
          const EventEditorDraft(
              audienceScope: 'YEAR_LEVEL', audienceYearLevel: 6),
        ),
        throwsArgumentError,
      );
    });

    test('DEPARTMENT scope includes department_id', () {
      expect(
        buildEventTargetsFromDraft(
          const EventEditorDraft(
              audienceScope: 'DEPARTMENT', audienceDepartmentId: 42),
        ),
        [
          {'scope_type': 'DEPARTMENT', 'department_id': 42},
        ],
      );
    });

    test('DEPARTMENT scope rejects missing department_id', () {
      expect(
        () => buildEventTargetsFromDraft(
          const EventEditorDraft(audienceScope: 'DEPARTMENT'),
        ),
        throwsArgumentError,
      );
    });

    test('COURSE scope includes course_id', () {
      expect(
        buildEventTargetsFromDraft(
          const EventEditorDraft(audienceScope: 'COURSE', audienceCourseId: 7),
        ),
        [
          {'scope_type': 'COURSE', 'course_id': 7},
        ],
      );
    });

    test('COURSE scope rejects missing course_id', () {
      expect(
        () => buildEventTargetsFromDraft(
          const EventEditorDraft(audienceScope: 'COURSE'),
        ),
        throwsArgumentError,
      );
    });

    test('DEPARTMENT_YEAR scope includes department_id and year_level', () {
      expect(
        buildEventTargetsFromDraft(
          const EventEditorDraft(
            audienceScope: 'DEPARTMENT_YEAR',
            audienceDepartmentId: 10,
            audienceYearLevel: 2,
          ),
        ),
        [
          {
            'scope_type': 'DEPARTMENT_YEAR',
            'department_id': 10,
            'year_level': 2,
          },
        ],
      );
    });

    test('DEPARTMENT_YEAR scope rejects missing department_id', () {
      expect(
        () => buildEventTargetsFromDraft(
          const EventEditorDraft(
            audienceScope: 'DEPARTMENT_YEAR',
            audienceYearLevel: 2,
          ),
        ),
        throwsArgumentError,
      );
    });

    test('DEPARTMENT_YEAR scope rejects missing year_level', () {
      expect(
        () => buildEventTargetsFromDraft(
          const EventEditorDraft(
            audienceScope: 'DEPARTMENT_YEAR',
            audienceDepartmentId: 10,
            audienceYearLevel: null,
          ),
        ),
        throwsArgumentError,
      );
    });

    test('COURSE_YEAR scope includes course_id and year_level', () {
      expect(
        buildEventTargetsFromDraft(
          const EventEditorDraft(
            audienceScope: 'COURSE_YEAR',
            audienceCourseId: 5,
            audienceYearLevel: 1,
          ),
        ),
        [
          {'scope_type': 'COURSE_YEAR', 'course_id': 5, 'year_level': 1},
        ],
      );
    });

    test('COURSE_YEAR scope rejects missing course_id', () {
      expect(
        () => buildEventTargetsFromDraft(
          const EventEditorDraft(
            audienceScope: 'COURSE_YEAR',
            audienceYearLevel: 1,
          ),
        ),
        throwsArgumentError,
      );
    });

    test('COURSE_YEAR scope rejects missing year_level', () {
      expect(
        () => buildEventTargetsFromDraft(
          const EventEditorDraft(
            audienceScope: 'COURSE_YEAR',
            audienceCourseId: 5,
            audienceYearLevel: null,
          ),
        ),
        throwsArgumentError,
      );
    });
  });

  group('createEventEditorDraft audience fields', () {
    test('defaults to ALL when event has no event_targets', () {
      final draft = createEventEditorDraft({});
      expect(draft.audienceScope, 'ALL');
      expect(draft.audienceYearLevel, 1);
      expect(draft.audienceDepartmentId, isNull);
      expect(draft.audienceCourseId, isNull);
    });

    test('defaults to ALL when called with null', () {
      expect(createEventEditorDraft().audienceScope, 'ALL');
    });

    test('loads YEAR_LEVEL target from existing event', () {
      final draft = createEventEditorDraft({
        'event_targets': [
          {'scope_type': 'YEAR_LEVEL', 'year_level': 4},
        ],
      });

      expect(draft.audienceScope, 'YEAR_LEVEL');
      expect(draft.audienceYearLevel, 4);
    });

    test('loads COURSE_YEAR target from existing event', () {
      final draft = createEventEditorDraft({
        'event_targets': [
          {'scope_type': 'COURSE_YEAR', 'course_id': 99, 'year_level': 2},
        ],
      });

      expect(draft.audienceScope, 'COURSE_YEAR');
      expect(draft.audienceCourseId, 99);
      expect(draft.audienceYearLevel, 2);
    });

    test('loads DEPARTMENT_YEAR target from existing event', () {
      final draft = createEventEditorDraft({
        'event_targets': [
          {'scope_type': 'DEPARTMENT_YEAR', 'department_id': 11, 'year_level': 3},
        ],
      });

      expect(draft.audienceScope, 'DEPARTMENT_YEAR');
      expect(draft.audienceDepartmentId, 11);
      expect(draft.audienceYearLevel, 3);
    });

    test('loads DEPARTMENT target from existing event', () {
      final draft = createEventEditorDraft({
        'event_targets': [
          {'scope_type': 'DEPARTMENT', 'department_id': 5},
        ],
      });

      expect(draft.audienceScope, 'DEPARTMENT');
      expect(draft.audienceDepartmentId, 5);
    });

    test('loads COURSE target from existing event', () {
      final draft = createEventEditorDraft({
        'event_targets': [
          {'scope_type': 'COURSE', 'course_id': 8},
        ],
      });

      expect(draft.audienceScope, 'COURSE');
      expect(draft.audienceCourseId, 8);
    });

    test('preserves non-audience draft fields', () {
      final draft = createEventEditorDraft({
        'name': 'Test Event',
        'event_targets': [
          {'scope_type': 'ALL'},
        ],
      });

      expect(draft.name, 'Test Event');
      expect(draft.audienceScope, 'ALL');
    });
  });
}
