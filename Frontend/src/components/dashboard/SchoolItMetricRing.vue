<template>
  <div
    class="school-it-metric-ring"
    :class="{
      'school-it-metric-ring--compact': compact,
    }"
    :style="ringStyle"
  >
    <svg
      class="school-it-metric-ring__svg"
      viewBox="0 0 120 120"
      aria-hidden="true"
    >
      <path
        class="school-it-metric-ring__track"
        :d="arcPath"
        pathLength="100"
      />

      <path
        class="school-it-metric-ring__arc"
        :d="arcPath"
        pathLength="100"
        :style="progressStyle"
      />

      <circle
        class="school-it-metric-ring__dot"
        :cx="startPoint.x"
        :cy="startPoint.y"
        r="3.5"
        :style="dotStyle"
      />
      <circle
        class="school-it-metric-ring__dot"
        :cx="progressEndPoint.x"
        :cy="progressEndPoint.y"
        r="3.5"
        :style="dotStyle"
      />
    </svg>

    <span class="school-it-metric-ring__value">{{ displayValue }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: [Number, String],
    default: null,
  },
  delay: {
    type: Number,
    default: 0,
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

const radius = 34
const center = 60
const startAngle = 34
const sweepAngle = -164

const arcPath = computed(() => describeArcBySweep(center, center, radius, startAngle, sweepAngle))
const normalizedValue = computed(() => normalizeValue(props.value))

const startPoint = computed(() => polarToCartesian(center, center, radius, startAngle))
const progressEndPoint = computed(() => {
  const ratio = (normalizedValue.value ?? 0) / 100
  return polarToCartesian(center, center, radius, startAngle + (sweepAngle * ratio))
})

const displayValue = computed(() => {
  return normalizedValue.value == null ? '--%' : `${normalizedValue.value}%`
})

const ringStyle = computed(() => ({
  '--ring-size': props.compact ? '128px' : '158px',
  '--ring-stroke': props.compact ? '11' : '12',
  '--ring-value-size': props.compact ? '16px' : '17px',
  '--ring-delay': `${props.delay}s`,
  '--ring-progress': `${normalizedValue.value ?? 0}`,
}))

const progressStyle = computed(() => ({
  strokeDasharray: '100',
  strokeDashoffset: '100',
}))

const dotStyle = computed(() => ({
  '--ring-dot-opacity': (normalizedValue.value ?? 0) > 0 ? 1 : 0,
}))

function normalizeValue(value) {
  if (value == null || value === '') return null
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return null
  return Math.max(0, Math.min(100, Math.round(normalized)))
}

function polarToCartesian(cx, cy, arcRadius, angleInDegrees) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0

  return {
    x: cx + (arcRadius * Math.cos(angleInRadians)),
    y: cy + (arcRadius * Math.sin(angleInRadians)),
  }
}

function describeArcBySweep(cx, cy, arcRadius, start, sweep) {
  const end = start + sweep
  const nextStart = polarToCartesian(cx, cy, arcRadius, start)
  const nextEnd = polarToCartesian(cx, cy, arcRadius, end)
  const largeArcFlag = Math.abs(sweep) > 180 ? '1' : '0'
  const sweepFlag = sweep >= 0 ? '1' : '0'

  return [
    'M', nextStart.x, nextStart.y,
    'A', arcRadius, arcRadius, 0, largeArcFlag, sweepFlag, nextEnd.x, nextEnd.y,
  ].join(' ')
}
</script>

<style scoped>
.school-it-metric-ring {
  position: relative;
  width: var(--ring-size);
  height: var(--ring-size);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.school-it-metric-ring__svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.school-it-metric-ring__track {
  fill: none;
  stroke: color-mix(in srgb, var(--color-primary) 16%, #efefe7 84%);
  stroke-width: var(--ring-stroke);
  stroke-linecap: round;
}

.school-it-metric-ring__arc {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: var(--ring-stroke);
  stroke-linecap: round;
  stroke-dasharray: 100;
  stroke-dashoffset: 100;
  animation: schoolItRingDraw 1.05s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: var(--ring-delay);
}

.school-it-metric-ring__dot {
  fill: var(--color-text-always-dark);
  opacity: 0;
  animation: schoolItRingFade 0.4s ease forwards;
  animation-delay: calc(var(--ring-delay) + 0.52s);
}

.school-it-metric-ring__value {
  position: absolute;
  inset: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-always-dark);
  font-size: var(--ring-value-size);
  line-height: 1;
  font-weight: 700;
  letter-spacing: -0.05em;
  opacity: 0;
  transform: translateY(6px);
  animation: schoolItRingValueIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: calc(var(--ring-delay) + 0.28s);
}

.school-it-metric-ring--compact .school-it-metric-ring__value {
  font-weight: 600;
}

@keyframes schoolItRingDraw {
  from {
    stroke-dashoffset: 100;
  }
  to {
    stroke-dashoffset: calc(100 - var(--ring-progress));
  }
}

@keyframes schoolItRingFade {
  from {
    opacity: 0;
  }
  to {
    opacity: var(--ring-dot-opacity);
  }
}

@keyframes schoolItRingValueIn {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .school-it-metric-ring__arc,
  .school-it-metric-ring__dot,
  .school-it-metric-ring__value {
    animation: none;
    opacity: 1;
    transform: none;
    stroke-dashoffset: calc(100 - var(--ring-progress));
  }

  .school-it-metric-ring__dot {
    opacity: var(--ring-dot-opacity);
  }
}
</style>
