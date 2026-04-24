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

const state = reactive({
    apiBaseUrl: resolveApiBaseUrl(),
    schoolId: null,
    userId: null,
    tokenSuffix: null,
    sessionId: null,
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
let fetchSequence = 0

function hasResolvedCouncilUnit(setup = null) {
    return Number.isFinite(Number(setup?.unit?.id))
}

function resolveNumericIdentityValue(value) {
    const normalized = Number(value)
    return Number.isFinite(normalized) ? normalized : null
}

function resolveTokenSuffix(token = localStorage.getItem('aura_token') || '') {
    const normalizedToken = String(token || '').trim()
    return normalizedToken ? normalizedToken.slice(-24) : null
}

function hasMatchingIdentity(authMeta = getStoredAuthMeta()) {
    return (
        state.userId === resolveNumericIdentityValue(authMeta?.userId)
        && state.schoolId === resolveNumericIdentityValue(authMeta?.schoolId)
        && state.sessionId === (authMeta?.sessionId || null)
        && state.tokenSuffix === resolveTokenSuffix()
    )
}

function resetWorkspaceState() {
    state.departments = []
    state.programs = []
    state.users = []
    state.campusSsgSetup = null
    state.schoolId = null
    state.userId = null
    state.tokenSuffix = null
    state.sessionId = null
    state.initialized = false
    state.statuses = {
        departments: 'idle',
        programs: 'idle',
        users: 'idle',
        council: 'idle',
    }
}

function setCampusSsgSetupSnapshot(setup) {
    state.campusSsgSetup = hasResolvedCouncilUnit(setup) ? setup : null
    state.statuses.council = hasResolvedCouncilUnit(setup) ? 'ready' : 'absent'
    state.initialized = true
}

function setDepartmentsSnapshot(departments) {
    state.departments = Array.isArray(departments) ? departments : []
    state.statuses.departments = 'ready'
    state.initialized = true
}

function setProgramsSnapshot(programs) {
    state.programs = Array.isArray(programs) ? programs : []
    state.statuses.programs = 'ready'
    state.initialized = true
}

function setUsersSnapshot(users) {
    state.users = Array.isArray(users) ? users : []
    state.statuses.users = 'ready'
    state.initialized = true
}

function classifyFailure(error) {
    if (error instanceof BackendApiError) {
        if (error.status === 403) return 'blocked'
        if (error.status === 404) return 'absent'
    }
    return 'error'
}

function hasReusableWorkspaceSnapshot() {
    return (
        state.initialized &&
        state.statuses.departments === 'ready' &&
        state.statuses.programs === 'ready' &&
        state.statuses.users === 'ready' &&
        state.statuses.council === 'ready'
    )
}

function setResolvedCollection(key, result) {
    if (result.status === 'fulfilled') {
        state[key] = Array.isArray(result.value) ? result.value : []
        state.statuses[key] = 'ready'
        return
    }

    const existingItems = Array.isArray(state[key]) ? state[key] : []
    if (existingItems.length) {
        state.statuses[key] = 'ready'
        return
    }

    state[key] = []
    state.statuses[key] = classifyFailure(result.reason)
}

function setResolvedCouncil(result) {
    if (result.status === 'fulfilled') {
        state.campusSsgSetup = hasResolvedCouncilUnit(result.value) ? result.value : null
        state.statuses.council = hasResolvedCouncilUnit(result.value) ? 'ready' : 'absent'
        return
    }

    if (hasResolvedCouncilUnit(state.campusSsgSetup)) {
        state.statuses.council = 'ready'
        return
    }

    state.campusSsgSetup = null
    state.statuses.council = classifyFailure(result.reason)
}

async function fetchSchoolItWorkspaceData() {
    const authMeta = getStoredAuthMeta()
    const schoolId = resolveNumericIdentityValue(authMeta?.schoolId)
    const userId = resolveNumericIdentityValue(authMeta?.userId)
    const token = localStorage.getItem('aura_token') || ''
    const sessionId = authMeta?.sessionId || null

    state.apiBaseUrl = resolveApiBaseUrl()
    state.schoolId = schoolId
    state.userId = userId
    state.tokenSuffix = resolveTokenSuffix(token)
    state.sessionId = sessionId

    const currentFetchSequence = ++fetchSequence
    if (!state.initialized) {
        state.statuses = {
            departments: 'loading',
            programs: 'loading',
            users: 'loading',
            council: 'loading',
        }
    }

    if (!token) {
        resetWorkspaceState()
        state.loading = false
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

        if (currentFetchSequence !== fetchSequence) {
            return state
        }

        setResolvedCollection('departments', departmentsResult)
        setResolvedCollection('programs', programsResult)
        setResolvedCollection('users', usersResult)
        setResolvedCouncil(councilResult)

        state.initialized = true
        return state
    } finally {
        if (currentFetchSequence === fetchSequence) {
            state.loading = false
        }
    }
}

export async function initializeSchoolItWorkspaceData(force = false) {
    if (initPromise && !force) return initPromise

    if (!hasMatchingIdentity()) {
        resetWorkspaceState()
    }

    if (!force && hasReusableWorkspaceSnapshot()) return state

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
        setDepartmentsSnapshot,
        setProgramsSnapshot,
        setUsersSnapshot,
    }
}
