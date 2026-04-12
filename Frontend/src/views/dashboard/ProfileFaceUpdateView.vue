<template>
  <div class="face-update-page">
    <main class="face-update-shell">
      <section v-if="step === 'password'" class="face-update-auth dashboard-enter dashboard-enter--1">
        <h1 class="face-update-auth__title">Update Face ID</h1>
        <p class="face-update-auth__copy">
          Confirm your password before scanning a new face reference for this account.
        </p>

        <form class="face-update-form" @submit.prevent="handlePasswordSubmit">
          <label class="face-update-field">
            <input
              v-model="currentPassword"
              class="face-update-input"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Current Password"
              autocomplete="current-password"
              :disabled="isVerifyingPassword"
            >
            <button
              type="button"
              class="face-update-visibility"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              @click="showPassword = !showPassword"
            >
              <component :is="showPassword ? EyeOff : Eye" :size="18" />
            </button>
          </label>

          <p v-if="passwordError" class="face-update-feedback face-update-feedback--error">
            {{ passwordError }}
          </p>

          <div class="face-update-actions">
            <SecurityActionPill
              :icon="ArrowRight"
              label="Continue"
              type="submit"
              :loading="isVerifyingPassword"
              :disabled="isVerifyingPassword"
              :full-width="true"
            />

            <SecurityActionPill
              :icon="ArrowLeft"
              label="Cancel"
              type="button"
              :disabled="isVerifyingPassword"
              :full-width="true"
              @click="handleCancel"
            />
          </div>
        </form>
      </section>

      <section v-else class="face-update-scan dashboard-enter dashboard-enter--2">
        <p class="face-update-scan__caption">{{ scanCaption }}</p>

        <div class="face-update-frame">
          <video
            v-show="cameraState === 'ready' && !capturedPreview"
            ref="videoEl"
            class="face-update-video"
            autoplay
            playsinline
            webkit-playsinline
            disablePictureInPicture
            disableRemotePlayback
            controlslist="nodownload noplaybackrate noremoteplayback"
            muted
          />

          <img
            v-if="capturedPreview"
            :src="capturedPreview"
            alt="Updated face preview"
            class="face-update-photo"
          >

          <div
            v-else-if="cameraState !== 'ready'"
            class="face-update-photo face-update-photo--placeholder"
            aria-hidden="true"
          >
            <UserRound :size="52" />
          </div>
        </div>

        <p class="face-update-feedback" :class="{
          'face-update-feedback--error': statusState === 'error',
          'face-update-feedback--success': statusState === 'success',
        }">
          {{ statusMessage }}
        </p>

        <button
          v-if="statusState === 'error'"
          class="face-update-retry"
          type="button"
          @click="retryEnrollment"
        >
          Try Again
        </button>

        <div class="face-update-brand">
          <img :src="activeAuraLogo" alt="Aura AI" class="face-update-brand__logo">
          <span>Powered by Aura Ai</span>
        </div>

        <p class="face-update-footnote">Learn more about Aura Project</p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, Eye, EyeOff, UserRound } from 'lucide-vue-next'
import SecurityActionPill from '@/components/security/SecurityActionPill.vue'
import { activeAuraLogo, applyTheme, loadTheme } from '@/config/theme.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { initFaceScanDetector, resetFaceScanDetector } from '@/composables/useFaceScanDetector.js'
import {
  registerStudentFace,
  resolveApiBaseUrl,
  verifyPasswordForUser,
} from '@/services/backendApi.js'
import { getStoredAuthMeta } from '@/services/localAuth.js'

const router = useRouter()
const {
  currentUser,
  schoolSettings,
  markCurrentUserFaceRegistered,
} = useDashboardSession()

const step = ref('password')
const currentPassword = ref('')
const showPassword = ref(false)
const isVerifyingPassword = ref(false)
const passwordError = ref('')
const statusState = ref('idle')
const statusMessage = ref('')
const capturedPreview = ref('')
const videoEl = ref(null)
const mediaStream = ref(null)
const cameraState = ref('idle')

let detectorInstance = null
let detectRaf = null
let captureTimeout = null
let detectStartedAt = 0
let detectionStreak = 0
let redirectTimeout = null

const faceDetectorWasmBaseUrl =
  import.meta.env.VITE_FACE_DETECTOR_WASM_URL ||
  'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.32/wasm'
const faceDetectorModelUrl =
  import.meta.env.VITE_FACE_DETECTOR_MODEL_URL ||
  'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite'
const faceDetectorMinConfidence = Number(import.meta.env.VITE_FACE_DETECTOR_MIN_CONFIDENCE ?? 0.5)
const faceDetectorSuppression = Number(import.meta.env.VITE_FACE_DETECTOR_SUPPRESSION ?? 0.3)
const faceDetectorIntervalMs = Number(import.meta.env.VITE_FACE_DETECTOR_INTERVAL_MS ?? 120)
const detectTimeoutMs = Number(import.meta.env.VITE_FACE_ENROLL_DETECT_TIMEOUT_MS ?? 12000)
const captureDelayMs = Number(import.meta.env.VITE_FACE_ENROLL_CAPTURE_DELAY_MS ?? 450)

const authEmail = computed(() =>
  currentUser.value?.email || getStoredAuthMeta()?.email || ''
)
const authUserId = computed(() => Number(currentUser.value?.id ?? getStoredAuthMeta()?.userId ?? NaN))
const scanCaption = computed(() => {
  if (statusState.value === 'success') return 'Face updated successfully.'
  return 'Scanning Face...'
})

function applySecurityTheme() {
  const authMeta = getStoredAuthMeta()
  applyTheme(loadTheme({
    school_name: currentUser.value?.school_name || authMeta?.schoolName || null,
    school_code: currentUser.value?.school_code || authMeta?.schoolCode || null,
    logo_url: schoolSettings.value?.logo_url || authMeta?.logoUrl || null,
    primary_color: schoolSettings.value?.primary_color || authMeta?.primaryColor || '#AAFF00',
    secondary_color: schoolSettings.value?.secondary_color || authMeta?.secondaryColor || '#FFD400',
    accent_color: schoolSettings.value?.accent_color || authMeta?.accentColor || '#000000',
  }))
}

watch(
  () => [
    currentUser.value?.school_name,
    currentUser.value?.school_code,
    schoolSettings.value?.logo_url,
    schoolSettings.value?.primary_color,
    schoolSettings.value?.secondary_color,
    schoolSettings.value?.accent_color,
  ],
  () => {
    applySecurityTheme()
  },
  { immediate: true }
)

onMounted(() => {
  applySecurityTheme()
})

onBeforeUnmount(() => {
  clearTimers()
  stopFaceDetection()
  stopCamera()
  resetFaceScanDetector()
  detectorInstance = null
})

async function handlePasswordSubmit() {
  passwordError.value = ''

  if (!currentPassword.value.trim()) {
    passwordError.value = 'Enter your current password before updating Face ID.'
    return
  }

  if (!authEmail.value) {
    passwordError.value = 'Unable to verify your account password right now.'
    return
  }

  isVerifyingPassword.value = true

  try {
    await verifyPasswordForUser(resolveApiBaseUrl(), {
      email: authEmail.value,
      password: currentPassword.value,
      expectedUserId: authUserId.value,
    })

    step.value = 'scan'
    await nextTick()
    await startEnrollmentFlow()
  } catch (error) {
    passwordError.value = error?.message || 'Password confirmation failed.'
  } finally {
    isVerifyingPassword.value = false
  }
}

function handleCancel() {
  router.push({ name: 'ProfileSecurity' })
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
  statusMessage.value = 'Preparing camera...'

  const cameraReady = await startCamera()
  if (!cameraReady) {
    setEnrollmentError(
      cameraState.value === 'denied'
        ? 'Camera access is required to update Face ID.'
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
  statusMessage.value = 'Position your face in the center of the frame.'
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
    // Ignore autoplay issues.
  }

  const ready = await waitForVideoReady(el)
  if (!ready) {
    cameraState.value = 'unsupported'
    return false
  }

  cameraState.value = 'ready'
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
      setEnrollmentError('No face detected. Please try again in a brighter area.')
      return
    }

    try {
      const result = detectorInstance.detectForVideo(videoEl.value, now)
      const hasFace = Array.isArray(result?.detections) && result.detections.length > 0
      detectionStreak = hasFace ? detectionStreak + 1 : 0

      if (detectionStreak >= 2) {
        statusState.value = 'capturing'
        statusMessage.value = 'Face detected. Updating Face ID...'
        stopFaceDetection()
        captureTimeout = setTimeout(() => {
          captureAndRegister()
        }, captureDelayMs)
        return
      }
    } catch {
      setEnrollmentError('Face detection failed. Please try again.')
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
    statusMessage.value = 'Updating your Face ID...'

    const imageDataUrl = captureVideoFrame()
    const rawBase64 = imageDataUrl.includes(',') ? imageDataUrl.split(',')[1] : imageDataUrl
    capturedPreview.value = imageDataUrl
    stopCamera()

    const token = localStorage.getItem('aura_token')
    try {
      await registerStudentFace(resolveApiBaseUrl(), token, imageDataUrl)
    } catch {
      await registerStudentFace(resolveApiBaseUrl(), token, rawBase64)
    }

    markCurrentUserFaceRegistered()
    statusState.value = 'success'
    statusMessage.value = 'Face ID updated successfully.'
    redirectTimeout = setTimeout(() => {
      router.replace({ name: 'ProfileSecurity', query: { done: 'face' } })
    }, 900)
  } catch (error) {
    setEnrollmentError(error?.message || 'Unable to update your Face ID right now.')
  }
}

function setEnrollmentError(message) {
  clearTimers()
  stopFaceDetection()
  stopCamera()
  statusState.value = 'error'
  statusMessage.value = message
}
</script>

<style scoped>
.face-update-page {
  min-height: 100vh;
  background: var(--color-bg, #ebebeb);
  padding: 48px 24px 36px;
  font-family: 'Manrope', sans-serif;
}

.face-update-shell {
  width: min(100%, 400px);
  margin: 0 auto;
}

.face-update-auth {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-top: 72px;
}

.face-update-auth__title {
  margin: 0;
  font-size: clamp(44px, 14vw, 58px);
  line-height: 0.94;
  letter-spacing: -0.06em;
  color: #0a0a0a;
}

.face-update-auth__copy {
  margin: 0;
  max-width: 286px;
  font-size: 15px;
  line-height: 1.3;
  color: #262621;
}

.face-update-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 8px;
}

.face-update-actions {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.face-update-field {
  position: relative;
  display: flex;
  align-items: center;
}

.face-update-input {
  width: 100%;
  min-height: 60px;
  padding: 0 56px 0 20px;
  border-radius: 999px;
  border: 1.5px solid rgba(10, 10, 10, 0.92);
  background: rgba(255, 255, 255, 0.7);
  color: #111111;
  font-size: 14px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.face-update-input::placeholder {
  color: #171717;
  opacity: 1;
}

.face-update-input:focus {
  border-color: color-mix(in srgb, var(--color-primary, #aaff00) 42%, #0a0a0a 58%);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary, #aaff00) 18%, transparent);
}

.face-update-visibility {
  position: absolute;
  right: 18px;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #555550;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.face-update-scan {
  min-height: calc(100vh - 84px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 22px;
}

.face-update-scan__caption {
  margin: 0;
  font-size: 17px;
  font-weight: 500;
  color: #101010;
}

.face-update-frame {
  width: min(100%, 240px);
  aspect-ratio: 1;
  border-radius: 50%;
  overflow: hidden;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.face-update-video,
.face-update-photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.face-update-video {
  background: #000000;
}

.face-update-photo--placeholder {
  color: #8d8d88;
  background: #f4f4f1;
}

.face-update-feedback {
  min-height: 18px;
  margin: 0;
  font-size: 12px;
  font-weight: 500;
  color: #6d6d69;
}

.face-update-feedback--error {
  color: #e23636;
}

.face-update-feedback--success {
  color: color-mix(in srgb, var(--color-primary, #aaff00) 52%, #111111 48%);
}

.face-update-retry {
  min-width: 208px;
  min-height: 56px;
  padding: 0 28px;
  border-radius: 999px;
  border: 1.4px solid rgba(10, 10, 10, 0.86);
  background: transparent;
  color: #171717;
  font-size: 16px;
  font-weight: 500;
}

.face-update-brand {
  margin-top: 22px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #161616;
  font-size: 13px;
}

.face-update-brand__logo {
  width: 34px;
  height: auto;
}

.face-update-footnote {
  margin: 44px 0 0;
  font-size: 12px;
  color: #161616;
}

@media (min-width: 900px) {
  .face-update-page {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 36px 24px;
  }

  .face-update-auth {
    padding-top: 0;
  }

  .face-update-scan {
    min-height: 720px;
  }
}
</style>
