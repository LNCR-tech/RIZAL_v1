import '../../../shared/utils/json.dart';

class AudienceScopeOption {
  const AudienceScopeOption({required this.value, required this.label});

  final String value;
  final String label;
}

class YearLevelOption {
  const YearLevelOption({required this.value, required this.label});

  final int value;
  final String label;
}

const audienceScopeOptions = [
  AudienceScopeOption(value: 'ALL', label: 'All Students'),
  AudienceScopeOption(value: 'YEAR_LEVEL', label: 'Specific Year Level'),
  AudienceScopeOption(value: 'DEPARTMENT', label: 'Specific Department'),
  AudienceScopeOption(value: 'COURSE', label: 'Specific Course'),
  AudienceScopeOption(
      value: 'DEPARTMENT_YEAR', label: 'Specific Department + Year Level'),
  AudienceScopeOption(
      value: 'COURSE_YEAR', label: 'Specific Course + Year Level'),
];

const yearLevelOptions = [
  YearLevelOption(value: 1, label: '1st Year'),
  YearLevelOption(value: 2, label: '2nd Year'),
  YearLevelOption(value: 3, label: '3rd Year'),
  YearLevelOption(value: 4, label: '4th Year'),
  YearLevelOption(value: 5, label: '5th Year'),
];

bool scopeNeedsYearLevel(String? scope) {
  final normalized = _normalizeScope(scope);
  return normalized == 'YEAR_LEVEL' ||
      normalized == 'DEPARTMENT_YEAR' ||
      normalized == 'COURSE_YEAR';
}

bool scopeNeedsDepartment(String? scope) {
  final normalized = _normalizeScope(scope);
  return normalized == 'DEPARTMENT' || normalized == 'DEPARTMENT_YEAR';
}

bool scopeNeedsCourse(String? scope) {
  final normalized = _normalizeScope(scope);
  return normalized == 'COURSE' || normalized == 'COURSE_YEAR';
}

class EventEditorDraft {
  const EventEditorDraft({
    this.name = '',
    this.audienceScope = 'ALL',
    this.audienceYearLevel = 1,
    this.audienceDepartmentId,
    this.audienceCourseId,
  });

  final String name;
  final String audienceScope;
  final int? audienceYearLevel;
  final int? audienceDepartmentId;
  final int? audienceCourseId;

  factory EventEditorDraft.fromEvent(Map<String, dynamic>? event) {
    final fields = _audienceDraftFromEventTargets(event?['event_targets']);
    return EventEditorDraft(
      name: asStr(event?['name']) ?? '',
      audienceScope: fields.audienceScope,
      audienceYearLevel: fields.audienceYearLevel,
      audienceDepartmentId: fields.audienceDepartmentId,
      audienceCourseId: fields.audienceCourseId,
    );
  }
}

List<Map<String, dynamic>> buildEventTargetsFromDraft(EventEditorDraft draft) {
  final scope = _normalizeScope(draft.audienceScope);
  if (scope == 'ALL') {
    return [
      {'scope_type': 'ALL'},
    ];
  }

  final target = <String, dynamic>{'scope_type': scope};

  if (scopeNeedsYearLevel(scope)) {
    final yearLevel = draft.audienceYearLevel;
    if (yearLevel == null || yearLevel < 1 || yearLevel > 5) {
      throw ArgumentError('Please select a valid year level (1-5).');
    }
    target['year_level'] = yearLevel;
  }

  if (scopeNeedsDepartment(scope)) {
    final departmentId = draft.audienceDepartmentId;
    if (departmentId == null || departmentId <= 0) {
      throw ArgumentError('Please select a department.');
    }
    target['department_id'] = departmentId;
  }

  if (scopeNeedsCourse(scope)) {
    final courseId = draft.audienceCourseId;
    if (courseId == null || courseId <= 0) {
      throw ArgumentError('Please select a course.');
    }
    target['course_id'] = courseId;
  }

  return [target];
}

EventEditorDraft createEventEditorDraft([Map<String, dynamic>? event]) =>
    EventEditorDraft.fromEvent(event);

String _normalizeScope(String? scope) {
  final value = (scope ?? 'ALL').trim().toUpperCase();
  return value.isEmpty ? 'ALL' : value;
}

EventEditorDraft _audienceDraftFromEventTargets(Object? eventTargets) {
  final targets = asMapList(eventTargets);
  if (targets.isEmpty) return const EventEditorDraft();

  final first = targets.first;
  return EventEditorDraft(
    audienceScope: _normalizeScope(asStr(first['scope_type'])),
    audienceYearLevel: asInt(first['year_level']) ?? 1,
    audienceDepartmentId: asInt(first['department_id']),
    audienceCourseId: asInt(first['course_id']),
  );
}
