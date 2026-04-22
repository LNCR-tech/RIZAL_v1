<template>
  <section class="school-it-home">
    <div class="school-it-home__shell">
      <SchoolItTopHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="schoolName"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <div class="school-it-home__body">
        <h1 class="school-it-home__title dashboard-enter dashboard-enter--2">Home</h1>

        <section class="school-it-home__search dashboard-enter dashboard-enter--3">
          <div class="school-it-home__search-row">
            <div class="school-it-home__search-wrap">
              <div class="school-it-home__search-shell" :class="{ 'school-it-home__search-shell--open': searchActive }">
                <div class="school-it-home__search-input-row">
                  <input v-model="searchQuery" v-bind="schoolSearchInputAttrs" type="text" placeholder="Search school data" class="school-it-home__search-input">
                  <button class="school-it-home__search-icon" type="button" aria-label="Search">
                    <Search :size="18" />
                  </button>
                </div>

                <div class="school-it-home__search-results">
                  <div class="school-it-home__search-results-inner">
                    <template v-if="searchActive">
                      <button
                        v-for="result in searchResults"
                        :key="result.key"
                        class="school-it-home__search-result"
                        type="button"
                        @click="openSearchResult(result)"
                      >
                        <div class="school-it-home__search-result-top">
                          <span class="school-it-home__search-result-name">{{ result.name }}</span>
                          <span class="school-it-home__search-result-type">{{ result.type }}</span>
                        </div>
                        <span class="school-it-home__search-result-meta">{{ result.meta }}</span>
                      </button>
                      <p v-if="!searchResults.length" class="school-it-home__empty">No matching school data found.</p>
                    </template>
                  </div>
                </div>
              </div>
            </div>

            <button
              v-show="!searchActive"
              class="school-it-home__ai-pill"
              :class="{ 'school-it-home__ai-pill--open': isAiOpen }"
              type="button"
              aria-label="Talk to Aura AI"
              :aria-expanded="isAiOpen ? 'true' : 'false'"
              aria-controls="school-it-ai-panel"
              @click="toggleAiPanel"
            >
              <img :src="secondaryAuraLogo" alt="Aura" class="school-it-home__ai-logo">
              <span class="school-it-home__ai-copy">Talk to<br>Aura Ai</span>
            </button>
          </div>

          <Transition
            name="school-it-ai-panel"
            @before-enter="onAiPanelBeforeEnter"
            @enter="onAiPanelEnter"
            @after-enter="onAiPanelAfterEnter"
            @before-leave="onAiPanelBeforeLeave"
            @leave="onAiPanelLeave"
            @after-leave="onAiPanelAfterLeave"
          >
            <div
              v-if="isAiOpen && !searchActive"
              id="school-it-ai-panel"
              class="school-it-home__ai-panel"
              role="region"
              aria-label="Aura AI chat"
            >
              <div class="school-it-home__ai-panel-inner">
                <div class="school-it-home__ai-shell">
                  <div ref="scrollEl" class="school-it-home__ai-messages">
                    <TransitionGroup name="school-it-bubble" tag="div" class="school-it-home__ai-messages-inner">
                      <template v-for="message in messages" :key="message.id">
                        <div
                          v-if="message.sender === 'user' || (message.text && message.text.trim().length > 0)"
                          :class="[
                            'school-it-home__bubble',
                            message.sender === 'ai'
                              ? 'school-it-home__bubble--ai'
                              : 'school-it-home__bubble--user',
                          ]"
                        >
                          <ChatMarkdownMessage :text="message.text" />
                        </div>
                      </template>

                      <div
                        v-if="isTyping"
                        key="typing"
                        class="school-it-home__bubble school-it-home__bubble--ai school-it-home__bubble--typing"
                      >
                        <span class="school-it-home__typing-dot" style="animation-delay: 0ms" />
                        <span class="school-it-home__typing-dot" style="animation-delay: 150ms" />
                        <span class="school-it-home__typing-dot" style="animation-delay: 300ms" />
                      </div>
                    </TransitionGroup>
                  </div>

                  <div class="school-it-home__ai-input">
                    <div class="school-it-home__ai-input-row">
                      <input
                        ref="aiInputEl"
                        v-model="inputText"
                        class="school-it-home__ai-input-field"
                        type="text"
                        placeholder="Ask Aura..."
                        :disabled="isTyping"
                        @keyup.enter="sendMessage"
                      >
                      <button
                        class="school-it-home__ai-send"
                        type="button"
                        aria-label="Send message"
                        :disabled="!inputText.trim() || isTyping"
                        @click="sendMessage"
                      >
                        <Send :size="15" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </section>

        <div class="school-it-home__cards">
          <section class="school-it-home__hero dashboard-enter dashboard-enter--4">
            <div class="school-it-home__hero-copy">
              <p class="school-it-home__hero-kicker">Hi School IT of</p>
              <h2 class="school-it-home__hero-title">{{ schoolName }}</h2>
              <button class="school-it-home__pill" type="button" @click="router.push({ name: settingsRouteName })">
                <span class="school-it-home__pill-icon"><ArrowRight :size="18" /></span>
                Edit Details
              </button>
            </div>

            <div class="school-it-home__hero-logo">
              <img
                v-if="heroLogoSrc"
                :key="heroLogoSrc"
                :src="heroLogoSrc"
                :alt="`${schoolName} logo`"
                class="school-it-home__hero-logo-image"
              >
              <div v-else class="school-it-home__hero-logo-fallback">{{ schoolInitials }}</div>
            </div>
          </section>

          <section class="school-it-home__summary dashboard-enter dashboard-enter--5">
            <div class="school-it-home__summary-lead">
              <h3 class="school-it-home__summary-title">Total<br>Dept.</h3>
              <button class="school-it-home__pill school-it-home__pill--compact" type="button" @click="router.push({ name: settingsRouteName })">
                <span class="school-it-home__pill-icon"><ArrowRight :size="18" /></span>
                Open Setup
              </button>
            </div>

            <div class="school-it-home__summary-panel">
              <div>
                <strong class="school-it-home__summary-number">{{ departmentCountLabel }}</strong>
                <span class="school-it-home__summary-label">Departments</span>
              </div>
              <div>
                <strong class="school-it-home__summary-meta-number">{{ programCountLabel }}</strong>
                <span class="school-it-home__summary-meta-label">Total programs</span>
              </div>
            </div>
          </section>

          <section class="school-it-home__rate dashboard-enter dashboard-enter--6">
            <div class="school-it-home__rate-copy">
              <p class="school-it-home__metric-kicker">{{ populationComparisonLabel }}</p>
              <h3 class="school-it-home__rate-title">
                <span class="school-it-home__rate-title-attendance">Attendance</span>
                <span class="school-it-home__rate-title-rate">Rate</span>
              </h3>
              <p class="school-it-home__rate-meta">{{ attendanceRateMeta }}</p>
              <span class="school-it-home__metric-date">{{ todayLabel }}</span>
            </div>

            <div class="school-it-home__metric-panel">
              <SchoolItMetricRing :value="presentRateLabel" :delay="0.08" />
              <span class="school-it-home__metric-label">Present</span>
            </div>
          </section>

          <section class="school-it-home__status dashboard-enter dashboard-enter--7">
            <div class="school-it-home__status-grid">
              <article class="school-it-home__status-panel">
                <SchoolItMetricRing :value="lateRateLabel" compact :delay="0.16" />
                <span class="school-it-home__metric-label school-it-home__metric-label--compact">Late</span>
              </article>
              <article class="school-it-home__status-panel">
                <SchoolItMetricRing :value="absentRateLabel" compact :delay="0.24" />
                <span class="school-it-home__metric-label school-it-home__metric-label--compact">Absent</span>
              </article>
            </div>
          </section>
        </div>

        <section class="school-it-home__reports dashboard-enter dashboard-enter--8">
          <article class="school-it-home__report-card school-it-home__report-card--summary">
            <div class="school-it-home__report-head">
              <div>
                <p class="school-it-home__report-kicker">Reports Snapshot</p>
                <h3 class="school-it-home__report-title">Attendance Pulse</h3>
              </div>
              <button class="school-it-home__pill school-it-home__pill--compact" type="button" @click="router.push({ name: reportsRouteName })">
                <span class="school-it-home__pill-icon"><ArrowRight :size="18" /></span>
                Open Reports
              </button>
            </div>

            <p v-if="reportSyncError" class="school-it-home__report-note">{{ reportSyncError }}</p>

            <div class="school-it-home__report-stats">
              <article v-for="card in schoolReportCards" :key="card.id" class="school-it-home__report-stat">
                <span>{{ card.label }}</span>
                <strong>{{ card.value }}</strong>
                <small>{{ card.meta }}</small>
              </article>
            </div>
          </article>

          <article class="school-it-home__report-card">
            <div class="school-it-home__report-head">
              <div>
                <p class="school-it-home__report-kicker">Status Mix</p>
                <h3 class="school-it-home__report-title">School Distribution</h3>
              </div>
            </div>

            <div v-if="schoolStatusChartData.labels.length" class="school-it-home__report-chart">
              <ReportsPieChart :data="schoolStatusChartData" :options="reportChartOptions.pie" />
            </div>
            <p v-else class="school-it-home__report-empty">No attendance breakdown yet.</p>
          </article>

          <article class="school-it-home__report-card">
            <div class="school-it-home__report-head">
              <div>
                <p class="school-it-home__report-kicker">Top Students</p>
                <h3 class="school-it-home__report-title">Attendance Leaders</h3>
              </div>
            </div>

            <div v-if="topStudentsChartData.labels.length" class="school-it-home__report-chart">
              <ReportsBarChart :data="topStudentsChartData" :options="reportChartOptions.barPercent" />
            </div>
            <div v-else class="school-it-home__report-list">
              <p class="school-it-home__report-empty">Top-student ranking is unavailable right now.</p>
            </div>
          </article>
        </section>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Search, Send } from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import SchoolItMetricRing from '@/components/dashboard/SchoolItMetricRing.vue'
import ReportsBarChart from '@/components/reports/ReportsBarChart.vue'
import ReportsPieChart from '@/components/reports/ReportsPieChart.vue'
import ChatMarkdownMessage from '@/components/ui/ChatMarkdownMessage.vue'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'
import { secondaryAuraLogo } from '@/config/theme.js'
import { useChat } from '@/composables/useChat.js'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { useSchoolItWorkspaceData } from '@/composables/useSchoolItWorkspaceData.js'
import { useStoredAuthMeta } from '@/composables/useStoredAuthMeta.js'
import { getAttendanceOverview, getAttendanceSummary } from '@/services/backendApi.js'
import { buildBarChartData, buildPieChartData, toPercent } from '@/services/dashboardReportCharts.js'
import { hasPrivilegedPendingFace } from '@/services/localAuth.js'
import { resolveBackendMediaCandidates, resolveLoadableMediaUrl } from '@/services/backendMedia.js'
import { createSearchFieldAttrs } from '@/services/searchFieldAttrs.js'
import { filterWorkspaceEntitiesBySchool } from '@/services/workspaceScope.js'
import { resolveChatLocation } from '@/services/routeWorkspace.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()
const searchQuery = ref('')
const schoolSearchInputAttrs = createSearchFieldAttrs('school-it-home-search')
const isAiOpen = ref(false)
const aiInputEl = ref(null)
const remoteAttendanceSummary = ref(null)
const remoteAttendanceOverview = ref([])
const reportSyncError = ref('')
const heroLogoSrc = ref('')

const {
  currentUser,
  schoolSettings,
  apiBaseUrl,
  events,
  token,
  initializeDashboardSession,
  refreshSchoolSettings,
} = useDashboardSession()
const {
  departments: workspaceDepartments,
  programs: workspacePrograms,
  statuses: workspaceStatuses,
  initializeSchoolItWorkspaceData,
} = useSchoolItWorkspaceData()
const {
  closeAll,
  inputText,
  isTyping,
  messages,
  scrollEl,
  sendMessage,
} = useChat()
const { logout } = useAuth()
const authMeta = useStoredAuthMeta()

const searchActive = computed(() => searchQuery.value.trim().length > 0)
const activeUser = computed(() => props.preview ? schoolItPreviewData.user : currentUser.value)
const activeSchoolSettings = computed(() => props.preview ? schoolItPreviewData.schoolSettings : schoolSettings.value)
const activeEvents = computed(() => props.preview ? schoolItPreviewData.events : events.value)

usePreviewTheme(() => props.preview, activeSchoolSettings)

const schoolId = computed(() => Number(
  activeUser.value?.school_id
  ?? activeSchoolSettings.value?.school_id
  ?? authMeta.value?.schoolId
))
const schoolName = computed(() => (
  activeSchoolSettings.value?.school_name
  || activeUser.value?.school_name
  || authMeta.value?.schoolName
  || 'University Name'
))
const rawSchoolLogoCandidates = computed(() => (
  props.preview
    ? [schoolItPreviewData.schoolSettings?.logo_url]
    : [
      activeSchoolSettings.value?.logo_url,
      authMeta.value?.logoUrl,
    ]
))
const avatarUrl = computed(() => activeUser.value?.avatar_url || '')
const heroLogoCandidates = computed(() => (
  resolveBackendMediaCandidates(rawSchoolLogoCandidates.value, apiBaseUrl.value)
))

const displayName = computed(() => {
  const first = activeUser.value?.first_name || ''
  const middle = activeUser.value?.middle_name || ''
  const last = activeUser.value?.last_name || ''
  return [first, middle, last].filter(Boolean).join(' ')
    || [authMeta.value?.firstName, authMeta.value?.lastName].filter(Boolean).join(' ')
    || activeUser.value?.email?.split('@')[0]
    || authMeta.value?.email?.split('@')[0]
    || 'School IT'
})

const initials = computed(() => buildInitials(displayName.value))
const schoolInitials = computed(() => buildInitials(schoolName.value))
const settingsRouteName = computed(() => props.preview ? 'PreviewSchoolItSettings' : 'SchoolItSettings')
const scheduleRouteName = computed(() => props.preview ? 'PreviewSchoolItSchedule' : 'SchoolItSchedule')
const reportsRouteName = computed(() => props.preview ? 'PreviewSchoolItEventReports' : 'SchoolItEventReports')

const activeDepartments = computed(() => props.preview ? schoolItPreviewData.departments : workspaceDepartments.value)
const activePrograms = computed(() => props.preview ? schoolItPreviewData.programs : workspacePrograms.value)
const activeAttendanceSummary = computed(() => props.preview ? schoolItPreviewData.attendanceSummary : remoteAttendanceSummary.value)
const departmentsStatus = computed(() => props.preview ? 'ready' : (workspaceStatuses.value?.departments || 'idle'))
const programsStatus = computed(() => props.preview ? 'ready' : (workspaceStatuses.value?.programs || 'idle'))

const filteredDepartments = computed(() => filterWorkspaceEntitiesBySchool(activeDepartments.value, schoolId.value))
const filteredPrograms = computed(() => filterWorkspaceEntitiesBySchool(activePrograms.value, schoolId.value))
const filteredEvents = computed(() => filterWorkspaceEntitiesBySchool(activeEvents.value, schoolId.value))

const departmentCountLabel = computed(() => formatSummaryCount(filteredDepartments.value, departmentsStatus.value))
const programCountLabel = computed(() => formatSummaryCount(filteredPrograms.value, programsStatus.value))

const attendanceSummary = computed(() => normalizeAttendanceSummary(activeAttendanceSummary.value) || buildEventAttendanceSummary(filteredEvents.value))
const totalAttendanceRecords = computed(() => attendanceSummary.value.total_attendance_records)
const attendedCount = computed(() => attendanceSummary.value.attended_count)
const uniqueStudents = computed(() => attendanceSummary.value.unique_students)
const attendanceRate = computed(() => attendanceSummary.value.attendance_rate)
const presentRateLabel = computed(() => toRoundedPercent(attendanceSummary.value.present_count, totalAttendanceRecords.value))
const lateRateLabel = computed(() => toRoundedPercent(attendanceSummary.value.late_count, totalAttendanceRecords.value))
const absentRateLabel = computed(() => toRoundedPercent(attendanceSummary.value.absent_count, totalAttendanceRecords.value))

const todayLabel = computed(() => new Intl.DateTimeFormat('en-PH', { month: 'long', day: 'numeric', year: 'numeric' }).format(new Date()))
const attendanceRateMeta = computed(() => totalAttendanceRecords.value <= 0
  ? 'No attendance records available yet.'
  : `${formatInteger(attendedCount.value)} attended overall · ${formatInteger(attendanceRate.value)}% rate`)
const populationComparisonLabel = computed(() => uniqueStudents.value > 0
  ? `Compared to ${formatInteger(uniqueStudents.value)} enrolled students`
  : 'Compare to total population')

const topStudentsRows = computed(() => props.preview ? buildPreviewTopStudents() : (
  Array.isArray(remoteAttendanceOverview.value)
    ? remoteAttendanceOverview.value.slice(0, 5)
    : []
))

const schoolReportCards = computed(() => [
  {
    id: 'records',
    label: 'Attendance Records',
    value: formatInteger(totalAttendanceRecords.value),
    meta: `${formatInteger(attendedCount.value)} marked attended`,
  },
  {
    id: 'students',
    label: 'Students Reached',
    value: formatInteger(uniqueStudents.value),
    meta: `${formatInteger(attendanceSummary.value.unique_events)} tracked events`,
  },
  {
    id: 'rate',
    label: 'Attendance Rate',
    value: `${toPercent(attendanceRate.value, 1)}%`,
    meta: `${formatInteger(attendanceSummary.value.absent_count)} absent · ${formatInteger(attendanceSummary.value.excused_count)} excused`,
  },
])

const schoolStatusChartData = computed(() => buildPieChartData([
  { label: 'Present', value: attendanceSummary.value.present_count },
  { label: 'Late', value: attendanceSummary.value.late_count },
  { label: 'Absent', value: attendanceSummary.value.absent_count },
  { label: 'Excused', value: attendanceSummary.value.excused_count },
]))

const topStudentsChartData = computed(() => buildBarChartData(
  topStudentsRows.value.map((row) => ({
    label: shortenName(row?.full_name || row?.student_name || row?.student_id || 'Student'),
    value: Number(row?.attendance_rate || 0),
  })),
  {
    label: 'Attendance Rate (%)',
    backgroundColor: 'rgba(0,87,184,0.82)',
  }
))

const reportChartOptions = {
  pie: {
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  },
  barPercent: {
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
  },
}

const programsByDepartment = computed(() => {
  const lookup = new Map()
  filteredDepartments.value.forEach((department) => lookup.set(Number(department.id), 0))

  filteredPrograms.value.forEach((program) => {
    const departmentIds = Array.isArray(program.department_ids)
      ? program.department_ids.map((value) => Number(value)).filter(Number.isFinite)
      : []

    departmentIds.forEach((departmentId) => {
      if (!lookup.has(departmentId)) return
      lookup.set(departmentId, (lookup.get(departmentId) || 0) + 1)
    })
  })

  return lookup
})

const searchResults = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return []

  const departmentResults = filteredDepartments.value
    .filter((department) => department.name.toLowerCase().includes(query))
    .map((department) => ({
      key: `department-${department.id}`,
      name: department.name,
      type: 'Department',
      meta: `${programsByDepartment.value.get(Number(department.id)) || 0} linked programs`,
      routeName: settingsRouteName.value,
    }))

  const programResults = filteredPrograms.value
    .filter((program) => program.name.toLowerCase().includes(query))
    .map((program) => ({
      key: `program-${program.id}`,
      name: program.name,
      type: 'Program',
      meta: `${program.department_ids?.length || 0} department links`,
      routeName: settingsRouteName.value,
    }))

  const eventResults = filteredEvents.value
    .filter((event) => String(event?.name || '').toLowerCase().includes(query))
    .map((event) => ({
      key: `event-${event.id}`,
      name: event.name,
      type: 'Event',
      meta: `${formatStatusLabel(event.status)} · ${event.location || 'TBA'}`,
      routeName: scheduleRouteName.value,
    }))

  return [...departmentResults, ...programResults, ...eventResults].slice(0, 8)
})

const nextFrame = (callback) => requestAnimationFrame(() => requestAnimationFrame(callback))

watch([apiBaseUrl, () => activeUser.value?.id, schoolId, () => props.preview], async ([resolvedApiBaseUrl, userId, , preview]) => {
  if (preview) return
  if (!resolvedApiBaseUrl || !userId) return

  await Promise.allSettled([
    initializeSchoolItWorkspaceData({
      includeUsers: false,
      includeCouncil: false,
    }),
    loadSchoolItHomeData(resolvedApiBaseUrl),
  ])
}, { immediate: true })

watch(isAiOpen, (open) => {
  if (!open) return
  closeAll()
  nextTick(() => {
    setTimeout(() => aiInputEl.value?.focus(), 220)
  })
})

watch(searchActive, (active) => {
  if (active) isAiOpen.value = false
})

watch(
  () => heroLogoCandidates.value.join('|'),
  async () => {
    heroLogoSrc.value = await resolveLoadableMediaUrl(heroLogoCandidates.value)
  },
  { immediate: true }
)

onMounted(async () => {
  if (props.preview) return

  if (!schoolSettings.value) {
    await initializeDashboardSession().catch(() => null)
  }

  if (token.value) {
    await refreshSchoolSettings().catch(() => null)
  }
})

async function loadSchoolItHomeData(resolvedApiBaseUrl) {
  const token = localStorage.getItem('aura_token') || ''
  reportSyncError.value = ''

  if (!token || hasPrivilegedPendingFace()) {
    remoteAttendanceSummary.value = null
    remoteAttendanceOverview.value = []
    return
  }

  const [attendanceSummaryResult, attendanceOverviewResult] = await Promise.allSettled([
    getAttendanceSummary(resolvedApiBaseUrl, token),
    getAttendanceOverview(resolvedApiBaseUrl, token, { limit: 6 }),
  ])

  remoteAttendanceSummary.value = attendanceSummaryResult.status === 'fulfilled' ? attendanceSummaryResult.value : null
  remoteAttendanceOverview.value = attendanceOverviewResult.status === 'fulfilled' ? attendanceOverviewResult.value : []

  if (attendanceSummaryResult.status === 'rejected' && attendanceOverviewResult.status === 'rejected') {
    reportSyncError.value = attendanceSummaryResult.reason?.message || attendanceOverviewResult.reason?.message || 'Live report data is unavailable right now.'
  }
}

function buildInitials(value) {
  const parts = String(value || '').split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return String(value || '').slice(0, 2).toUpperCase()
}

function normalizeAttendanceSummary(payload) {
  const summary = payload?.summary
  if (!summary || typeof summary !== 'object') return null

  const totalAttendanceRecords = toCount(summary.total_attendance_records)
  const presentCount = toCount(summary.present_count)
  const lateCount = toCount(summary.late_count)
  const absentCount = toCount(summary.absent_count)
  const excusedCount = toCount(summary.excused_count)
  const attendedCount = toCount(summary.attended_count || (presentCount + lateCount))
  const uniqueStudentsCount = toCount(summary.unique_students)
  const uniqueEventsCount = toCount(summary.unique_events)
  const rate = Number(summary.attendance_rate)

  return {
    total_attendance_records: totalAttendanceRecords,
    present_count: presentCount,
    late_count: lateCount,
    attended_count: attendedCount,
    absent_count: absentCount,
    excused_count: excusedCount,
    unique_students: uniqueStudentsCount,
    unique_events: uniqueEventsCount,
    attendance_rate: Number.isFinite(rate) ? Math.max(0, Math.min(100, rate)) : toRoundedPercent(attendedCount, totalAttendanceRecords),
  }
}

function buildEventAttendanceSummary(items) {
  const studentIds = new Set()
  const summary = items.reduce((aggregate, event) => {
    const eventSummary = event?.attendance_summary && typeof event.attendance_summary === 'object' ? event.attendance_summary : null
    const eventAttendances = Array.isArray(event?.attendances) ? event.attendances : []
    const presentCount = eventSummary ? toCount(eventSummary.present_count ?? eventSummary.present) : countStatus(eventAttendances, 'present')
    const lateCount = eventSummary ? toCount(eventSummary.late_count ?? eventSummary.late) : countStatus(eventAttendances, 'late')
    const absentCount = eventSummary ? toCount(eventSummary.absent_count ?? eventSummary.absent) : countStatus(eventAttendances, 'absent')
    const excusedCount = eventSummary ? toCount(eventSummary.excused_count ?? eventSummary.excused) : countStatus(eventAttendances, 'excused')
    const attendedCount = presentCount + lateCount
    const total = eventSummary
      ? toCount(eventSummary.total_attendance_records ?? eventSummary.total ?? attendedCount + absentCount + excusedCount)
      : eventAttendances.length

    eventAttendances.forEach((attendance) => {
      if (attendance?.student_id != null) studentIds.add(String(attendance.student_id))
    })

    return {
      total_attendance_records: aggregate.total_attendance_records + total,
      present_count: aggregate.present_count + presentCount,
      late_count: aggregate.late_count + lateCount,
      attended_count: aggregate.attended_count + attendedCount,
      absent_count: aggregate.absent_count + absentCount,
      excused_count: aggregate.excused_count + excusedCount,
      unique_events: aggregate.unique_events + (total > 0 ? 1 : 0),
    }
  }, {
    total_attendance_records: 0,
    present_count: 0,
    late_count: 0,
    attended_count: 0,
    absent_count: 0,
    excused_count: 0,
    unique_events: 0,
  })

  return {
    ...summary,
    unique_students: studentIds.size,
    attendance_rate: toRoundedPercent(summary.attended_count, summary.total_attendance_records),
  }
}

function buildPreviewTopStudents() {
  return (Array.isArray(schoolItPreviewData.users) ? schoolItPreviewData.users : [])
    .filter((user) => user?.student_profile)
    .slice(0, 5)
    .map((user, index) => ({
      id: user.student_profile.id || user.id,
      student_id: user.student_profile.student_id || `Preview-${index + 1}`,
      full_name: [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.email || 'Student',
      attendance_rate: Math.max(72, 96 - (index * 5)),
      total_events: 10 + index,
    }))
}

function shortenName(value) {
  const parts = String(value || '').trim().split(/\s+/).filter(Boolean)
  if (parts.length <= 1) return parts[0] || 'Student'
  return `${parts[0]} ${parts[parts.length - 1].charAt(0)}.`
}

function countStatus(items, targetStatus) {
  return items.filter((item) => String(item?.status ?? '').toLowerCase() === targetStatus).length
}

function toCount(value) {
  const normalized = Number(value)
  return Number.isFinite(normalized) && normalized > 0 ? Math.round(normalized) : 0
}

function toRoundedPercent(value, total) {
  const normalizedValue = Number(value)
  const normalizedTotal = Number(total)
  if (!Number.isFinite(normalizedValue) || !Number.isFinite(normalizedTotal) || normalizedTotal <= 0) return 0
  return Math.round((normalizedValue / normalizedTotal) * 100)
}

function formatSummaryCount(items, status) {
  const count = Array.isArray(items) ? items.length : 0
  if (count > 0) return String(count)
  if (status === 'ready' || status === 'absent') return '0'
  if (status === 'error' || status === 'blocked') return '--'
  return '...'
}

function formatInteger(value) {
  return new Intl.NumberFormat('en-PH').format(Math.max(0, Number(value) || 0))
}

function formatStatusLabel(status) {
  const normalized = String(status || '').trim().toLowerCase()
  return normalized ? normalized.charAt(0).toUpperCase() + normalized.slice(1) : 'Unknown'
}

function openSearchResult(result) {
  searchQuery.value = ''
  router.push({ name: result.routeName })
}

function toggleAiPanel() {
  router.push(resolveChatLocation())
}

function onAiPanelBeforeEnter(element) {
  element.style.height = '0px'
  element.style.opacity = '0'
  element.style.transform = 'translateY(-8px)'
  element.style.willChange = 'height, opacity, transform'
}

function onAiPanelEnter(element) {
  const height = element.scrollHeight
  element.style.transition = 'height 520ms cubic-bezier(0.22, 1, 0.36, 1), opacity 320ms ease, transform 420ms cubic-bezier(0.22, 1, 0.36, 1)'
  nextFrame(() => {
    element.style.height = `${height}px`
    element.style.opacity = '1'
    element.style.transform = 'translateY(0)'
  })
}

function onAiPanelAfterEnter(element) {
  element.style.height = 'auto'
  element.style.transition = ''
  element.style.willChange = ''
}

function onAiPanelBeforeLeave(element) {
  element.style.height = `${element.scrollHeight}px`
  element.style.opacity = '1'
  element.style.transform = 'translateY(0)'
  element.style.willChange = 'height, opacity, transform'
}

function onAiPanelLeave(element) {
  element.style.transition = 'height 420ms cubic-bezier(0.4, 0, 0.2, 1), opacity 240ms ease, transform 300ms ease'
  nextFrame(() => {
    element.style.height = '0px'
    element.style.opacity = '0'
    element.style.transform = 'translateY(-6px)'
  })
}

function onAiPanelAfterLeave(element) {
  element.style.transition = ''
  element.style.height = ''
  element.style.opacity = ''
  element.style.transform = ''
  element.style.willChange = ''
}

async function handleLogout() {
  await logout()
}
</script>

<style scoped>
.school-it-home{min-height:100vh;padding:30px 28px 120px;font-family:'Manrope',sans-serif}
.school-it-home__shell{width:100%;max-width:1120px;margin:0 auto}
.school-it-home__body{display:flex;flex-direction:column;gap:18px;margin-top:24px}
.school-it-home__title{margin:0;font-size:22px;font-weight:800;line-height:1;letter-spacing:-.05em;color:var(--color-text-primary)}
.school-it-home__search{display:flex;flex-direction:column;gap:10px}
.school-it-home__search-row{display:flex;align-items:stretch;gap:clamp(8px,3vw,12px)}
.school-it-home__search-wrap{flex:1;min-width:0}
.school-it-home__search-shell{display:grid;grid-template-rows:auto 0fr;padding:11px clamp(12px,4vw,16px);border-radius:30px;background:var(--color-surface);transition:grid-template-rows .32s cubic-bezier(.22,1,.36,1),border-radius .32s cubic-bezier(.22,1,.36,1)}
.school-it-home__search-shell--open{grid-template-rows:auto 1fr;border-radius:28px}
.school-it-home__search-input-row{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:clamp(8px,2.5vw,10px);min-height:clamp(38px,10vw,40px)}
.school-it-home__search-input{flex:1;min-width:0;border:none;background:transparent;outline:none;color:var(--color-text-always-dark);font-size:clamp(13px,3.8vw,14px);font-weight:500}
.school-it-home__search-input::placeholder{color:var(--color-text-muted)}
.school-it-home__search-icon{width:clamp(30px,8vw,32px);height:clamp(30px,8vw,32px);padding:0;border:1px solid var(--color-surface-border);border-radius:999px;background:transparent;color:var(--color-primary);display:inline-flex;align-items:center;justify-content:center;align-self:center;line-height:0;appearance:none;flex-shrink:0;place-self:center}
.school-it-home__search-icon :deep(svg){display:block;width:clamp(15px,4.5vw,18px);height:clamp(15px,4.5vw,18px);transform:translateY(0)}
.school-it-home__search-results{overflow:hidden;min-height:0}
.school-it-home__search-results-inner{display:flex;flex-direction:column;gap:10px;padding:14px 0 6px}
.school-it-home__search-result{width:100%;padding:14px 16px;border:none;border-radius:22px;background:color-mix(in srgb,var(--color-surface) 90%,var(--color-bg));display:flex;flex-direction:column;gap:8px;text-align:left}
.school-it-home__search-result-top{display:flex;align-items:center;justify-content:space-between;gap:12px}
.school-it-home__search-result-name{font-size:14px;font-weight:700;color:var(--color-text-always-dark)}
.school-it-home__search-result-type{min-height:28px;padding:0 12px;border-radius:999px;background:color-mix(in srgb,var(--color-primary) 18%,white);color:var(--color-text-always-dark);display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;letter-spacing:.02em;flex-shrink:0}
.school-it-home__search-result-meta,.school-it-home__empty{font-size:12px;color:var(--color-text-muted)}
.school-it-home__ai-pill{width:clamp(108px,30vw,122px);min-height:clamp(56px,15vw,60px);padding:0 clamp(12px,4vw,14px);border:none;border-radius:999px;background:var(--color-search-pill-bg);color:var(--color-search-pill-text);display:inline-flex;align-items:center;justify-content:center;gap:clamp(8px,2.6vw,10px);flex-shrink:0;transition:opacity .2s ease,transform .2s ease,box-shadow .25s ease,filter .22s ease}
.school-it-home__ai-pill:hover{filter:brightness(1.08);transform:scale(1.04)}
.school-it-home__ai-pill:active{transform:scale(.96)}
.school-it-home__ai-pill--open{box-shadow:0 12px 24px rgba(0,0,0,.14);transform:translateY(1px) scale(.98)}
.school-it-home__ai-logo{width:clamp(28px,8vw,32px);height:clamp(28px,8vw,32px);object-fit:contain}
.school-it-home__ai-copy{font-size:clamp(12px,3.4vw,13px);font-weight:700;line-height:.98;text-align:left}
.school-it-home__ai-panel{overflow:hidden;transform-origin:top center}
.school-it-home__ai-panel-inner{overflow:hidden}
.school-it-home__ai-shell{position:relative;display:flex;flex-direction:column;gap:10px;padding:14px;background:var(--color-ai-surface);border-radius:28px;box-shadow:0 18px 40px rgba(0,0,0,.14);overflow:hidden}
.school-it-home__ai-messages{position:relative;z-index:1;display:flex;flex-direction:column;gap:10px;min-height:clamp(110px,22vh,180px);max-height:min(46vh,320px);overflow-y:auto;padding:6px 6px 0;scrollbar-width:none}
.school-it-home__ai-messages::-webkit-scrollbar{display:none}
.school-it-home__ai-messages-inner{display:flex;flex-direction:column;gap:10px}
.school-it-home__bubble{max-width:88%;padding:12px 16px;border-radius:24px;font-size:13px;font-weight:600;line-height:1.6;font-family:'Manrope',sans-serif;word-break:break-word}
.school-it-home__bubble--ai{align-self:flex-start;background:#FFFFFF;color:#0A0A0A;box-shadow:0 8px 18px rgba(0,0,0,.08)}
.school-it-home__bubble--user{align-self:flex-end;background:var(--color-ai-user-bubble-bg);color:var(--color-ai-user-bubble-text);border:1px solid var(--color-ai-input-border)}
.school-it-home__bubble--typing{display:flex;align-items:center;gap:6px;padding:12px 16px}
.school-it-home__typing-dot{width:6px;height:6px;border-radius:999px;background:color-mix(in srgb,var(--color-ai-surface-text) 50%, transparent);animation:school-it-dot-bounce 1s infinite ease-in-out}
.school-it-home__ai-input{position:relative;z-index:1}
.school-it-home__ai-input-row{display:flex;align-items:center;gap:8px;height:44px;padding:0 8px 0 16px;border:1.4px solid var(--color-ai-input-border);border-radius:999px;background:var(--color-ai-input-bg);transition:border-color .2s ease,background .2s ease}
.school-it-home__ai-input-row:focus-within{background:var(--color-ai-input-bg-focus);border-color:color-mix(in srgb,var(--color-ai-surface-text) 22%, var(--color-ai-surface))}
.school-it-home__ai-input-field{flex:1;min-width:0;border:none;outline:none;background:transparent;color:var(--color-ai-surface-text);font-size:12.5px;font-weight:600}
.school-it-home__ai-input-field::placeholder{color:var(--color-ai-surface-text);opacity:.55}
.school-it-home__ai-send{display:flex;align-items:center;justify-content:center;width:34px;height:34px;border:none;border-radius:999px;background:var(--color-ai-send-bg);color:var(--color-ai-surface-text);cursor:pointer;flex-shrink:0;transition:background .18s ease,transform .15s ease,opacity .18s ease}
.school-it-home__ai-send:hover:not(:disabled){background:var(--color-ai-send-bg-hover);transform:scale(1.08)}
.school-it-home__ai-send:disabled{opacity:.45;cursor:not-allowed}
.school-it-bubble-enter-active{animation:school-it-bubble-pop .45s cubic-bezier(.34,1.56,.64,1) both}
.school-it-home__bubble--ai.school-it-bubble-enter-active{transform-origin:bottom left}
.school-it-home__bubble--user.school-it-bubble-enter-active{transform-origin:bottom right}
.school-it-home__cards{display:grid;gap:20px}
.school-it-home__hero,.school-it-home__summary,.school-it-home__rate,.school-it-home__status{border-radius:32px;overflow:hidden}
.school-it-home__hero{position:relative;display:block;min-height:230px;padding:28px 18px 0;background:var(--color-primary);--school-it-hero-logo-size:140px;--school-it-hero-logo-offset:-20px;--school-it-hero-logo-top:68%}
.school-it-home__hero-copy{position:relative;z-index:1;display:flex;flex-direction:column;min-width:0;min-height:202px;max-width:calc(100% - (var(--school-it-hero-logo-size) * 0.68));align-self:stretch}
.school-it-home__hero-kicker{margin:0;font-size:17px;line-height:1.18;font-weight:500;color:var(--color-banner-text)}
.school-it-home__hero-title{margin:8px 0 0;max-width:6ch;font-size:clamp(26px,10vw,58px);line-height:.95;letter-spacing:-.07em;font-weight:800;color:var(--color-banner-text)}
.school-it-home__hero-logo{position:absolute;right:var(--school-it-hero-logo-offset);top:var(--school-it-hero-logo-top);transform:translateY(-50%);display:flex;align-items:flex-end;justify-content:flex-end;pointer-events:none;z-index:0}
.school-it-home__hero-logo-image{width:var(--school-it-hero-logo-size);height:var(--school-it-hero-logo-size);object-fit:contain;object-position:bottom right}
.school-it-home__hero-logo-fallback{width:var(--school-it-hero-logo-size);height:var(--school-it-hero-logo-size);border-radius:32px;background:rgba(10,10,10,.12);color:var(--color-banner-text);display:inline-flex;align-items:center;justify-content:center;font-size:28px;font-weight:800;letter-spacing:.08em}
.school-it-home__pill{width:fit-content;min-height:58px;margin-top:auto;margin-bottom:24px;padding:0 22px 0 8px;border:none;border-radius:999px;background:var(--color-surface);color:var(--color-text-always-dark);display:inline-flex;align-items:center;gap:14px;font-size:13px;font-weight:700}
.school-it-home__pill--compact{min-height:56px;margin-bottom:0}
.school-it-home__pill-icon{width:42px;height:42px;border-radius:999px;background:var(--color-nav);color:var(--color-nav-text);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
.school-it-home__summary{display:grid;grid-template-columns:minmax(0,1fr) minmax(156px,.95fr);gap:8px;background:var(--color-surface)}
.school-it-home__summary-lead{display:flex;flex-direction:column;justify-content:space-between;min-height:184px;padding:24px 18px 18px}
.school-it-home__summary-title{margin:0;font-size:clamp(26px,10vw,52px);line-height:.95;letter-spacing:-.07em;font-weight:700;color:var(--color-text-always-dark)}
.school-it-home__summary-panel,.school-it-home__metric-panel,.school-it-home__status-panel{background:color-mix(in srgb,var(--color-surface) 88%,var(--color-bg))}
.school-it-home__summary-panel{display:flex;flex-direction:column;justify-content:center;gap:14px;padding:22px 18px}
.school-it-home__summary-number{display:block;font-size:clamp(36px,11vw,56px);line-height:.9;letter-spacing:-.08em;font-weight:700;color:var(--color-primary)}
.school-it-home__summary-label,.school-it-home__summary-meta-label{font-size:16px;line-height:1.08;font-weight:500;color:var(--color-text-always-dark)}
.school-it-home__summary-meta-number{display:block;margin-bottom:2px;font-size:22px;line-height:1;letter-spacing:-.05em;font-weight:700;color:var(--color-text-always-dark)}
.school-it-home__rate{display:grid;grid-template-columns:minmax(0,1fr) minmax(166px,.82fr);gap:8px;background:var(--color-surface);min-height:234px}
.school-it-home__rate-copy{display:flex;flex-direction:column;justify-content:center;min-width:0;padding:22px 18px}
.school-it-home__metric-kicker{margin:0;max-width:13ch;font-size:12px;line-height:1.25;color:var(--color-text-secondary)}
.school-it-home__rate-title{display:flex;flex-direction:column;align-items:flex-start;gap:0;margin:10px 0 6px;color:var(--color-text-always-dark);overflow-wrap:anywhere;word-break:normal}
.school-it-home__rate-title-attendance{font-size:clamp(20px,4.8vw,28px);line-height:.96;letter-spacing:-.05em;font-weight:500}
.school-it-home__rate-title-rate{font-size:clamp(34px,9.4vw,58px);line-height:.88;letter-spacing:-.08em;font-weight:700}
.school-it-home__rate-meta{margin:0;font-size:13px;line-height:1.35;color:var(--color-text-secondary)}
.school-it-home__metric-date{margin-top:4px;font-size:12px;line-height:1.3;color:var(--color-text-secondary)}
.school-it-home__metric-panel{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:18px 14px}
.school-it-home__metric-label{margin-top:2px;font-size:14px;line-height:1.1;font-weight:500;color:var(--color-text-always-dark)}
.school-it-home__metric-label--compact{margin-top:0}
.school-it-home__status{background:var(--color-surface);padding:12px}
.school-it-home__status-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.school-it-home__status-panel{min-height:222px;border-radius:24px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:16px 10px 14px}
.school-it-home__reports{display:grid;gap:18px}
.school-it-home__report-card{padding:20px;border-radius:28px;background:var(--color-surface);box-shadow:0 18px 36px rgba(15,23,42,.05)}
.school-it-home__report-card--summary{display:flex;flex-direction:column;gap:14px}
.school-it-home__report-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px}
.school-it-home__report-kicker{margin:0;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--color-text-muted)}
.school-it-home__report-title{margin:4px 0 0;font-size:24px;line-height:1.02;letter-spacing:-.05em;font-weight:800;color:var(--color-text-primary)}
.school-it-home__report-note,.school-it-home__report-empty{margin:0;font-size:12px;line-height:1.5;color:var(--color-text-muted)}
.school-it-home__report-stats{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(160px,1fr))}
.school-it-home__report-stat{padding:14px;border-radius:20px;background:color-mix(in srgb,var(--color-surface) 88%,var(--color-bg));display:flex;flex-direction:column;gap:6px}
.school-it-home__report-stat span{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--color-text-muted)}
.school-it-home__report-stat strong{font-size:28px;line-height:1;letter-spacing:-.05em;color:var(--color-primary)}
.school-it-home__report-stat small{font-size:12px;line-height:1.45;color:var(--color-text-muted)}
.school-it-home__report-chart{min-height:260px}
.school-it-home__report-list{display:flex;align-items:center;min-height:260px}
@media (min-width:768px){
  .school-it-home{padding:40px 36px 56px}
  .school-it-home__body{margin-top:30px;gap:22px}
  .school-it-home__title{font-size:28px}
  .school-it-home__search-row{max-width:780px}
  .school-it-home__ai-panel{max-width:780px}
  .school-it-home__cards{grid-template-columns:minmax(0,1.1fr) minmax(320px,.9fr);grid-template-areas:"hero hero" "summary rate" "status status";gap:22px}
  .school-it-home__hero{grid-area:hero;min-height:332px;padding:34px 28px 0;--school-it-hero-logo-size:164px;--school-it-hero-logo-offset:-24px;--school-it-hero-logo-top:69%}
  .school-it-home__hero-copy{min-height:276px;max-width:calc(100% - (var(--school-it-hero-logo-size) * 0.74))}
  .school-it-home__hero-title{max-width:8ch}
  .school-it-home__summary{grid-area:summary;min-height:266px}
  .school-it-home__rate{grid-area:rate;min-height:266px}
  .school-it-home__status{grid-area:status}
  .school-it-home__status-panel{min-height:252px}
  .school-it-home__reports{grid-template-columns:minmax(0,1.05fr) minmax(280px,.95fr) minmax(280px,1fr)}
}
@media (min-width:1100px){
  .school-it-home__cards{grid-template-columns:minmax(0,1.04fr) minmax(360px,.96fr);grid-template-areas:"hero hero" "summary rate" "summary status"}
}
@media (prefers-reduced-motion:reduce){
  .school-it-home__ai-pill,.school-it-home__ai-send,.school-it-bubble-enter-active{transition:none;animation:none}
}

@keyframes school-it-dot-bounce{
  0%,100%{transform:translateY(0)}
  40%{transform:translateY(-4px)}
}

@keyframes school-it-bubble-pop{
  0%{opacity:0;transform:scale(.55)}
  65%{opacity:1;transform:scale(1.04)}
  82%{transform:scale(.97)}
  100%{transform:scale(1)}
}
</style>
