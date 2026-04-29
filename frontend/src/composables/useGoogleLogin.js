import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { loginWithGoogle, resolveApiBaseUrl } from '@/services/backendApi.js'
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

function describeError(err) {
    const detail = err?.payload?.detail
    if (typeof detail === 'string' && detail.trim()) return detail
    if (err?.status === 404) return 'Google account is not registered.'
    if (err?.status === 403) return 'Google login is disabled.'
    if (err?.status === 401) return 'Invalid Google token.'
    return err?.message || 'Google login failed. Please try again.'
}

export function useGoogleLogin() {
    const router = useRouter()
    const isLoading = ref(false)
    const error = ref(null)

    async function loginWithGoogleCredential(idToken, options = {}) {
        isLoading.value = true
        error.value = null
        try {
            if (!idToken) throw new Error('Missing Google credential.')
            clearSessionExpiredNotice()

            const apiBaseUrl = resolveApiBaseUrl()
            const tokenPayload = await loginWithGoogle(apiBaseUrl, idToken)
            const accessToken = tokenPayload?.access_token
            if (!accessToken) throw new Error('The API did not return an access token.')

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
                throw new Error('The backend did not return a complete user session.')
            }
            const nextRoute = sessionNeedsFaceRegistration()
                ? { name: 'FaceRegistration' }
                : getDefaultAuthenticatedRoute()
            if (options.preventRedirect) return nextRoute
            router.push(nextRoute)
        } catch (err) {
            clearDashboardSession()
            error.value = describeError(err)
            if (options.preventRedirect) return null
        } finally {
            isLoading.value = false
        }
    }

    return { loginWithGoogleCredential, isLoading, error }
}
