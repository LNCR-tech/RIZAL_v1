<template>
  <section class="gather-kiosk">
    <header class="gather-kiosk__header">
      <button
        type="button"
        class="gather-kiosk__icon-button"
        aria-label="Back"
        @click="goBack"
      >
        <ArrowLeft :size="18" :stroke-width="2.35" />
      </button>

      <div class="gather-kiosk__brand">
        <GatherBrandMark class="gather-kiosk__brand-mark" />
        <div class="gather-kiosk__brand-copy">
          <p class="gather-kiosk__eyebrow">Gather</p>
          <h1 class="gather-kiosk__title">Attendance kiosk</h1>
        </div>
      </div>

      <button
        type="button"
        class="gather-kiosk__icon-button"
        :disabled="isRefreshingLocation || scanBusy"
        :aria-label="isRefreshingLocation ? 'Refreshing location' : 'Refresh location'"
        @click="refreshGatherContext"
      >
        <LoaderCircle
          v-if="isRefreshingLocation"
          :size="18"
          :stroke-width="2.2"
          class="gather-kiosk__spinner"
        />
        <RefreshCw v-else :size="18" :stroke-width="2.2" />
      </button>
    </header>

    <div class="gather-kiosk__body">
      <section class="gather-kiosk__camera-card">
        <div class="gather-kiosk__camera-toolbar">
          <button
            type="button"
            class="gather-kiosk__camera-chip gather-kiosk__camera-chip--event"
            @click="eventSheetOpen = true"
          >
            <span class="gather-kiosk__camera-chip-label">Event</span>
            <strong class="gather-kiosk__camera-chip-value">
              {{ selectedEvent ? selectedEvent.name : (hasEvents ? 'Choose event' : 'No events yet') }}
            </strong>
            <ChevronsUpDown :size="14" :stroke-width="2.2" />
          </button>

          <button
            type="button"
            class="gather-kiosk__camera-chip gather-kiosk__camera-chip--location"
            :disabled="isRefreshingLocation || scanBusy"
            @click="refreshGatherContext"
          >
            <MapPin :size="14" :stroke-width="2.2" />
            <span>{{ locationPillLabel }}</span>
          </button>
        </div>

        <div class="gather-kiosk__camera-shell">
          <video
            ref="videoEl"
            class="gather-kiosk__camera"
            autoplay
            muted
            playsinline
            webkit-playsinline
            disablePictureInPicture
            disableRemotePlayback
            controlslist="nodownload noplaybackrate noremoteplayback"
          />

          <canvas ref="canvasEl" class="gather-kiosk__canvas" aria-hidden="true" />

          <div v-if="selectedEvent" class="gather-kiosk__camera-ui">
            <div
              class="gather-kiosk__live-indicator"
              :class="{
                'gather-kiosk__live-indicator--active': cameraOn && !scanBusy,
                'gather-kiosk__live-indicator--busy': scanBusy,
              }"
            >
              <span class="gather-kiosk__live-dot" aria-hidden="true" />
              <span>{{ scanBusy ? 'Scanning' : (cameraOn ? 'Live' : 'Standby') }}</span>
            </div>

            <div class="gather-kiosk__camera-controls">
              <button
                v-if="torchSupported"
                type="button"
                class="gather-kiosk__camera-control"
                :class="{ 'gather-kiosk__camera-control--active': torchEnabled }"
                :disabled="scanBusy || isCameraStarting"
                :aria-pressed="torchEnabled"
                :aria-label="torchEnabled ? 'Turn flash off' : 'Turn flash on'"
                @click="toggleTorch"
              >
                <Zap :size="14" :stroke-width="2.2" />
                <span>{{ torchEnabled ? 'Flash On' : 'Flash' }}</span>
              </button>

              <button
                type="button"
                class="gather-kiosk__camera-control"
                :disabled="scanBusy || isCameraStarting"
                :aria-label="`Switch camera. Current camera is ${cameraFacingLabel}.`"
                @click="toggleCameraFacing"
              >
                <RefreshCw :size="14" :stroke-width="2.2" />
                <span>{{ cameraFacingLabel }}</span>
              </button>
            </div>
          </div>

          <div
            v-if="selectedEvent"
            class="gather-kiosk__camera-grid"
            :data-facing="activeFacingMode"
            aria-hidden="true"
          >
            <span class="gather-kiosk__camera-grid-line gather-kiosk__camera-grid-line--v1" />
            <span class="gather-kiosk__camera-grid-line gather-kiosk__camera-grid-line--v2" />
            <span class="gather-kiosk__camera-grid-line gather-kiosk__camera-grid-line--v3" />
            <span class="gather-kiosk__camera-grid-line gather-kiosk__camera-grid-line--h1" />
            <span class="gather-kiosk__camera-grid-line gather-kiosk__camera-grid-line--h2" />
            <span class="gather-kiosk__camera-grid-line gather-kiosk__camera-grid-line--h3" />
          </div>

          <div v-if="showDiscoveryStage" class="gather-kiosk__discovery-stage">
            <GatherScanDiscoveryArt
              :busy="isDiscoveringNearbyEvents"
              :title="discoveryTitle"
              :description="discoveryCopy"
            />

            <div
              v-if="needsEventSelection"
              class="gather-kiosk__discovery-list"
            >
              <button
                v-for="event in nearbyEvents"
                :key="`discovery-${event.id}`"
                type="button"
                class="gather-kiosk__discovery-item"
                @click="handleEventSelect(event.id)"
              >
                <div class="gather-kiosk__discovery-top">
                  <strong>{{ event.name }}</strong>
                  <span class="gather-kiosk__discovery-phase">
                    {{ formatPhaseLabel(event.attendance_phase) }}
                  </span>
                </div>

                <p class="gather-kiosk__discovery-location">{{ event.location }}</p>

                <div class="gather-kiosk__discovery-meta">
                  <span>{{ formatDateTime(event.start_datetime) }}</span>
                  <span>{{ formatDistance(event.distance_m) }}</span>
                </div>
              </button>
            </div>

            <button
              v-else-if="!isRefreshingLocation"
              type="button"
              class="gather-kiosk__discovery-action"
              @click="loadNearbyEvents"
            >
              Scan again
            </button>
          </div>

          <div v-else-if="!cameraOn" class="gather-kiosk__camera-placeholder">
            <GatherBrandMark class="gather-kiosk__placeholder-brand" />
            <p class="gather-kiosk__placeholder-title">Live camera view</p>
            <p class="gather-kiosk__placeholder-copy">
              Allow camera access to open the Gather kiosk feed.
            </p>
          </div>

          <div v-else-if="scanBusy && !isAutomaticMode" class="gather-kiosk__camera-overlay">
            <LoaderCircle :size="22" :stroke-width="2.2" class="gather-kiosk__spinner" />
            <span>Processing capture</span>
          </div>
        </div>
      </section>

      <div class="gather-kiosk__content">
        <div
          v-if="selectedEvent"
          class="gather-kiosk__mode-switch"
          :class="`gather-kiosk__mode-switch--${scanMode}`"
          role="tablist"
          aria-label="Gather scan mode"
        >
          <button
            type="button"
            class="gather-kiosk__mode-option"
            :class="{ 'gather-kiosk__mode-option--active': isAutomaticMode }"
            :aria-selected="isAutomaticMode"
            @click="setScanMode('automatic')"
          >
            Automatic
          </button>

          <button
            type="button"
            class="gather-kiosk__mode-option"
            :class="{ 'gather-kiosk__mode-option--active': !isAutomaticMode }"
            :aria-selected="!isAutomaticMode"
            @click="setScanMode('manual')"
          >
            Manual
          </button>
        </div>

        <div v-if="selectedEvent" class="gather-kiosk__capture-row">
          <span class="gather-kiosk__capture-spacer" aria-hidden="true" />

          <div
            v-if="isAutomaticMode"
            class="gather-kiosk__auto-capture"
            :class="{
              'gather-kiosk__auto-capture--busy': scanBusy,
              'gather-kiosk__auto-capture--ready': cameraOn,
            }"
          >
            <span class="gather-kiosk__auto-dot" aria-hidden="true" />

            <div class="gather-kiosk__auto-copy">
              <strong>{{ autoModeTitle }}</strong>
              <span>{{ autoModeMeta }}</span>
            </div>
          </div>

          <button
            v-else
            type="button"
            class="gather-kiosk__capture"
            :disabled="!canCapture"
            :aria-label="scanBusy ? 'Processing capture' : 'Capture attendance'"
            @click="handleCapture"
          >
            <span class="gather-kiosk__capture-ring" />
            <span class="gather-kiosk__capture-core">
              <LoaderCircle
                v-if="scanBusy || isCameraStarting"
                :size="20"
                :stroke-width="2.15"
                class="gather-kiosk__spinner"
              />
            </span>
          </button>

          <button
            type="button"
            class="gather-kiosk__history-pill"
            aria-label="Open attendance history"
            @click="openHistorySheet"
          >
            <History :size="14" :stroke-width="2.2" />
            <span>History</span>
            <span
              v-if="attendanceHistory.length"
              class="gather-kiosk__history-pill-count"
            >
              {{ attendanceHistory.length > 99 ? '99+' : attendanceHistory.length }}
            </span>
          </button>
        </div>

        <span
          class="gather-kiosk__sr-status"
          :data-tone="statusTone"
          role="status"
          aria-live="polite"
        >
          {{ statusMessage }}
        </span>

        <div v-if="!location || !hasEvents || needsEventSelection || (selectedEvent && !cameraOn)" class="gather-kiosk__assist">
          <button
            v-if="selectedEvent && !cameraOn"
            type="button"
            class="gather-kiosk__assist-button"
            @click="startCamera"
          >
            Enable camera
          </button>

          <button
            v-if="!location"
            type="button"
            class="gather-kiosk__assist-button"
            @click="loadNearbyEvents"
          >
            Share location
          </button>

          <button
            v-if="hasEvents && !selectedEvent"
            type="button"
            class="gather-kiosk__assist-button"
            @click="eventSheetOpen = true"
          >
            Choose event
          </button>
        </div>

        <section v-if="outcomes.length" class="gather-kiosk__results">
          <header class="gather-kiosk__results-header">
            <div>
              <p class="gather-kiosk__results-eyebrow">Latest Capture</p>
              <h3 class="gather-kiosk__results-title">
                {{ lastScanAt ? formatDateTime(lastScanAt) : 'Just now' }}
              </h3>
            </div>
          </header>

          <div class="gather-kiosk__result-list">
            <article
              v-for="(outcome, index) in outcomes"
              :key="`${outcome.student_id || 'unknown'}-${outcome.action}-${index}`"
              class="gather-kiosk__result-card"
              :class="`gather-kiosk__result-card--${outcomeTone(outcome.action)}`"
            >
              <div class="gather-kiosk__result-top">
                <div class="gather-kiosk__result-copy">
                  <strong>{{ outcome.student_name || 'Unmatched face' }}</strong>
                  <span>{{ formatPhaseLabel(outcome.action === 'time_out' ? 'sign_out' : 'sign_in') }}</span>
                </div>
                <span class="gather-kiosk__result-badge">
                  {{ outcome.action.replace(/_/g, ' ') }}
                </span>
              </div>

              <p class="gather-kiosk__result-message">{{ outcome.message }}</p>

              <div class="gather-kiosk__result-meta">
                <span v-if="outcome.student_id">{{ outcome.student_id }}</span>
                <span v-if="typeof outcome.confidence === 'number'">
                  {{ `${Math.round(outcome.confidence * 100)}% confidence` }}
                </span>
                <span v-if="typeof outcome.distance === 'number'">
                  {{ formatDistance(outcome.distance) }}
                </span>
              </div>
            </article>
          </div>
        </section>
      </div>
    </div>

    <Transition name="gather-sheet">
      <div
        v-if="eventSheetOpen"
        class="gather-kiosk__sheet-backdrop"
        @click.self="eventSheetOpen = false"
      >
        <section class="gather-kiosk__sheet">
          <span class="gather-kiosk__sheet-handle" aria-hidden="true" />

          <header class="gather-kiosk__sheet-header">
            <div>
              <p class="gather-kiosk__sheet-eyebrow">Gather Events</p>
              <h2 class="gather-kiosk__sheet-title">Choose an active attendance event</h2>
            </div>

            <button
              type="button"
              class="gather-kiosk__sheet-close"
              aria-label="Close event picker"
              @click="eventSheetOpen = false"
            >
              <X :size="18" :stroke-width="2.25" />
            </button>
          </header>

          <div v-if="nearbyEvents.length" class="gather-kiosk__sheet-list">
            <button
              v-for="event in nearbyEvents"
              :key="event.id"
              type="button"
              class="gather-kiosk__sheet-item"
              :class="{ 'gather-kiosk__sheet-item--active': Number(event.id) === Number(selectedEventId) }"
              @click="handleEventSelect(event.id)"
            >
              <div class="gather-kiosk__sheet-item-copy">
                <strong>{{ event.name }}</strong>
                <span>{{ event.location }}</span>
                <small>{{ formatDateTime(event.start_datetime) }}</small>
              </div>

              <div class="gather-kiosk__sheet-item-meta">
                <span class="gather-kiosk__sheet-phase">{{ formatPhaseLabel(event.attendance_phase) }}</span>
                <span>{{ formatDistance(event.distance_m) }}</span>
              </div>
            </button>
          </div>

          <p v-else class="gather-kiosk__sheet-empty">
            Share your location first so Gather can load nearby backend events.
          </p>
        </section>
      </div>
    </Transition>

    <Transition name="gather-sheet">
      <div
        v-if="historySheetOpen"
        class="gather-kiosk__sheet-backdrop"
        @click.self="historySheetOpen = false"
      >
        <section class="gather-kiosk__sheet">
          <span class="gather-kiosk__sheet-handle" aria-hidden="true" />

          <header class="gather-kiosk__sheet-header">
            <div>
              <p class="gather-kiosk__sheet-eyebrow">Attendance History</p>
              <h2 class="gather-kiosk__sheet-title">Students marked in this Gather session</h2>
            </div>

            <button
              type="button"
              class="gather-kiosk__sheet-close"
              aria-label="Close attendance history"
              @click="historySheetOpen = false"
            >
              <X :size="18" :stroke-width="2.25" />
            </button>
          </header>

          <div v-if="hasAttendanceHistory" class="gather-kiosk__history-list">
            <article
              v-for="entry in attendanceHistory"
              :key="entry.id"
              class="gather-kiosk__history-card"
            >
              <div class="gather-kiosk__history-top">
                <div class="gather-kiosk__history-copy">
                  <strong>{{ entry.studentName }}</strong>
                  <span>{{ entry.studentId || entry.eventName }}</span>
                </div>

                <span class="gather-kiosk__history-badge">
                  {{ entry.actionLabel }}
                </span>
              </div>

              <p class="gather-kiosk__history-message">{{ entry.message }}</p>

              <div class="gather-kiosk__history-meta">
                <span>{{ entry.eventName }}</span>
                <span v-if="entry.eventLocation">{{ entry.eventLocation }}</span>
                <span>{{ formatDateTime(entry.recordedAt) }}</span>
              </div>
            </article>
          </div>

          <p v-else class="gather-kiosk__sheet-empty">
            Students marked by this Gather kiosk will appear here after the first successful attendance scan.
          </p>
        </section>
      </div>
    </Transition>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  ArrowLeft,
  ChevronsUpDown,
  History,
  LoaderCircle,
  MapPin,
  RefreshCw,
  X,
  Zap,
} from 'lucide-vue-next'
import GatherScanDiscoveryArt from '@/components/gather/GatherScanDiscoveryArt.vue'
import GatherBrandMark from '@/components/mobile/navigation/GatherBrandMark.vue'
import { useGatherKiosk } from '@/composables/useGatherKiosk.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const eventSheetOpen = ref(false)
const historySheetOpen = ref(false)

const {
  activeFacingMode,
  activateEvent,
  attendanceHistory,
  cameraFacingLabel,
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
  isDiscoveringNearbyEvents,
  isRefreshingLocation,
  lastScanAt,
  loadNearbyEvents,
  location,
  locationMessage,
  locationPillLabel,
  needsEventSelection,
  outcomeTone,
  outcomes,
  refreshGatherContext,
  scanBusy,
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
  toggleCameraFacing,
  toggleTorch,
  torchEnabled,
  torchSupported,
  videoEl,
  canvasEl,
  nearbyEvents,
} = useGatherKiosk(() => props.preview)

const discoveryTitle = computed(() => {
  if (isDiscoveringNearbyEvents.value) {
    return 'Scanning nearby events'
  }

  if (needsEventSelection.value) {
    return 'Choose a Gather event'
  }

  return 'No nearby Gather events'
})

const discoveryCopy = computed(() => {
  if (isDiscoveringNearbyEvents.value) {
    return 'Gather is checking your current location and matching open attendance events from the backend.'
  }

  if (needsEventSelection.value) {
    return 'Select one nearby event to open the live camera kiosk. You can still switch to another event later from the camera header.'
  }

  return locationMessage.value || 'Share your location to load nearby Gather events.'
})

const showDiscoveryStage = computed(() => isRefreshingLocation.value || !selectedEvent.value)
const autoModeTitle = computed(() => (scanBusy.value ? 'Scanning' : 'Automatic'))
const autoModeMeta = computed(() => {
  if (!selectedEvent.value) {
    return 'Select an event to start'
  }

  if (!cameraOn.value) {
    return 'Waiting for camera'
  }

  return 'Watching for faces'
})

async function handleEventSelect(eventId) {
  await activateEvent(eventId)
  eventSheetOpen.value = false
}

function openHistorySheet() {
  eventSheetOpen.value = false
  historySheetOpen.value = true
}
</script>

<style scoped>
.gather-kiosk {
  min-height: 100vh;
  padding:
    max(20px, calc(env(safe-area-inset-top, 0px) + 8px))
    18px
    max(36px, calc(env(safe-area-inset-bottom, 0px) + 18px));
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-nav-active) 12%, var(--color-bg)) 0%, transparent 30%),
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 52%, var(--color-bg)) 0%, var(--color-bg) 100%);
  color: var(--color-text-primary);
  font-family: 'Manrope', sans-serif;
}

.gather-kiosk__header,
.gather-kiosk__brand,
.gather-kiosk__camera-toolbar,
.gather-kiosk__camera-chip,
.gather-kiosk__camera-ui,
.gather-kiosk__camera-controls,
.gather-kiosk__camera-control,
.gather-kiosk__discovery-stage,
.gather-kiosk__discovery-list,
.gather-kiosk__discovery-item,
.gather-kiosk__discovery-top,
.gather-kiosk__discovery-meta,
.gather-kiosk__live-indicator,
.gather-kiosk__mode-switch,
.gather-kiosk__mode-option,
.gather-kiosk__auto-capture,
.gather-kiosk__auto-copy,
.gather-kiosk__assist,
.gather-kiosk__results-header,
.gather-kiosk__result-top,
.gather-kiosk__result-copy,
.gather-kiosk__sheet-header,
.gather-kiosk__sheet-item,
.gather-kiosk__sheet-item-copy,
.gather-kiosk__sheet-item-meta {
  display: flex;
}

.gather-kiosk__header,
.gather-kiosk__camera-toolbar,
.gather-kiosk__result-top,
.gather-kiosk__sheet-header,
.gather-kiosk__sheet-item {
  align-items: center;
  justify-content: space-between;
}

.gather-kiosk__header {
  gap: 14px;
}

.gather-kiosk__icon-button,
.gather-kiosk__sheet-close {
  width: 44px;
  height: 44px;
  padding: 0;
  border: 1px solid var(--color-surface-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 88%, transparent);
  color: var(--color-surface-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.gather-kiosk__icon-button:disabled {
  opacity: 0.6;
}

.gather-kiosk__brand {
  min-width: 0;
  flex: 1;
  align-items: center;
  gap: 10px;
}

.gather-kiosk__brand-mark {
  width: 34px;
  height: 34px;
}

.gather-kiosk__brand-copy,
.gather-kiosk__selection,
.gather-kiosk__result-copy,
.gather-kiosk__sheet-item-copy {
  min-width: 0;
  flex-direction: column;
}

.gather-kiosk__eyebrow,
.gather-kiosk__results-eyebrow,
.gather-kiosk__sheet-eyebrow,
.gather-kiosk__camera-chip-label {
  margin: 0;
  font-size: 10px;
  line-height: 1.1;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.gather-kiosk__eyebrow,
.gather-kiosk__results-eyebrow,
.gather-kiosk__sheet-eyebrow {
  color: var(--color-text-secondary);
}

.gather-kiosk__title,
.gather-kiosk__sheet-title,
.gather-kiosk__results-title {
  margin: 0;
  letter-spacing: -0.05em;
  color: var(--color-text-primary);
}

.gather-kiosk__title {
  font-size: 20px;
  line-height: 1;
  font-weight: 800;
}

.gather-kiosk__body {
  margin-top: 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.gather-kiosk__camera-card {
  position: relative;
  padding: 12px;
  border-radius: 32px;
  background: color-mix(in srgb, var(--color-surface) 90%, var(--color-bg));
  border: 1px solid var(--color-surface-border);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
}

.gather-kiosk__camera-toolbar {
  position: relative;
  z-index: 2;
  gap: 10px;
}

.gather-kiosk__camera-chip {
  min-height: 42px;
  padding: 0 14px;
  border: none;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 88%, transparent);
  color: var(--color-surface-text);
  align-items: center;
  gap: 8px;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.05);
}

.gather-kiosk__camera-chip--event {
  flex: 1;
  min-width: 0;
}

.gather-kiosk__camera-chip--location {
  flex: 0 0 auto;
}

.gather-kiosk__camera-chip-label {
  color: var(--color-text-secondary);
}

.gather-kiosk__camera-chip-value {
  min-width: 0;
  flex: 1;
  font-size: 13px;
  line-height: 1.2;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: left;
}

.gather-kiosk__camera-shell {
  position: relative;
  margin-top: 12px;
  min-height: min(68vh, 560px);
  border-radius: 28px;
  background:
    radial-gradient(circle at top, color-mix(in srgb, var(--color-nav-active) 10%, transparent) 0%, transparent 40%),
    color-mix(in srgb, var(--color-text-primary) 32%, var(--color-surface));
  overflow: hidden;
}

.gather-kiosk__camera-shell::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(10, 10, 10, 0.2) 0%, transparent 22%, transparent 72%, rgba(10, 10, 10, 0.26) 100%),
    radial-gradient(circle at center, transparent 48%, rgba(10, 10, 10, 0.18) 100%);
  pointer-events: none;
  z-index: 2;
}

.gather-kiosk__camera,
.gather-kiosk__discovery-stage,
.gather-kiosk__camera-placeholder,
.gather-kiosk__camera-overlay {
  position: absolute;
  inset: 0;
}

.gather-kiosk__camera {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  object-position: center center;
  transform: none;
  background: #090909;
}

.gather-kiosk__camera::-webkit-media-controls,
.gather-kiosk__camera::-webkit-media-controls-enclosure,
.gather-kiosk__camera::-webkit-media-controls-panel,
.gather-kiosk__camera::-webkit-media-controls-play-button,
.gather-kiosk__camera::-webkit-media-controls-start-playback-button,
.gather-kiosk__camera::-webkit-media-controls-overlay-play-button {
  display: none !important;
  opacity: 0 !important;
}

.gather-kiosk__canvas {
  display: none;
}

.gather-kiosk__camera-ui {
  position: absolute;
  top: 14px;
  left: 14px;
  right: 14px;
  z-index: 4;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  pointer-events: none;
}

.gather-kiosk__live-indicator,
.gather-kiosk__camera-control {
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  backdrop-filter: blur(16px) saturate(1.05);
  -webkit-backdrop-filter: blur(16px) saturate(1.05);
}

.gather-kiosk__live-indicator {
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(10, 10, 10, 0.28);
  color: rgba(255, 255, 255, 0.92);
  align-items: center;
  gap: 8px;
  font-size: 11px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.gather-kiosk__live-indicator--busy,
.gather-kiosk__live-indicator--active {
  background: rgba(10, 10, 10, 0.38);
}

.gather-kiosk__live-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.36);
}

.gather-kiosk__live-indicator--active .gather-kiosk__live-dot {
  background: #ff5449;
  box-shadow: 0 0 0 6px rgba(255, 84, 73, 0.14);
  animation: gather-kiosk-live-pulse 1.8s ease-in-out infinite;
}

.gather-kiosk__live-indicator--busy .gather-kiosk__live-dot {
  background: color-mix(in srgb, var(--color-nav-active) 80%, white 20%);
  box-shadow: 0 0 0 6px color-mix(in srgb, var(--color-nav-active) 20%, transparent);
}

.gather-kiosk__camera-controls {
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  pointer-events: auto;
}

.gather-kiosk__camera-control {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(10, 10, 10, 0.24);
  color: rgba(255, 255, 255, 0.92);
  align-items: center;
  gap: 8px;
  font-size: 12px;
  line-height: 1;
  font-weight: 700;
}

.gather-kiosk__camera-control:disabled {
  opacity: 0.58;
}

.gather-kiosk__camera-control--active {
  background: rgba(255, 255, 255, 0.22);
}

.gather-kiosk__camera-grid {
  position: absolute;
  inset: 0;
  z-index: 3;
  pointer-events: none;
}

.gather-kiosk__camera-grid-line {
  position: absolute;
  background: rgba(255, 255, 255, 0.14);
}

.gather-kiosk__camera-grid-line--v1,
.gather-kiosk__camera-grid-line--v2,
.gather-kiosk__camera-grid-line--v3 {
  top: 0;
  bottom: 0;
  width: 1px;
}

.gather-kiosk__camera-grid-line--h1,
.gather-kiosk__camera-grid-line--h2,
.gather-kiosk__camera-grid-line--h3 {
  left: 0;
  right: 0;
  height: 1px;
}

.gather-kiosk__camera-grid-line--v1 {
  left: 25%;
}

.gather-kiosk__camera-grid-line--v2 {
  left: 50%;
}

.gather-kiosk__camera-grid-line--v3 {
  left: 75%;
}

.gather-kiosk__camera-grid-line--h1 {
  top: 25%;
}

.gather-kiosk__camera-grid-line--h2 {
  top: 50%;
}

.gather-kiosk__camera-grid-line--h3 {
  top: 75%;
}

.gather-kiosk__discovery-stage,
.gather-kiosk__camera-placeholder,
.gather-kiosk__camera-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
  padding: 26px;
  z-index: 5;
}

.gather-kiosk__discovery-stage {
  justify-content: flex-start;
  gap: 18px;
  overflow-y: auto;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 94%, var(--color-bg)) 0%, color-mix(in srgb, var(--color-bg) 20%, var(--color-surface)) 100%);
}

.gather-kiosk__discovery-list {
  width: 100%;
  flex-direction: column;
  gap: 10px;
}

.gather-kiosk__discovery-item {
  width: 100%;
  padding: 15px 16px;
  border: 1px solid var(--color-surface-border);
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-bg) 32%, var(--color-surface));
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
  text-align: left;
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.05);
}

.gather-kiosk__discovery-top {
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.gather-kiosk__discovery-top strong {
  font-size: 15px;
  line-height: 1.25;
  color: var(--color-text-primary);
}

.gather-kiosk__discovery-phase {
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-nav-active) 14%, transparent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-nav-active);
  white-space: nowrap;
}

.gather-kiosk__discovery-location,
.gather-kiosk__discovery-meta {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.gather-kiosk__discovery-meta {
  flex-wrap: wrap;
  gap: 8px 12px;
}

.gather-kiosk__discovery-action {
  min-height: 42px;
  padding: 0 16px;
  border: 1px solid var(--color-surface-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 92%, transparent);
  color: var(--color-surface-text);
  font-size: 13px;
  line-height: 1;
  font-weight: 700;
}

.gather-kiosk__camera-placeholder {
  color: var(--color-surface-text);
}

.gather-kiosk__camera-overlay {
  background: color-mix(in srgb, var(--color-surface) 24%, transparent);
  color: var(--color-surface);
}

.gather-kiosk__placeholder-brand {
  width: 48px;
  height: 48px;
}

.gather-kiosk__placeholder-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.gather-kiosk__placeholder-copy,
.gather-kiosk__result-message,
.gather-kiosk__sheet-empty {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--color-text-secondary);
}

.gather-kiosk__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  text-align: center;
}

.gather-kiosk__mode-switch {
  position: relative;
  width: min(100%, 240px);
  padding: 4px;
  border: 1px solid var(--color-surface-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 92%, transparent);
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.04);
}

.gather-kiosk__mode-switch::before {
  content: '';
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 4px;
  width: calc(50% - 4px);
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-nav-active) 14%, var(--color-surface));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.62),
    0 10px 18px rgba(15, 23, 42, 0.04);
  transition: transform 220ms ease;
}

.gather-kiosk__mode-switch--manual::before {
  transform: translateX(100%);
}

.gather-kiosk__mode-option {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 38px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-secondary);
  align-items: center;
  justify-content: center;
  font-size: 13px;
  line-height: 1;
  font-weight: 700;
}

.gather-kiosk__mode-option--active {
  color: var(--color-text-primary);
}

.gather-kiosk__capture-row {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 12px;
}

.gather-kiosk__capture-spacer {
  min-height: 1px;
}

.gather-kiosk__capture {
  grid-column: 2;
  justify-self: center;
  position: relative;
  width: 92px;
  height: 92px;
  padding: 0;
  border: none;
  background: transparent;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.gather-kiosk__capture:disabled {
  opacity: 0.62;
}

.gather-kiosk__auto-capture {
  grid-column: 2;
  justify-self: center;
  min-width: 132px;
  min-height: 58px;
  padding: 0 16px;
  border: 1px solid var(--color-surface-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 94%, transparent);
  align-items: center;
  gap: 10px;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.05);
}

.gather-kiosk__auto-capture--ready {
  border-color: color-mix(in srgb, var(--color-nav-active) 24%, var(--color-surface-border));
}

.gather-kiosk__auto-capture--busy {
  border-color: color-mix(in srgb, var(--color-nav-active) 32%, var(--color-surface-border));
}

.gather-kiosk__auto-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-nav-active) 80%, white 20%);
  box-shadow: 0 0 0 6px color-mix(in srgb, var(--color-nav-active) 16%, transparent);
}

.gather-kiosk__auto-capture--busy .gather-kiosk__auto-dot,
.gather-kiosk__auto-capture--ready .gather-kiosk__auto-dot {
  animation: gather-kiosk-live-pulse 1.8s ease-in-out infinite;
}

.gather-kiosk__auto-copy {
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
}

.gather-kiosk__auto-copy strong {
  font-size: 14px;
  line-height: 1.1;
  color: var(--color-text-primary);
}

.gather-kiosk__auto-copy span {
  font-size: 11px;
  line-height: 1.35;
  color: var(--color-text-secondary);
}

.gather-kiosk__history-pill {
  grid-column: 3;
  justify-self: start;
  min-height: 42px;
  padding: 0 14px;
  border: 1px solid var(--color-surface-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 92%, transparent);
  color: var(--color-surface-text);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.05);
  white-space: nowrap;
}

.gather-kiosk__history-pill-count {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-nav-active) 18%, transparent);
  color: var(--color-nav-active);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  line-height: 1;
  font-weight: 800;
}

.gather-kiosk__capture-ring,
.gather-kiosk__capture-core {
  position: absolute;
  border-radius: 999px;
}

.gather-kiosk__capture-ring {
  inset: 0;
  border: 4px solid color-mix(in srgb, var(--color-surface) 82%, var(--color-surface-border));
}

.gather-kiosk__capture-core {
  inset: 13px;
  background: color-mix(in srgb, var(--color-surface) 96%, white 4%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.72),
    0 14px 28px rgba(15, 23, 42, 0.08);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-nav);
}

.gather-kiosk__sr-status {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.gather-kiosk__assist {
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.gather-kiosk__assist-button {
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid var(--color-surface-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 92%, transparent);
  color: var(--color-surface-text);
  font-size: 13px;
  font-weight: 700;
}

.gather-kiosk__results {
  width: 100%;
  margin-top: 4px;
  padding: 18px;
  border-radius: 28px;
  background: color-mix(in srgb, var(--color-surface) 92%, transparent);
  border: 1px solid var(--color-surface-border);
  text-align: left;
}

.gather-kiosk__results-header {
  margin-bottom: 12px;
}

.gather-kiosk__results-title {
  font-size: 19px;
  line-height: 1.05;
  font-weight: 800;
}

.gather-kiosk__result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gather-kiosk__result-card {
  padding: 14px;
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-bg) 36%, var(--color-surface));
  border: 1px solid var(--color-surface-border);
}

.gather-kiosk__result-card--success {
  border-color: color-mix(in srgb, var(--color-nav-active) 28%, var(--color-surface-border));
}

.gather-kiosk__result-card--error {
  border-color: color-mix(in srgb, #d64845 24%, var(--color-surface-border));
}

.gather-kiosk__result-top {
  gap: 12px;
}

.gather-kiosk__result-copy strong {
  font-size: 15px;
  color: var(--color-text-primary);
}

.gather-kiosk__result-copy span,
.gather-kiosk__result-meta,
.gather-kiosk__sheet-item-copy span,
.gather-kiosk__sheet-item-copy small,
.gather-kiosk__sheet-item-meta {
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.gather-kiosk__result-badge,
.gather-kiosk__sheet-phase {
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-nav-active) 14%, transparent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-nav-active);
}

.gather-kiosk__result-message {
  margin-top: 10px;
  color: var(--color-surface-text);
}

.gather-kiosk__result-meta {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.gather-kiosk__sheet-backdrop {
  position: fixed;
  inset: 0;
  z-index: 90;
  background: rgba(10, 10, 10, 0.34);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 18px 14px max(18px, calc(env(safe-area-inset-bottom, 0px) + 12px));
}

.gather-kiosk__sheet {
  width: min(100%, 420px);
  max-height: min(74vh, 620px);
  overflow: auto;
  padding: 12px 14px 16px;
  border-radius: 30px;
  background: color-mix(in srgb, var(--color-surface) 96%, var(--color-bg));
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.18);
}

.gather-kiosk__sheet-handle {
  display: block;
  width: 52px;
  height: 5px;
  border-radius: 999px;
  margin: 0 auto 12px;
  background: color-mix(in srgb, var(--color-text-primary) 16%, transparent);
}

.gather-kiosk__sheet-title {
  font-size: 22px;
  line-height: 1.02;
  font-weight: 800;
}

.gather-kiosk__sheet-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}

.gather-kiosk__history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}

.gather-kiosk__sheet-item {
  gap: 12px;
  width: 100%;
  padding: 15px 16px;
  border: 1px solid var(--color-surface-border);
  border-radius: 24px;
  background: color-mix(in srgb, var(--color-bg) 38%, var(--color-surface));
  text-align: left;
}

.gather-kiosk__sheet-item--active {
  border-color: color-mix(in srgb, var(--color-nav-active) 30%, var(--color-surface-border));
  background: color-mix(in srgb, var(--color-nav-active) 10%, var(--color-surface));
}

.gather-kiosk__sheet-item-copy {
  gap: 2px;
}

.gather-kiosk__sheet-item-copy strong {
  font-size: 15px;
  line-height: 1.25;
  color: var(--color-text-primary);
}

.gather-kiosk__sheet-item-meta {
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  text-align: right;
}

.gather-kiosk__history-card {
  padding: 15px 16px;
  border: 1px solid var(--color-surface-border);
  border-radius: 24px;
  background: color-mix(in srgb, var(--color-bg) 38%, var(--color-surface));
  text-align: left;
}

.gather-kiosk__history-top,
.gather-kiosk__history-copy,
.gather-kiosk__history-meta {
  display: flex;
}

.gather-kiosk__history-top {
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.gather-kiosk__history-copy {
  min-width: 0;
  flex-direction: column;
}

.gather-kiosk__history-copy strong {
  font-size: 15px;
  line-height: 1.25;
  color: var(--color-text-primary);
}

.gather-kiosk__history-copy span,
.gather-kiosk__history-message,
.gather-kiosk__history-meta {
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.gather-kiosk__history-badge {
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-nav-active) 14%, transparent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-nav-active);
  white-space: nowrap;
}

.gather-kiosk__history-message {
  margin: 10px 0 0;
  color: var(--color-surface-text);
}

.gather-kiosk__history-meta {
  margin-top: 10px;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.gather-kiosk__sheet-empty {
  padding: 24px 6px 10px;
  text-align: center;
}

.gather-kiosk__spinner {
  animation: gather-kiosk-spin 0.88s linear infinite;
}

.gather-sheet-enter-active,
.gather-sheet-leave-active {
  transition: opacity 220ms ease;
}

.gather-sheet-enter-active .gather-kiosk__sheet,
.gather-sheet-leave-active .gather-kiosk__sheet {
  transition: transform 260ms ease, opacity 220ms ease;
}

.gather-sheet-enter-from,
.gather-sheet-leave-to {
  opacity: 0;
}

.gather-sheet-enter-from .gather-kiosk__sheet,
.gather-sheet-leave-to .gather-kiosk__sheet {
  opacity: 0;
  transform: translateY(20px);
}

@keyframes gather-kiosk-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@keyframes gather-kiosk-live-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(255, 84, 73, 0.28);
  }

  50% {
    box-shadow: 0 0 0 7px rgba(255, 84, 73, 0.08);
  }
}

@media (max-width: 380px) {
  .gather-kiosk {
    padding-inline: 14px;
  }

  .gather-kiosk__camera-card {
    padding: 10px;
    border-radius: 28px;
  }

  .gather-kiosk__camera-shell {
    min-height: min(64vh, 520px);
    border-radius: 24px;
  }

  .gather-kiosk__capture {
    width: 86px;
    height: 86px;
  }

  .gather-kiosk__history-pill {
    min-height: 40px;
    padding-inline: 12px;
    font-size: 12px;
  }

  .gather-kiosk__camera-ui {
    top: 10px;
    left: 10px;
    right: 10px;
  }

  .gather-kiosk__camera-control,
  .gather-kiosk__live-indicator {
    min-height: 32px;
    padding-inline: 10px;
  }

  .gather-kiosk__capture-core {
    inset: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .gather-kiosk__spinner,
  .gather-sheet-enter-active,
  .gather-sheet-leave-active,
  .gather-sheet-enter-active .gather-kiosk__sheet,
  .gather-sheet-leave-active .gather-kiosk__sheet {
    animation: none;
    transition: none;
  }
}
</style>
