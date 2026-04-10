<template>
  <section class="gather-attendance">
    <template v-if="hasEvents">
      <MobileAttendanceScannerStage
        class="gather-attendance__stage"
        :background-video-ref="setBackgroundVideoRef"
        :focus-video-ref="setFocusVideoRef"
        :camera-ready="cameraReady"
        :face-detected="faceDetected"
        :busy="isSubmitting || isResolvingLocation"
        :face-image-url="faceImageUrl"
      />

      <div class="gather-attendance__top-gradient" aria-hidden="true" />
      <div class="gather-attendance__bottom-gradient" aria-hidden="true" />

      <header class="gather-attendance__topbar">
        <button
          type="button"
          class="gather-attendance__back"
          aria-label="Go back"
          @click="goBack"
        >
          <ArrowLeft :size="20" :stroke-width="2.25" />
        </button>

        <div class="gather-attendance__brand">
          <div class="gather-attendance__brand-copy">
            <GatherBrandMark class="gather-attendance__brand-mark" />
            <div class="gather-attendance__brand-stack">
              <span class="gather-attendance__eyebrow">{{ headerEyebrow }}</span>
              <span class="gather-attendance__title">Gather</span>
            </div>
          </div>

          <div
            class="gather-attendance__status"
            :class="`gather-attendance__status--${statusModel.tone}`"
            role="status"
            aria-live="polite"
          >
            <LoaderCircle
              v-if="statusModel.icon === 'loader'"
              :size="14"
              :stroke-width="2.2"
              class="gather-attendance__status-spinner"
            />
            <ShieldCheck
              v-else-if="statusModel.icon === 'shield-check'"
              :size="14"
              :stroke-width="2.2"
            />
            <ShieldX
              v-else-if="statusModel.icon === 'shield-x'"
              :size="14"
              :stroke-width="2.2"
            />
            <Shield v-else :size="14" :stroke-width="2.2" />

            <span class="gather-attendance__status-copy">{{ statusModel.message }}</span>
          </div>
        </div>
      </header>

      <section class="gather-attendance__hud">
        <div class="gather-attendance__events" role="list" aria-label="Gather event options">
          <GatherEventPill
            v-for="item in candidateEvents"
            :key="item.id"
            :title="item.event.name"
            :meta-label="item.metaLabel"
            :time-label="item.timeLabel"
            :status-label="item.statusLabel"
            :tone="item.tone"
            :active="selectedEvent?.id === item.id"
            @select="selectEvent(item.id)"
          />
        </div>

        <div v-if="selectedEvent" class="gather-attendance__selection-card">
          <div class="gather-attendance__selection-head">
            <span class="gather-attendance__selection-kicker">
              {{ selectedEvent.scopeLabel || selectedEvent.statusLabel }}
            </span>
            <span
              class="gather-attendance__selection-badge"
              :class="`gather-attendance__selection-badge--${selectedEvent.tone}`"
            >
              {{ selectedEvent.statusLabel }}
            </span>
          </div>

          <h1 class="gather-attendance__selection-title">{{ selectedEvent.event.name }}</h1>

          <div class="gather-attendance__selection-meta">
            <span class="gather-attendance__selection-meta-item">
              <MapPin :size="13" :stroke-width="2.1" />
              <span>{{ selectedEvent.metaLabel }}</span>
            </span>

            <span class="gather-attendance__selection-meta-item">
              <Clock3 :size="13" :stroke-width="2.1" />
              <span>{{ selectedEvent.timeLabel }}</span>
            </span>
          </div>
        </div>

        <div class="gather-attendance__controls">
          <div class="gather-attendance__side-pill">
            <MapPin :size="15" :stroke-width="2.2" />
            <span>{{ locationChipLabel }}</span>
          </div>

          <button
            type="button"
            class="gather-attendance__shutter"
            :disabled="!canCapture"
            :aria-label="submitButtonLabel"
            @click="handleSubmit"
          >
            <span class="gather-attendance__shutter-ring" />
            <span class="gather-attendance__shutter-core" />
          </button>

          <div class="gather-attendance__side-pill">
            <Clock3 :size="15" :stroke-width="2.2" />
            <span>{{ currentTimeLabel }}</span>
          </div>
        </div>

        <div class="gather-attendance__action-copy">
          <p class="gather-attendance__action-title">{{ submitButtonLabel }}</p>
          <p class="gather-attendance__action-meta">{{ actionHint }}</p>
          <p class="gather-attendance__action-meta gather-attendance__action-meta--secondary">
            {{ locationMetaLabel }}
          </p>
        </div>
      </section>

      <Transition name="gather-success">
        <div
          v-if="successSheet"
          class="gather-attendance__success-backdrop"
          @click.self="dismissSuccess"
        >
          <GatherSuccessSheet
            :title="successSheet.title"
            :subtitle="successSheet.subtitle"
            :rows="successSheet.rows"
            @dismiss="dismissSuccess"
          />
        </div>
      </Transition>
    </template>

    <section v-else class="gather-attendance__empty">
      <div class="gather-attendance__empty-card">
        <GatherBrandMark class="gather-attendance__empty-brand" />
        <p class="gather-attendance__empty-kicker">Gather</p>
        <h1 class="gather-attendance__empty-title">No attendance-ready events yet.</h1>
        <p class="gather-attendance__empty-copy">
          Open your event list and wait for a live check-in or check-out window from the backend.
        </p>

        <div class="gather-attendance__empty-actions">
          <button
            type="button"
            class="gather-attendance__empty-button gather-attendance__empty-button--primary"
            @click="openEventsView"
          >
            Open Events
          </button>
          <button
            type="button"
            class="gather-attendance__empty-button"
            @click="goBack"
          >
            Go Back
          </button>
        </div>
      </div>
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
import GatherBrandMark from '@/components/mobile/navigation/GatherBrandMark.vue'
import GatherEventPill from '@/components/gather/GatherEventPill.vue'
import GatherSuccessSheet from '@/components/gather/GatherSuccessSheet.vue'
import MobileAttendanceScannerStage from '@/components/mobile/attendance/MobileAttendanceScannerStage.vue'
import { useGatherAttendance } from '@/composables/useGatherAttendance.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const {
  actionHint,
  cameraReady,
  canCapture,
  candidateEvents,
  currentTimeLabel,
  dismissSuccess,
  faceDetected,
  faceImageUrl,
  goBack,
  handleSubmit,
  hasEvents,
  headerEyebrow,
  isResolvingLocation,
  isSubmitting,
  locationChipLabel,
  locationMetaLabel,
  openEventsView,
  selectedEvent,
  selectEvent,
  setBackgroundVideoRef,
  setFocusVideoRef,
  statusModel,
  submitButtonLabel,
  successSheet,
} = useGatherAttendance(() => props.preview)
</script>

<style scoped>
.gather-attendance {
  position: fixed;
  inset: 0;
  background: #000000;
  overflow: hidden;
  color: #ffffff;
  font-family: 'Manrope', sans-serif;
  z-index: 100;
}

.gather-attendance__stage {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.gather-attendance__top-gradient,
.gather-attendance__bottom-gradient {
  position: absolute;
  left: 0;
  right: 0;
  z-index: 1;
  pointer-events: none;
}

.gather-attendance__top-gradient {
  top: 0;
  height: 34vh;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.72) 0%, rgba(0, 0, 0, 0.12) 62%, rgba(0, 0, 0, 0) 100%);
}

.gather-attendance__bottom-gradient {
  bottom: 0;
  height: 48vh;
  background: linear-gradient(0deg, rgba(0, 0, 0, 0.92) 0%, rgba(0, 0, 0, 0.48) 46%, rgba(0, 0, 0, 0) 100%);
}

.gather-attendance__topbar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 12;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: max(18px, env(safe-area-inset-top, 18px)) 18px 0;
}

.gather-attendance__back {
  width: 42px;
  height: 42px;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  color: #111111;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
  cursor: pointer;
}

.gather-attendance__brand {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gather-attendance__brand-copy {
  display: flex;
  align-items: center;
  gap: 10px;
}

.gather-attendance__brand-mark {
  width: 36px;
  height: 36px;
}

.gather-attendance__brand-stack {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.gather-attendance__eyebrow {
  font-size: 10px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.56);
}

.gather-attendance__title {
  font-size: 24px;
  line-height: 0.95;
  font-weight: 900;
  letter-spacing: -0.06em;
}

.gather-attendance__status {
  max-width: min(100%, 312px);
  min-height: 38px;
  padding: 10px 14px;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
  -webkit-backdrop-filter: blur(18px) saturate(155%);
  backdrop-filter: blur(18px) saturate(155%);
}

.gather-attendance__status--success {
  color: color-mix(in srgb, var(--color-nav-active) 82%, white 18%);
}

.gather-attendance__status--error {
  color: #ffb9af;
}

.gather-attendance__status-copy {
  font-size: 11px;
  line-height: 1.35;
  font-weight: 700;
}

.gather-attendance__status-spinner {
  animation: gather-attendance-spin 1s linear infinite;
}

.gather-attendance__hud {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 12;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 0 0 max(22px, calc(env(safe-area-inset-bottom, 0px) + 12px));
}

.gather-attendance__events {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 0 18px;
  scrollbar-width: none;
}

.gather-attendance__events::-webkit-scrollbar {
  display: none;
}

.gather-attendance__selection-card {
  margin: 0 18px;
  padding: 16px 18px 18px;
  border-radius: 28px;
  background:
    linear-gradient(180deg, rgba(10, 10, 10, 0.78) 0%, rgba(10, 10, 10, 0.58) 100%),
    var(--color-nav-glass-bg);
  border: 1px solid color-mix(in srgb, var(--color-nav-glass-border) 82%, transparent);
  box-shadow:
    0 18px 40px rgba(0, 0, 0, 0.26),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  backdrop-filter: blur(24px) saturate(160%);
}

.gather-attendance__selection-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.gather-attendance__selection-kicker {
  font-size: 11px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.44);
}

.gather-attendance__selection-badge {
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  line-height: 1;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.gather-attendance__selection-badge--ready {
  background: color-mix(in srgb, var(--color-nav-active) 18%, transparent);
  color: color-mix(in srgb, var(--color-nav-active) 90%, white 10%);
}

.gather-attendance__selection-badge--pending,
.gather-attendance__selection-badge--muted,
.gather-attendance__selection-badge--done {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.82);
}

.gather-attendance__selection-badge--error {
  background: rgba(255, 105, 84, 0.16);
  color: #ffbaa8;
}

.gather-attendance__selection-title {
  margin: 10px 0 0;
  font-size: clamp(22px, 6.5vw, 32px);
  line-height: 0.98;
  font-weight: 900;
  letter-spacing: -0.06em;
}

.gather-attendance__selection-meta {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.gather-attendance__selection-meta-item {
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  line-height: 1;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.82);
}

.gather-attendance__controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  gap: 18px;
  align-items: center;
  padding: 0 18px;
}

.gather-attendance__side-pill {
  min-height: 46px;
  padding: 0 14px;
  border-radius: 18px;
  background: rgba(0, 0, 0, 0.38);
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.82);
  font-size: 12px;
  line-height: 1;
  font-weight: 800;
  -webkit-backdrop-filter: blur(16px) saturate(145%);
  backdrop-filter: blur(16px) saturate(145%);
}

.gather-attendance__shutter {
  position: relative;
  width: 86px;
  height: 86px;
  border: none;
  border-radius: 999px;
  background: transparent;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.gather-attendance__shutter:disabled {
  opacity: 0.54;
  cursor: not-allowed;
}

.gather-attendance__shutter-ring,
.gather-attendance__shutter-core {
  position: absolute;
  border-radius: 999px;
}

.gather-attendance__shutter-ring {
  inset: 0;
  border: 3.5px solid rgba(255, 255, 255, 0.92);
}

.gather-attendance__shutter-core {
  inset: 12px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.18),
    0 0 26px rgba(255, 255, 255, 0.14);
}

.gather-attendance__action-copy {
  padding: 0 26px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  text-align: center;
}

.gather-attendance__action-title {
  margin: 0;
  font-size: 16px;
  line-height: 1.08;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.gather-attendance__action-meta {
  margin: 0;
  max-width: 30ch;
  font-size: 12px;
  line-height: 1.45;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.7);
}

.gather-attendance__action-meta--secondary {
  color: rgba(255, 255, 255, 0.46);
}

.gather-attendance__success-backdrop {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 24px 18px max(24px, calc(env(safe-area-inset-bottom, 0px) + 18px));
  background: rgba(0, 0, 0, 0.28);
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
}

.gather-attendance__empty {
  min-height: 100vh;
  padding: 24px 18px max(30px, calc(env(safe-area-inset-bottom, 0px) + 18px));
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-nav-active) 12%, transparent) 0%, transparent 28%),
    linear-gradient(180deg, rgba(10, 10, 10, 0.94) 0%, rgba(8, 8, 8, 1) 100%);
}

.gather-attendance__empty-card {
  width: min(100%, 380px);
  padding: 28px 22px 24px;
  border-radius: 34px;
  background:
    linear-gradient(180deg, rgba(10, 10, 10, 0.82) 0%, rgba(10, 10, 10, 0.66) 100%),
    var(--color-nav-glass-bg);
  border: 1px solid color-mix(in srgb, var(--color-nav-glass-border) 82%, transparent);
  box-shadow:
    0 24px 52px rgba(0, 0, 0, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  -webkit-backdrop-filter: blur(24px) saturate(150%);
  backdrop-filter: blur(24px) saturate(150%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
}

.gather-attendance__empty-brand {
  width: 48px;
  height: 48px;
}

.gather-attendance__empty-kicker {
  margin: 0;
  font-size: 11px;
  line-height: 1;
  font-weight: 900;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--color-nav-active) 88%, white 12%);
}

.gather-attendance__empty-title {
  margin: 0;
  font-size: clamp(28px, 8vw, 38px);
  line-height: 0.98;
  font-weight: 900;
  letter-spacing: -0.06em;
}

.gather-attendance__empty-copy {
  margin: 0;
  max-width: 28ch;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.64);
}

.gather-attendance__empty-actions {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 8px;
}

.gather-attendance__empty-button {
  width: 100%;
  min-height: 48px;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.92);
  font: inherit;
  font-size: 14px;
  font-weight: 800;
}

.gather-attendance__empty-button--primary {
  background: var(--color-nav-active);
  color: var(--color-text-always-dark);
}

.gather-success-enter-active,
.gather-success-leave-active {
  transition:
    opacity 220ms ease,
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1);
}

.gather-success-enter-from,
.gather-success-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@keyframes gather-attendance-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 360px) {
  .gather-attendance__controls {
    gap: 12px;
  }

  .gather-attendance__side-pill {
    padding-inline: 10px;
    font-size: 11px;
  }

  .gather-attendance__status {
    max-width: min(100%, 260px);
  }
}
</style>
