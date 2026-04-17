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
import { hasPrivilegedPendingFace, needsStoredPasswordChange } from '@/services/localAuth.js'
import { setNavigationPending } from '@/services/navigationState.js'
import { createPlatformView } from '@/router/platformView.js'

const AppLayout = () => import('@/layouts/AppLayout.vue')
const authView = (viewName) => createPlatformView(`auth/${viewName}`)
const dashboardView = (viewName) => createPlatformView(`dashboard/${viewName}`)
const toolsView = (viewName) => createPlatformView(`tools/${viewName}`)

const HomeView = dashboardView('HomeView')
const ProfileView = dashboardView('ProfileView')
const ScheduleView = dashboardView('ScheduleView')
const EventDetailView = dashboardView('EventDetailView')
const AttendanceView = dashboardView('AttendanceView')
const AnalyticsView = dashboardView('AnalyticsView')
const AdminWorkspaceView = dashboardView('AdminWorkspaceView')
const WorkspacePlaceholderView = dashboardView('WorkspacePlaceholderView')
const PrivilegedComingSoonView = dashboardView('PrivilegedComingSoonView')
const ProfileSecurityView = dashboardView('ProfileSecurityView')
const ProfileFaceUpdateView = dashboardView('ProfileFaceUpdateView')
const PrivilegedFaceVerificationView = authView('PrivilegedFaceVerificationView')
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
const GovernanceWorkspaceView = dashboardView('GovernanceWorkspaceView')
const SgEventsView = dashboardView('SgEventsView')
const SgCreateUnitView = dashboardView('SgCreateUnitView')
const SanctionsDashboardView = dashboardView('SanctionsDashboardView')
const SanctionedStudentsListView = dashboardView('SanctionedStudentsListView')
const StudentSanctionDetailView = dashboardView('StudentSanctionDetailView')
const StudentSanctionsView = dashboardView('StudentSanctionsView')
const GatherWelcomeView = dashboardView('GatherWelcomeView')
const GatherAttendanceView = dashboardView('GatherAttendanceView')
const AuraChatView = dashboardView('AuraChatView')

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
        path: '/privileged/face',
        name: 'PrivilegedFaceVerification',
        component: PrivilegedFaceVerificationView,
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
            {
                path: 'chat',
                name: 'AdminAuraChat',
                component: AuraChatView,
                meta: {
                    hideMobileNav: true,
                },
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
            {
                path: 'chat',
                name: 'PreviewAdminAuraChat',
                component: AuraChatView,
                meta: {
                    hideMobileNav: true,
                },
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
            {
                path: 'chat',
                name: 'SchoolItAuraChat',
                component: AuraChatView,
                meta: {
                    hideMobileNav: true,
                },
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
            {
                path: 'chat',
                name: 'PreviewSchoolItAuraChat',
                component: AuraChatView,
                meta: {
                    hideMobileNav: true,
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
                path: 'schedule/:id/attendance',
                name: 'PreviewAttendance',
                component: AttendanceView,
                props: { preview: true },
                meta: {
                    hideMobileNav: true,
                },
            },
            {
                path: 'analytics',
                name: 'PreviewDashboardAnalytics',
                component: AnalyticsView,
                props: { preview: true },
            },
            {
                path: 'sanctions',
                name: 'PreviewDashboardSanctions',
                component: StudentSanctionsView,
                props: { preview: true },
            },
            {
                path: 'profile',
                name: 'PreviewDashboardProfile',
                component: ProfileView,
                props: { preview: true },
            },
            {
                path: 'chat',
                name: 'PreviewDashboardAuraChat',
                component: AuraChatView,
                meta: {
                    hideMobileNav: true,
                },
            },
            {
                path: 'gather',
                name: 'PreviewGatherWelcome',
                component: GatherWelcomeView,
                props: { preview: true },
                meta: {
                    hideMobileNav: true,
                },
            },
            {
                path: 'gather/attendance',
                name: 'PreviewGatherAttendance',
                component: GatherAttendanceView,
                props: { preview: true },
                meta: {
                    hideMobileNav: true,
                },
            },
        ],
    },
    // Governance Dashboard routes
    {
        path: '/governance',
        component: AppLayout,
        meta: {
            requiresAuth: true,
            allowWithoutFaceEnrollment: true,
            primaryNavContext: 'governance',
            workspaceContext: 'governance',
        },
        children: [
            {
                path: '',
                name: 'SgDashboard',
                component: GovernanceWorkspaceView,
                props: { section: 'overview' },
            },
            {
                path: 'students',
                name: 'SgStudents',
                component: GovernanceWorkspaceView,
                props: { section: 'students' },
            },
            {
                path: 'admin',
                name: 'SgAdmin',
                component: GovernanceWorkspaceView,
                props: { section: 'governance' },
            },
            {
                path: 'members',
                redirect: { name: 'SgAdmin' },
            },
            {
                path: 'events',
                name: 'SgEvents',
                component: SgEventsView,
            },
            {
                path: 'announcements',
                redirect: { name: 'SgEvents' },
            },
            {
                path: 'attendance',
                redirect: { name: 'SgEvents' },
            },
            {
                path: 'create-unit',
                name: 'SgCreateUnit',
                component: SgCreateUnitView,
            },
            {
                path: 'events/sanctions',
                name: 'SgSanctionsDashboard',
                component: SanctionsDashboardView,
            },
            {
                path: 'events/:eventId/sanctions/students',
                name: 'SgSanctionedStudents',
                component: SanctionedStudentsListView,
            },
            {
                path: 'events/:eventId/sanctions/students/:userId',
                name: 'SgStudentSanctionDetail',
                component: StudentSanctionDetailView,
            },
            {
                path: 'events/:id',
                name: 'SgEventDetail',
                component: EventDetailView,
            },
            {
                path: 'chat',
                name: 'SgAuraChat',
                component: AuraChatView,
                meta: {
                    hideMobileNav: true,
                },
            },
            {
                path: 'gather',
                name: 'SgGatherWelcome',
                component: GatherWelcomeView,
                meta: {
                    hideMobileNav: true,
                },
            },
            {
                path: 'gather/attendance',
                name: 'SgGatherAttendance',
                component: GatherAttendanceView,
                meta: {
                    hideMobileNav: true,
                },
            },
        ],
    },
    {
        path: '/exposed/governance',
        component: AppLayout,
        meta: {
            primaryNavContext: 'governance_preview',
            workspaceContext: 'governance_preview',
        },
        children: [
            {
                path: '',
                name: 'PreviewSgDashboard',
                component: GovernanceWorkspaceView,
                props: { preview: true, section: 'overview' },
            },
            {
                path: 'students',
                name: 'PreviewSgStudents',
                component: GovernanceWorkspaceView,
                props: { preview: true, section: 'students' },
            },
            {
                path: 'admin',
                name: 'PreviewSgAdmin',
                component: GovernanceWorkspaceView,
                props: { preview: true, section: 'governance' },
            },
            {
                path: 'members',
                redirect: { name: 'PreviewSgAdmin' },
            },
            {
                path: 'events',
                name: 'PreviewSgEvents',
                component: SgEventsView,
                props: { preview: true },
            },
            {
                path: 'announcements',
                redirect: { name: 'PreviewSgEvents' },
            },
            {
                path: 'attendance',
                redirect: { name: 'PreviewSgEvents' },
            },
            {
                path: 'create-unit',
                name: 'PreviewSgCreateUnit',
                component: SgCreateUnitView,
                props: { preview: true },
            },
            {
                path: 'events/sanctions',
                name: 'PreviewSgSanctionsDashboard',
                component: SanctionsDashboardView,
                props: { preview: true },
            },
            {
                path: 'events/:eventId/sanctions/students',
                name: 'PreviewSgSanctionedStudents',
                component: SanctionedStudentsListView,
                props: { preview: true },
            },
            {
                path: 'events/:eventId/sanctions/students/:userId',
                name: 'PreviewSgStudentSanctionDetail',
                component: StudentSanctionDetailView,
                props: { preview: true },
            },
            {
                path: 'events/:id',
                name: 'PreviewSgEventDetail',
                component: EventDetailView,
                props: { preview: true },
            },
            {
                path: 'chat',
                name: 'PreviewSgAuraChat',
                component: AuraChatView,
                meta: {
                    hideMobileNav: true,
                },
            },
            {
                path: 'gather',
                name: 'PreviewSgGatherWelcome',
                component: GatherWelcomeView,
                props: { preview: true },
                meta: {
                    hideMobileNav: true,
                },
            },
            {
                path: 'gather/attendance',
                name: 'PreviewSgGatherAttendance',
                component: GatherAttendanceView,
                props: { preview: true },
                meta: {
                    hideMobileNav: true,
                },
            },
        ],
    },
    {
        path: '/sg',
        redirect: '/governance'
    },
    {
        path: '/sg/:pathMatch(.*)*',
        redirect: (to) => {
            const rawPathMatch = to.params.pathMatch
            const pathSegments = Array.isArray(rawPathMatch)
                ? rawPathMatch
                : rawPathMatch
                    ? [rawPathMatch]
                    : []

            return pathSegments.length > 0
                ? `/governance/${pathSegments.join('/')}`
                : '/governance'
        }
    },
    {
        path: '/exposed/sg',
        redirect: '/exposed/governance'
    },
    {
        path: '/exposed/sg/:pathMatch(.*)*',
        redirect: (to) => {
            const rawPathMatch = to.params.pathMatch
            const pathSegments = Array.isArray(rawPathMatch)
                ? rawPathMatch
                : rawPathMatch
                    ? [rawPathMatch]
                    : []

            return pathSegments.length > 0
                ? `/exposed/governance/${pathSegments.join('/')}`
                : '/exposed/governance'
        }
    },
    // Redirect /exposed/dashboard/sg to /exposed/governance
    {
        path: '/exposed/dashboard/sg',
        redirect: '/exposed/governance'
    },
    {
        path: '/exposed/dashboard/sg/:pathMatch(.*)*',
        redirect: (to) => {
            const rawPathMatch = to.params.pathMatch
            const pathSegments = Array.isArray(rawPathMatch)
                ? rawPathMatch
                : rawPathMatch
                    ? [rawPathMatch]
                    : []

            return pathSegments.length > 0
                ? `/exposed/governance/${pathSegments.join('/')}`
                : '/exposed/governance'
        }
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
                meta: {
                    hideMobileNav: true,
                },
            },
            {
                path: 'analytics',
                name: 'Analytics',
                component: AnalyticsView,
            },
            {
                path: 'sanctions',
                name: 'DashboardSanctions',
                component: StudentSanctionsView,
            },
            {
                path: 'chat',
                name: 'DashboardAuraChat',
                component: AuraChatView,
                meta: {
                    hideMobileNav: true,
                },
            },
            {
                path: 'gather',
                name: 'GatherWelcome',
                component: GatherWelcomeView,
                meta: {
                    hideMobileNav: true,
                },
            },
            {
                path: 'gather/attendance',
                name: 'GatherAttendance',
                component: GatherAttendanceView,
                meta: {
                    hideMobileNav: true,
                },
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
    const pendingPrivilegedFace = hasPrivilegedPendingFace()

    if (to.meta.requiresAuth && !isAuthenticated) {
        return { name: 'Login' }
    }

    if (isAuthenticated && mustChangePassword && to.name !== 'ChangePassword') {
        return { name: 'ChangePassword' }
    }

    if (
        isAuthenticated &&
        pendingPrivilegedFace &&
        !mustChangePassword &&
        to.name !== 'PrivilegedFaceVerification'
    ) {
        return { name: 'PrivilegedFaceVerification' }
    }

    if (to.name === 'ChangePassword') {
        if (!isAuthenticated) {
            return { name: 'Login' }
        }

        if (!mustChangePassword) {
            if (pendingPrivilegedFace) {
                return { name: 'PrivilegedFaceVerification' }
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

        return true
    }

    if (to.name === 'PrivilegedFaceVerification') {
        if (!isAuthenticated) {
            return { name: 'Login' }
        }

        if (mustChangePassword) {
            return { name: 'ChangePassword' }
        }

        if (!pendingPrivilegedFace) {
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
        if (pendingPrivilegedFace) {
            return { name: 'PrivilegedFaceVerification' }
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

    if (to.meta.requiresAuth && isAuthenticated) {
        if (pendingPrivilegedFace) {
            return true
        }
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
