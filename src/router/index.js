import { createRouter, createWebHistory } from 'vue-router'
import {
    clearDashboardSession,
    getDefaultAuthenticatedRoute,
    hasSessionToken,
    initializeDashboardSession,
    isAdminSession,
    isPrivilegedSession,
    isSchoolItSession,
    sessionNeedsFaceRegistration,
} from '@/composables/useDashboardSession.js'
import { hasPendingFaceVerification, hasPrivilegedPendingFace, needsStoredPasswordChange } from '@/services/localAuth.js'
import { setNavigationPending } from '@/services/navigationState.js'
import { createPlatformView } from '@/router/platformView.js'

const AppLayout = () => import('@/layouts/AppLayout.vue')
const authView = (viewName) => createPlatformView(`auth/${viewName}`)
const dashboardView = (viewName) => createPlatformView(`dashboard/${viewName}`)
const reusableView = (viewName) => createPlatformView(viewName, {
  desktopPath: `desktop/desktopReusable/${viewName}`,
  mobilePath: `mobile/dashboard/${viewName}`,
})
const toolsView = (viewName) => createPlatformView(`tools/${viewName}`)

const HomeView = reusableView('HomeView')
const ProfileView = reusableView('ProfileView')
const ScheduleView = reusableView('ScheduleView')
const EventDetailView = reusableView('EventDetailView')
const AttendanceView = reusableView('AttendanceView')
const AnalyticsView = reusableView('AnalyticsView')
const AdminWorkspaceView = dashboardView('AdminWorkspaceView')
const WorkspacePlaceholderView = reusableView('WorkspacePlaceholderView')
const PrivilegedComingSoonView = reusableView('PrivilegedComingSoonView')
const ProfileSecurityView = reusableView('ProfileSecurityView')
const ProfileFaceUpdateView = reusableView('ProfileFaceUpdateView')
const SchoolItHomeView = dashboardView('SchoolItHomeView')
const SchoolItUsersView = dashboardView('SchoolItUsersView')
const SchoolItImportStudentsView = dashboardView('SchoolItImportStudentsView')
const SchoolItDepartmentProgramsView = dashboardView('SchoolItDepartmentProgramsView')
const SchoolItProgramStudentsView = dashboardView('SchoolItProgramStudentsView')
const SchoolItUnassignedStudentsView = dashboardView('SchoolItUnassignedStudentsView')
const SchoolItStudentCouncilView = dashboardView('SchoolItStudentCouncilView')
const SchoolItScheduleView = dashboardView('SchoolItScheduleView')
const SchoolItAttendanceMonitorView = dashboardView('SchoolItAttendanceMonitorView')
const SchoolItEventReportsView = dashboardView('SchoolItEventReportsView')
const SchoolItSettingsView = dashboardView('SchoolItSettingsView')
const SchoolItAccountsView = dashboardView('SchoolItAccountsView')
const SgDashboardView = dashboardView('SgDashboardView')
const SgMembersView = dashboardView('SgMembersView')
const SgStudentsView = dashboardView('SgStudentsView')
const SgAnnouncementsView = dashboardView('SgAnnouncementsView')
const SgCreateUnitView = dashboardView('SgCreateUnitView')
const SgEventsView = dashboardView('SgEventsView')
const SgAttendanceView = dashboardView('SgAttendanceView')

const routes = [
    // Auth routes (no layout)
    {
        path: '/',
        name: 'Login',
        component: authView('LoginView'),
        meta: { requiresGuest: true },
    },
    {
        path: '/quick-attendance',
        name: 'QuickAttendance',
        component: authView('QuickAttendanceView'),
    },
    {
        path: '/api-lab',
        name: 'ApiLab',
        component: toolsView('ApiLabView'),
    },
    {
        path: '/face-registration',
        name: 'FaceRegistration',
        component: authView('FaceRegistrationView'),
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },
    {
        path: '/change-password',
        name: 'ChangePassword',
        component: authView('ChangePasswordView'),
        props: { flow: 'required' },
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },
    {
        path: '/privileged-face',
        name: 'PrivilegedFaceVerification',
        component: authView('PrivilegedFaceVerificationView'),
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
            allowPrivilegedPendingFace: true,
        },
    },
    {
        path: '/profile/security',
        name: 'ProfileSecurity',
        component: ProfileSecurityView,
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },
    {
        path: '/profile/security/password',
        name: 'ProfileSecurityPassword',
        component: authView('ChangePasswordView'),
        props: { flow: 'settings' },
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },
    {
        path: '/profile/security/face',
        name: 'ProfileSecurityFace',
        component: ProfileFaceUpdateView,
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },
    {
        path: '/privileged',
        name: 'PrivilegedDashboard',
        component: PrivilegedComingSoonView,
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
        },
    },
    {
        path: '/admin',
        component: AppLayout,
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
            primaryNavContext: 'admin',
            workspaceContext: 'admin',
        },
        children: [
            {
                path: '',
                name: 'AdminHome',
                component: AdminWorkspaceView,
                props: { section: 'overview' },
            },
            {
                path: 'schools',
                name: 'AdminSchools',
                component: AdminWorkspaceView,
                props: { section: 'schools' },
            },
            {
                path: 'accounts',
                name: 'AdminAccounts',
                component: AdminWorkspaceView,
                props: { section: 'accounts' },
            },
            {
                path: 'oversight',
                name: 'AdminOversight',
                component: AdminWorkspaceView,
                props: { section: 'oversight' },
            },
            {
                path: 'profile',
                name: 'AdminProfile',
                component: AdminWorkspaceView,
                props: { section: 'profile' },
            },
        ],
    },
    {
        path: '/exposed/admin',
        component: AppLayout,
        meta: {
            primaryNavContext: 'admin_preview',
            workspaceContext: 'admin_preview',
        },
        children: [
            {
                path: '',
                name: 'PreviewAdminHome',
                component: AdminWorkspaceView,
                props: { preview: true, section: 'overview' },
            },
            {
                path: 'schools',
                name: 'PreviewAdminSchools',
                component: AdminWorkspaceView,
                props: { preview: true, section: 'schools' },
            },
            {
                path: 'accounts',
                name: 'PreviewAdminAccounts',
                component: AdminWorkspaceView,
                props: { preview: true, section: 'accounts' },
            },
            {
                path: 'oversight',
                name: 'PreviewAdminOversight',
                component: AdminWorkspaceView,
                props: { preview: true, section: 'oversight' },
            },
            {
                path: 'profile',
                name: 'PreviewAdminProfile',
                component: AdminWorkspaceView,
                props: { preview: true, section: 'profile' },
            },
        ],
    },
    {
        path: '/workspace',
        component: AppLayout,
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
            primaryNavContext: 'workspace',
            workspaceContext: 'workspace',
        },
        children: [
            {
                path: '',
                name: 'SchoolItHome',
                component: SchoolItHomeView,
            },
            {
                path: 'users',
                name: 'SchoolItUsers',
                component: SchoolItUsersView,
            },
            {
                path: 'users/import',
                name: 'SchoolItImportStudents',
                component: SchoolItImportStudentsView,
            },
            {
                path: 'users/department/:departmentId',
                name: 'SchoolItDepartmentPrograms',
                component: SchoolItDepartmentProgramsView,
            },
            {
                path: 'users/department/:departmentId/program/:programId',
                name: 'SchoolItProgramStudents',
                component: SchoolItProgramStudentsView,
            },
            {
                path: 'users/unassigned',
                name: 'SchoolItUnassignedStudents',
                component: SchoolItUnassignedStudentsView,
            },
            {
                path: 'accounts',
                name: 'SchoolItAccounts',
                component: SchoolItAccountsView,
            },
            {
                path: 'student-council',
                name: 'SchoolItStudentCouncil',
                component: SchoolItStudentCouncilView,
            },
            {
                path: 'schedule',
                name: 'SchoolItSchedule',
                component: SchoolItScheduleView,
                props: {
                    title: 'Schedule',
                    description: 'School IT schedule controls will live here once the event operations UI is ready.',
                },
            },
            {
                path: 'schedule/monitor',
                name: 'SchoolItAttendanceMonitor',
                component: SchoolItAttendanceMonitorView,
            },
            {
                path: 'schedule/reports',
                name: 'SchoolItEventReports',
                component: SchoolItEventReportsView,
            },
            {
                path: 'schedule/:id',
                name: 'SchoolItEventDetail',
                component: EventDetailView,
            },
            {
                path: 'settings',
                name: 'SchoolItSettings',
                component: SchoolItSettingsView,
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
        meta: {
            primaryNavContext: 'workspace_preview',
            workspaceContext: 'workspace_preview',
        },
        children: [
            {
                path: '',
                name: 'PreviewSchoolItHome',
                component: SchoolItHomeView,
                props: { preview: true },
            },
            {
                path: 'users',
                name: 'PreviewSchoolItUsers',
                component: SchoolItUsersView,
                props: { preview: true },
            },
            {
                path: 'users/import',
                name: 'PreviewSchoolItImportStudents',
                component: SchoolItImportStudentsView,
                props: { preview: true },
            },
            {
                path: 'users/department/:departmentId',
                name: 'PreviewSchoolItDepartmentPrograms',
                component: SchoolItDepartmentProgramsView,
                props: { preview: true },
            },
            {
                path: 'users/department/:departmentId/program/:programId',
                name: 'PreviewSchoolItProgramStudents',
                component: SchoolItProgramStudentsView,
                props: { preview: true },
            },
            {
                path: 'users/unassigned',
                name: 'PreviewSchoolItUnassignedStudents',
                component: SchoolItUnassignedStudentsView,
                props: { preview: true },
            },
            {
                path: 'accounts',
                name: 'PreviewSchoolItAccounts',
                component: SchoolItAccountsView,
                props: { preview: true },
            },
            {
                path: 'student-council',
                name: 'PreviewSchoolItStudentCouncil',
                component: SchoolItStudentCouncilView,
                props: { preview: true },
            },
            {
                path: 'schedule',
                name: 'PreviewSchoolItSchedule',
                component: SchoolItScheduleView,
                props: { preview: true },
            },
            {
                path: 'schedule/monitor',
                name: 'PreviewSchoolItAttendanceMonitor',
                component: SchoolItAttendanceMonitorView,
                props: { preview: true },
            },
            {
                path: 'schedule/reports',
                name: 'PreviewSchoolItEventReports',
                component: SchoolItEventReportsView,
                props: { preview: true },
            },
            {
                path: 'schedule/:id',
                name: 'PreviewSchoolItEventDetail',
                component: EventDetailView,
                props: { preview: true },
            },
            {
                path: 'settings',
                name: 'PreviewSchoolItSettings',
                component: SchoolItSettingsView,
                props: { preview: true },
            },
            {
                path: 'profile',
                name: 'PreviewSchoolItProfile',
                component: WorkspacePlaceholderView,
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
        meta: {
            primaryNavContext: 'dashboard_preview',
            workspaceContext: 'dashboard_preview',
        },
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
    // SG Dashboard routes
    {
        path: '/sg',
        component: AppLayout,
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
            primaryNavContext: 'dashboard',
            workspaceContext: 'sg',
        },
        children: [
            {
                path: '',
                name: 'SgDashboard',
                component: SgDashboardView,
            },
            {
                path: 'members',
                name: 'SgMembers',
                component: SgMembersView,
            },
            {
                path: 'students',
                name: 'SgStudents',
                component: SgStudentsView,
            },
            {
                path: 'announcements',
                name: 'SgAnnouncements',
                component: SgAnnouncementsView,
            },
            {
                path: 'create-unit',
                name: 'SgCreateUnit',
                component: SgCreateUnitView,
            },
            {
                path: 'events',
                name: 'SgEvents',
                component: SgEventsView,
            },
            {
                path: 'events/:id',
                name: 'SgEventDetail',
                component: EventDetailView,
            },
            {
                path: 'attendance',
                name: 'SgAttendance',
                component: SgAttendanceView,
            },
        ],
    },
    {
        path: '/exposed/sg',
        component: AppLayout,
        meta: {
            primaryNavContext: 'dashboard_preview',
            workspaceContext: 'sg_preview',
        },
        children: [
            {
                path: '',
                name: 'PreviewSgDashboard',
                component: SgDashboardView,
                props: { preview: true },
            },
        ],
    },
    // Student dashboard routes (wrapped in AppLayout)
    {
        path: '/dashboard',
        component: AppLayout,
        meta: {
            requiresAuth: true,
            primaryNavContext: 'dashboard',
            workspaceContext: 'dashboard',
        },
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
    setNavigationPending(true)
    const isAuthenticated = hasSessionToken()
    const mustChangePassword = needsStoredPasswordChange()
    const pendingFaceVerification = hasPendingFaceVerification()

    if (to.meta.requiresAuth && !isAuthenticated) {
        return { name: 'Login' }
    }

    if (to.name === 'PrivilegedFaceVerification') {
        if (!isAuthenticated) {
            return { name: 'Login' }
        }

        if (pendingFaceVerification) {
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

    if (isAuthenticated && pendingFaceVerification) {
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
            const adminSession = isAdminSession()
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
            if (adminSession && (to.path.startsWith('/dashboard') || to.path.startsWith('/workspace') || to.name === 'PrivilegedDashboard')) {
                return defaultRoute
            }
            if (!adminSession && to.path.startsWith('/admin')) {
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

router.afterEach(() => {
    setNavigationPending(false)
})

router.onError(() => {
    setNavigationPending(false)
})

export default router
