import jrmsuLogoUrl from '@/data/jrmsu_icon.png'

const STORAGE_KEY = 'aura.mockBackendState'
const LEGACY_LOGO_PATHS = new Set([
    'src/data/jrmsu_icon.png',
    '/src/data/jrmsu_icon.png',
])

export const MOCK_LOGIN_CREDENTIALS = {
    student: {
        email: 'student@mock.local',
        password: 'StudentPass123!',
    },
    schoolIt: {
        email: 'schoolit@mock.local',
        password: 'SchoolIT123!',
    },
    admin: {
        email: 'admin@mock.local',
        password: 'AdminPass123!',
    },
}

const ROLE_IDS = {
    student: 1,
    school_IT: 2,
    admin: 3,
}

function clone(value) {
    return JSON.parse(JSON.stringify(value))
}

function nowIso() {
    return new Date().toISOString()
}

function hoursFromNow(hours) {
    return new Date(Date.now() + hours * 60 * 60 * 1000).toISOString()
}

function resolveMockLogoUrl(logoUrl) {
    const normalized = String(logoUrl || '').trim()
    if (!normalized) return jrmsuLogoUrl
    return LEGACY_LOGO_PATHS.has(normalized) ? jrmsuLogoUrl : normalized
}

function createInitialState() {
    return {
        nextIds: {
            school: 9,
            user: 401,
            studentProfile: 701,
            event: 1005,
            attendance: 5003,
        },
        schools: [
            {
                id: 8,
                school_name: 'JRMSU Test School',
                school_code: 'JRMSU',
                logo_url: jrmsuLogoUrl,
                primary_color: '#0057B8',
                secondary_color: '#FFD400',
                accent_color: '#000000',
                active_status: true,
            },
        ],
        departments: [
            { id: 1, name: 'College of Computing' },
            { id: 2, name: 'College of Business' },
            { id: 3, name: 'College of Engineering' },
        ],
        programs: [
            { id: 1, name: 'BS Computer Science', department_ids: [1] },
            { id: 2, name: 'BS Information Technology', department_ids: [1] },
            { id: 3, name: 'BS Accountancy', department_ids: [2] },
            { id: 4, name: 'BS Civil Engineering', department_ids: [3] },
        ],
        users: [
            {
                id: 101,
                email: MOCK_LOGIN_CREDENTIALS.student.email,
                password: MOCK_LOGIN_CREDENTIALS.student.password,
                school_id: 8,
                created_at: nowIso(),
                first_name: 'Mia',
                middle_name: 'L',
                last_name: 'Santos',
                is_active: true,
                must_change_password: false,
                roles: ['student'],
                avatar_url: null,
                face_reference_enrolled: true,
                student_profile: {
                    id: 701,
                    user_id: 101,
                    school_id: 8,
                    student_id: 'CS-2026-001',
                    department_id: 1,
                    program_id: 1,
                    year_level: 2,
                    is_face_registered: false,
                    registration_complete: false,
                    photo_url: null,
                    avatar_url: null,
                },
            },
            {
                id: 201,
                email: MOCK_LOGIN_CREDENTIALS.schoolIt.email,
                password: MOCK_LOGIN_CREDENTIALS.schoolIt.password,
                school_id: 8,
                created_at: nowIso(),
                first_name: 'School',
                middle_name: '',
                last_name: 'IT',
                is_active: true,
                must_change_password: false,
                roles: ['school_IT'],
                avatar_url: null,
                face_reference_enrolled: true,
                student_profile: null,
            },
            {
                id: 1,
                email: MOCK_LOGIN_CREDENTIALS.admin.email,
                password: MOCK_LOGIN_CREDENTIALS.admin.password,
                school_id: null,
                created_at: nowIso(),
                first_name: 'System',
                middle_name: '',
                last_name: 'Administrator',
                is_active: true,
                must_change_password: false,
                roles: ['admin'],
                avatar_url: null,
                face_reference_enrolled: true,
                student_profile: null,
            },
        ],
        events: [
            {
                id: 1001,
                school_id: 8,
                name: 'Campus Innovation Fair',
                location: 'Main Auditorium',
                start_datetime: hoursFromNow(-2),
                end_datetime: hoursFromNow(2),
                status: 'ongoing',
                geo_required: true,
                geo_latitude: 8.150921,
                geo_longitude: 123.842741,
                geo_radius_m: 250,
            },
            {
                id: 1002,
                school_id: 8,
                name: 'Student Leadership Summit',
                location: 'Conference Hall',
                start_datetime: hoursFromNow(26),
                end_datetime: hoursFromNow(30),
                status: 'upcoming',
                geo_required: true,
                geo_latitude: 8.15132,
                geo_longitude: 123.84351,
                geo_radius_m: 300,
            },
            {
                id: 1003,
                school_id: 8,
                name: 'Career Prep Workshop',
                location: 'Engineering Building',
                start_datetime: hoursFromNow(72),
                end_datetime: hoursFromNow(75),
                status: 'upcoming',
                geo_required: false,
                geo_latitude: 8.14982,
                geo_longitude: 123.84173,
                geo_radius_m: 250,
            },
            {
                id: 1004,
                school_id: 8,
                name: 'Welcome Assembly',
                location: 'Gymnasium',
                start_datetime: hoursFromNow(-72),
                end_datetime: hoursFromNow(-69),
                status: 'completed',
                geo_required: false,
                geo_latitude: 8.15048,
                geo_longitude: 123.8441,
                geo_radius_m: 250,
            },
        ],
        attendance: [
            {
                id: 5001,
                event_id: 1004,
                student_id: 'CS-2026-001',
                method: 'face_scan',
                status: 'present',
                time_in: hoursFromNow(-71.5),
            },
            {
                id: 5002,
                event_id: 9999,
                student_id: 'CS-2026-001',
                method: 'manual',
                status: 'absent',
                time_in: null,
            },
        ],
        sessions: {},
    }
}

function loadState() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (!raw) {
            const initial = createInitialState()
            saveState(initial)
            return initial
        }
        const parsed = JSON.parse(raw)
        const migrated = migrateState(parsed)
        if (migrated !== parsed) {
            saveState(migrated)
        }
        return migrated
    } catch {
        const initial = createInitialState()
        saveState(initial)
        return initial
    }
}

function migrateState(state) {
    if (!state || typeof state !== 'object') {
        return createInitialState()
    }

    let mutated = false
    const nextState = { ...state }

    if (Array.isArray(state.schools)) {
        nextState.schools = state.schools.map((school) => {
            const nextLogoUrl = resolveMockLogoUrl(school?.logo_url)
            if (nextLogoUrl === school?.logo_url) {
                return school
            }
            mutated = true
            return {
                ...school,
                logo_url: nextLogoUrl,
            }
        })
    }

    return mutated ? nextState : state
}

function saveState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

function normalizeRoleName(roleName) {
    return String(roleName || '').trim().toLowerCase().replace(/_/g, '-')
}

function findUserByEmail(state, email) {
    const normalizedEmail = String(email || '').trim().toLowerCase()
    return state.users.find((user) => String(user.email).trim().toLowerCase() === normalizedEmail) || null
}

function getUserByToken(state, token) {
    const session = state.sessions?.[token]
    if (!session) {
        throw new Error('Session is not valid')
    }

    const user = state.users.find((entry) => entry.id === session.user_id)
    if (!user) {
        throw new Error('User not found for session')
    }
    return user
}

function schoolSettingsForUser(state, user) {
    if (!user?.school_id) return null
    const school = state.schools.find((entry) => entry.id === user.school_id)
    if (!school) return null

    return {
        school_id: school.id,
        school_name: school.school_name,
        school_code: school.school_code,
        logo_url: school.logo_url,
        primary_color: school.primary_color,
        secondary_color: school.secondary_color,
        accent_color: school.accent_color,
        subscription_status: 'trial',
        active_status: school.active_status,
    }
}

function buildRoles(roleNames = []) {
    return roleNames.map((name) => ({
        id: ROLE_IDS[name] || ROLE_IDS[normalizeRoleName(name)] || Date.now(),
        role: {
            id: ROLE_IDS[name] || ROLE_IDS[normalizeRoleName(name)] || Date.now(),
            name,
        },
    }))
}

function buildUserPayload(state, user) {
    const base = {
        id: user.id,
        email: user.email,
        school_id: user.school_id,
        created_at: user.created_at || nowIso(),
        first_name: user.first_name,
        middle_name: user.middle_name || null,
        last_name: user.last_name,
        is_active: Boolean(user.is_active),
        must_change_password: Boolean(user.must_change_password),
        roles: buildRoles(user.roles),
        avatar_url: user.avatar_url || null,
    }

    if (user.student_profile) {
        base.student_profile = clone(user.student_profile)
    }

    const schoolSettings = schoolSettingsForUser(state, user)
    if (schoolSettings) {
        base.school_name = schoolSettings.school_name
        base.school_code = schoolSettings.school_code
    }

    return base
}

function buildTokenPayload(state, user, token) {
    const schoolSettings = schoolSettingsForUser(state, user)

    return {
        access_token: token,
        token_type: 'bearer',
        email: user.email,
        roles: [...user.roles],
        user_id: user.id,
        first_name: user.first_name,
        last_name: user.last_name,
        school_id: user.school_id ?? null,
        school_name: schoolSettings?.school_name ?? null,
        school_code: schoolSettings?.school_code ?? null,
        logo_url: schoolSettings?.logo_url ?? null,
        primary_color: schoolSettings?.primary_color ?? null,
        secondary_color: schoolSettings?.secondary_color ?? null,
        accent_color: schoolSettings?.accent_color ?? null,
        must_change_password: Boolean(user.must_change_password),
        session_id: token,
        face_verification_required: false,
        face_reference_enrolled: Boolean(user.face_reference_enrolled || user.student_profile?.is_face_registered),
        face_verification_pending: false,
        change_password_endpoint: '/auth/change-password',
    }
}

function createSession(state, user) {
    const token = `mock-token-${user.id}-${Date.now()}`
    state.sessions[token] = {
        user_id: user.id,
        created_at: nowIso(),
    }
    saveState(state)
    return token
}

function requireRole(user, allowedRoles, message) {
    const userRoles = new Set((user.roles || []).map(normalizeRoleName))
    const permitted = allowedRoles.some((role) => userRoles.has(normalizeRoleName(role)))
    if (!permitted) {
        throw new Error(message || 'Insufficient permissions.')
    }
}

export function isMockApiEnabled() {
    return true
}

export async function loginForAccessToken(baseUrl, { username, password }) {
    const state = loadState()
    const user = findUserByEmail(state, username)
    if (!user || user.password !== String(password ?? '')) {
        throw new Error('Incorrect email or password')
    }

    const token = createSession(state, user)
    return buildTokenPayload(state, user, token)
}

export async function getDepartments() {
    return clone(loadState().departments)
}

export async function getPrograms() {
    return clone(loadState().programs)
}

export async function getSchoolSettings(baseUrl, token) {
    const state = loadState()
    const user = getUserByToken(state, token)
    const settings = schoolSettingsForUser(state, user)
    if (!settings) {
        throw new Error('User is not assigned to a school')
    }
    return clone(settings)
}

export async function updateSchoolSettings(baseUrl, token, payload) {
    const state = loadState()
    const user = getUserByToken(state, token)
    requireRole(user, ['admin', 'school_IT'], 'Only admin or School IT can update school settings.')

    const schoolId = user.school_id || payload?.school_id
    const school = state.schools.find((entry) => entry.id === schoolId)
    if (!school) throw new Error('School not found')

    school.school_name = payload.school_name || school.school_name
    school.logo_url = payload.logo_url ?? school.logo_url
    school.primary_color = payload.primary_color || school.primary_color
    school.secondary_color = payload.secondary_color || school.secondary_color
    school.accent_color = payload.accent_color || school.accent_color
    saveState(state)

    return schoolSettingsForUser(state, { school_id: school.id })
}

export async function getEvents(baseUrl, token, params = {}) {
    const state = loadState()
    const user = getUserByToken(state, token)
    const schoolId = user.school_id

    let events = state.events.filter((event) => schoolId == null || event.school_id === schoolId)
    if (params?.limit) {
        events = events.slice(0, Number(params.limit))
    }

    return clone(events)
}

export async function getEventById(baseUrl, token, eventId) {
    const state = loadState()
    getUserByToken(state, token)
    const event = state.events.find((entry) => Number(entry.id) === Number(eventId))
    if (!event) throw new Error('Event not found')
    return clone(event)
}

export async function createSchoolWithSchoolIt(baseUrl, token, payload) {
    const state = loadState()
    const actor = getUserByToken(state, token)
    requireRole(actor, ['admin'], 'Admin privileges required.')

    const schoolId = state.nextIds.school++
    const userId = state.nextIds.user++

    const school = {
        id: schoolId,
        school_name: payload.school_name,
        school_code: payload.school_code || `SCH-${schoolId}`,
        logo_url: null,
        primary_color: payload.primary_color || '#0057B8',
        secondary_color: payload.secondary_color || '#FFD400',
        accent_color: '#000000',
        active_status: true,
    }
    state.schools.push(school)

    state.users.push({
        id: userId,
        email: String(payload.school_it_email || '').trim().toLowerCase(),
        password: String(payload.school_it_password || 'SchoolIT123!'),
        school_id: schoolId,
        created_at: nowIso(),
        first_name: payload.school_it_first_name || 'School',
        middle_name: payload.school_it_middle_name || '',
        last_name: payload.school_it_last_name || 'IT',
        is_active: true,
        must_change_password: false,
        roles: ['school_IT'],
        avatar_url: null,
        face_reference_enrolled: true,
        student_profile: null,
    })

    saveState(state)

    return {
        school: schoolSettingsForUser(state, { school_id: school.id }),
        school_it_email: payload.school_it_email,
        school_it_user_id: userId,
        generated_temporary_password: payload.school_it_password || 'SchoolIT123!',
    }
}

export async function createUser(baseUrl, token, payload) {
    const state = loadState()
    const actor = getUserByToken(state, token)
    requireRole(actor, ['school_IT', 'admin'], 'Admin or School IT privileges required.')

    if (actor.school_id == null) {
        throw new Error('Platform admin cannot create school-scoped users via /users. Use school admin flows instead.')
    }

    if (findUserByEmail(state, payload.email)) {
        throw new Error('Email already registered in this school')
    }

    const user = {
        id: state.nextIds.user++,
        email: String(payload.email || '').trim().toLowerCase(),
        password: String(payload.password || 'StudentPass123!'),
        school_id: actor.school_id,
        created_at: nowIso(),
        first_name: payload.first_name || 'Student',
        middle_name: payload.middle_name || '',
        last_name: payload.last_name || 'User',
        is_active: true,
        must_change_password: false,
        roles: Array.isArray(payload.roles) ? payload.roles : ['student'],
        avatar_url: null,
        face_reference_enrolled: false,
        student_profile: null,
    }

    state.users.push(user)
    saveState(state)
    return buildUserPayload(state, user)
}

export async function createStudentProfile(baseUrl, token, payload) {
    const state = loadState()
    const actor = getUserByToken(state, token)
    requireRole(actor, ['school_IT', 'admin'], 'Admin or School IT privileges required.')

    const targetUser = state.users.find((entry) => entry.id === Number(payload.user_id))
    if (!targetUser) throw new Error('Target user not found')
    if (actor.school_id != null && targetUser.school_id !== actor.school_id) {
        throw new Error('Target user not found')
    }

    targetUser.student_profile = {
        id: state.nextIds.studentProfile++,
        user_id: targetUser.id,
        school_id: targetUser.school_id,
        student_id: payload.student_id || `STU-${targetUser.id}`,
        department_id: payload.department_id ?? null,
        program_id: payload.program_id ?? null,
        year_level: payload.year_level ?? 1,
        is_face_registered: false,
        registration_complete: false,
        photo_url: null,
        avatar_url: null,
    }

    saveState(state)
    return buildUserPayload(state, targetUser)
}

export async function getCurrentUserProfile(baseUrl, token) {
    const state = loadState()
    return buildUserPayload(state, getUserByToken(state, token))
}

export async function getUserById(baseUrl, token, userId) {
    const state = loadState()
    const actor = getUserByToken(state, token)
    const user = state.users.find((entry) => entry.id === Number(userId))
    if (!user) throw new Error('User not found')
    if (actor.school_id != null && user.school_id !== actor.school_id) {
        throw new Error('User not found')
    }
    return buildUserPayload(state, user)
}

export async function updateUser(baseUrl, token, userId, payload) {
    const state = loadState()
    const actor = getUserByToken(state, token)
    const user = state.users.find((entry) => entry.id === Number(userId))
    if (!user) throw new Error('User not found')
    if (actor.school_id != null && user.school_id !== actor.school_id && actor.id !== user.id) {
        throw new Error('User not found')
    }

    user.email = payload.email != null ? String(payload.email).trim().toLowerCase() : user.email
    user.first_name = payload.first_name ?? user.first_name
    user.middle_name = payload.middle_name ?? user.middle_name
    user.last_name = payload.last_name ?? user.last_name
    saveState(state)

    return buildUserPayload(state, user)
}

export async function resetUserPassword(baseUrl, token, userId, password) {
    const state = loadState()
    const actor = getUserByToken(state, token)
    requireRole(actor, ['school_IT', 'admin'], 'Admin or School IT privileges required.')

    const user = state.users.find((entry) => entry.id === Number(userId))
    if (!user) throw new Error('User not found')

    user.password = String(password || '')
    user.must_change_password = false
    saveState(state)
    return {
        user_id: user.id,
        email: user.email,
        temporary_password: user.password,
        must_change_password: Boolean(user.must_change_password),
    }
}

export async function changePassword(baseUrl, token, payload) {
    const state = loadState()
    const user = getUserByToken(state, token)
    if (user.password !== String(payload.current_password || '')) {
        throw new Error('Current password is incorrect')
    }

    user.password = String(payload.new_password || '')
    user.must_change_password = false
    saveState(state)

    return { message: 'Password updated successfully' }
}

export async function getMyAttendance(baseUrl, token, params = {}) {
    const state = loadState()
    const user = getUserByToken(state, token)
    const studentId = user.student_profile?.student_id
    if (!studentId) return []

    let records = state.attendance.filter((entry) => entry.student_id === studentId)
    if (params?.event_id != null) {
        records = records.filter((entry) => Number(entry.event_id) === Number(params.event_id))
    }
    if (params?.limit) {
        records = records.slice(0, Number(params.limit))
    }
    return clone(records)
}

export async function getFaceStatus(baseUrl, token) {
    const state = loadState()
    const user = getUserByToken(state, token)

    return {
        face_verification_required: false,
        face_reference_enrolled: Boolean(user.face_reference_enrolled || user.student_profile?.is_face_registered),
        provider: 'mock',
        updated_at: nowIso(),
        last_verified_at: nowIso(),
        liveness_enabled: true,
        anti_spoof_ready: true,
        anti_spoof_reason: null,
        live_capture_required: false,
    }
}

export async function saveFaceReference(baseUrl, token) {
    const state = loadState()
    const user = getUserByToken(state, token)
    user.face_reference_enrolled = true
    saveState(state)

    return {
        user_id: user.id,
        face_reference_enrolled: true,
        provider: 'mock',
        updated_at: nowIso(),
        liveness: {
            label: 'Real',
            score: 0.99,
        },
    }
}

export async function registerStudentFace(baseUrl, token) {
    const state = loadState()
    const user = getUserByToken(state, token)
    if (!user.student_profile) {
        throw new Error('Only users with a student profile can register a student face.')
    }

    user.student_profile.is_face_registered = true
    user.student_profile.registration_complete = true
    user.face_reference_enrolled = true
    saveState(state)

    return {
        message: 'Face registered successfully.',
        student_id: user.student_profile.student_id,
    }
}

export async function verifyFaceReference(baseUrl, token) {
    const state = loadState()
    const user = getUserByToken(state, token)
    user.face_reference_enrolled = true
    saveState(state)

    return {
        matched: true,
        distance: 0.21,
        confidence: 0.94,
        threshold: 0.5,
        verified_at: nowIso(),
        access_token: token,
        token_type: 'bearer',
        session_id: token,
        face_verification_pending: false,
    }
}

export async function recordFaceScanAttendance(baseUrl, token, {
    eventId,
    studentId,
}) {
    const state = loadState()
    const user = getUserByToken(state, token)

    const existing = state.attendance.find(
        (entry) => Number(entry.event_id) === Number(eventId) && String(entry.student_id) === String(studentId)
    )

    if (!existing) {
        state.attendance.unshift({
            id: state.nextIds.attendance++,
            event_id: Number(eventId),
            student_id: String(studentId),
            method: 'face_scan',
            status: 'present',
            time_in: nowIso(),
        })
    } else {
        existing.method = existing.method || 'face_scan'
        existing.status = 'present'
        existing.time_in = existing.time_in || nowIso()
    }

    saveState(state)
    return {
        ok: true,
        action: existing?.time_in ? 'timeout' : 'timein',
        student_id: String(studentId),
        student_name: `${user?.first_name ?? 'Mock'} ${user?.last_name ?? 'Student'}`.trim(),
        attendance_id: existing?.id ?? state.nextIds.attendance - 1,
        distance: 0.18,
        confidence: 0.96,
        threshold: 0.5,
        liveness: {
            label: 'real',
            score: 0.99,
        },
        message: 'Attendance recorded successfully.',
    }
}

export async function recordFaceScanTimeout(baseUrl, token, { eventId, studentId }) {
    const state = loadState()
    getUserByToken(state, token)

    const existing = state.attendance.find(
        (entry) => Number(entry.event_id) === Number(eventId) && String(entry.student_id) === String(studentId)
    )

    if (!existing) {
        state.attendance.unshift({
            id: state.nextIds.attendance++,
            event_id: Number(eventId),
            student_id: String(studentId),
            method: 'manual',
            status: 'absent',
            time_in: null,
        })
        saveState(state)
    }

    return { ok: true }
}

export async function verifyEventLocation(baseUrl, token, eventId, payload) {
    const state = loadState()
    getUserByToken(state, token)

    const event = state.events.find((entry) => Number(entry.id) === Number(eventId))
    if (!event) throw new Error('Event not found')

    if (!event.geo_required) {
        return { ok: true, reason: null }
    }

    if (payload?.latitude == null || payload?.longitude == null) {
        return { ok: false, reason: 'Location coordinates are required.' }
    }

    return {
        ok: true,
        reason: null,
        distance_m: 42,
        radius_m: event.geo_radius_m,
    }
}

export async function getEventTimeStatus(baseUrl, token, eventId) {
    const state = loadState()
    getUserByToken(state, token)
    const event = state.events.find((entry) => Number(entry.id) === Number(eventId))
    if (!event) throw new Error('Event not found')

    return {
        event_id: Number(eventId),
        status: event.status,
        current_time: nowIso(),
    }
}

export function resetMockBackendState() {
    const initial = createInitialState()
    saveState(initial)
    return clone(initial)
}
