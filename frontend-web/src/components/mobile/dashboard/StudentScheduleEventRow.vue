<template>
  <article class="student-event-row" :class="{ 'student-event-row--expanded': expanded }">
    <div class="student-event-row__head">
      <button
        type="button"
        class="student-event-row__summary"
        @click="$emit('open-detail', item.event)"
      >
        <span class="student-event-row__icon-shell" aria-hidden="true">
          <Clock3 :size="20" :stroke-width="2.1" />
        </span>

        <span class="student-event-row__content">
          <span class="student-event-row__title">{{ item.event.name }}</span>
          <span class="student-event-row__meta">
            <template v-if="item.scopeLabel">{{ item.scopeLabel }} | </template>
            {{ item.timeRangeLabel }}
          </span>

          <span class="student-event-row__badges">
            <span
              class="student-event-row__badge"
              :class="`student-event-row__badge--${item.lifecycleStatus}`"
            >
              <span class="student-event-row__badge-dot" aria-hidden="true"></span>
              {{ item.lifecycleLabel }}
            </span>

            <span
              class="student-event-row__badge student-event-row__badge--attendance"
              :class="`student-event-row__badge--attendance-${item.attendancePill.tone}`"
            >
              {{ item.attendancePill.label }}
            </span>
          </span>
        </span>
      </button>

      <button
        type="button"
        class="student-event-row__toggle"
        :aria-expanded="expanded ? 'true' : 'false'"
        :aria-label="expanded ? 'Collapse event details' : 'Expand event details'"
        @click="$emit('toggle-expand', item.eventId)"
      >
        <ChevronDown
          :size="24"
          :stroke-width="2.2"
          class="student-event-row__toggle-icon"
          :class="{ 'student-event-row__toggle-icon--expanded': expanded }"
        />
      </button>
    </div>

    <div class="student-event-row__details" :class="{ 'student-event-row__details--expanded': expanded }">
      <div class="student-event-row__details-inner">
        <div class="student-event-row__details-card">
          <div class="student-event-row__attendance-grid">
            <div class="student-event-row__attendance-cell">
              <span class="student-event-row__attendance-label">Checked In</span>
              <strong class="student-event-row__attendance-value">{{ item.checkedInLabel }}</strong>
            </div>

            <div class="student-event-row__attendance-divider" aria-hidden="true"></div>

            <div class="student-event-row__attendance-cell">
              <span class="student-event-row__attendance-label">Checked Out</span>
              <strong class="student-event-row__attendance-value">{{ item.checkedOutLabel }}</strong>
            </div>
          </div>

          <div class="student-event-row__actions">
            <button
              type="button"
              class="student-event-row__action student-event-row__action--primary"
              :class="{ 'student-event-row__action--disabled': item.primaryAction.disabled }"
              :disabled="item.primaryAction.disabled"
              @click.stop="$emit('primary-action', item)"
            >
              {{ item.primaryAction.label }}
            </button>

            <button
              type="button"
              class="student-event-row__action student-event-row__action--secondary"
              disabled
              @click.stop
            >
              Excuse
            </button>
          </div>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup>
import { ChevronDown, Clock3 } from 'lucide-vue-next'

defineProps({
  item: {
    type: Object,
    required: true,
  },
  expanded: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['open-detail', 'toggle-expand', 'primary-action'])
</script>

<style scoped>
.student-event-row {
  border-radius: 32px;
  background: var(--color-surface);
  box-shadow: 0 16px 36px rgba(10, 10, 10, 0.06);
  overflow: hidden;
}

.student-event-row__head {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px 18px 16px;
}

.student-event-row__summary {
  flex: 1;
  min-width: 0;
  padding: 0;
  border: none;
  background: transparent;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  text-align: left;
}

.student-event-row__icon-shell {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--color-text-always-dark) 8%, var(--color-surface));
  color: var(--color-text-always-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.student-event-row__content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.student-event-row__title {
  font-size: 18px;
  line-height: 1.05;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--color-text-always-dark);
}

.student-event-row__meta {
  font-size: 12px;
  line-height: 1.35;
  font-weight: 600;
  color: var(--color-text-muted);
}

.student-event-row__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 2px;
}

.student-event-row__badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.student-event-row__badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.student-event-row__badge--ongoing {
  background: rgba(217, 45, 32, 0.08);
  color: #b42318;
}

.student-event-row__badge--upcoming {
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
}

.student-event-row__badge--completed {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
}

.student-event-row__badge--cancelled {
  background: rgba(107, 114, 128, 0.12);
  color: #4b5563;
}

.student-event-row__badge--attendance {
  gap: 0;
}

.student-event-row__badge--attendance-muted {
  background: rgba(10, 10, 10, 0.06);
  color: var(--color-text-muted);
}

.student-event-row__badge--attendance-neutral {
  background: rgba(79, 70, 229, 0.08);
  color: #4338ca;
}

.student-event-row__badge--attendance-present {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
}

.student-event-row__badge--attendance-late {
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
}

.student-event-row__badge--attendance-absent {
  background: rgba(217, 45, 32, 0.08);
  color: #b42318;
}

.student-event-row__toggle {
  width: 42px;
  height: 42px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-always-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.student-event-row__toggle-icon {
  transition: transform 280ms cubic-bezier(0.22, 1, 0.36, 1);
}

.student-event-row__toggle-icon--expanded {
  transform: rotate(180deg);
}

.student-event-row__details {
  display: grid;
  grid-template-rows: 0fr;
  opacity: 0;
  transform: translateY(-6px);
  transition:
    grid-template-rows 320ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 180ms ease,
    transform 220ms ease;
}

.student-event-row__details--expanded {
  grid-template-rows: 1fr;
  opacity: 1;
  transform: translateY(0);
}

.student-event-row__details-inner {
  min-height: 0;
  overflow: hidden;
  padding: 0 18px 18px;
}

.student-event-row__details-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 126px;
  gap: 14px;
  align-items: center;
  padding: 18px 16px;
  border-radius: 24px;
  background: color-mix(in srgb, var(--color-text-always-dark) 4%, var(--color-bg));
}

.student-event-row__attendance-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 1px minmax(0, 1fr);
  gap: 16px;
  align-items: center;
}

.student-event-row__attendance-cell {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.student-event-row__attendance-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.student-event-row__attendance-value {
  font-size: 14px;
  line-height: 1.35;
  font-weight: 700;
  color: var(--color-text-always-dark);
}

.student-event-row__attendance-divider {
  width: 1px;
  min-height: 72px;
  background: color-mix(in srgb, var(--color-text-always-dark) 12%, transparent);
}

.student-event-row__actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.student-event-row__action {
  padding: 0 14px;
  border: none;
  min-height: 44px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  text-align: center;
  line-height: 1.15;
  transition: transform 180ms ease, opacity 180ms ease, background-color 180ms ease;
}

.student-event-row__action:active:not(:disabled) {
  transform: scale(0.97);
}

.student-event-row__action--primary {
  background: var(--color-primary);
  color: var(--color-banner-text);
}

.student-event-row__action--primary.student-event-row__action--disabled {
  background: color-mix(in srgb, var(--color-text-always-dark) 10%, var(--color-surface));
  color: var(--color-text-muted);
}

.student-event-row__action--secondary {
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  border: 1px solid color-mix(in srgb, var(--color-text-always-dark) 8%, transparent);
}

.student-event-row__action--secondary:disabled {
  opacity: 1;
}

@media (max-width: 360px) {
  .student-event-row__details-card {
    grid-template-columns: 1fr;
  }
}
</style>
