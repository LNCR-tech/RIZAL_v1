<template>
  <div class="analytics-page">
    <TopBar
      class="dashboard-enter dashboard-enter--1"
      :user="activeUser"
      :unread-count="activeUnreadAnnouncements"
      @toggle-notifications="toggleNotifications"
    />

    <StudentAnalyticsDashboard
      class="dashboard-enter dashboard-enter--2"
      :user="activeUser"
      :events="schoolEvents"
      :records="activeAttendanceRecords"
      :school-name="resolvedSchoolName"
      :school-logo-candidates="schoolLogoCandidates"
      :api-base-url="apiBaseUrl"
      @open-event="openEvent"
      @announcement-click="toggleNotifications"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import TopBar from '@/components/dashboard/TopBar.vue'
import StudentAnalyticsDashboard from '@/components/dashboard/StudentAnalyticsDashboard.vue'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useNotifications } from '@/composables/useNotifications.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { useStoredAuthMeta } from '@/composables/useStoredAuthMeta.js'
import { studentDashboardPreviewData } from '@/data/studentDashboardPreview.js'
import { primeLocationAccess } from '@/services/devicePermissions.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()
const authMeta = useStoredAuthMeta()
const { toggleNotifications, unreadNotifCount } = useNotifications()

const {
  currentUser,
  schoolSettings,
  events,
  attendanceRecords,
  unreadAnnouncements,
  hasAttendanceForEvent,
  hasOpenAttendanceForEvent,
  apiBaseUrl,
} = useDashboardSession()

const activeUser = computed(() => props.preview ? studentDashboardPreviewData.user : currentUser.value)
const activeSchoolSettings = computed(() => props.preview ? studentDashboardPreviewData.schoolSettings : schoolSettings.value)
const activeEvents = computed(() => props.preview ? studentDashboardPreviewData.events : events.value)
const activeAttendanceRecords = computed(() => props.preview ? studentDashboardPreviewData.attendanceRecords : attendanceRecords.value)
const activeUnreadAnnouncements = computed(() => (
  props.preview
    ? unreadNotifCount.value
    : Math.max(unreadAnnouncements.value, unreadNotifCount.value)
))

usePreviewTheme(() => props.preview, activeSchoolSettings)

const resolvedSchoolName = computed(() => (
  activeSchoolSettings.value?.school_name ||
  activeUser.value?.school_name ||
  authMeta.value?.schoolName ||
  'University Name'
))

const schoolLogoCandidates = computed(() => [
  activeSchoolSettings.value?.logo_url,
  activeUser.value?.school_logo_url,
  activeUser.value?.school?.logo_url,
  authMeta.value?.logoUrl,
].filter(Boolean))

const schoolEvents = computed(() => {
  const schoolId = Number(activeUser.value?.school_id)
  return activeEvents.value.filter((event) => !Number.isFinite(schoolId) || Number(event?.school_id) === schoolId)
})

function normalizeStatus(status) {
  const normalized = String(status || '').toLowerCase()
  return normalized === 'done' ? 'completed' : normalized
}

function openEvent(event) {
  if (!event?.id) return

  const normalizedEventId = Number(event.id)
  const shouldRouteToAttendance = (
    hasOpenAttendanceForEvent(normalizedEventId)
    || (normalizeStatus(event.status) === 'ongoing' && !hasAttendanceForEvent(normalizedEventId))
  )

  if (!props.preview && shouldRouteToAttendance) {
    void primeLocationAccess()
    router.push(`/dashboard/schedule/${event.id}/attendance`)
    return
  }

  router.push(props.preview ? `/exposed/dashboard/schedule/${event.id}` : `/dashboard/schedule/${event.id}`)
}
</script>

<style scoped>
.analytics-page {
  min-height: 100dvh;
  padding:
    calc(14px + env(safe-area-inset-top))
    14px
    calc(104px + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-x: hidden;
}

.analytics-page :deep(header) {
  padding-top: 4px;
  padding-bottom: 0;
}

@media (min-width: 768px) {
  .analytics-page {
    min-height: 100vh;
    padding: 36px 36px 40px;
    gap: 28px;
  }

  .analytics-page :deep(header) {
    padding-top: 24px;
    padding-bottom: 8px;
  }
}
</style>
