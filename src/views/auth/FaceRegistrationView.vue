<template>
  <div class="face-gate-page">
    <div v-if="step === 'intro'" class="face-gate-shell face-gate-shell--intro">
      <h1 class="intro-title">
        Hi {{ firstName }},<br>
        face is<br>
        unregistered<br>
        please register<br>
        now.
      </h1>

      <button class="register-pill" type="button" @click="beginEnrollment">
        <span class="register-pill__icon">
          <ArrowRight :size="18" />
        </span>
        <span class="register-pill__text">Register Now</span>
      </button>
    </div>

    <div v-else class="face-gate-shell face-gate-shell--capture">
      <p class="capture-caption">{{ captionText }}</p>

      <div class="face-orbit" :class="orbitClass">
        <span class="face-orbit__dot face-orbit__dot--top" aria-hidden="true"></span>
        <span class="face-orbit__dot face-orbit__dot--left" aria-hidden="true"></span>

        <div class="face-orbit__inner">
          <video
            v-show="showLivePreview"
            ref="videoEl"
            class="face-media face-media--video"
            autoplay
            playsinline
            muted
          ></video>

          <img
            v-if="capturedPreview"
            :src="capturedPreview"
            alt="Registered face preview"
            class="face-media"
          />

          <div v-if="showPlaceholder" class="face-placeholder">
            {{ placeholderText }}
          </div>
        </div>
      </div>

      <p class="capture-status" :class="statusClass">{{ statusMessage }}</p>

      <button
        v-if="showRetry"
        class="retry-pill"
        type="button"
        @click="retryEnrollment"
      >
        Try Again
      </button>
    </div>

    <button class="signout-link" type="button" @click="logout">
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
import { saveFaceReference } from '@/services/backendApi.js'
import { initFaceScanDetector, resetFaceScanDetector } from '@/composables/useFaceScanDetector.js'

const router = useRouter()
const { logout } = useAuth()
const {
  apiBaseUrl,
  currentUser,
  initializeDashboardSession,
  needsFaceRegistration,
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
const captionText = computed(() =>
  statusState.value === 'success'
    ? 'Face registered successfully.'
    : 'Ensure your face is well-lit.'
)
const showRetry = computed(() => statusState.value === 'error')
const showLivePreview = computed(() => !capturedPreview.value)
const showPlaceholder = computed(() => !capturedPreview.value && (!videoReady.value || cameraState.value !== 'ready'))
const placeholderText = computed(() => {
  if (cameraState.value === 'denied') return 'Camera access is required.'
  if (cameraState.value === 'unsupported') return 'Camera is unavailable on this device.'
  if (statusState.value === 'starting') return 'Starting camera...'
  return 'Preparing camera...'
})
const statusClass = computed(() => ({
  'capture-status--error': statusState.value === 'error',
  'capture-status--success': statusState.value === 'success',
}))
const orbitClass = computed(() => ({
  'face-orbit--error': statusState.value === 'error',
  'face-orbit--success': statusState.value === 'success',
  'face-orbit--active': ['starting', 'detecting', 'capturing', 'submitting'].includes(statusState.value),
}))

const faceDetectorWasmBaseUrl =
  import.meta.env.VITE_FACE_DETECTOR_WASM_URL ||
  'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
const faceDetectorModelUrl =
  import.meta.env.VITE_FACE_DETECTOR_MODEL_URL ||
  'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite'
const faceDetectorMinConfidence = Number(import.meta.env.VITE_FACE_DETECTOR_MIN_CONFIDENCE ?? 0.5)
const faceDetectorSuppression = Number(import.meta.env.VITE_FACE_DETECTOR_SUPPRESSION ?? 0.3)
const faceDetectorIntervalMs = Number(import.meta.env.VITE_FACE_DETECTOR_INTERVAL_MS ?? 120)
const detectTimeoutMs = Number(import.meta.env.VITE_FACE_ENROLL_DETECT_TIMEOUT_MS ?? 12000)
const captureDelayMs = Number(import.meta.env.VITE_FACE_ENROLL_CAPTURE_DELAY_MS ?? 450)

watch(
  () => needsFaceRegistration.value,
  (required) => {
    if (!required) {
      router.replace({ name: 'Home' })
    }
  }
)

onMounted(() => {
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
    return true
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
      await saveFaceReference(apiBaseUrl.value, token, imageDataUrl)
    } catch {
      await saveFaceReference(apiBaseUrl.value, token, rawBase64)
    }

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
  min-height: 100vh;
  background: #ebebeb;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 36px 24px 28px;
  font-family: 'Manrope', sans-serif;
}

.face-gate-shell {
  width: min(100%, 340px);
  display: flex;
  flex-direction: column;
}

.face-gate-shell--intro {
  align-items: flex-start;
  gap: 44px;
}

.face-gate-shell--capture {
  align-items: center;
  gap: 24px;
}

.intro-title {
  margin: 0;
  font-size: clamp(27px, 8vw, 46px);
  line-height: 0.96;
  letter-spacing: -0.05em;
  font-weight: 700;
  color: #0a0a0a;
}

.register-pill {
  display: inline-flex;
  align-items: center;
  gap: 18px;
  min-height: 58px;
  padding: 4px 22px 4px 4px;
  border: none;
  border-radius: 999px;
  background: var(--color-primary, #caff00);
  color: #0a0a0a;
  cursor: pointer;
  box-shadow: 0 16px 28px rgba(10, 10, 10, 0.08);
  transition: transform 0.16s ease;
}

.register-pill:active,
.retry-pill:active,
.signout-link:active {
  transform: scale(0.97);
}

.register-pill__icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #0a0a0a;
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

.capture-caption {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: #4c4c46;
}

.face-orbit {
  position: relative;
  width: min(72vw, 286px);
  aspect-ratio: 1;
  border-radius: 50%;
  background: conic-gradient(from -55deg, var(--color-primary, #caff00) 0deg 300deg, #f1efe4 300deg 360deg);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: filter 0.2s ease, transform 0.2s ease;
}

.face-orbit--active {
  animation: orbitPulse 1.6s ease-in-out infinite;
}

.face-orbit--error {
  background: conic-gradient(from -55deg, #f55b5b 0deg 300deg, #f1efe4 300deg 360deg);
}

.face-orbit--success {
  background: conic-gradient(from -55deg, var(--color-primary, #caff00) 0deg 360deg, var(--color-primary, #caff00) 360deg 360deg);
}

.face-orbit__inner {
  width: calc(100% - 42px);
  height: calc(100% - 42px);
  border-radius: 50%;
  overflow: hidden;
  background: #f7f5ec;
  display: flex;
  align-items: center;
  justify-content: center;
}

.face-orbit__dot {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #0a0a0a;
}

.face-orbit__dot--top {
  top: 16px;
  left: 54%;
}

.face-orbit__dot--left {
  left: 15px;
  top: 53%;
}

.face-media {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.face-media--video {
  transform: scaleX(-1);
}

.face-placeholder {
  padding: 0 28px;
  text-align: center;
  font-size: 14px;
  line-height: 1.5;
  color: #55554e;
}

.capture-status {
  min-height: 18px;
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #6b6b64;
  text-align: center;
}

.capture-status--error {
  color: #ff5f5f;
}

.capture-status--success {
  color: #5a7f00;
}

.retry-pill {
  min-width: 162px;
  min-height: 48px;
  padding: 0 24px;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.68);
  color: #4b4b45;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 14px 24px rgba(10, 10, 10, 0.05);
}

.signout-link {
  margin-top: 28px;
  border: none;
  background: transparent;
  color: #6b6b64;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

@keyframes orbitPulse {
  0%,
  100% {
    transform: scale(1);
    filter: brightness(1);
  }

  50% {
    transform: scale(1.015);
    filter: brightness(1.03);
  }
}
</style>
