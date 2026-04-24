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
import { hasPrivilegedPendingFace, storeAuthMeta } from '@/services/localAuth.js'
import { markCurrentRuntimeSession } from '@/services/sessionPersistence.js'
import { clearSessionExpiredNotice } from '@/services/sessionExpiry.js'

export function useAuth() {
    const router = useRouter()
    const isLoading = ref(false)
    const error = ref(null)

    async function login(email, password, options = {}) {
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

            const accessToken = tokenPayload?.access_token
            if (!accessToken) {
                throw new Error('The API did not return an access token.')
            }

            localStorage.setItem('aura_token', accessToken)
            localStorage.setItem('aura_user_roles', JSON.stringify(tokenPayload?.roles ?? []))
            const authMeta = storeAuthMeta(tokenPayload)
            markCurrentRuntimeSession()

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

            const initializedSession = await initializeDashboardSession(true)
            if (!initializedSession?.user || sessionUsesLimitedMode()) {
                throw new Error('The backend did not return a complete user session. Please try again once the backend is stable.')
            }
            
            const nextRoute = sessionNeedsFaceRegistration()
                ? { name: 'FaceRegistration' }
                : getDefaultAuthenticatedRoute()

            if (options.preventRedirect) return nextRoute
            router.push(nextRoute)
            
        } catch (err) {
            clearDashboardSession()
            error.value = err?.message || 'Login failed. Please try again.'
            if (options.preventRedirect) return null
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
