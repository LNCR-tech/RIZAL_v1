<template>
  <Transition name="event-editor-sheet">
    <div
      v-if="isOpen"
      class="event-editor__backdrop"
      @click.self="emit('close')"
    >
      <section
        class="event-editor__sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="event-editor-title"
      >
        <span class="event-editor__handle" aria-hidden="true"></span>

        <header class="event-editor__header">
          <div>
            <p class="event-editor__eyebrow">Event</p>
            <h2 id="event-editor-title" class="event-editor__title">{{ title }}</h2>
          </div>

          <button
            class="event-editor__close"
            type="button"
            aria-label="Close event editor"
            :disabled="saving"
            @click="emit('close')"
          >
            <X :size="18" />
          </button>
        </header>

        <form class="event-editor__form" @submit.prevent="handleSubmit">
          <section class="event-editor__section">
            <header class="event-editor__section-header">
              <MapPin :size="17" aria-hidden="true" />
              <h3>Details</h3>
            </header>

            <div class="event-editor__grid event-editor__grid--single">
              <label class="event-editor__field">
                <span class="event-editor__field-label">Name</span>
                <input
                  v-model="draft.name"
                  class="event-editor__field-input"
                  type="text"
                  name="event_name"
                  placeholder="Campus Orientation"
                  autocomplete="off"
                >
              </label>
            </div>
          </section>

          <section class="event-editor__section">
            <header class="event-editor__section-header">
              <CalendarClock :size="17" aria-hidden="true" />
              <h3>Schedule</h3>
            </header>

            <div class="event-editor__grid">
              <label class="event-editor__field">
                <span class="event-editor__field-label">Starts</span>
                <input
                  v-model="draft.startTime"
                  class="event-editor__field-input"
                  type="datetime-local"
                  name="event_start_datetime"
                >
              </label>

              <label class="event-editor__field">
                <span class="event-editor__field-label">Ends</span>
                <input
                  v-model="draft.endTime"
                  class="event-editor__field-input"
                  type="datetime-local"
                  name="event_end_datetime"
                >
              </label>
            </div>
          </section>

          <section class="event-editor__section">
            <header class="event-editor__section-header">
              <SlidersHorizontal :size="17" aria-hidden="true" />
              <h3>Attendance</h3>
            </header>

            <div class="event-editor__grid event-editor__grid--compact">
              <label class="event-editor__field">
                <span class="event-editor__field-label">Check-in opens</span>
                <span class="event-editor__input-unit">
                  <input
                    v-model="draft.earlyCheckInMinutes"
                    class="event-editor__field-input"
                    type="number"
                    min="0"
                    step="1"
                    name="event_early_check_in_minutes"
                    inputmode="numeric"
                  >
                  <span>min</span>
                </span>
              </label>

              <label class="event-editor__field">
                <span class="event-editor__field-label">Late after</span>
                <span class="event-editor__input-unit">
                  <input
                    v-model="draft.lateThresholdMinutes"
                    class="event-editor__field-input"
                    type="number"
                    min="0"
                    step="1"
                    name="event_late_threshold_minutes"
                    inputmode="numeric"
                  >
                  <span>min</span>
                </span>
              </label>

              <label class="event-editor__field">
                <span class="event-editor__field-label">Sign-out grace</span>
                <span class="event-editor__input-unit">
                  <input
                    v-model="draft.signOutGraceMinutes"
                    class="event-editor__field-input"
                    type="number"
                    min="0"
                    step="1"
                    name="event_sign_out_grace_minutes"
                    inputmode="numeric"
                  >
                  <span>min</span>
                </span>
              </label>

              <label class="event-editor__field">
                <span class="event-editor__field-label">Sign-out delay</span>
                <span class="event-editor__input-unit">
                  <input
                    v-model="draft.signOutOpenDelayMinutes"
                    class="event-editor__field-input"
                    type="number"
                    min="0"
                    step="1"
                    name="event_sign_out_open_delay_minutes"
                    inputmode="numeric"
                  >
                  <span>min</span>
                </span>
              </label>
            </div>
          </section>

          <section class="event-editor__section event-editor__section--location">
            <header class="event-editor__section-header event-editor__section-header--split">
              <div>
                <div class="event-editor__section-title">
                  <ShieldCheck :size="17" aria-hidden="true" />
                  <h3>Location</h3>
                </div>
                <p class="event-editor__section-copy">{{ geofenceSummary }}</p>
              </div>

              <label class="event-editor__switch">
                <input
                  v-model="draft.geoRequired"
                  type="checkbox"
                  name="event_geo_required"
                >
                <span class="event-editor__switch-track"></span>
                <span class="event-editor__switch-text">Required</span>
              </label>
            </header>

            <div class="event-editor__grid event-editor__grid--compact">
              <label class="event-editor__field">
                <span class="event-editor__field-label">Radius</span>
                <span class="event-editor__input-unit">
                  <input
                    v-model="draft.radiusM"
                    class="event-editor__field-input"
                    type="number"
                    min="1"
                    step="1"
                    name="event_geo_radius_m"
                    placeholder="100"
                    inputmode="numeric"
                  >
                  <span>m</span>
                </span>
              </label>

              <label class="event-editor__field">
                <span class="event-editor__field-label">GPS accuracy</span>
                <span class="event-editor__input-unit">
                  <input
                    v-model="draft.maxAccuracyM"
                    class="event-editor__field-input"
                    type="number"
                    min="1"
                    step="1"
                    name="event_geo_max_accuracy"
                    placeholder="50"
                    inputmode="numeric"
                  >
                  <span>m</span>
                </span>
              </label>
            </div>

            <EventLocationPicker
              v-model:location-label="draft.location"
              v-model:latitude="draft.latitude"
              v-model:longitude="draft.longitude"
              :radius-m="draft.radiusM"
              :disabled="saving"
            />
          </section>

          <p
            v-if="feedbackMessage"
            class="event-editor__feedback"
            :class="{ 'event-editor__feedback--error': feedbackTone === 'error' }"
          >
            {{ feedbackMessage }}
          </p>

          <div class="event-editor__actions">
            <button
              class="event-editor__secondary"
              type="button"
              :disabled="saving"
              @click="emit('close')"
            >
              Cancel
            </button>

            <button
              class="event-editor__primary"
              type="submit"
              :disabled="saving"
            >
              {{ saving ? 'Saving...' : submitLabel }}
            </button>
          </div>
        </form>
      </section>
    </div>
  </Transition>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  CalendarClock,
  MapPin,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from 'lucide-vue-next'
import EventLocationPicker from '@/components/events/EventLocationPicker.vue'
import {
  buildEventUpdatePayloadFromDraft,
  createEventEditorDraft,
} from '@/services/eventEditor.js'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  event: {
    type: Object,
    default: null,
  },
  title: {
    type: String,
    default: 'Edit Event',
  },
  description: {
    type: String,
    default: 'Update event details.',
  },
  submitLabel: {
    type: String,
    default: 'Save Event',
  },
  saving: {
    type: Boolean,
    default: false,
  },
  errorMessage: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close', 'save'])

const draft = ref(createEventEditorDraft())
const localError = ref('')

const feedbackMessage = computed(() => localError.value || props.errorMessage)
const feedbackTone = computed(() => (localError.value || props.errorMessage ? 'error' : 'info'))
const hasGeofencePoint = computed(() => {
  const latitude = Number(draft.value?.latitude)
  const longitude = Number(draft.value?.longitude)
  const radius = Number(draft.value?.radiusM)
  return Number.isFinite(latitude) && Number.isFinite(longitude) && Number.isFinite(radius) && radius > 0
})
const geofenceSummary = computed(() => {
  if (draft.value?.geoRequired) {
    return hasGeofencePoint.value ? 'Location check is required.' : 'Pick a point and radius.'
  }

  return hasGeofencePoint.value ? 'Location saved as optional.' : 'Optional.'
})

watch(
  () => [props.isOpen, props.event],
  ([isOpen]) => {
    if (!isOpen) return
    draft.value = createEventEditorDraft(props.event)
    localError.value = ''
  },
  { immediate: true }
)

function handleSubmit() {
  try {
    localError.value = ''
    emit('save', buildEventUpdatePayloadFromDraft(draft.value))
  } catch (error) {
    localError.value = error?.message || 'Unable to prepare the event update.'
  }
}
</script>

<style scoped>
.event-editor__backdrop {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 10px;
  background: rgba(10, 10, 10, 0.34);
  backdrop-filter: blur(10px);
}

.event-editor__sheet {
  width: min(100%, 760px);
  max-height: calc(100dvh - 20px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 18px;
  background: var(--color-surface);
  color: var(--color-text-always-dark, #111827);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.22);
}

.event-editor__handle {
  width: 44px;
  height: 5px;
  border-radius: 999px;
  margin: 10px auto 2px;
  background: rgba(17, 24, 39, 0.16);
  flex-shrink: 0;
}

.event-editor__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 18px 14px;
  border-bottom: 1px solid rgba(17, 24, 39, 0.08);
  flex-shrink: 0;
}

.event-editor__eyebrow {
  margin: 0 0 3px;
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted, #9ca3af);
}

.event-editor__title {
  margin: 0;
  font-size: 22px;
  line-height: 1.15;
  font-weight: 800;
  color: var(--color-text-always-dark, #111827);
}

.event-editor__close {
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.06);
  color: var(--color-text-always-dark, #111827);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: transform 150ms ease, background 150ms ease;
}

.event-editor__close:active {
  transform: scale(0.96);
}

.event-editor__form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 0 18px 18px;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.event-editor__section {
  display: grid;
  gap: 14px;
  padding-top: 18px;
  border-top: 1px solid rgba(17, 24, 39, 0.08);
}

.event-editor__section:first-child {
  border-top: none;
}

.event-editor__section-header,
.event-editor__section-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.event-editor__section-header {
  color: var(--color-primary, #3b82f6);
}

.event-editor__section-header h3,
.event-editor__section-title h3 {
  margin: 0;
  font-size: 14px;
  line-height: 1.2;
  font-weight: 900;
  color: var(--color-text-always-dark, #111827);
}

.event-editor__section-header--split {
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.event-editor__section-copy {
  margin: 6px 0 0;
  color: var(--color-text-secondary, #6b7280);
  font-size: 12px;
  line-height: 1.35;
  font-weight: 700;
}

.event-editor__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.event-editor__grid--single {
  grid-template-columns: 1fr;
}

.event-editor__grid--compact {
  gap: 10px;
}

.event-editor__field {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.event-editor__field-label {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.04em;
  color: var(--color-text-secondary, #6b7280);
  text-transform: uppercase;
}

.event-editor__field-input {
  width: 100%;
  min-height: 46px;
  padding: 11px 13px;
  border: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 8px;
  background: #fff;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-always-dark, #111827);
  outline: none;
  box-sizing: border-box;
}

.event-editor__field-input:focus,
.event-editor__input-unit:focus-within {
  border-color: color-mix(in srgb, var(--color-primary, #3b82f6) 60%, white);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary, #3b82f6) 16%, transparent);
}

.event-editor__field-input::placeholder {
  color: var(--color-text-muted, #9ca3af);
}

.event-editor__input-unit {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  min-height: 46px;
  border: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.event-editor__input-unit .event-editor__field-input {
  min-height: 44px;
  border: none;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.event-editor__input-unit > span {
  padding: 0 12px;
  color: var(--color-text-muted, #9ca3af);
  font-size: 12px;
  font-weight: 900;
}

.event-editor__switch {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  min-height: 34px;
  color: var(--color-text-always-dark, #111827);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  white-space: nowrap;
}

.event-editor__switch input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.event-editor__switch-track {
  position: relative;
  width: 42px;
  height: 24px;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.16);
  transition: background 160ms ease, box-shadow 160ms ease;
}

.event-editor__switch-track::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 3px 8px rgba(17, 24, 39, 0.2);
  transition: transform 160ms ease;
}

.event-editor__switch input:checked + .event-editor__switch-track {
  background: var(--color-primary, #3b82f6);
}

.event-editor__switch input:checked + .event-editor__switch-track::after {
  transform: translateX(18px);
}

.event-editor__switch input:focus-visible + .event-editor__switch-track {
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary, #3b82f6) 20%, transparent);
}

.event-editor__feedback {
  margin: 0;
  padding: 12px 13px;
  border-radius: 8px;
  background: rgba(37, 99, 235, 0.08);
  font-size: 13px;
  font-weight: 800;
  line-height: 1.4;
  color: #1d4ed8;
}

.event-editor__feedback--error {
  background: rgba(220, 38, 38, 0.1);
  color: #b91c1c;
}

.event-editor__actions {
  position: sticky;
  bottom: 0;
  z-index: 2;
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid rgba(17, 24, 39, 0.08);
  background: var(--color-surface);
}

.event-editor__secondary,
.event-editor__primary {
  min-height: 46px;
  border: none;
  border-radius: 8px;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  transition: transform 150ms ease, filter 150ms ease;
}

.event-editor__secondary {
  background: rgba(17, 24, 39, 0.07);
  color: var(--color-text-always-dark, #111827);
}

.event-editor__primary {
  background: var(--color-primary, #3b82f6);
  color: var(--color-primary-text, #fff);
}

.event-editor__secondary:active,
.event-editor__primary:active {
  transform: scale(0.98);
}

.event-editor__secondary:disabled,
.event-editor__primary:disabled,
.event-editor__close:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.event-editor-sheet-enter-active,
.event-editor-sheet-leave-active {
  transition: opacity 0.22s ease;
}

.event-editor-sheet-enter-active .event-editor__sheet,
.event-editor-sheet-leave-active .event-editor__sheet {
  transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.22s ease;
}

.event-editor-sheet-enter-from,
.event-editor-sheet-leave-to {
  opacity: 0;
}

.event-editor-sheet-enter-from .event-editor__sheet,
.event-editor-sheet-leave-to .event-editor__sheet {
  transform: translateY(22px);
  opacity: 0;
}

@media (min-width: 761px) {
  .event-editor__backdrop {
    align-items: center;
    padding: 24px;
  }

  .event-editor__sheet {
    max-height: calc(100dvh - 48px);
  }

  .event-editor__handle {
    display: none;
  }

  .event-editor__header {
    padding: 22px 24px 16px;
  }

  .event-editor__form {
    padding: 0 24px 24px;
  }
}

@media (max-width: 520px) {
  .event-editor__backdrop {
    padding: 0;
  }

  .event-editor__sheet {
    width: 100%;
    max-height: 94dvh;
    border-radius: 18px 18px 0 0;
  }

  .event-editor__grid,
  .event-editor__grid--compact {
    grid-template-columns: 1fr;
  }

  .event-editor__section-header--split {
    align-items: stretch;
    flex-direction: column;
  }

  .event-editor__switch {
    justify-content: space-between;
    width: 100%;
    padding: 8px 0 2px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .event-editor-sheet-enter-active,
  .event-editor-sheet-leave-active,
  .event-editor-sheet-enter-active .event-editor__sheet,
  .event-editor-sheet-leave-active .event-editor__sheet,
  .event-editor__close,
  .event-editor__secondary,
  .event-editor__primary,
  .event-editor__status-option,
  .event-editor__switch-track,
  .event-editor__switch-track::after {
    transition: none;
  }
}
</style>
