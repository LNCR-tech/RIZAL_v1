<template>
  <div class="upcoming-section">
    <div class="upcoming-section__header">
      <h3 class="upcoming-section__title">Upcoming Events</h3>
      <button
        v-if="events.length > maxVisible"
        class="upcoming-section__view-all"
        type="button"
        @click="$emit('view-all')"
      >
        View All
      </button>
    </div>

    <div v-if="visibleEvents.length" class="upcoming-section__list">
      <button
        v-for="event in visibleEvents"
        :key="event.id"
        class="upcoming-card"
        type="button"
        @click="$emit('select-event', event)"
      >
        <!-- Date badge -->
        <div class="upcoming-card__date">
          <span class="upcoming-card__month">{{ formatMonth(event.start_datetime) }}</span>
          <span class="upcoming-card__day">{{ formatDay(event.start_datetime) }}</span>
        </div>

        <!-- Details -->
        <div class="upcoming-card__body">
          <div class="upcoming-card__top-row">
            <span class="upcoming-card__name">{{ event.name }}</span>
            <span
              class="upcoming-card__org-tag"
              :class="`upcoming-card__org-tag--${resolveOrgKey(event)}`"
            >
              {{ resolveOrgLabel(event) }}
            </span>
          </div>
          <div class="upcoming-card__meta-row">
            <span class="upcoming-card__location">{{ event.location || 'TBA' }}</span>
            <span class="upcoming-card__time">{{ formatTime(event.start_datetime) }}</span>
          </div>
        </div>

        <!-- Status dot -->
        <span
          class="upcoming-card__status-dot"
          :class="`upcoming-card__status-dot--${normalizeStatus(event.status)}`"
          :title="normalizeStatus(event.status)"
        />
      </button>
    </div>

    <p v-else class="upcoming-section__empty">
      No upcoming events scheduled.
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  events: {
    type: Array,
    default: () => [],
  },
  maxVisible: {
    type: Number,
    default: 5,
  },
})

defineEmits(['select-event', 'view-all'])

const visibleEvents = computed(() => {
  const sorted = [...props.events].sort(
    (a, b) => new Date(a.start_datetime) - new Date(b.start_datetime)
  )
  return sorted.slice(0, props.maxVisible)
})

function resolveOrgKey(event) {
  const scope = String(event?.scope_label || '').toLowerCase()
  if (scope.includes('campus')) return 'ssg'
  return 'sg'
}

function resolveOrgLabel(event) {
  return resolveOrgKey(event) === 'ssg' ? 'SSG' : 'SG'
}

function normalizeStatus(status) {
  const s = String(status || '').toLowerCase()
  if (s === 'done') return 'completed'
  return s
}

function formatMonth(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('en', { month: 'short' }).toUpperCase()
}

function formatDay(dt) {
  if (!dt) return ''
  return new Date(dt).getDate()
}

function formatTime(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleTimeString('en-PH', { hour: 'numeric', minute: '2-digit' })
}
</script>

<style scoped>
.upcoming-section {
  display: flex;
  flex-direction: column;
  gap: clamp(14px, 3.5vw, 18px);
}

.upcoming-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.upcoming-section__title {
  margin: 0;
  font-size: clamp(16px, 4.5vw, 20px);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-text-primary);
}

.upcoming-section__view-all {
  border: none;
  background: none;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 999px;
  transition: background 0.15s ease;
}

.upcoming-section__view-all:hover {
  background: rgba(10, 10, 10, 0.04);
}

.upcoming-section__list {
  display: flex;
  flex-direction: column;
  gap: clamp(8px, 2vw, 12px);
}

.upcoming-card {
  display: flex;
  align-items: center;
  gap: clamp(12px, 3vw, 16px);
  padding: clamp(12px, 3.5vw, 16px);
  border-radius: 20px;
  background: var(--color-surface);
  border: 1px solid rgba(10, 10, 10, 0.04);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  text-align: left;
}

.upcoming-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.05);
}

.upcoming-card:active {
  transform: scale(0.99);
}

.upcoming-card__date {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: clamp(42px, 12vw, 50px);
  height: clamp(50px, 14vw, 58px);
  border-radius: 16px;
  background: var(--color-primary);
  flex-shrink: 0;
}

.upcoming-card__month {
  font-size: 10px;
  font-weight: 700;
  color: var(--color-banner-text);
  letter-spacing: 0.04em;
}

.upcoming-card__day {
  font-size: clamp(18px, 5vw, 22px);
  font-weight: 800;
  line-height: 1;
  color: var(--color-banner-text);
}

.upcoming-card__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.upcoming-card__top-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upcoming-card__name {
  font-size: clamp(13px, 3.5vw, 14px);
  font-weight: 700;
  color: var(--color-surface-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.upcoming-card__org-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.upcoming-card__org-tag--ssg {
  background: rgba(99, 102, 241, 0.12);
  color: #4F46E5;
}

.upcoming-card__org-tag--sg {
  background: rgba(139, 92, 246, 0.12);
  color: #7C3AED;
}

.upcoming-card__meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-surface-text-muted);
}

.upcoming-card__status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.upcoming-card__status-dot--upcoming {
  background: var(--color-primary);
  animation: dot-pulse 2s ease-in-out infinite;
}

.upcoming-card__status-dot--ongoing {
  background: var(--color-status-compliant);
  animation: dot-pulse 1.5s ease-in-out infinite;
}

.upcoming-card__status-dot--completed {
  background: var(--color-surface-text-muted);
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.7); }
}

.upcoming-section__empty {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-muted);
  text-align: center;
  padding: 32px 16px;
}
</style>
