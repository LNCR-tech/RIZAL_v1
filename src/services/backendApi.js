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
    normalizePasswordChangeResponse,
    normalizePasswordResetResponse,
    normalizeProgram,
    normalizeSchoolSettings,
    normalizeStudentFaceRegistrationResponse,
    normalizeTokenPayload,
    normalizeUserWithRelations,
} from '@/services/backendNormalizers.js'

export class BackendApiError extends Error {
    constructor(message, { status = 0, details = null } = {}) {
        super(message)
        this.name = 'BackendApiError'
        this.status = status
        this.details = details
    }
}

export { resolveApiBaseUrl }

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

    return payload
}

async function request(baseUrl, path, options = {}) {
    const {
        token,
        params,
        headers = {},
        body,
        ...rest
    } = options

    let response
    try {
        response = await fetch(buildUrl(baseUrl, path, params), {
            ...rest,
            headers: {
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
                ...(isNgrokApiBaseUrl(baseUrl) ? { 'ngrok-skip-browser-warning': 'true' } : {}),
                ...headers,
            },
            body,
        })
    } catch (error) {
        throw new BackendApiError(
            'Unable to reach the API. The server may be unavailable or the request may be blocked.',
            {
                details: {
                    cause: error?.message || null,
                    path,
                },
            }
        )
    }

    return parseResponse(response)
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
                fallbackStatuses.includes(Number(error.status))

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

    return normalizeTokenPayload(await request(baseUrl, '/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body,
    }))
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

export async function getDepartments(baseUrl) {
    const payload = await request(baseUrl, '/departments/', { method: 'GET' })
    return Array.isArray(payload) ? payload.map(normalizeDepartment) : []
}

export async function getPrograms(baseUrl) {
    const payload = await request(baseUrl, '/programs/', { method: 'GET' })
    return Array.isArray(payload) ? payload.map(normalizeProgram) : []
}

export async function getSchoolSettings(baseUrl, token) {
    return normalizeSchoolSettings(await requestWithFallback(baseUrl, ['/api/school/me', '/school-settings/me'], {
        method: 'GET',
        token,
    }))
}

export async function updateSchoolSettings(baseUrl, token, payload) {
    return normalizeSchoolSettings(await request(baseUrl, '/school-settings/me', {
        method: 'PUT',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }))
}

export async function getEvents(baseUrl, token, params = {}) {
    const payload = await request(baseUrl, '/events/', {
        method: 'GET',
        token,
        params,
    })
    return Array.isArray(payload) ? payload.map(normalizeEvent) : []
}

export async function getEventById(baseUrl, token, eventId) {
    return normalizeEvent(await request(baseUrl, `/events/${eventId}`, {
        method: 'GET',
        token,
    }))
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
    return normalizeUserWithRelations(await request(baseUrl, '/users/', {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }))
}

export async function createStudentProfile(baseUrl, token, payload) {
    return normalizeUserWithRelations(await request(baseUrl, '/users/admin/students/', {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }))
}

export async function getCurrentUserProfile(baseUrl, token) {
    return normalizeUserWithRelations(await request(baseUrl, '/users/me/', {
        method: 'GET',
        token,
    }))
}

export async function getUserById(baseUrl, token, userId) {
    return normalizeUserWithRelations(await request(baseUrl, `/users/${userId}`, {
        method: 'GET',
        token,
    }))
}

export async function updateUser(baseUrl, token, userId, payload) {
    return normalizeUserWithRelations(await request(baseUrl, `/users/${userId}`, {
        method: 'PATCH',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }))
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

export async function getFaceStatus(baseUrl, token) {
    return normalizeFaceStatus(await request(baseUrl, '/auth/security/face-status', {
        method: 'GET',
        token,
    }))
}

export async function saveFaceReference(baseUrl, token, imageBase64) {
    return normalizeFaceReferenceResponse(await request(baseUrl, '/auth/security/face-reference', {
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
    return normalizeFaceVerificationResponse(await request(baseUrl, '/auth/security/face-verify', {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    }))
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
