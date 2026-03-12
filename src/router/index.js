import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    // Redirect root to Super Admin
    {
        path: '/',
        redirect: '/super-admin'
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

// Simplified Navigation guard for direct access
router.beforeEach((to, _from, next) => {
    // Ensure we have a mock token for development if login is removed
    if (!localStorage.getItem('aura_token')) {
        localStorage.setItem('aura_token', 'aura_dev_bypass_token')
        localStorage.setItem('aura_user_roles', JSON.stringify([{ role: { id: 1, name: 'super_admin' } }]))
    }
    
    next()
})

export default router
