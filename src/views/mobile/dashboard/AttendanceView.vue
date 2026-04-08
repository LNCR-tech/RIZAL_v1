<template>
  <section class="mobile-student-attendance">
    <template v-if="event || isInitializing">
      <!-- Camera fills the ENTIRE viewport as a background layer -->
      <MobileAttendanceScannerStage
        class="mobile-student-attendance__stage"
        :background-video-ref="setBackgroundVideoRef"
        :focus-video-ref="setFocusVideoRef"
        :camera-ready="cameraReady"
        :face-detected="faceDetected"
        :busy="isSubmitting || isResolvingLocation"
        :face-image-url="faceImageUrl"
      />

      <!-- Header overlay floats on top of camera -->
      <header class="mobile-student-attendance__overlay">
        <button
          type="button"
          class="mobile-student-attendance__back"
          aria-label="Go back"
          @click="goBack"
        >
          <ArrowLeft :size="22" :stroke-width="2.2" />
        </button>

        <div
          class="mobile-student-attendance__pill"
          :class="`mobile-student-attendance__pill--${statusModel.tone}`"
          role="status"
          aria-live="polite"
        >
          <LoaderCircle
            v-if="statusModel.icon === 'loader'"
            :size="16"
            :stroke-width="2.2"
            class="mobile-student-attendance__pill-spinner"
          />
          <ShieldCheck
            v-else-if="statusModel.icon === 'shield-check'"
            :size="16"
            :stroke-width="2.2"
          />
          <ShieldX
            v-else-if="statusModel.icon === 'shield-x'"
            :size="16"
            :stroke-width="2.2"
          />
          <Shield v-else :size="16" :stroke-width="2.2" />

          <span class="mobile-student-attendance__pill-text">{{ statusModel.message }}</span>
        </div>

        <div class="mobile-student-attendance__back-spacer" aria-hidden="true"></div>
      </header>

      <!-- Card floats at the bottom ON TOP of the camera -->
      <section class="mobile-student-attendance__card">
        <h1 class="mobile-student-attendance__title">{{ actionLabel }}</h1>

        <div class="mobile-student-attendance__info-grid">
          <article class="mobile-student-attendance__info-block">
            <div class="mobile-student-attendance__info-chip">
              <MapPin :size="13" :stroke-width="2.2" />
              <span>Current Location</span>
            </div>

            <p class="mobile-student-attendance__info-value mobile-student-attendance__info-value--location">
              {{ currentLocationLabel }}
            </p>

            <p
              v-if="distanceLabel"
              class="mobile-student-attendance__info-meta"
            >
              {{ distanceLabel }}
            </p>
          </article>

          <div class="mobile-student-attendance__divider" aria-hidden="true"></div>

          <article class="mobile-student-attendance__info-block">
            <div class="mobile-student-attendance__info-chip">
              <Clock3 :size="13" :stroke-width="2.2" />
              <span>Current Time</span>
            </div>

            <p class="mobile-student-attendance__info-value mobile-student-attendance__info-value--time">
              {{ currentTimeLabel }}
            </p>
          </article>
        </div>

        <button
          type="button"
          class="mobile-student-attendance__cta"
          :class="`mobile-student-attendance__cta--${actionTone}`"
          :disabled="isSubmitting || !event"
          @click="handleSubmit"
        >
          {{ submitButtonLabel }}
        </button>
      </section>
    </template>

    <section v-else class="mobile-student-attendance__missing">
      <p class="mobile-student-attendance__missing-title">Event not found.</p>
      <button
        type="button"
        class="mobile-student-attendance__missing-button"
        @click="goBack"
      >
        Go Back
      </button>
    </section>
  </section>
</template>

<script setup>
import {
  ArrowLeft,
  Clock3,
  LoaderCircle,
  MapPin,
  Shield,
  ShieldCheck,
  ShieldX,
} from 'lucide-vue-next'
import MobileAttendanceScannerStage from '@/components/mobile/attendance/MobileAttendanceScannerStage.vue'
import { useMobileStudentAttendance } from '@/composables/useMobileStudentAttendance.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const {
  actionLabel,
  actionTone,
  cameraReady,
  currentLocationLabel,
  currentTimeLabel,
  distanceLabel,
  event,
  faceDetected,
  faceImageUrl,
  goBack,
  handleSubmit,
  isInitializing,
  isResolvingLocation,
  isSubmitting,
  setBackgroundVideoRef,
  setFocusVideoRef,
  statusModel,
  submitButtonLabel,
} = useMobileStudentAttendance(() => props.preview)
</script>

<style scoped>
/* ── Root: covers entire viewport ── */
.mobile-student-attendance {
  position: fixed;
  inset: 0;
  background: #000000;
  font-family: 'Manrope', sans-serif;
  overflow: hidden;
  z-index: 100;
}

/* ── Camera stage: absolute, fills entire viewport behind everything ── */
.mobile-student-attendance__stage {
  position: absolute;
  inset: 0;
  z-index: 0;
}

/* ── Header overlay: pinned to top ── */
.mobile-student-attendance__overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 18px 20px 0;
  padding-top: max(18px, env(safe-area-inset-top, 18px));
  pointer-events: none;
}

.mobile-student-attendance__back,
.mobile-student-attendance__pill {
  pointer-events: auto;
}

.mobile-student-attendance__back {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.96);
  color: #1d1d1f;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 18px rgba(8, 15, 24, 0.10);
}

.mobile-student-attendance__back-spacer {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  pointer-events: none;
}

.mobile-student-attendance__pill {
  min-height: 38px;
  max-width: min(72vw, 280px);
  padding: 9px 16px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 8px 22px rgba(8, 15, 24, 0.10);
}

.mobile-student-attendance__pill--neutral {
  color: #2f3a44;
}

.mobile-student-attendance__pill--loading {
  color: #2f3a44;
}

.mobile-student-attendance__pill--success {
  color: #1d7f47;
}

.mobile-student-attendance__pill--error {
  color: #c0362c;
}

.mobile-student-attendance__pill-text {
  font-size: 12px;
  line-height: 1.25;
  font-weight: 600;
  letter-spacing: -0.01em;
  text-align: center;
}

.mobile-student-attendance__pill-spinner {
  animation: mobile-student-attendance-spin 1s linear infinite;
}

/* ── Card: pinned to bottom, floats on top of camera ── */
.mobile-student-attendance__card {
  position: absolute;
  bottom: 16px;
  left: 16px;
  right: 16px;
  z-index: 10;
  padding: 22px 20px 18px;
  padding-bottom: max(18px, env(safe-area-inset-bottom, 18px));
  border-radius: 28px;
  background: #ffffff;
  box-shadow: 0 18px 44px rgba(7, 14, 23, 0.18);
}

.mobile-student-attendance__title {
  margin: 0;
  text-align: center;
  font-size: 18px;
  line-height: 1.1;
  font-weight: 500;
  color: #1c1c1e;
}

.mobile-student-attendance__info-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 1px minmax(0, 1fr);
  gap: 16px;
  align-items: stretch;
}

.mobile-student-attendance__info-block {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
}

.mobile-student-attendance__info-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 18%, white);
  color: color-mix(in srgb, var(--color-text-always-dark) 82%, var(--color-primary));
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
}

.mobile-student-attendance__info-value {
  margin: 0;
  color: #232326;
}

.mobile-student-attendance__info-value--location {
  font-size: clamp(13px, 4vw, 18px);
  line-height: 1.22;
  font-weight: 500;
}

.mobile-student-attendance__info-value--time {
  font-size: clamp(22px, 6vw, 30px);
  line-height: 1;
  font-weight: 500;
  letter-spacing: -0.05em;
}

.mobile-student-attendance__info-meta {
  margin: 0;
  font-size: 12px;
  line-height: 1.2;
  font-weight: 500;
  color: #8a8f98;
}

.mobile-student-attendance__divider {
  width: 1px;
  align-self: stretch;
  background: rgba(28, 28, 30, 0.12);
}

.mobile-student-attendance__cta {
  width: 100%;
  min-height: 56px;
  margin-top: 18px;
  border: none;
  border-radius: 999px;
  font-family: 'Manrope', sans-serif;
  font-size: 18px;
  line-height: 1;
  font-weight: 500;
  transition:
    transform 180ms ease,
    opacity 180ms ease,
    background-color 180ms ease,
    color 180ms ease;
}

.mobile-student-attendance__cta:active:not(:disabled) {
  transform: scale(0.98);
}

.mobile-student-attendance__cta:disabled {
  opacity: 0.7;
}

.mobile-student-attendance__cta--primary {
  background: var(--color-primary);
  color: var(--color-banner-text);
}

.mobile-student-attendance__cta--muted {
  background: color-mix(in srgb, var(--color-text-always-dark) 8%, white);
  color: color-mix(in srgb, var(--color-text-always-dark) 78%, white);
}

.mobile-student-attendance__missing {
  position: absolute;
  inset: 0;
  padding: 32px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
}

.mobile-student-attendance__missing-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-always-dark);
}

.mobile-student-attendance__missing-button {
  min-height: 48px;
  padding: 0 24px;
  border: none;
  border-radius: 999px;
  background: var(--color-primary);
  color: var(--color-banner-text);
  font-family: 'Manrope', sans-serif;
  font-size: 15px;
  font-weight: 600;
}

@keyframes mobile-student-attendance-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 360px) {
  .mobile-student-attendance__pill {
    max-width: 68vw;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mobile-student-attendance__pill-spinner,
  .mobile-student-attendance__cta {
    animation: none;
    transition: none;
  }
}
</style>
