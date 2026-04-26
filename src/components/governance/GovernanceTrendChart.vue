<template>
  <div class="governance-trend-chart">
    <div class="governance-trend-chart__frame">
      <svg
        v-if="hasPoints"
        class="governance-trend-chart__svg"
        viewBox="0 0 320 180"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <g class="governance-trend-chart__grid">
          <line
            v-for="gridLine in gridLines"
            :key="gridLine"
            x1="20"
            :y1="gridLine"
            x2="300"
            :y2="gridLine"
          />
        </g>
        <path class="governance-trend-chart__fill" :d="fillPath" />
        <path class="governance-trend-chart__line" :d="linePath" />
        <circle
          v-for="point in plottedPoints"
          :key="point.key"
          class="governance-trend-chart__point"
          :cx="point.x"
          :cy="point.y"
          r="4.5"
        />
      </svg>
    </div>

    <div class="governance-trend-chart__labels">
      <div
        v-for="point in plottedPoints"
        :key="`${point.key}-label`"
        class="governance-trend-chart__label"
      >
        <strong>{{ point.label }}</strong>
        <span>{{ point.valueLabel }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  points: {
    type: Array,
    default: () => [],
  },
})

const normalizedPoints = computed(() => (
  (Array.isArray(props.points) ? props.points : []).map((point, index) => ({
    key: point?.key || `${point?.label || 'point'}-${index}`,
    label: String(point?.label || ''),
    value: Number(point?.value) || 0,
    valueLabel: String(point?.valueLabel || point?.value || '0'),
  }))
))

const hasPoints = computed(() => normalizedPoints.value.length > 1)
const maxValue = computed(() => Math.max(1, ...normalizedPoints.value.map((point) => point.value)))
const minValue = computed(() => Math.min(0, ...normalizedPoints.value.map((point) => point.value)))
const innerWidth = 280
const innerHeight = 120
const xOffset = 20
const yOffset = 24

const plottedPoints = computed(() => {
  const values = normalizedPoints.value
  if (!values.length) return []

  const range = Math.max(1, maxValue.value - minValue.value)

  return values.map((point, index) => {
    const progress = values.length === 1 ? 0.5 : index / (values.length - 1)
    const x = xOffset + (innerWidth * progress)
    const normalized = (point.value - minValue.value) / range
    const y = yOffset + (innerHeight - (innerHeight * normalized))

    return {
      ...point,
      x,
      y,
    }
  })
})

const linePath = computed(() => {
  if (!hasPoints.value) return ''
  return plottedPoints.value.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ')
})

const fillPath = computed(() => {
  if (!hasPoints.value) return ''
  const points = plottedPoints.value
  const first = points[0]
  const last = points[points.length - 1]
  return `${linePath.value} L ${last.x} ${yOffset + innerHeight} L ${first.x} ${yOffset + innerHeight} Z`
})

const gridLines = computed(() => [24, 64, 104, 144])
</script>

<style scoped>
.governance-trend-chart {
  display: grid;
  gap: 14px;
}

.governance-trend-chart__frame {
  min-height: 180px;
  border-radius: 24px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-primary) 5%, transparent), transparent 38%),
    color-mix(in srgb, var(--color-bg) 50%, var(--color-surface));
}

.governance-trend-chart__svg {
  width: 100%;
  height: 180px;
  display: block;
}

.governance-trend-chart__grid line {
  stroke: color-mix(in srgb, var(--color-text-muted) 16%, transparent);
  stroke-width: 1;
  stroke-dasharray: 4 6;
}

.governance-trend-chart__fill {
  fill: color-mix(in srgb, var(--color-primary) 14%, transparent);
}

.governance-trend-chart__line {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 4;
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 10px 18px color-mix(in srgb, var(--color-primary) 22%, transparent));
}

.governance-trend-chart__point {
  fill: var(--color-surface);
  stroke: var(--color-primary);
  stroke-width: 3;
}

.governance-trend-chart__labels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(66px, 1fr));
  gap: 10px;
}

.governance-trend-chart__label {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.governance-trend-chart__label strong {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-trend-chart__label span {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-primary);
}
</style>
