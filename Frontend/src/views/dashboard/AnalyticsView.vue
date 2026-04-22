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

    <section class="analytics-reports dashboard-enter dashboard-enter--5">
      <header class="analytics-reports__header">
        <div>
          <p class="analytics-reports__eyebrow">Self-Service Reports</p>
          <h2 class="analytics-reports__title">Attendance Reports</h2>
          <p class="analytics-reports__subtitle">Detailed attendance, trend, event-mix, and compliance reporting for your own account.</p>
        </div>
        <button class="analytics-reports__refresh" type="button" @click="reloadReports">Refresh</button>
      </header>

      <p v-if="reportsError" class="analytics-reports__banner analytics-reports__banner--error">{{ reportsError }}</p>
      <p v-else-if="reportsFallbackNotice" class="analytics-reports__banner">{{ reportsFallbackNotice }}</p>

      <div v-if="isLoadingReports" class="analytics-reports__loading">
        <p>Loading your reports...</p>
      </div>

      <template v-else>
        <div class="analytics-reports__stats">
          <article v-for="card in attendanceReportCards" :key="card.id" class="analytics-reports__stat-card">
            <span>{{ card.label }}</span>
            <strong>{{ card.value }}</strong>
            <small>{{ card.meta }}</small>
          </article>
        </div>

        <div class="analytics-reports__charts">
          <article class="analytics-reports__panel">
            <div class="analytics-reports__panel-head">
              <div>
                <h3>Attendance Status Mix</h3>
                <p>Present, late, absent, and excused status split.</p>
              </div>
            </div>
            <div v-if="attendanceStatusChartData.labels.length" class="analytics-reports__chart">
              <ReportsPieChart :data="attendanceStatusChartData" :options="reportChartOptions.pie" />
            </div>
            <p v-else class="analytics-reports__empty">No attendance status data yet.</p>
          </article>

          <article class="analytics-reports__panel">
            <div class="analytics-reports__panel-head">
              <div>
                <h3>Attendance Trend</h3>
                <p>Monthly attendance movement based on your report history.</p>
              </div>
            </div>
            <div v-if="attendanceTrendChartData.labels.length" class="analytics-reports__chart">
              <ReportsLineChart :data="attendanceTrendChartData" :options="reportChartOptions.line" />
            </div>
            <p v-else class="analytics-reports__empty">More report history is needed for a trend line.</p>
          </article>

          <article class="analytics-reports__panel">
            <div class="analytics-reports__panel-head">
              <div>
                <h3>Event Type Mix</h3>
                <p>Where your attendance is being measured most often.</p>
              </div>
            </div>
            <div v-if="eventTypeChartData.labels.length" class="analytics-reports__chart">
              <ReportsBarChart :data="eventTypeChartData" :options="reportChartOptions.bar" />
            </div>
            <p v-else class="analytics-reports__empty">No event categories are available yet.</p>
          </article>

          <article class="analytics-reports__panel">
            <div class="analytics-reports__panel-head">
              <div>
                <h3>Compliance Status</h3>
                <p>Pending versus complied sanctions tied to your attendance record.</p>
              </div>
            </div>
            <div v-if="sanctionsStatusChartData.labels.length" class="analytics-reports__chart">
              <ReportsPieChart :data="sanctionsStatusChartData" :options="reportChartOptions.pie" />
            </div>
            <p v-else class="analytics-reports__empty">No sanctions are recorded for your account.</p>
          </article>
        </div>

        <div class="analytics-reports__stats analytics-reports__stats--insights">
          <article v-for="card in personalInsightCards" :key="card.id" class="analytics-reports__stat-card analytics-reports__stat-card--soft">
            <span>{{ card.label }}</span>
            <strong>{{ card.value }}</strong>
            <small>{{ card.meta }}</small>
          </article>
        </div>

        <div class="analytics-reports__tables">
          <article class="analytics-reports__panel">
            <div class="analytics-reports__panel-head">
              <div>
                <h3>Attendance Record Log</h3>
                <p>Your latest attendance records from the student report.</p>
              </div>
            </div>
            <div class="analytics-reports__table-wrap">
              <table class="analytics-reports__table">
                <thead><tr><th>Date</th><th>Event</th><th>Status</th><th>Method</th></tr></thead>
                <tbody>
                  <tr v-for="record in recentReportRecords" :key="record.key">
                    <td>{{ record.dateLabel }}</td>
                    <td>{{ record.eventName }}</td>
                    <td>{{ record.statusLabel }}</td>
                    <td>{{ record.methodLabel }}</td>
                  </tr>
                  <tr v-if="!recentReportRecords.length"><td colspan="4" class="analytics-reports__empty-cell">No report records available.</td></tr>
                </tbody>
              </table>
            </div>
          </article>

          <article class="analytics-reports__panel">
            <div class="analytics-reports__panel-head">
              <div>
                <h3>Sanctions Follow-Up</h3>
                <p>Recent sanction records and compliance state.</p>
              </div>
            </div>
            <div class="analytics-reports__table-wrap">
              <table class="analytics-reports__table">
                <thead><tr><th>Event</th><th>Status</th><th>Items</th><th>Updated</th></tr></thead>
                <tbody>
                  <tr v-for="item in recentSanctionRows" :key="item.key">
                    <td>{{ item.eventName }}</td>
                    <td>{{ item.statusLabel }}</td>
                    <td>{{ item.itemCount }}</td>
                    <td>{{ item.updatedLabel }}</td>
                  </tr>
                  <tr v-if="!recentSanctionRows.length"><td colspan="4" class="analytics-reports__empty-cell">No sanction follow-up rows.</td></tr>
                </tbody>
              </table>
            </div>
          </article>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Bell } from 'lucide-vue-next'
import TopBar from '@/components/dashboard/TopBar.vue'
import SemesterProgressBar from '@/components/dashboard/SemesterProgressBar.vue'
import AttendanceStatusHero from '@/components/dashboard/AttendanceStatusHero.vue'
import QuickStatsRow from '@/components/dashboard/QuickStatsRow.vue'
import SsgSgBreakdown from '@/components/dashboard/SsgSgBreakdown.vue'
import UpcomingEventsSection from '@/components/dashboard/UpcomingEventsSection.vue'
import AttendanceHistoryTable from '@/components/dashboard/AttendanceHistoryTable.vue'
import ReportsBarChart from '@/components/reports/ReportsBarChart.vue'
import ReportsLineChart from '@/components/reports/ReportsLineChart.vue'
import ReportsPieChart from '@/components/reports/ReportsPieChart.vue'

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
import {
  getMySanctionsReport,
  getStudentReport,
  getStudentStats,
} from '@/services/reportService.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()
const showNotifications = ref(false)

import { useNotifications } from '@/composables/useNotifications.js'
const { toggleNotifications, unreadNotifCount } = useNotifications()

const {
  apiBaseUrl,
  token,
  currentUser,
  events,
  attendanceRecords,
  unreadAnnouncements,
  initializeDashboardSession,
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

const reportStudent = ref(null)
const reportStudentStats = ref(null)
const reportSanctions = ref([])
const isLoadingReports = ref(false)
const reportsError = ref('')
const reportsFallbackNotice = ref('')

const reportStudentProfileId = computed(() => {
  const profileId = Number(activeUser.value?.student_profile?.id)
  return Number.isFinite(profileId) && profileId > 0 ? profileId : null
})

const reportSummary = computed(() => {
  if (reportStudent.value?.student) return reportStudent.value.student
  return buildDerivedSummary(latestAttendanceRecords.value)
})

const reportAttendanceRecords = computed(() => {
  const rows = Array.isArray(reportStudent.value?.attendance_records) ? reportStudent.value.attendance_records : null
  return rows?.length ? rows : buildDerivedAttendanceRows(latestAttendanceRecords.value)
})

const reportTrendData = computed(() => {
  const rows = Array.isArray(reportStudentStats.value?.trend_data) ? reportStudentStats.value.trend_data : null
  return rows?.length ? rows : buildDerivedTrendData(latestAttendanceRecords.value)
})

const reportEventTypeRows = computed(() => buildEventTypeRows(reportAttendanceRecords.value))
const reportSanctionRows = computed(() => {
  if (Array.isArray(reportSanctions.value) && reportSanctions.value.length) {
    return reportSanctions.value
  }
  return props.preview ? buildPreviewSanctions() : []
})

const attendanceReportCards = computed(() => {
  const summary = reportSummary.value
  const totalEvents = Number(summary?.total_events || 0)
  const attendedEvents = Number(summary?.attended_events || attendedCount.value)
  const absentEvents = Number(summary?.absent_events || missedCount.value)
  const lateEvents = Number(summary?.late_events || 0)
  const excusedEvents = Number(summary?.excused_events || excusedCount.value)
  const attendanceRate = Number(summary?.attendance_rate || (totalEvents > 0 ? (attendedEvents / totalEvents) * 100 : 0))

  return [
    { id: 'report-total', label: 'Tracked Events', value: formatWhole(totalEvents), meta: 'Attendance-marked events in your report scope.' },
    { id: 'report-attended', label: 'Attended', value: formatWhole(attendedEvents), meta: 'Present and late events combined.' },
    { id: 'report-late', label: 'Late', value: formatWhole(lateEvents), meta: 'Late attendance records.' },
    { id: 'report-absent', label: 'Absent', value: formatWhole(absentEvents), meta: 'Absence records in the current report history.' },
    { id: 'report-excused', label: 'Excused', value: formatWhole(excusedEvents), meta: 'Excused attendance records.' },
    { id: 'report-rate', label: 'Attendance Rate', value: `${formatPercentValue(attendanceRate)}%`, meta: 'Attended events divided by tracked events.' },
  ]
})

const attendanceStatusChartData = computed(() => {
  const summary = reportSummary.value
  const present = Math.max(Number(summary?.attended_events || 0) - Number(summary?.late_events || 0), 0)
  const late = Number(summary?.late_events || 0)
  const absent = Number(summary?.absent_events || 0)
  const excused = Number(summary?.excused_events || 0)
  if (present <= 0 && late <= 0 && absent <= 0 && excused <= 0) return { labels: [], datasets: [] }

  return {
    labels: ['Present', 'Late', 'Absent', 'Excused'],
    datasets: [{
      data: [present, late, absent, excused],
      backgroundColor: ['rgba(0,87,184,0.88)', 'rgba(245,158,11,0.88)', 'rgba(239,68,68,0.88)', 'rgba(16,185,129,0.88)'],
      borderWidth: 0,
    }],
  }
})

const attendanceTrendChartData = computed(() => {
  const points = Array.isArray(reportTrendData.value) ? reportTrendData.value : []
  if (!points.length) return { labels: [], datasets: [] }

  return {
    labels: points.map((entry) => String(entry?.label || entry?.period || '')),
    datasets: [
      {
        label: 'Attended',
        data: points.map((entry) => Number(entry?.attended || entry?.attended_count || entry?.present_count || 0) + Number(entry?.late_count || 0)),
        borderColor: 'rgba(0,87,184,0.88)',
        backgroundColor: 'rgba(0,87,184,0.12)',
        tension: 0.32,
      },
      {
        label: 'Absent',
        data: points.map((entry) => Number(entry?.absent || entry?.absent_count || 0)),
        borderColor: 'rgba(239,68,68,0.88)',
        backgroundColor: 'rgba(239,68,68,0.12)',
        tension: 0.32,
      },
    ],
  }
})

const eventTypeChartData = computed(() => {
  const rows = reportEventTypeRows.value
  if (!rows.length) return { labels: [], datasets: [] }
  return {
    labels: rows.map((row) => row.label),
    datasets: [{
      label: 'Events',
      data: rows.map((row) => row.total),
      backgroundColor: ['rgba(0,87,184,0.88)', 'rgba(245,158,11,0.88)', 'rgba(16,185,129,0.88)', 'rgba(15,23,42,0.88)', 'rgba(148,163,184,0.88)'],
      borderRadius: 10,
    }],
  }
})

const sanctionsStatusChartData = computed(() => {
  const pending = reportSanctionRows.value.filter((item) => hasPendingSanctionItems(item)).length
  const complied = Math.max(reportSanctionRows.value.length - pending, 0)
  if (pending <= 0 && complied <= 0) return { labels: [], datasets: [] }

  return {
    labels: ['Pending', 'Complied'],
    datasets: [{
      data: [pending, complied],
      backgroundColor: ['rgba(239,68,68,0.88)', 'rgba(16,185,129,0.88)'],
      borderWidth: 0,
    }],
  }
})

const personalInsightCards = computed(() => {
  const summary = reportSummary.value
  const totalEvents = Number(summary?.total_events || 0)
  const attendanceRate = Number(summary?.attendance_rate || 0)
  const attendedWithoutLate = Math.max(Number(summary?.attended_events || 0) - Number(summary?.late_events || 0), 0)
  const punctualityRate = Number(summary?.attended_events || 0) > 0
    ? (attendedWithoutLate / Number(summary.attended_events || 1)) * 100
    : 0
  const pendingSanctions = reportSanctionRows.value.filter((item) => hasPendingSanctionItems(item)).length
  const riskLabel = attendanceRate < 75 ? 'At Risk' : attendanceRate < 90 ? 'Watch' : 'Healthy'
  const upcomingCount = upcomingEvents.value.length

  return [
    { id: 'risk-level', label: 'Attendance Risk', value: riskLabel, meta: `${formatPercentValue(attendanceRate)}% attendance across ${formatWhole(totalEvents)} tracked events.` },
    { id: 'punctuality', label: 'Punctuality Rate', value: `${formatPercentValue(punctualityRate)}%`, meta: 'Present-only share of your attended events.' },
    { id: 'pending-sanctions', label: 'Pending Compliance', value: formatWhole(pendingSanctions), meta: 'Sanction records still waiting for compliance.' },
    { id: 'upcoming-events', label: 'Upcoming Events', value: formatWhole(upcomingCount), meta: 'Upcoming and ongoing events currently visible in your dashboard.' },
  ]
})

const recentReportRecords = computed(() => {
  return [...reportAttendanceRecords.value]
    .map((record, index) => normalizeReportRecord(record, index))
    .sort((left, right) => right.timestamp - left.timestamp)
    .slice(0, 8)
})

const recentSanctionRows = computed(() => {
  return [...reportSanctionRows.value]
    .map((record, index) => normalizeSanctionRow(record, index))
    .sort((left, right) => right.timestamp - left.timestamp)
    .slice(0, 8)
})

const reportChartOptions = {
  pie: { plugins: { legend: { position: 'bottom' } } },
  line: {
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  },
  bar: {
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  },
}

watch(
  [apiBaseUrl, token, reportStudentProfileId, () => props.preview],
  async ([url, authToken, profileId, preview]) => {
    if (preview) {
      hydratePreviewReports()
      return
    }

    if (!url || !authToken) return
    if (!profileId) {
      hydrateDerivedReports()
      reportsFallbackNotice.value = 'Detailed student report access is not available for this account yet. Showing derived attendance data.'
      return
    }

    await loadReports(url, authToken, profileId)
  },
  { immediate: true }
)

onMounted(async () => {
  if (!props.preview) {
    await initializeDashboardSession().catch(() => null)
  } else {
    hydratePreviewReports()
  }
})

async function loadReports(url, authToken, profileId) {
  isLoadingReports.value = true
  reportsError.value = ''
  reportsFallbackNotice.value = ''

  try {
    const [studentPayload, statsPayload, sanctionsPayload] = await Promise.all([
      getStudentReport(profileId, { baseUrl: url, token: authToken }),
      getStudentStats(profileId, {
        baseUrl: url,
        token: authToken,
        params: { group_by: 'month' },
      }),
      getMySanctionsReport({ baseUrl: url, token: authToken }).catch(() => []),
    ])

    reportStudent.value = studentPayload
    reportStudentStats.value = statsPayload
    reportSanctions.value = Array.isArray(sanctionsPayload) ? sanctionsPayload : []
  } catch (error) {
    reportsError.value = error?.message || 'Unable to load your detailed student reports.'
    hydrateDerivedReports()
    reportsFallbackNotice.value = 'Showing derived attendance data from your dashboard cache while the detailed report endpoint is unavailable.'
  } finally {
    isLoadingReports.value = false
  }
}

function hydrateDerivedReports() {
  reportStudent.value = {
    student: buildDerivedSummary(latestAttendanceRecords.value),
    attendance_records: buildDerivedAttendanceRows(latestAttendanceRecords.value),
  }
  reportStudentStats.value = {
    trend_data: buildDerivedTrendData(latestAttendanceRecords.value),
  }
  reportSanctions.value = []
}

function hydratePreviewReports() {
  reportStudent.value = {
    student: buildDerivedSummary(latestAttendanceRecords.value),
    attendance_records: buildDerivedAttendanceRows(latestAttendanceRecords.value),
  }
  reportStudentStats.value = {
    trend_data: buildDerivedTrendData(latestAttendanceRecords.value),
  }
  reportSanctions.value = buildPreviewSanctions()
  reportsError.value = ''
  reportsFallbackNotice.value = 'Preview mode is showing simulated sanction and trend data.'
  isLoadingReports.value = false
}

async function reloadReports() {
  if (props.preview) {
    hydratePreviewReports()
    return
  }

  const profileId = reportStudentProfileId.value
  if (!profileId || !apiBaseUrl.value || !token.value) {
    hydrateDerivedReports()
    return
  }

  await loadReports(apiBaseUrl.value, token.value, profileId)
}

function buildDerivedSummary(records = []) {
  const summary = (Array.isArray(records) ? records : []).reduce((accumulator, record) => {
    const status = resolveAnalyticsStatus(record)
    accumulator.total_events += 1
    if (status === 'present' || status === 'late') accumulator.attended_events += 1
    if (status === 'late') accumulator.late_events += 1
    if (status === 'absent') accumulator.absent_events += 1
    if (status === 'excused') accumulator.excused_events += 1
    return accumulator
  }, {
    total_events: 0,
    attended_events: 0,
    late_events: 0,
    absent_events: 0,
    excused_events: 0,
  })

  return {
    ...summary,
    attendance_rate: summary.total_events > 0
      ? (summary.attended_events / summary.total_events) * 100
      : 0,
  }
}

function buildDerivedAttendanceRows(records = []) {
  return (Array.isArray(records) ? records : []).map((record, index) => {
    const eventId = Number(record?.event_id)
    const event = eventLookup.value[eventId]
    const timestamp = getAttendanceRecordTimestamp(record)
    const status = resolveAnalyticsStatus(record)

    return {
      id: record?.id || `${eventId || 'event'}-${index}`,
      event_id: eventId || null,
      event_name: event?.name || `Event ${eventId || ''}`.trim(),
      status,
      display_status: status,
      method: record?.method || record?.attendance_method || 'QR',
      attended_at: timestamp ? new Date(timestamp).toISOString() : null,
      created_at: timestamp ? new Date(timestamp).toISOString() : null,
    }
  })
}

function buildDerivedTrendData(records = []) {
  const buckets = new Map()

  for (const record of Array.isArray(records) ? records : []) {
    const timestamp = getAttendanceRecordTimestamp(record)
    const date = timestamp ? new Date(timestamp) : null
    if (!date || Number.isNaN(date.getTime())) continue

    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    if (!buckets.has(key)) {
      buckets.set(key, {
        period: key,
        label: date.toLocaleDateString('en-PH', { month: 'short', year: 'numeric' }),
        present_count: 0,
        late_count: 0,
        absent_count: 0,
        excused_count: 0,
        attended_count: 0,
      })
    }

    const bucket = buckets.get(key)
    const status = resolveAnalyticsStatus(record)
    if (status === 'present') {
      bucket.present_count += 1
      bucket.attended_count += 1
    } else if (status === 'late') {
      bucket.late_count += 1
      bucket.attended_count += 1
    } else if (status === 'absent') {
      bucket.absent_count += 1
    } else if (status === 'excused') {
      bucket.excused_count += 1
    }
  }

  return [...buckets.values()].sort((left, right) => String(left.period).localeCompare(String(right.period)))
}

function buildEventTypeRows(records = []) {
  const buckets = new Map()

  for (const record of Array.isArray(records) ? records : []) {
    const eventId = Number(record?.event_id)
    const event = eventLookup.value[eventId]
    const label = String(
      record?.event_type
      || event?.event_type
      || event?.scope_label
      || 'General'
    ).trim() || 'General'

    if (!buckets.has(label)) {
      buckets.set(label, {
        label,
        total: 0,
      })
    }
    buckets.get(label).total += 1
  }

  return [...buckets.values()]
    .sort((left, right) => right.total - left.total)
    .slice(0, 6)
}

function buildPreviewSanctions() {
  return [
    {
      id: 'preview-pending',
      event_id: 8,
      event_name: 'Department Meeting',
      status: 'pending',
      created_at: new Date().toISOString(),
      items: [
        { id: 'preview-item-1', status: 'pending' },
        { id: 'preview-item-2', status: 'pending' },
      ],
    },
    {
      id: 'preview-complied',
      event_id: 10,
      event_name: 'College Sportsfest',
      status: 'complied',
      updated_at: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString(),
      items: [
        { id: 'preview-item-3', status: 'complied' },
      ],
    },
  ]
}

function hasPendingSanctionItems(record = null) {
  const overallStatus = normalizeSanctionStatus(record?.status)
  if (overallStatus === 'pending') return true
  const items = Array.isArray(record?.items) ? record.items : []
  return items.some((item) => normalizeSanctionStatus(item?.status) === 'pending')
}

function normalizeSanctionStatus(value) {
  const normalized = String(value || '').trim().toLowerCase()
  return normalized || 'pending'
}

function normalizeReportRecord(record = {}, index = 0) {
  const timestamp = new Date(
    record?.attended_at
    || record?.created_at
    || record?.time_in
    || 0
  ).getTime()
  const normalizedStatus = String(record?.display_status || record?.status || 'unknown')
  return {
    key: `${record?.id || record?.event_id || 'record'}-${index}`,
    timestamp: Number.isFinite(timestamp) ? timestamp : 0,
    dateLabel: formatShortDate(record?.attended_at || record?.created_at || record?.time_in),
    eventName: record?.event_name || `Event ${record?.event_id || ''}`.trim(),
    statusLabel: formatStatusLabel(normalizedStatus),
    methodLabel: String(record?.method || 'QR'),
  }
}

function normalizeSanctionRow(record = {}, index = 0) {
  const updatedAt = record?.updated_at || record?.complied_at || record?.created_at || null
  const timestamp = new Date(updatedAt || 0).getTime()
  return {
    key: `${record?.id || record?.event_id || 'sanction'}-${index}`,
    timestamp: Number.isFinite(timestamp) ? timestamp : 0,
    eventName: String(record?.event_name || `Event ${record?.event_id || ''}`).trim(),
    statusLabel: formatStatusLabel(hasPendingSanctionItems(record) ? 'pending' : 'complied'),
    itemCount: formatWhole(Array.isArray(record?.items) ? record.items.length : 0),
    updatedLabel: formatShortDate(updatedAt),
  }
}

function formatShortDate(value) {
  if (!value) return 'N/A'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'N/A'
  return date.toLocaleDateString('en-PH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function formatWhole(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return '0'
  return new Intl.NumberFormat('en-US').format(Math.max(0, Math.round(normalized)))
}

function formatPercentValue(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return '0'
  return `${Math.round(normalized * 10) / 10}`.replace(/\.0$/, '')
}

function formatStatusLabel(status = '') {
  const normalized = String(status || '').trim().toLowerCase()
  if (!normalized) return 'Unknown'
  return normalized.replace(/_/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase())
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

.analytics-reports {
  margin: 0 auto;
  width: min(1180px, calc(100% - 32px));
  padding: 0 0 110px;
  display: grid;
  gap: 18px;
}

.analytics-reports__header,
.analytics-reports__panel-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
}

.analytics-reports__eyebrow {
  margin: 0 0 6px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.analytics-reports__title {
  margin: 0;
  font-size: clamp(28px, 3vw, 40px);
  line-height: 0.96;
  letter-spacing: -0.05em;
  color: var(--color-text-primary);
}

.analytics-reports__subtitle,
.analytics-reports__panel-head p {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--color-text-secondary);
}

.analytics-reports__refresh {
  min-height: 46px;
  padding: 0 16px;
  border: none;
  border-radius: 999px;
  background: var(--color-secondary);
  color: var(--color-secondary-text);
  font: inherit;
  font-weight: 700;
}

.analytics-reports__banner,
.analytics-reports__loading {
  padding: 14px 18px;
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-surface) 88%, transparent);
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
}

.analytics-reports__banner--error {
  color: #b42318;
}

.analytics-reports__stats,
.analytics-reports__charts,
.analytics-reports__tables {
  display: grid;
  gap: 16px;
}

.analytics-reports__stats {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.analytics-reports__stats--insights {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.analytics-reports__stat-card,
.analytics-reports__panel {
  border-radius: 28px;
  background: var(--color-surface);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.05);
}

.analytics-reports__stat-card {
  min-height: 138px;
  padding: 18px;
  display: grid;
  gap: 10px;
}

.analytics-reports__stat-card--soft {
  min-height: 124px;
}

.analytics-reports__stat-card span,
.analytics-reports__stat-card small {
  color: var(--color-text-muted);
}

.analytics-reports__stat-card span {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.analytics-reports__stat-card strong {
  font-size: 34px;
  line-height: 0.96;
  letter-spacing: -0.05em;
  color: var(--color-text-primary);
}

.analytics-reports__stat-card small {
  font-size: 13px;
  line-height: 1.45;
}

.analytics-reports__charts {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.analytics-reports__tables {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.analytics-reports__panel {
  padding: 20px;
  display: grid;
  gap: 16px;
}

.analytics-reports__panel-head h3 {
  margin: 0;
  font-size: 22px;
  line-height: 1.04;
  letter-spacing: -0.04em;
  color: var(--color-text-primary);
}

.analytics-reports__chart {
  min-height: 260px;
}

.analytics-reports__table-wrap {
  overflow-x: auto;
}

.analytics-reports__table {
  width: 100%;
  min-width: 420px;
  border-collapse: collapse;
}

.analytics-reports__table thead th {
  padding: 0 10px 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.analytics-reports__table tbody td {
  padding: 12px 10px;
  border-top: 1px solid color-mix(in srgb, var(--color-text-muted) 18%, transparent);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.analytics-reports__empty,
.analytics-reports__empty-cell {
  color: var(--color-text-muted);
  font-size: 13px;
}

.analytics-reports__empty-cell {
  text-align: center;
}

@media (max-width: 1180px) {
  .analytics-reports__stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .analytics-reports__stats--insights,
  .analytics-reports__charts,
  .analytics-reports__tables {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .analytics-reports {
    width: calc(100% - 24px);
    padding-bottom: 120px;
  }

  .analytics-reports__header,
  .analytics-reports__panel-head {
    flex-direction: column;
    align-items: stretch;
  }

  .analytics-reports__refresh {
    width: 100%;
  }

  .analytics-reports__stats,
  .analytics-reports__stats--insights,
  .analytics-reports__charts,
  .analytics-reports__tables {
    grid-template-columns: 1fr;
  }
}
</style>
