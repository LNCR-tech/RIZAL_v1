import { describe, it, expect } from 'vitest'
import {
  AUDIENCE_SCOPE_OPTIONS,
  YEAR_LEVEL_OPTIONS,
  buildEventTargetsFromDraft,
  createEventEditorDraft,
  scopeNeedsCourse,
  scopeNeedsDepartment,
  scopeNeedsYearLevel,
} from '@/services/eventEditor.js'

// ---------------------------------------------------------------------------
// Scope predicate helpers
// ---------------------------------------------------------------------------

describe('scopeNeedsYearLevel', () => {
  it.each(['YEAR_LEVEL', 'DEPARTMENT_YEAR', 'COURSE_YEAR'])('returns true for %s', (scope) => {
    expect(scopeNeedsYearLevel(scope)).toBe(true)
  })
  it.each(['ALL', 'DEPARTMENT', 'COURSE'])('returns false for %s', (scope) => {
    expect(scopeNeedsYearLevel(scope)).toBe(false)
  })
})

describe('scopeNeedsDepartment', () => {
  it.each(['DEPARTMENT', 'DEPARTMENT_YEAR'])('returns true for %s', (scope) => {
    expect(scopeNeedsDepartment(scope)).toBe(true)
  })
  it.each(['ALL', 'YEAR_LEVEL', 'COURSE', 'COURSE_YEAR'])('returns false for %s', (scope) => {
    expect(scopeNeedsDepartment(scope)).toBe(false)
  })
})

describe('scopeNeedsCourse', () => {
  it.each(['COURSE', 'COURSE_YEAR'])('returns true for %s', (scope) => {
    expect(scopeNeedsCourse(scope)).toBe(true)
  })
  it.each(['ALL', 'YEAR_LEVEL', 'DEPARTMENT', 'DEPARTMENT_YEAR'])('returns false for %s', (scope) => {
    expect(scopeNeedsCourse(scope)).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// AUDIENCE_SCOPE_OPTIONS and YEAR_LEVEL_OPTIONS shape
// ---------------------------------------------------------------------------

describe('AUDIENCE_SCOPE_OPTIONS', () => {
  it('contains all six scope values', () => {
    const values = AUDIENCE_SCOPE_OPTIONS.map((o) => o.value)
    expect(values).toEqual(expect.arrayContaining([
      'ALL', 'YEAR_LEVEL', 'DEPARTMENT', 'COURSE', 'DEPARTMENT_YEAR', 'COURSE_YEAR',
    ]))
    expect(values).toHaveLength(6)
  })
  it('every option has a non-empty label', () => {
    AUDIENCE_SCOPE_OPTIONS.forEach((opt) => {
      expect(typeof opt.label).toBe('string')
      expect(opt.label.length).toBeGreaterThan(0)
    })
  })
})

describe('YEAR_LEVEL_OPTIONS', () => {
  it('has exactly 5 entries for years 1–5', () => {
    expect(YEAR_LEVEL_OPTIONS).toHaveLength(5)
    YEAR_LEVEL_OPTIONS.forEach((opt, i) => {
      expect(opt.value).toBe(i + 1)
    })
  })
})

// ---------------------------------------------------------------------------
// buildEventTargetsFromDraft
// ---------------------------------------------------------------------------

describe('buildEventTargetsFromDraft', () => {
  it('ALL scope returns [{scope_type:"ALL"}]', () => {
    expect(buildEventTargetsFromDraft({ audienceScope: 'ALL' })).toEqual([{ scope_type: 'ALL' }])
  })

  it('defaults to ALL when audienceScope is absent', () => {
    expect(buildEventTargetsFromDraft({})).toEqual([{ scope_type: 'ALL' }])
  })

  it('YEAR_LEVEL scope includes year_level', () => {
    const result = buildEventTargetsFromDraft({ audienceScope: 'YEAR_LEVEL', audienceYearLevel: 3 })
    expect(result).toEqual([{ scope_type: 'YEAR_LEVEL', year_level: 3 }])
  })

  it('YEAR_LEVEL scope throws when year_level is missing', () => {
    expect(() => buildEventTargetsFromDraft({ audienceScope: 'YEAR_LEVEL', audienceYearLevel: null }))
      .toThrow()
  })

  it('YEAR_LEVEL scope throws when year_level is out of range', () => {
    expect(() => buildEventTargetsFromDraft({ audienceScope: 'YEAR_LEVEL', audienceYearLevel: 6 }))
      .toThrow()
  })

  it('DEPARTMENT scope includes department_id', () => {
    const result = buildEventTargetsFromDraft({ audienceScope: 'DEPARTMENT', audienceDepartmentId: 42 })
    expect(result).toEqual([{ scope_type: 'DEPARTMENT', department_id: 42 }])
  })

  it('DEPARTMENT scope throws when department_id is missing', () => {
    expect(() => buildEventTargetsFromDraft({ audienceScope: 'DEPARTMENT', audienceDepartmentId: null }))
      .toThrow()
  })

  it('COURSE scope includes course_id', () => {
    const result = buildEventTargetsFromDraft({ audienceScope: 'COURSE', audienceCourseId: 7 })
    expect(result).toEqual([{ scope_type: 'COURSE', course_id: 7 }])
  })

  it('COURSE scope throws when course_id is missing', () => {
    expect(() => buildEventTargetsFromDraft({ audienceScope: 'COURSE', audienceCourseId: null }))
      .toThrow()
  })

  it('DEPARTMENT_YEAR scope includes both department_id and year_level', () => {
    const result = buildEventTargetsFromDraft({
      audienceScope: 'DEPARTMENT_YEAR',
      audienceDepartmentId: 10,
      audienceYearLevel: 2,
    })
    expect(result).toEqual([{ scope_type: 'DEPARTMENT_YEAR', department_id: 10, year_level: 2 }])
  })

  it('DEPARTMENT_YEAR scope throws when department_id is missing', () => {
    expect(() => buildEventTargetsFromDraft({
      audienceScope: 'DEPARTMENT_YEAR',
      audienceDepartmentId: null,
      audienceYearLevel: 2,
    })).toThrow()
  })

  it('DEPARTMENT_YEAR scope throws when year_level is missing', () => {
    expect(() => buildEventTargetsFromDraft({
      audienceScope: 'DEPARTMENT_YEAR',
      audienceDepartmentId: 10,
      audienceYearLevel: null,
    })).toThrow()
  })

  it('COURSE_YEAR scope includes both course_id and year_level', () => {
    const result = buildEventTargetsFromDraft({
      audienceScope: 'COURSE_YEAR',
      audienceCourseId: 5,
      audienceYearLevel: 1,
    })
    expect(result).toEqual([{ scope_type: 'COURSE_YEAR', course_id: 5, year_level: 1 }])
  })

  it('COURSE_YEAR scope throws when course_id is missing', () => {
    expect(() => buildEventTargetsFromDraft({
      audienceScope: 'COURSE_YEAR',
      audienceCourseId: null,
      audienceYearLevel: 1,
    })).toThrow()
  })

  it('COURSE_YEAR scope throws when year_level is missing', () => {
    expect(() => buildEventTargetsFromDraft({
      audienceScope: 'COURSE_YEAR',
      audienceCourseId: 5,
      audienceYearLevel: null,
    })).toThrow()
  })
})

// ---------------------------------------------------------------------------
// createEventEditorDraft — audience field hydration
// ---------------------------------------------------------------------------

describe('createEventEditorDraft audience fields', () => {
  it('defaults to ALL when event has no event_targets', () => {
    const draft = createEventEditorDraft({})
    expect(draft.audienceScope).toBe('ALL')
    expect(draft.audienceYearLevel).toBe(1)
    expect(draft.audienceDepartmentId).toBeNull()
    expect(draft.audienceCourseId).toBeNull()
  })

  it('defaults to ALL when called with null', () => {
    const draft = createEventEditorDraft(null)
    expect(draft.audienceScope).toBe('ALL')
  })

  it('loads YEAR_LEVEL target from existing event', () => {
    const draft = createEventEditorDraft({
      event_targets: [{ scope_type: 'YEAR_LEVEL', year_level: 4 }],
    })
    expect(draft.audienceScope).toBe('YEAR_LEVEL')
    expect(draft.audienceYearLevel).toBe(4)
  })

  it('loads COURSE_YEAR target from existing event', () => {
    const draft = createEventEditorDraft({
      event_targets: [{ scope_type: 'COURSE_YEAR', course_id: 99, year_level: 2 }],
    })
    expect(draft.audienceScope).toBe('COURSE_YEAR')
    expect(draft.audienceCourseId).toBe(99)
    expect(draft.audienceYearLevel).toBe(2)
  })

  it('loads DEPARTMENT_YEAR target from existing event', () => {
    const draft = createEventEditorDraft({
      event_targets: [{ scope_type: 'DEPARTMENT_YEAR', department_id: 11, year_level: 3 }],
    })
    expect(draft.audienceScope).toBe('DEPARTMENT_YEAR')
    expect(draft.audienceDepartmentId).toBe(11)
    expect(draft.audienceYearLevel).toBe(3)
  })

  it('loads DEPARTMENT target from existing event', () => {
    const draft = createEventEditorDraft({
      event_targets: [{ scope_type: 'DEPARTMENT', department_id: 5 }],
    })
    expect(draft.audienceScope).toBe('DEPARTMENT')
    expect(draft.audienceDepartmentId).toBe(5)
  })

  it('loads COURSE target from existing event', () => {
    const draft = createEventEditorDraft({
      event_targets: [{ scope_type: 'COURSE', course_id: 8 }],
    })
    expect(draft.audienceScope).toBe('COURSE')
    expect(draft.audienceCourseId).toBe(8)
  })

  it('preserves all other draft fields alongside audience fields', () => {
    const draft = createEventEditorDraft({
      name: 'Test Event',
      event_targets: [{ scope_type: 'ALL' }],
    })
    expect(draft.name).toBe('Test Event')
    expect(draft.audienceScope).toBe('ALL')
  })
})
