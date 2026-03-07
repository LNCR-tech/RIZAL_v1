import { createRouter, createWebHashHistory } from 'vue-router'
import LandingPage from '../views/LandingPage.vue'
import DashboardLayout from '../layouts/DashboardLayout.vue'

const router = createRouter({
    history: createWebHashHistory(),
    routes: [
        {
            path: '/',
            name: 'home',
            component: LandingPage
        },



        // Student Routes with Dashboard Layout
        {
            path: '/student',
            component: DashboardLayout,
            redirect: '/student/dashboard',
            children: [
                {
                    path: 'dashboard',
                    name: 'student-dashboard',
                    component: () => import('../views/student/StudentDashboard.vue')
                },
                {
                    path: 'profile',
                    name: 'student-profile',
                    component: () => import('../views/student/StudentProfile.vue')
                },
                {
                    path: 'events',
                    name: 'student-events',
                    component: () => import('../views/student/StudentEvents.vue')
                },
                {
                    path: 'attendance',
                    name: 'student-attendance',
                    component: () => import('../views/student/StudentAttendance.vue')
                },
                {
                    path: 'announcements',
                    name: 'student-announcements',
                    component: () => import('../views/student/StudentAnnouncements.vue')
                },

            ]
        },

        // SG Routes
        {
            path: '/sg',
            component: DashboardLayout,
            children: [
                {
                    path: 'approvals',
                    name: 'sg-approvals',
                    component: () => import('../views/sg/AccountApprovals.vue')
                },
            ]
        },

        // Admin Routes
        {
            path: '/admin',
            component: DashboardLayout,
            children: [
                {
                    path: 'dashboard',
                    name: 'admin-dashboard',
                    component: () => import('../views/admin/AdminDashboard.vue')
                },
                {
                    path: 'profile',
                    name: 'admin-profile',
                    component: () => import('../views/admin/Profile.vue')
                },
                {
                    path: 'events',
                    name: 'admin-events',
                    component: () => import('../views/admin/Events.vue')
                },
                {
                    path: 'colleges',
                    name: 'admin-colleges',
                    component: () => import('../views/admin/Colleges.vue')
                },
                {
                    path: 'students',
                    name: 'admin-students',
                    component: () => import('../views/admin/Students.vue')
                },
                {
                    path: 'logs',
                    name: 'admin-logs',
                    component: () => import('../views/admin/LoggedInRecords.vue')
                },
                {
                    path: 'attendance',
                    name: 'admin-attendance',
                    component: () => import('../views/admin/Attendance.vue')
                },
                {
                    path: 'create-account',
                    name: 'admin-create-account',
                    component: () => import('../views/admin/AdminCreateAccount.vue')
                },
                // Redirect /admin/users to /admin/students (backwards compatibility)
                {
                    path: 'users',
                    redirect: '/admin/students'
                },
            ]
        },
    ]
})

// Recover once from stale/lost lazy chunks (common after app update in installed WebViews).
const CHUNK_RETRY_KEY = 'aura_chunk_retry_once'
router.onError((error, to) => {
    const message = error?.message || ''
    const isChunkError = /Failed to fetch dynamically imported module|Importing a module script failed|Loading chunk/i.test(message)
    if (!isChunkError) return

    const hasRetried = sessionStorage.getItem(CHUNK_RETRY_KEY) === '1'
    if (hasRetried) {
        sessionStorage.removeItem(CHUNK_RETRY_KEY)
        console.error('Chunk load failed after retry:', error)
        return
    }

    sessionStorage.setItem(CHUNK_RETRY_KEY, '1')
    if (to?.fullPath) {
        window.location.hash = `#${to.fullPath}`
    }
    window.location.reload()
})

router.afterEach(() => {
    sessionStorage.removeItem(CHUNK_RETRY_KEY)
})

export default router
