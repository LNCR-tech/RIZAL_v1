import { computed, nextTick, onBeforeUnmount, onMounted, ref, unref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { initFaceScanDetector, resetFaceScanDetector } from '@/composables/useFaceScanDetector.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { studentDashboardPreviewData } from '@/data/studentDashboardPreview.js'
import {
  formatCompactDuration,
  getMillisecondsUntilSignOutOpen,
  isOpenAttendanceRecord,
  parseEventDateTime,
  resolveAttendanceActionState,
  resolveAttendanceCompletionState,
  resolveEventLifecycleStatus,
  buildAttendanceLocationErrorMessage,
} from '@/services/attendanceFlow.js'
import {
  getCurrentPositionOrThrow,
  getCurrentPositionWithinAccuracyOrThrow,
  requestCameraPermission,
} from '@/services/devicePermissions.js'
import {
  getEventTimeStatus,
  recordFaceScanAttendance as postFaceScanAttendance,
  resolveApiBaseUrl,
  verifyEventLocation,
} from '@/services/backendApi.js'
import { normalizeAttendanceRecord } from '@/services/backendNormalizers.js'
import {
  formatCoordinateLocationLabel,
  formatVenueDistance,
  measureDistanceMeters,
  resolveLocationLabel,
} from '@/services/locationDisplay.js'
import {
  hasNavigableHistory,
  resolveBackFallbackLocation,
} from '@/services/routeWorkspace.js'

const clockFormatter = new Intl.DateTimeFormat('en-PH', {
  hour: 'numeric',
  minute: '2-digit',
})
const timestampFormatter = new Intl.DateTimeFormat('en-PH', {
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
})

function resolvePreviewFlag(source) {
  return Boolean(unref(typeof source === 'function' ? source() : source))
}

function normalizeAction(action) {
  return String(action || '').trim().toLowerCase().replace(/[\s-]+/g, '_')
}

function isSignOutAction(action) {
  return ['sign_out', 'signed_out', 'check_out', 'checkout', 'time_out', 'out'].includes(
    normalizeAction(action)
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

function formatAttendanceTimestamp(value) {
  if (!value) return '--, --'
  const parsed = parseEventDateTime(value)
  return Number.isFinite(parsed.getTime()) ? timestampFormatter.format(parsed) : '--, --'
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

function resolveBlockedStateModel(actionState, actionLabel, event, timeStatus) {
  if (actionState === 'not-open') {
    return {
      tone: 'neutral',
      message: `${actionLabel} is not available yet.`,
    }
  }

  if (actionState === 'waiting-sign-out') {
    const remainingMs = getMillisecondsUntilSignOutOpen({
      event,
      timeStatus,
    })
    const countdown = Number.isFinite(remainingMs) && remainingMs > 0
      ? ` Sign-out opens in ${formatCompactDuration(remainingMs)}.`
      : ''

    return {
      tone: 'neutral',
      message: `Check out is not available yet.${countdown}`.trim(),
    }
  }

  if (actionState === 'missed-check-in') {
    return {
      tone: 'error',
      message: 'Check-in is already closed for this event.',
    }
  }

  if (actionState === 'done') {
    return {
      tone: 'neutral',
      message: 'Attendance is already completed for this event.',
    }
  }

  return {
    tone: 'error',
    message: 'Attendance is already closed for this event.',
  }
}

function resolveLiveStatusMessage({ cameraReady, faceDetected, locationReady, actionLabel }) {
  if (!cameraReady) {
    return 'Allow camera access to continue.'
  }

  if (!faceDetected) {
    return 'Center your face inside the frame.'
  }

  if (!locationReady) {
    return 'Face detected. Checking your location...'
  }

  return `${actionLabel} is ready.`
}

function resolveLocationErrorMessage(source, fallback = 'Unable to verify your location.') {
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

function buildOptimisticAttendanceRecord({
  result,
  existingAttendanceRecord = null,
  eventId,
  studentId,
}) {
  const normalizedEventId = Number(eventId)
  if (!Number.isFinite(normalizedEventId)) {
    return null
  }

  const attendanceId = Number(result?.attendance_id)
  const action = normalizeAction(result?.action)
  const timeIn = result?.time_in ?? existingAttendanceRecord?.time_in ?? null
  const timeOut = result?.time_out ?? existingAttendanceRecord?.time_out ?? null
  const checkInStatus =
    result?.geo?.attendance_decision?.attendance_status
    ?? existingAttendanceRecord?.check_in_status
    ?? existingAttendanceRecord?.status
    ?? null
  const hasCompletedAttendance = Boolean(timeOut) || isSignOutAction(action)
  const finalizedStatus =
    existingAttendanceRecord?.check_in_status
    ?? checkInStatus
    ?? existingAttendanceRecord?.status
    ?? 'present'
  const isValidCompletedAttendance = hasCompletedAttendance
    ? ['present', 'late'].includes(String(finalizedStatus || '').trim().toLowerCase())
    : false

  if (!Number.isFinite(attendanceId) && !timeIn && !timeOut) {
    return null
  }

  return normalizeAttendanceRecord({
    ...(existingAttendanceRecord || {}),
    id: Number.isFinite(attendanceId) ? attendanceId : Number(existingAttendanceRecord?.id ?? 0),
    event_id: normalizedEventId,
    student_id: studentId,
    method: existingAttendanceRecord?.method || 'face_scan',
    status: finalizedStatus,
    display_status: hasCompletedAttendance ? finalizedStatus : 'incomplete',
    completion_state: hasCompletedAttendance ? 'completed' : 'incomplete',
    check_in_status: checkInStatus,
    check_out_status: hasCompletedAttendance ? 'present' : null,
    time_in: timeIn,
    time_out: timeOut,
    duration_minutes: result?.duration_minutes ?? existingAttendanceRecord?.duration_minutes ?? null,
    is_valid_attendance: hasCompletedAttendance ? isValidCompletedAttendance : false,
    notes: hasCompletedAttendance
      ? (isValidCompletedAttendance
        ? null
        : existingAttendanceRecord?.notes ?? 'Attendance was completed, but the final result is not valid.')
      : 'Pending sign-out.',
  })
}

export function useMobileStudentAttendance(previewSource = false) {
  const preview = computed(() => resolvePreviewFlag(previewSource))
  const route = useRoute()
  const router = useRouter()
  const apiBaseUrl = resolveApiBaseUrl()
  const {
    currentUser,
    ensureDashboardEvent,
    getDashboardEventById,
    getLatestAttendanceForEvent,
    refreshAttendanceRecords,
    upsertAttendanceRecordSnapshot,
  } = useDashboardSession()

  const previewAttendanceRecords = ref(
    studentDashboardPreviewData.attendanceRecords.map((record) => ({ ...record }))
  )
  const now = ref(new Date())
  const eventTimeStatus = ref(null)
  const userCoords = ref(null)
  const locationCheck = ref(null)
  const currentLocationLabel = ref('Current location unavailable')
  const currentLocationError = ref('')
  const latestError = ref(null)
  const latestSuccess = ref(null)
  const latestNotice = ref(null)
  const loadingMessage = ref('')
  const isInitializing = ref(true)
  const isResolvingLocation = ref(false)
  const isSubmitting = ref(false)
  const cameraState = ref('idle')
  const backgroundVideoReady = ref(false)
  const focusVideoReady = ref(false)
  const backgroundVideoEl = ref(null)
  const focusVideoEl = ref(null)
  const mediaStream = ref(null)
  const faceDetected = ref(false)
  const requestId = ref(0)

  let cameraStartPromise = null
  let faceDetectorInstance = null
  let faceDetectRaf = null
  let clockIntervalId = null
  let eventTimeStatusIntervalId = null
  let geocodeController = null

  const activeUser = computed(() => (
    preview.value ? studentDashboardPreviewData.user : currentUser.value
  ))
  const activeSchoolSettings = computed(() => (
    preview.value ? studentDashboardPreviewData.schoolSettings : null
  ))
  const eventId = computed(() => Number(route.params.id))
  const event = computed(() => (
    preview.value
      ? studentDashboardPreviewData.events.find((item) => Number(item?.id) === eventId.value) ?? null
      : getDashboardEventById(eventId.value)
  ))
  const latestAttendanceRecord = computed(() => (
    preview.value
      ? pickLatestAttendanceRecord(previewAttendanceRecords.value, eventId.value)
      : getLatestAttendanceForEvent(eventId.value)
  ))
  const lifecycleStatus = computed(() => (
    resolveEventLifecycleStatus(event.value, eventTimeStatus.value) || 'upcoming'
  ))
  const actionState = computed(() => resolveAttendanceActionState({
    event: event.value,
    eventStatus: lifecycleStatus.value,
    attendanceRecord: latestAttendanceRecord.value,
    timeStatus: eventTimeStatus.value,
    now: now.value,
  }))
  const actionKind = computed(() => resolveActionKind(actionState.value, latestAttendanceRecord.value))
  const actionLabel = computed(() => resolveActionLabel(actionKind.value))
  const actionTone = computed(() => resolveActionTone(actionState.value))
  const canSubmit = computed(() => actionState.value === 'sign-in' || actionState.value === 'sign-out')
  const cameraReady = computed(() => (
    cameraState.value === 'ready' && backgroundVideoReady.value && focusVideoReady.value
  ))
  const locationReady = computed(() => (
    Number.isFinite(Number(userCoords.value?.latitude))
    && Number.isFinite(Number(userCoords.value?.longitude))
  ))
  const currentTimeLabel = computed(() => clockFormatter.format(now.value))
  const faceImageUrl = computed(() => (
    activeUser.value?.student_profile?.photo_url
    || activeUser.value?.student_profile?.avatar_url
    || activeUser.value?.avatar_url
    || ''
  ))
  const eventGeo = computed(() => resolveEventGeo(event.value))
  const checkedInLabel = computed(() => formatAttendanceTimestamp(latestAttendanceRecord.value?.time_in))
  const checkedOutLabel = computed(() => formatAttendanceTimestamp(latestAttendanceRecord.value?.time_out))
  const distanceLabel = computed(() => {
    const verifiedDistance =
      Number(locationCheck.value?.effective_distance_m ?? locationCheck.value?.distance_m)

    if (Number.isFinite(verifiedDistance)) {
      return formatVenueDistance(verifiedDistance)
    }

    const computedDistance = measureDistanceMeters(userCoords.value, {
      latitude: eventGeo.value.latitude,
      longitude: eventGeo.value.longitude,
    })

    return formatVenueDistance(computedDistance)
  })
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

    return {
      tone: 'neutral',
      icon: 'shield',
      message: resolveLiveStatusMessage({
        cameraReady: cameraReady.value,
        faceDetected: faceDetected.value,
        locationReady: locationReady.value,
        actionLabel: actionLabel.value,
      }),
    }
  })
  const submitButtonLabel = computed(() => (
    isSubmitting.value ? `${actionLabel.value}...` : actionLabel.value
  ))
  const actionHint = computed(() => {
    if (actionState.value === 'waiting-sign-out') {
      const remainingMs = getMillisecondsUntilSignOutOpen({
        event: event.value,
        timeStatus: eventTimeStatus.value,
      })
      return Number.isFinite(remainingMs) && remainingMs > 0
        ? `Available in ${formatCompactDuration(remainingMs)}`
        : 'Waiting for sign-out window'
    }

    if (actionState.value === 'done') {
      return 'Attendance completed'
    }

    if (actionState.value === 'closed') {
      return 'Attendance closed'
    }

    if (actionState.value === 'missed-check-in') {
      return 'Check-in window missed'
    }

    if (actionState.value === 'not-open') {
      return 'Not open yet'
    }

    if (distanceLabel.value) {
      return distanceLabel.value
    }

    return ''
  })

  usePreviewTheme(preview, activeSchoolSettings)

  function setBackgroundVideoRef(el) {
    backgroundVideoEl.value = el
  }

  function setFocusVideoRef(el) {
    focusVideoEl.value = el
  }

  function clearTransientState() {
    latestError.value = null
    latestSuccess.value = null
    latestNotice.value = null
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
      // Ignore autoplay failures. The stream stays attached and will render once allowed.
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
          || 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.32/wasm',
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

  function stopFaceDetection() {
    if (faceDetectRaf) cancelAnimationFrame(faceDetectRaf)
    faceDetectRaf = null
    faceDetected.value = false
  }

  async function startFaceDetection() {
    if (!cameraReady.value || !focusVideoEl.value) return

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
      if (!focusVideoEl.value || !cameraReady.value) return

      if (nowMs - lastDetectAt < detectIntervalMs) {
        faceDetectRaf = requestAnimationFrame(loop)
        return
      }

      lastDetectAt = nowMs
      try {
        const result = faceDetectorInstance.detectForVideo(focusVideoEl.value, nowMs)
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

  async function loadEventTimeStatus() {
    if (preview.value) {
      eventTimeStatus.value = null
      return null
    }

    const normalizedEventId = eventId.value
    if (!Number.isFinite(normalizedEventId)) {
      eventTimeStatus.value = null
      return null
    }

    const token = localStorage.getItem('aura_token')
    if (!token) {
      eventTimeStatus.value = null
      return null
    }

    try {
      eventTimeStatus.value = await getEventTimeStatus(apiBaseUrl, token, normalizedEventId)
    } catch {
      eventTimeStatus.value = null
    }

    return eventTimeStatus.value
  }

  async function refreshAttendanceContext() {
    const normalizedEventId = eventId.value
    if (!Number.isFinite(normalizedEventId)) {
      return {
        attendanceRecord: latestAttendanceRecord.value,
        timeStatus: eventTimeStatus.value,
      }
    }

    if (preview.value) {
      return {
        attendanceRecord: pickLatestAttendanceRecord(previewAttendanceRecords.value, normalizedEventId),
        timeStatus: eventTimeStatus.value,
      }
    }

    await Promise.allSettled([
      refreshAttendanceRecords({ event_id: normalizedEventId }),
      loadEventTimeStatus(),
    ])

    return {
      attendanceRecord: getLatestAttendanceForEvent(normalizedEventId),
      timeStatus: eventTimeStatus.value,
    }
  }

  async function refreshLocationLabel(coords, preferredLabel = '') {
    const latitude = Number(coords?.latitude)
    const longitude = Number(coords?.longitude)
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      currentLocationLabel.value = 'Current location unavailable'
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

  async function resolveCurrentPosition({ precise = false, silent = false } = {}) {
    if (!silent) {
      loadingMessage.value = 'Checking current location...'
    }
    isResolvingLocation.value = true
    currentLocationError.value = ''

    try {
      const desiredAccuracy = Number(event.value?.geo_max_accuracy_m)
      const coords = precise && event.value?.geo_required
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
      if (!userCoords.value) {
        currentLocationLabel.value = 'Current location unavailable'
      }
      throw error
    } finally {
      isResolvingLocation.value = false
      if (!silent && !isSubmitting.value) {
        loadingMessage.value = ''
      }
    }
  }

  async function verifyCurrentLocation(coords) {
    if (!event.value?.geo_required) {
      locationCheck.value = {
        ok: true,
        accuracy_m: coords?.accuracy ?? null,
      }
      return locationCheck.value
    }

    if (preview.value) {
      const measuredDistance = measureDistanceMeters(coords, {
        latitude: eventGeo.value.latitude,
        longitude: eventGeo.value.longitude,
      })
      locationCheck.value = {
        ok: true,
        distance_m: measuredDistance,
        radius_m: eventGeo.value.radiusM,
        accuracy_m: coords?.accuracy ?? null,
      }
      return locationCheck.value
    }

    const token = localStorage.getItem('aura_token')
    if (!token) {
      throw new Error('Your session has expired. Please sign in again.')
    }

    const verification = await verifyEventLocation(apiBaseUrl, token, eventId.value, {
      latitude: coords.latitude,
      longitude: coords.longitude,
      accuracy_m: coords.accuracy ?? null,
    })

    locationCheck.value = verification
    if (verification?.time_status) {
      eventTimeStatus.value = verification.time_status
    }

    if (!verification?.ok) {
      throw new Error(buildAttendanceLocationErrorMessage(verification))
    }

    return verification
  }

  function captureVideoFrame() {
    const element = focusVideoEl.value || backgroundVideoEl.value
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
    return canvas.toDataURL('image/jpeg', 0.92)
  }

  function upsertPreviewAttendanceRecord(record) {
    const normalizedRecord = normalizeAttendanceRecord(record)
    const normalizedEventId = Number(normalizedRecord?.event_id)
    if (!Number.isFinite(normalizedEventId)) {
      return normalizedRecord
    }

    const nextRecords = [
      ...previewAttendanceRecords.value.filter((item) => Number(item?.event_id) !== normalizedEventId),
      normalizedRecord,
    ]

    previewAttendanceRecords.value = nextRecords
    studentDashboardPreviewData.attendanceRecords = nextRecords.map((item) => ({ ...item }))
    return normalizedRecord
  }

  async function recordAttendance(imageDataUrl, coords) {
    const normalizedEventId = eventId.value
    if (!Number.isFinite(normalizedEventId)) {
      throw new Error('Event information is missing. Please go back and try again.')
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
        timeStatus: eventTimeStatus.value,
      }
    }

    const token = localStorage.getItem('aura_token')
    if (!token) {
      throw new Error('Your session has expired. Please sign in again.')
    }

    const rawBase64 = imageDataUrl.includes(',') ? imageDataUrl.split(',')[1] : imageDataUrl
    const payload = {
      eventId: normalizedEventId,
      studentId: studentId != null ? String(studentId) : '',
      imageBase64: imageDataUrl,
      latitude: coords?.latitude ?? null,
      longitude: coords?.longitude ?? null,
      accuracyM: coords?.accuracy ?? null,
    }

    let result = null
    try {
      result = await postFaceScanAttendance(apiBaseUrl, token, payload)
    } catch {
      result = await postFaceScanAttendance(apiBaseUrl, token, {
        ...payload,
        imageBase64: rawBase64,
      })
    }

    if (result && !result.ok) {
      throw new Error(result.message || 'Cannot verify face right now.')
    }

    if (result?.geo?.time_status) {
      eventTimeStatus.value = result.geo.time_status
    }
    if (result?.geo) {
      locationCheck.value = result.geo
    }

    let attendanceContext = {
      attendanceRecord: getLatestAttendanceForEvent(normalizedEventId),
      timeStatus: eventTimeStatus.value,
    }

    try {
      attendanceContext = await refreshAttendanceContext()
    } catch {
      // Keep the successful scan result even when the follow-up refresh fails.
    }

    const optimisticRecord = buildOptimisticAttendanceRecord({
      result,
      existingAttendanceRecord: attendanceContext.attendanceRecord || latestAttendanceRecord.value,
      eventId: normalizedEventId,
      studentId,
    })

    if (optimisticRecord) {
      upsertAttendanceRecordSnapshot(optimisticRecord)
      attendanceContext = {
        ...attendanceContext,
        attendanceRecord:
          resolveAttendanceCompletionState(attendanceContext.attendanceRecord) === 'completed'
            ? attendanceContext.attendanceRecord
            : optimisticRecord,
      }
    }

    return {
      result,
      attendanceRecord: attendanceContext.attendanceRecord,
      timeStatus: attendanceContext.timeStatus,
    }
  }

  async function refreshEventStatusPolling() {
    if (preview.value) return

    const nextRequestId = requestId.value + 1
    requestId.value = nextRequestId
    await loadEventTimeStatus()
    if (requestId.value !== nextRequestId) return
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
      void refreshEventStatusPolling()
    }, 15000)
  }

  function stopEventStatusPolling() {
    if (eventTimeStatusIntervalId != null) {
      clearInterval(eventTimeStatusIntervalId)
      eventTimeStatusIntervalId = null
    }
  }

  async function goBack() {
    if (hasNavigableHistory(route)) {
      router.back()
      return
    }

    router.push(resolveBackFallbackLocation(route, { eventId: eventId.value }))
  }

  async function handleSubmit() {
    if (!event.value || isSubmitting.value) return

    clearTransientState()
    const currentState = actionState.value
    if (!canSubmit.value) {
      latestNotice.value = resolveBlockedStateModel(
        currentState,
        actionLabel.value,
        event.value,
        eventTimeStatus.value,
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

      if (!faceDetected.value) {
        throw new Error('Cannot verify face. Center your face inside the frame and try again.')
      }

      loadingMessage.value = 'Checking current location...'
      const coords = await resolveCurrentPosition({ precise: true })

      loadingMessage.value = 'Verifying location...'
      await verifyCurrentLocation(coords)

      loadingMessage.value = `${actionLabel.value}...`
      const imageDataUrl = captureVideoFrame()
      await recordAttendance(imageDataUrl, coords)
      await refreshAttendanceContext().catch(() => null)

      latestSuccess.value = {
        message: 'Identity and location verified',
      }
      currentLocationError.value = ''
    } catch (error) {
      latestError.value = {
        message: resolveLocationErrorMessage(
          error,
          `Unable to complete ${actionLabel.value.toLowerCase()} right now.`,
        ),
      }
    } finally {
      loadingMessage.value = ''
      isSubmitting.value = false
    }
  }

  async function initialize() {
    isInitializing.value = true

    if (!preview.value) {
      await ensureDashboardEvent(eventId.value).catch(() => null)
    }

    await Promise.allSettled([
      refreshAttendanceContext(),
      startCamera(),
      resolveCurrentPosition({ precise: false, silent: true }),
    ])

    await startFaceDetection()
    startEventStatusPolling()
    isInitializing.value = false
  }

  watch(
    () => [backgroundVideoEl.value, focusVideoEl.value, mediaStream.value],
    ([backgroundEl, focusEl, stream]) => {
      if (backgroundEl && focusEl && stream) {
        void attachStreamToVideos()
      }
    },
    { flush: 'post' }
  )

  watch(
    () => cameraReady.value,
    (ready) => {
      if (ready) {
        void startFaceDetection()
      } else {
        stopFaceDetection()
      }
    }
  )

  watch(
    () => eventId.value,
    () => {
      clearTransientState()
      locationCheck.value = null
      currentLocationError.value = ''
      void initialize()
    }
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
    actionLabel,
    actionState,
    actionTone,
    cameraReady,
    canSubmit,
    checkedInLabel,
    checkedOutLabel,
    currentLocationLabel,
    currentTimeLabel,
    distanceLabel,
    event,
    eventTimeStatus,
    faceDetected,
    faceImageUrl,
    goBack,
    handleSubmit,
    isInitializing,
    isResolvingLocation,
    isSubmitting,
    locationReady,
    setBackgroundVideoRef,
    setFocusVideoRef,
    statusModel,
    submitButtonLabel,
  }
}
