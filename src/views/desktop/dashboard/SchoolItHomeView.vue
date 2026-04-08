<template>
  <section class="school-it-home">
    <div class="school-it-home__shell">
      <StandardHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="schoolName"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />
      <div class="school-it-home__breadcrumbs">
        <Breadcrumbs />
      </div>

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
                      <div
                        v-for="message in messages"
                        :key="message.id"
                        :class="[
                          'school-it-home__bubble',
                          message.sender === 'ai'
                            ? 'school-it-home__bubble--ai'
                            : 'school-it-home__bubble--user',
                        ]"
                      >
                        {{ message.text }}
                      </div>

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
            <div class="school-it-home__summary-content">
              <div class="school-it-home__summary-header">
                <span class="school-it-home__summary-mini">University Structure</span>
                <h3 class="school-it-home__summary-title">Departments</h3>
              </div>
              
              <div class="school-it-home__summary-stats">
                <div class="school-it-home__summary-stat">
                  <strong class="school-it-home__summary-value">{{ departmentCountLabel }}</strong>
                  <span class="school-it-home__summary-caption">Active Depts</span>
                </div>
                <div class="school-it-home__summary-divider" />
                <div class="school-it-home__summary-stat">
                  <strong class="school-it-home__summary-value school-it-home__summary-value--small">{{ programCountLabel }}</strong>
                  <span class="school-it-home__summary-caption">Programs</span>
                </div>
              </div>

              <button class="school-it-home__ghost-pill" type="button" @click="router.push({ name: settingsRouteName })">
                <span>Access Structure</span>
                <ArrowRight :size="14" />
              </button>
            </div>
          </section>

          <section class="school-it-home__rate dashboard-enter dashboard-enter--6">
            <div class="school-it-home__rate-content">
              <div class="school-it-home__rate-info">
                <span class="school-it-home__summary-mini">Today's Performance</span>
                <h3 class="school-it-home__rate-minimal-title">Attendance Rate</h3>
                <p class="school-it-home__rate-minimal-meta">{{ attendanceRateMeta }}</p>
              </div>

              <div class="school-it-home__rate-visual">
                <SchoolItMetricRing :value="presentRateLabel" compact :delay="0.08" />
                <span class="school-it-home__rate-visual-label">Present</span>
              </div>
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
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Search, Send } from 'lucide-vue-next'
import StandardHeader from '@/components/desktop/dashboard/StandardHeader.vue'
import Breadcrumbs from '@/components/desktop/dashboard/Breadcrumbs.vue'
import SchoolItMetricRing from '@/components/desktop/dashboard/SchoolItMetricRing.vue'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'
import { secondaryAuraLogo } from '@/config/theme.js'
import { useChat } from '@/composables/useChat.js'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { useSchoolItWorkspaceData } from '@/composables/useSchoolItWorkspaceData.js'
import { useStoredAuthMeta } from '@/composables/useStoredAuthMeta.js'
import { getAttendanceSummary } from '@/services/backendApi.js'
import { useSchoolItPreviewStore } from '@/composables/useSchoolItPreviewStore.js'
import { hasPrivilegedPendingFace } from '@/services/localAuth.js'
import { resolveBackendMediaCandidates, resolveLoadableMediaUrl } from '@/services/backendMedia.js'
import { createSearchFieldAttrs } from '@/services/searchFieldAttrs.js'
import { filterWorkspaceEntitiesBySchool } from '@/services/workspaceScope.js'

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
const activeUser = computed(() => props.preview ? previewState.user : currentUser.value)
const activeSchoolSettings = computed(() => props.preview ? previewState.schoolSettings : schoolSettings.value)
const activeEvents = computed(() => props.preview ? previewState.events : events.value)

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
    ? [previewState.schoolSettings?.logo_url]
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
  await initializeSchoolItWorkspaceData()
  await loadSchoolItHomeData(resolvedApiBaseUrl)
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
  if (!token || hasPrivilegedPendingFace()) {
    remoteAttendanceSummary.value = null
    return
  }

  const [attendanceSummaryResult] = await Promise.allSettled([
    getAttendanceSummary(resolvedApiBaseUrl, token),
  ])

  remoteAttendanceSummary.value = attendanceSummaryResult.status === 'fulfilled' ? attendanceSummaryResult.value : null
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
  isAiOpen.value = !isAiOpen.value
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
.school-it-home__search-input{flex:1;min-width:0;border:none;background:transparent;outline:none;color:var(--color-text-primary);font-size:clamp(13px,3.8vw,14px);font-weight:500}
.school-it-home__search-input::placeholder{color:var(--color-text-muted)}
.school-it-home__search-icon{width:clamp(30px,8vw,32px);height:clamp(30px,8vw,32px);padding:0;border:1px solid var(--color-surface-border);border-radius:999px;background:transparent;color:var(--color-primary);display:inline-flex;align-items:center;justify-content:center;align-self:center;line-height:0;appearance:none;flex-shrink:0;place-self:center}
.school-it-home__search-icon :deep(svg){display:block;width:clamp(15px,4.5vw,18px);height:clamp(15px,4.5vw,18px);transform:translateY(0)}
.school-it-home__search-results{overflow:hidden;min-height:0}
.school-it-home__search-results-inner{display:flex;flex-direction:column;gap:10px;padding:14px 0 6px}
.school-it-home__search-result{width:100%;padding:14px 16px;border:none;border-radius:22px;background:color-mix(in srgb,var(--color-surface) 90%,var(--color-bg));display:flex;flex-direction:column;gap:8px;text-align:left}
.school-it-home__search-result-top{display:flex;align-items:center;justify-content:space-between;gap:12px}
.school-it-home__search-result-name{font-size:14px;font-weight:700;color:var(--color-text-primary)}
.school-it-home__search-result-type{min-height:28px;padding:0 12px;border-radius:999px;background:var(--color-primary);color:var(--color-banner-text);display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;letter-spacing:.02em;flex-shrink:0}
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
.school-it-home__bubble--ai{align-self:flex-start;background:var(--color-surface);color:var(--color-surface-text);border:1px solid var(--aura-glass-border);box-shadow:var(--aura-shadow-soft)}
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
.school-it-home__pill{width:fit-content;min-height:58px;margin-top:auto;margin-bottom:24px;padding:0 22px 0 8px;border:none;border-radius:999px;background:var(--color-surface);color:var(--color-surface-text);display:inline-flex;align-items:center;gap:14px;font-size:13px;font-weight:700}
.school-it-home__pill--compact{min-height:56px;margin-bottom:0}
.school-it-home__pill-icon{width:42px;height:42px;border-radius:999px;background:var(--color-nav);color:var(--color-nav-text);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
.school-it-home__summary{background:var(--color-surface);display:flex;flex-direction:column;border:1px solid var(--aura-glass-border);box-shadow:var(--aura-shadow-soft), var(--aura-glow-primary)}
.school-it-home__summary-content{padding:26px;display:flex;flex-direction:column;gap:22px;flex:1}
.school-it-home__summary-mini{font-size:10px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--color-text-muted);display:block;margin-bottom:6px}
.school-it-home__summary-title{margin:0;font-size:28px;font-weight:800;letter-spacing:-.04em;color:var(--color-text-primary)}
.school-it-home__summary-stats{display:flex;align-items:center;gap:20px}
.school-it-home__summary-stat{display:flex;flex-direction:column;gap:2px}
.school-it-home__summary-value{font-size:42px;line-height:1;font-weight:800;letter-spacing:-.06em;color:var(--color-primary)}
.school-it-home__summary-value--small{color:var(--color-text-primary);opacity:.85}
.school-it-home__summary-caption{font-size:12px;font-weight:600;color:var(--color-text-muted)}
.school-it-home__summary-divider{width:1px;height:30px;background:var(--color-surface-border);opacity:.5}
.school-it-home__ghost-pill{margin-top:auto;display:inline-flex;align-items:center;gap:8px;padding:10px 14px;background:var(--color-field-surface);border:none;border-radius:999px;font-size:12px;font-weight:700;color:var(--color-text-primary);width:fit-content;cursor:pointer;transition:all .2s ease}
.school-it-home__ghost-pill:hover{background:var(--color-surface-border)}

.school-it-home__rate{background:var(--color-surface);display:flex;flex-direction:column;border:1px solid var(--aura-glass-border);box-shadow:var(--aura-shadow-soft), var(--aura-glow-primary)}
.school-it-home__rate-content{padding:26px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex:1}
.school-it-home__rate-info{display:flex;flex-direction:column;min-width:0}
.school-it-home__rate-minimal-title{margin:0;font-size:24px;font-weight:800;letter-spacing:-.04em;color:var(--color-text-primary)}
.school-it-home__rate-minimal-meta{margin:8px 0 0;font-size:13px;line-height:1.5;color:var(--color-text-secondary);max-width:20ch}
.school-it-home__rate-visual{display:flex;flex-direction:column;align-items:center;gap:6px;flex-shrink:0}
.school-it-home__rate-visual-label{font-size:11px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--color-text-muted)}

.school-it-home__status{background:var(--color-surface);padding:12px}
.school-it-home__status-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.school-it-home__status-panel{min-height:222px;border-radius:24px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:16px 10px 14px;border:1px solid var(--aura-glass-border);box-shadow:var(--aura-shadow-soft)}
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
.school-it-home__breadcrumbs {
  margin: 12px 0;
  padding: 0 4px;
}
</style>
