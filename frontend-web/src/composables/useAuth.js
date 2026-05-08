import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { loginForAccessToken, resolveApiBaseUrl } from '@/services/backendApi.js'
import {
    clearDashboardSession,
    getDefaultAuthenticatedRoute,
    initializeDashboardSession,
    sessionUsesLimitedMode,
    sessionNeedsFaceRegistration,
} from '@/composables/useDashboardSession.js'
import { hasPrivilegedPendingFace, sanitizeToken, storeAuthMeta } from '@/services/localAuth.js'
import { markCurrentRuntimeSession, readStoredSessionToken } from '@/services/sessionPersistence.js'
import { clearSessionExpiredNotice } from '@/services/sessionExpiry.js'

function normalizeRoleKey(role = '') {
    const normalizedRole = String(role || '')
        .trim()
        .toLowerCase()
        .replace(/_/g, '-')

    return normalizedRole === 'campus-admin' ? 'school-it' : normalizedRole
}

function resolveRouteFromRoles(roles = []) {
    const roleKeys = Array.isArray(roles)
        ? roles.map((role) => normalizeRoleKey(role))
        : []

    if (roleKeys.includes('school-it')) {
        return { name: 'SchoolItHome' }
    }
    if (roleKeys.includes('admin')) {
        return { name: 'AdminHome' }
    }
    if (roleKeys.includes('ssg') || roleKeys.includes('sg') || roleKeys.includes('org')) {
        return { name: 'SgDashboard' }
    }
    return { name: 'Home' }
}

function resolveFallbackRoute(authMeta = null) {
    if (Array.isArray(authMeta?.roles) && authMeta.roles.length > 0) {
        return resolveRouteFromRoles(authMeta.roles)
    }

    try {
        const storedRoles = JSON.parse(localStorage.getItem('aura_user_roles') || '[]')
        return resolveRouteFromRoles(storedRoles)
    } catch {
        return resolveRouteFromRoles([])
    }
}

export function useAuth() {
    const router = useRouter()
    const isLoading = ref(false)
    const error = ref(null)

    async function login(email, password, options = {}) {
        if (isLoading.value) {
            return options.preventRedirect ? null : undefined
        }

        isLoading.value = true
        error.value = null

        try {
            if (!email || !password) {
                throw new Error('Please enter your email and password.')
            }

            clearSessionExpiredNotice()

            const apiBaseUrl = resolveApiBaseUrl()
            const tokenPayload = await loginForAccessToken(apiBaseUrl, {
                username: email,
                password,
            })

            const accessToken = sanitizeToken(tokenPayload?.access_token)
            if (!accessToken) {
                throw new Error('The API did not return an access token.')
            }

            localStorage.setItem('aura_token', accessToken)
            localStorage.setItem('aura_user_roles', JSON.stringify(tokenPayload?.roles ?? []))
            const authMeta = storeAuthMeta(tokenPayload)
            markCurrentRuntimeSession()
            const persistedToken = sanitizeToken(readStoredSessionToken())
            if (persistedToken !== accessToken) {
                throw new Error('Authenticated, but the session token was not persisted.')
            }

            if (hasPrivilegedPendingFace(authMeta)) {
                const nextRoute = { name: 'PrivilegedFaceVerification' }
                if (options.preventRedirect) return nextRoute
                router.push(nextRoute)
                return
            }

            if (authMeta.mustChangePassword) {
                const nextRoute = { name: 'ChangePassword' }
                if (options.preventRedirect) return nextRoute
                router.push(nextRoute)
                return
            }

            let initializedSession = null
            try {
                initializedSession = await initializeDashboardSession(true)
            } catch {
                initializedSession = null
            }

            let nextRoute = sessionNeedsFaceRegistration()
                ? { name: 'FaceRegistration' }
                : getDefaultAuthenticatedRoute()
            if (!initializedSession?.user || sessionUsesLimitedMode()) {
                nextRoute = resolveFallbackRoute(authMeta)
            }

            if (options.preventRedirect) return nextRoute
            await router.push(nextRoute)
            
        } catch (err) {
            const stillAuthenticated = Boolean(sanitizeToken(readStoredSessionToken()))
            if (!stillAuthenticated) {
                clearDashboardSession()
            }
            error.value = err?.message || 'Login failed. Please try again.'
            if (options.preventRedirect) {
                return stillAuthenticated
                    ? resolveFallbackRoute()
                    : null
            }
        } finally {
            isLoading.value = false
        }
    }

    function logout() {
        clearDashboardSession()
        router.push({ name: 'Login' })
    }

    return { login, logout, isLoading, error }
}
