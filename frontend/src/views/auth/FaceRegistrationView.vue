<template>
  <div class="face-gate-page">
    <div v-if="step === 'intro'" class="face-gate-shell face-gate-shell--intro">
      <section class="intro-card">
        <span class="intro-chip">{{ schoolName }}</span>
        <h1 class="intro-title">
          Hi {{ firstName }},<br>
          face is<br>
          unregistered<br>
          please register<br>
          now.
        </h1>
        <p class="intro-copy">
          We will use the same face-scan experience as attendance so future check-ins feel familiar.
        </p>

        <button class="register-pill" type="button" @click="beginEnrollment">
          <span class="register-pill__icon">
            <ArrowRight :size="18" />
          </span>
          <span class="register-pill__text">Register Now</span>
        </button>
      </section>
    </div>

    <div v-else class="face-gate-shell face-gate-shell--capture">
      <section class="capture-card">
        <header class="capture-header">
          <span class="capture-chip">Face Setup</span>
          <Transition name="title-fade" mode="out-in">
            <h2 class="capture-title" :key="captureTitle">{{ captureTitle }}</h2>
          </Transition>
        </header>

        <FaceScanPanel
          class="face-gate-panel"
          :caption="panelCaption"
          :progress="scanProgress"
          :is-camera-ready="panelCameraReady"
          :face-image-url="panelFaceImageUrl"
          :show-error="showRetry"
          :error-text="statusMessage"
          :video-ref="setVideoEl"
          @retry="retryEnrollment"
        />

        <p v-if="showStatusMessage" class="capture-status" :class="statusClass">{{ statusText }}</p>
      </section>
    </div>

    <button v-if="step === 'intro'" class="signout-link" type="button" @click="logout">
      Sign Out
    </button>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from 'lucide-vue-next'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { applyTheme, loadTheme } from '@/config/theme.js'
import { registerStudentFace } from '@/services/backendApi.js'
import { initFaceScanDetector, resetFaceScanDetector } from '@/composables/useFaceScanDetector.js'
import { getStoredAuthMeta, patchStoredAuthMeta } from '@/services/localAuth.js'
import FaceScanPanel from '@/components/attendance/FaceScanPanel.vue'

const router = useRouter()
const { logout } = useAuth()
const {
  apiBaseUrl,
  currentUser,
  initializeDashboardSession,
  needsFaceRegistration,
  schoolSettings,
} = useDashboardSession()

const step = ref('intro')
const statusState = ref('idle')
const statusMessage = ref('')
const capturedPreview = ref('')
const videoEl = ref(null)
const mediaStream = ref(null)
const videoReady = ref(false)
const cameraState = ref('idle')

let detectorInstance = null
let detectRaf = null
let captureTimeout = null
let detectStartedAt = 0
let detectionStreak = 0
let redirectTimeout = null

const firstName = computed(() => currentUser.value?.first_name?.trim() || 'there')
const schoolName = computed(() => (
  currentUser.value?.school_name?.trim() ||
  schoolSettings.value?.school_name?.trim() ||
  getStoredAuthMeta()?.schoolName ||
  'Your school'
))
const captureTitle = computed(() => {
  if (statusState.value === 'success') return 'All set!'
  if (statusState.value === 'submitting' || statusState.value === 'capturing') return 'Registering...'
  if (statusState.value === 'starting') return 'Preparing camera'
  if (statusState.value === 'detecting') return 'Scanning...'
  if (statusState.value === 'error') return 'Try again'
  return 'Register your face'
})
const captureCopy = computed(() => {
  if (statusState.value === 'success') {
    return 'Your face profile is saved. We are taking you straight to your dashboard.'
  }
  if (statusState.value === 'submitting' || statusState.value === 'capturing') {
    return 'Stay centered for a moment while we save a clean reference image.'
  }
  if (statusState.value === 'starting') {
    return 'We are warming up your camera and loading the same scan frame used for attendance.'
  }
  if (statusState.value === 'detecting') {
    return 'Use a well-lit angle and keep your face inside the frame so future attendance scans feel natural.'
  }
  if (statusState.value === 'error') {
    return 'Better lighting and a centered face usually fixes this on the next try.'
  }
  return 'Use the same school-branded scan flow that powers attendance check-ins.'
})
const panelCaption = computed(() => {
  if (statusState.value === 'success') return 'Face registered.'
  if (statusState.value === 'submitting' || statusState.value === 'capturing') return 'Hold still...'
  if (statusState.value === 'starting') return 'Warming up camera...'
  if (statusState.value === 'error') return 'Registration failed.'
  return 'Keep your face centered.'
})
const showRetry = computed(() => statusState.value === 'error')
const statusClass = computed(() => ({
  'capture-status--error': statusState.value === 'error',
  'capture-status--success': statusState.value === 'success',
}))
const panelCameraReady = computed(() => cameraState.value === 'ready' && !capturedPreview.value)
const panelFaceImageUrl = computed(() =>
  capturedPreview.value ||
  currentUser.value?.avatar_url ||
  currentUser.value?.profile_photo_url ||
  ''
)
const showStatusMessage = computed(() =>
  Boolean(statusText.value) && statusState.value === 'success'
)
const statusText = computed(() => {
  if (statusState.value === 'success') {
    return 'Face registered successfully. Redirecting to your dashboard...'
  }

  return statusMessage.value
})
const scanProgress = computed(() => {
  if (statusState.value === 'success') return 100
  if (statusState.value === 'submitting') return 88
  if (statusState.value === 'capturing') return 72
  if (statusState.value === 'detecting') return 46
  if (statusState.value === 'starting') return 18
  if (statusState.value === 'error') return 64
  return panelCameraReady.value ? 28 : 12
})

const faceDetectorWasmBaseUrl =
  import.meta.env.VITE_FACE_DETECTOR_WASM_URL ||
  'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
const faceDetectorModelUrl =
  import.meta.env.VITE_FACE_DETECTOR_MODEL_URL ||
  'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite'
const faceDetectorMinConfidence = Number(import.meta.env.VITE_FACE_DETECTOR_MIN_CONFIDENCE ?? 0.5)
const faceDetectorSuppression = Number(import.meta.env.VITE_FACE_DETECTOR_SUPPRESSION ?? 0.3)
const faceDetectorIntervalMs = Number(import.meta.env.VITE_FACE_DETECTOR_INTERVAL_MS ?? 200)
const detectTimeoutMs = Number(import.meta.env.VITE_FACE_ENROLL_DETECT_TIMEOUT_MS ?? 12000)
const captureDelayMs = Number(import.meta.env.VITE_FACE_ENROLL_CAPTURE_DELAY_MS ?? 450)

const setVideoEl = (el) => {
  videoEl.value = el
}

function applyRegistrationTheme() {
  const authMeta = getStoredAuthMeta()
  const fallbackSettings = {
    school_name: currentUser.value?.school_name || authMeta?.schoolName || null,
    school_code: currentUser.value?.school_code || authMeta?.schoolCode || null,
    logo_url: schoolSettings.value?.logo_url || authMeta?.logoUrl || null,
    primary_color: schoolSettings.value?.primary_color || authMeta?.primaryColor || '#0057B8',
    secondary_color: schoolSettings.value?.secondary_color || authMeta?.secondaryColor || '#FFD400',
    accent_color: schoolSettings.value?.accent_color || authMeta?.accentColor || '#000000',
  }

  applyTheme(loadTheme(fallbackSettings))
}

watch(
  () => needsFaceRegistration.value,
  (required) => {
    if (!required) {
      router.replace({ name: 'Home' })
    }
  }
)

watch(
  () => [
    currentUser.value?.school_name,
    currentUser.value?.school_code,
    schoolSettings.value?.primary_color,
    schoolSettings.value?.secondary_color,
    schoolSettings.value?.accent_color,
    schoolSettings.value?.logo_url,
  ],
  () => {
    applyRegistrationTheme()
  },
  { immediate: true }
)

onMounted(() => {
  applyRegistrationTheme()
  if (!needsFaceRegistration.value) {
    router.replace({ name: 'Home' })
  }
})

onBeforeUnmount(() => {
  clearTimers()
  stopFaceDetection()
  stopCamera()
  resetFaceScanDetector()
  detectorInstance = null
})

async function beginEnrollment() {
  step.value = 'capture'
  await nextTick()
  await startEnrollmentFlow()
}

async function retryEnrollment() {
  capturedPreview.value = ''
  await startEnrollmentFlow()
}

async function startEnrollmentFlow() {
  clearTimers()
  stopFaceDetection()
  stopCamera()

  statusState.value = 'starting'
  statusMessage.value = 'Starting camera...'
  videoReady.value = false
  detectionStreak = 0

  const cameraReady = await startCamera()
  if (!cameraReady) {
    setRegistrationError(
      cameraState.value === 'denied'
        ? 'Camera access is required to register your face.'
        : 'Camera is unavailable on this device.'
    )
    return
  }

  const detectorReady = await ensureFaceDetector()
  if (!detectorReady) {
    statusState.value = 'capturing'
    statusMessage.value = 'Hold still while we capture your face.'
    captureTimeout = setTimeout(() => {
      captureAndRegister()
    }, captureDelayMs + 500)
    return
  }

  statusState.value = 'detecting'
  statusMessage.value = 'Center your face inside the frame.'
  detectStartedAt = 0
  startFaceDetection()
}

async function ensureFaceDetector() {
  if (detectorInstance) return true

  try {
    detectorInstance = await initFaceScanDetector({
      wasmBaseUrl: faceDetectorWasmBaseUrl,
      modelAssetPath: faceDetectorModelUrl,
      minDetectionConfidence: faceDetectorMinConfidence,
      minSuppressionThreshold: faceDetectorSuppression,
      runningMode: 'VIDEO',
    })
    return Boolean(detectorInstance)
  } catch {
    detectorInstance = null
    resetFaceScanDetector()
    return false
  }
}

async function startCamera() {
  if (!navigator?.mediaDevices?.getUserMedia) {
    cameraState.value = 'unsupported'
    return false
  }

  cameraState.value = 'requesting'

  try {
    mediaStream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'user',
        width: { ideal: 720 },
        height: { ideal: 720 },
      },
      audio: false,
    })
  } catch {
    cameraState.value = 'denied'
    return false
  }

  const el = videoEl.value
  if (!el) {
    cameraState.value = 'unsupported'
    return false
  }

  el.srcObject = mediaStream.value
  el.muted = true
  el.autoplay = true
  el.playsInline = true

  try {
    await el.play().catch(() => null)
  } catch {
    // Ignore autoplay issues; ready state watcher below handles availability.
  }

  const ready = await waitForVideoReady(el)
  if (!ready) {
    cameraState.value = 'unsupported'
    return false
  }

  cameraState.value = 'ready'
  videoReady.value = true
  return true
}

function waitForVideoReady(el) {
  if (el.readyState >= 2) return Promise.resolve(true)

  return new Promise((resolve) => {
    let settled = false
    const finish = (nextValue) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      el.removeEventListener('loadeddata', handleReady)
      el.removeEventListener('canplay', handleReady)
      el.removeEventListener('error', handleError)
      resolve(nextValue)
    }

    const handleReady = () => finish(true)
    const handleError = () => finish(false)
    const timer = setTimeout(() => finish(false), 8000)

    el.addEventListener('loadeddata', handleReady, { once: true })
    el.addEventListener('canplay', handleReady, { once: true })
    el.addEventListener('error', handleError, { once: true })
  })
}

function startFaceDetection() {
  stopFaceDetection()
  detectStartedAt = 0
  detectionStreak = 0

  const detect = (now) => {
    if (!videoEl.value || !detectorInstance || statusState.value === 'submitting') return

    if (!detectStartedAt) detectStartedAt = now
    if (now - detectStartedAt > detectTimeoutMs) {
      setRegistrationError('No face detected. Please try again in a brighter area.')
      return
    }

    try {
      const result = detectorInstance.detectForVideo(videoEl.value, now)
      const hasFace = Array.isArray(result?.detections) && result.detections.length > 0
      detectionStreak = hasFace ? detectionStreak + 1 : 0

      if (detectionStreak >= 2) {
        statusState.value = 'capturing'
        statusMessage.value = 'Face detected. Registering...'
        stopFaceDetection()
        captureTimeout = setTimeout(() => {
          captureAndRegister()
        }, captureDelayMs)
        return
      }
    } catch {
      setRegistrationError('Face detection failed. Please try again.')
      return
    }

    captureTimeout = setTimeout(() => {
      detectRaf = requestAnimationFrame(detect)
    }, faceDetectorIntervalMs)
  }

  detectRaf = requestAnimationFrame(detect)
}

function stopFaceDetection() {
  if (detectRaf) cancelAnimationFrame(detectRaf)
  detectRaf = null
  if (captureTimeout) clearTimeout(captureTimeout)
  captureTimeout = null
}

function stopCamera() {
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach((track) => track.stop())
    mediaStream.value = null
  }
  if (videoEl.value) {
    videoEl.value.srcObject = null
  }
  videoReady.value = false
  cameraState.value = 'idle'
}

function clearTimers() {
  if (captureTimeout) clearTimeout(captureTimeout)
  captureTimeout = null
  if (redirectTimeout) clearTimeout(redirectTimeout)
  redirectTimeout = null
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

async function captureAndRegister() {
  try {
    statusState.value = 'submitting'
    statusMessage.value = 'Registering your face...'

    const imageDataUrl = captureVideoFrame()
    const rawBase64 = imageDataUrl.includes(',') ? imageDataUrl.split(',')[1] : imageDataUrl
    capturedPreview.value = imageDataUrl

    stopCamera()

    const token = localStorage.getItem('aura_token')
    try {
      await registerStudentFace(apiBaseUrl.value, token, imageDataUrl)
    } catch {
      await registerStudentFace(apiBaseUrl.value, token, rawBase64)
    }

    patchStoredAuthMeta({
      faceReferenceEnrolled: true,
    })

    await initializeDashboardSession(true)
    if (needsFaceRegistration.value) {
      throw new Error('Face registration was saved, but the account is still marked as unregistered.')
    }

    statusState.value = 'success'
    statusMessage.value = 'Face registered successfully. Redirecting to your dashboard...'
    redirectTimeout = setTimeout(() => {
      router.replace({ name: 'Home' })
    }, 900)
  } catch (error) {
    setRegistrationError(error?.message || 'Unable to register your face right now.')
  }
}

function setRegistrationError(message) {
  clearTimers()
  stopFaceDetection()
  stopCamera()
  statusState.value = 'error'
  statusMessage.value = message
}
</script>

<style scoped>
.face-gate-page {
  --scan-size: clamp(244px, 70vw, 292px);
  --scan-thickness: 9px;
  --scan-gap: 8px;
  --scan-media: calc(var(--scan-size) - (var(--scan-thickness) * 2) - (var(--scan-gap) * 2));
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: var(--color-bg, #ebebeb);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 34px 24px 28px;
  font-family: 'Manrope', sans-serif;
}

.face-gate-shell {
  position: relative;
  z-index: 1;
  width: min(100%, 420px);
  display: flex;
  flex-direction: column;
}

.face-gate-shell--intro {
  align-items: stretch;
}

.face-gate-shell--capture {
  align-items: center;
}

.intro-card,
.capture-card {
  width: 100%;
  border-radius: 32px;
  padding: 28px 24px 24px;
  background: transparent;
  border: none;
  box-shadow: none;
  backdrop-filter: none;
}

.intro-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 18px;
}

.capture-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

.intro-chip,
.capture-chip {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary, #0057b8) 18%, #ffffff 82%);
  color: color-mix(in srgb, var(--color-primary, #0057b8) 56%, #0a0a0a 44%);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.capture-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  text-align: center;
}

.intro-title {
  margin: 0;
  font-size: clamp(27px, 8vw, 44px);
  line-height: 0.96;
  letter-spacing: -0.05em;
  font-weight: 700;
  color: #0a0a0a;
}

.intro-copy,
.capture-copy {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #5b5b54;
}

.capture-title {
  margin: 0;
  font-size: clamp(24px, 7vw, 30px);
  line-height: 1;
  letter-spacing: -0.04em;
  font-weight: 700;
  color: #111111;
}

.title-fade-enter-active,
.title-fade-leave-active {
  transition: opacity 0.22s ease;
}

.title-fade-enter-from,
.title-fade-leave-to {
  opacity: 0;
}

.register-pill {
  display: inline-flex;
  align-items: center;
  gap: 18px;
  min-height: 58px;
  padding: 4px 22px 4px 4px;
  border: none;
  border-radius: 999px;
  background: var(--color-primary, #0057b8);
  color: var(--color-primary-text, #ffffff);
  cursor: pointer;
  font-family: 'Manrope', sans-serif;
  transition: transform 0.16s ease;
}

.register-pill:active,
.signout-link:active {
  transform: scale(0.97);
}

.register-pill__icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: var(--color-nav, #0a0a0a);
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.register-pill__text {
  font-size: 13px;
  font-weight: 700;
}

.face-gate-panel {
  width: 100%;
}

.capture-status {
  width: min(100%, 276px);
  min-height: 20px;
  margin: -2px 0 0;
  font-size: 12.5px;
  line-height: 1.4;
  font-weight: 600;
  color: #5f5f5f;
  text-align: center;
}

.capture-status--error {
  color: #d24848;
}

.capture-status--success {
  color: color-mix(in srgb, var(--color-primary, #0057b8) 52%, #111111 48%);
}

.signout-link {
  margin-top: 24px;
  border: none;
  background: transparent;
  color: color-mix(in srgb, var(--color-primary, #0057b8) 34%, #4d4d47 66%);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.face-gate-panel :deep(.face-scan-section) {
  gap: 16px;
}

.face-gate-panel :deep(.step-caption) {
  font-size: 14px;
  line-height: 1.35;
  font-weight: 600;
  color: #1d1d18;
  max-width: 250px;
}

.face-gate-panel :deep(.face-scan) {
  margin-top: 0;
}

.face-gate-panel :deep(.scan-ring-base) {
  stroke: color-mix(in srgb, var(--color-primary, #0057b8) 12%, #fff7d7 88%);
}

.face-gate-panel :deep(.scan-ring-progress) {
  stroke: var(--color-primary, #0057b8);
}

.face-gate-panel :deep(.scan-ring-dot) {
  fill: #111111;
}

.face-gate-panel :deep(.scan-media) {
  background: var(--color-surface, #ffffff);
  box-shadow: none;
}

.face-gate-panel :deep(.scan-video) {
  transform: scaleX(-1);
}

.face-gate-panel :deep(.scan-photo--placeholder) {
  color: color-mix(in srgb, var(--color-primary, #0057b8) 22%, #7b7b72 78%);
}

.face-gate-panel :deep(.face-error-block) {
  gap: 12px;
  margin-top: 4px;
}

.face-gate-panel :deep(.face-error) {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
}

.face-gate-panel :deep(.face-retry-btn) {
  width: 148px;
  min-height: 48px;
  padding: 0 20px;
  border-radius: 999px;
  background: #ffffff;
  color: color-mix(in srgb, var(--color-primary, #0057b8) 30%, #2f2f2a 70%);
  font-size: 13px;
  font-weight: 600;
  font-family: 'Manrope', sans-serif;
}

@media (max-width: 480px) {
  .face-gate-page {
    padding: 24px 18px 20px;
  }

  .face-gate-shell {
    width: min(100%, 360px);
  }

  .intro-title {
    font-size: clamp(25px, 11vw, 40px);
  }

  .intro-card,
  .capture-card {
    padding: 24px 18px 20px;
    border-radius: 28px;
  }
}
</style>
