import {
    isNgrokApiBaseUrl,
    resolveAbsoluteApiBaseUrl,
    resolveApiBaseUrl,
} from '@/services/backendBaseUrl.js'
import {
    normalizeAttendanceRecord,
    normalizeCreateSchoolWithSchoolItResponse,
    normalizeDepartment,
    normalizeEvent,
    normalizeEventLocationResponse,
    normalizeEventTimeStatus,
    normalizeFaceReferenceResponse,
    normalizeFaceStatus,
    normalizeFaceVerificationResponse,
    normalizeGovernanceMember,
    normalizeGovernanceSsgSetup,
    normalizeGovernanceStudentCandidate,
    normalizeGovernanceUnitDetail,
    normalizePasswordChangeResponse,
    normalizePasswordResetResponse,
    normalizeProgram,
    normalizeSchoolSettings,
    normalizeStudentFaceRegistrationResponse,
    normalizeTokenPayload,
    normalizeUserWithRelations,
} from '@/services/backendNormalizers.js'
import {
    normalizeImportJobCreateResponse,
    normalizeImportJobStatus,
    normalizeImportPreviewSummary,
} from '@/services/studentImport.js'
import { notifySessionExpired } from '@/services/sessionExpiry.js'

export class BackendApiError extends Error {
    constructor(message, { status = 0, details = null } = {}) {
        super(message)
        this.name = 'BackendApiError'
        this.status = status
        this.details = details
    }
}

export { resolveApiBaseUrl }

const DEFAULT_API_TIMEOUT_MS = 15000
const configuredApiTimeoutMs = Number(import.meta.env.VITE_API_TIMEOUT_MS)
const API_TIMEOUT_MS = Number.isFinite(configuredApiTimeoutMs) && configuredApiTimeoutMs > 0
    ? configuredApiTimeoutMs
    : DEFAULT_API_TIMEOUT_MS

function buildUrl(baseUrl, path, params) {
    const url = new URL(`${resolveAbsoluteApiBaseUrl(baseUrl)}${path}`)

    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            if (value == null || value === '') return
            url.searchParams.set(key, String(value))
        })
    }

    return url.toString()
}

async function parseResponse(response) {
    const contentType = response.headers.get('content-type') || ''
    const isJson = contentType.includes('application/json')

    let payload = null
    try {
        payload = isJson ? await response.json() : await response.text()
    } catch {
        payload = null
    }

    if (!response.ok) {
        const message =
            payload?.detail?.message ||
            payload?.detail ||
            payload?.message ||
            response.statusText ||
            'Request failed.'
        throw new BackendApiError(String(message), {
            status: response.status,
            details: payload,
        })
    }

    if (!isJson) {
        const textPayload = typeof payload === 'string' ? payload.trim() : ''
        const isEmptyBody =
            response.status === 204 ||
            response.status === 205 ||
            textPayload.length === 0

        if (isEmptyBody) {
            return null
        }

        throw new BackendApiError('The API returned an unexpected non-JSON response.', {
            status: response.status,
            details: {
                kind: 'unexpected_non_json',
                contentType,
                payload: textPayload,
            },
        })
    }

    return payload
}

async function request(baseUrl, path, options = {}) {
    const {
        token,
        params,
        headers = {},
        body,
        suppressSessionExpiryHandling = false,
        ...rest
    } = options

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS)

    let response
    try {
        response = await fetch(buildUrl(baseUrl, path, params), {
            ...rest,
            signal: controller.signal,
            headers: {
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
                ...(isNgrokApiBaseUrl(baseUrl) ? { 'ngrok-skip-browser-warning': 'true' } : {}),
                ...headers,
            },
            body,
        })
    } catch (error) {
        if (error?.name === 'AbortError') {
            throw new BackendApiError(
                `The API took too long to respond. The backend or ngrok tunnel may be offline. (${API_TIMEOUT_MS}ms timeout)`,
                {
                    details: {
                        path,
                        timeoutMs: API_TIMEOUT_MS,
                    },
                }
            )
        }

        throw new BackendApiError(
            'Unable to reach the API. The server may be unavailable or the request may be blocked.',
            {
                details: {
                    cause: error?.message || null,
                    path,
                },
            }
        )
    } finally {
        clearTimeout(timeoutId)
    }

    try {
        return await parseResponse(response)
    } catch (error) {
        if (
            token &&
            !suppressSessionExpiryHandling &&
            error instanceof BackendApiError &&
            Number(error.status) === 401
        ) {
            notifySessionExpired()
        }

        throw error
    }
}

async function requestWithFallback(baseUrl, candidatePaths, options = {}, fallbackStatuses = [403, 404, 405]) {
    let lastError = null

    for (const candidatePath of candidatePaths) {
        try {
            return await request(baseUrl, candidatePath, options)
        } catch (error) {
            lastError = error
            const shouldTryNext =
                error instanceof BackendApiError &&
                (
                    fallbackStatuses.includes(Number(error.status)) ||
                    error?.details?.kind === 'unexpected_non_json'
                )

            if (!shouldTryNext) {
                throw error
            }
        }
    }

    throw lastError ?? new BackendApiError('Request failed.')
}

export async function loginForAccessToken(baseUrl, { username, password }) {
    const body = new URLSearchParams({
        username: String(username ?? ''),
        password: String(password ?? ''),
    })

    return normalizeTokenPayload(await requestWithFallback(baseUrl, ['/token', '/api/token'], {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body,
    }, [404, 405]))
}

export async function verifyPasswordForUser(baseUrl, {
    email,
    password,
    expectedUserId = null,
}) {
    const payload = await loginForAccessToken(baseUrl, {
        username: email,
        password,
    })

    const normalizedEmail = String(email || '').trim().toLowerCase()
    const responseEmail = String(payload?.email || '').trim().toLowerCase()
    if (normalizedEmail && responseEmail && normalizedEmail !== responseEmail) {
        throw new BackendApiError('Password confirmation matched a different account.')
    }

    const normalizedExpectedUserId = Number(expectedUserId)
    const responseUserId = Number(payload?.user_id)
    if (Number.isFinite(normalizedExpectedUserId) && Number.isFinite(responseUserId) && normalizedExpectedUserId !== responseUserId) {
        throw new BackendApiError('Password confirmation matched a different account.')
    }

    return true
}

export async function getDepartments(baseUrl, token = null) {
    const payload = await requestWithFallback(baseUrl, ['/api/departments/', '/departments/'], {
        method: 'GET',
        token,
    }, [404, 405])
    return Array.isArray(payload) ? payload.map(normalizeDepartment) : []
}

export async function createDepartment(baseUrl, token, payload) {
    return normalizeDepartment(await requestWithFallback(baseUrl, ['/api/departments/', '/departments/'], {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }, [404, 405]))
}

export async function updateDepartment(baseUrl, token, departmentId, payload) {
    return normalizeDepartment(await requestWithFallback(baseUrl, [`/api/departments/${departmentId}`, `/departments/${departmentId}`], {
        method: 'PATCH',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }, [404, 405]))
}

export async function deleteDepartment(baseUrl, token, departmentId) {
    await requestWithFallback(baseUrl, [`/api/departments/${departmentId}`, `/departments/${departmentId}`], {
        method: 'DELETE',
        token,
    }, [404, 405])
    return true
}

export async function getPrograms(baseUrl, token = null) {
    const payload = await requestWithFallback(baseUrl, ['/api/programs/', '/programs/'], {
        method: 'GET',
        token,
    }, [404, 405])
    return Array.isArray(payload) ? payload.map(normalizeProgram) : []
}

export async function createProgram(baseUrl, token, payload) {
    return normalizeProgram(await requestWithFallback(baseUrl, ['/api/programs/', '/programs/'], {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }, [404, 405]))
}

export async function updateProgram(baseUrl, token, programId, payload) {
    return normalizeProgram(await requestWithFallback(baseUrl, [`/api/programs/${programId}`, `/programs/${programId}`], {
        method: 'PATCH',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }, [404, 405]))
}

export async function deleteProgram(baseUrl, token, programId) {
    await requestWithFallback(baseUrl, [`/api/programs/${programId}`, `/programs/${programId}`], {
        method: 'DELETE',
        token,
    }, [404, 405])
    return true
}

export async function getSchoolSettings(baseUrl, token) {
    return normalizeSchoolSettings(await requestWithFallback(baseUrl, ['/api/school/me', '/api/school-settings/me', '/school-settings/me'], {
        method: 'GET',
        token,
    }, [404, 405]))
}

export async function updateSchoolSettings(baseUrl, token, payload) {
    return normalizeSchoolSettings(await requestWithFallback(baseUrl, ['/api/school-settings/me', '/school-settings/me'], {
        method: 'PUT',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }, [404, 405]))
}

export async function updateSchoolBranding(baseUrl, token, payload = {}, logoFile = null) {
    const formData = new FormData()

    if (payload.school_name !== undefined) {
        formData.append('school_name', String(payload.school_name ?? ''))
    }
    if (payload.primary_color !== undefined) {
        formData.append('primary_color', String(payload.primary_color ?? ''))
    }
    if (payload.secondary_color !== undefined) {
        formData.append('secondary_color', String(payload.secondary_color ?? ''))
    }
    if (payload.school_code !== undefined) {
        formData.append('school_code', String(payload.school_code ?? ''))
    }
    if (payload.event_default_early_check_in_minutes !== undefined) {
        formData.append('event_default_early_check_in_minutes', String(payload.event_default_early_check_in_minutes))
    }
    if (payload.event_default_late_threshold_minutes !== undefined) {
        formData.append('event_default_late_threshold_minutes', String(payload.event_default_late_threshold_minutes))
    }
    if (payload.event_default_sign_out_grace_minutes !== undefined) {
        formData.append('event_default_sign_out_grace_minutes', String(payload.event_default_sign_out_grace_minutes))
    }
    if (logoFile) {
        formData.append('logo', logoFile)
    }

    return normalizeSchoolSettings(await request(baseUrl, '/api/school/update', {
        method: 'PUT',
        token,
        body: formData,
    }))
}

export async function getEvents(baseUrl, token, params = {}) {
    const payload = await requestWithFallback(baseUrl, ['/api/events/', '/events/'], {
        method: 'GET',
        token,
        params,
    }, [404, 405])
    return Array.isArray(payload) ? payload.map(normalizeEvent) : []
}

export async function getEventById(baseUrl, token, eventId) {
    return normalizeEvent(await requestWithFallback(baseUrl, [`/api/events/${eventId}`, `/events/${eventId}`], {
        method: 'GET',
        token,
    }, [404, 405]))
}

export async function getUsers(baseUrl, token, params = {}) {
    const payload = await requestWithFallback(baseUrl, ['/api/users/', '/users/'], {
        method: 'GET',
        token,
        params,
    }, [404, 405])
    return Array.isArray(payload) ? payload.map(normalizeUserWithRelations) : []
}

async function getGovernanceAccess(baseUrl, token) {
    return request(baseUrl, '/api/governance/access/me', {
        method: 'GET',
        token,
    })
}

async function getGovernanceUnitDetail(baseUrl, token, governanceUnitId) {
    return normalizeGovernanceUnitDetail(await request(baseUrl, `/api/governance/units/${governanceUnitId}`, {
        method: 'GET',
        token,
    }))
}

async function getGovernanceUnits(baseUrl, token) {
    const payload = await request(baseUrl, '/api/governance/units', {
        method: 'GET',
        token,
    })

    return Array.isArray(payload) ? payload.map(normalizeGovernanceUnitDetail) : []
}

function hasResolvedSsgUnit(setup = null) {
    return Number.isFinite(Number(setup?.unit?.id))
}

function pickSsgUnitFromGovernanceAccess(payload = null) {
    const units = Array.isArray(payload?.units) ? payload.units : []
    return units.find((unit) => String(unit?.unit_type || '').toUpperCase() === 'SSG') || null
}

function pickSsgUnitFromGovernanceUnits(units = [], schoolId = null) {
    const normalizedSchoolId = Number.isFinite(Number(schoolId)) ? Number(schoolId) : null
    const ssgUnits = (Array.isArray(units) ? units : [])
        .filter((unit) => String(unit?.unit_type || '').toUpperCase() === 'SSG')
        .filter((unit) => unit?.is_active !== false)
        .filter((unit) => (
            normalizedSchoolId == null
                ? true
                : Number(unit?.school_id) === normalizedSchoolId
        ))

    if (ssgUnits.length === 1) return ssgUnits[0]
    return null
}

export async function getCampusSsgSetup(baseUrl, token) {
    let primaryError = null

    try {
        const setup = normalizeGovernanceSsgSetup(await request(baseUrl, '/api/governance/ssg/setup', {
            method: 'GET',
            token,
        }))
        if (hasResolvedSsgUnit(setup)) {
            return setup
        }

        primaryError = new BackendApiError('Student Council setup returned an incomplete payload.', {
            details: setup,
        })
    } catch (error) {
        if (!(error instanceof BackendApiError)) {
            throw error
        }

        if (error.status === 403) {
            throw error
        }

        primaryError = error
    }

    let accessPayload = null
    try {
        accessPayload = await getGovernanceAccess(baseUrl, token)
        const accessUnit = pickSsgUnitFromGovernanceAccess(accessPayload)
        if (accessUnit?.governance_unit_id != null) {
            const detail = await getGovernanceUnitDetail(baseUrl, token, Number(accessUnit.governance_unit_id))
            const setup = normalizeGovernanceSsgSetup({
                unit: detail,
                total_imported_students: 0,
            })
            if (hasResolvedSsgUnit(setup)) {
                return setup
            }
        }
    } catch (error) {
        if (error instanceof BackendApiError && error.status === 403) {
            throw error
        }
    }

    try {
        const governanceUnits = await getGovernanceUnits(baseUrl, token)
        const fallbackUnit = pickSsgUnitFromGovernanceUnits(governanceUnits, accessPayload?.school_id)
        if (!fallbackUnit?.id) {
            if (primaryError?.status === 404) {
                return null
            }
            throw primaryError || new BackendApiError('Student Council setup could not be resolved from the backend.')
        }

        const detail = await getGovernanceUnitDetail(baseUrl, token, Number(fallbackUnit.id))
        const setup = normalizeGovernanceSsgSetup({
            unit: detail,
            total_imported_students: 0,
        })
        if (hasResolvedSsgUnit(setup)) {
            return setup
        }

        throw primaryError || new BackendApiError('Student Council setup could not be resolved from the backend.')
    } catch (error) {
        if (error instanceof BackendApiError && error.status === 403) {
            throw error
        }

        if (primaryError?.status === 404) {
            return null
        }

        throw primaryError || error
    }
}

export async function createGovernanceUnit(baseUrl, token, payload) {
    return normalizeGovernanceUnitDetail(await request(baseUrl, '/api/governance/units', {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }))
}

export async function updateGovernanceUnit(baseUrl, token, governanceUnitId, payload) {
    return normalizeGovernanceUnitDetail(await request(baseUrl, `/api/governance/units/${governanceUnitId}`, {
        method: 'PATCH',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }))
}

export async function deleteGovernanceUnit(baseUrl, token, governanceUnitId) {
    await request(baseUrl, `/api/governance/units/${governanceUnitId}`, {
        method: 'DELETE',
        token,
    })
    return true
}

export async function searchGovernanceStudentCandidates(baseUrl, token, params = {}) {
    const payload = await request(baseUrl, '/api/governance/students/search', {
        method: 'GET',
        token,
        params,
    })
    return Array.isArray(payload) ? payload.map(normalizeGovernanceStudentCandidate) : []
}

export async function assignGovernanceMember(baseUrl, token, governanceUnitId, payload) {
    return normalizeGovernanceMember(await request(baseUrl, `/api/governance/units/${governanceUnitId}/members`, {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }))
}

export async function updateGovernanceMember(baseUrl, token, governanceMemberId, payload) {
    return normalizeGovernanceMember(await request(baseUrl, `/api/governance/members/${governanceMemberId}`, {
        method: 'PATCH',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }))
}

export async function deleteGovernanceMember(baseUrl, token, governanceMemberId) {
    await request(baseUrl, `/api/governance/members/${governanceMemberId}`, {
        method: 'DELETE',
        token,
    })
    return true
}

export async function createSchoolWithSchoolIt(baseUrl, token, payload) {
    const formData = new FormData()

    appendFormValue(formData, 'school_name', payload.school_name)
    appendFormValue(formData, 'primary_color', payload.primary_color)
    appendFormValue(formData, 'secondary_color', payload.secondary_color)
    appendFormValue(formData, 'school_code', payload.school_code)
    appendFormValue(formData, 'school_it_email', payload.school_it_email)
    appendFormValue(formData, 'school_it_first_name', payload.school_it_first_name)
    appendFormValue(formData, 'school_it_middle_name', payload.school_it_middle_name)
    appendFormValue(formData, 'school_it_last_name', payload.school_it_last_name)
    appendFormValue(formData, 'school_it_password', payload.school_it_password)

    if (payload.logo) {
        formData.append('logo', payload.logo, payload.logo_name || 'logo.png')
    }

    return normalizeCreateSchoolWithSchoolItResponse(await request(baseUrl, '/api/school/admin/create-school-it', {
        method: 'POST',
        token,
        body: formData,
    }))
}

export async function createUser(baseUrl, token, payload) {
    return normalizeUserWithRelations(await requestWithFallback(baseUrl, ['/api/users/', '/users/'], {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }, [404, 405]))
}

export async function createStudentProfile(baseUrl, token, payload) {
    return normalizeUserWithRelations(await requestWithFallback(baseUrl, ['/api/users/admin/students/', '/users/admin/students/'], {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }, [404, 405]))
}

export async function previewImportStudents(baseUrl, token, file) {
    const formData = new FormData()
    formData.append('file', file)

    return normalizeImportPreviewSummary(await request(baseUrl, '/api/admin/import-students/preview', {
        method: 'POST',
        token,
        body: formData,
    }))
}

export async function startStudentImport(baseUrl, token, file) {
    const formData = new FormData()
    formData.append('file', file)

    return normalizeImportJobCreateResponse(await request(baseUrl, '/api/admin/import-students', {
        method: 'POST',
        token,
        body: formData,
    }))
}

export async function getStudentImportStatus(baseUrl, token, jobId) {
    return normalizeImportJobStatus(await request(baseUrl, `/api/admin/import-status/${jobId}`, {
        method: 'GET',
        token,
    }))
}

export async function getCurrentUserProfile(baseUrl, token) {
    const payload = await requestWithFallback(baseUrl, ['/api/users/me/', '/users/me/'], {
        method: 'GET',
        token,
    }, [404, 405])
    const normalized = normalizeUserWithRelations(payload)
    if (!normalized) {
        throw new BackendApiError('The API returned an invalid current-user profile response.', {
            details: payload,
        })
    }
    return normalized
}

export async function getUserById(baseUrl, token, userId) {
    return normalizeUserWithRelations(await requestWithFallback(baseUrl, [`/api/users/${userId}`, `/users/${userId}`], {
        method: 'GET',
        token,
    }, [404, 405]))
}

export async function updateUser(baseUrl, token, userId, payload) {
    return normalizeUserWithRelations(await requestWithFallback(baseUrl, [`/api/users/${userId}`, `/users/${userId}`], {
        method: 'PATCH',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }, [404, 405]))
}

export async function updateStudentProfile(baseUrl, token, profileId, payload) {
    return normalizeUserWithRelations(await requestWithFallback(baseUrl, [`/api/users/student-profiles/${profileId}`, `/users/student-profiles/${profileId}`], {
        method: 'PATCH',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }, [404, 405]))
}

export async function resetUserPassword(baseUrl, token, userId, password) {
    return normalizePasswordResetResponse(await request(baseUrl, `/users/${userId}/reset-password`, {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            password,
        }),
    }))
}

export async function changePassword(baseUrl, token, payload, endpoint = '/auth/change-password') {
    return normalizePasswordChangeResponse(await request(baseUrl, endpoint, {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }))
}

export async function getMyAttendance(baseUrl, token, params = {}) {
    const payload = await request(baseUrl, '/attendance/students/me', {
        method: 'GET',
        token,
        params,
    })
    return Array.isArray(payload) ? payload.map(normalizeAttendanceRecord) : []
}

export async function getAttendanceSummary(baseUrl, token, params = {}) {
    return request(baseUrl, '/attendance/summary', {
        method: 'GET',
        token,
        params,
    })
}

export async function getFaceStatus(baseUrl, token) {
    return normalizeFaceStatus(await requestWithFallback(baseUrl, ['/api/auth/security/face-status', '/auth/security/face-status'], {
        method: 'GET',
        token,
    }, [404, 405]))
}

export async function saveFaceReference(baseUrl, token, imageBase64) {
    return normalizeFaceReferenceResponse(await requestWithFallback(baseUrl, ['/api/auth/security/face-reference', '/auth/security/face-reference'], {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            image_base64: imageBase64,
        }),
    }, [404, 405]))
}

export async function registerStudentFace(baseUrl, token, imageBase64) {
    return normalizeStudentFaceRegistrationResponse(await request(baseUrl, '/face/register', {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            image_base64: imageBase64,
        }),
    }))
}

export async function verifyFaceReference(baseUrl, token, payload) {
    return normalizeFaceVerificationResponse(await requestWithFallback(baseUrl, ['/api/auth/security/face-verify', '/auth/security/face-verify'], {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }, [404, 405]))
}

export async function recordFaceScanAttendance(baseUrl, token, {
    eventId,
    studentId,
    imageBase64,
    latitude = null,
    longitude = null,
    accuracyM = null,
    threshold = null,
}) {
    const payload = await request(baseUrl, '/face/face-scan-with-recognition', {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            event_id: eventId,
            image_base64: imageBase64,
            latitude,
            longitude,
            accuracy_m: accuracyM,
            threshold,
        }),
    })
    return { ok: payload?.ok !== false, ...payload }
}

export async function recordFaceScanTimeout(baseUrl, token, { eventId, studentId }) {
    const payload = await request(baseUrl, '/attendance/face-scan-timeout', {
        method: 'POST',
        token,
        params: {
            event_id: eventId,
            student_id: studentId,
        },
    })
    return { ok: payload?.ok !== false, ...payload }
}

export async function verifyEventLocation(baseUrl, token, eventId, payload) {
    return normalizeEventLocationResponse(await request(baseUrl, `/events/${eventId}/verify-location`, {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }))
}

export async function getEventTimeStatus(baseUrl, token, eventId) {
    return normalizeEventTimeStatus(await request(baseUrl, `/events/${eventId}/time-status`, {
        method: 'GET',
        token,
    }))
}

function appendFormValue(formData, key, value) {
    if (value == null || value === '') return
    formData.append(key, String(value))
}
