<template>
  <section class="school-it-reports">
    <div class="school-it-reports__shell">
      <SchoolItTopHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="activeSchoolSettings?.school_name || activeUser?.school_name || ''"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <div class="school-it-reports__body">
        <header class="school-it-reports__header dashboard-enter dashboard-enter--2">
          <button class="school-it-reports__back" type="button" @click="goBack" aria-label="Go Back">
            <ArrowLeft :size="20" />
          </button>
          <div class="school-it-reports__header-copy">
            <h1 class="school-it-reports__title">Reports Dashboard</h1>
            <p class="school-it-reports__subtitle">Event, student, school, and system reporting in one view.</p>
          </div>
        </header>

        <button
          class="school-it-reports__filters-toggle dashboard-enter dashboard-enter--3"
          type="button"
          :aria-expanded="String(mobileFiltersOpen)"
          @click="toggleMobileFilters"
        >
          <SlidersHorizontal :size="15" />
          <span>{{ mobileFiltersOpen ? 'Hide Filters' : 'Show Filters' }}</span>
        </button>

        <section
          v-show="!isMobileViewport || mobileFiltersOpen"
          class="school-it-reports__filters-panel dashboard-enter dashboard-enter--3"
        >
          <label class="school-it-reports__field">
            <span>Date From</span>
            <input v-model="filters.startDate" class="school-it-reports__field-input" type="date">
          </label>
          <label class="school-it-reports__field">
            <span>Date To</span>
            <input v-model="filters.endDate" class="school-it-reports__field-input" type="date">
          </label>
          <label class="school-it-reports__field">
            <span>Event</span>
            <select v-model="filters.eventId" class="school-it-reports__field-input">
              <option value="">All events</option>
              <option v-for="event in eventFilterOptions" :key="event.id" :value="String(event.id)">{{ event.name }}</option>
            </select>
          </label>
          <label class="school-it-reports__field">
            <span>Student</span>
            <select v-model="filters.studentId" class="school-it-reports__field-input">
              <option value="">All students</option>
              <option v-for="student in studentFilterOptions" :key="student.id" :value="String(student.id)">{{ student.full_name }}</option>
            </select>
          </label>
          <label class="school-it-reports__field">
            <span>Department</span>
            <select v-model="filters.departmentId" class="school-it-reports__field-input">
              <option value="">All departments</option>
              <option v-for="department in departmentFilterOptions" :key="department.id" :value="String(department.id)">{{ department.name }}</option>
            </select>
          </label>
          <button class="school-it-reports__clear-btn" type="button" @click="resetFilters">
            <X :size="14" /> Reset
          </button>
        </section>

        <nav class="school-it-reports__tabs dashboard-enter dashboard-enter--4">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="school-it-reports__tab"
            :class="{ 'school-it-reports__tab--active': activeTab === tab.id }"
            type="button"
            @click="setActiveTab(tab.id)"
          >
            <component :is="tab.icon" :size="15" />{{ tab.label }}
          </button>
        </nav>

        <section class="school-it-reports__content dashboard-enter dashboard-enter--5">
          <template v-if="activeTab === 'event'">
            <div class="school-it-reports__toolbar">
              <div class="school-it-reports__search-shell">
                <input v-model="searchQuery" class="school-it-reports__search-input" type="text" placeholder="Search events">
                <span class="school-it-reports__search-icon"><Search :size="16" /></span>
              </div>
              <button v-if="selectedEvent" class="school-it-reports__clear-btn" type="button" @click="clearSelection">
                <X :size="14" /> Clear Selection
              </button>
            </div>

            <div v-if="isLoadingEvents" class="school-it-reports__skeleton-grid">
              <div v-for="index in 3" :key="`event-skeleton-${index}`" class="school-it-reports__skeleton-card" />
            </div>

            <div v-else class="school-it-reports__table-wrap">
              <table class="school-it-reports__table">
                <thead>
                  <tr><th>Event</th><th>Date</th><th>Location</th><th>Actions</th></tr>
                </thead>
                <tbody>
                  <tr
                    v-for="event in filteredEvents"
                    :key="event.id"
                    :class="{ 'school-it-reports__table-row--selected': Number(event.id) === selectedEventId }"
                    @click="viewEvent(event)"
                  >
                    <td>{{ event.name }}</td>
                    <td>{{ formatDate(event.start_datetime) }}</td>
                    <td>{{ event.location || 'N/A' }}</td>
                    <td class="school-it-reports__cell-actions">
                      <button class="school-it-reports__btn school-it-reports__btn--view" type="button" @click.stop="viewEvent(event)">View</button>
                      <button class="school-it-reports__btn school-it-reports__btn--dark" type="button" @click.stop="downloadReport(event, 'csv')">CSV</button>
                    </td>
                  </tr>
                  <tr v-if="!filteredEvents.length"><td colspan="4" class="school-it-reports__empty">No events found.</td></tr>
                </tbody>
              </table>
            </div>

            <p v-if="selectionError" class="school-it-reports__banner school-it-reports__banner--error">{{ selectionError }}</p>
            <p v-if="isLoadingSelection" class="school-it-reports__banner">Loading selected event report...</p>

            <template v-if="selectedEvent && selectedEventReport && !isLoadingSelection">
              <header class="school-it-reports__detail-header">
                <div>
                  <h2 class="school-it-reports__section-title">{{ selectedEventReport.event_name || selectedEvent.name }}</h2>
                  <p class="school-it-reports__section-subtitle">{{ formatDate(selectedEvent.start_datetime) }} | {{ selectedEvent.location || 'N/A' }}</p>
                </div>
                <div class="school-it-reports__actions">
                  <button class="school-it-reports__btn school-it-reports__btn--dark" type="button" @click="downloadReport(selectedEvent, 'csv')">
                    <Download :size="14" /> Export CSV
                  </button>
                  <button class="school-it-reports__btn school-it-reports__btn--accent" type="button" @click="downloadReport(selectedEvent, 'excel')">
                    <FileSpreadsheet :size="14" /> Export Excel
                  </button>
                </div>
              </header>

              <div class="school-it-reports__stats-grid">
                <article v-for="card in eventSummaryCards" :key="card.id" class="school-it-reports__stat-card">
                  <span>{{ card.label }}</span>
                  <strong>{{ card.value }}</strong>
                  <small>{{ card.meta }}</small>
                </article>
              </div>

              <div class="school-it-reports__chart-grid">
                <article class="school-it-reports__panel">
                  <h3>Attendance Per Event</h3>
                  <div v-if="eventBarChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsBarChart class="school-it-reports__chart-canvas" :data="eventBarChartData" :options="chartOptions.bar" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No chart data.</p>
                </article>
                <article class="school-it-reports__panel">
                  <h3>Status Distribution</h3>
                  <div v-if="eventPieChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsPieChart class="school-it-reports__chart-canvas" :data="eventPieChartData" :options="chartOptions.pie" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No chart data.</p>
                </article>
                <article class="school-it-reports__panel">
                  <h3>Monthly Trend</h3>
                  <div v-if="eventLineChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsLineChart class="school-it-reports__chart-canvas" :data="eventLineChartData" :options="chartOptions.line" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No trend data.</p>
                </article>
              </div>

              <div class="school-it-reports__toolbar">
                <div class="school-it-reports__search-shell">
                  <input v-model="attendeeQuery" class="school-it-reports__search-input" type="text" placeholder="Search attendees">
                  <span class="school-it-reports__search-icon"><Search :size="16" /></span>
                </div>
              </div>

              <div class="school-it-reports__table-wrap">
                <table class="school-it-reports__table">
                  <thead>
                    <tr><th>Student ID</th><th>Name</th><th>Status</th><th>Sign In</th><th>Sign Out</th><th>Method</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in filteredAttendanceRows" :key="row.key">
                      <td>{{ row.studentId }}</td>
                      <td>{{ row.studentName }}</td>
                      <td>{{ row.statusLabel }}</td>
                      <td>{{ row.timeInLabel }}</td>
                      <td>{{ row.timeOutLabel }}</td>
                      <td>{{ row.methodLabel }}</td>
                    </tr>
                    <tr v-if="!filteredAttendanceRows.length"><td colspan="6" class="school-it-reports__empty">No attendance records found.</td></tr>
                  </tbody>
                </table>
              </div>
            </template>
          </template>

          <template v-else-if="activeTab === 'student'">
            <div v-if="isLoadingOverview" class="school-it-reports__skeleton-grid">
              <div v-for="index in 3" :key="`student-skeleton-${index}`" class="school-it-reports__skeleton-card" />
            </div>
            <p v-else-if="attendanceOverviewError" class="school-it-reports__banner school-it-reports__banner--error">{{ attendanceOverviewError }}</p>
            <template v-else-if="studentReport">
              <header class="school-it-reports__detail-header">
                <div>
                  <h2 class="school-it-reports__section-title">{{ studentReport.student.student_name }}</h2>
                  <p class="school-it-reports__section-subtitle">Student ID: {{ studentReport.student.student_id || 'N/A' }}</p>
                </div>
              </header>
              <div class="school-it-reports__stats-grid">
                <article v-for="card in studentSummaryCards" :key="card.id" class="school-it-reports__stat-card">
                  <span>{{ card.label }}</span><strong>{{ card.value }}</strong><small>{{ card.meta }}</small>
                </article>
              </div>
              <div class="school-it-reports__chart-grid">
                <article class="school-it-reports__panel">
                  <h3>Status Distribution</h3>
                  <div v-if="studentPieChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsPieChart class="school-it-reports__chart-canvas" :data="studentPieChartData" :options="chartOptions.pie" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No chart data.</p>
                </article>
                <article class="school-it-reports__panel">
                  <h3>Monthly Trend</h3>
                  <div v-if="studentLineChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsLineChart class="school-it-reports__chart-canvas" :data="studentLineChartData" :options="chartOptions.line" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No trend data.</p>
                </article>
              </div>

              <div class="school-it-reports__toolbar">
                <div class="school-it-reports__search-shell">
                  <input v-model="studentRecordQuery" class="school-it-reports__search-input" type="text" placeholder="Search student records">
                  <span class="school-it-reports__search-icon"><Search :size="16" /></span>
                </div>
              </div>

              <div class="school-it-reports__table-wrap">
                <table class="school-it-reports__table">
                  <thead><tr><th>Event</th><th>Date</th><th>Status</th><th>Sign In</th><th>Sign Out</th><th>Method</th></tr></thead>
                  <tbody>
                    <tr v-for="record in filteredStudentRecords" :key="record.id">
                      <td>{{ record.event_name }}</td>
                      <td>{{ formatDate(record.event_date) }}</td>
                      <td>{{ formatStatusLabel(record.display_status || record.status) }}</td>
                      <td>{{ formatDateTime(record.time_in, 'N/A') }}</td>
                      <td>{{ formatDateTime(record.time_out, 'N/A') }}</td>
                      <td>{{ formatMethod(record.method) }}</td>
                    </tr>
                    <tr v-if="!filteredStudentRecords.length"><td colspan="6" class="school-it-reports__empty">No student records found.</td></tr>
                  </tbody>
                </table>
              </div>
            </template>
            <p v-else class="school-it-reports__banner">Select a student from the filter panel.</p>
          </template>

          <template v-else-if="activeTab === 'school'">
            <div v-if="isLoadingSchoolSummary" class="school-it-reports__skeleton-grid">
              <div v-for="index in 3" :key="`school-skeleton-${index}`" class="school-it-reports__skeleton-card" />
            </div>
            <p v-else-if="schoolSummaryError" class="school-it-reports__banner school-it-reports__banner--error">{{ schoolSummaryError }}</p>
            <template v-else-if="schoolSummaryPayload">
              <div class="school-it-reports__stats-grid">
                <article v-for="card in schoolSummaryCards" :key="card.id" class="school-it-reports__stat-card">
                  <span>{{ card.label }}</span><strong>{{ card.value }}</strong><small>{{ card.meta }}</small>
                </article>
              </div>
              <div class="school-it-reports__chart-grid">
                <article class="school-it-reports__panel">
                  <h3>Status Distribution</h3>
                  <div v-if="schoolPieChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsPieChart class="school-it-reports__chart-canvas" :data="schoolPieChartData" :options="chartOptions.pie" />
                  </div>
                </article>
                <article class="school-it-reports__panel">
                  <h3>Monthly Trend</h3>
                  <div v-if="schoolLineChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsLineChart class="school-it-reports__chart-canvas" :data="schoolLineChartData" :options="chartOptions.line" />
                  </div>
                </article>
                <article class="school-it-reports__panel">
                  <h3>Top Student Rates</h3>
                  <div v-if="schoolBarChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsBarChart class="school-it-reports__chart-canvas" :data="schoolBarChartData" :options="chartOptions.barPercent" />
                  </div>
                </article>
              </div>

              <div class="school-it-reports__table-wrap">
                <table class="school-it-reports__table">
                  <thead><tr><th>Student ID</th><th>Name</th><th>Department</th><th>Program</th><th>Total Events</th><th>Rate</th></tr></thead>
                  <tbody>
                    <tr v-for="row in topStudentsRows" :key="row.id">
                      <td>{{ row.student_id || 'N/A' }}</td>
                      <td>{{ row.full_name }}</td>
                      <td>{{ row.department_name || 'Unassigned' }}</td>
                      <td>{{ row.program_name || 'Unassigned' }}</td>
                      <td>{{ formatWhole(row.total_events) }}</td>
                      <td>{{ formatPercent(row.attendance_rate) }}%</td>
                    </tr>
                    <tr v-if="!topStudentsRows.length"><td colspan="6" class="school-it-reports__empty">No student overview rows.</td></tr>
                  </tbody>
                </table>
              </div>
            </template>
          </template>

          <template v-else>
            <header class="school-it-reports__detail-header">
              <h2 class="school-it-reports__section-title">System Logs</h2>
              <button class="school-it-reports__btn school-it-reports__btn--view" type="button" @click="loadSystemLogs">Refresh</button>
            </header>
            <div v-if="isLoadingSystemLogs" class="school-it-reports__skeleton-grid">
              <div v-for="index in 3" :key="`system-skeleton-${index}`" class="school-it-reports__skeleton-card" />
            </div>
            <p v-else-if="systemLogsError" class="school-it-reports__banner school-it-reports__banner--error">{{ systemLogsError }}</p>
            <template v-else>
              <div class="school-it-reports__stats-grid">
                <article class="school-it-reports__stat-card"><span>Audit Logs</span><strong>{{ formatWhole(auditLogs.total || 0) }}</strong><small>Total audit rows.</small></article>
                <article class="school-it-reports__stat-card"><span>Notification Logs</span><strong>{{ formatWhole(notificationLogs.length) }}</strong><small>Total notification rows.</small></article>
                <article class="school-it-reports__stat-card"><span>Import Job</span><strong>{{ importReport?.jobStatus?.state || 'N/A' }}</strong><small>Last import lookup state.</small></article>
              </div>

              <div class="school-it-reports__table-wrap">
                <table class="school-it-reports__table">
                  <thead><tr><th>Timestamp</th><th>Action</th><th>Status</th><th>Actor</th><th>Details</th></tr></thead>
                  <tbody>
                    <tr v-for="item in auditRows" :key="item.id">
                      <td>{{ formatDateTime(item.created_at, 'N/A') }}</td>
                      <td>{{ item.action }}</td>
                      <td>{{ formatStatusLabel(item.status) }}</td>
                      <td>{{ item.actor_user_id || 'N/A' }}</td>
                      <td>{{ item.details || 'No details' }}</td>
                    </tr>
                    <tr v-if="!auditRows.length"><td colspan="5" class="school-it-reports__empty">No audit logs returned.</td></tr>
                  </tbody>
                </table>
              </div>

              <div class="school-it-reports__table-wrap">
                <table class="school-it-reports__table">
                  <thead><tr><th>Timestamp</th><th>Category</th><th>Channel</th><th>Status</th><th>User</th><th>Subject</th></tr></thead>
                  <tbody>
                    <tr v-for="item in notificationRows" :key="item.id">
                      <td>{{ formatDateTime(item.created_at, 'N/A') }}</td>
                      <td>{{ item.category }}</td>
                      <td>{{ item.channel }}</td>
                      <td>{{ formatStatusLabel(item.status) }}</td>
                      <td>{{ item.user_id || 'N/A' }}</td>
                      <td>{{ item.subject || 'No subject' }}</td>
                    </tr>
                    <tr v-if="!notificationRows.length"><td colspan="6" class="school-it-reports__empty">No notification logs returned.</td></tr>
                  </tbody>
                </table>
              </div>

              <article class="school-it-reports__panel">
                <h3>Import Reports</h3>
                <div class="school-it-reports__import-tools">
                  <input v-model="importJobId" class="school-it-reports__field-input" type="text" placeholder="Import Job ID">
                  <input v-model="importPreviewToken" class="school-it-reports__field-input" type="text" placeholder="Preview Token (optional)">
                  <button class="school-it-reports__btn school-it-reports__btn--view" type="button" @click="loadImportReport">Load</button>
                </div>
                <p v-if="importError" class="school-it-reports__banner school-it-reports__banner--error">{{ importError }}</p>
                <p v-else-if="isLoadingImport" class="school-it-reports__banner">Loading import report...</p>
                <div v-else-if="importReport?.jobStatus" class="school-it-reports__table-wrap">
                  <table class="school-it-reports__table">
                    <thead><tr><th>Row</th><th>Error</th></tr></thead>
                    <tbody>
                      <tr v-for="error in importErrors" :key="`${error.row}-${error.error}`">
                        <td>{{ error.row }}</td>
                        <td>{{ error.error }}</td>
                      </tr>
                      <tr v-if="!importErrors.length"><td colspan="2" class="school-it-reports__empty">No failed rows in this import job.</td></tr>
                    </tbody>
                  </table>
                </div>
              </article>
            </template>
          </template>
        </section>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, BarChart3, Building2, Download, FileSpreadsheet, FileText, Search, SlidersHorizontal, UserRound, X } from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import ReportsBarChart from '@/components/reports/ReportsBarChart.vue'
import ReportsLineChart from '@/components/reports/ReportsLineChart.vue'
import ReportsPieChart from '@/components/reports/ReportsPieChart.vue'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useStoredAuthMeta } from '@/composables/useStoredAuthMeta.js'
import {
  getAttendanceOverview,
  getAuditLogs,
  getEventAttendanceRecords,
  getEventAttendanceReport as fetchEventReport,
  getImportReports,
  getNotificationLogs,
  getReportDepartments,
  getReportEvents,
  getSchoolSummary,
  getStudentReport,
  getStudentStats,
} from '@/services/reportService.js'
import { filterWorkspaceEntitiesBySchool } from '@/services/workspaceScope.js'

defineProps({ preview: { type: Boolean, default: false } })

const route = useRoute()
const router = useRouter()
const { logout } = useAuth()
const authMeta = useStoredAuthMeta()
const {
  currentUser,
  schoolSettings,
  apiBaseUrl,
  initializeDashboardSession,
  refreshSchoolSettings,
} = useDashboardSession()

const tabs = [
  { id: 'event', label: 'Event Reports', icon: BarChart3 },
  { id: 'student', label: 'Student Reports', icon: UserRound },
  { id: 'school', label: 'School Summary', icon: Building2 },
  { id: 'system', label: 'System Logs', icon: FileText },
]
const validTabs = new Set(tabs.map((tab) => tab.id))
const activeTab = ref('event')

const filters = reactive({
  startDate: '',
  endDate: '',
  eventId: '',
  studentId: '',
  departmentId: '',
})

const searchQuery = ref('')
const attendeeQuery = ref('')
const studentRecordQuery = ref('')

const events = ref([])
const departments = ref([])
const selectedEventId = ref(null)
const selectedEventReport = ref(null)
const selectedEventRecords = ref([])
const eventCache = new Map()

const isLoadingEvents = ref(true)
const isLoadingSelection = ref(false)
const isDownloading = ref('')
const selectionError = ref('')

const overviewRows = ref([])
const studentReport = ref(null)
const studentStats = ref(null)
const schoolSummary = ref(null)
const auditLogs = ref({ total: 0, items: [] })
const notificationLogs = ref([])
const importReport = ref(null)

const isLoadingOverview = ref(false)
const isLoadingSchoolSummary = ref(false)
const isLoadingSystemLogs = ref(false)
const isLoadingImport = ref(false)

const attendanceOverviewError = ref('')
const schoolSummaryError = ref('')
const systemLogsError = ref('')
const importError = ref('')

const importJobId = ref('')
const importPreviewToken = ref('')
const isMobileViewport = ref(false)
const mobileFiltersOpen = ref(false)

let mobileMediaQuery = null

const activeUser = computed(() => currentUser.value)
const activeSchoolSettings = computed(() => schoolSettings.value)
const schoolId = computed(() => Number(activeUser.value?.school_id ?? activeSchoolSettings.value?.school_id ?? authMeta.value?.schoolId))
const displayName = computed(() => {
  const first = activeUser.value?.first_name || authMeta.value?.firstName || ''
  const middle = activeUser.value?.middle_name || ''
  const last = activeUser.value?.last_name || authMeta.value?.lastName || ''
  return [first, middle, last].filter(Boolean).join(' ') || activeUser.value?.email?.split('@')[0] || 'Campus Admin'
})
const initials = computed(() => {
  const parts = String(displayName.value || '').split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return String(displayName.value || '').slice(0, 2).toUpperCase()
})
const avatarUrl = computed(() => activeUser.value?.avatar_url || '')

const scopedEvents = computed(() => filterWorkspaceEntitiesBySchool(events.value, schoolId.value))
const scopedDepartments = computed(() => filterWorkspaceEntitiesBySchool(departments.value, schoolId.value))

const eventFilterOptions = computed(() => [...scopedEvents.value].sort((a, b) => new Date(b.start_datetime || 0) - new Date(a.start_datetime || 0)))
const studentFilterOptions = computed(() => [...overviewRows.value].sort((a, b) => String(a.full_name || '').localeCompare(String(b.full_name || ''))))
const departmentFilterOptions = computed(() => [...scopedDepartments.value].sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''))))

const filteredEvents = computed(() => {
  const query = String(searchQuery.value || '').trim().toLowerCase()
  const start = parseDateInput(filters.startDate)
  const end = parseDateInput(filters.endDate)
  return eventFilterOptions.value
    .filter((event) => isDateInRange(event.start_datetime, start, end))
    .filter((event) => {
      if (!query) return true
      return [event.name, event.location].filter(Boolean).join(' ').toLowerCase().includes(query)
    })
})

const selectedEvent = computed(() => scopedEvents.value.find((event) => Number(event.id) === Number(selectedEventId.value)) || null)

const filteredAttendanceRows = computed(() => {
  const query = String(attendeeQuery.value || '').trim().toLowerCase()
  const latestByStudent = new Map()

  for (const record of Array.isArray(selectedEventRecords.value) ? selectedEventRecords.value : []) {
    const key = String(record?.student_id || record?.student_name || record?.attendance?.student_id || '')
    const existing = latestByStudent.get(key)
    const ts = new Date(record?.attendance?.time_out || record?.attendance?.time_in || 0).getTime()
    const existingTs = new Date(existing?.attendance?.time_out || existing?.attendance?.time_in || 0).getTime()
    if (!existing || ts > existingTs) latestByStudent.set(key, record)
  }

  const rows = Array.from(latestByStudent.values()).map((record) => {
    const attendance = record?.attendance || {}
    const status = resolveAttendanceStatus(attendance)
    return {
      key: `${record?.student_id || record?.student_name || 'student'}:${attendance.id || attendance.time_in || 'row'}`,
      studentId: String(record?.student_id || 'N/A'),
      studentName: String(record?.student_name || 'Unknown Student'),
      statusLabel: formatStatusLabel(status),
      timeInLabel: formatDateTime(attendance.time_in, 'N/A'),
      timeOutLabel: formatDateTime(attendance.time_out, status === 'waiting' ? 'Waiting' : 'N/A'),
      methodLabel: formatMethod(attendance.method),
    }
  })

  if (!query) return rows
  return rows.filter((row) => [row.studentId, row.studentName, row.statusLabel, row.methodLabel].join(' ').toLowerCase().includes(query))
})

const filteredStudentRecords = computed(() => {
  const rows = Array.isArray(studentReport.value?.attendance_records) ? studentReport.value.attendance_records : []
  const query = String(studentRecordQuery.value || '').trim().toLowerCase()
  if (!query) return rows
  return rows.filter((record) => [record.event_name, record.status, record.display_status, record.method].filter(Boolean).join(' ').toLowerCase().includes(query))
})

const schoolSummaryPayload = computed(() => schoolSummary.value?.summary || null)

const eventSummaryCards = computed(() => {
  const report = selectedEventReport.value
  if (!report) return []
  return [
    { id: 'participants', label: 'Total Participants', value: formatWhole(report.total_participants), meta: 'Students in event scope.' },
    { id: 'attendees', label: 'Attended', value: formatWhole(report.attendees), meta: 'Completed attendance rows.' },
    { id: 'late', label: 'Late', value: formatWhole(report.late_attendees), meta: 'Late attendees.' },
    { id: 'incomplete', label: 'Waiting', value: formatWhole(report.incomplete_attendees), meta: 'Waiting for sign-out.' },
    { id: 'absent', label: 'Absent', value: formatWhole(report.absentees), meta: 'Absent records.' },
    { id: 'rate', label: 'Attendance Rate', value: `${formatPercent(report.attendance_rate)}%`, meta: 'Attended vs participants.' },
  ]
})

const studentSummaryCards = computed(() => {
  const summary = studentReport.value?.student
  if (!summary) return []
  return [
    { id: 'total', label: 'Total Events', value: formatWhole(summary.total_events), meta: 'Events in selected range.' },
    { id: 'attended', label: 'Attended', value: formatWhole(summary.attended_events), meta: 'Present + late.' },
    { id: 'late', label: 'Late', value: formatWhole(summary.late_events), meta: 'Late records.' },
    { id: 'absent', label: 'Absent', value: formatWhole(summary.absent_events), meta: 'Absent records.' },
    { id: 'excused', label: 'Excused', value: formatWhole(summary.excused_events), meta: 'Excused records.' },
    { id: 'rate', label: 'Attendance Rate', value: `${formatPercent(summary.attendance_rate)}%`, meta: 'Attended vs total.' },
  ]
})

const schoolSummaryCards = computed(() => {
  const summary = schoolSummaryPayload.value
  if (!summary) return []
  return [
    { id: 'total', label: 'Total Records', value: formatWhole(summary.total_attendance_records), meta: 'Attendance rows.' },
    { id: 'attended', label: 'Attended', value: formatWhole(summary.attended_count), meta: 'Present + late rows.' },
    { id: 'rate', label: 'Attendance Rate', value: `${formatPercent(summary.attendance_rate)}%`, meta: 'Attended vs total.' },
    { id: 'students', label: 'Unique Students', value: formatWhole(summary.unique_students), meta: 'Distinct students.' },
    { id: 'events', label: 'Unique Events', value: formatWhole(summary.unique_events), meta: 'Distinct events.' },
    { id: 'excused', label: 'Excused', value: formatWhole(summary.excused_count), meta: 'Excused rows.' },
  ]
})

const topStudentsRows = computed(() => [...overviewRows.value].sort((a, b) => Number(b.attendance_rate || 0) - Number(a.attendance_rate || 0)).slice(0, 20))
const auditRows = computed(() => Array.isArray(auditLogs.value?.items) ? auditLogs.value.items : [])
const notificationRows = computed(() => Array.isArray(notificationLogs.value) ? notificationLogs.value : [])
const importErrors = computed(() => Array.isArray(importReport.value?.jobStatus?.errors) ? importReport.value.jobStatus.errors : [])

const eventChartRows = computed(() => filteredEvents.value.slice(0, 10).map((event) => {
  const report = eventCache.get(Number(event.id))?.report
  const summary = event.attendance_summary || {}
  return {
    name: event.name,
    date: event.start_datetime,
    total: Number(report?.total_participants ?? summary.total_attendance_records ?? 0),
    attended: Number(report?.attendees ?? summary.attended_count ?? summary.present_count ?? 0),
    late: Number(report?.late_attendees ?? summary.late_count ?? 0),
    absent: Number(report?.absentees ?? summary.absent_count ?? 0),
    excused: Number(summary.excused_count ?? 0),
  }
}))

const eventBarChartData = computed(() => ({
  labels: eventChartRows.value.map((row) => row.name),
  datasets: [{ label: 'Attended', data: eventChartRows.value.map((row) => row.attended), backgroundColor: 'rgba(0,87,184,0.88)', borderRadius: 10 }],
}))

const eventPieChartData = computed(() => {
  const report = selectedEventReport.value
  if (!report) return { labels: [], datasets: [] }
  const late = Number(report.late_attendees || 0)
  const absent = Number(report.absentees || 0)
  const present = Math.max(Number(report.attendees || 0) - late, 0)
  const excused = Number(report.excused_attendees || 0)
  return {
    labels: ['Present', 'Late', 'Absent', 'Excused'],
    datasets: [{ data: [present, late, absent, excused], backgroundColor: ['rgba(0,87,184,0.88)', 'rgba(245,158,11,0.88)', 'rgba(239,68,68,0.88)', 'rgba(16,185,129,0.88)'], borderWidth: 0 }],
  }
})

const eventLineChartData = computed(() => buildMonthlyLineData(eventChartRows.value))
const schoolLineChartData = computed(() => buildMonthlyLineData(eventChartRows.value))

const studentPieChartData = computed(() => {
  const summary = studentReport.value?.student
  if (!summary) return { labels: [], datasets: [] }
  return {
    labels: ['Present', 'Late', 'Absent', 'Excused'],
    datasets: [{ data: [Number(summary.attended_events || 0) - Number(summary.late_events || 0), Number(summary.late_events || 0), Number(summary.absent_events || 0), Number(summary.excused_events || 0)], backgroundColor: ['rgba(0,87,184,0.88)', 'rgba(245,158,11,0.88)', 'rgba(239,68,68,0.88)', 'rgba(16,185,129,0.88)'], borderWidth: 0 }],
  }
})

const studentLineChartData = computed(() => buildStudentTrendLineData(studentStats.value?.trend_data))

const schoolPieChartData = computed(() => {
  const summary = schoolSummaryPayload.value
  if (!summary) return { labels: [], datasets: [] }
  return {
    labels: ['Present', 'Late', 'Absent', 'Excused'],
    datasets: [{ data: [Number(summary.present_count || 0), Number(summary.late_count || 0), Number(summary.absent_count || 0), Number(summary.excused_count || 0)], backgroundColor: ['rgba(0,87,184,0.88)', 'rgba(245,158,11,0.88)', 'rgba(239,68,68,0.88)', 'rgba(16,185,129,0.88)'], borderWidth: 0 }],
  }
})

const schoolBarChartData = computed(() => ({
  labels: topStudentsRows.value.slice(0, 8).map((row) => row.full_name),
  datasets: [{ label: 'Attendance Rate (%)', data: topStudentsRows.value.slice(0, 8).map((row) => roundPercent(row.attendance_rate)), backgroundColor: 'rgba(0,87,184,0.88)', borderRadius: 10 }],
}))

const chartOptions = {
  pie: { plugins: { legend: { position: 'bottom' } } },
  line: { scales: { y: { beginAtZero: true } } },
  bar: { scales: { y: { beginAtZero: true } } },
  barPercent: { scales: { y: { beginAtZero: true, max: 100 } } },
}

let selectionRequestId = 0
let overviewRequestId = 0
let studentRequestId = 0
let summaryRequestId = 0
let logsRequestId = 0

onMounted(async () => {
  initializeMobileLayout()
  await initializeDashboardSession().catch(() => null)
  if (!schoolSettings.value) await refreshSchoolSettings().catch(() => null)
  applyTabFromRoute()
  await Promise.all([loadEvents(), loadDepartments(), loadAttendanceOverview(), loadSchoolSummary(), loadSystemLogs()])
  await syncEventFromRoute()
})

onBeforeUnmount(() => {
  teardownMobileLayout()
})

watch(() => route.query.section, () => applyTabFromRoute(), { immediate: true })
watch([() => route.query.eventId, scopedEvents, isLoadingEvents], () => { syncEventFromRoute().catch(() => null) }, { immediate: true })
watch(() => filters.eventId, () => { handleEventFilterChange().catch(() => null) })
watch(() => filters.studentId, () => { loadStudentReport().catch(() => null) })
watch(() => [filters.startDate, filters.endDate, filters.departmentId], () => {
  loadAttendanceOverview().catch(() => null)
  loadSchoolSummary().catch(() => null)
})
watch(filteredEvents, () => { prefetchEventReports().catch(() => null) })

function resolveApiContext() {
  return {
    token: localStorage.getItem('aura_token') || '',
    baseUrl: apiBaseUrl.value || '',
  }
}

function applyMobileViewport(matches) {
  const wasMobile = isMobileViewport.value
  isMobileViewport.value = Boolean(matches)

  if (isMobileViewport.value && !wasMobile) {
    mobileFiltersOpen.value = false
  }

  if (!isMobileViewport.value) {
    mobileFiltersOpen.value = true
  }
}

function initializeMobileLayout() {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return
  mobileMediaQuery = window.matchMedia('(max-width: 720px)')
  applyMobileViewport(mobileMediaQuery.matches)

  if (typeof mobileMediaQuery.addEventListener === 'function') {
    mobileMediaQuery.addEventListener('change', handleMobileViewportChange)
    return
  }

  if (typeof mobileMediaQuery.addListener === 'function') {
    mobileMediaQuery.addListener(handleMobileViewportChange)
  }
}

function teardownMobileLayout() {
  if (!mobileMediaQuery) return

  if (typeof mobileMediaQuery.removeEventListener === 'function') {
    mobileMediaQuery.removeEventListener('change', handleMobileViewportChange)
    mobileMediaQuery = null
    return
  }

  if (typeof mobileMediaQuery.removeListener === 'function') {
    mobileMediaQuery.removeListener(handleMobileViewportChange)
  }
  mobileMediaQuery = null
}

function handleMobileViewportChange(event) {
  applyMobileViewport(event?.matches)
}

function toggleMobileFilters() {
  if (!isMobileViewport.value) return
  mobileFiltersOpen.value = !mobileFiltersOpen.value
}

function applyTabFromRoute() {
  const section = String(route.query.section || '').trim().toLowerCase()
  activeTab.value = validTabs.has(section) ? section : 'event'
}

function setActiveTab(tabId) {
  if (!validTabs.has(tabId)) return
  activeTab.value = tabId
  if (String(route.query.section || '').toLowerCase() === tabId) return
  router.replace({ query: { ...route.query, section: tabId } }).catch(() => null)
}

async function loadEvents() {
  isLoadingEvents.value = true

  try {
    events.value = await getReportEvents(resolveApiContext())
  } catch (error) {
    selectionError.value = error?.message || 'Unable to load events.'
  } finally {
    isLoadingEvents.value = false
  }
}

async function prefetchEventReports() {
  const candidates = filteredEvents.value.slice(0, 8)
  if (!candidates.length) return
  await Promise.all(candidates.map(async (event) => {
    try {
      await getEventBundle(event)
    } catch {
      return null
    }
    return null
  }))
}

async function loadDepartments() {
  try {
    departments.value = await getReportDepartments(resolveApiContext())
  } catch {
    departments.value = []
  }
}

async function loadAttendanceOverview() {
  const requestId = ++overviewRequestId
  isLoadingOverview.value = true
  attendanceOverviewError.value = ''

  try {
    const rows = await getAttendanceOverview({
      ...resolveApiContext(),
      params: {
        start_date: filters.startDate || undefined,
        end_date: filters.endDate || undefined,
        department_id: toPositiveInt(filters.departmentId),
        limit: 250,
      },
    })

    if (requestId !== overviewRequestId) return
    overviewRows.value = Array.isArray(rows) ? rows : []

    if (filters.studentId && !overviewRows.value.some((row) => Number(row.id) === Number(filters.studentId))) {
      filters.studentId = ''
    }
    if (!filters.studentId && overviewRows.value.length) {
      filters.studentId = String(overviewRows.value[0].id)
    }
  } catch (error) {
    if (requestId !== overviewRequestId) return
    attendanceOverviewError.value = error?.message || 'Unable to load student overview.'
    overviewRows.value = []
  } finally {
    if (requestId === overviewRequestId) isLoadingOverview.value = false
  }
}

async function loadStudentReport() {
  const studentId = toPositiveInt(filters.studentId)
  if (!studentId) {
    studentReport.value = null
    studentStats.value = null
    return
  }

  const requestId = ++studentRequestId
  try {
    const payload = await Promise.all([
      getStudentReport(studentId, {
        ...resolveApiContext(),
        params: {
          start_date: filters.startDate || undefined,
          end_date: filters.endDate || undefined,
        },
      }),
      getStudentStats(studentId, {
        ...resolveApiContext(),
        params: {
          start_date: filters.startDate || undefined,
          end_date: filters.endDate || undefined,
          group_by: 'month',
        },
      }),
    ])

    if (requestId !== studentRequestId) return
    studentReport.value = payload[0]
    studentStats.value = payload[1]
  } catch {
    if (requestId !== studentRequestId) return
    studentReport.value = null
    studentStats.value = null
  }
}

async function loadSchoolSummary() {
  const requestId = ++summaryRequestId
  isLoadingSchoolSummary.value = true
  schoolSummaryError.value = ''

  try {
    const payload = await getSchoolSummary({
      ...resolveApiContext(),
      params: {
        start_date: filters.startDate || undefined,
        end_date: filters.endDate || undefined,
        department_id: toPositiveInt(filters.departmentId),
      },
    })

    if (requestId !== summaryRequestId) return
    schoolSummary.value = payload
  } catch (error) {
    if (requestId !== summaryRequestId) return
    schoolSummaryError.value = error?.message || 'Unable to load school summary.'
    schoolSummary.value = null
  } finally {
    if (requestId === summaryRequestId) isLoadingSchoolSummary.value = false
  }
}

async function loadSystemLogs() {
  const requestId = ++logsRequestId
  isLoadingSystemLogs.value = true
  systemLogsError.value = ''

  try {
    const [auditPayload, notificationPayload] = await Promise.all([
      getAuditLogs({
        ...resolveApiContext(),
        params: {
          limit: 100,
          offset: 0,
          start_date: filters.startDate || undefined,
          end_date: filters.endDate || undefined,
        },
      }),
      getNotificationLogs({ ...resolveApiContext(), params: { limit: 150 } }),
    ])

    if (requestId !== logsRequestId) return
    auditLogs.value = auditPayload || { total: 0, items: [] }
    notificationLogs.value = Array.isArray(notificationPayload) ? notificationPayload : []
  } catch (error) {
    if (requestId !== logsRequestId) return
    systemLogsError.value = error?.message || 'Unable to load system logs.'
    auditLogs.value = { total: 0, items: [] }
    notificationLogs.value = []
  } finally {
    if (requestId === logsRequestId) isLoadingSystemLogs.value = false
  }
}

async function loadImportReport() {
  const jobId = String(importJobId.value || '').trim()
  const previewToken = String(importPreviewToken.value || '').trim()
  importError.value = ''

  if (!jobId && !previewToken) {
    importError.value = 'Enter an import job ID or preview token.'
    return
  }

  isLoadingImport.value = true
  try {
    importReport.value = await getImportReports({
      ...resolveApiContext(),
      jobId: jobId || undefined,
      previewToken: previewToken || undefined,
    })
  } catch (error) {
    importError.value = error?.message || 'Unable to load import report.'
    importReport.value = null
  } finally {
    isLoadingImport.value = false
  }
}

async function syncEventFromRoute() {
  const routeEventId = normalizeId(route.query.eventId)
  if (!routeEventId) {
    if (selectedEventId.value != null) clearSelection({ updateRoute: false })
    return
  }
  if (routeEventId === Number(selectedEventId.value) && selectedEventReport.value) return

  const event = scopedEvents.value.find((item) => Number(item.id) === routeEventId)
  if (!event) return
  filters.eventId = String(routeEventId)
  await viewEvent(event, { updateRoute: false })
}

async function handleEventFilterChange() {
  const eventId = normalizeId(filters.eventId)
  if (!eventId) {
    if (selectedEventId.value != null) clearSelection()
    return
  }
  if (eventId === Number(selectedEventId.value)) return

  const event = scopedEvents.value.find((item) => Number(item.id) === eventId)
  if (!event) return
  await viewEvent(event)
}

async function viewEvent(event, { updateRoute = true } = {}) {
  const eventId = Number(event?.id)
  if (!Number.isFinite(eventId)) return null

  selectedEventId.value = eventId
  filters.eventId = String(eventId)
  selectionError.value = ''
  isLoadingSelection.value = true
  const requestId = ++selectionRequestId

  if (updateRoute && normalizeId(route.query.eventId) !== eventId) {
    router.replace({ query: { ...route.query, eventId: String(eventId) } }).catch(() => null)
  }

  try {
    const bundle = await getEventBundle(event)
    if (requestId !== selectionRequestId) return null
    selectedEventReport.value = bundle.report
    selectedEventRecords.value = bundle.records
    return bundle
  } catch (error) {
    if (requestId !== selectionRequestId) return null
    selectionError.value = error?.message || 'Unable to load selected event report.'
    selectedEventReport.value = null
    selectedEventRecords.value = []
    return null
  } finally {
    if (requestId === selectionRequestId) isLoadingSelection.value = false
  }
}

async function getEventBundle(event) {
  const eventId = Number(event?.id)
  if (!Number.isFinite(eventId)) throw new Error('Invalid event')
  if (eventCache.has(eventId)) return eventCache.get(eventId)

  const bundle = await loadLiveEventBundle(eventId)

  eventCache.set(eventId, bundle)
  return bundle
}

async function loadLiveEventBundle(eventId) {
  const ctx = resolveApiContext()
  const [report, records] = await Promise.all([
    fetchEventReport(eventId, ctx),
    getEventAttendanceRecords(eventId, {
      ...ctx,
      params: {
        active_only: false,
      },
    }),
  ])
  return { report, records: Array.isArray(records) ? records : [] }
}

function clearSelection({ updateRoute = true } = {}) {
  selectedEventId.value = null
  selectedEventReport.value = null
  selectedEventRecords.value = []
  filters.eventId = ''
  attendeeQuery.value = ''

  if (updateRoute) {
    const nextQuery = { ...route.query }
    delete nextQuery.eventId
    router.replace({ query: nextQuery }).catch(() => null)
  }
}

function resetFilters() {
  filters.startDate = ''
  filters.endDate = ''
  filters.departmentId = ''
  if (selectedEventId.value != null) clearSelection()
}

async function downloadReport(event, format = 'csv') {
  const eventId = Number(event?.id)
  if (!Number.isFinite(eventId)) return

  const key = `${eventId}:${format}`
  if (isDownloading.value === key) return
  isDownloading.value = key

  try {
    const bundle = await viewEvent(event) || await getEventBundle(event)
    const rows = filteredAttendanceRows.value
    if (format === 'excel') downloadExcel(bundle.report, rows)
    else downloadCsv(bundle.report, rows)
  } finally {
    isDownloading.value = ''
  }
}

function downloadCsv(report, rows) {
  const lines = [
    ['Event', report?.event_name || 'Event'],
    ['Date', report?.event_date || 'N/A'],
    ['Location', report?.event_location || 'N/A'],
    [],
    ['Summary'],
    ['Total Participants', formatWhole(report?.total_participants || 0)],
    ['Completed Attendance', formatWhole(report?.attendees || 0)],
    ['Late Attendees', formatWhole(report?.late_attendees || 0)],
    ['Waiting for Sign Out', formatWhole(report?.incomplete_attendees || 0)],
    ['Absent', formatWhole(report?.absentees || 0)],
    ['Attendance Rate', `${formatPercent(report?.attendance_rate || 0)}%`],
    [],
    ['Student ID', 'Student Name', 'Status', 'Sign In', 'Sign Out', 'Method'],
    ...rows.map((row) => [row.studentId, row.studentName, row.statusLabel, row.timeInLabel, row.timeOutLabel, row.methodLabel]),
  ]
  const content = `\uFEFF${lines.map((line) => line.map(csvField).join(',')).join('\r\n')}`
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  triggerDownload(blob, `${sanitize(report?.event_name || 'event_report')}.csv`)
}

function downloadExcel(report, rows) {
  const html = `
    <html><head><meta charset="utf-8"></head><body>
    <h1>${escapeHtml(report?.event_name || 'Event Report')}</h1>
    <p>${escapeHtml(report?.event_date || 'N/A')} | ${escapeHtml(report?.event_location || 'N/A')}</p>
    <table border="1" cellspacing="0" cellpadding="6">
      <tr><th>Student ID</th><th>Student Name</th><th>Status</th><th>Sign In</th><th>Sign Out</th><th>Method</th></tr>
      ${rows.map((row) => `<tr><td>${escapeHtml(row.studentId)}</td><td>${escapeHtml(row.studentName)}</td><td>${escapeHtml(row.statusLabel)}</td><td>${escapeHtml(row.timeInLabel)}</td><td>${escapeHtml(row.timeOutLabel)}</td><td>${escapeHtml(row.methodLabel)}</td></tr>`).join('')}
    </table></body></html>`
  const blob = new Blob([`\uFEFF${html}`], { type: 'application/vnd.ms-excel;charset=utf-8;' })
  triggerDownload(blob, `${sanitize(report?.event_name || 'event_report')}.xls`)
}

function buildMonthlyLineData(rows) {
  const byMonth = new Map()
  for (const row of Array.isArray(rows) ? rows : []) {
    const date = new Date(row.date || '')
    if (Number.isNaN(date.getTime())) continue
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    if (!byMonth.has(key)) byMonth.set(key, { attended: 0, total: 0 })
    const bucket = byMonth.get(key)
    bucket.attended += Number(row.attended || 0)
    bucket.total += Number(row.total || 0)
  }
  const labels = Array.from(byMonth.keys()).sort((a, b) => a.localeCompare(b))
  return {
    labels,
    datasets: [{
      label: 'Attendance Rate (%)',
      data: labels.map((label) => {
        const bucket = byMonth.get(label)
        return bucket.total > 0 ? roundPercent((bucket.attended / bucket.total) * 100) : 0
      }),
      borderColor: 'rgba(0,87,184,0.88)',
      backgroundColor: 'rgba(0,87,184,0.88)',
      tension: 0.25,
    }],
  }
}

function buildStudentTrendLineData(rows) {
  const trendRows = Array.isArray(rows) ? rows : []
  if (!trendRows.length) return { labels: [], datasets: [] }

  const grouped = new Map()
  for (const row of trendRows) {
    const period = String(row?.period || '').trim()
    if (!period) continue
    if (!grouped.has(period)) grouped.set(period, { present: 0, late: 0, absent: 0, excused: 0 })
    const bucket = grouped.get(period)
    const status = normalizeStatus(row?.status)
    if (Object.hasOwn(bucket, status)) bucket[status] += Number(row?.count || 0)
  }

  const labels = Array.from(grouped.keys()).sort((a, b) => a.localeCompare(b))
  return {
    labels,
    datasets: [
      { label: 'Present', data: labels.map((label) => grouped.get(label).present), borderColor: 'rgba(0,87,184,0.88)', backgroundColor: 'rgba(0,87,184,0.88)', tension: 0.25 },
      { label: 'Late', data: labels.map((label) => grouped.get(label).late), borderColor: 'rgba(245,158,11,0.88)', backgroundColor: 'rgba(245,158,11,0.88)', tension: 0.25 },
      { label: 'Absent', data: labels.map((label) => grouped.get(label).absent), borderColor: 'rgba(239,68,68,0.88)', backgroundColor: 'rgba(239,68,68,0.88)', tension: 0.25 },
      { label: 'Excused', data: labels.map((label) => grouped.get(label).excused), borderColor: 'rgba(16,185,129,0.88)', backgroundColor: 'rgba(16,185,129,0.88)', tension: 0.25 },
    ],
  }
}

function parseDateInput(value) {
  if (!value) return null
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return null
  return date
}

function isDateInRange(value, start, end) {
  const date = new Date(value || 0)
  if (Number.isNaN(date.getTime())) return true
  if (start && date < start) return false
  if (end) {
    const endBoundary = new Date(end)
    endBoundary.setHours(23, 59, 59, 999)
    if (date > endBoundary) return false
  }
  return true
}

function resolveAttendanceStatus(attendance = {}) {
  const completion = String(attendance.completion_state || '').toLowerCase()
  const status = String(attendance.display_status || attendance.status || '').toLowerCase()
  if (completion !== 'completed') return 'waiting'
  if (status === 'late') return 'late'
  if (status === 'absent') return 'absent'
  if (status === 'excused') return 'excused'
  return 'present'
}

function normalizeStatus(status) {
  const value = String(status || '').toLowerCase()
  if (['present', 'late', 'absent', 'excused'].includes(value)) return value
  return 'waiting'
}

function formatStatusLabel(status) {
  const value = normalizeStatus(status)
  if (value === 'waiting') return 'Waiting'
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function formatMethod(method) {
  const value = String(method || '').trim().toLowerCase()
  if (value === 'face_scan') return 'Face Scan'
  if (value === 'manual') return 'Manual'
  return value || 'Unknown'
}

function normalizeId(value) {
  const raw = Array.isArray(value) ? value[0] : value
  const normalized = Number(raw)
  return Number.isFinite(normalized) ? normalized : null
}

function toPositiveInt(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized) || normalized <= 0) return undefined
  return Math.round(normalized)
}

function formatDate(value) {
  if (!value) return 'Unspecified Date'
  const normalized = String(value)
  const date = /^\d{4}-\d{2}-\d{2}$/.test(normalized) ? new Date(`${normalized}T00:00:00`) : new Date(normalized)
  if (Number.isNaN(date.getTime())) return normalized
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date)
}

function formatDateTime(value, fallback = 'N/A') {
  if (!value) return fallback
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date)
}

function roundPercent(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return 0
  return Math.max(0, Math.min(100, Math.round(normalized)))
}

function formatPercent(value) {
  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized.toFixed(2).replace(/\.00$/, '') : '0'
}

function formatWhole(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return '0'
  return Math.round(normalized).toLocaleString('en-US')
}

function sanitize(value) {
  return String(value || 'event_report').trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'event_report'
}

function csvField(value) {
  const text = String(value ?? '')
  const safe = /^[=+\-@]/.test(text) ? `'${text}` : text
  return `"${safe.replace(/"/g, '""')}"`
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function goBack() {
  router.push({ name: 'SchoolItSchedule' })
}

async function handleLogout() {
  await logout()
}
</script>

<style scoped>
.school-it-reports {
  min-height: 100vh;
  padding: 30px 28px 120px;
  font-family: 'Manrope', sans-serif;
  background: var(--color-bg, #f3f4f6);
}

.school-it-reports__shell {
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
}

.school-it-reports__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 32px;
}

.school-it-reports__header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.school-it-reports__back {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.school-it-reports__header-copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.school-it-reports__title {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  color: var(--color-text-always-dark, #111827);
}

.school-it-reports__subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--color-text-secondary, #6b7280);
}

.school-it-reports__filters-panel {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  padding: 16px;
  border-radius: 24px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.06);
}

.school-it-reports__filters-toggle {
  display: none;
  min-height: 42px;
  border: none;
  border-radius: 999px;
  padding: 0 14px;
  background: #ffffff;
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
  color: #111827;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
}

.school-it-reports__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.school-it-reports__field-input {
  min-height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  padding: 0 10px;
  font: inherit;
  font-size: 14px;
  text-transform: none;
  letter-spacing: 0;
  color: #111827;
  background: #fff;
}

.school-it-reports__clear-btn {
  min-height: 40px;
  border: none;
  border-radius: 999px;
  padding: 0 14px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
}

.school-it-reports__tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.school-it-reports__tab {
  border: none;
  border-radius: 999px;
  min-height: 38px;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.9);
  color: #334155;
  white-space: nowrap;
}

.school-it-reports__tab--active {
  background: var(--color-primary, #0057B8);
  color: #fff;
}

.school-it-reports__content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px;
  border-radius: 28px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.08);
}

.school-it-reports__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.school-it-reports__search-shell {
  width: min(100%, 360px);
  height: 44px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  display: flex;
  align-items: center;
  padding: 0 10px 0 16px;
}

.school-it-reports__search-input {
  flex: 1;
  border: none;
  outline: none;
  font: inherit;
  font-size: 14px;
  color: #111827;
  background: transparent;
}

.school-it-reports__search-icon {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}

.school-it-reports__table-wrap {
  overflow-x: auto;
  width: 100%;
}

.school-it-reports__table {
  width: 100%;
  min-width: 760px;
  border-collapse: separate;
  border-spacing: 0;
}

.school-it-reports__table th {
  text-align: left;
  padding: 12px 14px;
  border-bottom: 2px solid #f1f5f9;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.school-it-reports__table td {
  padding: 14px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.school-it-reports__table-row--selected {
  background: color-mix(in srgb, var(--color-primary, #0057B8) 10%, white);
}

.school-it-reports__cell-actions {
  display: inline-flex;
  gap: 8px;
}

.school-it-reports__empty {
  text-align: center !important;
  color: #64748b;
  padding: 28px !important;
}

.school-it-reports__btn {
  border: none;
  border-radius: 999px;
  min-height: 34px;
  padding: 0 14px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.school-it-reports__btn--view {
  background: var(--color-primary, #0057B8);
  color: #fff;
}

.school-it-reports__btn--dark {
  background: #111827;
  color: #fff;
}

.school-it-reports__btn--accent {
  background: var(--color-secondary, #FFD400);
  color: #111827;
}

.school-it-reports__banner {
  border-radius: 16px;
  padding: 12px 14px;
  background: color-mix(in srgb, var(--color-primary, #0057B8) 8%, white);
  color: #0f172a;
}

.school-it-reports__banner--error {
  background: color-mix(in srgb, #ef4444 12%, white);
  color: #991b1b;
}

.school-it-reports__detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.school-it-reports__section-title {
  margin: 0;
  font-size: 21px;
  font-weight: 800;
  color: #111827;
}

.school-it-reports__section-subtitle {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

.school-it-reports__actions {
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
}

.school-it-reports__stats-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.school-it-reports__stat-card {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: #fff;
}

.school-it-reports__stat-card span {
  font-size: 12px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 800;
}

.school-it-reports__stat-card strong {
  font-size: 24px;
  line-height: 1.1;
  color: var(--color-primary, #0057B8);
}

.school-it-reports__stat-card small {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.school-it-reports__chart-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.school-it-reports__chart-scroll {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}

.school-it-reports__chart-canvas {
  min-width: 0;
}

.school-it-reports__panel {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
  background: #fff;
}

.school-it-reports__panel h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #111827;
}

.school-it-reports__panel-empty {
  margin: 0;
  color: #64748b;
  font-size: 13px;
}

.school-it-reports__import-tools {
  display: grid;
  gap: 8px;
  grid-template-columns: 1fr 1fr auto;
  margin-bottom: 10px;
}

.school-it-reports__skeleton-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.school-it-reports__skeleton-card {
  min-height: 140px;
  border-radius: 16px;
  background: linear-gradient(90deg, rgba(226, 232, 240, 0.8) 25%, rgba(241, 245, 249, 0.95) 50%, rgba(226, 232, 240, 0.8) 75%);
  background-size: 220% 100%;
  animation: reports-skeleton 1.2s ease-in-out infinite;
}

@keyframes reports-skeleton {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

@media (max-width: 1160px) {
  .school-it-reports__filters-panel {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .school-it-reports {
    padding: 20px 12px 80px;
  }

  .school-it-reports__header {
    align-items: center;
  }

  .school-it-reports__title {
    font-size: 22px;
  }

  .school-it-reports__filters-toggle {
    display: inline-flex;
    width: 100%;
  }

  .school-it-reports__content {
    padding: 16px;
  }

  .school-it-reports__filters-panel {
    grid-template-columns: 1fr;
    padding: 12px;
    border-radius: 16px;
  }

  .school-it-reports__stats-grid,
  .school-it-reports__chart-grid {
    grid-template-columns: 1fr;
  }

  .school-it-reports__actions {
    width: 100%;
  }

  .school-it-reports__actions .school-it-reports__btn {
    flex: 1 1 auto;
    justify-content: center;
  }

  .school-it-reports__cell-actions {
    display: flex;
    flex-direction: column;
  }

  .school-it-reports__table {
    min-width: 640px;
  }

  .school-it-reports__chart-canvas {
    min-width: 420px;
  }

  .school-it-reports__search-shell {
    width: 100%;
  }

  .school-it-reports__import-tools {
    grid-template-columns: 1fr;
  }
}
</style>
