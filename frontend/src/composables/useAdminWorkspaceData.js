import { computed, reactive, readonly } from 'vue'
import {
    BackendApiError,
    createSchoolWithSchoolIt,
    dispatchLowAttendanceNotifications,
    dispatchMissedEventNotifications,
    getAdminSchoolItAccounts,
    getAdminSchools,
    getAuditLogs,
    getGovernanceRequests,
    getGovernanceSettings,
    getNotificationLogs,
    resolveApiBaseUrl,
    resetAdminSchoolItPassword,
    runGovernanceRetention,
    updateAdminSchoolItAccountStatus,
    updateAdminSchoolStatus,
    updateGovernanceRequest,
    updateGovernanceSettings,
} from '@/services/backendApi.js'
import {
    normalizeGovernanceRequest,
    normalizeGovernanceSetting,
    normalizeNotificationLogItem,
    normalizePasswordResetResponse,
    normalizeRetentionRunResult,
    normalizeSchoolItAccount,
    normalizeSchoolSummary,
} from '@/services/backendNormalizers.js'
import { adminDashboardPreviewData, createAdminDashboardPreviewData } from '@/data/adminDashboardPreview.js'
import { getStoredAuthMeta } from '@/services/localAuth.js'

function createStatuses() {
    return {
        schools: 'idle',
        accounts: 'idle',
        audits: 'idle',
        notifications: 'idle',
        requests: 'idle',
        governance: 'idle',
    }
}

function createState() {
    return {
        apiBaseUrl: resolveApiBaseUrl(),
        tokenSuffix: null,
        sessionId: null,
        userId: null,
        initialized: false,
        loading: false,
        creatingSchool: false,
        schools: [],
        campusAccounts: [],
        auditLogs: [],
        auditLogTotal: 0,
        notificationLogs: [],
        governanceRequests: [],
        governanceSettingsBySchool: {},
        selectedSchoolId: null,
        lastPasswordReset: null,
        lastDispatchSummary: null,
        lastRetentionRun: null,
        statuses: createStatuses(),
        error: '',
    }
}

const state = reactive(createState())
const previewState = reactive(createState())

let initPromise = null

function resolveTokenSuffix(token = localStorage.getItem('aura_token') || '') {
    const normalized = String(token || '').trim()
    return normalized ? normalized.slice(-24) : null
}

function resolveIdentityValue(value) {
    const normalized = Number(value)
    return Number.isFinite(normalized) ? normalized : null
}

function resetState(target) {
    const next = createState()
    Object.assign(target, next)
}

function setPreviewSnapshot() {
    const snapshot = createAdminDashboardPreviewData()
    resetState(previewState)
    previewState.initialized = true
    previewState.loading = false
    previewState.schools = Array.isArray(snapshot.schools) ? snapshot.schools : []
    previewState.campusAccounts = Array.isArray(snapshot.campusAccounts) ? snapshot.campusAccounts : []
    previewState.auditLogs = Array.isArray(snapshot.auditLogs?.items) ? snapshot.auditLogs.items : []
    previewState.auditLogTotal = Number(snapshot.auditLogs?.total || previewState.auditLogs.length || 0)
    previewState.notificationLogs = Array.isArray(snapshot.notificationLogs) ? snapshot.notificationLogs : []
    previewState.governanceRequests = Array.isArray(snapshot.governanceRequests) ? snapshot.governanceRequests : []
    previewState.governanceSettingsBySchool = { ...(snapshot.governanceSettingsBySchool || {}) }
    previewState.selectedSchoolId = snapshot.schools?.[0]?.school_id ?? null
    previewState.statuses = {
        schools: 'ready',
        accounts: 'ready',
        audits: 'ready',
        notifications: 'ready',
        requests: 'ready',
        governance: previewState.selectedSchoolId ? 'ready' : 'absent',
    }
}

setPreviewSnapshot()

function hasMatchingIdentity() {
    const authMeta = getStoredAuthMeta()
    return (
        state.userId === resolveIdentityValue(authMeta?.userId)
        && state.sessionId === (authMeta?.sessionId || null)
        && state.tokenSuffix === resolveTokenSuffix()
    )
}

function classifyFailure(error) {
    if (error instanceof BackendApiError) {
        if (error.status === 403) return 'blocked'
        if (error.status === 404) return 'absent'
    }
    return 'error'
}

function ensureSelectedSchool(target) {
    if (
        Number.isFinite(Number(target.selectedSchoolId))
        && target.schools.some((school) => Number(school?.school_id) === Number(target.selectedSchoolId))
    ) {
        return Number(target.selectedSchoolId)
    }

    const fallbackId = target.schools?.[0]?.school_id ?? null
    target.selectedSchoolId = fallbackId
    return fallbackId
}

async function fetchGovernanceSettingsForSelectedSchool(target, token) {
    const selectedSchoolId = ensureSelectedSchool(target)
    if (!Number.isFinite(Number(selectedSchoolId))) {
        target.statuses.governance = 'absent'
        return null
    }

    target.statuses.governance = 'loading'

    try {
        const settings = await getGovernanceSettings(target.apiBaseUrl, token, {
            school_id: selectedSchoolId,
        })
        target.governanceSettingsBySchool = {
            ...target.governanceSettingsBySchool,
            [selectedSchoolId]: settings,
        }
        target.statuses.governance = settings ? 'ready' : 'absent'
        return settings
    } catch (error) {
        target.statuses.governance = classifyFailure(error)
        throw error
    }
}

async function fetchAdminWorkspaceData() {
    const authMeta = getStoredAuthMeta()
    const token = localStorage.getItem('aura_token') || ''

    state.apiBaseUrl = resolveApiBaseUrl()
    state.tokenSuffix = resolveTokenSuffix(token)
    state.sessionId = authMeta?.sessionId || null
    state.userId = resolveIdentityValue(authMeta?.userId)
    state.loading = true
    state.error = ''
    state.statuses = {
        schools: 'loading',
        accounts: 'loading',
        audits: 'loading',
        notifications: 'loading',
        requests: 'loading',
        governance: 'loading',
    }

    if (!token) {
        resetState(state)
        return state
    }

    try {
        const [schoolsResult, accountsResult, auditsResult, notificationsResult, requestsResult] = await Promise.allSettled([
            getAdminSchools(state.apiBaseUrl, token),
            getAdminSchoolItAccounts(state.apiBaseUrl, token),
            getAuditLogs(state.apiBaseUrl, token, { limit: 40 }),
            getNotificationLogs(state.apiBaseUrl, token, { limit: 40 }),
            getGovernanceRequests(state.apiBaseUrl, token, { limit: 40 }),
        ])

        if (schoolsResult.status === 'fulfilled') {
            state.schools = Array.isArray(schoolsResult.value) ? schoolsResult.value : []
            state.statuses.schools = 'ready'
        } else {
            state.schools = []
            state.statuses.schools = classifyFailure(schoolsResult.reason)
        }

        if (accountsResult.status === 'fulfilled') {
            state.campusAccounts = Array.isArray(accountsResult.value) ? accountsResult.value : []
            state.statuses.accounts = 'ready'
        } else {
            state.campusAccounts = []
            state.statuses.accounts = classifyFailure(accountsResult.reason)
        }

        if (auditsResult.status === 'fulfilled') {
            state.auditLogs = Array.isArray(auditsResult.value?.items) ? auditsResult.value.items : []
            state.auditLogTotal = Number(auditsResult.value?.total || state.auditLogs.length || 0)
            state.statuses.audits = 'ready'
        } else {
            state.auditLogs = []
            state.auditLogTotal = 0
            state.statuses.audits = classifyFailure(auditsResult.reason)
        }

        if (notificationsResult.status === 'fulfilled') {
            state.notificationLogs = Array.isArray(notificationsResult.value) ? notificationsResult.value : []
            state.statuses.notifications = 'ready'
        } else {
            state.notificationLogs = []
            state.statuses.notifications = classifyFailure(notificationsResult.reason)
        }

        if (requestsResult.status === 'fulfilled') {
            state.governanceRequests = Array.isArray(requestsResult.value) ? requestsResult.value : []
            state.statuses.requests = 'ready'
        } else {
            state.governanceRequests = []
            state.statuses.requests = classifyFailure(requestsResult.reason)
        }

        await fetchGovernanceSettingsForSelectedSchool(state, token).catch((error) => {
            state.error = error?.message || 'Governance settings are unavailable right now.'
            return null
        })

        state.initialized = true
        return state
    } finally {
        state.loading = false
    }
}

export async function initializeAdminWorkspaceData(options = {}) {
    const { preview = false, force = false } = options

    if (preview) {
        if (force) setPreviewSnapshot()
        return previewState
    }

    if (!hasMatchingIdentity()) {
        resetState(state)
    }

    if (state.initialized && !force) return state
    if (initPromise && !force) return initPromise

    initPromise = fetchAdminWorkspaceData().finally(() => {
        initPromise = null
    })

    return initPromise
}

export function refreshAdminWorkspaceData(options = {}) {
    return initializeAdminWorkspaceData({
        ...options,
        force: true,
    })
}

export async function selectAdminSchool(schoolId, options = {}) {
    const { preview = false } = options
    const target = preview ? previewState : state
    const nextSchoolId = resolveIdentityValue(schoolId)
    target.selectedSchoolId = nextSchoolId

    if (preview) {
        target.statuses.governance = nextSchoolId ? 'ready' : 'absent'
        return target.governanceSettingsBySchool[nextSchoolId] ?? null
    }

    const token = localStorage.getItem('aura_token') || ''
    if (!token) return null
    return fetchGovernanceSettingsForSelectedSchool(target, token)
}

export async function createAdminSchool(payload, options = {}) {
    const { preview = false } = options
    if (preview) {
        const nextSchoolId = Math.max(0, ...previewState.schools.map((item) => Number(item?.school_id) || 0)) + 1
        const nextUserId = Math.max(0, ...previewState.campusAccounts.map((item) => Number(item?.user_id) || 0)) + 1
        const createdAt = new Date().toISOString()
        const schoolSummary = normalizeSchoolSummary({
            school_id: nextSchoolId,
            school_name: payload.school_name,
            school_code: payload.school_code || null,
            subscription_status: 'trial',
            active_status: true,
            created_at: createdAt,
            updated_at: createdAt,
            primary_color: payload.primary_color,
            secondary_color: payload.secondary_color,
            logo_url: payload.logo ? URL.createObjectURL(payload.logo) : null,
        })

        const campusAccount = normalizeSchoolItAccount({
            user_id: nextUserId,
            email: payload.school_it_email,
            first_name: payload.school_it_first_name,
            last_name: payload.school_it_last_name,
            school_id: nextSchoolId,
            school_name: payload.school_name,
            is_active: true,
        })

        previewState.schools = [schoolSummary, ...previewState.schools]
        previewState.campusAccounts = [campusAccount, ...previewState.campusAccounts]
        previewState.selectedSchoolId = nextSchoolId
        previewState.governanceSettingsBySchool = {
            ...previewState.governanceSettingsBySchool,
            [nextSchoolId]: normalizeGovernanceSetting({
                school_id: nextSchoolId,
                attendance_retention_days: 365,
                audit_log_retention_days: 365,
                import_file_retention_days: 30,
                auto_delete_enabled: false,
                updated_at: createdAt,
            }),
        }

        return {
            school: schoolSummary,
            school_it_user_id: nextUserId,
            school_it_email: campusAccount.email,
            generated_temporary_password: payload.school_it_password || `Temp-${nextSchoolId}!`,
        }
    }

    const token = localStorage.getItem('aura_token') || ''
    if (!token) {
        throw new BackendApiError('No authenticated admin session is available.')
    }

    state.creatingSchool = true
    try {
        const created = await createSchoolWithSchoolIt(state.apiBaseUrl, token, payload)
        const createdSchool = normalizeSchoolSummary({
            ...created?.school,
            school_id: created?.school?.school_id,
            school_name: created?.school?.school_name,
            school_code: created?.school?.school_code,
            subscription_status: created?.school?.subscription_status,
            active_status: created?.school?.active_status,
            created_at: created?.school?.created_at,
            updated_at: created?.school?.updated_at,
        })
        const createdAccount = normalizeSchoolItAccount({
            user_id: created?.school_it_user_id,
            email: created?.school_it_email,
            school_id: created?.school?.school_id,
            school_name: created?.school?.school_name,
            is_active: true,
            first_name: payload.school_it_first_name,
            last_name: payload.school_it_last_name,
        })

        state.schools = [createdSchool, ...state.schools.filter((item) => Number(item?.school_id) !== Number(createdSchool?.school_id))]
        state.campusAccounts = [createdAccount, ...state.campusAccounts.filter((item) => Number(item?.user_id) !== Number(createdAccount?.user_id))]
        state.selectedSchoolId = createdSchool?.school_id ?? state.selectedSchoolId
        if (created?.school?.school_id) {
            state.governanceSettingsBySchool = {
                ...state.governanceSettingsBySchool,
                [created.school.school_id]: normalizeGovernanceSetting({
                    school_id: created.school.school_id,
                    attendance_retention_days: 365,
                    audit_log_retention_days: 365,
                    import_file_retention_days: 30,
                    auto_delete_enabled: false,
                    updated_at: created.school.updated_at || new Date().toISOString(),
                }),
            }
        }
        state.lastPasswordReset = normalizePasswordResetResponse({
            user_id: created?.school_it_user_id,
            email: created?.school_it_email,
            temporary_password: created?.generated_temporary_password,
            must_change_password: true,
        })
        return created
    } finally {
        state.creatingSchool = false
    }
}

export async function saveAdminSchoolStatus(schoolId, payload, options = {}) {
    const { preview = false } = options
    const target = preview ? previewState : state
    const normalizedSchoolId = resolveIdentityValue(schoolId)

    if (preview) {
        target.schools = target.schools.map((school) => (
            Number(school?.school_id) === normalizedSchoolId
                ? normalizeSchoolSummary({
                    ...school,
                    ...payload,
                    school_id: normalizedSchoolId,
                    updated_at: new Date().toISOString(),
                })
                : school
        ))
        return target.schools.find((school) => Number(school?.school_id) === normalizedSchoolId) ?? null
    }

    const token = localStorage.getItem('aura_token') || ''
    const updated = await updateAdminSchoolStatus(state.apiBaseUrl, token, normalizedSchoolId, payload)
    target.schools = target.schools.map((school) => (
        Number(school?.school_id) === normalizedSchoolId
            ? normalizeSchoolSummary({
                ...school,
                school_id: updated?.school_id,
                school_name: updated?.school_name,
                school_code: updated?.school_code,
                subscription_status: updated?.subscription_status,
                active_status: updated?.active_status,
                created_at: updated?.created_at,
                updated_at: updated?.updated_at,
            })
            : school
    ))
    return updated
}

export async function saveAdminCampusAccountStatus(userId, isActive, options = {}) {
    const { preview = false } = options
    const target = preview ? previewState : state
    const normalizedUserId = resolveIdentityValue(userId)

    if (preview) {
        target.campusAccounts = target.campusAccounts.map((account) => (
            Number(account?.user_id) === normalizedUserId
                ? normalizeSchoolItAccount({
                    ...account,
                    is_active: Boolean(isActive),
                })
                : account
        ))
        return target.campusAccounts.find((account) => Number(account?.user_id) === normalizedUserId) ?? null
    }

    const token = localStorage.getItem('aura_token') || ''
    const updated = await updateAdminSchoolItAccountStatus(state.apiBaseUrl, token, normalizedUserId, isActive)
    target.campusAccounts = target.campusAccounts.map((account) => (
        Number(account?.user_id) === normalizedUserId ? updated : account
    ))
    return updated
}

export async function resetAdminCampusPassword(userId, options = {}) {
    const { preview = false } = options
    const normalizedUserId = resolveIdentityValue(userId)

    if (preview) {
        const account = previewState.campusAccounts.find((item) => Number(item?.user_id) === normalizedUserId)
        const result = normalizePasswordResetResponse({
            user_id: normalizedUserId,
            email: account?.email || null,
            temporary_password: `Temp-${normalizedUserId}!`,
            must_change_password: true,
        })
        previewState.lastPasswordReset = result
        return result
    }

    const token = localStorage.getItem('aura_token') || ''
    const result = await resetAdminSchoolItPassword(state.apiBaseUrl, token, normalizedUserId)
    state.lastPasswordReset = result
    return result
}

export async function dispatchAdminNotification(kind, params = {}, options = {}) {
    const { preview = false } = options
    const target = preview ? previewState : state
    const schoolId = resolveIdentityValue(params.school_id ?? target.selectedSchoolId)

    if (preview) {
        const summary = {
            processed_users: 12,
            sent: 11,
            failed: 1,
            skipped: 0,
            category: kind,
        }
        target.lastDispatchSummary = summary
        target.notificationLogs = [
            normalizeNotificationLogItem({
                id: Date.now(),
                school_id: schoolId,
                user_id: null,
                category: kind,
                channel: 'email',
                status: 'sent',
                subject: kind === 'missed_events' ? 'Missed event notifications dispatched' : 'Low attendance notifications dispatched',
                message: `Dispatch completed for school ${schoolId}.`,
                created_at: new Date().toISOString(),
            }),
            ...target.notificationLogs,
        ]
        return summary
    }

    const token = localStorage.getItem('aura_token') || ''
    const actionParams = {
        ...params,
        school_id: schoolId,
    }
    const summary = kind === 'missed_events'
        ? await dispatchMissedEventNotifications(state.apiBaseUrl, token, actionParams)
        : await dispatchLowAttendanceNotifications(state.apiBaseUrl, token, actionParams)

    state.lastDispatchSummary = summary
    state.notificationLogs = await getNotificationLogs(state.apiBaseUrl, token, {
        limit: 40,
        school_id: schoolId,
    }).catch(() => state.notificationLogs)
    return summary
}

export async function saveAdminGovernanceSettings(payload, options = {}) {
    const { preview = false, schoolId = null } = options
    const target = preview ? previewState : state
    const normalizedSchoolId = resolveIdentityValue(schoolId ?? target.selectedSchoolId)

    if (!Number.isFinite(normalizedSchoolId)) {
        throw new BackendApiError('Select a school first.')
    }

    if (preview) {
        const updated = normalizeGovernanceSetting({
            ...(target.governanceSettingsBySchool[normalizedSchoolId] || {}),
            ...payload,
            school_id: normalizedSchoolId,
            updated_at: new Date().toISOString(),
        })
        target.governanceSettingsBySchool = {
            ...target.governanceSettingsBySchool,
            [normalizedSchoolId]: updated,
        }
        return updated
    }

    const token = localStorage.getItem('aura_token') || ''
    const updated = await updateGovernanceSettings(state.apiBaseUrl, token, payload, {
        school_id: normalizedSchoolId,
    })
    state.governanceSettingsBySchool = {
        ...state.governanceSettingsBySchool,
        [normalizedSchoolId]: updated,
    }
    return updated
}

export async function reviewAdminGovernanceRequest(requestId, payload, options = {}) {
    const { preview = false } = options
    const target = preview ? previewState : state
    const normalizedRequestId = resolveIdentityValue(requestId)

    if (preview) {
        const updated = normalizeGovernanceRequest({
            ...target.governanceRequests.find((item) => Number(item?.id) === normalizedRequestId),
            ...payload,
            id: normalizedRequestId,
            resolved_at: new Date().toISOString(),
        })
        target.governanceRequests = target.governanceRequests.map((item) => (
            Number(item?.id) === normalizedRequestId ? updated : item
        ))
        return updated
    }

    const token = localStorage.getItem('aura_token') || ''
    const updated = await updateGovernanceRequest(state.apiBaseUrl, token, normalizedRequestId, payload)
    state.governanceRequests = state.governanceRequests.map((item) => (
        Number(item?.id) === normalizedRequestId ? updated : item
    ))
    return updated
}

export async function runAdminRetentionCleanup(payload, options = {}) {
    const { preview = false, schoolId = null } = options
    const target = preview ? previewState : state
    const normalizedSchoolId = resolveIdentityValue(schoolId ?? target.selectedSchoolId)

    if (!Number.isFinite(normalizedSchoolId)) {
        throw new BackendApiError('Select a school first.')
    }

    if (preview) {
        const result = normalizeRetentionRunResult({
            school_id: normalizedSchoolId,
            dry_run: Boolean(payload?.dry_run),
            deleted_audit_logs: 18,
            deleted_import_logs: 4,
            deleted_notifications: 12,
            summary: `audit_logs=18, import_jobs=4, notifications=12, dry_run=${Boolean(payload?.dry_run)}`,
        })
        target.lastRetentionRun = result
        return result
    }

    const token = localStorage.getItem('aura_token') || ''
    const result = await runGovernanceRetention(state.apiBaseUrl, token, payload, {
        school_id: normalizedSchoolId,
    })
    state.lastRetentionRun = result
    return result
}

export function useAdminWorkspaceData(preview = false) {
    const target = preview ? previewState : state

    return {
        adminWorkspaceState: readonly(target),
        schools: computed(() => target.schools),
        campusAccounts: computed(() => target.campusAccounts),
        auditLogs: computed(() => target.auditLogs),
        auditLogTotal: computed(() => target.auditLogTotal),
        notificationLogs: computed(() => target.notificationLogs),
        governanceRequests: computed(() => target.governanceRequests),
        governanceSettingsBySchool: computed(() => target.governanceSettingsBySchool),
        selectedSchoolId: computed(() => target.selectedSchoolId),
        lastPasswordReset: computed(() => target.lastPasswordReset),
        lastDispatchSummary: computed(() => target.lastDispatchSummary),
        lastRetentionRun: computed(() => target.lastRetentionRun),
        initializeAdminWorkspaceData: (options = {}) => initializeAdminWorkspaceData({ ...options, preview }),
        refreshAdminWorkspaceData: (options = {}) => refreshAdminWorkspaceData({ ...options, preview }),
        selectAdminSchool: (schoolId) => selectAdminSchool(schoolId, { preview }),
        createAdminSchool: (payload) => createAdminSchool(payload, { preview }),
        saveAdminSchoolStatus: (schoolId, payload) => saveAdminSchoolStatus(schoolId, payload, { preview }),
        saveAdminCampusAccountStatus: (userId, isActive) => saveAdminCampusAccountStatus(userId, isActive, { preview }),
        resetAdminCampusPassword: (userId) => resetAdminCampusPassword(userId, { preview }),
        dispatchAdminNotification: (kind, params) => dispatchAdminNotification(kind, params, { preview }),
        saveAdminGovernanceSettings: (payload, options = {}) => saveAdminGovernanceSettings(payload, { ...options, preview }),
        reviewAdminGovernanceRequest: (requestId, payload) => reviewAdminGovernanceRequest(requestId, payload, { preview }),
        runAdminRetentionCleanup: (payload, options = {}) => runAdminRetentionCleanup(payload, { ...options, preview }),
    }
}
