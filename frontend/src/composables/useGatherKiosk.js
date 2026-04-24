import { computed, onBeforeUnmount, onMounted, ref, unref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { studentDashboardPreviewData } from '@/data/studentDashboardPreview.js'
import {
  getCurrentPositionOrThrow,
  getCurrentPositionWithinAccuracyOrThrow,
  isNativeApp,
  requestCameraPermission,
} from '@/services/devicePermissions.js'
import {
  describePublicAttendanceError,
  fetchNearbyPublicAttendanceEvents,
  resolvePublicAttendanceRetryAfterMs,
  submitPublicAttendanceScan,
} from '@/services/publicAttendance.js'
import {
  isGovernanceWorkspaceContext,
  resolveWorkspaceHomeLocation,
} from '@/services/routeWorkspace.js'
import { notifyAttendanceMarked } from '@/services/localNotifications.js'

const dateTimeFormatter = new Intl.DateTimeFormat('en-PH', {
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
})

const timeFormatter = new Intl.DateTimeFormat('en-PH', {
  hour: 'numeric',
  minute: '2-digit',
})

const previewDefaultCoordinates = {
  latitude: 8.1552,
  longitude: 123.8421,
}
const rawGatherDiscoveryDesiredAccuracyM = Number(import.meta.env.VITE_GATHER_DISCOVERY_ACCURACY_M ?? 45)
const gatherDiscoveryDesiredAccuracyM = Number.isFinite(rawGatherDiscoveryDesiredAccuracyM) && rawGatherDiscoveryDesiredAccuracyM > 0
  ? rawGatherDiscoveryDesiredAccuracyM
  : 45
const rawGatherDiscoveryTimeoutMs = Number(import.meta.env.VITE_GEOLOCATION_TIMEOUT_MS ?? 18000)
const gatherDiscoveryTimeoutMs = Number.isFinite(rawGatherDiscoveryTimeoutMs) && rawGatherDiscoveryTimeoutMs > 0
  ? Math.max(rawGatherDiscoveryTimeoutMs, 18000)
  : 18000

const COOLDOWN_ACTIONS = new Set([
  'time_in',
  'time_out',
  'already_signed_in',
  'already_signed_out',
  'cooldown_skipped',
])

function resolvePreviewFlag(source) {
  return Boolean(unref(typeof source === 'function' ? source() : source))
}

function toFullName(user = null) {
  const parts = [user?.first_name, user?.last_name]
    .map((value) => String(value || '').trim())
    .filter(Boolean)

  return parts.join(' ') || 'Preview Attendee'
}

function formatDateTime(value) {
  if (!value) return 'Time TBA'

  try {
    return dateTimeFormatter.format(new Date(value))
  } catch {
    return 'Time TBA'
  }
}

function formatTime(value) {
  if (!value) return 'Time TBA'

  try {
    return timeFormatter.format(new Date(value))
  } catch {
    return 'Time TBA'
  }
}

function formatDistance(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return 'N/A'
  return `${normalized.toFixed(normalized < 10 ? 1 : 0)} m`
}

function formatPhaseLabel(phase) {
  return String(phase || '').trim().toLowerCase() === 'sign_out'
    ? 'Check Out'
    : 'Check In'
}

function outcomeTone(action) {
  const normalized = String(action || '').trim().toLowerCase()
  if (normalized === 'time_in' || normalized === 'time_out') return 'success'
  if (['liveness_failed', 'out_of_scope', 'no_match', 'rejected'].includes(normalized)) return 'error'
  return 'info'
}

function primaryOutcomeMessage(responseOutcomes, fallback) {
  const preferred = (Array.isArray(responseOutcomes) ? responseOutcomes : []).find((outcome) =>
    ['time_in', 'time_out'].includes(String(outcome?.action || '').trim().toLowerCase())
  )

  return preferred?.message || responseOutcomes?.[0]?.message || fallback || 'Gather scan finished.'
}

function toneFromOutcomes(responseOutcomes) {
  if ((responseOutcomes || []).some((outcome) => outcomeTone(outcome?.action) === 'success')) {
    return 'success'
  }

  if ((responseOutcomes || []).some((outcome) => outcomeTone(outcome?.action) === 'error')) {
    return 'error'
  }

  return 'info'
}

function normalizeHistoryActionLabel(action) {
  const normalized = String(action || '').trim().toLowerCase()

  if (normalized === 'time_in' || normalized === 'already_signed_in') return 'Checked In'
  if (normalized === 'time_out' || normalized === 'already_signed_out') return 'Checked Out'
  if (normalized === 'cooldown_skipped') return 'On Cooldown'

  return normalized
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function isHistoryOutcome(outcome = null) {
  const normalizedAction = String(outcome?.action || '').trim().toLowerCase()

  if (!outcome?.student_id && !outcome?.student_name) {
    return false
  }

  return !['no_match', 'rejected', 'liveness_failed'].includes(normalizedAction)
}

function parseDateValue(value) {
  const timestamp = new Date(value || '').getTime()
  return Number.isFinite(timestamp) ? timestamp : null
}

function buildPreviewEvents(events = [], schoolName = 'Campus') {
  const now = Date.now()

  return [...events]
    .filter((event) => Number.isFinite(Number(event?.id)))
    .filter((event) => {
      const endAt = parseDateValue(event?.end_datetime)
      return endAt == null || endAt >= now
    })
    .sort((left, right) => {
      const leftStart = parseDateValue(left?.start_datetime) ?? Number.MAX_SAFE_INTEGER
      const rightStart = parseDateValue(right?.start_datetime) ?? Number.MAX_SAFE_INTEGER

      const leftIsOngoing = leftStart <= now
      const rightIsOngoing = rightStart <= now
      if (leftIsOngoing !== rightIsOngoing) return leftIsOngoing ? -1 : 1

      return leftStart - rightStart
    })
    .map((event, index) => {
      const startAt = parseDateValue(event?.start_datetime)
      const endAt = parseDateValue(event?.end_datetime)
      const isOngoing = startAt != null && startAt <= now && (endAt == null || endAt > now)
      const phaseMessage = isOngoing
        ? `${event?.name || 'This event'} is open for Gather capture.`
        : `${event?.name || 'This event'} opens at ${formatDateTime(event?.start_datetime)}.`

      return {
        id: Number(event.id),
        school_id: Number(event.school_id || 0),
        school_name: schoolName,
        name: String(event?.name || 'Untitled Event').trim() || 'Untitled Event',
        location: String(event?.location || 'Campus').trim() || 'Campus',
        start_datetime: event?.start_datetime || null,
        end_datetime: event?.end_datetime || null,
        distance_m: 18 + (index * 12),
        attendance_phase: 'sign_in',
        phase_message: phaseMessage,
        scope_label: String(event?.scope_label || event?.unit_name || schoolName).trim() || schoolName,
      }
    })
}

function resolvePreviewLocation(events = []) {
  const eventWithGeo = events.find((event) => (
    Number.isFinite(Number(event?.geo_latitude))
    && Number.isFinite(Number(event?.geo_longitude))
  ))

  return {
    latitude: Number(eventWithGeo?.geo_latitude) || previewDefaultCoordinates.latitude,
    longitude: Number(eventWithGeo?.geo_longitude) || previewDefaultCoordinates.longitude,
    accuracyM: 12,
    resolvedAt: new Date().toISOString(),
  }
}

async function waitForVideoReady(video) {
  if (!video) {
    throw new Error('Camera preview is not ready yet.')
  }

  if (video.readyState >= HTMLMediaElement.HAVE_METADATA) {
    return
  }

  await new Promise((resolve, reject) => {
    const handleLoaded = () => {
      cleanup()
      resolve()
    }

    const handleError = () => {
      cleanup()
      reject(new Error('Camera stream metadata failed to load.'))
    }

    const cleanup = () => {
      video.removeEventListener('loadedmetadata', handleLoaded)
      video.removeEventListener('error', handleError)
    }

    video.addEventListener('loadedmetadata', handleLoaded)
    video.addEventListener('error', handleError)
  })
}

function humanizeCameraError(error) {
  if (error instanceof DOMException) {
    if (error.name === 'NotAllowedError') {
      return 'Camera permission was denied. Allow camera access to continue.'
    }

    if (error.name === 'NotFoundError') {
      return 'No camera device was found on this device.'
    }

    if (error.name === 'NotReadableError') {
      return 'Camera is already in use by another app or browser tab.'
    }
  }

  return error instanceof Error ? error.message : 'Unable to access the camera.'
}

export function useGatherKiosk(previewSource = false) {
  const route = useRoute()
  const router = useRouter()
  const preview = computed(() => resolvePreviewFlag(previewSource))
  const { previewBundle } = useSgPreviewBundle(preview)

  const videoEl = ref(null)
  const canvasEl = ref(null)
  const location = ref(null)
  const locationMessage = ref('Share your location to load nearby Gather events.')
  const isRefreshingLocation = ref(false)
  const nearbyEvents = ref([])
  const selectedEventId = ref(null)
  const scanMode = ref('automatic')
  const scanCooldownSeconds = ref(8)
  const cameraOn = ref(false)
  const isCameraStarting = ref(false)
  const preferredFacingMode = ref('environment')
  const activeFacingMode = ref('environment')
  const torchSupported = ref(false)
  const torchEnabled = ref(false)
  const scanBusy = ref(false)
  const statusMessage = ref('Gather is preparing your camera and nearby attendance events.')
  const statusTone = ref('info')
  const outcomes = ref([])
  const lastScanAt = ref('')
  const attendanceHistory = ref([])

  let mediaStream = null
  let scanTimeoutId = 0
  let cooldownByStudent = {}
  let historySequence = 0

  const previewSeed = computed(() => {
    if (!preview.value) return null

    if (isGovernanceWorkspaceContext(route)) {
      return {
        user: previewBundle.value?.user ?? studentDashboardPreviewData.user,
        schoolName:
          previewBundle.value?.schoolSettings?.school_name
          || previewBundle.value?.user?.school_name
          || studentDashboardPreviewData.schoolSettings.school_name,
        events: Array.isArray(previewBundle.value?.events)
          ? previewBundle.value.events
          : studentDashboardPreviewData.events,
      }
    }

    return {
      user: studentDashboardPreviewData.user,
      schoolName:
        studentDashboardPreviewData.schoolSettings.school_name
        || studentDashboardPreviewData.user?.school_name
        || 'Campus',
      events: studentDashboardPreviewData.events,
    }
  })

  const hasEvents = computed(() => nearbyEvents.value.length > 0)
  const selectedEvent = computed(() => (
    nearbyEvents.value.find((event) => Number(event.id) === Number(selectedEventId.value)) || null
  ))
  const selectedEventPhaseLabel = computed(() => formatPhaseLabel(selectedEvent.value?.attendance_phase))
  const locationPillLabel = computed(() => (
    location.value ? `GPS ${formatDistance(location.value.accuracyM)}` : 'Share location'
  ))
  const selectedEventMeta = computed(() => {
    if (!selectedEvent.value) {
      return 'Choose an attendance event after location is ready.'
    }

    const distance = formatDistance(selectedEvent.value.distance_m)
    const time = formatTime(selectedEvent.value.start_datetime)
    return `${selectedEvent.value.location} · ${time} · ${distance}`
  })
  const canCapture = computed(() => (
    Boolean(location.value && selectedEvent.value && cameraOn.value)
    && !scanBusy.value
    && !isCameraStarting.value
  ))
  const hasAttendanceHistory = computed(() => attendanceHistory.value.length > 0)
  const isAutomaticMode = computed(() => scanMode.value === 'automatic')
  const cameraFacingLabel = computed(() => (
    String(activeFacingMode.value || preferredFacingMode.value).trim().toLowerCase() === 'user'
      ? 'Front'
      : 'Rear'
  ))
  const needsEventSelection = computed(() => hasEvents.value && !selectedEvent.value)
  const isDiscoveringNearbyEvents = computed(() => isRefreshingLocation.value && !location.value && !hasEvents.value)

  function syncStatusMessage() {
    if (scanBusy.value) {
      statusMessage.value = 'Processing this Gather capture...'
      statusTone.value = 'info'
      return
    }

    if (!location.value) {
      statusMessage.value = locationMessage.value
      statusTone.value = 'info'
      return
    }

    if (!hasEvents.value) {
      statusMessage.value = 'No nearby Gather events are open right now.'
      statusTone.value = 'info'
      return
    }

    if (!selectedEvent.value) {
      statusMessage.value = 'Choose a nearby Gather event to open the camera kiosk.'
      statusTone.value = 'info'
      return
    }

    if (!cameraOn.value) {
      statusMessage.value = 'Camera access is needed before you can capture attendance.'
      statusTone.value = 'info'
      return
    }

    statusMessage.value = isAutomaticMode.value
      ? `${selectedEvent.value?.name || 'This event'} is live in automatic mode. Keep faces inside the camera frame.`
      : (
        selectedEvent.value?.phase_message
        || `${selectedEvent.value?.name || 'This event'} is ready for ${selectedEventPhaseLabel.value.toLowerCase()}.`
      )
    statusTone.value = 'info'
  }

  function selectEvent(eventId) {
    const normalizedEventId = Number(eventId)
    if (!Number.isFinite(normalizedEventId)) return

    selectedEventId.value = normalizedEventId
    outcomes.value = []
    lastScanAt.value = ''
    syncStatusMessage()
  }

  function appendAttendanceHistory(event, responseOutcomes = [], recordedAt = new Date().toISOString()) {
    const nextEntries = (Array.isArray(responseOutcomes) ? responseOutcomes : [])
      .filter(isHistoryOutcome)
      .map((outcome) => {
        historySequence += 1

        return {
          id: `gather-history-${historySequence}`,
          studentId: outcome?.student_id || null,
          studentName: outcome?.student_name || 'Unknown Student',
          action: outcome?.action || 'recorded',
          actionLabel: normalizeHistoryActionLabel(outcome?.action),
          eventId: Number(event?.id || 0) || null,
          eventName: event?.name || 'Gather Event',
          eventLocation: event?.location || '',
          recordedAt: outcome?.time_out || outcome?.time_in || recordedAt,
          message: outcome?.message || 'Attendance was recorded.',
        }
      })

    if (!nextEntries.length) return

    attendanceHistory.value = [...nextEntries, ...attendanceHistory.value].slice(0, 60)
  }

  function setScanMode(nextMode) {
    const normalizedMode = String(nextMode || '').trim().toLowerCase()
    if (!['automatic', 'manual'].includes(normalizedMode)) return
    if (scanMode.value === normalizedMode) return

    scanMode.value = normalizedMode
    syncStatusMessage()
  }

  async function activateEvent(eventId, options = {}) {
    selectEvent(eventId)

    if (!selectedEvent.value) {
      return
    }

    if (options?.startCamera === false) {
      syncStatusMessage()
      return
    }

    if (!cameraOn.value) {
      await startCamera()
    } else {
      syncStatusMessage()
    }
  }

  function getActiveVideoTrack() {
    return mediaStream?.getVideoTracks?.()?.[0] || null
  }

  function stopScanLoop() {
    if (scanTimeoutId) {
      window.clearTimeout(scanTimeoutId)
      scanTimeoutId = 0
    }
  }

  function syncCooldownStudentIds() {
    const now = Date.now()
    const activeEntries = Object.values(cooldownByStudent)
      .filter((entry) => Number(entry?.expiresAt) > now)
      .sort((left, right) => Number(left.expiresAt) - Number(right.expiresAt))

    cooldownByStudent = Object.fromEntries(activeEntries.map((entry) => [entry.studentId, entry]))
    return activeEntries.map((entry) => entry.studentId)
  }

  async function applyTorchState(nextState) {
    const track = getActiveVideoTrack()
    if (!track?.applyConstraints || !torchSupported.value) {
      torchEnabled.value = false
      return false
    }

    try {
      await track.applyConstraints({
        advanced: [{ torch: Boolean(nextState) }],
      })
      torchEnabled.value = Boolean(nextState)
      return true
    } catch {
      torchEnabled.value = false
      return false
    }
  }

  function syncCameraCapabilities(stream) {
    const track = stream?.getVideoTracks?.()?.[0] || null
    if (!track) {
      activeFacingMode.value = preferredFacingMode.value
      torchSupported.value = false
      torchEnabled.value = false
      return
    }

    const settings = typeof track.getSettings === 'function' ? track.getSettings() : {}
    const capabilities = typeof track.getCapabilities === 'function' ? track.getCapabilities() : {}

    activeFacingMode.value = String(settings?.facingMode || preferredFacingMode.value || 'environment').trim().toLowerCase()
    torchSupported.value = Boolean(capabilities?.torch)

    if (!torchSupported.value) {
      torchEnabled.value = false
    }
  }

  function buildCameraConstraintCandidates(facingMode) {
    const resolvedFacingMode = String(facingMode || 'environment').trim().toLowerCase() === 'user'
      ? 'user'
      : 'environment'

    const baseVideo = {
      width: { ideal: 1440 },
      height: { ideal: 1920 },
      aspectRatio: { ideal: 3 / 4 },
    }

    return [
      {
        audio: false,
        video: {
          ...baseVideo,
          facingMode: { exact: resolvedFacingMode },
        },
      },
      {
        audio: false,
        video: {
          ...baseVideo,
          facingMode: { ideal: resolvedFacingMode },
        },
      },
      {
        audio: false,
        video: {
          ...baseVideo,
        },
      },
    ]
  }

  async function openCameraStream(facingMode) {
    let lastError = null

    for (const constraints of buildCameraConstraintCandidates(facingMode)) {
      try {
        return await navigator.mediaDevices.getUserMedia(constraints)
      } catch (error) {
        lastError = error
      }
    }

    throw lastError || new Error('Unable to open the requested camera.')
  }

  async function loadNearbyEvents(options = {}) {
    const silent = Boolean(options?.silent)
    const resetSelection = Boolean(options?.resetSelection)
    const clearResults = Boolean(options?.clearResults)

    isRefreshingLocation.value = true

    if (clearResults) {
      outcomes.value = []
      lastScanAt.value = ''
    }

    if (resetSelection) {
      selectedEventId.value = null
    }

    if (!silent) {
      statusMessage.value = 'Looking for nearby Gather events...'
      statusTone.value = 'info'
    }

    try {
      if (preview.value) {
        const previewEvents = buildPreviewEvents(
          previewSeed.value?.events ?? [],
          previewSeed.value?.schoolName ?? 'Campus',
        )
        const previewLocation = resolvePreviewLocation(previewSeed.value?.events ?? [])

        location.value = previewLocation
        locationMessage.value = `Preview location ready at ${formatDateTime(previewLocation.resolvedAt)}.`
        nearbyEvents.value = previewEvents
        selectedEventId.value = previewEvents.some((event) => Number(event.id) === Number(selectedEventId.value))
          ? selectedEventId.value
          : null

        if (!previewEvents.length && !silent) {
          statusMessage.value = 'No preview Gather events are available right now.'
          statusTone.value = 'info'
        }

        if (previewEvents.length && !silent) {
          syncStatusMessage()
        }

        return
      }

      const position = await (
        isNativeApp()
          ? getCurrentPositionWithinAccuracyOrThrow({
              desiredAccuracy: gatherDiscoveryDesiredAccuracyM,
              enableHighAccuracy: true,
              timeout: gatherDiscoveryTimeoutMs,
              maximumAge: 0,
              onAccuracyUpdate: (accuracy) => {
                if (silent || !Number.isFinite(Number(accuracy)) || Number(accuracy) <= 0) return
                statusMessage.value = `Improving GPS accuracy... currently ${formatDistance(accuracy)}.`
                statusTone.value = 'info'
              },
            })
          : getCurrentPositionOrThrow({
              enableHighAccuracy: true,
              timeout: 12000,
              maximumAge: 0,
            })
      )

      const resolvedLocation = {
        latitude: position.latitude,
        longitude: position.longitude,
        accuracyM: position.accuracy,
        resolvedAt: position.capturedAt || new Date().toISOString(),
      }

      const response = await fetchNearbyPublicAttendanceEvents(resolvedLocation)

      location.value = resolvedLocation
      locationMessage.value = `Location updated at ${formatDateTime(resolvedLocation.resolvedAt)} with ${formatDistance(resolvedLocation.accuracyM)} accuracy.`
      nearbyEvents.value = response.events
      scanCooldownSeconds.value = response.scan_cooldown_seconds
      selectedEventId.value = response.events.some((event) => Number(event.id) === Number(selectedEventId.value))
        ? selectedEventId.value
        : null

      if (!response.events.length && !silent) {
        statusMessage.value = 'No nearby Gather events are open right now.'
        statusTone.value = 'info'
      }

      if (response.events.length && !silent) {
        syncStatusMessage()
      }
    } catch (error) {
      location.value = null
      nearbyEvents.value = []
      selectedEventId.value = null
      locationMessage.value = describePublicAttendanceError(error)

      if (!silent) {
        statusMessage.value = locationMessage.value
        statusTone.value = 'error'
      }
    } finally {
      isRefreshingLocation.value = false
    }
  }

  async function refreshGatherContext() {
    stopCamera()
    await loadNearbyEvents({
      clearResults: true,
      resetSelection: true,
    })
  }

  async function startCamera(options = {}) {
    const silent = Boolean(options?.silent)
    const force = Boolean(options?.force)

    if ((mediaStream && !force) || isCameraStarting.value) {
      return
    }

    isCameraStarting.value = true

    try {
      if (force) {
        stopCamera()
      }

      const permission = await requestCameraPermission()
      if (!permission.granted) {
        throw new Error(permission.message || 'Camera permission was denied. Allow camera access to continue.')
      }

      if (!navigator?.mediaDevices?.getUserMedia) {
        throw new Error('Camera access is not supported on this browser.')
      }

      const stream = await openCameraStream(preferredFacingMode.value)

      mediaStream = stream
      syncCameraCapabilities(stream)

      if (videoEl.value) {
        videoEl.value.srcObject = stream
        await waitForVideoReady(videoEl.value)
        await videoEl.value.play().catch(() => null)
      }

      cameraOn.value = true

      if (torchEnabled.value && torchSupported.value) {
        await applyTorchState(true)
      }

      if (!silent) {
        syncStatusMessage()
      }
    } catch (error) {
      cameraOn.value = false

      if (!silent) {
        statusMessage.value = humanizeCameraError(error)
        statusTone.value = 'error'
      }
    } finally {
      isCameraStarting.value = false
    }
  }

  function stopCamera() {
    stopScanLoop()
    torchEnabled.value = false
    torchSupported.value = false

    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop())
      mediaStream = null
    }

    if (videoEl.value) {
      videoEl.value.srcObject = null
    }

    cameraOn.value = false
  }

  async function toggleCameraFacing() {
    preferredFacingMode.value = preferredFacingMode.value === 'environment' ? 'user' : 'environment'
    torchEnabled.value = false

    if (!cameraOn.value) {
      activeFacingMode.value = preferredFacingMode.value
      syncStatusMessage()
      return
    }

    try {
      await startCamera({ force: true })
      statusMessage.value = `${cameraFacingLabel.value} camera is live.`
      statusTone.value = 'info'
    } catch (error) {
      statusMessage.value = humanizeCameraError(error)
      statusTone.value = 'error'
    }
  }

  async function toggleTorch() {
    if (!torchSupported.value || isCameraStarting.value || !cameraOn.value) {
      return
    }

    const nextState = !torchEnabled.value
    const applied = await applyTorchState(nextState)

    if (!applied) {
      statusMessage.value = 'Flash is not available on this camera.'
      statusTone.value = 'info'
      return
    }

    statusMessage.value = nextState ? 'Flash turned on.' : 'Flash turned off.'
    statusTone.value = 'info'
  }

  async function captureFrameBlob() {
    const video = videoEl.value
    const canvas = canvasEl.value

    if (!video || !canvas || video.videoWidth <= 0 || video.videoHeight <= 0) {
      throw new Error('Camera preview is not ready yet.')
    }

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('Failed to prepare the camera frame.')
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height)

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
        0.9,
      )
    })
  }

  async function submitPreviewCapture(event) {
    const attendeeName = toFullName(previewSeed.value?.user)

    return {
      message: `Preview capture processed for ${event?.name || 'Gather'}.`,
      scan_cooldown_seconds: scanCooldownSeconds.value,
      outcomes: [
        {
          action: 'time_in',
          student_id: previewSeed.value?.user?.student_profile?.student_id || 'PREVIEW-001',
          student_name: attendeeName,
          message: `${attendeeName} was marked present in preview mode.`,
          confidence: 0.986,
          distance: Number(event?.distance_m) || 12,
          liveness: {
            label: 'Live',
            score: 0.998,
          },
          time_in: new Date().toISOString(),
          time_out: null,
        },
      ],
    }
  }

  async function processCapture(options = {}) {
    const automatic = Boolean(options?.automatic)

    if (scanBusy.value) return

    if (!location.value) {
      await loadNearbyEvents()
    }

    if (!cameraOn.value) {
      await startCamera()
    }

    if (!location.value || !cameraOn.value || !selectedEvent.value) {
      syncStatusMessage()
      return
    }

    const activeEvent = selectedEvent.value
    scanBusy.value = true
    syncStatusMessage()

    try {
      const frameBlob = await captureFrameBlob()
      const response = preview.value
        ? await submitPreviewCapture(activeEvent, frameBlob)
        : await submitPublicAttendanceScan({
          eventId: activeEvent.id,
          imageBlob: frameBlob,
          location: location.value,
          cooldownStudentIds: automatic ? syncCooldownStudentIds() : [],
        })

      const responseCooldown = Number(response?.scan_cooldown_seconds)
      if (Number.isFinite(responseCooldown) && responseCooldown >= 0) {
        scanCooldownSeconds.value = responseCooldown
      }

      outcomes.value = Array.isArray(response.outcomes) ? response.outcomes : []
      lastScanAt.value = new Date().toISOString()
      appendAttendanceHistory(activeEvent, response.outcomes, lastScanAt.value)
      void Promise.allSettled(
        (response.outcomes || []).map((outcome) => notifyAttendanceMarked({
          audience: 'kiosk',
          action: outcome?.action,
          eventName: activeEvent?.name,
          studentName: outcome?.student_name || outcome?.student_id,
        }))
      )

      if (automatic) {
        const now = Date.now()
        for (const outcome of response.outcomes || []) {
          if (!outcome?.student_id || !COOLDOWN_ACTIONS.has(String(outcome.action || '').trim().toLowerCase())) {
            continue
          }

          cooldownByStudent[outcome.student_id] = {
            studentId: outcome.student_id,
            studentName: outcome.student_name || null,
            expiresAt: now + (scanCooldownSeconds.value * 1000),
          }
        }

        syncCooldownStudentIds()
      }

      statusMessage.value = primaryOutcomeMessage(response.outcomes, response.message)
      statusTone.value = toneFromOutcomes(response.outcomes)
      return { ok: true, response }
    } catch (error) {
      statusMessage.value = preview.value
        ? (error instanceof Error ? error.message : 'Preview Gather capture failed.')
        : describePublicAttendanceError(error)
      statusTone.value = 'error'
      return { ok: false, error }
    } finally {
      scanBusy.value = false
    }
  }

  async function runAutomaticScanCycle() {
    if (!isAutomaticMode.value || !cameraOn.value || !location.value || !selectedEvent.value || scanBusy.value) {
      return
    }

    const result = await processCapture({ automatic: true })
    if (!isAutomaticMode.value) return

    if (result?.ok) {
      scheduleNextScan(Math.max(900, Math.round(scanCooldownSeconds.value * 250)))
      return
    }

    scheduleNextScan(resolvePublicAttendanceRetryAfterMs(result?.error, 1600))
  }

  function scheduleNextScan(delayMs = 0) {
    stopScanLoop()

    if (!isAutomaticMode.value || !cameraOn.value || !location.value || !selectedEvent.value || scanBusy.value) {
      return
    }

    scanTimeoutId = window.setTimeout(() => {
      scanTimeoutId = 0
      void runAutomaticScanCycle()
    }, Math.max(0, Number(delayMs) || 0))
  }

  async function handleCapture() {
    if (isAutomaticMode.value) return
    await processCapture({ automatic: false })
  }

  function goBack() {
    router.replace(resolveWorkspaceHomeLocation(route))
  }

  onMounted(async () => {
    await loadNearbyEvents({ silent: true, resetSelection: true })
    syncStatusMessage()
  })

  watch(
    [
      scanMode,
      cameraOn,
      selectedEventId,
      location,
    ],
    () => {
      if (isAutomaticMode.value && cameraOn.value && selectedEvent.value && location.value) {
        scheduleNextScan(0)
        return
      }

      stopScanLoop()
    },
  )

  onBeforeUnmount(() => {
    stopScanLoop()
    stopCamera()
  })

  return {
    attendanceHistory,
    canCapture,
    cameraOn,
    formatDateTime,
    formatDistance,
    formatPhaseLabel,
    goBack,
    handleCapture,
    hasEvents,
    hasAttendanceHistory,
    isAutomaticMode,
    isCameraStarting,
    isRefreshingLocation,
    lastScanAt,
    loadNearbyEvents,
    location,
    locationMessage,
    locationPillLabel,
    cameraFacingLabel,
    activeFacingMode,
    activateEvent,
    outcomeTone,
    outcomes,
    refreshGatherContext,
    scanBusy,
    scanCooldownSeconds,
    scanMode,
    selectEvent,
    selectedEvent,
    selectedEventId,
    selectedEventMeta,
    selectedEventPhaseLabel,
    setScanMode,
    startCamera,
    statusMessage,
    statusTone,
    isDiscoveringNearbyEvents,
    needsEventSelection,
    toggleCameraFacing,
    toggleTorch,
    torchEnabled,
    torchSupported,
    videoEl,
    canvasEl,
    nearbyEvents,
  }
}
