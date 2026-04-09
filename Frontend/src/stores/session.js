import { defineStore } from 'pinia'
import { useDashboardSession } from '@/composables/useDashboardSession.js'

export const useSessionStore = defineStore('session', () => {
  const session = useDashboardSession()

  return {
    dashboardState: session.dashboardState,
    apiBaseUrl: session.apiBaseUrl,
    token: session.token,
    currentUser: session.currentUser,
    schoolSettings: session.schoolSettings,
    events: session.events,
    attendanceRecords: session.attendanceRecords,
    faceStatus: session.faceStatus,
    limitedMode: session.limitedMode,
    needsFaceRegistration: session.needsFaceRegistration,
    initializeDashboardSession: session.initializeDashboardSession,
    refreshAttendanceRecords: session.refreshAttendanceRecords,
    refreshSchoolSettings: session.refreshSchoolSettings,
    refreshFaceStatus: session.refreshFaceStatus,
    ensureDashboardEvent: session.ensureDashboardEvent,
    saveCurrentUserProfile: session.saveCurrentUserProfile,
    clearDashboardSession: session.clearDashboardSession,
    hasAttendanceForEvent: session.hasAttendanceForEvent,
    hasOpenAttendanceForEvent: session.hasOpenAttendanceForEvent,
    getDefaultAuthenticatedRoute: session.getDefaultAuthenticatedRoute,
  }
})

