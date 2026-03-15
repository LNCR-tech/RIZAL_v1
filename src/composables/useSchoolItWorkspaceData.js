import { computed, reactive, readonly } from 'vue'
import {
    BackendApiError,
    getCampusSsgSetup,
    getDepartments,
    getPrograms,
    getUsers,
    resolveApiBaseUrl,
} from '@/services/backendApi.js'
import { getStoredAuthMeta } from '@/services/localAuth.js'

const SCHOOL_IT_WORKSPACE_CACHE_KEY = 'aura_school_it_workspace_cache_v1'

const state = reactive({
    apiBaseUrl: resolveApiBaseUrl(),
    schoolId: null,
    userId: null,
    initialized: false,
    loading: false,
    departments: [],
    programs: [],
    users: [],
    campusSsgSetup: null,
    statuses: {
        departments: 'idle',
        programs: 'idle',
        users: 'idle',
        council: 'idle',
    },
})

let initPromise = null

function buildIdentity(authMeta = getStoredAuthMeta()) {
    return {
        sessionId: authMeta?.sessionId || null,
        userId: Number.isFinite(Number(authMeta?.userId)) ? Number(authMeta.userId) : null,
        schoolId: Number.isFinite(Number(authMeta?.schoolId)) ? Number(authMeta.schoolId) : null,
        email: authMeta?.email || null,
    }
}

function readCache() {
    try {
        const raw = localStorage.getItem(SCHOOL_IT_WORKSPACE_CACHE_KEY)
        if (!raw) return null
        return JSON.parse(raw)
    } catch {
        localStorage.removeItem(SCHOOL_IT_WORKSPACE_CACHE_KEY)
        return null
    }
}

function identitiesMatch(left, right) {
    if (!left || !right) return false
    return ['sessionId', 'userId', 'schoolId', 'email'].every((key) => {
        const expected = right[key]
        if (expected == null || expected === '') return true
        return left[key] === expected
    })
}

function persistCache() {
    const identity = buildIdentity()
    if (!identity.userId && !identity.schoolId) return

    localStorage.setItem(SCHOOL_IT_WORKSPACE_CACHE_KEY, JSON.stringify({
        version: 1,
        identity,
        snapshot: {
            departments: state.departments,
            programs: state.programs,
            users: state.users,
            campusSsgSetup: state.campusSsgSetup,
            statuses: state.statuses,
        },
    }))
}

function setCampusSsgSetupSnapshot(setup) {
    state.campusSsgSetup = setup ?? null
    state.statuses.council = setup?.unit ? 'ready' : 'absent'
    state.initialized = true
    persistCache()
}

function hydrateCache() {
    const cached = readCache()
    if (!cached?.snapshot || !identitiesMatch(cached.identity, buildIdentity())) return false

    state.departments = Array.isArray(cached.snapshot.departments) ? cached.snapshot.departments : []
    state.programs = Array.isArray(cached.snapshot.programs) ? cached.snapshot.programs : []
    state.users = Array.isArray(cached.snapshot.users) ? cached.snapshot.users : []
    state.campusSsgSetup = cached.snapshot.campusSsgSetup ?? null
    state.statuses = {
        departments: cached.snapshot.statuses?.departments || 'idle',
        programs: cached.snapshot.statuses?.programs || 'idle',
        users: cached.snapshot.statuses?.users || 'idle',
        council: cached.snapshot.statuses?.council || 'idle',
    }
    state.initialized = true
    return true
}

function classifyFailure(error) {
    if (error instanceof BackendApiError) {
        if (error.status === 403) return 'blocked'
        if (error.status === 404) return 'absent'
    }
    return 'error'
}

function setResolvedCollection(key, result) {
    if (result.status === 'fulfilled') {
        state[key] = Array.isArray(result.value) ? result.value : []
        state.statuses[key] = 'ready'
        return
    }

    state[key] = []
    state.statuses[key] = classifyFailure(result.reason)
}

function setResolvedCouncil(result) {
    if (result.status === 'fulfilled') {
        state.campusSsgSetup = result.value ?? null
        state.statuses.council = result.value ? 'ready' : 'absent'
        return
    }

    state.campusSsgSetup = null
    state.statuses.council = classifyFailure(result.reason)
}

async function fetchSchoolItWorkspaceData() {
    const authMeta = getStoredAuthMeta()
    const schoolId = Number(authMeta?.schoolId)
    const userId = Number(authMeta?.userId)

    state.apiBaseUrl = resolveApiBaseUrl()
    state.schoolId = Number.isFinite(schoolId) ? schoolId : null
    state.userId = Number.isFinite(userId) ? userId : null

    if (!hydrateCache()) {
        state.statuses = {
            departments: 'loading',
            programs: 'loading',
            users: 'loading',
            council: 'loading',
        }
    }

    const token = localStorage.getItem('aura_token') || ''
    if (!token) {
        state.departments = []
        state.programs = []
        state.users = []
        state.campusSsgSetup = null
        state.initialized = false
        state.loading = false
        state.statuses = {
            departments: 'idle',
            programs: 'idle',
            users: 'idle',
            council: 'idle',
        }
        return state
    }

    state.loading = true

    try {
        const [departmentsResult, programsResult, usersResult, councilResult] = await Promise.allSettled([
            getDepartments(state.apiBaseUrl, token),
            getPrograms(state.apiBaseUrl, token),
            getUsers(state.apiBaseUrl, token),
            getCampusSsgSetup(state.apiBaseUrl, token),
        ])

        setResolvedCollection('departments', departmentsResult)
        setResolvedCollection('programs', programsResult)
        setResolvedCollection('users', usersResult)
        setResolvedCouncil(councilResult)

        state.initialized = true
        persistCache()
        return state
    } finally {
        state.loading = false
    }
}

export async function initializeSchoolItWorkspaceData(force = false) {
    if (initPromise && !force) return initPromise
    if (!force && state.initialized) return state

    initPromise = fetchSchoolItWorkspaceData().finally(() => {
        initPromise = null
    })

    return initPromise
}

export function refreshSchoolItWorkspaceData() {
    return initializeSchoolItWorkspaceData(true)
}

export function useSchoolItWorkspaceData() {
    return {
        schoolItWorkspaceState: readonly(state),
        departments: computed(() => state.departments),
        programs: computed(() => state.programs),
        users: computed(() => state.users),
        campusSsgSetup: computed(() => state.campusSsgSetup),
        statuses: computed(() => state.statuses),
        initializeSchoolItWorkspaceData,
        refreshSchoolItWorkspaceData,
        setCampusSsgSetupSnapshot,
    }
}
