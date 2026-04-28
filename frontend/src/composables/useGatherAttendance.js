import { computed, nextTick, onBeforeUnmount, onMounted, ref, unref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { initFaceScanDetector, resetFaceScanDetector } from '@/composables/useFaceScanDetector.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { studentDashboardPreviewData } from '@/data/studentDashboardPreview.js'
import {
  buildAttendanceLocationErrorMessage,
  formatCompactDuration,
  getLatestAttendanceRecordsByEvent,
  getMillisecondsUntilSignOutOpen,
  isOpenAttendanceRecord,
  parseEventDateTime,
  resolveAttendanceActionState,
  resolveAttendanceDisplayStatus,
  resolveEventLifecycleStatus,
  resolveEventWindowStage,
} from '@/services/attendanceFlow.js'
import {
  formatCoordinateLocationLabel,
  formatVenueDistance,
  measureDistanceMeters,
  resolveLocationLabel,
} from '@/services/locationDisplay.js'
import {
  getCurrentPositionOrThrow,
  getCurrentPositionWithinAccuracyOrThrow,
  prepareLocationAccess,
  requestCameraPermission,
} from '@/services/devicePermissions.js'
import {
  getEventTimeStatus,
  resolveApiBaseUrl,
  verifyEventLocation,
} from '@/services/backendApi.js'
import { normalizeAttendanceRecord } from '@/services/backendNormalizers.js'
import {
  describePublicAttendanceError,
  submitPublicAttendanceScan,
} from '@/services/publicAttendance.js'
import {
  hasNavigableHistory,
  isGovernanceWorkspaceContext,
  resolveEventListLocation,
  resolveGatherWelcomeLocation,
} from '@/services/routeWorkspace.js'

const timeFormatter = new Intl.DateTimeFormat('en-PH', {
  hour: 'numeric',
  minute: '2-digit',
})
const dayFormatter = new Intl.DateTimeFormat('en-PH', {
  month: 'short',
  day: 'numeric',
})
const stampFormatter = new Intl.DateTimeFormat('en-PH', {
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
})
const faceScanTimeoutMs = Number(import.meta.env.VITE_FACE_SCAN_TIMEOUT_MS ?? 3000)
const faceScanGateEnabled = import.meta.env.VITE_FACE_SCAN_GATE !== 'false'

const ACTION_RANK = {
  'sign-out': 0,
  'sign-in': 1,
  'waiting-sign-out': 2,
  'not-open': 3,
  'missed-check-in': 4,
  closed: 5,
  done: 6,
}
const GATHER_SUCCESS_ACTIONS = new Set(['time_in', 'time_out', 'already_signed_in', 'already_signed_out'])

function resolvePreviewFlag(source) {
  return Boolean(unref(typeof source === 'function' ? source() : source))
}

function parseValidDate(value) {
  const parsed = parseEventDateTime(value)
  return Number.isFinite(parsed.getTime()) ? parsed : null
}

function normalizeAction(value) {
  return String(value || '').trim().toLowerCase().replace(/[\s-]+/g, '_')
}

function isSignOutAction(value) {
  return ['sign_out', 'signed_out', 'check_out', 'checkout', 'time_out', 'timeout', 'out'].includes(
    normalizeAction(value)
  )
}

function resolveEventGeo(event = null) {
  const latitude = Number(
    event?.geo_latitude
      ?? event?.geoLatitude
      ?? event?.latitude
      ?? event?.location_latitude
      ?? event?.locationLat
  )
  const longitude = Number(
    event?.geo_longitude
      ?? event?.geoLongitude
      ?? event?.longitude
      ?? event?.location_longitude
      ?? event?.locationLon
  )
  const radius = Number(
    event?.geo_radius_m
      ?? event?.geoRadiusM
      ?? event?.radius_m
      ?? event?.radiusM
      ?? event?.location_radius_m
  )

  return {
    latitude: Number.isFinite(latitude) ? latitude : null,
    longitude: Number.isFinite(longitude) ? longitude : null,
    radiusM: Number.isFinite(radius) ? radius : null,
  }
}

function pickLatestAttendanceRecord(records = [], eventId = null) {
  const normalizedEventId = Number(eventId)
  if (!Number.isFinite(normalizedEventId)) return null

  return records
    .filter((record) => Number(record?.event_id) === normalizedEventId)
    .sort((left, right) => {
      const leftTime = new Date(left?.time_in || left?.created_at || 0).getTime()
      const rightTime = new Date(right?.time_in || right?.created_at || 0).getTime()
      return rightTime - leftTime
    })[0] ?? null
}

function resolveActionKind(actionState, attendanceRecord) {
  if (
    actionState === 'sign-out'
    || actionState === 'waiting-sign-out'
    || (actionState === 'closed' && isOpenAttendanceRecord(attendanceRecord))
  ) {
    return 'sign-out'
  }

  return 'sign-in'
}

function resolveActionLabel(actionKind) {
  return actionKind === 'sign-out' ? 'Check Out' : 'Check In'
}

function resolveActionTone(actionState) {
  return actionState === 'sign-in' || actionState === 'sign-out' ? 'primary' : 'muted'
}

function resolveLiveStatusMessage({ cameraReady, faceDetected, actionLabel, selectedEvent }) {
  if (!selectedEvent) {
    return 'No attendance-ready events right now.'
  }

  if (!cameraReady) {
    return 'Allow camera access to open the live Gather viewfinder.'
  }

  if (!faceDetected) {
    return 'Center your face inside the frame.'
  }

  return `${actionLabel} is ready for ${selectedEvent.event.name}.`
}

function resolveGatherActionKind(event = null, timeStatus = null) {
  const stage = resolveEventWindowStage(event, timeStatus)
  if (['early_check_in', 'late_check_in', 'absent_check_in'].includes(stage)) {
    return 'sign-in'
  }
  if (stage === 'sign_out_open') {
    return 'sign-out'
  }
  return ''
}

function resolveGatherBlockedStateModel(actionLabel, event, timeStatus) {
  const stage = resolveEventWindowStage(event, timeStatus)

  if (stage === 'before_check_in') {
    return {
      tone: 'neutral',
      message: `${actionLabel} is not available yet.`,
    }
  }

  if (stage === 'sign_out_pending') {
    const remainingMs = getMillisecondsUntilSignOutOpen({ event, timeStatus })
    const countdown = Number.isFinite(remainingMs) && remainingMs > 0
      ? ` Sign-out opens in ${formatCompactDuration(remainingMs)}.`
      : ''

    return {
      tone: 'neutral',
      message: `Check out is not available yet.${countdown}`.trim(),
    }
  }

  if (stage === 'closed') {
    return {
      tone: 'error',
      message: 'Attendance is already closed for this event.',
    }
  }

  return {
    tone: 'neutral',
    message: `${actionLabel} is not available for this event right now.`,
  }
}

function summarizeGatherScanOutcomes(response = {}) {
  const outcomes = Array.isArray(response?.outcomes) ? response.outcomes : []
  const successfulOutcomes = outcomes.filter((outcome) =>
    GATHER_SUCCESS_ACTIONS.has(normalizeAction(outcome?.action))
  )
  const primaryOutcome = successfulOutcomes[0] || outcomes[0] || null

  return {
    outcomes,
    successfulOutcomes,
    primaryOutcome,
    detectedCount: outcomes.length,
    successfulCount: successfulOutcomes.length,
  }
}

function resolveLocationErrorMessage(source, fallback = 'Unable to verify your location.') {
  const publicAttendanceMessage = describePublicAttendanceError(source)
  if (publicAttendanceMessage && publicAttendanceMessage !== 'The public attendance kiosk request failed.') {
    return publicAttendanceMessage
  }

  const detail = source?.details ?? source?.detail ?? source
  const hasLocationDetail = detail && typeof detail === 'object' && (
    detail.reason != null
    || detail.distance_m != null
    || detail.radius_m != null
    || detail.accuracy_m != null
  )

  if (hasLocationDetail) {
    return buildAttendanceLocationErrorMessage(detail)
  }

  const message = String(source?.message || '').trim()
  return message || fallback
}

function formatTimestamp(value) {
  if (!value) return '--'
  const parsed = parseValidDate(value)
  return parsed ? stampFormatter.format(parsed) : '--'
}

function formatAttendanceOutcome(status) {
  const normalized = String(status || '').trim().toLowerCase()
  if (normalized === 'present') return 'Present'
  if (normalized === 'late') return 'Late'
  if (normalized === 'absent') return 'Absent'
  if (normalized === 'excused') return 'Excused'
  if (normalized === 'incomplete') return 'In progress'
  return 'Recorded'
}

function resolveEventTone(actionState) {
  if (actionState === 'sign-in' || actionState === 'sign-out') return 'ready'
  if (actionState === 'missed-check-in' || actionState === 'closed') return 'error'
  if (actionState === 'done') return 'done'
  if (actionState === 'waiting-sign-out' || actionState === 'not-open') return 'pending'
  return 'muted'
}

function resolveEventStatusLabel({ actionState, attendanceRecord, event, timeStatus }) {
  if (actionState === 'sign-in') return 'Check-in Open'
  if (actionState === 'sign-out') return 'Check-out Open'
  if (actionState === 'waiting-sign-out') {
    const remainingMs = getMillisecondsUntilSignOutOpen({ event, timeStatus })
    return Number.isFinite(remainingMs) && remainingMs > 0
      ? `Opens ${formatCompactDuration(remainingMs)}`
      : 'Waiting'
  }
  if (actionState === 'not-open') return 'Not Open'
  if (actionState === 'missed-check-in') return 'Missed'
  if (actionState === 'done') {
    return formatAttendanceOutcome(resolveAttendanceDisplayStatus(attendanceRecord))
  }
  return 'Closed'
}

function formatEventTimeLabel(event, lifecycleStatus) {
  const start = parseValidDate(event?.start_datetime)
  if (!start) return 'Time TBD'

  if (lifecycleStatus === 'ongoing') return 'Now'

  const now = new Date()
  const isSameDay =
    start.getFullYear() === now.getFullYear()
    && start.getMonth() === now.getMonth()
    && start.getDate() === now.getDate()

  return isSameDay ? timeFormatter.format(start) : dayFormatter.format(start)
}

function compareCandidateModels(left, right) {
  const leftRank = ACTION_RANK[left.actionState] ?? 99
  const rightRank = ACTION_RANK[right.actionState] ?? 99
  if (leftRank !== rightRank) return leftRank - rightRank

  const leftLifecycleRank = left.lifecycleStatus === 'ongoing' ? 0 : left.lifecycleStatus === 'upcoming' ? 1 : 2
  const rightLifecycleRank = right.lifecycleStatus === 'ongoing' ? 0 : right.lifecycleStatus === 'upcoming' ? 1 : 2
  if (leftLifecycleRank !== rightLifecycleRank) return leftLifecycleRank - rightLifecycleRank

  const leftStart = parseValidDate(left.event?.start_datetime)?.getTime() ?? 0
  const rightStart = parseValidDate(right.event?.start_datetime)?.getTime() ?? 0

  if (left.lifecycleStatus === 'completed' && right.lifecycleStatus === 'completed') {
    return rightStart - leftStart
  }

  return leftStart - rightStart
}

function shouldIncludeEvent(model) {
  if (!model?.event) return false
  if (model.actionState !== 'closed' && model.actionState !== 'done') return true
  return model.lifecycleStatus === 'ongoing' || model.lifecycleStatus === 'upcoming'
}

export function useGatherAttendance(previewSource = false) {
  const preview = computed(() => resolvePreviewFlag(previewSource))
  const route = useRoute()
  const router = useRouter()
  const apiBaseUrl = resolveApiBaseUrl()
  const { previewBundle } = useSgPreviewBundle(preview)
  const {
    currentUser,
    attendanceRecords,
    events,
    refreshAttendanceRecords,
  } = useDashboardSession()

  const now = ref(new Date())
  const previewAttendanceRecords = ref([])
  const eventTimeStatuses = ref({})
  const currentLocationLabel = ref('Location will be verified live')
  const currentLocationError = ref('')
  const locationCheck = ref(null)
  const loadingMessage = ref('')
  const latestError = ref(null)
  const latestSuccess = ref(null)
  const latestNotice = ref(null)
  const successSheet = ref(null)
  const isResolvingLocation = ref(false)
  const isSubmitting = ref(false)
  const cameraState = ref('idle')
  const backgroundVideoReady = ref(false)
  const focusVideoReady = ref(false)
  const backgroundVideoEl = ref(null)
  const focusVideoEl = ref(null)
  const mediaStream = ref(null)
  const faceDetected = ref(false)
  const selectedEventId = ref(null)
  const userCoords = ref(null)
  const requestId = ref(0)
  const previewSourceKey = computed(() => {
    if (!preview.value) return 'live'
    if (isGovernanceWorkspaceContext(route)) {
      const unitId = Number(previewBundle.value?.activeUnit?.id ?? 0)
      return `governance-${unitId || 'default'}`
    }
    return 'student'
  })

  let cameraStartPromise = null
  let faceDetectorInstance = null
  let faceDetectRaf = null
  let clockIntervalId = null
  let eventTimeStatusIntervalId = null
  let geocodeController = null

  const previewSeed = computed(() => {
    if (!preview.value) return null
    if (isGovernanceWorkspaceContext(route)) {
      return {
        user: previewBundle.value?.user ?? studentDashboardPreviewData.user,
        schoolSettings: previewBundle.value?.schoolSettings ?? studentDashboardPreviewData.schoolSettings,
        events: Array.isArray(previewBundle.value?.events)
          ? previewBundle.value.events
          : studentDashboardPreviewData.events,
        attendanceRecords: Array.isArray(previewBundle.value?.attendance?.records)
          ? previewBundle.value.attendance.records
          : studentDashboardPreviewData.attendanceRecords,
      }
    }

    return {
      user: studentDashboardPreviewData.user,
      schoolSettings: studentDashboardPreviewData.schoolSettings,
      events: studentDashboardPreviewData.events,
      attendanceRecords: studentDashboardPreviewData.attendanceRecords,
    }
  })

  const activeUser = computed(() => (
    preview.value ? previewSeed.value?.user ?? null : currentUser.value
  ))
  const activeSchoolSettings = computed(() => (
    preview.value ? previewSeed.value?.schoolSettings ?? null : null
  ))
  const activeEvents = computed(() => (
    preview.value ? previewSeed.value?.events ?? [] : events.value
  ))
  const activeAttendanceRecords = computed(() => (
    preview.value ? previewAttendanceRecords.value : attendanceRecords.value
  ))
  const faceImageUrl = computed(() => (
    activeUser.value?.student_profile?.photo_url
    || activeUser.value?.student_profile?.avatar_url
    || activeUser.value?.avatar_url
    || ''
  ))

  usePreviewTheme(preview, activeSchoolSettings)

  watch(
    [preview, previewSourceKey, () => previewSeed.value?.attendanceRecords],
    ([isPreview]) => {
      if (!isPreview) return
      previewAttendanceRecords.value = Array.isArray(previewSeed.value?.attendanceRecords)
        ? previewSeed.value.attendanceRecords.map((record) => normalizeAttendanceRecord({ ...record }))
        : []
    },
    { immediate: true, deep: true },
  )

  const attendanceByEventId = computed(() => {
    const map = new Map()

    getLatestAttendanceRecordsByEvent(activeAttendanceRecords.value).forEach((record) => {
      const eventId = Number(record?.event_id)
      if (!Number.isFinite(eventId)) return
      map.set(eventId, record)
    })

    return map
  })

  const schoolEvents = computed(() => {
    const schoolId = Number(activeUser.value?.school_id)

    return [...activeEvents.value]
      .filter((event) => {
        const eventId = Number(event?.id)
        if (!Number.isFinite(eventId)) return false
        return !Number.isFinite(schoolId) || Number(event?.school_id) === schoolId
      })
      .sort((left, right) => {
        const leftStart = parseValidDate(left?.start_datetime)?.getTime() ?? 0
        const rightStart = parseValidDate(right?.start_datetime)?.getTime() ?? 0
        return leftStart - rightStart
      })
  })

  const eventModels = computed(() => (
    schoolEvents.value.map((event) => {
      const id = Number(event?.id)
      const attendanceRecord = attendanceByEventId.value.get(id) ?? null
      const timeStatus = eventTimeStatuses.value[id] ?? null
      const lifecycleStatus = resolveEventLifecycleStatus(event, timeStatus) || 'upcoming'
      const actionState = resolveAttendanceActionState({
        event,
        eventStatus: lifecycleStatus,
        attendanceRecord,
        timeStatus,
        now: now.value,
      })
      const gatherActionKind = resolveGatherActionKind(event, timeStatus)
      const actionKind = gatherActionKind || resolveActionKind(actionState, attendanceRecord)
      const actionLabel = resolveActionLabel(actionKind)
      const canSubmit = Boolean(gatherActionKind)
      const statusLabel = canSubmit
        ? (gatherActionKind === 'sign-out' ? 'Check-out Open' : 'Check-in Open')
        : resolveEventStatusLabel({
          actionState,
          attendanceRecord,
          event,
          timeStatus,
        })

      return {
        id,
        event,
        attendanceRecord,
        timeStatus,
        lifecycleStatus,
        actionKind,
        actionLabel,
        actionState,
        actionTone: canSubmit ? 'primary' : resolveActionTone(actionState),
        canSubmit,
        tone: canSubmit ? 'ready' : resolveEventTone(actionState),
        statusLabel,
        timeLabel: formatEventTimeLabel(event, lifecycleStatus),
        metaLabel: event?.location || 'Location unavailable',
        scopeLabel: event?.scope_label || '',
        eventGeo: resolveEventGeo(event),
      }
    })
  ))

  const candidateEvents = computed(() => {
    const filtered = eventModels.value.filter(shouldIncludeEvent).sort(compareCandidateModels)

    if (filtered.length) return filtered

    return eventModels.value
      .filter((model) => model.lifecycleStatus === 'ongoing' || model.lifecycleStatus === 'upcoming')
      .sort(compareCandidateModels)
      .slice(0, 6)
  })

  const selectedEvent = computed(() => {
    const normalizedSelectedId = Number(selectedEventId.value)
    if (Number.isFinite(normalizedSelectedId)) {
      const current = candidateEvents.value.find((item) => item.id === normalizedSelectedId)
      if (current) return current
    }

    return candidateEvents.value[0] ?? null
  })

  const cameraReady = computed(() => (
    cameraState.value === 'ready' && backgroundVideoReady.value && focusVideoReady.value
  ))
  const currentTimeLabel = computed(() => timeFormatter.format(now.value))
  const distanceLabel = computed(() => {
    const verifiedDistance =
      Number(locationCheck.value?.effective_distance_m ?? locationCheck.value?.distance_m)

    if (Number.isFinite(verifiedDistance)) {
      return formatVenueDistance(verifiedDistance)
    }

    const geo = selectedEvent.value?.eventGeo
    const computedDistance = measureDistanceMeters(userCoords.value, {
      latitude: geo?.latitude,
      longitude: geo?.longitude,
    })

    return formatVenueDistance(computedDistance)
  })
  const locationChipLabel = computed(() => {
    if (distanceLabel.value) return distanceLabel.value
    if (selectedEvent.value?.event?.geo_required) return 'GPS required'
    if (userCoords.value?.latitude && userCoords.value?.longitude) return 'GPS ready'
    return 'Live GPS'
  })
  const locationMetaLabel = computed(() => (
    currentLocationError.value
      ? currentLocationError.value
      : currentLocationLabel.value
  ))
  const statusModel = computed(() => {
    if (latestError.value?.message) {
      return {
        tone: 'error',
        icon: 'shield-x',
        message: latestError.value.message,
      }
    }

    if (latestSuccess.value?.message) {
      return {
        tone: 'success',
        icon: 'shield-check',
        message: latestSuccess.value.message,
      }
    }

    if (loadingMessage.value) {
      return {
        tone: 'loading',
        icon: 'loader',
        message: loadingMessage.value,
      }
    }

    if (cameraState.value === 'denied') {
      return {
        tone: 'error',
        icon: 'shield-x',
        message: 'Camera access is required to continue.',
      }
    }

    if (cameraState.value === 'unsupported') {
      return {
        tone: 'error',
        icon: 'shield-x',
        message: 'Camera is not available on this device.',
      }
    }

    if (currentLocationError.value) {
      return {
        tone: 'error',
        icon: 'shield-x',
        message: currentLocationError.value,
      }
    }

    if (latestNotice.value?.message) {
      return {
        tone: latestNotice.value.tone || 'neutral',
        icon: latestNotice.value.tone === 'error' ? 'shield-x' : 'shield',
        message: latestNotice.value.message,
      }
    }

    if (!selectedEvent.value) {
      return {
        tone: 'neutral',
        icon: 'shield',
        message: 'No attendance-ready events right now.',
      }
    }

    return {
      tone: 'neutral',
      icon: 'shield',
      message: resolveLiveStatusMessage({
        cameraReady: cameraReady.value,
        faceDetected: faceDetected.value,
        actionLabel: selectedEvent.value.actionLabel,
        selectedEvent: selectedEvent.value,
      }),
    }
  })
  const submitButtonLabel = computed(() => {
    if (!selectedEvent.value) return 'No Event Selected'
    return isSubmitting.value ? `${selectedEvent.value.actionLabel}...` : selectedEvent.value.actionLabel
  })
  const actionHint = computed(() => {
    if (!selectedEvent.value) return 'Open the events page when a live attendance session is available.'
    if (distanceLabel.value) return distanceLabel.value
    if (selectedEvent.value.scopeLabel) return selectedEvent.value.scopeLabel
    return locationMetaLabel.value
  })
  const headerEyebrow = computed(() => (
    selectedEvent.value?.scopeLabel
    || activeUser.value?.school_code
    || 'Live attendance'
  ))
  const canCapture = computed(() => Boolean(selectedEvent.value) && !isSubmitting.value)

  function clearTransientState() {
    latestError.value = null
    latestSuccess.value = null
    latestNotice.value = null
  }

  function setBackgroundVideoRef(el) {
    backgroundVideoEl.value = el
  }

  function setFocusVideoRef(el) {
    focusVideoEl.value = el
  }

  function getCameraProcessingVideoEl() {
    const candidates = [
      backgroundVideoEl.value,
      focusVideoEl.value,
    ]

    return candidates.find((el) => (
      el
      && el.readyState >= 2
      && el.videoWidth > 0
      && el.videoHeight > 0
    )) || candidates.find(Boolean) || null
  }

  async function attachStreamToVideo(el, readyRef) {
    if (!el || !mediaStream.value) return false

    el.autoplay = true
    el.muted = true
    el.playsInline = true
    el.srcObject = mediaStream.value
    readyRef.value = false

    try {
      await el.play().catch(() => null)
    } catch {
      // Keep the stream attached and wait for the browser to render it.
    }

    if (el.readyState >= 2) {
      readyRef.value = true
      return true
    }

    return new Promise((resolve) => {
      let settled = false
      const cleanup = () => {
        el.removeEventListener('loadeddata', handleReady)
        el.removeEventListener('canplay', handleReady)
        el.removeEventListener('error', handleError)
      }
      const finish = (value) => {
        if (settled) return
        settled = true
        cleanup()
        readyRef.value = value
        resolve(value)
      }
      const handleReady = () => finish(true)
      const handleError = () => finish(false)

      el.addEventListener('loadeddata', handleReady, { once: true })
      el.addEventListener('canplay', handleReady, { once: true })
      el.addEventListener('error', handleError, { once: true })
      setTimeout(() => finish(false), 2400)
    })
  }

  async function attachStreamToVideos() {
    await Promise.allSettled([
      attachStreamToVideo(backgroundVideoEl.value, backgroundVideoReady),
      attachStreamToVideo(focusVideoEl.value, focusVideoReady),
    ])
  }

  async function startCamera() {
    if (!navigator?.mediaDevices?.getUserMedia) {
      cameraState.value = 'unsupported'
      return false
    }

    if (cameraState.value === 'ready' && mediaStream.value) {
      await attachStreamToVideos()
      return cameraReady.value
    }

    if (cameraStartPromise) return cameraStartPromise

    cameraStartPromise = (async () => {
      cameraState.value = 'requesting'
      const permission = await requestCameraPermission()
      if (!permission.granted) {
        cameraState.value = permission.denied ? 'denied' : 'unsupported'
        return false
      }

      try {
        mediaStream.value = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
          },
          audio: false,
        })
      } catch {
        cameraState.value = 'denied'
        return false
      }

      cameraState.value = 'ready'
      await nextTick()
      await attachStreamToVideos()
      return cameraReady.value
    })()

    try {
      return await cameraStartPromise
    } finally {
      cameraStartPromise = null
    }
  }

  function stopFaceDetection() {
    if (faceDetectRaf) cancelAnimationFrame(faceDetectRaf)
    faceDetectRaf = null
    faceDetected.value = false
  }

  function stopCamera() {
    if (mediaStream.value) {
      mediaStream.value.getTracks().forEach((track) => track.stop())
      mediaStream.value = null
    }

    if (backgroundVideoEl.value) {
      backgroundVideoEl.value.srcObject = null
    }
    if (focusVideoEl.value) {
      focusVideoEl.value.srcObject = null
    }

    backgroundVideoReady.value = false
    focusVideoReady.value = false
    if (cameraState.value !== 'denied' && cameraState.value !== 'unsupported') {
      cameraState.value = 'idle'
    }
    stopFaceDetection()
  }

  async function ensureFaceDetector() {
    if (faceDetectorInstance) return true

    try {
      faceDetectorInstance = await initFaceScanDetector({
        wasmBaseUrl:
          import.meta.env.VITE_FACE_DETECTOR_WASM_URL
          || 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm',
        modelAssetPath:
          import.meta.env.VITE_FACE_DETECTOR_MODEL_URL
          || 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite',
        minDetectionConfidence: Number(import.meta.env.VITE_FACE_DETECTOR_MIN_CONFIDENCE ?? 0.5),
        minSuppressionThreshold: Number(import.meta.env.VITE_FACE_DETECTOR_SUPPRESSION ?? 0.3),
        runningMode: 'VIDEO',
      })
      return Boolean(faceDetectorInstance)
    } catch {
      faceDetectorInstance = null
      resetFaceScanDetector()
      return false
    }
  }

  async function startFaceDetection() {
    if (!cameraReady.value || !getCameraProcessingVideoEl()) return

    const detectorReady = await ensureFaceDetector()
    if (!detectorReady) {
      faceDetected.value = true
      return
    }

    stopFaceDetection()
    let streak = 0
    let lastSeenAt = 0
    let lastDetectAt = 0
    const detectIntervalMs = Number(import.meta.env.VITE_FACE_DETECTOR_INTERVAL_MS ?? 120)
    const detectHoldMs = Number(import.meta.env.VITE_FACE_SCAN_DETECT_HOLD_MS ?? 700)
    const minFrames = Number(import.meta.env.VITE_FACE_SCAN_MIN_FRAMES ?? 1)

    const loop = (nowMs) => {
      const videoEl = getCameraProcessingVideoEl()
      if (!videoEl || !cameraReady.value) return

      if (nowMs - lastDetectAt < detectIntervalMs) {
        faceDetectRaf = requestAnimationFrame(loop)
        return
      }

      lastDetectAt = nowMs
      try {
        const result = faceDetectorInstance.detectForVideo(videoEl, nowMs)
        const hasFace = Array.isArray(result?.detections) && result.detections.length > 0
        if (hasFace) {
          streak += 1
          lastSeenAt = nowMs
        } else {
          streak = 0
        }

        const held = lastSeenAt > 0 && nowMs - lastSeenAt <= detectHoldMs
        faceDetected.value = streak >= minFrames || held
      } catch {
        faceDetected.value = false
      }

      faceDetectRaf = requestAnimationFrame(loop)
    }

    faceDetectRaf = requestAnimationFrame(loop)
  }

  function waitForFaceOrTimeout(timeoutMs = faceScanTimeoutMs) {
    return new Promise((resolve) => {
      if (!faceScanGateEnabled || faceDetected.value) {
        resolve('detected')
        return
      }

      let stopFaceWatch = () => {}
      let stopCameraWatch = () => {}
      let timer = null

      const cleanup = () => {
        if (timer) clearTimeout(timer)
        stopFaceWatch()
        stopCameraWatch()
      }

      timer = window.setTimeout(() => {
        cleanup()
        resolve('timeout')
      }, timeoutMs)

      stopFaceWatch = watch(faceDetected, (detected) => {
        if (!detected) return
        cleanup()
        resolve('detected')
      })

      stopCameraWatch = watch(cameraReady, (ready) => {
        if (ready) return
        cleanup()
        resolve('camera-not-ready')
      })
    })
  }

  async function waitForFaceDetection() {
    if (!faceScanGateEnabled || faceDetected.value) return true

    const detectorReady = await ensureFaceDetector()
    if (!detectorReady) {
      faceDetected.value = true
      return true
    }

    await startFaceDetection()
    return (await waitForFaceOrTimeout()) === 'detected'
  }

  async function refreshLocationLabel(coords, preferredLabel = '') {
    const latitude = Number(coords?.latitude)
    const longitude = Number(coords?.longitude)
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      currentLocationLabel.value = 'Location will be verified live'
      return currentLocationLabel.value
    }

    geocodeController?.abort?.()
    geocodeController = typeof AbortController !== 'undefined' ? new AbortController() : null

    try {
      currentLocationLabel.value = await resolveLocationLabel({
        latitude,
        longitude,
        preferredLabel,
        signal: geocodeController?.signal,
      })
    } catch {
      currentLocationLabel.value = formatCoordinateLocationLabel({ latitude, longitude })
    }

    return currentLocationLabel.value
  }

  async function resolveCurrentPosition({ precise = false } = {}) {
    const activeModel = selectedEvent.value
    if (!activeModel?.event) {
      throw new Error('Choose an event first.')
    }

    loadingMessage.value = 'Checking current location...'
    isResolvingLocation.value = true
    currentLocationError.value = ''

    try {
      const desiredAccuracy = Number(activeModel.event?.geo_max_accuracy_m)
      const coords = precise && activeModel.event?.geo_required
        ? await getCurrentPositionWithinAccuracyOrThrow({
          desiredAccuracy: Number.isFinite(desiredAccuracy) && desiredAccuracy > 0
            ? desiredAccuracy
            : null,
          enableHighAccuracy: true,
          timeout: Math.max(Number(import.meta.env.VITE_GEOLOCATION_TIMEOUT_MS ?? 9000), 9000),
          maximumAge: 0,
        })
        : await getCurrentPositionOrThrow({
          enableHighAccuracy: precise,
          timeout: Math.max(Number(import.meta.env.VITE_GEOLOCATION_TIMEOUT_MS ?? 7000), 7000),
          maximumAge: precise ? 0 : 45_000,
        })

      userCoords.value = {
        latitude: coords.latitude,
        longitude: coords.longitude,
        accuracy: coords.accuracy ?? null,
        capturedAt: new Date().toISOString(),
      }
      await refreshLocationLabel(userCoords.value)
      return userCoords.value
    } catch (error) {
      currentLocationError.value = error?.message || 'Unable to determine your current location.'
      throw error
    } finally {
      isResolvingLocation.value = false
    }
  }

  async function warmLocationAccess() {
    if (preview.value) return null

    const access = await prepareLocationAccess({
      enableHighAccuracy: false,
      timeout: Math.max(Number(import.meta.env.VITE_GEOLOCATION_TIMEOUT_MS ?? 7000), 7000),
      maximumAge: 45_000,
    }).catch(() => null)

    const coords = access?.position
    if (!coords) {
      return access
    }

    userCoords.value = {
      latitude: coords.latitude,
      longitude: coords.longitude,
      accuracy: coords.accuracy ?? null,
      capturedAt: coords.capturedAt || new Date().toISOString(),
    }

    await refreshLocationLabel(userCoords.value).catch(() => null)
    return access
  }

  async function verifyCurrentLocation(coords) {
    const activeModel = selectedEvent.value
    if (!activeModel?.event) {
      throw new Error('Choose an event first.')
    }

    if (!activeModel.event?.geo_required) {
      locationCheck.value = {
        ok: true,
        accuracy_m: coords?.accuracy ?? null,
      }
      return locationCheck.value
    }

    if (preview.value) {
      const measuredDistance = measureDistanceMeters(coords, {
        latitude: activeModel.eventGeo.latitude,
        longitude: activeModel.eventGeo.longitude,
      })
      locationCheck.value = {
        ok: true,
        distance_m: measuredDistance,
        radius_m: activeModel.eventGeo.radiusM,
        accuracy_m: coords?.accuracy ?? null,
      }
      return locationCheck.value
    }

    const token = localStorage.getItem('aura_token')
    if (!token) {
      throw new Error('Your session has expired. Please sign in again.')
    }

    const verification = await verifyEventLocation(apiBaseUrl, token, activeModel.id, {
      latitude: coords.latitude,
      longitude: coords.longitude,
      accuracy_m: coords.accuracy ?? null,
    })

    locationCheck.value = verification
    if (verification?.time_status) {
      eventTimeStatuses.value = {
        ...eventTimeStatuses.value,
        [activeModel.id]: verification.time_status,
      }
    }

    if (!verification?.ok) {
      throw new Error(buildAttendanceLocationErrorMessage(verification))
    }

    return verification
  }

  async function captureVideoFrameBlob() {
    const element = getCameraProcessingVideoEl()
    if (!element || element.videoWidth <= 0 || element.videoHeight <= 0) {
      throw new Error('Cannot verify face right now. Camera preview is not ready.')
    }

    const size = Math.min(element.videoWidth, element.videoHeight)
    const startX = Math.max(0, (element.videoWidth - size) / 2)
    const startY = Math.max(0, (element.videoHeight - size) / 2)
    const canvas = document.createElement('canvas')
    canvas.width = 720
    canvas.height = 720
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      throw new Error('Cannot prepare the face image right now.')
    }

    ctx.drawImage(element, startX, startY, size, size, 0, 0, canvas.width, canvas.height)
    return await new Promise((resolve, reject) => {
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('Failed to capture a camera frame.'))
            return
          }
          resolve(blob)
        },
        'image/jpeg',
        0.92,
      )
    })
  }

  function upsertPreviewAttendanceRecord(record) {
    const normalizedRecord = normalizeAttendanceRecord(record)
    const normalizedEventId = Number(normalizedRecord?.event_id)
    if (!Number.isFinite(normalizedEventId)) {
      return normalizedRecord
    }

    previewAttendanceRecords.value = [
      ...previewAttendanceRecords.value.filter((item) => Number(item?.event_id) !== normalizedEventId),
      normalizedRecord,
    ]

    return normalizedRecord
  }

  async function recordAttendance(imageBlob, coords) {
    const activeModel = selectedEvent.value
    const normalizedEventId = Number(activeModel?.id)
    if (!Number.isFinite(normalizedEventId)) {
      throw new Error('Choose an event first.')
    }

    const studentId =
      activeUser.value?.student_profile?.student_id
      ?? activeUser.value?.student_profile?.id
      ?? activeUser.value?.id
      ?? null

    if (preview.value) {
      const existingAttendanceRecord = pickLatestAttendanceRecord(
        previewAttendanceRecords.value,
        normalizedEventId,
      )
      const action = isOpenAttendanceRecord(existingAttendanceRecord) ? 'sign_out' : 'sign_in'
      const nowIso = new Date().toISOString()
      const nextRecord = upsertPreviewAttendanceRecord({
        ...(existingAttendanceRecord || {}),
        id: Number(existingAttendanceRecord?.id) || Date.now(),
        event_id: normalizedEventId,
        event_name: activeModel.event?.name || null,
        student_id: studentId != null ? String(studentId) : null,
        method: existingAttendanceRecord?.method || 'face_scan',
        status: existingAttendanceRecord?.status || existingAttendanceRecord?.check_in_status || 'present',
        display_status: action === 'sign_out'
          ? (existingAttendanceRecord?.status || existingAttendanceRecord?.check_in_status || 'present')
          : 'incomplete',
        completion_state: action === 'sign_out' ? 'completed' : 'incomplete',
        check_in_status: existingAttendanceRecord?.check_in_status || existingAttendanceRecord?.status || 'present',
        check_out_status: action === 'sign_out' ? 'present' : null,
        time_in: existingAttendanceRecord?.time_in || nowIso,
        time_out: action === 'sign_out' ? nowIso : null,
        created_at: existingAttendanceRecord?.created_at || nowIso,
        updated_at: nowIso,
        is_valid_attendance: action === 'sign_out',
        notes: action === 'sign_out' ? null : 'Pending sign-out.',
      })

      return {
        result: {
          ok: true,
          action,
          attendance_id: nextRecord.id,
          time_in: nextRecord.time_in,
          time_out: nextRecord.time_out,
          geo: {
            ok: true,
            distance_m: locationCheck.value?.distance_m ?? null,
            accuracy_m: coords?.accuracy ?? null,
          },
        },
        attendanceRecord: nextRecord,
      }
    }

    const response = await submitPublicAttendanceScan({
      eventId: normalizedEventId,
      imageBlob,
      location: {
        latitude: coords?.latitude ?? null,
        longitude: coords?.longitude ?? null,
        accuracyM: coords?.accuracy ?? null,
      },
      cooldownStudentIds: [],
    })
    const outcomeSummary = summarizeGatherScanOutcomes(response)
    if (!outcomeSummary.successfulCount) {
      throw new Error(
        outcomeSummary.primaryOutcome?.message
        || response?.message
        || 'No eligible student faces were matched in this scan.',
      )
    }

    if (response?.geo?.time_status) {
      eventTimeStatuses.value = {
        ...eventTimeStatuses.value,
        [normalizedEventId]: response.geo.time_status,
      }
    }
    if (response?.geo) {
      locationCheck.value = response.geo
    }

    const primaryOutcome = outcomeSummary.primaryOutcome

    return {
      result: {
        ok: true,
        action: primaryOutcome?.action || 'recorded',
        time_in: primaryOutcome?.time_in ?? null,
        time_out: primaryOutcome?.time_out ?? null,
        student_name: primaryOutcome?.student_name ?? null,
        student_id: primaryOutcome?.student_id ?? null,
        message:
          primaryOutcome?.message
          || response?.message
          || 'Gather scan processed successfully.',
        detected_count: outcomeSummary.detectedCount,
        recorded_count: outcomeSummary.successfulCount,
        geo: response?.geo ?? null,
      },
      attendanceRecord: null,
      outcomes: outcomeSummary.outcomes,
    }
  }

  async function refreshEventStatuses(forceIds = []) {
    if (preview.value) return

    const token = localStorage.getItem('aura_token')
    if (!token) return

    const candidateIds = candidateEvents.value.slice(0, 8).map((item) => item.id)
    const eventIds = [...new Set([...candidateIds, ...forceIds].filter((id) => Number.isFinite(Number(id))))]
    if (!eventIds.length) return

    const nextRequestId = requestId.value + 1
    requestId.value = nextRequestId

    const results = await Promise.allSettled(
      eventIds.map((eventId) => getEventTimeStatus(apiBaseUrl, token, eventId))
    )

    if (requestId.value !== nextRequestId) return

    const nextStatuses = { ...eventTimeStatuses.value }

    results.forEach((result, index) => {
      if (result.status !== 'fulfilled') return
      nextStatuses[eventIds[index]] = result.value
    })

    eventTimeStatuses.value = nextStatuses
  }

  function startClock() {
    if (clockIntervalId != null) clearInterval(clockIntervalId)
    clockIntervalId = window.setInterval(() => {
      now.value = new Date()
    }, 1000)
  }

  function stopClock() {
    if (clockIntervalId != null) {
      clearInterval(clockIntervalId)
      clockIntervalId = null
    }
  }

  function startEventStatusPolling() {
    if (eventTimeStatusIntervalId != null) clearInterval(eventTimeStatusIntervalId)
    if (preview.value) return

    eventTimeStatusIntervalId = window.setInterval(() => {
      const eventId = Number(selectedEvent.value?.id)
      void refreshEventStatuses(Number.isFinite(eventId) ? [eventId] : [])
    }, 15000)
  }

  function stopEventStatusPolling() {
    if (eventTimeStatusIntervalId != null) {
      clearInterval(eventTimeStatusIntervalId)
      eventTimeStatusIntervalId = null
    }
  }

  function selectEvent(eventId) {
    const normalizedEventId = Number(eventId)
    if (!Number.isFinite(normalizedEventId)) return

    selectedEventId.value = normalizedEventId
    locationCheck.value = null
    currentLocationError.value = ''
    clearTransientState()
    successSheet.value = null
  }

  function dismissSuccess() {
    successSheet.value = null
  }

  async function goBack() {
    if (hasNavigableHistory(route)) {
      router.back()
      return
    }

    router.push(resolveGatherWelcomeLocation(route))
  }

  async function openEventsView() {
    router.push(resolveEventListLocation(route))
  }

  async function handleSubmit() {
    if (!selectedEvent.value || isSubmitting.value) return

    clearTransientState()

    if (!selectedEvent.value.canSubmit) {
      latestNotice.value = resolveGatherBlockedStateModel(
        selectedEvent.value.actionLabel,
        selectedEvent.value.event,
        selectedEvent.value.timeStatus,
      )
      return
    }

    isSubmitting.value = true
    loadingMessage.value = 'Preparing verification...'

    try {
      const cameraStarted = await startCamera()
      if (!cameraStarted || !cameraReady.value) {
        throw new Error('Camera access is required to continue.')
      }

      loadingMessage.value = 'Checking face...'
      await waitForFaceDetection()

      const coords = await resolveCurrentPosition({ precise: true })
      loadingMessage.value = 'Verifying location...'
      await verifyCurrentLocation(coords)

      loadingMessage.value = `${selectedEvent.value.actionLabel}...`
      const imageBlob = await captureVideoFrameBlob()
      const { result } = await recordAttendance(imageBlob, coords)
      await refreshEventStatuses([selectedEvent.value.id]).catch(() => null)

      const recordedCount = Number(result?.recorded_count) || 0
      const detectedCount = Number(result?.detected_count) || recordedCount
      const completedAt = result?.time_out || result?.time_in || new Date().toISOString()
      const detectedLabel = String(detectedCount)
      const recordedLabel = String(recordedCount)
      const subtitle = recordedCount > 1
        ? `${recordedLabel} students were recorded for ${selectedEvent.value.event.name}.`
        : `Attendance recorded for ${selectedEvent.value.event.name}.`

      latestSuccess.value = {
        message: result?.message || 'Gather scan processed successfully.',
      }
      currentLocationError.value = ''
      successSheet.value = {
        title: recordedCount > 1
          ? 'Gather scan complete'
          : (isSignOutAction(result?.action) ? 'Check out complete' : 'Check in complete'),
        subtitle,
        rows: [
          {
            label: 'Recorded',
            value: recordedLabel,
          },
          {
            label: 'Detected',
            value: detectedLabel,
          },
          {
            label: 'Time',
            value: formatTimestamp(completedAt || new Date().toISOString()),
          },
          result?.student_name
            ? {
              label: 'Latest',
              value: result.student_name,
            }
            : null,
          distanceLabel.value
            ? {
              label: 'Distance',
              value: distanceLabel.value,
            }
            : null,
        ].filter(Boolean),
      }
    } catch (error) {
      latestError.value = {
        message: resolveLocationErrorMessage(
          error,
          `Unable to complete ${selectedEvent.value.actionLabel.toLowerCase()} right now.`,
        ),
      }
    } finally {
      loadingMessage.value = ''
      isSubmitting.value = false
    }
  }

  async function initialize() {
    clearTransientState()
    if (!preview.value) {
      await refreshAttendanceRecords().catch(() => null)
    }
    await refreshEventStatuses(
      Number.isFinite(Number(selectedEventId.value)) ? [Number(selectedEventId.value)] : []
    ).catch(() => null)
    await warmLocationAccess().catch(() => null)
    await startCamera().catch(() => null)
    await startFaceDetection()
    startEventStatusPolling()
  }

  watch(
    () => [backgroundVideoEl.value, focusVideoEl.value, mediaStream.value],
    ([backgroundEl, focusEl, stream]) => {
      if (backgroundEl && focusEl && stream) {
        void attachStreamToVideos()
      }
    },
    { flush: 'post' },
  )

  watch(
    () => cameraReady.value,
    (ready) => {
      if (ready) {
        void startFaceDetection()
      } else {
        stopFaceDetection()
      }
    },
  )

  watch(
    () => candidateEvents.value.map((item) => item.id).join('|'),
    () => {
      const currentSelectedId = Number(selectedEventId.value)
      const currentExists = candidateEvents.value.some((item) => item.id === currentSelectedId)

      if (!currentExists) {
        selectedEventId.value = candidateEvents.value.find((item) => item.canSubmit)?.id
          ?? candidateEvents.value[0]?.id
          ?? null
      }

      const selectedId = Number(selectedEventId.value)
      if (Number.isFinite(selectedId)) {
        void refreshEventStatuses([selectedId]).catch(() => null)
      }
    },
    { immediate: true },
  )

  watch(
    () => selectedEvent.value?.id,
    (eventId, previousEventId) => {
      if (eventId === previousEventId) return
      locationCheck.value = null
      currentLocationError.value = ''
      clearTransientState()
      successSheet.value = null
      if (Number.isFinite(Number(eventId))) {
        void refreshEventStatuses([Number(eventId)]).catch(() => null)
      }
    },
  )

  onMounted(() => {
    startClock()
    void initialize()
  })

  onBeforeUnmount(() => {
    stopClock()
    stopEventStatusPolling()
    stopCamera()
    stopFaceDetection()
    geocodeController?.abort?.()
    geocodeController = null
    resetFaceScanDetector()
    faceDetectorInstance = null
  })

  return {
    actionHint,
    cameraReady,
    canCapture,
    candidateEvents,
    currentTimeLabel,
    dismissSuccess,
    faceDetected,
    faceImageUrl,
    goBack,
    handleSubmit,
    hasEvents: computed(() => candidateEvents.value.length > 0),
    headerEyebrow,
    isResolvingLocation,
    isSubmitting,
    locationChipLabel,
    locationMetaLabel,
    openEventsView,
    selectedEvent,
    selectEvent,
    setBackgroundVideoRef,
    setFocusVideoRef,
    statusModel,
    submitButtonLabel,
    successSheet,
  }
}
