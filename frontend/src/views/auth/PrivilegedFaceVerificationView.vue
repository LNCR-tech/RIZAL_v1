<template>
  <div class="face-gate-page">
    <div v-if="step === 'intro'" class="face-gate-shell face-gate-shell--intro">
      <section class="intro-card">
        <span class="intro-chip">{{ schoolName }}</span>
        <h1 class="intro-title">
          Hi {{ firstName }},<br>
          {{ introTitleLines.line2 }}<br>
          {{ introTitleLines.line3 }}<br>
          {{ introTitleLines.line4 }}<br>
          {{ introTitleLines.line5 }}
        </h1>
        <p class="intro-copy">{{ introCopy }}</p>

        <button
          class="register-pill"
          type="button"
          :disabled="statusState === 'loading'"
          @click="beginFlow"
        >
          <span class="register-pill__icon">
            <ArrowRight :size="18" />
          </span>
          <span class="register-pill__text">{{ introCtaLabel }}</span>
        </button>

        <p
          v-if="statusMessage && step === 'intro' && (statusState === 'error' || statusState === 'idle')"
          class="intro-feedback"
          :class="{ 'intro-feedback--error': statusState === 'error' }"
        >
          {{ statusMessage }}
        </p>
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
          @retry="retryFlow"
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
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from 'lucide-vue-next'
import { useAuth } from '@/composables/useAuth.js'
import {
  getDefaultAuthenticatedRoute,
  initializeDashboardSession,
} from '@/composables/useDashboardSession.js'
import { applyTheme, loadTheme } from '@/config/theme.js'
import {
  getFaceStatus,
  resolveApiBaseUrl,
  saveFaceReference,
  verifyFaceReference,
} from '@/services/backendApi.js'
import { initFaceScanDetector, resetFaceScanDetector } from '@/composables/useFaceScanDetector.js'
import {
  getStoredAuthMeta,
  hasPrivilegedPendingFace,
  needsStoredPasswordChange,
  patchStoredAuthMeta,
} from '@/services/localAuth.js'
import { markCurrentRuntimeSession } from '@/services/sessionPersistence.js'
import FaceScanPanel from '@/components/attendance/FaceScanPanel.vue'

const router = useRouter()
const { logout } = useAuth()

const initialAuthMeta = getStoredAuthMeta()
const apiBaseUrl = ref(resolveApiBaseUrl())
const step = ref('intro')
const mode = ref(initialAuthMeta?.faceReferenceEnrolled ? 'verify' : 'register')
const statusState = ref('loading')
const statusMessage = ref('')
const capturedPreview = ref('')
const videoEl = ref(null)
const mediaStream = ref(null)
const videoReady = ref(false)
const cameraState = ref('idle')
const authMeta = ref(initialAuthMeta)
const faceStatus = ref(null)

let detectorInstance = null
let detectRaf = null
let captureTimeout = null
let detectStartedAt = 0
let detectionStreak = 0
let redirectTimeout = null

const firstName = computed(() => authMeta.value?.firstName?.trim() || 'there')
const schoolName = computed(() => authMeta.value?.schoolName?.trim() || 'Your school')
const introTitleLines = computed(() => {
  if (mode.value === 'register') {
    return {
      line2: 'face is',
      line3: 'unregistered',
      line4: 'please register',
      line5: 'now.',
    }
  }

  return {
    line2: 'face is',
    line3: 'registered',
    line4: 'please verify',
    line5: 'now.',
  }
})
const introCopy = computed(() => {
  if (mode.value === 'register') {
    return 'We will use the same face-scan experience as attendance so future School IT sign-ins feel familiar.'
  }

  return 'We will use the same face-scan experience to confirm this School IT account before protected tools open.'
})
const introCtaLabel = computed(() => mode.value === 'register' ? 'Register Now' : 'Verify Now')
const captureTitle = computed(() => {
  if (statusState.value === 'success') return 'All set!'
  if (statusState.value === 'submitting') {
    return mode.value === 'register' ? 'Registering...' : 'Verifying...'
  }
  if (statusState.value === 'capturing') return mode.value === 'register' ? 'Registering...' : 'Verifying...'
  if (statusState.value === 'starting') return 'Preparing camera'
  if (statusState.value === 'detecting') return 'Scanning...'
  if (statusState.value === 'error') return 'Try again'
  return mode.value === 'register' ? 'Register your face' : 'Verify your face'
})
const captureCopy = computed(() => {
  if (statusState.value === 'success') {
    return 'Your School IT face verification is complete. We are taking you straight to your workspace.'
  }
  if (statusState.value === 'submitting') {
    return mode.value === 'register'
      ? 'Stay centered for a moment while we save a clean reference image.'
      : 'Stay centered for a moment while we verify your live face against the saved reference.'
  }
  if (statusState.value === 'starting') {
    return 'We are warming up your camera and loading the same scan frame used for secure attendance.'
  }
  if (statusState.value === 'detecting') {
    return 'Use a well-lit angle and keep your face inside the frame so future secure sign-ins feel natural.'
  }
  if (statusState.value === 'error') {
    return 'Better lighting and a centered face usually fixes this on the next try.'
  }

  return mode.value === 'register'
    ? 'Use the same school-branded scan flow that powers secure attendance check-ins.'
    : 'Use the same school-branded scan flow to unlock the protected School IT workspace.'
})
const panelCaption = computed(() => {
  if (statusState.value === 'success') {
    return mode.value === 'register' ? 'Face registered.' : 'Face verified.'
  }
  if (statusState.value === 'submitting') return 'Hold still...'
  if (statusState.value === 'capturing') return 'Hold still...'
  if (statusState.value === 'starting') return 'Warming up camera...'
  if (statusState.value === 'error') return mode.value === 'register' ? 'Registration failed.' : 'Verification failed.'
  return 'Keep your face centered.'
})
const showRetry = computed(() => statusState.value === 'error')
const statusClass = computed(() => ({
  'capture-status--error': statusState.value === 'error',
  'capture-status--success': statusState.value === 'success',
}))
const panelCameraReady = computed(() => cameraState.value === 'ready' && !capturedPreview.value)
const panelFaceImageUrl = computed(() => capturedPreview.value || '')
const showStatusMessage = computed(() =>
  Boolean(statusText.value) && statusState.value === 'success'
)
const statusText = computed(() => {
  if (statusState.value === 'success') {
    return mode.value === 'register'
      ? 'Face registered successfully. Preparing verification...'
      : 'Face verified successfully. Opening your workspace...'
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

function refreshAuthMeta() {
  authMeta.value = getStoredAuthMeta()
}

function applyPrivilegedTheme() {
  const meta = getStoredAuthMeta()
  applyTheme(loadTheme({
    school_name: meta?.schoolName || null,
    school_code: meta?.schoolCode || null,
    logo_url: meta?.logoUrl || null,
    primary_color: meta?.primaryColor || '#0057B8',
    secondary_color: meta?.secondaryColor || '#FFD400',
    accent_color: meta?.accentColor || '#000000',
  }))
}

function describeAntiSpoofReason(reason) {
  switch (reason) {
    case 'opencv_unavailable':
    case 'onnxruntime_unavailable':
      return 'Backend camera verification is not ready yet.'
    case 'model_missing':
      return 'The backend anti-spoof model is not installed yet.'
    case 'session_unavailable':
      return 'The backend anti-spoof service could not start.'
    default:
      return 'Privileged face verification is not ready on the backend yet.'
  }
}

onMounted(async () => {
  applyPrivilegedTheme()
  await ensurePendingPrivilegedFace()
})

onBeforeUnmount(() => {
  clearTimers()
  stopFaceDetection()
  stopCamera()
  resetFaceScanDetector()
  detectorInstance = null
})

async function ensurePendingPrivilegedFace() {
  refreshAuthMeta()

  if (!localStorage.getItem('aura_token')) {
    router.replace({ name: 'Login' })
    return
  }

  if (!hasPrivilegedPendingFace(authMeta.value)) {
    await routeIntoUnlockedSession()
    return
  }

  await loadFaceStatus()
}

async function loadFaceStatus() {
  statusState.value = 'loading'
  statusMessage.value = 'Checking face verification status...'

  try {
    const token = localStorage.getItem('aura_token')
    const nextStatus = await getFaceStatus(apiBaseUrl.value, token)
    faceStatus.value = nextStatus

    patchStoredAuthMeta({
      faceVerificationRequired: nextStatus.face_verification_required,
      faceVerificationPending: nextStatus.face_verification_required,
      faceReferenceEnrolled: nextStatus.face_reference_enrolled,
    })
    refreshAuthMeta()
    applyPrivilegedTheme()

    if (!nextStatus.anti_spoof_ready) {
      setPendingFaceError(describeAntiSpoofReason(nextStatus.anti_spoof_reason), false)
      return
    }

    if (!nextStatus.face_verification_required) {
      await routeIntoUnlockedSession()
      return
    }

    mode.value = nextStatus.face_reference_enrolled ? 'verify' : 'register'
    step.value = 'intro'
    statusState.value = 'idle'
    statusMessage.value = ''
  } catch (error) {
    setPendingFaceError(error?.message || 'Unable to load privileged face verification status.', false)
  }
}

async function beginFlow() {
  step.value = 'capture'
  capturedPreview.value = ''
  await nextTick()
  await startPendingFaceFlow()
}

async function retryFlow() {
  capturedPreview.value = ''
  await startPendingFaceFlow()
}

async function startPendingFaceFlow() {
  clearTimers()
  stopFaceDetection()
  stopCamera()

  statusState.value = 'starting'
  statusMessage.value = 'Starting camera...'
  videoReady.value = false
  detectionStreak = 0

  const cameraReady = await startCamera()
  if (!cameraReady) {
    setPendingFaceError(
      cameraState.value === 'denied'
        ? 'Camera access is required to continue.'
        : 'Camera is unavailable on this device.'
    )
    return
  }

  const detectorReady = await ensureFaceDetector()
  if (!detectorReady) {
    statusState.value = 'capturing'
    statusMessage.value = 'Hold still while we capture your face.'
    captureTimeout = setTimeout(() => {
      captureAndSubmit()
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
    // Let the ready-state guard decide if the video is usable.
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
      setPendingFaceError('Face not found.')
      return
    }

    try {
      const result = detectorInstance.detectForVideo(videoEl.value, now)
      const hasFace = Array.isArray(result?.detections) && result.detections.length > 0
      detectionStreak = hasFace ? detectionStreak + 1 : 0

      if (detectionStreak >= 2) {
        statusState.value = 'capturing'
        statusMessage.value = 'Face detected. Capturing...'
        stopFaceDetection()
        captureTimeout = setTimeout(() => {
          captureAndSubmit()
        }, captureDelayMs)
        return
      }
    } catch {
      setPendingFaceError('Face not found.')
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

async function captureAndSubmit() {
  try {
    statusState.value = 'submitting'
    statusMessage.value = mode.value === 'register'
      ? 'Registering your face...'
      : 'Verifying your face...'

    const imageDataUrl = captureVideoFrame()
    const rawBase64 = imageDataUrl.includes(',') ? imageDataUrl.split(',')[1] : imageDataUrl
    capturedPreview.value = imageDataUrl

    stopCamera()

    const token = localStorage.getItem('aura_token')

    if (mode.value === 'register') {
      try {
        await saveFaceReference(apiBaseUrl.value, token, imageDataUrl)
      } catch {
        await saveFaceReference(apiBaseUrl.value, token, rawBase64)
      }

      patchStoredAuthMeta({
        faceReferenceEnrolled: true,
        faceVerificationRequired: true,
        faceVerificationPending: true,
      })
      refreshAuthMeta()
      applyPrivilegedTheme()

      mode.value = 'verify'
      step.value = 'intro'
      statusState.value = 'idle'
      statusMessage.value = 'Face registered successfully. Verify once to continue.'
      capturedPreview.value = ''
      return
    }

    let verification = null
    try {
      verification = await verifyFaceReference(apiBaseUrl.value, token, {
        image_base64: imageDataUrl,
      })
    } catch {
      verification = await verifyFaceReference(apiBaseUrl.value, token, {
        image_base64: rawBase64,
      })
    }

    if (!verification?.matched) {
      throw new Error('Face not match.')
    }

    if (!verification?.access_token) {
      throw new Error('Face verified, but the backend did not return a full-access token.')
    }

    localStorage.setItem('aura_token', verification.access_token)
    markCurrentRuntimeSession()

    patchStoredAuthMeta({
      tokenType: verification.token_type || 'bearer',
      sessionId: verification.session_id ?? authMeta.value?.sessionId ?? null,
      faceVerificationRequired: Boolean(verification.face_verification_pending),
      faceVerificationPending: Boolean(verification.face_verification_pending),
      faceReferenceEnrolled: true,
    })
    refreshAuthMeta()

    statusState.value = 'success'
    statusMessage.value = 'Face verified successfully. Opening your workspace...'
    redirectTimeout = setTimeout(async () => {
      try {
        await routeIntoUnlockedSession()
      } catch (error) {
        setPendingFaceError(error?.message || 'Face verification succeeded, but the session could not be initialized.', false)
      }
    }, 700)
  } catch (error) {
    setPendingFaceError(error?.message || 'Unable to verify this account right now.')
  }
}

async function routeIntoUnlockedSession() {
  if (needsStoredPasswordChange()) {
    router.replace({ name: 'ChangePassword' })
    return
  }

  await initializeDashboardSession(true)
  router.replace(getDefaultAuthenticatedRoute())
}

function setPendingFaceError(message, keepCaptureStep = true) {
  clearTimers()
  stopFaceDetection()
  stopCamera()
  if (!keepCaptureStep) {
    step.value = 'intro'
  }
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
}

.intro-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 18px;
}

.intro-chip,
.capture-chip {
  display: inline-flex;
  align-items: center;
  padding: 10px 16px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary, #0057B8) 12%, white 88%);
  color: var(--color-primary, #0057B8);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.intro-title,
.capture-title {
  margin: 0;
  font-family: 'Manrope', sans-serif;
  font-size: clamp(48px, 11vw, 68px);
  line-height: 0.95;
  font-weight: 800;
  color: #0e0e0e;
}

.title-fade-enter-active,
.title-fade-leave-active {
  transition: opacity 0.22s ease;
}

.title-fade-enter-from,
.title-fade-leave-to {
  opacity: 0;
}

.intro-copy,
.capture-copy {
  margin: 0;
  max-width: 320px;
  font-size: 14px;
  line-height: 1.45;
  color: #5e5e5e;
}

.intro-feedback,
.capture-status {
  margin: 0;
  font-size: 14px;
  line-height: 1.4;
  text-align: center;
}

.intro-feedback {
  color: #3a5d00;
}

.intro-feedback--error,
.capture-status--error {
  color: #d24848;
}

.capture-status--success {
  color: #3a5d00;
}

.register-pill {
  margin-top: 10px;
  border: none;
  border-radius: 999px;
  background: var(--color-primary, #0057B8);
  color: var(--color-on-primary, #ffffff);
  display: inline-flex;
  align-items: center;
  gap: 14px;
  padding: 6px 20px 6px 6px;
  min-height: 68px;
  cursor: pointer;
  transition: transform 0.16s ease;
}

.register-pill:disabled {
  opacity: 0.5;
  cursor: wait;
}

.register-pill:active,
.signout-link:active {
  transform: scale(0.98);
}

.register-pill__icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #0b0b0b;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.register-pill__text {
  font-size: 16px;
  font-weight: 700;
}

.capture-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.capture-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  text-align: center;
}

.face-gate-panel {
  width: 100%;
}

.signout-link {
  margin-top: 22px;
  border: none;
  background: transparent;
  color: #2a2a2a;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

@media (min-width: 768px) {
  .face-gate-page {
    padding-inline: 32px;
  }

  .intro-card,
  .capture-card {
    padding-inline: 32px;
  }

  .register-pill {
    min-inline-size: clamp(220px, 28vw, 252px);
    justify-content: flex-start;
  }

  .intro-copy,
  .capture-copy {
    max-width: 380px;
  }
}
</style>
