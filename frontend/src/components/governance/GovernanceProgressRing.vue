<template>
  <div
    class="governance-progress-ring"
    :style="{
      '--ring-size': `${size}px`,
      '--ring-stroke-width': `${strokeWidth}px`,
    }"
  >
    <svg
      class="governance-progress-ring__svg"
      :viewBox="`0 0 ${viewBoxSize} ${viewBoxSize}`"
      aria-hidden="true"
    >
      <circle
        class="governance-progress-ring__track"
        :cx="center"
        :cy="center"
        :r="radius"
      />
      <circle
        class="governance-progress-ring__progress"
        :cx="center"
        :cy="center"
        :r="radius"
        :style="{
          strokeDasharray: `${circumference}px`,
          strokeDashoffset: `${dashOffset}px`,
        }"
      />
    </svg>

    <div class="governance-progress-ring__content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  percentage: {
    type: Number,
    default: 0,
  },
  size: {
    type: Number,
    default: 172,
  },
  strokeWidth: {
    type: Number,
    default: 10,
  },
})

const safePercentage = computed(() => {
  const normalized = Number(props.percentage)
  if (!Number.isFinite(normalized)) return 0
  return Math.max(0, Math.min(100, normalized))
})

const viewBoxSize = 120
const center = viewBoxSize / 2
const radius = computed(() => center - (props.strokeWidth / 2))
const circumference = computed(() => 2 * Math.PI * radius.value)
const dashOffset = computed(() => {
  return circumference.value - ((safePercentage.value / 100) * circumference.value)
})
</script>

<style scoped>
.governance-progress-ring {
  position: relative;
  width: var(--ring-size);
  height: var(--ring-size);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.governance-progress-ring__svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.governance-progress-ring__track,
.governance-progress-ring__progress {
  fill: none;
  stroke-width: var(--ring-stroke-width);
}

.governance-progress-ring__track {
  stroke: color-mix(in srgb, var(--color-primary) 12%, var(--color-surface));
}

.governance-progress-ring__progress {
  stroke: var(--color-primary);
  stroke-linecap: round;
  transition: stroke-dashoffset 0.35s ease;
  filter: drop-shadow(0 0 16px color-mix(in srgb, var(--color-primary) 35%, transparent));
}

.governance-progress-ring__content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 4px;
}
</style>
