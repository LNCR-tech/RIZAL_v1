// ---------------------------------------------------------------------------
// Audience / event_targets
// ---------------------------------------------------------------------------

export const AUDIENCE_SCOPE_OPTIONS = [
    { value: 'ALL', label: 'All Students' },
    { value: 'YEAR_LEVEL', label: 'Specific Year Level' },
    { value: 'DEPARTMENT', label: 'Specific Department' },
    { value: 'COURSE', label: 'Specific Course' },
    { value: 'DEPARTMENT_YEAR', label: 'Specific Department + Year Level' },
    { value: 'COURSE_YEAR', label: 'Specific Course + Year Level' },
]

export const YEAR_LEVEL_OPTIONS = [
    { value: 1, label: '1st Year' },
    { value: 2, label: '2nd Year' },
    { value: 3, label: '3rd Year' },
    { value: 4, label: '4th Year' },
    { value: 5, label: '5th Year' },
]

/** True when the chosen scope requires a year_level field. */
export function scopeNeedsYearLevel(scope) {
    return scope === 'YEAR_LEVEL' || scope === 'DEPARTMENT_YEAR' || scope === 'COURSE_YEAR'
}

/** True when the chosen scope requires a department_id field. */
export function scopeNeedsDepartment(scope) {
    return scope === 'DEPARTMENT' || scope === 'DEPARTMENT_YEAR'
}

/** True when the chosen scope requires a course_id field. */
export function scopeNeedsCourse(scope) {
    return scope === 'COURSE' || scope === 'COURSE_YEAR'
}

/**
 * Build the event_targets array from the audience draft fields.
 * Returns null when the scope is ALL (backend default — omit the field).
 * Throws a descriptive Error when required sub-fields are missing.
 */
export function buildEventTargetsFromDraft(draft) {
    const scope = String(draft?.audienceScope || 'ALL').toUpperCase()

    if (scope === 'ALL') {
        return [{ scope_type: 'ALL' }]
    }

    const target = { scope_type: scope }

    if (scopeNeedsYearLevel(scope)) {
        const yearLevel = Number(draft?.audienceYearLevel)
        if (!Number.isFinite(yearLevel) || yearLevel < 1 || yearLevel > 5) {
            throw new Error('Please select a valid year level (1–5).')
        }
        target.year_level = yearLevel
    }

    if (scopeNeedsDepartment(scope)) {
        const deptId = Number(draft?.audienceDepartmentId)
        if (!Number.isFinite(deptId) || deptId <= 0) {
            throw new Error('Please select a department.')
        }
        target.department_id = deptId
    }

    if (scopeNeedsCourse(scope)) {
        const courseId = Number(draft?.audienceCourseId)
        if (!Number.isFinite(courseId) || courseId <= 0) {
            throw new Error('Please select a course.')
        }
        target.course_id = courseId
    }

    return [target]
}

/**
 * Derive audience draft fields from an existing event's event_targets array.
 * Falls back to ALL when the array is empty or absent.
 */
function audienceDraftFromEventTargets(eventTargets) {
    const targets = Array.isArray(eventTargets) ? eventTargets : []
    const first = targets[0]
    if (!first) return { audienceScope: 'ALL', audienceYearLevel: 1, audienceDepartmentId: null, audienceCourseId: null }

    return {
        audienceScope: String(first.scope_type || 'ALL').toUpperCase(),
        audienceYearLevel: first.year_level ?? 1,
        audienceDepartmentId: first.department_id ?? null,
        audienceCourseId: first.course_id ?? null,
    }
}

// ---------------------------------------------------------------------------
// Status helpers
// ---------------------------------------------------------------------------

const EVENT_STATUS_VALUES = ['upcoming', 'ongoing', 'completed', 'cancelled']

export const EVENT_STATUS_OPTIONS = [
    { value: 'upcoming', label: 'Upcoming' },
    { value: 'ongoing', label: 'Ongoing' },
    { value: 'completed', label: 'Completed' },
    { value: 'cancelled', label: 'Cancelled' },
]

function normalizeStatusValue(value) {
    const normalized = String(value || '').trim().toLowerCase()
    if (normalized === 'done') return 'completed'
    return EVENT_STATUS_VALUES.includes(normalized) ? normalized : 'upcoming'
}

export function toOptionalFiniteNumber(value) {
    if (value == null || value === '') return null
    const normalized = Number(value)
    return Number.isFinite(normalized) ? normalized : null
}

function isValidLatitude(value) {
    return Number.isFinite(value) && value >= -90 && value <= 90
}

function isValidLongitude(value) {
    return Number.isFinite(value) && value >= -180 && value <= 180
}

export function toOptionalNonNegativeInteger(value, fallback = 0) {
    if (value == null || value === '') return fallback
    const normalized = Number(value)
    if (!Number.isFinite(normalized)) return fallback
    return Math.max(0, Math.round(normalized))
}

export function toBackendDateTimeValue(value) {
    const normalized = String(value || '').trim()
    if (!normalized) return normalized

    const parsed = new Date(normalized)
    if (!Number.isFinite(parsed.getTime())) return normalized
    return parsed.toISOString()
}

export function toLocalDateTimeInputValue(value) {
    const normalized = String(value || '').trim()
    if (!normalized) return ''

    const match = normalized.match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})/)
    if (match) {
        return `${match[1]}T${match[2]}`
    }

    const parsed = new Date(normalized)
    if (!Number.isFinite(parsed.getTime())) return ''

    const year = parsed.getFullYear()
    const month = `${parsed.getMonth() + 1}`.padStart(2, '0')
    const day = `${parsed.getDate()}`.padStart(2, '0')
    const hours = `${parsed.getHours()}`.padStart(2, '0')
    const minutes = `${parsed.getMinutes()}`.padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}`
}

export function createEventEditorDraft(event = null) {
    const audienceFields = audienceDraftFromEventTargets(event?.event_targets)
    return {
        name: String(event?.name || '').trim(),
        location: String(event?.location || '').trim(),
        startTime: toLocalDateTimeInputValue(event?.start_datetime ?? event?.start_time),
        endTime: toLocalDateTimeInputValue(event?.end_datetime ?? event?.end_time),
        status: normalizeStatusValue(event?.status),
        geoRequired: Boolean(event?.geo_required),
        latitude: event?.geo_latitude ?? '',
        longitude: event?.geo_longitude ?? '',
        radiusM: event?.geo_radius_m ?? '',
        maxAccuracyM: event?.geo_max_accuracy_m ?? '',
        earlyCheckInMinutes: event?.early_check_in_minutes ?? 0,
        lateThresholdMinutes: event?.late_threshold_minutes ?? 0,
        signOutGraceMinutes: event?.sign_out_grace_minutes ?? 0,
        signOutOpenDelayMinutes: event?.sign_out_open_delay_minutes ?? 0,
        ...audienceFields,
    }
}

export function validateEventEditorDraft(draft) {
    const name = String(draft?.name || '').trim()
    const location = String(draft?.location || '').trim()
    const startTime = new Date(String(draft?.startTime || '').trim())
    const endTime = new Date(String(draft?.endTime || '').trim())

    if (!name) {
        throw new Error('Event name is required.')
    }

    if (!location) {
        throw new Error('Event location is required.')
    }

    if (!Number.isFinite(startTime.getTime()) || !Number.isFinite(endTime.getTime())) {
        throw new Error('Please provide valid start and end dates.')
    }

    if (endTime <= startTime) {
        throw new Error('The event end time must be later than the start time.')
    }

    const geoLatitude = toOptionalFiniteNumber(draft?.latitude)
    const geoLongitude = toOptionalFiniteNumber(draft?.longitude)
    const geoRadius = toOptionalFiniteNumber(draft?.radiusM)
    const providedGeoFields = [geoLatitude != null, geoLongitude != null, geoRadius != null]

    if (providedGeoFields.some(Boolean) && !providedGeoFields.every(Boolean)) {
        throw new Error('Latitude, longitude, and radius must be provided together for the event geofence.')
    }

    if (Boolean(draft?.geoRequired) && !providedGeoFields.every(Boolean)) {
        throw new Error('Geofence coordinates and radius are required when geolocation is enabled.')
    }

    if (geoLatitude != null && !isValidLatitude(geoLatitude)) {
        throw new Error('Latitude must be between -90 and 90.')
    }

    if (geoLongitude != null && !isValidLongitude(geoLongitude)) {
        throw new Error('Longitude must be between -180 and 180.')
    }

    if (geoRadius != null && geoRadius <= 0) {
        throw new Error('Allowed radius must be greater than 0 meters.')
    }

    const signOutGraceMinutes = toOptionalNonNegativeInteger(draft?.signOutGraceMinutes, 0)
    const signOutOpenDelayMinutes = toOptionalNonNegativeInteger(draft?.signOutOpenDelayMinutes, 0)

    if (signOutOpenDelayMinutes > signOutGraceMinutes) {
        throw new Error('Sign-out open delay cannot be greater than sign-out grace minutes.')
    }
}

export function buildEventUpdatePayloadFromDraft(draft) {
    validateEventEditorDraft(draft)

    return {
        name: String(draft?.name || '').trim(),
        location: String(draft?.location || '').trim(),
        start_datetime: toBackendDateTimeValue(draft?.startTime),
        end_datetime: toBackendDateTimeValue(draft?.endTime),
        status: normalizeStatusValue(draft?.status),
        geo_required: Boolean(draft?.geoRequired),
        geo_latitude: toOptionalFiniteNumber(draft?.latitude),
        geo_longitude: toOptionalFiniteNumber(draft?.longitude),
        geo_radius_m: toOptionalFiniteNumber(draft?.radiusM),
        geo_max_accuracy_m: toOptionalFiniteNumber(draft?.maxAccuracyM),
        early_check_in_minutes: toOptionalNonNegativeInteger(draft?.earlyCheckInMinutes, 0),
        late_threshold_minutes: toOptionalNonNegativeInteger(draft?.lateThresholdMinutes, 0),
        sign_out_grace_minutes: toOptionalNonNegativeInteger(draft?.signOutGraceMinutes, 0),
        sign_out_open_delay_minutes: toOptionalNonNegativeInteger(draft?.signOutOpenDelayMinutes, 0),
        event_targets: buildEventTargetsFromDraft(draft),
    }
}
