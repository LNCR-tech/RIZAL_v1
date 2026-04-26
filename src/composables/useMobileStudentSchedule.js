import { computed, onBeforeUnmount, onMounted, ref, unref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { studentDashboardPreviewData } from '@/data/studentDashboardPreview.js'
import {
  getEventTimeStatus,
  resolveApiBaseUrl,
} from '@/services/backendApi.js'
import {
  getLatestAttendanceRecordsByEvent,
  hasSignedInAttendance,
  hasSignedOutAttendance,
  parseEventDateTime,
  resolveAttendanceActionState,
  resolveAttendanceDisplayStatus,
  resolveEventLifecycleStatus,
} from '@/services/attendanceFlow.js'
import { primeLocationAccess } from '@/services/devicePermissions.js'
import {
  resolveAttendanceLocation,
  resolveEventDetailLocation,
} from '@/services/routeWorkspace.js'

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'ongoing', label: 'Ongoing' },
  { id: 'upcoming', label: 'Upcoming' },
  { id: 'completed', label: 'Done' },
]

const STATUS_RANK = {
  ongoing: 0,
  upcoming: 1,
  completed: 2,
  cancelled: 3,
}

const LIFECYCLE_LABELS = {
  ongoing: 'Ongoing',
  upcoming: 'Upcoming',
  completed: 'Done',
  cancelled: 'Cancelled',
}

const weekdayFormatter = new Intl.DateTimeFormat('en-PH', { weekday: 'short' })
const timeFormatter = new Intl.DateTimeFormat('en-PH', {
  hour: 'numeric',
  minute: '2-digit',
})
const attendanceDateTimeFormatter = new Intl.DateTimeFormat('en-PH', {
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
})

function startOfDay(date) {
  const next = new Date(date)
  next.setHours(0, 0, 0, 0)
  return next
}

function startOfWeek(date) {
  const next = startOfDay(date)
  next.setDate(next.getDate() - next.getDay())
  return next
}

function addDays(date, amount) {
  const next = new Date(date)
  next.setDate(next.getDate() + amount)
  return next
}

function toDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function fromDateKey(value) {
  const [year, month, day] = String(value || '').split('-').map((part) => Number(part))
  if (!Number.isFinite(year) || !Number.isFinite(month) || !Number.isFinite(day)) {
    return startOfDay(new Date())
  }

  return new Date(year, month - 1, day)
}

function parseValidEventDate(value) {
  const parsed = parseEventDateTime(value)
  return Number.isFinite(parsed.getTime()) ? parsed : null
}

function formatTimeRange(event) {
  const start = parseValidEventDate(event?.start_datetime)
  if (!start) return 'Time unavailable'

  const end = parseValidEventDate(event?.end_datetime) || start
  return `${timeFormatter.format(start)} - ${timeFormatter.format(end)}`
}

function formatAttendanceDateTime(value) {
  const parsed = parseValidEventDate(value)
  return parsed ? attendanceDateTimeFormatter.format(parsed) : '--, --'
}

function normalizeStatus(value) {
  return value === 'done' ? 'completed' : String(value || '').toLowerCase()
}

function resolveLifecycleLabel(status) {
  return LIFECYCLE_LABELS[status] || 'Upcoming'
}

function resolveAttendancePill(attendanceRecord) {
  if (!attendanceRecord) {
    return { label: 'No record yet', tone: 'muted' }
  }

  if (hasSignedInAttendance(attendanceRecord) && !hasSignedOutAttendance(attendanceRecord)) {
    return { label: 'Checked in', tone: 'neutral' }
  }

  const displayStatus = resolveAttendanceDisplayStatus(attendanceRecord)

  if (displayStatus === 'present') {
    return { label: 'Present', tone: 'present' }
  }

  if (displayStatus === 'late') {
    return { label: 'Late', tone: 'late' }
  }

  if (displayStatus === 'absent') {
    return { label: 'Absent', tone: 'absent' }
  }

  if (displayStatus === 'excused') {
    return { label: 'Excused', tone: 'neutral' }
  }

  if (displayStatus === 'incomplete') {
    return { label: 'Checked in', tone: 'neutral' }
  }

  return { label: 'No record yet', tone: 'muted' }
}

function resolvePrimaryAction(actionState) {
  if (actionState === 'sign-in') {
    return { label: 'Check in now', disabled: false }
  }

  if (actionState === 'sign-out') {
    return { label: 'Check out now', disabled: false }
  }

  if (actionState === 'not-open') {
    return { label: 'Check in now', disabled: true }
  }

  if (actionState === 'waiting-sign-out') {
    return { label: 'Waiting for check out', disabled: true }
  }

  if (actionState === 'done') {
    return { label: 'Attendance done', disabled: true }
  }

  if (actionState === 'missed-check-in') {
    return { label: 'Check in missed', disabled: true }
  }

  return { label: 'Closed', disabled: true }
}

function compareRows(left, right) {
  const leftRank = STATUS_RANK[left.lifecycleStatus] ?? 99
  const rightRank = STATUS_RANK[right.lifecycleStatus] ?? 99
  if (leftRank !== rightRank) return leftRank - rightRank

  const leftStart = parseValidEventDate(left.event?.start_datetime)?.getTime() ?? 0
  const rightStart = parseValidEventDate(right.event?.start_datetime)?.getTime() ?? 0
  const leftEnd = parseValidEventDate(left.event?.end_datetime)?.getTime() ?? leftStart
  const rightEnd = parseValidEventDate(right.event?.end_datetime)?.getTime() ?? rightStart
  const now = Date.now()

  if (left.lifecycleStatus === 'ongoing' && right.lifecycleStatus === 'ongoing') {
    const leftDistance = Math.abs(leftStart - now)
    const rightDistance = Math.abs(rightStart - now)
    if (leftDistance !== rightDistance) return leftDistance - rightDistance
    return leftEnd - rightEnd
  }

  if (left.lifecycleStatus === 'upcoming' && right.lifecycleStatus === 'upcoming') {
    return leftStart - rightStart
  }

  if (left.lifecycleStatus === 'completed' && right.lifecycleStatus === 'completed') {
    return rightEnd - leftEnd
  }

  if (left.lifecycleStatus === 'cancelled' && right.lifecycleStatus === 'cancelled') {
    return rightStart - leftStart
  }

  return leftStart - rightStart
}

function eventOccursOnDate(event, dateKey) {
  const start = parseValidEventDate(event?.start_datetime)
  if (!start) return false

  const end = parseValidEventDate(event?.end_datetime) || start
  const targetDate = startOfDay(fromDateKey(dateKey)).getTime()
  const startDate = startOfDay(start).getTime()
  const endDate = startOfDay(end).getTime()

  return targetDate >= startDate && targetDate <= endDate
}

function buildWeekDays(weekStartDate, todayKey) {
  return Array.from({ length: 7 }, (_, index) => {
    const date = addDays(weekStartDate, index)
    const key = toDateKey(date)
    return {
      key,
      label: weekdayFormatter.format(date),
      dayNumber: String(date.getDate()),
      isToday: key === todayKey,
    }
  })
}

function resolvePreviewSourceFlag(source) {
  return Boolean(unref(typeof source === 'function' ? source() : source))
}

export function useMobileStudentSchedule(previewSource = false) {
  const preview = computed(() => resolvePreviewSourceFlag(previewSource))
  const route = useRoute()
  const router = useRouter()
  const apiBaseUrl = resolveApiBaseUrl()
  const today = startOfDay(new Date())
  const todayKey = ref(toDateKey(today))
  const activeFilter = ref('all')
  const selectedDateKey = ref(todayKey.value)
  const expandedEventId = ref(null)
  const eventTimeStatuses = ref({})
  const requestId = ref(0)
  const {
    currentUser,
    events,
    attendanceRecords,
    hasOpenAttendanceForEvent,
    refreshAttendanceRecords,
    unreadAnnouncements,
  } = useDashboardSession()
  const activeUser = computed(() => (
    preview.value ? studentDashboardPreviewData.user : currentUser.value
  ))
  const activeEvents = computed(() => (
    preview.value ? studentDashboardPreviewData.events : events.value
  ))
  const activeAttendanceRecords = computed(() => (
    preview.value ? studentDashboardPreviewData.attendanceRecords : attendanceRecords.value
  ))
  const activeUnreadAnnouncements = computed(() => (
    preview.value ? 0 : unreadAnnouncements.value
  ))
  const activeSchoolSettings = computed(() => (
    preview.value ? studentDashboardPreviewData.schoolSettings : null
  ))
  let eventTimeStatusIntervalId = null

  usePreviewTheme(preview, activeSchoolSettings)

  const displayName = computed(() => {
    const user = activeUser.value
    if (!user) return 'User Full Name'

    const fullName = [user.first_name, user.middle_name, user.last_name]
      .filter(Boolean)
      .join(' ')
      .trim()

    return fullName || user.email?.split('@')[0] || 'User Full Name'
  })

  const initials = computed(() => {
    const parts = displayName.value.split(' ').filter(Boolean)
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
    }

    return displayName.value.slice(0, 2).toUpperCase()
  })

  const avatarUrl = computed(() => (
    activeUser.value?.student_profile?.photo_url
    || activeUser.value?.student_profile?.avatar_url
    || activeUser.value?.avatar_url
    || ''
  ))

  const schoolEvents = computed(() => {
    const schoolId = Number(activeUser.value?.school_id)
    return activeEvents.value.filter((event) => (
      !Number.isFinite(schoolId) || Number(event?.school_id) === schoolId
    ))
  })

  const attendanceByEventId = computed(() => {
    const map = new Map()

    getLatestAttendanceRecordsByEvent(activeAttendanceRecords.value).forEach((record) => {
      const eventId = Number(record?.event_id)
      if (!Number.isFinite(eventId)) return
      map.set(eventId, record)
    })

    return map
  })

  const weekPages = computed(() => {
    const candidates = [today]

    schoolEvents.value.forEach((event) => {
      const start = parseValidEventDate(event?.start_datetime)
      const end = parseValidEventDate(event?.end_datetime)
      if (start) candidates.push(start)
      if (end) candidates.push(end)
    })

    const timestamps = candidates
      .map((date) => startOfDay(date).getTime())
      .filter((value) => Number.isFinite(value))

    const minTime = Math.min(...timestamps)
    const maxTime = Math.max(...timestamps)
    const firstWeekStart = startOfWeek(new Date(minTime))
    const lastWeekStart = startOfWeek(new Date(maxTime))
    const pages = []
    let cursor = new Date(firstWeekStart)

    while (cursor.getTime() <= lastWeekStart.getTime()) {
      pages.push({
        key: toDateKey(cursor),
        days: buildWeekDays(cursor, todayKey.value),
      })
      cursor = addDays(cursor, 7)
    }

    return pages.length
      ? pages
      : [{ key: todayKey.value, days: buildWeekDays(startOfWeek(today), todayKey.value) }]
  })

  const todayWeekIndex = computed(() => {
    const index = weekPages.value.findIndex((page) => (
      page.days.some((day) => day.key === todayKey.value)
    ))

    return index >= 0 ? index : 0
  })

  const timeStatusCandidateIds = computed(() => {
    if (preview.value) return []

    const ids = new Set()
    schoolEvents.value.forEach((event) => {
      const eventId = Number(event?.id)
      if (!Number.isFinite(eventId)) return

      const status = normalizeStatus(event?.status)
      if (status === 'ongoing' || status === 'upcoming' || hasOpenAttendanceForEvent(eventId)) {
        ids.add(eventId)
      }
    })

    return [...ids].sort((left, right) => left - right)
  })

  const selectedDateEvents = computed(() => (
    schoolEvents.value.filter((event) => eventOccursOnDate(event, selectedDateKey.value))
  ))

  const eventRows = computed(() => {
    return selectedDateEvents.value
      .map((event) => {
        const eventId = Number(event?.id)
        const attendanceRecord = attendanceByEventId.value.get(eventId) ?? null
        const timeStatus = Number.isFinite(eventId) ? eventTimeStatuses.value[eventId] ?? null : null
        const lifecycleStatus = resolveEventLifecycleStatus(event, timeStatus) || 'upcoming'
        const lifecycleLabel = resolveLifecycleLabel(lifecycleStatus)
        const attendancePill = resolveAttendancePill(attendanceRecord)
        const actionState = resolveAttendanceActionState({
          event,
          eventStatus: lifecycleStatus,
          attendanceRecord,
          timeStatus,
          now: new Date(),
        })
        const primaryAction = resolvePrimaryAction(actionState)

        return {
          event,
          eventId,
          lifecycleStatus,
          lifecycleLabel,
          attendanceRecord,
          attendancePill,
          actionState,
          primaryAction,
          timeRangeLabel: formatTimeRange(event),
          checkedInLabel: formatAttendanceDateTime(attendanceRecord?.time_in),
          checkedOutLabel: formatAttendanceDateTime(attendanceRecord?.time_out),
          scopeLabel: String(event?.scope_label || '').trim(),
        }
      })
      .sort(compareRows)
  })

  const visibleRows = computed(() => {
    if (activeFilter.value === 'all') return eventRows.value
    return eventRows.value.filter((row) => row.lifecycleStatus === activeFilter.value)
  })

  async function syncEventTimeStatuses(eventIds) {
    const nextRequestId = requestId.value + 1
    requestId.value = nextRequestId
    const previousStatuses = eventTimeStatuses.value

    if (preview.value || !eventIds.length) {
      eventTimeStatuses.value = {}
      return
    }

    const token = localStorage.getItem('aura_token')
    if (!token) {
      eventTimeStatuses.value = {}
      return
    }

    const nextStatuses = {}

    await Promise.all(eventIds.map(async (eventId) => {
      try {
        nextStatuses[eventId] = await getEventTimeStatus(apiBaseUrl, token, eventId)
      } catch {
        nextStatuses[eventId] = null
      }
    }))

    if (requestId.value !== nextRequestId) return
    eventTimeStatuses.value = nextStatuses

    const closedTransitionIds = eventIds.filter((eventId) => (
      nextStatuses?.[eventId]?.event_status === 'closed'
      && previousStatuses?.[eventId]?.event_status !== 'closed'
    ))

    if (closedTransitionIds.length) {
      await Promise.allSettled(
        closedTransitionIds.map((eventId) => refreshAttendanceRecords({ event_id: eventId }))
      )
    }
  }

  function stopEventTimeStatusPolling() {
    if (eventTimeStatusIntervalId != null) {
      clearInterval(eventTimeStatusIntervalId)
      eventTimeStatusIntervalId = null
    }
  }

  function startEventTimeStatusPolling() {
    stopEventTimeStatusPolling()
    if (preview.value) return

    eventTimeStatusIntervalId = window.setInterval(() => {
      void syncEventTimeStatuses(timeStatusCandidateIds.value)
    }, 15000)
  }

  function toggleExpanded(eventId) {
    expandedEventId.value = expandedEventId.value === eventId ? null : eventId
  }

  function openEventDetail(event) {
    if (!event?.id) return
    router.push(resolveEventDetailLocation(route, event.id))
  }

  function openPrimaryAction(row) {
    if (!row?.event?.id || row.primaryAction.disabled) return

    if (!preview.value) {
      void primeLocationAccess()
    }

    router.push(resolveAttendanceLocation(route, row.event.id))
  }

  watch(
    weekPages,
    (pages) => {
      const hasSelectedDate = pages.some((page) => (
        page.days.some((day) => day.key === selectedDateKey.value)
      ))

      if (!hasSelectedDate) {
        selectedDateKey.value = todayKey.value
      }
    },
    { immediate: true }
  )

  watch(timeStatusCandidateIds, (eventIds) => {
    void syncEventTimeStatuses(eventIds)
  }, { immediate: true })

  watch(preview, (isPreview) => {
    if (isPreview) {
      stopEventTimeStatusPolling()
      eventTimeStatuses.value = {}
      return
    }

    startEventTimeStatusPolling()
  }, { immediate: true })

  watch([selectedDateKey, activeFilter], () => {
    expandedEventId.value = null
  })

  watch(visibleRows, (rows) => {
    if (!rows.some((row) => row.eventId === expandedEventId.value)) {
      expandedEventId.value = null
    }
  })

  onMounted(() => {
    if (preview.value) return
    refreshAttendanceRecords({ limit: 200 }).catch(() => null)
  })

  onBeforeUnmount(() => {
    stopEventTimeStatusPolling()
  })

  return {
    activeFilter,
    activeUnreadAnnouncements,
    avatarUrl,
    displayName,
    expandedEventId,
    filters: FILTERS,
    initials,
    openEventDetail,
    openPrimaryAction,
    selectedDateKey,
    todayWeekIndex,
    toggleExpanded,
    visibleRows,
    weekPages,
  }
}
