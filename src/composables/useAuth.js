import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api.js'

export function useAuth() {
    const router = useRouter()
    const isLoading = ref(false)
    const error = ref(null)

    async function login(email, password) {
        isLoading.value = true
        error.value = null

        // 🟢 DEVELOPMENT BYPASS: Support for Super Admin mock login
        if (email === 'superadmin@aura.edu' && password === 'admin123') {
            const mockToken = 'aura_dev_token_superadmin'
            const mockRoles = [{ role: { id: 1, name: 'super_admin' } }]
            localStorage.setItem('aura_token', mockToken)
            localStorage.setItem('aura_user_roles', JSON.stringify(mockRoles))
            router.push({ name: 'SuperAdminDashboard' })
            isLoading.value = false
            return
        }

        // 🟡 DEVELOPMENT BYPASS: Allow new campus admins to login
        const savedCampuses = localStorage.getItem('aura_campuses')
        if (savedCampuses) {
            try {
                const campuses = JSON.parse(savedCampuses)
                const targetCampus = campuses.find(c => c.admin?.email === email && c.admin?.password === password)
                
                if (targetCampus) {
                    const mockToken = `aura_dev_token_${targetCampus.id}`
                    const mockRoles = [{ role: { id: 2, name: 'admin' } }]
                    
                    // Set impersonation data so they see their own campus
                    localStorage.setItem('aura_token', mockToken)
                    localStorage.setItem('aura_user_roles', JSON.stringify(mockRoles))
                    localStorage.setItem('aura_impersonate_school_id', targetCampus.id)
                    localStorage.setItem('aura_impersonate_school_name', targetCampus.name)
                    localStorage.setItem('aura_impersonate_school_logo', targetCampus.logo)
                    
                    router.push({ name: 'Home' })
                    isLoading.value = false
                    return
                }
            } catch (e) {
                console.error('Bypass check error:', e)
            }
        }

        try {
            const response = await api.post('/login', { email, password })
            
            if (response.data && response.data.access_token) {
                localStorage.setItem('aura_token', response.data.access_token)
                
                // Store useful user info
                if (response.data.roles) {
                    localStorage.setItem('aura_user_roles', JSON.stringify(response.data.roles))
                }
                
                // Redirect based on role
                const roles = response.data.roles || []
                if (roles.some(r => r?.role?.name === 'super_admin' || r?.role?.name === 'superadmin')) {
                    router.push({ name: 'SuperAdminDashboard' })
                } else {
                    router.push({ name: 'Home' })
                }
            } else {
                throw new Error('Login failed. No token received.')
            }
        } catch (err) {
            console.error('Login error:', err)
            error.value = err.response?.data?.detail || err.message || 'Login failed. Please check your credentials.'
        } finally {
            isLoading.value = false
        }
    }

    function logout() {
        localStorage.removeItem('aura_token')
        localStorage.removeItem('aura_user_roles')
        router.push({ name: 'Login' })
    }

    return { login, logout, isLoading, error }
}
