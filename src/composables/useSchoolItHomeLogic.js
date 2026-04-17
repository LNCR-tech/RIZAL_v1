import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
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
import { resolveBackendMediaCandidates, withMediaCacheKey } from '@/services/backendMedia.js'
import { createSearchFieldAttrs } from '@/services/searchFieldAttrs.js'
import { filterWorkspaceEntitiesBySchool } from '@/services/workspaceScope.js'

export function useSchoolItHomeLogic(props) {
  const router = useRouter()
  const searchQuery = ref('')
  const schoolSearchInputAttrs = createSearchFieldAttrs('school-it-home-search')
  const isAiOpen = ref(false)
  const aiInputEl = ref(null)
  const remoteAttendanceSummary = ref(null)
  const heroLogoUnavailable = ref(false)
  const heroLogoCandidateIndex = ref(0)
  const heroLogoRetryKey = ref(0)

  const {
    currentUser,
    schoolSettings,
    apiBaseUrl,
    events,
    token,
    initializeDashboardSession,
    refreshSchoolSettings
  } = useDashboardSession()
  const { state: previewState } = useSchoolItPreviewStore()
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
  const heroLogoSrc = computed(() => (
    heroLogoUnavailable.value
      ? null
      : withMediaCacheKey(
        heroLogoCandidates.value[heroLogoCandidateIndex.value] || null,
        heroLogoRetryKey.value || ''
      )
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
  const accountsRouteName = computed(() => props.preview ? 'PreviewSchoolItAccounts' : 'SchoolItAccounts')

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

  watch(() => heroLogoCandidates.value.join('|'), () => {
    heroLogoUnavailable.value = false
    heroLogoCandidateIndex.value = 0
    heroLogoRetryKey.value = 0
  })

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

  function handleHeroLogoError() {
    if (heroLogoCandidateIndex.value < heroLogoCandidates.value.length - 1) {
      heroLogoCandidateIndex.value += 1
      return
    }

    if (!heroLogoRetryKey.value) {
      heroLogoRetryKey.value = Date.now()
      return
    }

    heroLogoUnavailable.value = true
  }

  function openSearchResult(result) {
    searchQuery.value = ''
    router.push({ name: result.routeName })
  }

  function toggleAiPanel() {
    isAiOpen.value = !isAiOpen.value
  }

  async function handleLogout() {
    await logout()
  }

  return {
    router,
    searchQuery,
    schoolSearchInputAttrs,
    isAiOpen,
    aiInputEl,
    scrollEl,
    searchActive,
    schoolName,
    avatarUrl,
    heroLogoSrc,
    heroLogoUnavailable,
    displayName,
    initials,
    schoolInitials,
    settingsRouteName,
    accountsRouteName,
    departmentCountLabel,
    programCountLabel,
    attendanceRateMeta,
    presentRateLabel,
    absentRateLabel,
    searchResults,
    inputText,
    isTyping,
    messages,
    sendMessage,
    secondaryAuraLogo,
    handleHeroLogoError,
    openSearchResult,
    toggleAiPanel,
    handleLogout
  }
}
