import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { loginForAccessToken, resolveApiBaseUrl } from '@/services/backendApi.js'
import {
    clearDashboardSession,
    initializeDashboardSession,
} from '@/composables/useDashboardSession.js'

export function useAuth() {
    const router = useRouter()
    const isLoading = ref(false)
    const error = ref(null)

    async function login(email, password) {
        isLoading.value = true
        error.value = null

        try {
            if (!email || !password) {
                throw new Error('Please enter your email and password.')
            }

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

            await initializeDashboardSession(true)
            router.push({ name: 'Home' })
        } catch (err) {
            clearDashboardSession()
            error.value = err?.message || 'Login failed. Please try again.'
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
