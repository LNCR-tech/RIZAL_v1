<template>
  <div class="analytics-page">
    <!-- ─── MOBILE ─── -->
    <div class="analytics-mobile md:hidden">
      <header class="analytics-mobile__header">
        <button
          class="analytics-mobile__profile"
          type="button"
          aria-label="Open profile"
          @click="router.push({ name: preview ? 'PreviewDashboardProfile' : 'Profile' })"
        >
          <img
            v-if="avatarUrl"
            :src="avatarUrl"
            :alt="displayName"
            class="analytics-mobile__avatar"
          >
          <span v-else class="analytics-mobile__avatar analytics-mobile__avatar--fallback">{{ initials }}</span>

          <span class="analytics-mobile__profile-copy">
            <span class="analytics-mobile__eyebrow">Welcome Back</span>
            <span class="analytics-mobile__name">{{ displayName }}</span>
          </span>
        </button>

        <button class="analytics-mobile__notify relative" type="button" aria-label="Notifications" @click="toggleNotifications">
          <Bell :size="18" :stroke-width="2" />
          <span
            v-if="unreadNotifCount > 0"
            class="absolute top-[14px] right-[14px] w-2 h-2 rounded-full"
            style="background: #FF5A36;"
          />
        </button>
      </header>

      <div class="analytics-mobile__body">
        <h1 class="analytics-mobile__title">Dashboard</h1>

        <!-- Semester Progress -->
        <SemesterProgressBar :events="schoolEvents" />

        <!-- Attendance Hero -->
        <AttendanceStatusHero
          :attended="attendedCount"
          :missed="missedCount"
          :excused="excusedCount"
        />

        <!-- Quick Stats -->
        <QuickStatsRow
          :total-events="totalMarkedEvents"
          :attended="attendedCount"
          :missed="missedCount"
          :excused="excusedCount"
        />

        <!-- SSG vs SG -->
        <SsgSgBreakdown
          :ssg-attended="ssgAttended"
          :ssg-total="ssgTotal"
          :sg-attended="sgAttended"
          :sg-total="sgTotal"
        />

        <!-- Upcoming Events -->
        <UpcomingEventsSection
          :events="upcomingEvents"
          @select-event="openEvent"
          @view-all="navigateToSchedule"
        />

        <!-- Attendance History -->
        <AttendanceHistoryTable :records="historyRecords" :per-page="5" />
      </div>
    </div>

    <!-- ─── DESKTOP ─── -->
    <div class="analytics-desktop hidden md:block">
      <TopBar
        class="dashboard-enter dashboard-enter--1"
        :user="activeUser"
        :unread-count="activeUnreadAnnouncements"
        @toggle-notifications="showNotifications = !showNotifications"
      />

      <section class="analytics-desktop__content">
        <header class="analytics-desktop__hero dashboard-enter dashboard-enter--2">
          <div>
            <p class="analytics-desktop__eyebrow">Attendance Dashboard</p>
            <h1 class="analytics-desktop__title">Analytics</h1>
          </div>
          <p class="analytics-desktop__subtitle">
            Track your attendance compliance, event breakdowns, and semester progress.
          </p>
        </header>

        <!-- Semester Progress Bar -->
        <SemesterProgressBar
          class="dashboard-enter dashboard-enter--3"
          :events="schoolEvents"
        />

        <!-- Hero + Quick Stats — side by side -->
        <div class="analytics-desktop__top-grid dashboard-enter dashboard-enter--3">
          <AttendanceStatusHero
            :attended="attendedCount"
            :missed="missedCount"
            :excused="excusedCount"
          />

          <div class="analytics-desktop__right-stack">
            <QuickStatsRow
              :total-events="totalMarkedEvents"
              :attended="attendedCount"
              :missed="missedCount"
              :excused="excusedCount"
            />

            <SsgSgBreakdown
              :ssg-attended="ssgAttended"
              :ssg-total="ssgTotal"
              :sg-attended="sgAttended"
              :sg-total="sgTotal"
            />
          </div>
        </div>

        <!-- Upcoming + History — two column -->
        <div class="analytics-desktop__bottom-grid dashboard-enter dashboard-enter--4">
          <UpcomingEventsSection
            :events="upcomingEvents"
            @select-event="openEvent"
            @view-all="navigateToSchedule"
          />

          <AttendanceHistoryTable :records="historyRecords" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell } from 'lucide-vue-next'
import TopBar from '@/components/dashboard/TopBar.vue'
import SemesterProgressBar from '@/components/dashboard/SemesterProgressBar.vue'
import AttendanceStatusHero from '@/components/dashboard/AttendanceStatusHero.vue'
import QuickStatsRow from '@/components/dashboard/QuickStatsRow.vue'
import SsgSgBreakdown from '@/components/dashboard/SsgSgBreakdown.vue'
import UpcomingEventsSection from '@/components/dashboard/UpcomingEventsSection.vue'
import AttendanceHistoryTable from '@/components/dashboard/AttendanceHistoryTable.vue'

import { surfaceAuraLogo } from '@/config/theme.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { studentDashboardPreviewData } from '@/data/studentDashboardPreview.js'
import {
  getAttendanceRecordTimestamp,
  getLatestAttendanceRecordsByEvent,
  isValidCompletedAttendanceRecord,
  resolveAttendanceDisplayStatus,
} from '@/services/attendanceFlow.js'
import { primeLocationAccess } from '@/services/devicePermissions.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()

import { useNotifications } from '@/composables/useNotifications.js'
const { toggleNotifications, unreadNotifCount } = useNotifications()

const {
  currentUser,
  events,
  attendanceRecords,
  unreadAnnouncements,
  hasAttendanceForEvent,
  hasOpenAttendanceForEvent,
} = useDashboardSession()

const activeUser = computed(() => props.preview ? studentDashboardPreviewData.user : currentUser.value)
const activeEvents = computed(() => props.preview ? studentDashboardPreviewData.events : events.value)
const activeAttendanceRecords = computed(() => props.preview ? studentDashboardPreviewData.attendanceRecords : attendanceRecords.value)
const activeUnreadAnnouncements = computed(() => props.preview ? unreadNotifCount.value : Math.max(unreadAnnouncements.value, unreadNotifCount.value))
const activeSchoolSettings = computed(() => props.preview ? studentDashboardPreviewData.schoolSettings : null)

usePreviewTheme(() => props.preview, activeSchoolSettings)

// --- User display ---
const displayName = computed(() => {
  const parts = [activeUser.value?.first_name, activeUser.value?.middle_name, activeUser.value?.last_name].filter(Boolean)
  return parts.join(' ') || activeUser.value?.email?.split('@')[0] || 'User Full Name'
})
const initials = computed(() => {
  const parts = displayName.value.split(' ').filter(Boolean)
  return parts.length >= 2 ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase() : displayName.value.slice(0, 2).toUpperCase()
})
const avatarUrl = computed(() => activeUser.value?.student_profile?.photo_url || activeUser.value?.student_profile?.avatar_url || activeUser.value?.avatar_url || '')

// --- Events ---
const schoolEvents = computed(() => {
  const schoolId = Number(activeUser.value?.school_id)
  return activeEvents.value.filter((event) => !Number.isFinite(schoolId) || Number(event?.school_id) === schoolId)
})

const eventLookup = computed(() => Object.fromEntries(schoolEvents.value.map((e) => [Number(e.id), e])))

function normalizeStatus(status) {
  const s = String(status || '').toLowerCase()
  return s === 'done' ? 'completed' : s
}

const upcomingEvents = computed(() =>
  schoolEvents.value.filter((e) => {
    const status = normalizeStatus(e.status)
    return status === 'upcoming' || status === 'ongoing'
  })
)

// --- Attendance analytics ---
const latestAttendanceRecords = computed(() => getLatestAttendanceRecordsByEvent(activeAttendanceRecords.value))

function resolveAnalyticsStatus(record) {
  const displayStatus = resolveAttendanceDisplayStatus(record)
  if (displayStatus === 'absent') return 'absent'
  if (displayStatus === 'late' && isValidCompletedAttendanceRecord(record)) return 'late'
  if (displayStatus === 'present' && isValidCompletedAttendanceRecord(record)) return 'present'
  if (displayStatus === 'excused') return 'excused'
  if (displayStatus === 'incomplete') return 'incomplete'
  return 'unmarked'
}

const attendanceSummary = computed(() => latestAttendanceRecords.value.reduce((acc, record) => {
  const status = resolveAnalyticsStatus(record)
  if (status === 'present') acc.present += 1
  if (status === 'late') acc.late += 1
  if (status === 'absent') acc.absent += 1
  if (status === 'excused') acc.excused += 1
  return acc
}, { present: 0, late: 0, absent: 0, excused: 0 }))

const attendedCount = computed(() => attendanceSummary.value.present + attendanceSummary.value.late)
const missedCount = computed(() => attendanceSummary.value.absent)
const excusedCount = computed(() => attendanceSummary.value.excused)
const totalMarkedEvents = computed(() => attendedCount.value + missedCount.value + excusedCount.value)

// --- SSG vs SG ---
function resolveOrgKey(event) {
  const scope = String(event?.scope_label || '').toLowerCase()
  if (scope.includes('campus')) return 'ssg'
  return 'sg'
}

const ssgSgAttendance = computed(() => {
  const result = { ssgAttended: 0, ssgTotal: 0, sgAttended: 0, sgTotal: 0 }
  latestAttendanceRecords.value.forEach((record) => {
    const eventId = Number(record?.event_id)
    const event = eventLookup.value[eventId]
    const status = resolveAnalyticsStatus(record)
    const org = resolveOrgKey(event)
    const isAttended = status === 'present' || status === 'late'

    if (org === 'ssg') {
      result.ssgTotal += 1
      if (isAttended) result.ssgAttended += 1
    } else {
      result.sgTotal += 1
      if (isAttended) result.sgAttended += 1
    }
  })
  return result
})

const ssgAttended = computed(() => ssgSgAttendance.value.ssgAttended)
const ssgTotal = computed(() => ssgSgAttendance.value.ssgTotal)
const sgAttended = computed(() => ssgSgAttendance.value.sgAttended)
const sgTotal = computed(() => ssgSgAttendance.value.sgTotal)

// --- Attendance history ---
const historyRecords = computed(() => {
  return latestAttendanceRecords.value
    .map((record) => {
      const eventId = Number(record?.event_id)
      const event = eventLookup.value[eventId]
      const status = resolveAnalyticsStatus(record)
      const timestamp = getAttendanceRecordTimestamp(record)

      return {
        key: `${eventId}-${timestamp}`,
        date: timestamp ? new Date(timestamp).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' }) : '—',
        eventName: event?.name || `Event ${eventId}`,
        orgKey: resolveOrgKey(event),
        orgLabel: resolveOrgKey(event) === 'ssg' ? 'SSG' : 'SG',
        statusKey: ['present', 'absent', 'late', 'excused'].includes(status) ? status : 'unknown',
        statusLabel: status === 'present' ? 'Present' : status === 'absent' ? 'Absent' : status === 'late' ? 'Late' : status === 'excused' ? 'Excused' : 'Unknown',
        timestamp,
      }
    })
    .sort((a, b) => b.timestamp - a.timestamp)
})

// --- Navigation ---
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

function navigateToSchedule() {
  router.push(props.preview ? '/exposed/dashboard/schedule' : '/dashboard/schedule')
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   PAGE ROOT
   ═══════════════════════════════════════════════════════════ */
.analytics-page {
  min-height: 100vh;
  padding: 0;
}

/* ═══════════════════════════════════════════════════════════
   MOBILE LAYOUT
   ═══════════════════════════════════════════════════════════ */
.analytics-mobile {
  padding: 34px 28px 120px;
  font-family: 'Manrope', sans-serif;
}

.analytics-mobile__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.analytics-mobile__profile {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-height: 52px;
  padding: 6px 16px 6px 6px;
  border: none;
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
}

.analytics-mobile__avatar {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  flex-shrink: 0;
  object-fit: cover;
}

.analytics-mobile__avatar--fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-nav);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
}

.analytics-mobile__profile-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.05;
}

.analytics-mobile__eyebrow {
  font-size: 10px;
  font-weight: 500;
  color: var(--color-text-muted);
}

.analytics-mobile__name {
  margin-top: 2px;
  font-size: 14px;
  font-weight: 600;
}

.analytics-mobile__notify {
  width: 52px;
  height: 52px;
  border: none;
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.analytics-mobile__body {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 30px;
}

.analytics-mobile__title {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--color-text-primary);
}

/* ═══════════════════════════════════════════════════════════
   DESKTOP LAYOUT
   ═══════════════════════════════════════════════════════════ */
.analytics-desktop {
  min-height: 100vh;
  padding: 36px 36px 40px;
}

.analytics-desktop__content {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.analytics-desktop__hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}

.analytics-desktop__eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.analytics-desktop__title {
  margin: 0;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.06em;
  color: var(--color-text-primary);
}

.analytics-desktop__subtitle {
  max-width: 420px;
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

/* Top grid: Hero (left) + Stats/SSG-SG (right) */
.analytics-desktop__top-grid {
  display: grid;
  grid-template-columns: minmax(380px, 1fr) minmax(0, 1.2fr);
  gap: 24px;
  align-items: start;
}

.analytics-desktop__right-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Bottom grid: Upcoming (left) + History (right) */
.analytics-desktop__bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
}

/* Large screen refinement */
@media (min-width: 1200px) {
  .analytics-desktop__top-grid {
    grid-template-columns: minmax(420px, 0.85fr) minmax(0, 1.15fr);
  }
}

/* Collapse to single column on small desktops */
@media (min-width: 768px) and (max-width: 1024px) {
  .analytics-desktop__top-grid {
    grid-template-columns: 1fr;
  }

  .analytics-desktop__bottom-grid {
    grid-template-columns: 1fr;
  }
}
</style>
