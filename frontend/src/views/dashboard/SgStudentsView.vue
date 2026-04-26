<template>
  <section class="sg-sub-page sg-students-page">
    <header class="sg-sub-header dashboard-enter dashboard-enter--1">
      <button class="sg-sub-back" type="button" @click="goBack">
        <ArrowLeft :size="20" />
      </button>
      <h1 class="sg-sub-title">Students</h1>
    </header>

    <div v-if="isLoading" class="sg-sub-loading dashboard-enter dashboard-enter--2">
      <p>Loading students...</p>
    </div>

    <div v-else-if="loadError" class="sg-sub-error dashboard-enter dashboard-enter--2">
      <p>{{ loadError }}</p>
      <button class="sg-sub-action" type="button" @click="reload">Try Again</button>
    </div>

    <template v-else>
      <div class="sg-sub-toolbar dashboard-enter dashboard-enter--2">
        <div class="sg-sub-search-shell">
          <input
            v-model="searchQuery"
            type="text"
            class="sg-sub-search-input"
            placeholder="Search students"
          />
          <Search :size="14" style="color: var(--color-text-muted);" />
        </div>
      </div>

      <div class="sg-student-directory dashboard-enter dashboard-enter--3">
        <div class="sg-student-directory-header">
          <span>Student List</span>
          <strong>{{ filteredStudents.length }}</strong>
        </div>

        <div v-if="filteredStudents.length" class="sg-students-list">
          <button
            v-for="student in filteredStudents"
            :key="studentKey(student)"
            type="button"
            class="sg-student-row"
            :aria-label="`View attendance for ${studentName(student)}`"
            @click="openStudentDetail(student)"
          >
            <span class="sg-student-avatar" aria-hidden="true">
              {{ studentInitials(student) }}
            </span>
            <span class="sg-student-info">
              <span class="sg-student-name">{{ studentName(student) }}</span>
              <span class="sg-student-id-line">{{ studentProfile(student)?.student_id || 'No student ID' }}</span>
              <span class="sg-student-meta-line">
                <span v-for="meta in studentMetaItems(student)" :key="meta" class="sg-student-meta-pill">
                  {{ meta }}
                </span>
              </span>
            </span>
            <span class="sg-student-action" aria-hidden="true">
              <ChevronRight :size="18" />
            </span>
          </button>
        </div>

        <p v-else class="sg-sub-empty">No students found.</p>
      </div>
    </template>

    <transition name="sg-sheet">
      <div
        v-if="selectedStudent"
        class="sg-sheet-backdrop"
        @click.self="closeStudentDetail"
      >
        <section
          class="sg-sheet sg-student-detail-sheet"
          role="dialog"
          aria-modal="true"
          :aria-label="`${selectedStudentName} attendance detail`"
        >
          <div class="sg-detail-scroll">
            <header class="sg-detail-header">
              <span class="sg-detail-avatar" aria-hidden="true">
                {{ studentInitials(selectedStudent) }}
              </span>
              <div class="sg-detail-heading">
                <h2>{{ selectedStudentName }}</h2>
                <p>{{ selectedProfile?.student_id || 'No student ID' }}</p>
              </div>
              <button
                class="sg-detail-close"
                type="button"
                aria-label="Close student detail"
                @click="closeStudentDetail"
              >
                <X :size="18" />
              </button>
            </header>

            <div class="sg-detail-meta">
              <span v-for="meta in selectedMetaItems" :key="meta">
                {{ meta }}
              </span>
            </div>

            <div v-if="detailLoading" class="sg-detail-state">
              <p>Loading attendance...</p>
            </div>

            <div v-else-if="detailError" class="sg-detail-state sg-detail-state--error">
              <p>{{ detailError }}</p>
              <button class="sg-detail-retry" type="button" @click="loadSelectedStudentAttendance">
                <RefreshCw :size="14" />
                Retry
              </button>
            </div>

            <template v-else>
              <div class="sg-detail-stat-grid">
                <div
                  v-for="stat in detailStats"
                  :key="stat.label"
                  class="sg-detail-stat"
                >
                  <strong>{{ stat.value }}</strong>
                  <span>{{ stat.label }}</span>
                </div>
              </div>

              <div class="sg-records-header">
                <span>Attendance</span>
                <strong>{{ detailRecords.length }}</strong>
              </div>

              <div v-if="detailRecords.length" class="sg-attendance-records">
                <article
                  v-for="record in detailRecords"
                  :key="recordKey(record)"
                  class="sg-attendance-record"
                >
                  <time class="sg-record-date" :datetime="record.event_date || record.time_in || ''">
                    <span>{{ formatMonth(record.event_date || record.time_in) }}</span>
                    <strong>{{ formatDay(record.event_date || record.time_in) }}</strong>
                  </time>
                  <div class="sg-record-main">
                    <h3>{{ record.event_name || 'Event' }}</h3>
                    <p>
                      <MapPin :size="13" />
                      <span>{{ record.event_location || 'No location' }}</span>
                    </p>
                    <p>
                      <Clock3 :size="13" />
                      <span>{{ formatTimeRange(record) }}</span>
                    </p>
                  </div>
                  <span
                    class="sg-status-badge"
                    :class="`sg-status-badge--${statusKey(record.display_status || record.status)}`"
                  >
                    {{ statusLabel(record.display_status || record.status) }}
                  </span>
                </article>
              </div>

              <div v-else class="sg-detail-empty">
                <CalendarDays :size="22" />
                <p>No attendance records yet.</p>
              </div>
            </template>
          </div>
        </section>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, CalendarDays, ChevronRight, Clock3, MapPin, RefreshCw, Search, X } from 'lucide-vue-next'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useGovernanceAccess } from '@/composables/useGovernanceAccess.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import { getGovernanceStudents, getStudentAttendanceReport } from '@/services/backendApi.js'
import { withPreservedGovernancePreviewQuery } from '@/services/routeWorkspace.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()
const { apiBaseUrl } = useDashboardSession()
const { governanceContext } = useGovernanceAccess()
const { previewBundle } = useSgPreviewBundle(() => props.preview)
const { isLoading: sgLoading } = useSgDashboard(props.preview)

const isLoading = ref(true)
const loadError = ref('')
const students = ref([])
const searchQuery = ref('')
const selectedStudent = ref(null)
const selectedStudentReport = ref(null)
const detailLoading = ref(false)
const detailError = ref('')
let detailRequestId = 0

const filteredStudents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return students.value
  return students.value.filter((s) =>
    [
      studentProfile(s)?.student_id,
      studentName(s),
      studentUser(s)?.email,
      studentProfile(s)?.department_name,
      studentProfile(s)?.program_name,
      studentProfile(s)?.year_level,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
      .includes(q)
  )
})

const selectedProfile = computed(() => studentProfile(selectedStudent.value))
const selectedStudentName = computed(() => (
  selectedStudent.value ? studentName(selectedStudent.value) : 'Student'
))
const selectedMetaItems = computed(() => (
  selectedStudent.value ? studentMetaItems(selectedStudent.value) : []
))
const detailSummary = computed(() => (
  selectedStudentReport.value?.student || {
    student_id: selectedProfile.value?.student_id || null,
    student_name: selectedStudentName.value,
    total_events: 0,
    attended_events: 0,
    late_events: 0,
    incomplete_events: 0,
    absent_events: 0,
    excused_events: 0,
    attendance_rate: 0,
    last_attendance: null,
  }
))
const detailRecords = computed(() => (
  Array.isArray(selectedStudentReport.value?.attendance_records)
    ? selectedStudentReport.value.attendance_records
    : []
))
const detailStats = computed(() => [
  { label: 'Rate', value: formatPercent(detailSummary.value.attendance_rate) },
  { label: 'Present', value: detailSummary.value.attended_events ?? 0 },
  { label: 'Late', value: detailSummary.value.late_events ?? 0 },
  { label: 'Absent', value: detailSummary.value.absent_events ?? 0 },
])

function studentUser(student) {
  return student?.user || student || null
}

function studentProfile(student) {
  return student?.student_profile || student?.user?.student_profile || null
}

function studentName(s) {
  const user = studentUser(s)
  return [user?.first_name, user?.last_name].filter(Boolean).join(' ').trim() || user?.email || 'Student'
}

function studentInitials(student) {
  const user = studentUser(student)
  const first = String(user?.first_name || '').trim().charAt(0)
  const last = String(user?.last_name || '').trim().charAt(0)
  const initials = `${first}${last}`.trim()
  return initials || String(studentName(student)).trim().charAt(0).toUpperCase() || 'S'
}

function studentKey(student) {
  const profile = studentProfile(student)
  return profile?.id || profile?.student_id || studentUser(student)?.id || student?.id || studentName(student)
}

function studentMetaItems(student) {
  const profile = studentProfile(student)
  const items = []
  if (profile?.program_name) items.push(profile.program_name)
  else if (profile?.department_name) items.push(profile.department_name)
  if (profile?.year_level) items.push(`Year ${profile.year_level}`)
  return items.length ? items : ['Student']
}

function governanceQueryParams() {
  const context = String(governanceContext.value || '').trim()
  return context ? { governance_context: context } : {}
}

function goBack() {
  router.push(
    props.preview
      ? withPreservedGovernancePreviewQuery(route, '/exposed/governance')
      : '/governance'
  )
}

watch(
  [apiBaseUrl, () => sgLoading.value, () => route.query?.variant, governanceContext],
  async ([url]) => {
    if (!url || sgLoading.value) return
    await loadStudents(url)
  },
  { immediate: true }
)

async function loadStudents(url) {
  isLoading.value = true
  loadError.value = ''
  try {
    if (props.preview) {
      students.value = Array.isArray(previewBundle.value?.students)
        ? previewBundle.value.students.map((student) => ({ ...student }))
        : []
      return
    }

    const token = localStorage.getItem('aura_token') || ''
    students.value = await getGovernanceStudents(url, token, governanceQueryParams())
  } catch (e) {
    loadError.value = e?.message || 'Unable to load students.'
  } finally {
    isLoading.value = false
  }
}

async function reload() {
  if (apiBaseUrl.value) await loadStudents(apiBaseUrl.value)
}

async function openStudentDetail(student) {
  selectedStudent.value = student
  selectedStudentReport.value = null
  detailError.value = ''
  await loadSelectedStudentAttendance()
}

function closeStudentDetail() {
  detailRequestId += 1
  selectedStudent.value = null
  selectedStudentReport.value = null
  detailLoading.value = false
  detailError.value = ''
}

async function loadSelectedStudentAttendance() {
  const student = selectedStudent.value
  if (!student) return

  const requestId = detailRequestId + 1
  detailRequestId = requestId
  detailLoading.value = true
  detailError.value = ''

  try {
    if (props.preview) {
      selectedStudentReport.value = buildPreviewStudentReport(student)
      return
    }

    const profileId = Number(studentProfile(student)?.id)
    if (!Number.isFinite(profileId) || profileId <= 0) {
      throw new Error('Student profile is unavailable.')
    }

    const token = localStorage.getItem('aura_token') || ''
    const report = await getStudentAttendanceReport(
      apiBaseUrl.value,
      token,
      profileId,
      governanceQueryParams()
    )

    if (detailRequestId === requestId) {
      selectedStudentReport.value = report
    }
  } catch (e) {
    if (detailRequestId === requestId) {
      detailError.value = e?.message || 'Unable to load attendance.'
    }
  } finally {
    if (detailRequestId === requestId) {
      detailLoading.value = false
    }
  }
}

function buildPreviewStudentReport(student) {
  const profile = studentProfile(student)
  const profileId = Number(profile?.id)
  const studentCode = String(profile?.student_id || '').trim()
  const eventMap = new Map(
    (Array.isArray(previewBundle.value?.events) ? previewBundle.value.events : [])
      .map((event) => [Number(event.id), event])
  )
  const rows = Object.values(previewBundle.value?.eventAttendanceRecords || {}).flat()
  const records = rows
    .filter((row) => {
      const attendance = row?.attendance || row
      const rowStudentCode = String(row?.student_id || '').trim()
      const rowProfileId = Number(attendance?.student_id)
      return (
        (studentCode && rowStudentCode === studentCode) ||
        (Number.isFinite(profileId) && rowProfileId === profileId)
      )
    })
    .map((row) => {
      const attendance = row?.attendance || row
      const event = eventMap.get(Number(attendance?.event_id))
      return {
        ...attendance,
        event_id: Number(attendance?.event_id || event?.id || 0),
        event_name: event?.name || attendance?.event_name || 'Event',
        event_location: event?.location || attendance?.event_location || null,
        event_date: event?.start_datetime || attendance?.event_date || attendance?.time_in || null,
        display_status: attendance?.display_status || attendance?.status || 'present',
      }
    })
    .sort((a, b) => dateTimeValue(b.event_date || b.time_in) - dateTimeValue(a.event_date || a.time_in))

  const counts = records.reduce((acc, record) => {
    const key = statusKey(record.display_status || record.status)
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})
  const attended = Number(counts.present || 0) + Number(counts.late || 0)
  const total = records.length

  return {
    student: {
      student_id: profile?.student_id || null,
      student_name: studentName(student),
      total_events: total,
      attended_events: attended,
      late_events: Number(counts.late || 0),
      incomplete_events: Number(counts.incomplete || 0),
      absent_events: Number(counts.absent || 0),
      excused_events: Number(counts.excused || 0),
      attendance_rate: total ? Math.round((attended / total) * 100) : 0,
      last_attendance: records[0]?.time_in || null,
    },
    attendance_records: records,
    monthly_stats: {},
    event_type_stats: {},
  }
}

function statusKey(value) {
  return String(value || 'incomplete')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'incomplete'
}

function statusLabel(value) {
  return statusKey(value)
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatPercent(value) {
  const numberValue = Number(value)
  return `${Number.isFinite(numberValue) ? Math.round(numberValue) : 0}%`
}

function safeDate(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function dateTimeValue(value) {
  return safeDate(value)?.getTime() || 0
}

function formatMonth(value) {
  const date = safeDate(value)
  if (!date) return '--'
  return new Intl.DateTimeFormat(undefined, { month: 'short' }).format(date)
}

function formatDay(value) {
  const date = safeDate(value)
  if (!date) return '--'
  return new Intl.DateTimeFormat(undefined, { day: '2-digit' }).format(date)
}

function formatTime(value) {
  const date = safeDate(value)
  if (!date) return ''
  return new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

function formatTimeRange(record) {
  const timeIn = formatTime(record?.time_in)
  const timeOut = formatTime(record?.time_out)
  if (timeIn && timeOut) return `${timeIn} - ${timeOut}`
  if (timeIn) return `In ${timeIn}`
  return 'No scan'
}

function recordKey(record) {
  return record?.id || `${record?.event_id || 'event'}-${record?.time_in || record?.event_date || 'record'}`
}
</script>

<style scoped>
@import '@/assets/css/sg-sub-views.css';

.sg-students-page {
  gap: 14px;
}

.sg-student-directory {
  background: var(--color-surface);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
}

.sg-student-directory-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 800;
}

.sg-student-directory-header strong {
  display: inline-flex;
  min-width: 28px;
  justify-content: center;
  padding: 3px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
  font-size: 12px;
}

.sg-students-list {
  display: flex;
  flex-direction: column;
}

.sg-student-row {
  width: 100%;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 0;
  border-bottom: 1px solid rgba(15, 23, 42, 0.07);
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.18s ease, transform 0.18s ease;
}

.sg-student-row:last-child {
  border-bottom: 0;
}

.sg-student-row:hover {
  background: rgba(15, 23, 42, 0.035);
}

.sg-student-row:active {
  transform: scale(0.99);
}

.sg-student-row:focus-visible,
.sg-detail-close:focus-visible,
.sg-detail-retry:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.sg-student-avatar,
.sg-detail-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border-radius: 8px;
  background: color-mix(in srgb, var(--color-primary) 16%, var(--color-surface));
  color: var(--color-primary);
  font-weight: 900;
}

.sg-student-avatar {
  width: 42px;
  height: 42px;
  font-size: 13px;
}

.sg-student-info {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.sg-student-name {
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sg-student-id-line {
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sg-student-meta-line {
  display: flex;
  min-width: 0;
  flex-wrap: wrap;
  gap: 5px;
}

.sg-student-meta-pill,
.sg-detail-meta span {
  max-width: 100%;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.055);
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 700;
  line-height: 1.2;
}

.sg-student-meta-pill {
  padding: 4px 7px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sg-student-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  color: var(--color-text-muted);
  background: rgba(15, 23, 42, 0.045);
}

.sg-student-detail-sheet {
  max-height: 88vh;
  border-radius: 16px 16px 0 0;
}

.sg-detail-scroll {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
}

.sg-detail-header {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
}

.sg-detail-avatar {
  width: 48px;
  height: 48px;
  font-size: 15px;
}

.sg-detail-heading {
  min-width: 0;
}

.sg-detail-heading h2 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 18px;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sg-detail-heading p {
  margin: 3px 0 0;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 800;
}

.sg-detail-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.055);
  color: var(--color-text-primary);
  cursor: pointer;
}

.sg-detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.sg-detail-meta span {
  padding: 5px 9px;
}

.sg-detail-state,
.sg-detail-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 160px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.045);
  color: var(--color-text-muted);
  text-align: center;
  font-size: 13px;
  font-weight: 700;
}

.sg-detail-state--error {
  background: rgba(239, 68, 68, 0.08);
  color: #b42318;
}

.sg-detail-retry {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  border-radius: 8px;
  padding: 9px 12px;
  background: var(--color-nav);
  color: var(--color-nav-text);
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

.sg-detail-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.sg-detail-stat {
  min-width: 0;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 8px;
  padding: 12px 8px;
  background: rgba(15, 23, 42, 0.025);
  text-align: center;
}

.sg-detail-stat strong {
  display: block;
  color: var(--color-text-primary);
  font-size: 18px;
  font-weight: 900;
  line-height: 1.1;
}

.sg-detail-stat span {
  display: block;
  margin-top: 5px;
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 800;
}

.sg-records-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 900;
}

.sg-records-header strong {
  color: var(--color-primary);
}

.sg-attendance-records {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sg-attendance-record {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 8px;
  background: var(--color-surface);
}

.sg-record-date {
  display: inline-flex;
  width: 46px;
  height: 50px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
  text-decoration: none;
}

.sg-record-date span {
  font-size: 10px;
  font-weight: 900;
  line-height: 1;
  text-transform: uppercase;
}

.sg-record-date strong {
  margin-top: 4px;
  font-size: 17px;
  font-weight: 900;
  line-height: 1;
}

.sg-record-main {
  min-width: 0;
}

.sg-record-main h3 {
  margin: 0 0 5px;
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sg-record-main p {
  display: flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  margin: 2px 0 0;
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 700;
}

.sg-record-main p span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sg-status-badge {
  justify-self: end;
  border-radius: 999px;
  padding: 5px 9px;
  background: rgba(100, 116, 139, 0.12);
  color: #475569;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  white-space: nowrap;
}

.sg-status-badge--present {
  background: rgba(22, 163, 74, 0.12);
  color: #15803d;
}

.sg-status-badge--late {
  background: rgba(217, 119, 6, 0.14);
  color: #a16207;
}

.sg-status-badge--absent {
  background: rgba(220, 38, 38, 0.12);
  color: #b91c1c;
}

.sg-status-badge--excused {
  background: rgba(37, 99, 235, 0.12);
  color: #1d4ed8;
}

.sg-status-badge--incomplete {
  background: rgba(100, 116, 139, 0.14);
  color: #475569;
}

@media (max-width: 420px) {
  .sg-student-row {
    grid-template-columns: auto minmax(0, 1fr) 30px;
    padding: 13px 12px;
  }

  .sg-detail-scroll {
    padding: 16px;
  }

  .sg-detail-stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sg-attendance-record {
    grid-template-columns: 42px minmax(0, 1fr);
  }

  .sg-record-date {
    width: 42px;
  }

  .sg-status-badge {
    grid-column: 2;
    justify-self: start;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sg-student-row,
  .sg-sub-action,
  .sg-sheet-enter-active,
  .sg-sheet-leave-active {
    transition: none;
  }
}
</style>
