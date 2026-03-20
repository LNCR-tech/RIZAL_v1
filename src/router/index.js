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
    isSchoolItSession,
    sessionNeedsFaceRegistration,
} from '@/composables/useDashboardSession.js'
import { hasPrivilegedPendingFace, needsStoredPasswordChange } from '@/services/localAuth.js'

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
        path: '/privileged-face',
        name: 'PrivilegedFaceVerification',
        component: () => import('@/views/auth/PrivilegedFaceVerificationView.vue'),
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
            allowPrivilegedPendingFace: true,
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
        path: '/privileged',
        name: 'PrivilegedDashboard',
        component: () => import('@/views/dashboard/PrivilegedComingSoonView.vue'),
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },
    {
        path: '/workspace',
        component: AppLayout,
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
        children: [
            {
                path: '',
                name: 'SchoolItHome',
                component: () => import('@/views/dashboard/SchoolItHomeView.vue'),
            },
            {
                path: 'users',
                name: 'SchoolItUsers',
                component: () => import('@/views/dashboard/SchoolItUsersView.vue'),
            },
            {
                path: 'users/import',
                name: 'SchoolItImportStudents',
                component: () => import('@/views/dashboard/SchoolItImportStudentsView.vue'),
            },
            {
                path: 'users/department/:departmentId',
                name: 'SchoolItDepartmentPrograms',
                component: () => import('@/views/dashboard/SchoolItDepartmentProgramsView.vue'),
            },
            {
                path: 'users/department/:departmentId/program/:programId',
                name: 'SchoolItProgramStudents',
                component: () => import('@/views/dashboard/SchoolItProgramStudentsView.vue'),
            },
            {
                path: 'student-council',
                name: 'SchoolItStudentCouncil',
                component: () => import('@/views/dashboard/SchoolItStudentCouncilView.vue'),
            },
            {
                path: 'schedule',
                name: 'SchoolItSchedule',
                component: () => import('@/views/dashboard/WorkspacePlaceholderView.vue'),
                props: {
                    title: 'Schedule',
                    description: 'School IT schedule controls will live here once the event operations UI is ready.',
                },
            },
            {
                path: 'settings',
                name: 'SchoolItSettings',
                component: () => import('@/views/dashboard/SchoolItSettingsView.vue'),
            },
            {
                path: 'profile',
                name: 'SchoolItProfile',
                component: ProfileView,
            },
        ],
    },
    {
        path: '/exposed/workspace',
        component: AppLayout,
        children: [
            {
                path: '',
                name: 'PreviewSchoolItHome',
                component: () => import('@/views/dashboard/SchoolItHomeView.vue'),
                props: { preview: true },
            },
            {
                path: 'users',
                name: 'PreviewSchoolItUsers',
                component: () => import('@/views/dashboard/SchoolItUsersView.vue'),
                props: { preview: true },
            },
            {
                path: 'users/import',
                name: 'PreviewSchoolItImportStudents',
                component: () => import('@/views/dashboard/SchoolItImportStudentsView.vue'),
                props: { preview: true },
            },
            {
                path: 'users/department/:departmentId',
                name: 'PreviewSchoolItDepartmentPrograms',
                component: () => import('@/views/dashboard/SchoolItDepartmentProgramsView.vue'),
                props: { preview: true },
            },
            {
                path: 'users/department/:departmentId/program/:programId',
                name: 'PreviewSchoolItProgramStudents',
                component: () => import('@/views/dashboard/SchoolItProgramStudentsView.vue'),
                props: { preview: true },
            },
            {
                path: 'student-council',
                name: 'PreviewSchoolItStudentCouncil',
                component: () => import('@/views/dashboard/SchoolItStudentCouncilView.vue'),
                props: { preview: true },
            },
            {
                path: 'schedule',
                name: 'PreviewSchoolItSchedule',
                component: () => import('@/views/dashboard/WorkspacePlaceholderView.vue'),
                props: {
                    title: 'Schedule',
                    description: 'School IT schedule controls will live here once the event operations UI is ready.',
                },
            },
            {
                path: 'settings',
                name: 'PreviewSchoolItSettings',
                component: () => import('@/views/dashboard/SchoolItSettingsView.vue'),
                props: { preview: true },
            },
            {
                path: 'profile',
                name: 'PreviewSchoolItProfile',
                component: () => import('@/views/dashboard/WorkspacePlaceholderView.vue'),
                props: {
                    title: 'Profile',
                    description: 'Profile controls will stay on the real authenticated workspace once the backend is available again.',
                },
            },
        ],
    },
    {
        path: '/exposed/dashboard',
        component: AppLayout,
        children: [
            {
                path: '',
                name: 'PreviewHome',
                component: HomeView,
                props: { preview: true },
            },
            {
                path: 'schedule',
                name: 'PreviewDashboardSchedule',
                component: ScheduleView,
                props: { preview: true },
            },
            {
                path: 'schedule/:id',
                name: 'PreviewEventDetail',
                component: EventDetailView,
                props: { preview: true },
            },
            {
                path: 'analytics',
                name: 'PreviewDashboardAnalytics',
                component: AnalyticsView,
                props: { preview: true },
            },
            {
                path: 'profile',
                name: 'PreviewDashboardProfile',
                component: ProfileView,
                props: { preview: true },
            },
        ],
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
    const privilegedPendingFace = hasPrivilegedPendingFace()

    if (to.meta.requiresAuth && !isAuthenticated) {
        return { name: 'Login' }
    }

    if (to.name === 'PrivilegedFaceVerification') {
        if (!isAuthenticated) {
            return { name: 'Login' }
        }

        if (privilegedPendingFace) {
            return true
        }

        if (mustChangePassword) {
            return { name: 'ChangePassword' }
        }

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

    if (isAuthenticated && privilegedPendingFace) {
        if (to.meta.allowPrivilegedPendingFace) {
            return true
        }
        return { name: 'PrivilegedFaceVerification' }
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
            const schoolItSession = isSchoolItSession()
            const needsFaceRegistration = sessionNeedsFaceRegistration()
            if (needsFaceRegistration && !to.meta.allowWithoutFaceEnrollment) {
                return { name: 'FaceRegistration' }
            }
            if (!needsFaceRegistration && to.name === 'FaceRegistration') {
                return defaultRoute
            }
            if (schoolItSession && to.name === 'PrivilegedDashboard') {
                return defaultRoute
            }
            if (schoolItSession && to.path.startsWith('/dashboard')) {
                return defaultRoute
            }
            if (!schoolItSession && to.path.startsWith('/workspace')) {
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
