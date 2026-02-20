import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../views/LandingPage.vue'
import DashboardLayout from '../layouts/DashboardLayout.vue'
import { getCurrentUser } from '../services/api.js'
import * as mockDb from '../mock/db.js'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: LandingPage
        },

        // Student Routes (standalone, no dashboard layout)
        {
            path: '/student/create',
            name: 'student-create',
            component: () => import('../views/student/CreateAccount.vue')
        },

        // Student Routes with Dashboard Layout
        {
            path: '/student',
            component: DashboardLayout,
            children: [
                {
                    path: 'profile',
                    name: 'student-profile',
                    meta: { requiresFaceScan: true },
                    component: () => import('../views/student/StudentProfile.vue')
                },
                {
                    path: 'events',
                    name: 'student-events',
                    meta: { requiresFaceScan: true },
                    component: () => import('../views/student/StudentEvents.vue')
                },
                {
                    path: 'attendance',
                    name: 'student-attendance',
                    meta: { requiresFaceScan: true },
                    component: () => import('../views/student/StudentAttendance.vue')
                },
                {
                    path: 'announcements',
                    name: 'student-announcements',
                    meta: { requiresFaceScan: true },
                    component: () => import('../views/student/StudentAnnouncements.vue')
                },
                {
                    path: 'pending',
                    name: 'student-pending',
                    meta: { pendingOnly: true },
                    component: () => import('../views/student/QRPending.vue')
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

// -----------------------------------------------------------
// STUDENT FACE SCAN GUARD
// -----------------------------------------------------------
// Controls student dashboard access based on faceScanRegistered status:
// - faceScanRegistered=true  → full dashboard (profile/events/announcements)
// - faceScanRegistered=false → QR pending page only
// Admin and SG routes are completely unaffected.
router.beforeEach((to, from, next) => {
    // Only apply to student routes with our meta flags
    if (!to.meta.requiresFaceScan && !to.meta.pendingOnly) {
        return next();
    }

    // Check face scan status from stored user or mock DB
    const currentUser = getCurrentUser();
    let isFaceScanRegistered = false;

    if (currentUser) {
        // Check mock DB for latest status (stays in sync if updated)
        const dbUser = mockDb.users.find(u => u.id === currentUser.id);
        isFaceScanRegistered = dbUser ? dbUser.faceScanRegistered : false;
    }

    if (to.meta.requiresFaceScan && !isFaceScanRegistered) {
        // Not registered → redirect to QR pending page
        return next({ name: 'student-pending' });
    }

    if (to.meta.pendingOnly && isFaceScanRegistered) {
        // Already registered → redirect to profile (skip pending)
        return next({ name: 'student-profile' });
    }

    next();
});

export default router
