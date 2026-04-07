<template>
  <div class="quick-attendance">
    <div class="quick-attendance__shell">
      <header class="quick-attendance__header">
        <button class="quick-attendance__back" type="button" @click="goBack">
          <ArrowLeft :size="18" />
          <span>Back</span>
        </button>

        <div class="quick-attendance__headline">
          <p class="quick-attendance__eyebrow">Quick Attendance</p>
          <h1 class="quick-attendance__title">Public Face Attendance Kiosk</h1>
          <p class="quick-attendance__subtitle">
            Nearby geofenced events can record student sign in and sign out from the landing page without logging students into the web app.
          </p>
        </div>

        <button
          class="quick-attendance__action"
          type="button"
          :disabled="isRefreshingLocation"
          @click="loadNearbyEvents"
        >
          <RefreshCw :size="16" :class="{ 'quick-attendance__spin': isRefreshingLocation }" />
          <span>{{ isRefreshingLocation ? 'Locating...' : 'Share Location' }}</span>
        </button>
      </header>

      <section class="quick-attendance__steps">
        <article class="quick-attendance__step">
          <strong>1. Share location</strong>
          <span>{{ locationMessage }}</span>
        </article>

        <article class="quick-attendance__step">
          <strong>2. Choose event</strong>
          <span>{{ selectedEvent ? `${selectedEvent.name} is ready for ${formatPhaseLabel(selectedEvent.attendance_phase).toLowerCase()}.` : 'Select a nearby event after loading location.' }}</span>
        </article>

        <article class="quick-attendance__step">
          <strong>3. Scan faces</strong>
          <span>{{ scanStatus }}</span>
        </article>
      </section>

      <div class="quick-attendance__layout">
        <section class="quick-attendance__panel">
          <div class="quick-attendance__panel-header">
            <div>
              <p class="quick-attendance__panel-eyebrow">Nearby Events</p>
              <h2 class="quick-attendance__panel-title">Choose an active public attendance event</h2>
            </div>
          </div>

          <div v-if="nearbyEvents.length" class="quick-attendance__event-list">
            <button
              v-for="event in nearbyEvents"
              :key="event.id"
              class="quick-attendance__event-card"
              :class="{ 'quick-attendance__event-card--selected': event.id === selectedEventId }"
              type="button"
              @click="handleSelectEvent(event)"
            >
              <div class="quick-attendance__event-top">
                <strong>{{ event.name }}</strong>
                <span class="quick-attendance__event-phase">{{ formatPhaseLabel(event.attendance_phase) }}</span>
              </div>

              <p class="quick-attendance__event-school">{{ event.school_name }}</p>
              <p class="quick-attendance__event-location">{{ event.location }}</p>

              <div class="quick-attendance__event-meta">
                <span>{{ formatDateTime(event.start_datetime) }}</span>
                <span>{{ formatDistance(event.distance_m) }} away</span>
              </div>

              <div class="quick-attendance__event-scope">
                <Compass :size="14" />
                <span>{{ event.scope_label }}</span>
              </div>
            </button>
          </div>

          <div v-else class="quick-attendance__empty">
            No nearby public attendance events are open for scanning right now.
          </div>
        </section>

        <section class="quick-attendance__panel">
          <div class="quick-attendance__panel-header">
            <div>
              <p class="quick-attendance__panel-eyebrow">Live Camera Scanner</p>
              <h2 class="quick-attendance__panel-title">Start the camera and arm the scan</h2>
            </div>
          </div>

          <div class="quick-attendance__scanner-card">
            <div class="quick-attendance__scanner-meta">
              <div>
                <strong>{{ selectedEvent?.name || 'No event selected' }}</strong>
                <span>
                  {{ selectedEvent ? `${formatPhaseLabel(selectedEvent.attendance_phase)} is active for ${selectedEvent.scope_label}.` : 'Choose a nearby event to activate the kiosk scanner.' }}
                </span>
              </div>

              <div class="quick-attendance__scanner-actions">
                <button
                  class="quick-attendance__scanner-button"
                  type="button"
                  @click="toggleCamera"
                >
                  <Camera :size="16" />
                  <span>{{ cameraOn ? 'Stop Camera' : 'Start Camera' }}</span>
                </button>

                <button
                  class="quick-attendance__scanner-button quick-attendance__scanner-button--primary"
                  :class="{ 'quick-attendance__scanner-button--armed': scanArmed }"
                  type="button"
                  :disabled="!selectedEvent || !location || !cameraOn"
                  @click="toggleScanArmed"
                >
                  <component :is="scanArmed ? PauseCircle : PlayCircle" :size="16" />
                  <span>{{ scanArmed ? 'Pause Scan' : 'Arm Live Scan' }}</span>
                </button>
              </div>
            </div>

            <div class="quick-attendance__camera-shell">
              <video
                ref="videoEl"
                class="quick-attendance__camera"
                autoplay
                muted
                playsinline
              />

              <div v-if="!cameraOn" class="quick-attendance__camera-placeholder">
                <Camera :size="28" />
                <p>Start the camera, keep the device inside the event geofence, and arm the live scan.</p>
              </div>
            </div>

            <canvas ref="canvasEl" class="quick-attendance__canvas" aria-hidden="true" />

            <div class="quick-attendance__status" :class="`quick-attendance__status--${scanStatusTone}`">
              <component :is="scanStatusTone === 'success' ? CheckCircle2 : LocateFixed" :size="16" />
              <span>{{ scanStatus }}</span>
            </div>

            <div class="quick-attendance__metrics">
              <div class="quick-attendance__metric">
                <span>Location accuracy</span>
                <strong>{{ formatDistance(location?.accuracyM) }}</strong>
              </div>

              <div class="quick-attendance__metric">
                <span>Scan cooldown</span>
                <strong>{{ scanCooldownSeconds }}s</strong>
              </div>

              <div class="quick-attendance__metric">
                <span>Last scan</span>
                <strong>{{ lastScanAt ? formatDateTime(lastScanAt) : 'Waiting' }}</strong>
              </div>

              <div class="quick-attendance__metric">
                <span>Status</span>
                <strong>{{ scanBusy ? 'Scanning…' : scanArmed ? 'Armed' : 'Idle' }}</strong>
              </div>
            </div>
          </div>
        </section>
      </div>

      <section class="quick-attendance__panel">
        <div class="quick-attendance__panel-header">
          <div>
            <p class="quick-attendance__panel-eyebrow">Latest Scan Outcomes</p>
            <h2 class="quick-attendance__panel-title">Recent attendance results</h2>
          </div>

          <span class="quick-attendance__panel-meta">
            {{ lastScanAt ? `Updated ${formatDateTime(lastScanAt)}` : 'Waiting for first scan' }}
          </span>
        </div>

        <div v-if="outcomes.length" class="quick-attendance__outcome-list">
          <article
            v-for="(outcome, index) in outcomes"
            :key="`${outcome.student_id || 'unknown'}-${outcome.action}-${index}`"
            class="quick-attendance__outcome"
            :class="`quick-attendance__outcome--${outcomeTone(outcome.action)}`"
          >
            <div class="quick-attendance__outcome-top">
              <strong>{{ outcome.student_name || 'Unmatched face' }}</strong>
              <span>{{ outcome.action.replace(/_/g, ' ') }}</span>
            </div>

            <small v-if="outcome.student_id">{{ outcome.student_id }}</small>
            <p>{{ outcome.message }}</p>

            <div class="quick-attendance__outcome-meta">
              <span>Confidence: {{ typeof outcome.confidence === 'number' ? outcome.confidence.toFixed(3) : 'N/A' }}</span>
              <span>Liveness: {{ outcome.liveness?.label || 'N/A' }}</span>
              <span>Distance: {{ formatDistance(outcome.distance) }}</span>
            </div>
          </article>
        </div>

        <div v-else class="quick-attendance__empty">
          Live scan outcomes will appear here after the first processed frame.
        </div>

        <div v-if="cooldownEntries.length" class="quick-attendance__cooldowns">
          <strong>Cooldown Window</strong>
          <div class="quick-attendance__cooldown-list">
            <span v-for="entry in cooldownEntries" :key="entry.studentId">
              {{ (entry.studentName || entry.studentId).trim() }} · {{ formatCooldownSeconds(entry.expiresAt) }}s
            </span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeMount, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft,
  Camera,
  CheckCircle2,
  Compass,
  LocateFixed,
  PauseCircle,
  PlayCircle,
  RefreshCw,
} from 'lucide-vue-next'
import { applyTheme, loadUnbrandedTheme } from '@/config/theme.js'
import { getCurrentPositionOrThrow } from '@/services/devicePermissions.js'
import {
  describePublicAttendanceError,
  fetchNearbyPublicAttendanceEvents,
  resolvePublicAttendanceRetryAfterMs,
  submitPublicAttendanceScan,
} from '@/services/publicAttendance.js'

const router = useRouter()
const videoEl = ref(null)
const canvasEl = ref(null)

const location = ref(null)
const locationMessage = ref('Allow location access to load nearby public attendance events.')
const isRefreshingLocation = ref(false)
const nearbyEvents = ref([])
const selectedEventId = ref(null)
const scanCooldownSeconds = ref(8)
const scanStatus = ref('Select a nearby event after loading location, then start the camera and arm the live scan.')
const scanStatusTone = ref('info')
const cameraOn = ref(false)
const scanArmed = ref(false)
const scanBusy = ref(false)
const outcomes = ref([])
const cooldownEntries = ref([])
const lastScanAt = ref('')

let mediaStream = null
let scanTimeoutId = 0
let cooldownIntervalId = 0
let cooldownByStudent = {}

const COOLDOWN_ACTIONS = new Set([
  'time_in',
  'time_out',
  'already_signed_in',
  'already_signed_out',
  'cooldown_skipped',
])

const selectedEvent = computed(() => (
  nearbyEvents.value.find((event) => Number(event.id) === Number(selectedEventId.value)) || null
))

onBeforeMount(() => {
  applyTheme(loadUnbrandedTheme())
})

onMounted(() => {
  cooldownIntervalId = window.setInterval(() => {
    syncCooldownEntries()
  }, 1000)
})

onBeforeUnmount(() => {
  stopScanLoop()
  stopCamera()

  if (cooldownIntervalId) {
    window.clearInterval(cooldownIntervalId)
    cooldownIntervalId = 0
  }
})

function goBack() {
  router.push({ name: 'Login' })
}

function formatDateTime(value) {
  if (!value) return 'N/A'

  try {
    return new Date(value).toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  } catch {
    return 'N/A'
  }
}

function formatDistance(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return 'N/A'
  return `${normalized.toFixed(normalized < 10 ? 1 : 0)} m`
}

function formatPhaseLabel(phase) {
  return String(phase || '').trim().toLowerCase() === 'sign_out' ? 'Sign Out' : 'Sign In'
}

function formatCooldownSeconds(expiresAt) {
  return Math.max(0, Math.ceil((Number(expiresAt) - Date.now()) / 1000))
}

function outcomeTone(action) {
  if (['time_in', 'time_out'].includes(action)) return 'success'
  if (['liveness_failed', 'out_of_scope', 'no_match', 'rejected'].includes(action)) return 'error'
  return 'info'
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

function syncCooldownEntries() {
  const now = Date.now()
  const nextEntries = Object.values(cooldownByStudent)
    .filter((entry) => Number(entry?.expiresAt) > now)
    .sort((left, right) => Number(left.expiresAt) - Number(right.expiresAt))

  cooldownByStudent = Object.fromEntries(nextEntries.map((entry) => [entry.studentId, entry]))
  cooldownEntries.value = nextEntries
  return nextEntries.map((entry) => entry.studentId)
}

async function loadNearbyEvents() {
  isRefreshingLocation.value = true
  scanStatusTone.value = 'info'
  scanStatus.value = 'Finding your location and loading nearby attendance events...'
  scanArmed.value = false
  stopScanLoop()

  try {
    const position = await getCurrentPositionOrThrow({
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0,
    })

    const nextLocation = {
      latitude: position.latitude,
      longitude: position.longitude,
      accuracyM: position.accuracy,
      resolvedAt: position.capturedAt || new Date().toISOString(),
    }

    const response = await fetchNearbyPublicAttendanceEvents(nextLocation)

    location.value = nextLocation
    locationMessage.value = `Location updated at ${formatDateTime(nextLocation.resolvedAt)} with ${formatDistance(nextLocation.accuracyM)} accuracy.`
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

    const selected = response.events.find((event) => Number(event.id) === Number(selectedEventId.value)) || response.events[0]
    scanStatus.value = selected?.phase_message || `Found ${response.events.length} nearby event${response.events.length === 1 ? '' : 's'}.`
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

function handleSelectEvent(event) {
  selectedEventId.value = event.id
  outcomes.value = []
  lastScanAt.value = ''
  scanStatus.value = event.phase_message || `${event.name} is ready for ${formatPhaseLabel(event.attendance_phase).toLowerCase()}.`
  scanStatusTone.value = 'info'
  scanArmed.value = false
  stopScanLoop()
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

async function startCamera() {
  if (mediaStream) return

  if (!navigator?.mediaDevices?.getUserMedia) {
    throw new Error('Camera access is not supported on this browser.')
  }

  const stream = await navigator.mediaDevices.getUserMedia({
    audio: false,
    video: {
      facingMode: 'user',
    },
  })

  mediaStream = stream

  if (videoEl.value) {
    videoEl.value.srcObject = stream
    await waitForVideoReady(videoEl.value)
    await videoEl.value.play().catch(() => null)
  }

  cameraOn.value = true
}

function stopCamera() {
  stopScanLoop()
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

async function toggleCamera() {
  if (cameraOn.value) {
    stopCamera()
    scanStatus.value = selectedEvent.value
      ? 'Camera stopped. Start the camera again to continue public attendance scanning.'
      : 'Camera stopped.'
    scanStatusTone.value = 'info'
    return
  }

  try {
    await startCamera()
    scanStatus.value = selectedEvent.value
      ? 'Camera is live. Arm the scan when you are ready.'
      : 'Camera is live. Choose a nearby event to arm the scan.'
    scanStatusTone.value = 'info'
  } catch (error) {
    cameraOn.value = false
    scanStatus.value = humanizeCameraError(error)
    scanStatusTone.value = 'error'
  }
}

function toggleScanArmed() {
  if (!cameraOn.value || !selectedEvent.value || !location.value) return

  scanArmed.value = !scanArmed.value
  if (!scanArmed.value) {
    stopScanLoop()
    scanStatus.value = 'Live scan paused.'
    scanStatusTone.value = 'info'
    return
  }

  scanStatus.value = 'Live scan armed. Keep faces inside the camera frame.'
  scanStatusTone.value = 'info'
  scheduleNextScan(0)
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

async function runScanCycle() {
  if (!scanArmed.value || !cameraOn.value || !selectedEvent.value || !location.value || scanBusy.value) {
    return
  }

  scanBusy.value = true

  try {
    const frameBlob = await captureFrameBlob()
    const activeCooldownStudentIds = syncCooldownEntries()
    const response = await submitPublicAttendanceScan({
      eventId: selectedEvent.value.id,
      imageBlob: frameBlob,
      location: location.value,
      cooldownStudentIds: activeCooldownStudentIds,
    })

    const now = Date.now()
    for (const outcome of response.outcomes) {
      if (!outcome.student_id || !COOLDOWN_ACTIONS.has(outcome.action)) continue

      cooldownByStudent[outcome.student_id] = {
        studentId: outcome.student_id,
        studentName: outcome.student_name || null,
        expiresAt: now + (response.scan_cooldown_seconds * 1000),
      }
    }

    syncCooldownEntries()
    scanCooldownSeconds.value = response.scan_cooldown_seconds
    outcomes.value = response.outcomes
    lastScanAt.value = new Date().toISOString()
    scanStatus.value = primaryOutcomeMessage(response.outcomes, response.message)
    scanStatusTone.value = toneFromOutcomes(response.outcomes)

    scheduleNextScan(1100)
  } catch (error) {
    scanStatus.value = describePublicAttendanceError(error)
    scanStatusTone.value = 'error'
    scheduleNextScan(resolvePublicAttendanceRetryAfterMs(error, 1600))
  } finally {
    scanBusy.value = false
  }
}

function scheduleNextScan(delayMs = 0) {
  stopScanLoop()

  if (!scanArmed.value || !cameraOn.value || !selectedEvent.value || !location.value) {
    return
  }

  scanTimeoutId = window.setTimeout(() => {
    scanTimeoutId = 0
    void runScanCycle()
  }, Math.max(0, Number(delayMs) || 0))
}
</script>

<style scoped>
.quick-attendance {
  min-height: 100vh;
  background: var(--color-bg);
  color: var(--color-text-primary);
  font-family: 'Manrope', sans-serif;
  padding: 28px 20px 40px;
}

.quick-attendance__shell {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.quick-attendance__header,
.quick-attendance__panel {
  border-radius: 28px;
  padding: 18px;
  background: var(--aura-glass-bg);
  backdrop-filter: blur(var(--nav-glass-blur));
  -webkit-backdrop-filter: blur(var(--nav-glass-blur));
  border: 1px solid var(--aura-glass-border);
  box-shadow: var(--aura-shadow-soft);
}

.quick-attendance__step,
.quick-attendance__scanner-card,
.quick-attendance__event-card,
.quick-attendance__outcome,
.quick-attendance__empty,
.quick-attendance__cooldowns {
  border: 1px solid var(--color-surface-border);
  background: var(--color-surface);
}

.quick-attendance__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.quick-attendance__back,
.quick-attendance__action,
.quick-attendance__scanner-button {
  min-height: 44px;
  border-radius: 999px;
  border: 1px solid var(--color-surface-border-strong);
  background: var(--color-surface);
  color: var(--color-text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 800;
  transition: all 0.2s ease;
}

.quick-attendance__back:hover,
.quick-attendance__action:hover,
.quick-attendance__scanner-button:hover {
  background: var(--color-field-surface);
  transform: translateY(-1px);
}

.quick-attendance__scanner-button--primary,
.quick-attendance__action {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-primary-text);
}

.quick-attendance__scanner-button--primary:hover,
.quick-attendance__action:hover {
  background: var(--color-primary-dark);
}

.quick-attendance__scanner-button--armed {
  background: var(--color-surface-border);
  color: var(--color-text-primary);
  border-color: var(--color-surface-border-strong);
}

.quick-attendance__back:disabled,
.quick-attendance__action:disabled,
.quick-attendance__scanner-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.quick-attendance__headline {
  flex: 1;
  min-width: 0;
}

.quick-attendance__eyebrow,
.quick-attendance__panel-eyebrow {
  margin: 0 0 6px;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
}

.quick-attendance__title,
.quick-attendance__panel-title {
  margin: 0;
  font-size: clamp(24px, 4vw, 34px);
  line-height: 1.05;
  letter-spacing: -0.04em;
  color: var(--color-text-primary);
}

.quick-attendance__subtitle {
  margin: 10px 0 0;
  max-width: 620px;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.quick-attendance__steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.quick-attendance__step {
  border-radius: 24px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
}

.quick-attendance__step strong {
  font-size: 14px;
  color: var(--color-text-primary);
}

.quick-attendance__step span,
.quick-attendance__panel-meta {
  font-size: 13px;
  line-height: 1.45;
  color: var(--color-text-secondary);
}

.quick-attendance__layout {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
  gap: 18px;
}

.quick-attendance__panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.quick-attendance__panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.quick-attendance__event-list,
.quick-attendance__outcome-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-attendance__event-card,
.quick-attendance__outcome,
.quick-attendance__empty,
.quick-attendance__cooldowns,
.quick-attendance__scanner-card {
  border-radius: 24px;
  padding: 18px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.quick-attendance__event-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-align: left;
  cursor: pointer;
}

.quick-attendance__event-card:hover {
  transform: scale(1.01);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.quick-attendance__event-card--selected {
  background: var(--color-primary);
  color: var(--color-primary-text);
  border-color: var(--color-primary-dark);
}

.quick-attendance__event-card--selected .quick-attendance__event-school,
.quick-attendance__event-card--selected .quick-attendance__event-location,
.quick-attendance__event-card--selected .quick-attendance__event-meta,
.quick-attendance__event-card--selected .quick-attendance__event-scope {
  color: var(--color-primary-text);
  opacity: 0.85;
}

.quick-attendance__event-top,
.quick-attendance__outcome-top,
.quick-attendance__scanner-meta {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.quick-attendance__event-phase {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid currentColor;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.quick-attendance__event-school,
.quick-attendance__event-location,
.quick-attendance__event-meta,
.quick-attendance__event-scope,
.quick-attendance__outcome p,
.quick-attendance__outcome small,
.quick-attendance__outcome-meta,
.quick-attendance__scanner-meta span {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--color-surface-text-secondary);
}

.quick-attendance__event-meta,
.quick-attendance__event-scope,
.quick-attendance__outcome-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.quick-attendance__scanner-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quick-attendance__scanner-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-attendance__camera-shell {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
  border: 2px solid transparent;
  background: var(--aura-mesh-primary);
  background-size: 200% 200%;
  animation: bg-shift 12s ease infinite;
  min-height: 280px;
  box-shadow: inset 0 4px 20px rgba(0,0,0,0.1);
}

.quick-attendance__camera-shell::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 22px;
  border: 1px solid var(--aura-iridescent-border);
  mask-image: linear-gradient(#fff 0 0), linear-gradient(#fff 0 0);
  -webkit-mask-image: linear-gradient(#fff 0 0), linear-gradient(#fff 0 0);
  -webkit-mask-clip: padding-box, border-box;
  mask-clip: padding-box, border-box;
  -webkit-mask-composite: destination-out;
  mask-composite: exclude;
  pointer-events: none;
}

@keyframes bg-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.quick-attendance__camera {
  width: 100%;
  min-height: 280px;
  object-fit: cover;
  display: block;
  border-radius: 22px;
}

.quick-attendance__camera-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  text-align: center;
  color: var(--color-surface-text);
  background: color-mix(in srgb, var(--color-surface) 60%, transparent);
  backdrop-filter: blur(8px);
}

.quick-attendance__camera-placeholder p {
  margin: 0;
  max-width: 280px;
  font-size: 14px;
  line-height: 1.5;
  font-weight: 600;
}

.quick-attendance__canvas {
  display: none;
}

.quick-attendance__status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 48px;
  border-radius: 16px;
  padding: 0 16px;
  font-size: 13.5px;
  font-weight: 700;
}

.quick-attendance__status--info {
  background: var(--color-field-surface);
  color: var(--color-text-primary);
}

.quick-attendance__status--success {
  background: var(--color-primary);
  color: var(--color-primary-text);
}

.quick-attendance__status--error {
  background: rgba(230, 0, 0, 0.08);
  color: #cc0000;
}

.quick-attendance__metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.quick-attendance__metric {
  border-radius: 18px;
  background: var(--color-bg);
  border: 1px solid var(--color-surface-border);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.quick-attendance__metric span {
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.quick-attendance__metric strong {
  font-size: 15px;
  color: var(--color-text-primary);
}

.quick-attendance__outcome--success {
  background: var(--color-primary);
  color: var(--color-primary-text);
  border-color: var(--color-primary-dark);
}

.quick-attendance__outcome--success p,
.quick-attendance__outcome--success small,
.quick-attendance__outcome--success .quick-attendance__outcome-meta,
.quick-attendance__outcome--success .quick-attendance__outcome-top span {
  color: var(--color-primary-text);
  opacity: 0.85;
}

.quick-attendance__outcome--error {
  background: rgba(230, 0, 0, 0.08);
  border-color: rgba(230, 0, 0, 0.15);
}

.quick-attendance__outcome--info {
  background: var(--color-field-surface);
}

.quick-attendance__cooldowns {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-attendance__cooldown-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-attendance__cooldown-list span {
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--color-field-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-surface-border);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.quick-attendance__spin {
  animation: quick-attendance-spin 0.9s linear infinite;
}

@keyframes quick-attendance-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 960px) {
  .quick-attendance__steps,
  .quick-attendance__layout,
  .quick-attendance__metrics {
    grid-template-columns: 1fr;
  }

  .quick-attendance__header,
  .quick-attendance__panel-header,
  .quick-attendance__scanner-meta {
    flex-direction: column;
  }

  .quick-attendance__action,
  .quick-attendance__back {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .quick-attendance {
    padding: 20px 14px 28px;
  }

  .quick-attendance__header,
  .quick-attendance__panel {
    border-radius: 24px;
    padding: 16px;
  }

  .quick-attendance__camera-shell,
  .quick-attendance__camera {
    min-height: 220px;
  }
}
</style>