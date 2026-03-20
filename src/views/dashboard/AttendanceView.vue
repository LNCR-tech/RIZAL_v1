<template>
  <div class="attendance-page">
    <div class="attendance-shell">
      <template v-if="event">
        <div
          ref="stepTrackEl"
          class="step-track dashboard-enter dashboard-enter--1"
          role="progressbar"
          aria-label="Attendance progress"
          :aria-valuenow="progressValue"
          aria-valuemin="0"
          aria-valuemax="100"
          :class="{ 'step-track--bounce': trackBounce }"
        >
          <div class="step-track-progress" :style="{ width: `${trackFillPx}px` }"></div>

          <div class="step-node" :class="stepNodeClass(0)" :ref="(el) => setStepNode(el, 0)">
            <component :is="stepNodeIcon(0)" :size="16" />
          </div>
          <div class="step-node" :class="stepNodeClass(1)" :ref="(el) => setStepNode(el, 1)">
            <component :is="stepNodeIcon(1)" :size="16" />
          </div>
          <div class="step-node" :class="stepNodeClass(2)" :ref="(el) => setStepNode(el, 2)">
            <component :is="stepNodeIcon(2)" :size="16" />
          </div>

          <ChevronsRight v-if="flowStep === 'face'" class="step-scan-arrow" :size="15" />
        </div>

        <FaceScanPanel
          v-if="flowStep === 'face'"
          class="dashboard-enter dashboard-enter--2"
          :progress="faceScanProgress"
          :is-camera-ready="isCameraReady"
          :face-image-url="faceImageUrl"
          :show-error="showFaceError"
          :video-ref="setVideoEl"
          @retry="retryFaceScan"
        />

        <section v-else-if="flowStep === 'location'" class="step-section step-section--location dashboard-enter dashboard-enter--2">
          <p class="step-caption">Locating you for the event...</p>

          <div class="location-map">
            <iframe
              v-if="mapUrl"
              :key="mapUrl"
              class="location-map-frame"
              :src="mapUrl"
              loading="lazy"
              referrerpolicy="no-referrer-when-downgrade"
              aria-label="Your current location map"
            />
            <div v-else class="location-map-fallback" aria-label="Map not available">
              <div class="map-grid"></div>
            </div>

            <div class="location-card">
              <div class="location-card-left">
                <span class="location-card-label">Your</span>
                <span class="location-card-title">Location</span>
              </div>

              <div class="location-card-coords">
                <div class="coord-group">
                  <span class="coord-label">Latitude</span>
                  <span class="coord-value">{{ latitudeText }}</span>
                </div>
                <div class="coord-group">
                  <span class="coord-label">Longitude</span>
                  <span class="coord-value">{{ longitudeText }}</span>
                </div>
              </div>

              <button
                class="location-card-action"
                type="button"
                aria-label="Open location in Google Maps"
                :disabled="!mapDestination"
                @click="openInMaps"
              >
                <ArrowUpRight :size="15" />
              </button>
            </div>
          </div>

          <p v-if="showLocationError" class="location-hint">{{ locationErrorText }}</p>

          <div v-if="showLocationError" class="location-error-block">
            <button class="location-retry-btn" type="button" @click="retryLocationCheck">
              Try Again
            </button>
          </div>

          <button
            v-else
            class="location-next-btn"
            type="button"
            :disabled="locationStatus !== 'ok'"
            @click="goToSuccess"
          >
            Next
          </button>
        </section>

        <section v-else class="step-section step-section--success dashboard-enter dashboard-enter--3">
          <p class="success-caption">{{ successMessage }}</p>
          <button class="success-btn" type="button" @click="goBack">
            <span class="success-btn-icon">
              <ArrowRight :size="16" />
            </span>
            <span class="success-btn-text">Go Back</span>
          </button>
        </section>
      </template>

      <section v-else class="step-section step-section--success dashboard-enter dashboard-enter--2">
        <p class="success-caption">Event not found.</p>
        <button class="success-btn" type="button" @click="goBack">
          <span class="success-btn-icon">
            <ArrowRight :size="16" />
          </span>
          <span class="success-btn-text">Go Back</span>
        </button>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ScanFace,
  ShieldCheck,
  Zap,
  Check,
  ChevronsRight,
  ArrowUpRight,
  ArrowRight,
} from 'lucide-vue-next'
import FaceScanPanel from '@/components/attendance/FaceScanPanel.vue'
import { initFaceScanDetector, resetFaceScanDetector } from '@/composables/useFaceScanDetector.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import {
  recordFaceScanAttendance as postFaceScanAttendance,
  recordFaceScanTimeout as postFaceScanTimeout,
  resolveApiBaseUrl,
  verifyEventLocation,
} from '@/services/backendApi.js'

const route = useRoute()
const router = useRouter()
const {
  currentUser,
  ensureDashboardEvent,
  getDashboardEventById,
  hasAttendanceForEvent,
  refreshAttendanceRecords,
} = useDashboardSession()

const eventId = computed(() => Number(route.params.id))
const event = computed(() => getDashboardEventById(eventId.value))

const flowStep = ref('face')
const isRunning = ref(false)
const userCoords = ref(null)
const successReason = ref('recorded')
const stepTrackEl = ref(null)
const stepNodeEls = ref([null, null, null])
const trackWidthPx = ref(0)
const trackCenters = ref({ left: 0, middle: 0, right: 0 })
const locationStatus = ref('idle')
const locationError = ref('')
const videoEl = ref(null)
const capturedFaceDataUrl = ref('')
const mediaStream = ref(null)
const cameraState = ref('idle')
const videoReady = ref(false)
const faceDetected = ref(false)
const faceScanError = ref(false)
const faceScanProgress = ref(0)
let faceDetectRaf = null
let faceProgressRaf = null
let retryResolve = null
let cameraStartPromise = null
let faceDetectorInstance = null
let locationRetryResolve = null
const faceScanTimeoutMs = Number(import.meta.env.VITE_FACE_SCAN_TIMEOUT_MS ?? 3000)
const faceScanProgressMax = Number(import.meta.env.VITE_FACE_SCAN_PROGRESS_MAX ?? 82)
const faceScanProgressDuration = Number(
  import.meta.env.VITE_FACE_SCAN_PROGRESS_DURATION_MS ?? Math.round(faceScanTimeoutMs * 0.6)
)
const faceDetectMinFrames = Number(import.meta.env.VITE_FACE_SCAN_MIN_FRAMES ?? 1)
const faceDetectHoldMs = Number(import.meta.env.VITE_FACE_SCAN_DETECT_HOLD_MS ?? 700)
const faceScanVideoReadyTimeoutMs = Number(
  import.meta.env.VITE_FACE_SCAN_VIDEO_READY_TIMEOUT_MS ?? faceScanTimeoutMs
)
const faceScanGateEnabled = import.meta.env.VITE_FACE_SCAN_GATE !== 'false'
const allowUnsupportedFallback = import.meta.env.VITE_FACE_SCAN_ALLOW_UNSUPPORTED === 'true'
const allowDeniedFallback = import.meta.env.VITE_FACE_SCAN_ALLOW_DENIED === 'true'
const faceDetectorWasmBaseUrl =
  import.meta.env.VITE_FACE_DETECTOR_WASM_URL ||
  'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
const faceDetectorModelUrl =
  import.meta.env.VITE_FACE_DETECTOR_MODEL_URL ||
  'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite'
const faceDetectorMinConfidence = Number(import.meta.env.VITE_FACE_DETECTOR_MIN_CONFIDENCE ?? 0.5)
const faceDetectorSuppression = Number(import.meta.env.VITE_FACE_DETECTOR_SUPPRESSION ?? 0.3)
const faceDetectorIntervalMs = Number(import.meta.env.VITE_FACE_DETECTOR_INTERVAL_MS ?? 120)
const geolocationTimeoutMs = Number(import.meta.env.VITE_GEOLOCATION_TIMEOUT_MS ?? 6000)
const geolocationMaxAgeMs = Number(import.meta.env.VITE_GEOLOCATION_MAX_AGE_MS ?? 0)
const geolocationHighAccuracy = import.meta.env.VITE_GEOLOCATION_HIGH_ACCURACY !== 'false'

const steps = [
  { key: 'face', icon: ScanFace },
  { key: 'location', icon: ShieldCheck },
  { key: 'success', icon: Zap },
]

const stepIndex = computed(() => steps.findIndex((step) => step.key === flowStep.value))
const trackFillPx = computed(() => {
  const { middle } = trackCenters.value
  if (!trackWidthPx.value) return 0
  if (flowStep.value === 'face') {
    const end = middle || trackWidthPx.value * 0.5
    return end * (faceScanProgress.value / 100)
  }
  if (flowStep.value === 'location') {
    return middle || trackWidthPx.value * 0.5
  }
  return trackWidthPx.value
})
const progressValue = computed(() => {
  if (!trackWidthPx.value) return 0
  return Math.max(0, Math.round((trackFillPx.value / trackWidthPx.value) * 100))
})
const trackBounce = ref(false)

function stepNodeClass(index) {
  if (flowStep.value === 'success' || stepIndex.value > index) return 'step-node--done'
  if (stepIndex.value === index) return 'step-node--active'
  return 'step-node--pending'
}

function stepNodeIcon(index) {
  if (flowStep.value === 'success' || stepIndex.value > index) return Check
  return steps[index].icon
}

const faceImageUrl = computed(() =>
  currentUser.value?.avatar_url || currentUser.value?.profile_photo_url || ''
)

const isCameraReady = computed(() => cameraState.value === 'ready')
const showFaceError = computed(() =>
  flowStep.value === 'face' && faceScanError.value
)
const showLocationError = computed(() =>
  flowStep.value === 'location' && locationStatus.value === 'error'
)
const setVideoEl = (el) => {
  videoEl.value = el
}
const setStepNode = (el, index) => {
  if (el) {
    stepNodeEls.value[index] = el
  }
}

const eventGeo = computed(() => resolveEventGeo())

const mapCenter = computed(() => {
  const lat = Number(userCoords.value?.latitude)
  const lon = Number(userCoords.value?.longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null
  return { latitude: lat, longitude: lon }
})

const locationErrorText = computed(() => locationError.value || 'Unable to verify your location.')

const latitudeText = computed(() => {
  const lat = mapCenter.value?.latitude
  if (lat == null) return '--'
  return new Intl.NumberFormat('en-PH', { maximumFractionDigits: 5 }).format(lat)
})

const longitudeText = computed(() => {
  const lon = mapCenter.value?.longitude
  if (lon == null) return '--'
  return new Intl.NumberFormat('en-PH', { maximumFractionDigits: 5 }).format(lon)
})

const mapUrl = computed(() => {
  if (!mapCenter.value) return null
  const lat = mapCenter.value.latitude
  const lon = mapCenter.value.longitude
  const radius =
    Number.isFinite(eventGeo.value?.radius) && eventGeo.value.radius > 0
      ? Math.max(eventGeo.value.radius, 180)
      : 240

  const latDelta = radius / 111320
  const lonDelta = radius / (111320 * Math.cos((lat * Math.PI) / 180) || 1)
  const bbox = [
    (lon - lonDelta).toFixed(6),
    (lat - latDelta).toFixed(6),
    (lon + lonDelta).toFixed(6),
    (lat + latDelta).toFixed(6),
  ].join(',')

  return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat},${lon}`
})

const mapDestination = computed(() => {
  if (mapCenter.value) {
    return `${mapCenter.value.latitude},${mapCenter.value.longitude}`
  }
  if (Number.isFinite(eventGeo.value?.lat) && Number.isFinite(eventGeo.value?.lon)) {
    return `${eventGeo.value.lat},${eventGeo.value.lon}`
  }
  const fallback = event.value?.location?.trim()
  return fallback || ''
})

const apiBaseUrl = resolveApiBaseUrl()
const successMessage = computed(() =>
  successReason.value === 'existing'
    ? 'Attendance already recorded.'
    : 'Attendance recorded successfully.'
)

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function getBrowserLocation() {
  if (!('geolocation' in navigator)) return null

  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        resolve({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        })
      },
      () => resolve(null),
      {
        enableHighAccuracy: geolocationHighAccuracy,
        timeout: geolocationTimeoutMs,
        maximumAge: geolocationMaxAgeMs,
      }
    )
  })
}

function waitForLocationRetry() {
  return new Promise((resolve) => {
    locationRetryResolve = () => {
      locationRetryResolve = null
      resolve()
    }
  })
}

function resolveEventGeo() {
  const data = event.value
  if (!data) return null

  const lat =
    Number(data.geo_latitude ?? data.geoLatitude ?? data.latitude ?? data.location_latitude ?? data.locationLat)
  const lon =
    Number(data.geo_longitude ?? data.geoLongitude ?? data.longitude ?? data.location_longitude ?? data.locationLon)
  const radiusRaw =
    Number(data.geo_radius_m ?? data.geoRadiusM ?? data.radius_m ?? data.radiusM ?? data.location_radius_m)
  const radius = Number.isFinite(radiusRaw) ? radiusRaw : null

  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return { lat: null, lon: null, radius }
  }

  return { lat, lon, radius }
}

async function recordFaceScanAttendance() {
  const eventIdValue = eventId.value
  const studentIdValue = currentUser.value?.student_profile?.student_id
  const imageDataUrl = capturedFaceDataUrl.value
  if (!eventIdValue || !studentIdValue || !imageDataUrl) {
    throw new Error('A live face capture is required before attendance can be recorded.')
  }

  const token = localStorage.getItem('aura_token')
  const rawBase64 = imageDataUrl.includes(',') ? imageDataUrl.split(',')[1] : imageDataUrl
  const payload = {
    eventId: eventIdValue,
    studentId: String(studentIdValue),
    imageBase64: imageDataUrl,
    latitude: userCoords.value?.latitude ?? null,
    longitude: userCoords.value?.longitude ?? null,
    accuracyM: userCoords.value?.accuracy ?? null,
  }

  try {
    await postFaceScanAttendance(apiBaseUrl, token, payload)
  } catch {
    await postFaceScanAttendance(apiBaseUrl, token, {
      ...payload,
      imageBase64: rawBase64,
    })
  }
  await refreshAttendanceRecords({ event_id: eventIdValue })
}

async function recordFaceScanTimeout() {
  const eventIdValue = eventId.value
  const studentIdValue = currentUser.value?.student_profile?.student_id
  if (!eventIdValue || !studentIdValue) return

  const token = localStorage.getItem('aura_token')
  await postFaceScanTimeout(apiBaseUrl, token, {
    eventId: eventIdValue,
    studentId: String(studentIdValue),
  })
}

async function waitForLocationCheck() {
  while (true) {
    locationStatus.value = 'checking'
    locationError.value = ''

    const coords = await getBrowserLocation()
    if (!coords) {
      locationStatus.value = 'error'
      locationError.value = 'Location access is required to continue.'
      await waitForLocationRetry()
      continue
    }

    userCoords.value = {
      latitude: coords.latitude,
      longitude: coords.longitude,
      accuracy: coords.accuracy ?? null,
      capturedAt: new Date().toISOString(),
    }

    if (!event.value?.geo_required) {
      locationStatus.value = 'ok'
      return
    }

    try {
      const token = localStorage.getItem('aura_token')
      const verification = await verifyEventLocation(apiBaseUrl, token, eventId.value, {
        latitude: coords.latitude,
        longitude: coords.longitude,
        accuracy_m: coords.accuracy ?? null,
      })

      if (!verification?.ok) {
        locationStatus.value = 'error'
        locationError.value = verification?.reason || 'You are outside the allowed event area.'
        await waitForLocationRetry()
        continue
      }
    } catch (error) {
      locationStatus.value = 'error'
      locationError.value = error?.message || 'Unable to verify your location.'
      await waitForLocationRetry()
      continue
    }

    locationStatus.value = 'ok'
    return
  }
}

async function runAttendanceFlow() {
  if (isRunning.value) return
  isRunning.value = true

  try {
    flowStep.value = 'face'
    await nextTick()
    await startCamera()
    await waitForFaceDetection()
    capturedFaceDataUrl.value = captureVideoFrame()

    flowStep.value = 'location'
    stopCamera()
    await waitForLocationCheck()
    await recordFaceScanAttendance()
    flowStep.value = 'success'
  } catch (error) {
    const message = error?.message || 'Unable to record your attendance right now.'
    if (flowStep.value === 'location') {
      locationStatus.value = 'error'
      locationError.value = message
    } else {
      faceScanError.value = true
    }
  } finally {
    stopCamera()
    isRunning.value = false
  }
}

function openInMaps() {
  if (!mapDestination.value) return
  const url = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(mapDestination.value)}`
  window.open(url, '_blank', 'noopener')
}

function goBack() {
  router.back()
}

function retryFaceScan() {
  faceScanError.value = false
  faceDetected.value = false
  videoReady.value = false
  capturedFaceDataUrl.value = ''
  startCamera()
  if (retryResolve) {
    const resolve = retryResolve
    retryResolve = null
    resolve()
    return
  }
  if (flowStep.value === 'face') startFaceProgress()
}

function captureVideoFrame() {
  const el = videoEl.value
  if (!el || el.videoWidth <= 0 || el.videoHeight <= 0) {
    throw new Error('Unable to capture a face image.')
  }

  const size = Math.min(el.videoWidth, el.videoHeight)
  const sx = Math.max(0, (el.videoWidth - size) / 2)
  const sy = Math.max(0, (el.videoHeight - size) / 2)
  const canvas = document.createElement('canvas')
  canvas.width = 720
  canvas.height = 720
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('Unable to prepare the face image.')
  }

  ctx.drawImage(el, sx, sy, size, size, 0, 0, canvas.width, canvas.height)
  return canvas.toDataURL('image/jpeg', 0.92)
}

function retryLocationCheck() {
  locationError.value = ''
  locationStatus.value = 'checking'
  if (locationRetryResolve) {
    const resolve = locationRetryResolve
    locationRetryResolve = null
    resolve()
  }
}

function goToSuccess() {
  flowStep.value = 'success'
}

function waitForRetry() {
  return new Promise((resolve) => {
    retryResolve = () => {
      retryResolve = null
      resolve()
    }
  })
}

function waitForVideoReady() {
  if (cameraState.value === 'denied' || cameraState.value === 'unsupported') {
    return Promise.resolve(cameraState.value)
  }
  if (cameraState.value === 'ready' && videoReady.value) return Promise.resolve('ready')

  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      stopWatch()
      resolve('timeout')
    }, faceScanVideoReadyTimeoutMs)

    const stopWatch = watch([cameraState, videoReady], ([state, ready]) => {
      if (state === 'denied' || state === 'unsupported') {
        clearTimeout(timer)
        stopWatch()
        resolve(state)
        return
      }
      if (state === 'ready' && ready) {
        clearTimeout(timer)
        stopWatch()
        resolve('ready')
      }
    })
  })
}

async function ensureFaceDetector() {
  if (faceDetectorInstance) return true
  try {
    faceDetectorInstance = await initFaceScanDetector({
      wasmBaseUrl: faceDetectorWasmBaseUrl,
      modelAssetPath: faceDetectorModelUrl,
      minDetectionConfidence: faceDetectorMinConfidence,
      minSuppressionThreshold: faceDetectorSuppression,
      runningMode: 'VIDEO',
    })
    return Boolean(faceDetectorInstance)
  } catch {
    faceDetectorInstance = null
    resetFaceScanDetector()
    return false
  }
}

function stopFaceProgress() {
  if (faceProgressRaf) cancelAnimationFrame(faceProgressRaf)
  faceProgressRaf = null
}

function animateFaceProgress(target, duration) {
  stopFaceProgress()
  const start = faceScanProgress.value
  const delta = target - start
  const startTime = performance.now()

  const tick = (now) => {
    const t = Math.min(1, (now - startTime) / duration)
    const eased = 1 - Math.pow(1 - t, 3)
    faceScanProgress.value = Math.max(0, Math.min(100, start + delta * eased))
    if (t < 1) {
      faceProgressRaf = requestAnimationFrame(tick)
    }
  }

  faceProgressRaf = requestAnimationFrame(tick)
}

function startFaceProgress() {
  faceScanProgress.value = 0
  animateFaceProgress(faceScanProgressMax, faceScanProgressDuration)
}

function waitForFaceOrTimeout() {
  return new Promise((resolve) => {
    if (faceDetected.value) {
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
      stopFaceProgress()
    }

    timer = setTimeout(() => {
      cleanup()
      resolve('timeout')
    }, faceScanTimeoutMs)

    stopFaceWatch = watch(faceDetected, (val) => {
      if (!val) return
      cleanup()
      resolve('detected')
    })

    stopCameraWatch = watch(cameraState, (state) => {
      if (state === 'denied' || state === 'unsupported') {
        cleanup()
        resolve(state)
      }
    })
  })
}

async function waitForFaceDetection() {
  if (!faceScanGateEnabled) {
    animateFaceProgress(100, 240)
    await delay(240)
    return
  }

  while (true) {
    faceScanError.value = false

    const readyState = await waitForVideoReady()
    if (readyState !== 'ready') {
      faceScanError.value = true
      if (readyState === 'denied' && allowDeniedFallback) return
      await waitForRetry()
      continue
    }

    const detectorReady = await ensureFaceDetector()
    if (!detectorReady) {
      faceScanError.value = true
      if (allowUnsupportedFallback) return
      await waitForRetry()
      continue
    }

    startFaceDetection()
    startFaceProgress()
    const result = await waitForFaceOrTimeout()

    if (result === 'detected') {
      faceScanError.value = false
      animateFaceProgress(100, 320)
      await delay(320)
      stopFaceDetection()
      return
    }

    faceScanError.value = true
    if (result === 'timeout') {
      stopFaceDetection()
      recordFaceScanTimeout().catch(() => null)
    }
    if (result === 'denied' && allowDeniedFallback) return
    await waitForRetry()
  }
}

async function attachStreamToVideo() {
  if (!videoEl.value || !mediaStream.value) return false
  const el = videoEl.value

  el.muted = true
  el.autoplay = true
  el.playsInline = true

  if (el.srcObject !== mediaStream.value) {
    el.srcObject = mediaStream.value
  }

  videoReady.value = false
  stopFaceDetection()

  try {
    await el.play().catch(() => null)
  } catch {
    // Ignore play errors (autoplay restrictions are handled by user gesture).
  }

  if (el.readyState >= 2) {
    videoReady.value = true
    return true
  }

  return new Promise((resolve) => {
    let settled = false
    const finish = (ready) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      el.removeEventListener('loadeddata', onReady)
      el.removeEventListener('canplay', onReady)
      el.removeEventListener('error', onError)
      videoReady.value = ready
      resolve(ready)
    }
    const onReady = () => finish(true)
    const onError = () => finish(false)
    const timer = setTimeout(() => finish(false), faceScanVideoReadyTimeoutMs)

    el.addEventListener('loadeddata', onReady, { once: true })
    el.addEventListener('canplay', onReady, { once: true })
    el.addEventListener('error', onError, { once: true })
  })
}

async function startCamera() {
  if (!navigator?.mediaDevices?.getUserMedia) {
    cameraState.value = 'unsupported'
    return
  }

  if (cameraStartPromise) return cameraStartPromise

  cameraStartPromise = (async () => {
    if (!mediaStream.value) {
      cameraState.value = 'requesting'
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user' },
          audio: false,
        })
        mediaStream.value = stream
      } catch {
        cameraState.value = 'denied'
        videoReady.value = false
        return
      }
    }

    cameraState.value = 'ready'
    await attachStreamToVideo()
  })()

  try {
    await cameraStartPromise
  } finally {
    cameraStartPromise = null
  }
}

function stopCamera() {
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach((track) => track.stop())
    mediaStream.value = null
  }
  if (videoEl.value) {
    videoEl.value.srcObject = null
  }
  cameraState.value = 'idle'
  videoReady.value = false
  stopFaceDetection()
  stopFaceProgress()
}

function startFaceDetection() {
  if (!faceDetectorInstance || !videoEl.value) return
  stopFaceDetection()
  let detectionStreak = 0
  let lastFaceSeenAt = 0
  let lastDetectAt = 0

  const detect = (now) => {
    if (!videoEl.value || cameraState.value !== 'ready' || flowStep.value !== 'face') return
    if (now - lastDetectAt < faceDetectorIntervalMs) {
      faceDetectRaf = requestAnimationFrame(detect)
      return
    }
    lastDetectAt = now
    try {
      const result = faceDetectorInstance.detectForVideo(videoEl.value, now)
      const hasFace = Array.isArray(result?.detections) && result.detections.length > 0
      if (hasFace) {
        detectionStreak += 1
        lastFaceSeenAt = now
      } else {
        detectionStreak = 0
      }
      const held = lastFaceSeenAt > 0 && now - lastFaceSeenAt <= faceDetectHoldMs
      faceDetected.value = detectionStreak >= faceDetectMinFrames || held
    } catch {
      faceDetected.value = false
    }
    faceDetectRaf = requestAnimationFrame(detect)
  }

  faceDetectRaf = requestAnimationFrame(detect)
}

function stopFaceDetection() {
  if (faceDetectRaf) cancelAnimationFrame(faceDetectRaf)
  faceDetectRaf = null
  faceDetected.value = false
}

watch(flowStep, (step) => {
  if (step === 'face') {
    faceScanError.value = false
    return
  }
  if (step === 'location') {
    locationStatus.value = 'checking'
    locationError.value = ''
    return
  }
  retryResolve = null
  locationRetryResolve = null
  stopFaceProgress()
  faceScanProgress.value = 0
  stopCamera()
})

watch(
  () => flowStep.value,
  () => {
    trackBounce.value = false
    requestAnimationFrame(() => {
      trackBounce.value = true
      setTimeout(() => {
        trackBounce.value = false
      }, 360)
    })
    nextTick(updateTrackMetrics)
  }
)

watch(
  videoEl,
  (el) => {
    if (el && mediaStream.value) {
      attachStreamToVideo()
    }
  },
  { flush: 'post' }
)

function updateTrackMetrics() {
  const track = stepTrackEl.value
  if (!track) return
  const trackRect = track.getBoundingClientRect()
  if (!trackRect.width) return

  trackWidthPx.value = trackRect.width

  const centers = stepNodeEls.value.map((node) => {
    if (!node) return null
    const rect = node.getBoundingClientRect()
    return rect.left + rect.width / 2 - trackRect.left
  })

  trackCenters.value = {
    left: centers[0] ?? 0,
    middle: centers[1] ?? trackRect.width / 2,
    right: centers[2] ?? trackRect.width,
  }
}

let trackResizeObserver = null

onMounted(async () => {
  await ensureDashboardEvent(eventId.value).catch(() => null)
  if (!event.value) return

  if (hasAttendanceForEvent(eventId.value)) {
    successReason.value = 'existing'
    flowStep.value = 'success'
  } else {
    successReason.value = 'recorded'
    runAttendanceFlow()
  }

  nextTick(updateTrackMetrics)
  if (stepTrackEl.value && typeof ResizeObserver !== 'undefined') {
    trackResizeObserver = new ResizeObserver(() => {
      updateTrackMetrics()
    })
    trackResizeObserver.observe(stepTrackEl.value)
  }
})

onBeforeUnmount(() => {
  stopCamera()
  retryResolve = null
  locationRetryResolve = null
  resetFaceScanDetector()
  faceDetectorInstance = null
  trackResizeObserver?.disconnect?.()
  trackResizeObserver = null
})
</script>

<style scoped>
.attendance-page {
  min-height: 100vh;
  padding: 32px 20px 160px;
  background: var(--color-bg, #f5f4ef);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  --track-width: min(320px, 92%);
  --track-height: 46px;
  --node-size: 34px;
  --track-pad: 8px;
  --scan-size: clamp(240px, 78vw, 300px);
  --scan-thickness: 9px;
  --scan-gap: 8px;
  --scan-media: calc(var(--scan-size) - (var(--scan-thickness) * 2) - (var(--scan-gap) * 2));
  --scan-start-angle: -90deg;
  --map-width: 341px;
  --map-height: 367px;
  --map-radius: 25px;
  --map-card-width: 332px;
  --map-card-height: 147px;
  --map-card-radius: 25px;
  --map-card-action-size: 49px;
  --map-card-bg: var(--color-primary, #aaff00);
  --map-card-text: var(--color-primary-text, #0a0a0a);
  --map-card-action-bg: var(--color-nav, #0a0a0a);
  --map-card-action-color: var(--color-surface, #ffffff);
  --map-card-shadow: 0 18px 26px rgba(0, 0, 0, 0.16);
}

.attendance-shell {
  width: 100%;
  max-width: 380px;
  min-height: calc(100vh - 32px - 160px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
}

.step-track {
  position: relative;
  width: var(--track-width);
  height: var(--track-height);
  background: #0a0a0a;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--track-pad);
  overflow: hidden;
}

.step-track-progress {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: var(--color-primary);
  border-radius: 999px;
  transition: width 0.45s cubic-bezier(0.22, 1, 0.36, 1);
  transform-origin: left center;
}

.step-node {
  position: relative;
  z-index: 2;
  width: var(--node-size);
  height: var(--node-size);
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0a0a0a;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.14);
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}

.step-node--active {
  color: #0a0a0a;
  transform: scale(1.05);
}

.step-node--done {
  color: var(--color-primary);
  transform: scale(1.03);
}

.step-node--pending {
  color: #0a0a0a;
  opacity: 0.75;
}

.step-scan-arrow {
  position: absolute;
  left: 33.5%;
  top: 50%;
  transform: translate(-50%, -50%);
  color: #0a0a0a;
  opacity: 0.65;
  z-index: 2;
}

.step-track--bounce .step-track-progress {
  animation: trackBounce 0.38s cubic-bezier(0.2, 0.8, 0.2, 1);
}

@keyframes trackBounce {
  0% {
    transform: scaleX(0.985);
  }
  55% {
    transform: scaleX(1.02);
  }
  100% {
    transform: scaleX(1);
  }
}

.step-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  text-align: center;
}

.step-section--location {
  gap: 12px;
  margin-top: 0;
  flex: 1;
  justify-content: center;
}

.step-section--success {
  align-self: stretch;
  gap: 12px;
  justify-content: flex-start;
  padding-top: 6px;
}

.step-caption {
  font-size: 13px;
  font-weight: 600;
  color: #5f5f5f;
  margin: 0;
}

.location-map {
  position: relative;
  width: min(var(--map-width), 100%);
  height: var(--map-height);
  border-radius: var(--map-radius);
  overflow: hidden;
  background: #dedede;
  margin-top: 8px;
  margin-bottom: 24px;
  align-self: center;
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.12);
  border: 1px solid #ececec;
}

.location-map-frame {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.location-map-fallback {
  position: relative;
  width: 100%;
  height: 100%;
  background: #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.map-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(#e0e0e0 1px, transparent 1px),
    linear-gradient(90deg, #e0e0e0 1px, transparent 1px);
  background-size: 18px 18px;
}

.location-card {
  position: absolute;
  left: 50%;
  bottom: 6px;
  width: min(var(--map-card-width), calc(100% - 8px));
  height: var(--map-card-height);
  transform: translateX(-50%);
  background: var(--map-card-bg);
  border-radius: var(--map-card-radius);
  padding: 18px 18px 18px 20px;
  display: grid;
  grid-template-columns: 84px minmax(0, 1fr) var(--map-card-action-size);
  column-gap: 18px;
  align-items: center;
  box-shadow: var(--map-card-shadow);
  color: var(--map-card-text);
}

.location-card-left {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 3px;
  min-width: 0;
  font-weight: 800;
  line-height: 1;
  align-self: stretch;
}

.location-card-label {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: -0.02em;
  opacity: 0.72;
}

.location-card-title {
  font-size: 15px;
  letter-spacing: -0.04em;
}

.location-card-coords {
  display: grid;
  gap: 8px;
  align-content: center;
  justify-items: start;
  min-width: 0;
}

.coord-label {
  font-size: 9px;
  font-weight: 500;
  line-height: 1.1;
  letter-spacing: -0.01em;
  opacity: 0.68;
}

.coord-value {
  font-size: 15px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.03em;
}

.coord-group {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.location-card-action {
  width: var(--map-card-action-size);
  height: var(--map-card-action-size);
  border-radius: 50%;
  border: none;
  background: var(--map-card-action-bg);
  color: var(--map-card-action-color);
  display: flex;
  align-items: center;
  justify-content: center;
  justify-self: end;
  align-self: center;
  flex-shrink: 0;
  cursor: pointer;
  box-shadow: 0 10px 18px rgba(0, 0, 0, 0.18);
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.location-card-action:active {
  transform: scale(0.95);
}

.location-card-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.location-hint {
  font-size: 9.5px;
  font-weight: 600;
  color: #d24848;
  margin: 0;
}

.location-next-btn {
  margin-top: 4px;
  border: none;
  background: #ffffff;
  color: #222222;
  font-size: 11px;
  font-weight: 600;
  padding: 8px 28px;
  border-radius: 999px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.2s ease;
}

.location-next-btn:active {
  transform: scale(0.97);
}

.location-next-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}

.location-error-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}

.location-error {
  font-size: 11px;
  font-weight: 700;
  color: #d24848;
  margin: 0;
}

.location-retry-btn {
  border: none;
  background: #ffffff;
  color: #222222;
  font-size: 11px;
  font-weight: 600;
  padding: 8px 24px;
  border-radius: 999px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: transform 0.15s ease;
}

.location-retry-btn:active {
  transform: scale(0.97);
}

.success-caption {
  font-size: 13px;
  font-weight: 700;
  color: #1a1a1a;
  text-align: center;
  margin: 0;
  max-width: 160px;
  line-height: 1.3;
  align-self: center;
}

.success-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  align-self: center;
  padding: 4px 14px 4px 4px;
  border-radius: 999px;
  border: none;
  background: var(--color-primary);
  color: #0a0a0a;
  cursor: pointer;
  box-shadow: 0 10px 18px rgba(0, 0, 0, 0.14);
  transition: transform 0.15s ease;
}

.success-btn:active {
  transform: scale(0.97);
}

.success-btn-icon {
  width: 29px;
  height: 29px;
  border-radius: 50%;
  background: #0a0a0a;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.success-btn-text {
  font-size: 8px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

@media (min-width: 768px) {
  .attendance-page {
    padding-top: 0;
    padding-bottom: 0;
    justify-content: center;
  }

  .attendance-shell {
    max-width: 380px;
    min-height: auto;
  }
}

</style>
