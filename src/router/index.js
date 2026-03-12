import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    // Auth routes (no layout)
    {
        path: '/',
        name: 'Login',
        component: () => import('@/views/auth/LoginView.vue'),
        meta: { requiresGuest: true },
    },

    // Student dashboard routes (wrapped in AppLayout)
    {
        path: '/dashboard',
        component: () => import('@/layouts/AppLayout.vue'),
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                name: 'Home',
                component: () => import('@/views/dashboard/HomeView.vue'),
            },
            {
                path: 'profile',
                name: 'Profile',
                component: () => import('@/views/dashboard/ProfileView.vue'),
            },
            {
                path: 'schedule',
                name: 'Schedule',
                component: () => import('@/views/dashboard/ScheduleView.vue'),
            },
            {
                path: 'analytics',
                name: 'Analytics',
                component: () => import('@/views/dashboard/AnalyticsView.vue'),
            },
        ],
    },

    // Super Admin routes (wrapped in AppLayout)
    {
        path: '/super-admin',
        component: () => import('@/layouts/AppLayout.vue'),
        meta: { requiresAuth: true, role: 'super_admin' },
        children: [
            {
                path: '',
                name: 'SuperAdminDashboard',
                component: () => import('@/views/super-admin/DashboardView.vue'),
            },
            {
                path: 'campuses',
                name: 'CampusManagement',
                component: () => import('@/views/super-admin/CampusManagementView.vue'),
            },
        ],
    },
]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
})

// Navigation guard
router.beforeEach((to, _from, next) => {
    const isAuthenticated = !!localStorage.getItem('aura_token')
    const rolesJSON = localStorage.getItem('aura_user_roles')
    let roles = []
    try {
        roles = rolesJSON ? JSON.parse(rolesJSON) : []
    } catch (e) {
        roles = []
    }

    const isSuperAdmin = (roles || []).some(r => r?.role?.name === 'super_admin' || r?.role?.name === 'superadmin')

    if (to.meta.requiresAuth && !isAuthenticated) {
        next({ name: 'Login' })
    } else if (to.meta.requiresGuest && isAuthenticated) {
        // Redirect based on role
        if (isSuperAdmin) {
            next({ name: 'SuperAdminDashboard' })
        } else {
            next({ name: 'Home' })
        }
    } else if (to.meta.role === 'super_admin' && !isSuperAdmin) {
        // Accessing super admin page but not a super admin
        next({ name: 'Home' })
    } else {
        next()
    }
})

export default router
