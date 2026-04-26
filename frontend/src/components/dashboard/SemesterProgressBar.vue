<template>
  <div class="semester-bar" :class="{ 'semester-bar--hidden': progressPercent <= 0 }">
    <div class="semester-bar__track">
      <div
        class="semester-bar__fill"
        :style="{ width: `${clampedPercent}%` }"
      />
    </div>
    <div class="semester-bar__labels">
      <span class="semester-bar__label">{{ startLabel }}</span>
      <span class="semester-bar__value">{{ clampedPercent }}% of semester</span>
      <span class="semester-bar__label">{{ endLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  events: {
    type: Array,
    default: () => [],
  },
})

const dateRange = computed(() => {
  const dates = props.events
    .map((e) => e?.start_datetime)
    .filter(Boolean)
    .map((d) => new Date(d).getTime())
    .filter((t) => Number.isFinite(t))

  if (!dates.length) return null

  return {
    start: new Date(Math.min(...dates)),
    end: new Date(Math.max(...dates)),
  }
})

const progressPercent = computed(() => {
  if (!dateRange.value) return 0

  const { start, end } = dateRange.value
  const range = end.getTime() - start.getTime()
  if (range <= 0) return 100

  const elapsed = Date.now() - start.getTime()
  return Math.round((elapsed / range) * 100)
})

const clampedPercent = computed(() => Math.max(0, Math.min(100, progressPercent.value)))

const startLabel = computed(() => {
  if (!dateRange.value) return ''
  return dateRange.value.start.toLocaleDateString('en-PH', { month: 'short', day: 'numeric' })
})

const endLabel = computed(() => {
  if (!dateRange.value) return ''
  return dateRange.value.end.toLocaleDateString('en-PH', { month: 'short', day: 'numeric' })
})
</script>

<style scoped>
.semester-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.semester-bar--hidden {
  display: none;
}

.semester-bar__track {
  position: relative;
  height: 6px;
  border-radius: 999px;
  background: var(--color-surface);
  overflow: hidden;
}

.semester-bar__fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  border-radius: 999px;
  background: var(--color-primary);
  transition: width 1.2s cubic-bezier(0.22, 1, 0.36, 1);
  min-width: 6px;
}

.semester-bar__labels {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.semester-bar__label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.semester-bar__value {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-secondary);
}
</style>
