import { computed, reactive, readonly } from 'vue'
import { applyTheme, loadTheme } from '@/config/theme.js'
import {
    getFaceStatus,
    getCurrentUserProfile,
    getEventById,
    getEvents,
    getMyAttendance,
    getSchoolSettings,
    resolveApiBaseUrl,
    updateUser,
} from '@/services/backendApi.js'

const state = reactive({
    apiBaseUrl: resolveApiBaseUrl(),
    token: localStorage.getItem('aura_token') || '',
    user: null,
    schoolSettings: null,
    events: [],
    attendanceRecords: [],
    faceStatus: null,
    initialized: false,
    loading: false,
    error: '',
})

let initPromise = null

function normalizeEvent(event) {
    if (!event) return null

    const status = event.status === 'done' ? 'completed' : event.status
    return {
        ...event,
        status,
    }
}

function sortEvents(events) {
    const statusRank = {
        ongoing: 0,
        upcoming: 1,
        completed: 2,
        cancelled: 3,
    }

    return [...events].sort((a, b) => {
        const aRank = statusRank[a?.status] ?? 99
        const bRank = statusRank[b?.status] ?? 99
        if (aRank !== bRank) return aRank - bRank
        return new Date(a?.start_datetime ?? 0) - new Date(b?.start_datetime ?? 0)
    })
}

function syncUserAttendanceRecords() {
    if (!state.user?.student_profile) return

    state.user = {
        ...state.user,
        student_profile: {
            ...state.user.student_profile,
            attendances: [...state.attendanceRecords],
        },
    }
}

function syncUserFaceState() {
    if (!state.user?.student_profile) return

    const isFaceRegistered = Boolean(
        state.faceStatus?.face_reference_enrolled ??
        state.user.student_profile?.is_face_registered
    )

    state.user = {
        ...state.user,
        student_profile: {
            ...state.user.student_profile,
            is_face_registered: isFaceRegistered,
        },
    }
}

function applyActiveTheme() {
    applyTheme(loadTheme(state.schoolSettings))
}

function resetDashboardState() {
    state.user = null
    state.schoolSettings = null
    state.events = []
    state.attendanceRecords = []
    state.faceStatus = null
    state.initialized = false
    state.loading = false
    state.error = ''
    applyActiveTheme()
}

function setToken(token) {
    state.token = String(token || '')
    if (state.token) {
        localStorage.setItem('aura_token', state.token)
    } else {
        localStorage.removeItem('aura_token')
    }
}

async function fetchDashboardData() {
    if (!state.token) {
        resetDashboardState()
        return null
    }

    state.loading = true
    state.error = ''

    try {
        const user = await getCurrentUserProfile(state.apiBaseUrl, state.token)

        const [settingsResult, eventsResult, attendanceResult, faceStatusResult] = await Promise.allSettled([
            getSchoolSettings(state.apiBaseUrl, state.token),
            getEvents(state.apiBaseUrl, state.token, { limit: 200 }),
            getMyAttendance(state.apiBaseUrl, state.token, { limit: 200 }),
            getFaceStatus(state.apiBaseUrl, state.token),
        ])

        const schoolId = Number(user?.school_id)
        const nextEvents = eventsResult.status === 'fulfilled' && Array.isArray(eventsResult.value)
            ? eventsResult.value
                .map(normalizeEvent)
                .filter(Boolean)
                .filter((event) => !Number.isFinite(schoolId) || Number(event?.school_id) === schoolId)
            : []

        state.user = user
        state.schoolSettings = settingsResult.status === 'fulfilled' ? settingsResult.value : null
        state.events = sortEvents(nextEvents)
        state.attendanceRecords = attendanceResult.status === 'fulfilled' && Array.isArray(attendanceResult.value)
            ? attendanceResult.value
            : []
        state.faceStatus = faceStatusResult.status === 'fulfilled'
            ? faceStatusResult.value
            : {
                face_reference_enrolled: Boolean(user?.student_profile?.is_face_registered),
            }
        state.initialized = true
        syncUserAttendanceRecords()
        syncUserFaceState()
        applyActiveTheme()

        return state
    } catch (error) {
        state.error = error?.message || 'Unable to load dashboard data.'
        throw error
    } finally {
        state.loading = false
    }
}

export function hasSessionToken() {
    return Boolean(localStorage.getItem('aura_token'))
}

export async function initializeDashboardSession(force = false) {
    state.apiBaseUrl = resolveApiBaseUrl()
    state.token = localStorage.getItem('aura_token') || ''

    if (!state.token) {
        resetDashboardState()
        return null
    }

    if (initPromise && !force) {
        return initPromise
    }

    initPromise = fetchDashboardData().finally(() => {
        initPromise = null
    })

    return initPromise
}

export async function refreshAttendanceRecords(params = {}) {
    if (!state.token) return []

    const records = await getMyAttendance(state.apiBaseUrl, state.token, {
        limit: 200,
        ...params,
    })

    state.attendanceRecords = Array.isArray(records) ? records : []
    syncUserAttendanceRecords()
    return state.attendanceRecords
}

export async function refreshFaceStatus() {
    if (!state.token) return null

    const nextFaceStatus = await getFaceStatus(state.apiBaseUrl, state.token)
    state.faceStatus = nextFaceStatus
    syncUserFaceState()
    return state.faceStatus
}

export async function ensureDashboardEvent(eventId) {
    const normalizedEventId = Number(eventId)
    if (!Number.isFinite(normalizedEventId) || !state.token) return null

    const existing = state.events.find((event) => Number(event?.id) === normalizedEventId)
    if (existing) return existing

    const event = normalizeEvent(await getEventById(state.apiBaseUrl, state.token, normalizedEventId))
    if (!event) return null

    const remaining = state.events.filter((item) => Number(item?.id) !== normalizedEventId)
    state.events = sortEvents([...remaining, event])
    return event
}

export async function saveCurrentUserProfile(payload) {
    const userId = Number(state.user?.id)
    if (!state.token || !Number.isFinite(userId)) {
        throw new Error('No authenticated user is available.')
    }

    await updateUser(state.apiBaseUrl, state.token, userId, payload)
    await initializeDashboardSession(true)
    return state.user
}

export function clearDashboardSession() {
    localStorage.removeItem('aura_token')
    localStorage.removeItem('aura_user_roles')
    setToken('')
    resetDashboardState()
}

export function getDashboardEventById(eventId) {
    const normalizedEventId = Number(eventId)
    if (!Number.isFinite(normalizedEventId)) return null
    return state.events.find((event) => Number(event?.id) === normalizedEventId) ?? null
}

export function hasAttendanceForEvent(eventId) {
    const normalizedEventId = Number(eventId)
    if (!Number.isFinite(normalizedEventId)) return false

    return state.attendanceRecords.some((attendance) => {
        const status = String(attendance?.status ?? '').toLowerCase()
        const hasTimeIn = Boolean(attendance?.time_in)
        return Number(attendance?.event_id) === normalizedEventId && (
            status === 'present' ||
            status === 'late' ||
            hasTimeIn
        )
    })
}

export function sessionNeedsFaceRegistration() {
    const roleNames = Array.isArray(state.user?.roles)
        ? state.user.roles.map((entry) => entry?.role?.name || entry?.name).filter(Boolean)
        : []

    const isStudentSession = Boolean(state.user?.student_profile) || roleNames.includes('student')
    if (!isStudentSession) return false

    return !Boolean(
        state.faceStatus?.face_reference_enrolled ??
        state.user?.student_profile?.is_face_registered
    )
}

export function useDashboardSession() {
    return {
        dashboardState: readonly(state),
        apiBaseUrl: computed(() => state.apiBaseUrl),
        currentUser: computed(() => state.user),
        schoolSettings: computed(() => state.schoolSettings),
        events: computed(() => state.events),
        attendanceRecords: computed(() => state.attendanceRecords),
        faceStatus: computed(() => state.faceStatus),
        needsFaceRegistration: computed(() => sessionNeedsFaceRegistration()),
        unreadAnnouncements: computed(() => 0),
        initializeDashboardSession,
        refreshAttendanceRecords,
        refreshFaceStatus,
        ensureDashboardEvent,
        saveCurrentUserProfile,
        clearDashboardSession,
        getDashboardEventById,
        hasAttendanceForEvent,
        sessionNeedsFaceRegistration,
    }
}
