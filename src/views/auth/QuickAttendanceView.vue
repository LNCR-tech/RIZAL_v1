<template>
  <div class="quick-kiosk" :class="`quick-kiosk--${kioskStage}`">
    <div class="quick-kiosk__feed">
      <div
        class="quick-kiosk__feed-visual"
        :class="{
          'quick-kiosk__feed-visual--blurred': !isScanning,
          'quick-kiosk__feed-visual--live': cameraOn,
        }"
      >
        <video
          ref="videoEl"
          class="quick-kiosk__video"
          autoplay
          muted
          playsinline
          webkit-playsinline
          disablePictureInPicture
          disableRemotePlayback
          controlslist="nodownload noplaybackrate noremoteplayback"
        />

        <div class="quick-kiosk__feed-placeholder" aria-hidden="true">
          <span class="quick-kiosk__feed-orb quick-kiosk__feed-orb--a" />
          <span class="quick-kiosk__feed-orb quick-kiosk__feed-orb--b" />
          <span class="quick-kiosk__feed-orb quick-kiosk__feed-orb--c" />
          <span class="quick-kiosk__feed-noise" />
        </div>

        <div class="quick-kiosk__feed-grid" aria-hidden="true" />
      </div>

      <div class="quick-kiosk__feed-scrim" aria-hidden="true" />

      <canvas ref="canvasEl" class="quick-kiosk__canvas" aria-hidden="true" />

      <div v-if="isScanning && !cameraOn" class="quick-kiosk__feed-empty">
        <Camera :size="28" :stroke-width="1.9" />
        <p>{{ cameraFallbackMessage }}</p>
      </div>
    </div>

    <button
      class="quick-kiosk__dismiss"
      type="button"
      :aria-label="dismissLabel"
      @click="handleDismiss"
    >
      <X :size="18" :stroke-width="2.1" />
    </button>

    <Transition name="kiosk-sheet">
      <div v-if="!isScanning" class="quick-kiosk__sheet-stage">
        <section class="quick-kiosk__sheet" :class="`quick-kiosk__sheet--${kioskStage}`">
          <div class="quick-kiosk__sheet-brand">
            <span class="quick-kiosk__brand-mark">Aura</span>
            <span class="quick-kiosk__brand-copy">Quick Attendance Kiosk</span>
          </div>

          <Transition name="kiosk-content" mode="out-in">
            <div v-if="isStandby" key="standby" class="quick-kiosk__content quick-kiosk__content--standby">
              <p class="quick-kiosk__eyebrow">Passive Crowd Recognition</p>
              <h1 class="quick-kiosk__title">Initialize Kiosk</h1>
              <p class="quick-kiosk__lead">
                Discover active geofenced events, then hand the camera over to ambient attendance scanning.
              </p>

              <button
                class="quick-kiosk__primary"
                type="button"
                :disabled="isRefreshingLocation"
                @click="handleFindNearbyEvents"
              >
                <LoaderCircle
                  v-if="isRefreshingLocation"
                  :size="18"
                  :stroke-width="2"
                  class="quick-kiosk__spinner"
                />
                <span>{{ isRefreshingLocation ? 'Finding Nearby Events' : 'Find Nearby Events' }}</span>
              </button>
            </div>

            <div v-else key="handoff" class="quick-kiosk__content quick-kiosk__content--handoff">
              <div class="quick-kiosk__sheet-header">
                <div>
                  <p class="quick-kiosk__eyebrow">Event Handoff</p>
                  <h1 class="quick-kiosk__title quick-kiosk__title--compact">Choose an active event</h1>
                </div>

                <button
                  class="quick-kiosk__ghost"
                  type="button"
                  :disabled="isRefreshingLocation || isCameraStarting"
                  aria-label="Refresh nearby events"
                  @click="loadNearbyEvents"
                >
                  <LoaderCircle
                    v-if="isRefreshingLocation"
                    :size="16"
                    :stroke-width="2"
                    class="quick-kiosk__spinner"
                  />
                  <RefreshCw v-else :size="16" :stroke-width="2" />
                </button>
              </div>

              <p class="quick-kiosk__lead quick-kiosk__lead--compact">{{ handoffMessage }}</p>

              <div v-if="nearbyEvents.length" class="quick-kiosk__event-list">
                <button
                  v-for="event in nearbyEvents"
                  :key="event.id"
                  class="quick-kiosk__event-row"
                  :class="{ 'quick-kiosk__event-row--selected': Number(event.id) === Number(selectedEventId) }"
                  type="button"
                  :disabled="isCameraStarting"
                  @click="activateEvent(event)"
                >
                  <div class="quick-kiosk__event-top">
                    <strong>{{ event.name }}</strong>
                    <span class="quick-kiosk__event-phase">{{ formatPhaseLabel(event.attendance_phase) }}</span>
                  </div>

                  <p class="quick-kiosk__event-subline">
                    <span class="quick-kiosk__event-chip">
                      <MapPin :size="13" :stroke-width="2" />
                      <span>{{ event.location }}</span>
                    </span>
                    <span class="quick-kiosk__event-dot" aria-hidden="true" />
                    <span class="quick-kiosk__event-chip">
                      <Clock3 :size="13" :stroke-width="2" />
                      <span>{{ formatEventWindow(event) }}</span>
                    </span>
                  </p>
                </button>
              </div>

              <div v-else class="quick-kiosk__empty">
                <p>{{ isRefreshingLocation ? 'Looking for active geofences nearby…' : 'No active public attendance events are available in range right now.' }}</p>
              </div>

              <p class="quick-kiosk__meta-note" aria-live="polite">{{ locationMessage }}</p>
            </div>
          </Transition>
        </section>
      </div>
    </Transition>

    <Transition name="kiosk-hud">
      <header v-if="isScanning" class="quick-kiosk__hud">
        <div class="quick-kiosk__hud-item quick-kiosk__hud-item--live">
          <span class="quick-kiosk__live-dot" aria-hidden="true" />
          <span>{{ liveLabel }}</span>
        </div>
        <span class="quick-kiosk__hud-divider" aria-hidden="true" />
        <div class="quick-kiosk__hud-item quick-kiosk__hud-item--event">
          {{ selectedEvent?.name || 'No Event Selected' }}
        </div>
        <span class="quick-kiosk__hud-divider" aria-hidden="true" />
        <div class="quick-kiosk__hud-item quick-kiosk__hud-item--count">
          {{ matchedCounterLabel }}
        </div>
      </header>
    </Transition>

    <Transition name="kiosk-status">
      <div
        v-if="isScanning"
        class="quick-kiosk__status"
        :class="`quick-kiosk__status--${scanStatusTone}`"
        aria-live="polite"
      >
        {{ scanStatus }}
      </div>
    </Transition>

    <div v-if="isScanning" class="quick-kiosk__ar-layer" aria-hidden="true">
      <div
        v-for="overlay in faceOverlays"
        :key="overlay.id"
        class="quick-kiosk__ar-box"
        :class="`quick-kiosk__ar-box--${overlay.tone}`"
        :style="faceOverlayStyle(overlay)"
      >
        <span
          v-if="overlay.label"
          class="quick-kiosk__ar-badge"
          :class="`quick-kiosk__ar-badge--${overlay.tone}`"
        >
          {{ overlay.label }}
        </span>
      </div>
    </div>

    <aside v-if="isScanning" class="quick-kiosk__log">
      <div class="quick-kiosk__log-header">
        <p class="quick-kiosk__eyebrow">Recent Matches</p>
        <span class="quick-kiosk__log-meta">{{ logStatus }}</span>
      </div>

      <TransitionGroup name="kiosk-log" tag="div" class="quick-kiosk__log-list">
        <article v-for="entry in recentMatches" :key="entry.id" class="quick-kiosk__log-row">
          <span class="quick-kiosk__avatar">{{ entry.initials }}</span>
          <div class="quick-kiosk__log-copy">
            <strong>{{ entry.firstName }}</strong>
            <span>{{ entry.timeLabel }}</span>
          </div>
        </article>
      </TransitionGroup>

      <p v-if="!recentMatches.length" class="quick-kiosk__log-empty">
        Matches will cascade here as students are confirmed.
      </p>
    </aside>
  </div>
</template>

<script setup>
import { computed, onBeforeMount, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Camera,
  Clock3,
  LoaderCircle,
  MapPin,
  RefreshCw,
  X,
} from 'lucide-vue-next'
import { applyTheme, loadUnbrandedTheme } from '@/config/theme.js'
import {
  getCurrentPositionOrThrow,
  getCurrentPositionWithinAccuracyOrThrow,
  isNativeApp,
  requestCameraPermission,
} from '@/services/devicePermissions.js'
import { notifyAttendanceMarked } from '@/services/localNotifications.js'
import {
  describePublicAttendanceError,
  fetchNearbyPublicAttendanceEvents,
  resolvePublicAttendanceRetryAfterMs,
  submitPublicAttendanceScan,
} from '@/services/publicAttendance.js'

const router = useRouter()
const videoEl = ref(null)
const canvasEl = ref(null)

const kioskStage = ref('standby')
const location = ref(null)
const locationMessage = ref('Allow location access to discover nearby public attendance events.')
const isRefreshingLocation = ref(false)
const nearbyEvents = ref([])
const selectedEventId = ref(null)
const scanCooldownSeconds = ref(8)
const scanStatus = ref('Find nearby events to initialize the kiosk.')
const scanStatusTone = ref('info')
const cameraOn = ref(false)
const isCameraStarting = ref(false)
const scanArmed = ref(false)
const scanBusy = ref(false)
const outcomes = ref([])
const lastScanAt = ref('')
const recentMatches = ref([])
const matchedStudentIds = ref([])
const rawDiscoveryDesiredAccuracyM = Number(import.meta.env.VITE_GATHER_DISCOVERY_ACCURACY_M ?? 45)
const discoveryDesiredAccuracyM = Number.isFinite(rawDiscoveryDesiredAccuracyM) && rawDiscoveryDesiredAccuracyM > 0
  ? rawDiscoveryDesiredAccuracyM
  : 45
const rawDiscoveryTimeoutMs = Number(import.meta.env.VITE_GEOLOCATION_TIMEOUT_MS ?? 18000)
const discoveryTimeoutMs = Number.isFinite(rawDiscoveryTimeoutMs) && rawDiscoveryTimeoutMs > 0
  ? Math.max(rawDiscoveryTimeoutMs, 18000)
  : 18000

let mediaStream = null
let scanTimeoutId = 0
let activeScanSessionId = 0
let cooldownByStudent = {}

const COOLDOWN_ACTIONS = new Set([
  'time_in',
  'time_out',
  'already_signed_in',
  'already_signed_out',
  'cooldown_skipped',
])

const MATCHED_ACTIONS = new Set([
  'time_in',
  'time_out',
  'already_signed_in',
  'already_signed_out',
  'cooldown_skipped',
])

const selectedEvent = computed(() => (
  nearbyEvents.value.find((event) => Number(event.id) === Number(selectedEventId.value)) || null
))

const isStandby = computed(() => kioskStage.value === 'standby')
const isScanning = computed(() => kioskStage.value === 'scanning')

const dismissLabel = computed(() => (isScanning.value ? 'Stop scanning' : 'Close kiosk'))

const handoffMessage = computed(() => {
  if (isRefreshingLocation.value) {
    return 'Locating the device and reading the active geofence perimeter.'
  }

  if (nearbyEvents.value.length) {
    return `${nearbyEvents.value.length} active ${nearbyEvents.value.length === 1 ? 'event is' : 'events are'} within range. Tap one row to go live.`
  }

  return 'Choose one nearby event to reveal the live scanner HUD.'
})

const liveLabel = computed(() => {
  if (scanBusy.value) return 'Reading'
  if (isCameraStarting.value) return 'Starting'
  if (cameraOn.value && scanArmed.value) return 'Live'
  if (cameraOn.value) return 'Ready'
  return 'Standby'
})

const matchedCounterLabel = computed(() => `${matchedStudentIds.value.length} / ${resolveCounterTarget(selectedEvent.value)}`)

const cameraFallbackMessage = computed(() => {
  if (scanStatusTone.value === 'error') return scanStatus.value
  if (isCameraStarting.value) return 'Connecting to the camera feed…'
  return 'Camera feed unavailable. Return to the event handoff and try again.'
})

const logStatus = computed(() => {
  if (recentMatches.value.length) {
    return lastScanAt.value ? `Updated ${formatLogTime(lastScanAt.value)}` : 'Live'
  }

  return scanBusy.value ? 'Scanning crowd' : 'Waiting'
})

const faceOverlays = computed(() => {
  return (Array.isArray(outcomes.value) ? outcomes.value : [])
    .map((outcome, index) => buildFaceOverlay(outcome, index))
    .filter(Boolean)
})

onBeforeMount(() => {
  applyTheme(loadUnbrandedTheme())
})

onBeforeUnmount(() => {
  activeScanSessionId += 1
  stopScanLoop()
  stopCamera()
})

function goBack() {
  router.push({ name: 'Login' })
}

function handleDismiss() {
  if (isScanning.value) {
    returnToEventHandoff()
    return
  }

  goBack()
}

function handleFindNearbyEvents() {
  kioskStage.value = 'handoff'
  void loadNearbyEvents()
}

function formatDateTime(value, options = {
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
}) {
  if (!value) return 'N/A'

  try {
    return new Intl.DateTimeFormat(undefined, options).format(new Date(value))
  } catch {
    return 'N/A'
  }
}

function formatClockTime(value) {
  if (!value) return 'TBA'

  try {
    return new Intl.DateTimeFormat(undefined, {
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date(value))
  } catch {
    return 'TBA'
  }
}

function formatLogTime(value) {
  if (!value) return 'Now'

  try {
    return new Intl.DateTimeFormat(undefined, {
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
    }).format(new Date(value))
  } catch {
    return 'Now'
  }
}

function formatDistance(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return 'N/A'
  return `${normalized.toFixed(normalized < 10 ? 1 : 0)} m`
}

function formatEventWindow(event) {
  const startLabel = formatClockTime(event?.start_datetime)
  const endLabel = formatClockTime(event?.end_datetime)

  if (startLabel !== 'TBA' && endLabel !== 'TBA') {
    return `${startLabel} - ${endLabel}`
  }

  if (startLabel !== 'TBA') {
    return startLabel
  }

  return event?.school_name || 'Campus'
}

function formatPhaseLabel(phase) {
  return String(phase || '').trim().toLowerCase() === 'sign_out' ? 'Sign Out' : 'Sign In'
}

function resolveCounterTarget(event) {
  const candidates = [
    event?.expected_attendance,
    event?.expectedAttendance,
    event?.target_attendance,
    event?.targetAttendance,
    event?.participant_limit,
    event?.participantLimit,
    event?.capacity,
  ]

  const match = candidates.find((value) => Number.isFinite(Number(value)) && Number(value) > 0)
  return match ? Number(match) : 500
}

function firstName(value) {
  return String(value || '').trim().split(/\s+/).filter(Boolean)[0] || 'Student'
}

function initials(value) {
  const parts = String(value || '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return 'AU'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0] || ''}${parts[parts.length - 1][0] || ''}`.toUpperCase()
}

function faceOverlayStyle(overlay) {
  return {
    left: overlay.left,
    top: overlay.top,
    width: overlay.width,
    height: overlay.height,
  }
}

function primaryOutcomeMessage(responseOutcomes, fallback) {
  const priority = (Array.isArray(responseOutcomes) ? responseOutcomes : []).find((outcome) =>
    ['time_in', 'time_out'].includes(String(outcome?.action || '').trim().toLowerCase())
  )

  return priority?.message || responseOutcomes?.[0]?.message || fallback
}

function toneFromOutcomes(responseOutcomes) {
  if ((responseOutcomes || []).some((outcome) => ['time_in', 'time_out'].includes(outcome.action))) {
    return 'success'
  }

  if ((responseOutcomes || []).some((outcome) => ['liveness_failed', 'out_of_scope', 'no_match', 'rejected'].includes(outcome.action))) {
    return 'error'
  }

  return 'info'
}

function activeCooldownStudentIds() {
  const now = Date.now()
  cooldownByStudent = Object.fromEntries(
    Object.entries(cooldownByStudent).filter(([, entry]) => Number(entry?.expiresAt) > now)
  )

  return Object.keys(cooldownByStudent)
}

function appendRecentMatches(responseOutcomes, occurredAt) {
  const freshEntries = []
  const seenStudentIds = new Set(matchedStudentIds.value)

  for (const [index, outcome] of (Array.isArray(responseOutcomes) ? responseOutcomes : []).entries()) {
    const action = String(outcome?.action || '').trim().toLowerCase()
    if (!MATCHED_ACTIONS.has(action) || !outcome?.student_id) continue

    seenStudentIds.add(outcome.student_id)
    const name = outcome.student_name || outcome.student_id

    freshEntries.push({
      id: `${outcome.student_id}-${action}-${occurredAt}-${index}`,
      studentId: outcome.student_id,
      firstName: firstName(name),
      initials: initials(name),
      timeLabel: formatLogTime(outcome.time_out || outcome.time_in || occurredAt),
    })
  }

  matchedStudentIds.value = Array.from(seenStudentIds)

  if (freshEntries.length) {
    recentMatches.value = [...freshEntries, ...recentMatches.value].slice(0, 8)
  }
}

async function loadNearbyEvents() {
  isRefreshingLocation.value = true
  scanStatusTone.value = 'info'
  scanStatus.value = 'Finding your location and discovering public attendance events…'

  try {
    const position = await (
      isNativeApp()
        ? getCurrentPositionWithinAccuracyOrThrow({
            desiredAccuracy: discoveryDesiredAccuracyM,
            enableHighAccuracy: true,
            timeout: discoveryTimeoutMs,
            maximumAge: 0,
            onAccuracyUpdate: (accuracy) => {
              if (!Number.isFinite(Number(accuracy)) || Number(accuracy) <= 0) return
              scanStatus.value = `Improving GPS accuracy... currently ${formatDistance(accuracy)}.`
              scanStatusTone.value = 'info'
            },
          })
        : getCurrentPositionOrThrow({
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0,
          })
    )

    const nextLocation = {
      latitude: position.latitude,
      longitude: position.longitude,
      accuracyM: position.accuracy,
      resolvedAt: position.capturedAt || new Date().toISOString(),
    }

    const response = await fetchNearbyPublicAttendanceEvents(nextLocation)

    location.value = nextLocation
    locationMessage.value = `Location updated ${formatDateTime(nextLocation.resolvedAt, {
      hour: 'numeric',
      minute: '2-digit',
    })} · accuracy ${formatDistance(nextLocation.accuracyM)}.`
    nearbyEvents.value = response.events
    selectedEventId.value = response.events.some((event) => Number(event.id) === Number(selectedEventId.value))
      ? selectedEventId.value
      : (response.events[0]?.id || null)
    scanCooldownSeconds.value = response.scan_cooldown_seconds
    outcomes.value = []
    lastScanAt.value = ''

    if (!response.events.length) {
      scanStatus.value = 'No nearby public attendance events are open for scanning right now.'
      scanStatusTone.value = 'info'
      return
    }

    const highlighted = response.events.find((event) => Number(event.id) === Number(selectedEventId.value)) || response.events[0]
    scanStatus.value = highlighted?.phase_message || `Found ${response.events.length} nearby event${response.events.length === 1 ? '' : 's'}.`
    scanStatusTone.value = 'info'
  } catch (error) {
    nearbyEvents.value = []
    selectedEventId.value = null
    locationMessage.value = describePublicAttendanceError(error)
    scanStatus.value = describePublicAttendanceError(error)
    scanStatusTone.value = 'error'
  } finally {
    isRefreshingLocation.value = false
  }
}

async function activateEvent(event) {
  if (!event) return

  selectedEventId.value = event.id
  kioskStage.value = 'scanning'
  outcomes.value = []
  recentMatches.value = []
  matchedStudentIds.value = []
  lastScanAt.value = ''
  cooldownByStudent = {}
  scanBusy.value = false
  scanStatusTone.value = 'info'
  scanStatus.value = `Opening ${event.name}…`
  scanArmed.value = false
  stopScanLoop()

  const sessionId = ++activeScanSessionId
  isCameraStarting.value = true

  try {
    const started = await startCamera(sessionId)
    if (!started || sessionId !== activeScanSessionId) return

    scanArmed.value = true
    scanStatus.value = 'Ambient scanning is live. Keep faces visible inside the frame.'
    scanStatusTone.value = 'info'
    scheduleNextScan(220, sessionId)
  } catch (error) {
    if (sessionId !== activeScanSessionId) return

    cameraOn.value = false
    scanArmed.value = false
    scanStatus.value = humanizeCameraError(error)
    scanStatusTone.value = 'error'
  } finally {
    if (sessionId === activeScanSessionId) {
      isCameraStarting.value = false
    }
  }
}

function returnToEventHandoff() {
  activeScanSessionId += 1
  isCameraStarting.value = false
  scanBusy.value = false
  stopScanLoop()
  stopCamera()
  kioskStage.value = 'handoff'
  scanStatusTone.value = 'info'
  scanStatus.value = selectedEvent.value
    ? `Live scanning stopped for ${selectedEvent.value.name}.`
    : 'Live scanning stopped.'
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
      return 'Camera permission was denied. Allow camera access and try again.'
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

async function startCamera(sessionId = activeScanSessionId) {
  if (mediaStream) {
    if (videoEl.value && videoEl.value.srcObject !== mediaStream) {
      videoEl.value.srcObject = mediaStream
      await waitForVideoReady(videoEl.value)
      await videoEl.value.play().catch(() => null)
    }

    cameraOn.value = true
    return true
  }

  const cameraPermission = await requestCameraPermission()
  if (!cameraPermission.granted) {
    throw new Error(cameraPermission.message || 'Camera permission was denied. Allow camera access and try again.')
  }

  if (!navigator?.mediaDevices?.getUserMedia) {
    throw new Error('Camera access is not supported on this browser.')
  }

  const stream = await navigator.mediaDevices.getUserMedia({
    audio: false,
    video: {
      facingMode: 'user',
    },
  })

  if (sessionId !== activeScanSessionId) {
    stream.getTracks().forEach((track) => track.stop())
    return false
  }

  mediaStream = stream

  if (videoEl.value) {
    videoEl.value.srcObject = stream
    await waitForVideoReady(videoEl.value)
    await videoEl.value.play().catch(() => null)
  }

  if (sessionId !== activeScanSessionId) {
    stream.getTracks().forEach((track) => track.stop())
    mediaStream = null

    if (videoEl.value) {
      videoEl.value.srcObject = null
    }

    return false
  }

  cameraOn.value = true
  return true
}

function stopCamera() {
  scanArmed.value = false

  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop())
    mediaStream = null
  }

  if (videoEl.value) {
    videoEl.value.srcObject = null
  }

  cameraOn.value = false
}

function stopScanLoop() {
  if (scanTimeoutId) {
    window.clearTimeout(scanTimeoutId)
    scanTimeoutId = 0
  }
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
      0.82,
    )
  })
}

async function runScanCycle(sessionId = activeScanSessionId) {
  if (
    sessionId !== activeScanSessionId
    || !scanArmed.value
    || !cameraOn.value
    || !selectedEvent.value
    || !location.value
    || scanBusy.value
  ) {
    return
  }

  scanBusy.value = true

  try {
    const activeEvent = selectedEvent.value
    const frameBlob = await captureFrameBlob()
    if (sessionId !== activeScanSessionId) return

    const response = await submitPublicAttendanceScan({
      eventId: activeEvent.id,
      imageBlob: frameBlob,
      location: location.value,
      cooldownStudentIds: activeCooldownStudentIds(),
    })

    if (sessionId !== activeScanSessionId) return

    const now = Date.now()
    for (const outcome of response.outcomes) {
      if (!outcome.student_id || !COOLDOWN_ACTIONS.has(outcome.action)) continue

      cooldownByStudent[outcome.student_id] = {
        studentId: outcome.student_id,
        studentName: outcome.student_name || null,
        expiresAt: now + (response.scan_cooldown_seconds * 1000),
      }
    }

    scanCooldownSeconds.value = response.scan_cooldown_seconds
    outcomes.value = response.outcomes

    const occurredAt = new Date().toISOString()
    appendRecentMatches(response.outcomes, occurredAt)
    lastScanAt.value = occurredAt
    scanStatus.value = primaryOutcomeMessage(response.outcomes, response.message)
    scanStatusTone.value = toneFromOutcomes(response.outcomes)
    void Promise.allSettled(
      (response.outcomes || []).map((outcome) => notifyAttendanceMarked({
        audience: 'kiosk',
        action: outcome?.action,
        eventName: activeEvent?.name,
        studentName: outcome?.student_name || outcome?.student_id,
      }))
    )

    scheduleNextScan(1100, sessionId)
  } catch (error) {
    if (sessionId !== activeScanSessionId) return

    scanStatus.value = describePublicAttendanceError(error)
    scanStatusTone.value = 'error'
    scheduleNextScan(resolvePublicAttendanceRetryAfterMs(error, 1600), sessionId)
  } finally {
    if (sessionId === activeScanSessionId) {
      scanBusy.value = false
    }
  }
}

function scheduleNextScan(delayMs = 0, sessionId = activeScanSessionId) {
  stopScanLoop()

  if (
    sessionId !== activeScanSessionId
    || !scanArmed.value
    || !cameraOn.value
    || !selectedEvent.value
    || !location.value
  ) {
    return
  }

  scanTimeoutId = window.setTimeout(() => {
    scanTimeoutId = 0
    void runScanCycle(sessionId)
  }, Math.max(0, Number(delayMs) || 0))
}

function buildFaceOverlay(outcome, index) {
  const box = extractFaceBox(outcome)
  if (!box) return null

  const action = String(outcome?.action || '').trim().toLowerCase()
  const isMatched = Boolean(outcome?.student_name) && MATCHED_ACTIONS.has(action)

  return {
    id: `${outcome?.student_id || 'pending'}-${action || 'scan'}-${index}`,
    tone: isMatched ? 'matched' : 'pending',
    label: isMatched ? firstName(outcome.student_name) : '',
    ...box,
  }
}

function extractFaceBox(outcome) {
  const candidates = [
    outcome?.bounding_box,
    outcome?.boundingBox,
    outcome?.face_box,
    outcome?.faceBox,
    outcome?.box,
  ]

  for (const candidate of candidates) {
    const normalized = normalizeFaceBox(candidate)
    if (normalized) return normalized
  }

  return null
}

function normalizeFaceBox(candidate) {
  if (!candidate) return null

  if (Array.isArray(candidate) && candidate.length >= 4) {
    return faceBoxFromRect(candidate[0], candidate[1], candidate[2], candidate[3])
  }

  if (typeof candidate !== 'object') return null

  const left = firstFinite(
    candidate.left,
    candidate.x,
    candidate.xmin,
    candidate.x_min,
    candidate.originX,
  )
  const top = firstFinite(
    candidate.top,
    candidate.y,
    candidate.ymin,
    candidate.y_min,
    candidate.originY,
  )
  const width = firstFinite(candidate.width, candidate.w)
  const height = firstFinite(candidate.height, candidate.h)

  if ([left, top, width, height].every((value) => value != null)) {
    return faceBoxFromRect(left, top, width, height)
  }

  const right = firstFinite(
    candidate.right,
    candidate.xmax,
    candidate.x_max,
    candidate.endX,
  )
  const bottom = firstFinite(
    candidate.bottom,
    candidate.ymax,
    candidate.y_max,
    candidate.endY,
  )

  if ([left, top, right, bottom].every((value) => value != null)) {
    return faceBoxFromRect(left, top, Number(right) - Number(left), Number(bottom) - Number(top))
  }

  return null
}

function faceBoxFromRect(left, top, width, height) {
  const normalizedLeft = normalizeCssMeasure(left)
  const normalizedTop = normalizeCssMeasure(top)
  const normalizedWidth = normalizeCssMeasure(width)
  const normalizedHeight = normalizeCssMeasure(height)

  if (!normalizedLeft || !normalizedTop || !normalizedWidth || !normalizedHeight) {
    return null
  }

  return {
    left: normalizedLeft,
    top: normalizedTop,
    width: normalizedWidth,
    height: normalizedHeight,
  }
}

function normalizeCssMeasure(value) {
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return null
    if (trimmed.endsWith('%') || trimmed.endsWith('px')) return trimmed

    const numeric = Number(trimmed)
    if (!Number.isFinite(numeric)) return null
    return numeric >= 0 && numeric <= 1
      ? `${(numeric * 100).toFixed(2)}%`
      : numeric >= 0 && numeric <= 100
        ? `${numeric.toFixed(2)}%`
        : `${numeric}px`
  }

  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return null

  if (numeric >= 0 && numeric <= 1) {
    return `${(numeric * 100).toFixed(2)}%`
  }

  if (numeric >= 0 && numeric <= 100) {
    return `${numeric.toFixed(2)}%`
  }

  return `${numeric}px`
}

function firstFinite(...values) {
  const match = values.find((value) => Number.isFinite(Number(value)))
  return match == null ? null : Number(match)
}
</script>

<style scoped>
.quick-kiosk {
  --kiosk-bg: #03080f;
  --kiosk-surface: rgba(16, 22, 33, 0.54);
  --kiosk-surface-strong: rgba(11, 16, 24, 0.72);
  --kiosk-text: #f5f7fb;
  --kiosk-muted: rgba(225, 232, 244, 0.66);
  --kiosk-muted-strong: rgba(225, 232, 244, 0.86);
  --kiosk-accent: #0a84ff;
  --kiosk-accent-strong: #6ec3ff;
  --kiosk-success: #32d74b;
  --kiosk-danger: #ff6159;
  position: relative;
  min-height: 100dvh;
  overflow: hidden;
  background: var(--kiosk-bg);
  color: var(--kiosk-text);
  font-family:
    -apple-system,
    BlinkMacSystemFont,
    'SF Pro Display',
    'SF Pro Text',
    'Segoe UI',
    sans-serif;
}

.quick-kiosk__feed,
.quick-kiosk__feed-visual,
.quick-kiosk__video,
.quick-kiosk__feed-placeholder,
.quick-kiosk__feed-grid,
.quick-kiosk__feed-scrim,
.quick-kiosk__ar-layer {
  position: absolute;
  inset: 0;
}

.quick-kiosk__feed {
  background:
    radial-gradient(circle at 12% 18%, rgba(10, 132, 255, 0.16), transparent 30%),
    radial-gradient(circle at 84% 18%, rgba(50, 215, 75, 0.1), transparent 26%),
    radial-gradient(circle at 52% 82%, rgba(255, 255, 255, 0.08), transparent 36%),
    #03080f;
}

.quick-kiosk__feed-visual {
  transition:
    filter 280ms cubic-bezier(0.22, 1, 0.36, 1),
    transform 280ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 180ms ease;
}

.quick-kiosk__feed-visual--blurred {
  filter: blur(28px) saturate(0.84) brightness(0.6);
  transform: scale(1.08);
}

.quick-kiosk--scanning .quick-kiosk__feed-visual {
  filter: none;
  transform: scale(1);
}

.quick-kiosk__video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: #06080d;
  opacity: 0;
  transition: opacity 180ms ease;
}

.quick-kiosk__feed-visual--live .quick-kiosk__video {
  opacity: 1;
}

.quick-kiosk__feed-placeholder {
  overflow: hidden;
  background:
    linear-gradient(140deg, rgba(4, 8, 14, 0.92) 0%, rgba(11, 17, 27, 0.88) 42%, rgba(8, 14, 22, 0.96) 100%);
}

.quick-kiosk__feed-visual--live .quick-kiosk__feed-placeholder {
  opacity: 0.2;
}

.quick-kiosk__feed-orb,
.quick-kiosk__feed-noise {
  position: absolute;
  border-radius: 999px;
}

.quick-kiosk__feed-orb--a {
  width: 42vw;
  height: 42vw;
  left: -6vw;
  top: 8vh;
  background: radial-gradient(circle, rgba(29, 125, 255, 0.42) 0%, rgba(29, 125, 255, 0) 72%);
  animation: kioskFloatA 18s ease-in-out infinite;
}

.quick-kiosk__feed-orb--b {
  width: 36vw;
  height: 36vw;
  right: -4vw;
  top: 14vh;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.14) 0%, rgba(255, 255, 255, 0) 68%);
  animation: kioskFloatB 20s ease-in-out infinite;
}

.quick-kiosk__feed-orb--c {
  width: 34vw;
  height: 34vw;
  left: 32vw;
  bottom: -8vw;
  background: radial-gradient(circle, rgba(50, 215, 75, 0.18) 0%, rgba(50, 215, 75, 0) 70%);
  animation: kioskFloatC 24s ease-in-out infinite;
}

.quick-kiosk__feed-noise {
  inset: -20%;
  border-radius: 0;
  opacity: 0.12;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(255, 255, 255, 0.28) 0 0.6px, transparent 0.9px),
    radial-gradient(circle at 70% 58%, rgba(255, 255, 255, 0.16) 0 0.6px, transparent 0.9px);
  background-size: 22px 22px, 28px 28px;
  mix-blend-mode: screen;
}

.quick-kiosk__feed-grid {
  opacity: 0.15;
  background:
    linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
  background-size: 64px 64px;
  mask-image: radial-gradient(circle at center, black 30%, transparent 82%);
}

.quick-kiosk__feed-scrim {
  background:
    linear-gradient(180deg, rgba(3, 8, 15, 0.72) 0%, rgba(3, 8, 15, 0.28) 24%, rgba(3, 8, 15, 0.34) 74%, rgba(3, 8, 15, 0.72) 100%),
    radial-gradient(circle at center, rgba(8, 14, 22, 0.08) 0%, rgba(3, 8, 15, 0.52) 100%);
  transition: background 220ms ease;
}

.quick-kiosk--standby .quick-kiosk__feed-scrim,
.quick-kiosk--handoff .quick-kiosk__feed-scrim {
  background:
    linear-gradient(180deg, rgba(3, 8, 15, 0.84) 0%, rgba(3, 8, 15, 0.42) 22%, rgba(3, 8, 15, 0.52) 74%, rgba(3, 8, 15, 0.86) 100%),
    radial-gradient(circle at center, rgba(13, 22, 34, 0.14) 0%, rgba(3, 8, 15, 0.62) 100%);
}

.quick-kiosk__canvas {
  display: none;
}

.quick-kiosk__feed-empty {
  position: absolute;
  z-index: 18;
  left: 50%;
  top: 50%;
  width: min(88vw, 24rem);
  transform: translate(-50%, -50%);
  padding: 1.2rem 1.3rem;
  border-radius: 1.6rem;
  background: rgba(7, 11, 18, 0.44);
  color: var(--kiosk-muted-strong);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.8rem;
  text-align: center;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow:
    0 24px 64px rgba(0, 0, 0, 0.28),
    inset 0 0 0 0.8px rgba(255, 255, 255, 0.08);
}

.quick-kiosk__feed-empty p {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.5;
}

.quick-kiosk__dismiss {
  position: fixed;
  top: max(18px, calc(env(safe-area-inset-top, 0px) + 12px));
  right: max(18px, calc(env(safe-area-inset-right, 0px) + 12px));
  z-index: 60;
  width: 46px;
  height: 46px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: rgba(10, 15, 22, 0.48);
  color: var(--kiosk-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow:
    0 18px 42px rgba(0, 0, 0, 0.22),
    inset 0 0 0 0.8px rgba(255, 255, 255, 0.08);
  transition:
    transform 180ms ease,
    background 180ms ease,
    box-shadow 180ms ease;
}

.quick-kiosk__dismiss:hover {
  transform: translateY(-1px);
  background: rgba(14, 20, 29, 0.6);
}

.quick-kiosk__dismiss:active {
  transform: scale(0.97);
}

.quick-kiosk__sheet-stage {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  padding:
    max(28px, calc(env(safe-area-inset-top, 0px) + 18px))
    20px
    max(28px, calc(env(safe-area-inset-bottom, 0px) + 18px));
}

.quick-kiosk__sheet {
  width: min(92vw, 33rem);
  max-height: min(88dvh, 42rem);
  padding: 1.4rem;
  border-radius: 2rem;
  background: var(--kiosk-surface);
  color: var(--kiosk-text);
  backdrop-filter: blur(28px) saturate(1.15);
  -webkit-backdrop-filter: blur(28px) saturate(1.15);
  box-shadow:
    0 36px 96px rgba(0, 0, 0, 0.34),
    inset 0 0 0 0.85px rgba(255, 255, 255, 0.08);
  transition:
    width 280ms cubic-bezier(0.22, 1, 0.36, 1),
    max-height 280ms cubic-bezier(0.22, 1, 0.36, 1),
    padding 280ms cubic-bezier(0.22, 1, 0.36, 1);
}

.quick-kiosk__sheet--handoff {
  width: min(92vw, 45rem);
  max-height: min(90dvh, 47rem);
}

.quick-kiosk__sheet-brand,
.quick-kiosk__sheet-header,
.quick-kiosk__event-top,
.quick-kiosk__event-subline,
.quick-kiosk__event-chip,
.quick-kiosk__hud,
.quick-kiosk__hud-item,
.quick-kiosk__log-header,
.quick-kiosk__log-row {
  display: flex;
}

.quick-kiosk__sheet-brand,
.quick-kiosk__sheet-header,
.quick-kiosk__event-top,
.quick-kiosk__hud,
.quick-kiosk__log-header,
.quick-kiosk__log-row {
  align-items: center;
  justify-content: space-between;
}

.quick-kiosk__sheet-brand {
  gap: 0.8rem;
}

.quick-kiosk__brand-mark {
  min-width: 3rem;
  height: 3rem;
  padding: 0 0.95rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--kiosk-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.88rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.quick-kiosk__brand-copy {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--kiosk-muted);
}

.quick-kiosk__content {
  display: flex;
  flex-direction: column;
}

.quick-kiosk__content--standby {
  align-items: center;
  gap: 1rem;
  padding: clamp(2.4rem, 5vw, 3.8rem) clamp(1rem, 3vw, 1.3rem) clamp(1rem, 3vw, 1.4rem);
  text-align: center;
}

.quick-kiosk__content--handoff {
  gap: 1rem;
  margin-top: 1.3rem;
}

.quick-kiosk__eyebrow {
  margin: 0;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(225, 232, 244, 0.52);
}

.quick-kiosk__title {
  margin: 0;
  font-size: clamp(2.8rem, 5.2vw, 4.35rem);
  line-height: 0.96;
  letter-spacing: -0.065em;
  text-wrap: balance;
}

.quick-kiosk__title--compact {
  font-size: clamp(1.8rem, 3vw, 2.55rem);
  line-height: 1;
  letter-spacing: -0.05em;
}

.quick-kiosk__lead,
.quick-kiosk__meta-note,
.quick-kiosk__log-meta,
.quick-kiosk__log-copy span,
.quick-kiosk__event-subline,
.quick-kiosk__empty p {
  margin: 0;
  font-size: 0.98rem;
  line-height: 1.6;
  color: var(--kiosk-muted);
}

.quick-kiosk__lead {
  max-width: 28rem;
  text-wrap: balance;
}

.quick-kiosk__lead--compact {
  max-width: 36rem;
}

.quick-kiosk__primary,
.quick-kiosk__ghost {
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  font: inherit;
  font-size: 0.98rem;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    opacity 180ms ease,
    background 180ms ease;
}

.quick-kiosk__primary {
  min-height: 56px;
  padding: 0 1.45rem;
  margin-top: 0.35rem;
  background: linear-gradient(180deg, #2d9fff 0%, var(--kiosk-accent) 100%);
  color: #f8fbff;
  box-shadow: 0 20px 48px rgba(10, 132, 255, 0.38);
}

.quick-kiosk__primary:hover,
.quick-kiosk__ghost:hover {
  transform: translateY(-1px);
}

.quick-kiosk__primary:active,
.quick-kiosk__ghost:active {
  transform: scale(0.98);
}

.quick-kiosk__primary:disabled,
.quick-kiosk__ghost:disabled,
.quick-kiosk__event-row:disabled {
  opacity: 0.64;
  cursor: not-allowed;
}

.quick-kiosk__ghost {
  width: 44px;
  height: 44px;
  padding: 0;
  background: rgba(255, 255, 255, 0.08);
  color: var(--kiosk-text);
  box-shadow: inset 0 0 0 0.8px rgba(255, 255, 255, 0.08);
}

.quick-kiosk__event-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  max-height: min(48vh, 26rem);
  padding-right: 0.2rem;
  overflow: auto;
}

.quick-kiosk__event-list::-webkit-scrollbar {
  width: 6px;
}

.quick-kiosk__event-list::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
}

.quick-kiosk__event-row {
  width: 100%;
  padding: 1rem 0.1rem;
  border: none;
  border-radius: 1.35rem;
  background: transparent;
  color: inherit;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.08);
  transition:
    transform 180ms ease,
    background 180ms ease,
    box-shadow 180ms ease;
}

.quick-kiosk__event-row:hover {
  transform: translateX(4px);
  background: rgba(255, 255, 255, 0.04);
}

.quick-kiosk__event-row--selected {
  background: rgba(255, 255, 255, 0.08);
  box-shadow:
    inset 0 0 0 0.8px rgba(255, 255, 255, 0.08),
    inset 0 -1px 0 rgba(255, 255, 255, 0.02);
  padding-inline: 0.9rem;
}

.quick-kiosk__event-top strong,
.quick-kiosk__log-copy strong {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.quick-kiosk__event-phase {
  min-height: 28px;
  padding: 0 0.72rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--kiosk-muted-strong);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.quick-kiosk__event-subline {
  align-items: center;
  flex-wrap: wrap;
  gap: 0.55rem;
  font-size: 0.88rem;
}

.quick-kiosk__event-chip {
  align-items: center;
  gap: 0.38rem;
}

.quick-kiosk__event-dot {
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
}

.quick-kiosk__empty {
  padding: 1.25rem 0;
}

.quick-kiosk__meta-note {
  font-size: 0.9rem;
}

.quick-kiosk__hud {
  position: fixed;
  top: max(18px, calc(env(safe-area-inset-top, 0px) + 12px));
  left: 50%;
  z-index: 50;
  transform: translateX(-50%);
  gap: 0.9rem;
  min-height: 58px;
  padding: 0 1.2rem;
  border-radius: 999px;
  background: rgba(7, 11, 18, 0.48);
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  box-shadow:
    0 24px 72px rgba(0, 0, 0, 0.34),
    inset 0 0 0 0.8px rgba(255, 255, 255, 0.08);
}

.quick-kiosk__hud-item {
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.quick-kiosk__hud-item--event {
  max-width: min(48vw, 28rem);
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-kiosk__hud-divider {
  width: 1px;
  height: 20px;
  background: rgba(255, 255, 255, 0.12);
}

.quick-kiosk__live-dot {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: #ff3b30;
  box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.42);
  animation: kioskPulse 1.7s ease-in-out infinite;
}

.quick-kiosk__status {
  position: fixed;
  left: max(20px, calc(env(safe-area-inset-left, 0px) + 14px));
  bottom: max(20px, calc(env(safe-area-inset-bottom, 0px) + 14px));
  z-index: 36;
  max-width: min(34rem, calc(100vw - 40px));
  padding: 0.95rem 1.15rem;
  border-radius: 1.3rem;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow:
    0 20px 54px rgba(0, 0, 0, 0.22),
    inset 0 0 0 0.8px rgba(255, 255, 255, 0.08);
  font-size: 0.92rem;
  line-height: 1.5;
}

.quick-kiosk__status--info {
  background: rgba(10, 16, 24, 0.56);
  color: var(--kiosk-muted-strong);
}

.quick-kiosk__status--success {
  background: rgba(9, 20, 14, 0.58);
  color: #d8ffe0;
}

.quick-kiosk__status--error {
  background: rgba(32, 10, 10, 0.62);
  color: #ffd8d5;
}

.quick-kiosk__ar-layer {
  z-index: 20;
  pointer-events: none;
}

.quick-kiosk__ar-box {
  position: absolute;
  border-radius: 28px;
  box-sizing: border-box;
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}

.quick-kiosk__ar-box::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background:
    linear-gradient(90deg, currentColor 0 18px, transparent 18px calc(100% - 18px), currentColor calc(100% - 18px) 100%),
    linear-gradient(currentColor 0 18px, transparent 18px calc(100% - 18px), currentColor calc(100% - 18px) 100%),
    linear-gradient(90deg, currentColor 0 18px, transparent 18px calc(100% - 18px), currentColor calc(100% - 18px) 100%) bottom,
    linear-gradient(currentColor 0 18px, transparent 18px calc(100% - 18px), currentColor calc(100% - 18px) 100%) right;
  background-repeat: no-repeat;
  background-size: 100% 1.5px, 1.5px 100%, 100% 1.5px, 1.5px 100%;
  opacity: 0.86;
}

.quick-kiosk__ar-box--pending {
  color: rgba(255, 255, 255, 0.86);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.14),
    0 0 0 1px rgba(255, 255, 255, 0.06);
}

.quick-kiosk__ar-box--matched {
  color: var(--kiosk-success);
  box-shadow:
    inset 0 0 0 1px rgba(50, 215, 75, 0.28),
    0 0 28px rgba(50, 215, 75, 0.16);
}

.quick-kiosk__ar-badge {
  position: absolute;
  left: 0.55rem;
  top: 0;
  transform: translateY(calc(-100% - 0.45rem));
  min-height: 28px;
  padding: 0 0.72rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.quick-kiosk__ar-badge--pending {
  background: rgba(245, 247, 251, 0.12);
  color: #f5f7fb;
}

.quick-kiosk__ar-badge--matched {
  background: rgba(50, 215, 75, 0.16);
  color: #d6ffe0;
}

.quick-kiosk__log {
  position: fixed;
  top: max(92px, calc(env(safe-area-inset-top, 0px) + 84px));
  right: max(20px, calc(env(safe-area-inset-right, 0px) + 14px));
  z-index: 35;
  width: min(24rem, 28vw);
  max-height: min(calc(100dvh - 132px), 36rem);
  padding: 1rem;
  border-radius: 1.8rem;
  background: rgba(7, 11, 18, 0.42);
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  box-shadow:
    0 26px 72px rgba(0, 0, 0, 0.28),
    inset 0 0 0 0.8px rgba(255, 255, 255, 0.08);
}

.quick-kiosk__log-header {
  gap: 1rem;
}

.quick-kiosk__log-meta {
  font-size: 0.82rem;
}

.quick-kiosk__log-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  margin-top: 0.9rem;
}

.quick-kiosk__log-row {
  gap: 0.8rem;
  padding: 0.88rem 0.92rem;
  border-radius: 1.1rem;
  background: rgba(255, 255, 255, 0.05);
  box-shadow: inset 0 0 0 0.8px rgba(255, 255, 255, 0.04);
}

.quick-kiosk__avatar {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 999px;
  flex: 0 0 auto;
  background: linear-gradient(160deg, rgba(110, 195, 255, 0.32), rgba(255, 255, 255, 0.08));
  color: #ecf6ff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.quick-kiosk__log-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.18rem;
}

.quick-kiosk__log-copy strong {
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-kiosk__log-copy span {
  font-size: 0.82rem;
}

.quick-kiosk__log-empty {
  margin: 0.9rem 0 0;
  font-size: 0.88rem;
  line-height: 1.5;
  color: var(--kiosk-muted);
}

.quick-kiosk__spinner {
  animation: kioskSpin 0.9s linear infinite;
}

.kiosk-sheet-enter-active,
.kiosk-sheet-leave-active {
  transition:
    opacity 220ms ease,
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1);
}

.kiosk-sheet-enter-from,
.kiosk-sheet-leave-to {
  opacity: 0;
  transform: scale(0.94);
}

.kiosk-content-enter-active,
.kiosk-content-leave-active {
  transition:
    opacity 180ms ease,
    transform 240ms cubic-bezier(0.22, 1, 0.36, 1);
}

.kiosk-content-enter-from,
.kiosk-content-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

.kiosk-hud-enter-active,
.kiosk-hud-leave-active,
.kiosk-status-enter-active,
.kiosk-status-leave-active {
  transition:
    opacity 220ms ease,
    transform 300ms cubic-bezier(0.22, 1, 0.36, 1);
}

.kiosk-hud-enter-from,
.kiosk-hud-leave-to {
  opacity: 0;
  transform: translate(-50%, -18px);
}

.kiosk-status-enter-from,
.kiosk-status-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

.kiosk-log-enter-active,
.kiosk-log-leave-active {
  transition:
    opacity 260ms ease,
    transform 340ms cubic-bezier(0.22, 1, 0.36, 1);
}

.kiosk-log-move {
  transition: transform 320ms cubic-bezier(0.22, 1, 0.36, 1);
}

.kiosk-log-enter-from,
.kiosk-log-leave-to {
  opacity: 0;
  transform: translateY(-14px) scale(0.98);
}

@keyframes kioskPulse {
  0% {
    box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.42);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(255, 59, 48, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(255, 59, 48, 0);
  }
}

@keyframes kioskSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes kioskFloatA {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(3vw, -2vh, 0);
  }
}

@keyframes kioskFloatB {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(-4vw, 2vh, 0);
  }
}

@keyframes kioskFloatC {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(2vw, -3vh, 0);
  }
}

@media (max-width: 1100px) {
  .quick-kiosk__hud {
    max-width: calc(100vw - 100px);
  }

  .quick-kiosk__hud-item--event {
    max-width: min(40vw, 18rem);
  }

  .quick-kiosk__log {
    top: auto;
    right: max(18px, calc(env(safe-area-inset-right, 0px) + 12px));
    left: max(18px, calc(env(safe-area-inset-left, 0px) + 12px));
    bottom: max(84px, calc(env(safe-area-inset-bottom, 0px) + 78px));
    width: auto;
    max-height: 13.5rem;
  }

  .quick-kiosk__status {
    max-width: calc(100vw - 36px);
    bottom: max(18px, calc(env(safe-area-inset-bottom, 0px) + 12px));
  }
}

@media (max-width: 720px) {
  .quick-kiosk__sheet-stage {
    align-items: flex-end;
  }

  .quick-kiosk__sheet,
  .quick-kiosk__sheet--handoff {
    width: 100%;
    max-height: min(88dvh, 42rem);
    border-radius: 1.75rem;
  }

  .quick-kiosk__content--standby {
    align-items: flex-start;
    text-align: left;
    padding-inline: 0.25rem;
  }

  .quick-kiosk__title {
    font-size: clamp(2.2rem, 10vw, 3.3rem);
  }

  .quick-kiosk__primary {
    width: 100%;
  }

  .quick-kiosk__sheet-header {
    align-items: flex-start;
  }

  .quick-kiosk__hud {
    width: calc(100vw - 104px);
    min-height: 54px;
    padding-inline: 0.95rem;
    gap: 0.7rem;
  }

  .quick-kiosk__hud-item {
    font-size: 0.82rem;
  }

  .quick-kiosk__hud-item--event {
    max-width: 38vw;
  }

  .quick-kiosk__event-top {
    align-items: flex-start;
    gap: 0.7rem;
  }

  .quick-kiosk__event-subline {
    align-items: flex-start;
    flex-direction: column;
    gap: 0.35rem;
  }

  .quick-kiosk__event-dot {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .quick-kiosk__feed-visual,
  .quick-kiosk__dismiss,
  .quick-kiosk__sheet,
  .quick-kiosk__primary,
  .quick-kiosk__ghost,
  .quick-kiosk__event-row,
  .kiosk-sheet-enter-active,
  .kiosk-sheet-leave-active,
  .kiosk-content-enter-active,
  .kiosk-content-leave-active,
  .kiosk-hud-enter-active,
  .kiosk-hud-leave-active,
  .kiosk-status-enter-active,
  .kiosk-status-leave-active,
  .kiosk-log-enter-active,
  .kiosk-log-leave-active,
  .kiosk-log-move {
    transition: none !important;
  }

  .quick-kiosk__spinner,
  .quick-kiosk__live-dot,
  .quick-kiosk__feed-orb {
    animation: none !important;
  }
}
</style>
