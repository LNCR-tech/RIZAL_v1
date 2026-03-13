const DEFAULT_API_BASE_URL = 'https://sas-deploy-production.up.railway.app'

export class BackendApiError extends Error {
    constructor(message, { status = 0, details = null } = {}) {
        super(message)
        this.name = 'BackendApiError'
        this.status = status
        this.details = details
    }
}

export function resolveApiBaseUrl(baseUrl = '') {
    const resolved = String(baseUrl || import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).trim()
    return resolved.replace(/\/+$/, '')
}

function buildUrl(baseUrl, path, params) {
    const url = new URL(`${resolveApiBaseUrl(baseUrl)}${path}`)

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

    const response = await fetch(buildUrl(baseUrl, path, params), {
        ...rest,
        headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...headers,
        },
        body,
    })

    return parseResponse(response)
}

export async function loginForAccessToken(baseUrl, { username, password }) {
    const body = new URLSearchParams({
        username: String(username ?? ''),
        password: String(password ?? ''),
    })

    return request(baseUrl, '/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body,
    })
}

export async function getDepartments(baseUrl) {
    return request(baseUrl, '/departments/', { method: 'GET' })
}

export async function getPrograms(baseUrl) {
    return request(baseUrl, '/programs/', { method: 'GET' })
}

export async function getSchoolSettings(baseUrl, token) {
    return request(baseUrl, '/school-settings/me', {
        method: 'GET',
        token,
    })
}

export async function updateSchoolSettings(baseUrl, token, payload) {
    return request(baseUrl, '/school-settings/me', {
        method: 'PUT',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
}

export async function getEvents(baseUrl, token, params = {}) {
    return request(baseUrl, '/events/', {
        method: 'GET',
        token,
        params,
    })
}

export async function getEventById(baseUrl, token, eventId) {
    return request(baseUrl, `/events/${eventId}`, {
        method: 'GET',
        token,
    })
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

    return request(baseUrl, '/api/school/admin/create-school-it', {
        method: 'POST',
        token,
        body: formData,
    })
}

export async function createUser(baseUrl, token, payload) {
    return request(baseUrl, '/users/', {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
}

export async function createStudentProfile(baseUrl, token, payload) {
    return request(baseUrl, '/users/admin/students/', {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
}

export async function getCurrentUserProfile(baseUrl, token) {
    return request(baseUrl, '/users/me/', {
        method: 'GET',
        token,
    })
}

export async function updateUser(baseUrl, token, userId, payload) {
    return request(baseUrl, `/users/${userId}`, {
        method: 'PATCH',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
}

export async function getMyAttendance(baseUrl, token, params = {}) {
    return request(baseUrl, '/attendance/students/me', {
        method: 'GET',
        token,
        params,
    })
}

export async function getFaceStatus(baseUrl, token) {
    return request(baseUrl, '/auth/security/face-status', {
        method: 'GET',
        token,
    })
}

export async function saveFaceReference(baseUrl, token, imageBase64) {
    return request(baseUrl, '/auth/security/face-reference', {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            image_base64: imageBase64,
        }),
    })
}

export async function recordFaceScanAttendance(baseUrl, token, { eventId, studentId }) {
    return request(baseUrl, '/attendance/face-scan', {
        method: 'POST',
        token,
        params: {
            event_id: eventId,
            student_id: studentId,
        },
    })
}

export async function recordFaceScanTimeout(baseUrl, token, { eventId, studentId }) {
    return request(baseUrl, '/attendance/face-scan-timeout', {
        method: 'POST',
        token,
        params: {
            event_id: eventId,
            student_id: studentId,
        },
    })
}

export async function verifyEventLocation(baseUrl, token, eventId, payload) {
    return request(baseUrl, `/events/${eventId}/verify-location`, {
        method: 'POST',
        token,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
}

export async function getEventTimeStatus(baseUrl, token, eventId) {
    return request(baseUrl, `/events/${eventId}/time-status`, {
        method: 'GET',
        token,
    })
}

function appendFormValue(formData, key, value) {
    if (value == null || value === '') return
    formData.append(key, String(value))
}
