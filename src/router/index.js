import { createRouter, createWebHistory } from 'vue-router'
import {
    clearDashboardSession,
    hasSessionToken,
    initializeDashboardSession,
    sessionNeedsFaceRegistration,
} from '@/composables/useDashboardSession.js'

const routes = [
    // Auth routes (no layout)
    {
        path: '/',
        name: 'Login',
        component: () => import('@/views/auth/LoginView.vue'),
        meta: { requiresGuest: true },
    },
    {
        path: '/api-lab',
        name: 'ApiLab',
        component: () => import('@/views/tools/ApiLabView.vue'),
    },
    {
        path: '/face-registration',
        name: 'FaceRegistration',
        component: () => import('@/views/auth/FaceRegistrationView.vue'),
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
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
                path: 'schedule/:id',
                name: 'EventDetail',
                component: () => import('@/views/dashboard/EventDetailView.vue'),
            },
            {
                path: 'schedule/:id/attendance',
                name: 'Attendance',
                component: () => import('@/views/dashboard/AttendanceView.vue'),
            },
            {
                path: 'analytics',
                name: 'Analytics',
                component: () => import('@/views/dashboard/AnalyticsView.vue'),
            },
        ],
    },
]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
    scrollBehavior() {
        return { left: 0, top: 0 }
    },
})

// Navigation guard
router.beforeEach(async (to) => {
    const isAuthenticated = hasSessionToken()

    if (to.meta.requiresAuth && !isAuthenticated) {
        return { name: 'Login' }
    }

    if (to.meta.requiresGuest && isAuthenticated) {
        try {
            await initializeDashboardSession()
            return sessionNeedsFaceRegistration()
                ? { name: 'FaceRegistration' }
                : { name: 'Home' }
        } catch {
            clearDashboardSession()
            return { name: 'Login' }
        }
    }

    if (to.meta.requiresAuth && isAuthenticated) {
        try {
            await initializeDashboardSession()
            const needsFaceRegistration = sessionNeedsFaceRegistration()
            if (needsFaceRegistration && !to.meta.allowWithoutFaceEnrollment) {
                return { name: 'FaceRegistration' }
            }
            if (!needsFaceRegistration && to.name === 'FaceRegistration') {
                return { name: 'Home' }
            }
        } catch {
            clearDashboardSession()
            return { name: 'Login' }
        }
    }

    return true
})

export default router
