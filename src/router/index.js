import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import HomeView from '@/views/dashboard/HomeView.vue'
import ProfileView from '@/views/dashboard/ProfileView.vue'
import ScheduleView from '@/views/dashboard/ScheduleView.vue'
import EventDetailView from '@/views/dashboard/EventDetailView.vue'
import AttendanceView from '@/views/dashboard/AttendanceView.vue'
import AnalyticsView from '@/views/dashboard/AnalyticsView.vue'
import {
    clearDashboardSession,
    getDefaultAuthenticatedRoute,
    hasSessionToken,
    initializeDashboardSession,
    isPrivilegedSession,
    sessionNeedsFaceRegistration,
} from '@/composables/useDashboardSession.js'
import { needsStoredPasswordChange } from '@/services/localAuth.js'

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
    {
        path: '/change-password',
        name: 'ChangePassword',
        component: () => import('@/views/auth/ChangePasswordView.vue'),
        props: { flow: 'required' },
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },
    {
        path: '/profile/security',
        name: 'ProfileSecurity',
        component: () => import('@/views/dashboard/ProfileSecurityView.vue'),
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },
    {
        path: '/profile/security/password',
        name: 'ProfileSecurityPassword',
        component: () => import('@/views/auth/ChangePasswordView.vue'),
        props: { flow: 'settings' },
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },
    {
        path: '/profile/security/face',
        name: 'ProfileSecurityFace',
        component: () => import('@/views/dashboard/ProfileFaceUpdateView.vue'),
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },
    {
        path: '/workspace',
        name: 'PrivilegedDashboard',
        component: () => import('@/views/dashboard/PrivilegedComingSoonView.vue'),
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },

    // Student dashboard routes (wrapped in AppLayout)
    {
        path: '/dashboard',
        component: AppLayout,
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                name: 'Home',
                component: HomeView,
            },
            {
                path: 'profile',
                name: 'Profile',
                component: ProfileView,
            },
            {
                path: 'schedule',
                name: 'Schedule',
                component: ScheduleView,
            },
            {
                path: 'schedule/:id',
                name: 'EventDetail',
                component: EventDetailView,
            },
            {
                path: 'schedule/:id/attendance',
                name: 'Attendance',
                component: AttendanceView,
            },
            {
                path: 'analytics',
                name: 'Analytics',
                component: AnalyticsView,
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
    const mustChangePassword = needsStoredPasswordChange()

    if (to.meta.requiresAuth && !isAuthenticated) {
        return { name: 'Login' }
    }

    if (isAuthenticated && mustChangePassword && to.name !== 'ChangePassword') {
        return { name: 'ChangePassword' }
    }

    if (to.name === 'ChangePassword') {
        if (!isAuthenticated) {
            return { name: 'Login' }
        }

        if (!mustChangePassword) {
            try {
                await initializeDashboardSession()
                return sessionNeedsFaceRegistration()
                    ? { name: 'FaceRegistration' }
                    : getDefaultAuthenticatedRoute()
            } catch {
                clearDashboardSession()
                return { name: 'Login' }
            }
        }

        return true
    }

    if (to.meta.requiresGuest && isAuthenticated) {
        try {
            await initializeDashboardSession()
            return sessionNeedsFaceRegistration()
                ? { name: 'FaceRegistration' }
                : getDefaultAuthenticatedRoute()
        } catch {
            clearDashboardSession()
            return { name: 'Login' }
        }
    }

    if (to.meta.requiresAuth && isAuthenticated) {
        try {
            await initializeDashboardSession()
            const defaultRoute = getDefaultAuthenticatedRoute()
            const privilegedSession = isPrivilegedSession()
            const needsFaceRegistration = sessionNeedsFaceRegistration()
            if (needsFaceRegistration && !to.meta.allowWithoutFaceEnrollment) {
                return { name: 'FaceRegistration' }
            }
            if (!needsFaceRegistration && to.name === 'FaceRegistration') {
                return defaultRoute
            }
            if (privilegedSession && to.path.startsWith('/dashboard')) {
                return defaultRoute
            }
            if (!privilegedSession && to.name === 'PrivilegedDashboard') {
                return defaultRoute
            }
        } catch {
            clearDashboardSession()
            return { name: 'Login' }
        }
    }

    return true
})

export default router
