<template>
  <div ref="rootRef" class="governance-arrival-curve">
    <div class="governance-arrival-curve__scroller">
      <div class="governance-arrival-curve__canvas" :style="{ width: `${canvasWidth}px` }">
        <svg
          class="governance-arrival-curve__chart"
          :viewBox="`0 0 ${canvasWidth} ${viewportHeight}`"
          role="img"
          :aria-label="ariaLabel"
        >
          <defs>
            <linearGradient :id="`${uid}-area`" x1="0" y1="0" x2="0" :y2="viewportHeight">
              <stop offset="0%" stop-color="color-mix(in srgb, var(--color-primary) 34%, white)" />
              <stop offset="100%" stop-color="color-mix(in srgb, var(--color-primary) 8%, transparent)" />
            </linearGradient>
            <linearGradient :id="`${uid}-line`" x1="0" y1="0" x2="0" :y2="viewportHeight">
              <stop offset="0%" stop-color="color-mix(in srgb, var(--color-primary) 78%, white)" />
              <stop offset="100%" stop-color="color-mix(in srgb, var(--color-primary) 58%, white)" />
            </linearGradient>
          </defs>

          <g aria-hidden="true">
            <g v-for="tick in yAxisTicks" :key="tick.key">
              <line
                class="governance-arrival-curve__grid-line"
                :x1="padding.left"
                :x2="canvasWidth - padding.right"
                :y1="tick.y"
                :y2="tick.y"
              />
              <text
                class="governance-arrival-curve__y-label"
                :x="padding.left - 10"
                :y="tick.y + 4"
                text-anchor="end"
              >
                {{ tick.label }}
              </text>
            </g>

            <rect
              v-if="peakPoint"
              class="governance-arrival-curve__highlight"
              :x="peakPoint.x - highlightWidth / 2"
              :y="padding.top + 6"
              :width="highlightWidth"
              :height="plotHeight + 2"
              rx="22"
            />

            <path
              v-if="areaPath"
              class="governance-arrival-curve__area"
              :d="areaPath"
              :fill="`url(#${uid}-area)`"
            />

            <path
              v-if="linePath"
              class="governance-arrival-curve__line"
              :d="linePath"
              :stroke="`url(#${uid}-line)`"
            />

            <g
              v-if="peakBadge"
              class="governance-arrival-curve__badge"
              :transform="`translate(${peakBadge.x} ${peakBadge.y})`"
            >
              <rect
                :x="-peakBadge.width / 2"
                y="0"
                :width="peakBadge.width"
                height="44"
                rx="22"
              />
              <text x="0" y="16" text-anchor="middle">
                {{ peakBadge.label }}
              </text>
              <text x="0" y="31" text-anchor="middle">
                {{ peakBadge.value }}
              </text>
            </g>

            <circle
              v-for="point in chartPointsWithPeak"
              :key="point.key"
              class="governance-arrival-curve__point"
              :class="{ 'is-peak': point.isPeak }"
              :cx="point.x"
              :cy="point.y"
              :r="point.isPeak ? 6.5 : 2.5"
            />

            <circle
              v-if="peakPoint"
              class="governance-arrival-curve__peak-core"
              :cx="peakPoint.x"
              :cy="peakPoint.y"
              r="4"
            />

            <text
              v-for="label in xAxisLabels"
              :key="label.key"
              class="governance-arrival-curve__x-label"
              :x="label.x"
              :y="viewportHeight - 6"
              text-anchor="middle"
            >
              {{ label.label }}
            </text>
          </g>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  insight: {
    type: Object,
    default: () => ({}),
  },
})

const rootRef = ref(null)
const containerWidth = ref(0)
const uid = `governance-arrival-${Math.random().toString(36).slice(2, 9)}`
const viewportHeight = 252
const padding = {
  top: 48,
  right: 16,
  bottom: 36,
  left: 40,
}

const normalizedItems = computed(() => (
  (Array.isArray(props.insight?.items) ? props.insight.items : []).map((item, index) => ({
    key: item?.key || `${item?.label || 'bucket'}-${index}`,
    label: String(item?.label || ''),
    value: Math.max(0, Number(item?.value) || 0),
    valueLabel: String(item?.valueLabel || item?.value || '0'),
    percentage: Math.max(0, Number(item?.percentage) || 0),
    percentageLabel: String(item?.percentageLabel || '0%'),
  }))
))

const plotHeight = viewportHeight - padding.top - padding.bottom
const slotWidth = computed(() => {
  const itemCount = normalizedItems.value.length
  if (itemCount <= 4) return 40
  if (itemCount <= 6) return 34
  return 30
})

const canvasWidth = computed(() => {
  const itemCount = normalizedItems.value.length
  const slotCount = itemCount > 1 ? itemCount - 1 : 1
  const preferredWidth = padding.left + padding.right + (slotCount * slotWidth.value)
  return Math.max(containerWidth.value || 0, Math.max(236, preferredWidth))
})

const plotWidth = computed(() => canvasWidth.value - padding.left - padding.right)
const yAxisMax = computed(() => {
  const maxPercentage = Math.max(0, ...normalizedItems.value.map((item) => item.percentage))
  return Math.max(10, Math.ceil(maxPercentage / 5) * 5)
})

const chartPoints = computed(() => {
  const items = normalizedItems.value
  const itemCount = items.length

  return items.map((item, index) => {
    const x = itemCount > 1
      ? padding.left + ((index / (itemCount - 1)) * plotWidth.value)
      : padding.left + (plotWidth.value / 2)
    const ratio = yAxisMax.value > 0 ? item.percentage / yAxisMax.value : 0
    const y = padding.top + plotHeight - (Math.max(0, Math.min(1, ratio)) * plotHeight)

    return {
      ...item,
      x,
      y,
    }
  })
})

const peakPoint = computed(() => {
  const points = chartPoints.value
  if (!points.length) return null

  const highestValue = Math.max(...points.map((point) => point.value))
  const highestPercentage = Math.max(...points.map((point) => point.percentage))

  const matched = points.find((point) => (
    point.value === highestValue && point.percentage === highestPercentage
  ))

  return matched ? { ...matched, isPeak: true } : null
})

const chartPointsWithPeak = computed(() => (
  chartPoints.value.map((point) => ({
    ...point,
    isPeak: peakPoint.value ? point.key === peakPoint.value.key : false,
  }))
))

const highlightWidth = computed(() => {
  const itemCount = normalizedItems.value.length
  if (itemCount <= 1) return 56
  return Math.min(72, Math.max(46, plotWidth.value / Math.max(itemCount * 1.65, 1)))
})

const yAxisTicks = computed(() => (
  Array.from({ length: 4 }, (_, index) => {
    const stepCount = 4
    const value = (yAxisMax.value / stepCount) * (stepCount - index)
    const ratio = yAxisMax.value > 0 ? value / yAxisMax.value : 0
    return {
      key: `tick-${index}`,
      label: `${Math.round(value)}%`,
      y: padding.top + plotHeight - (ratio * plotHeight),
    }
  })
))

const xAxisLabels = computed(() => {
  const points = chartPointsWithPeak.value
  if (points.length <= 6) return points

  const step = Math.max(1, Math.ceil(points.length / 4))
  const labels = points.filter((_, index) => index % step === 0)
  const last = points[points.length - 1]

  if (!labels.find((item) => item.key === last.key)) {
    labels.push(last)
  }

  return labels
})

const linePath = computed(() => buildSmoothPath(chartPointsWithPeak.value))
const areaPath = computed(() => buildAreaPath(chartPointsWithPeak.value, padding.top + plotHeight))

const peakBadge = computed(() => {
  if (!peakPoint.value) return null

  const label = peakPoint.value.label
  const value = `${peakPoint.value.valueLabel} students • ${peakPoint.value.percentageLabel}`
  const width = Math.max(132, Math.min(196, (value.length * 6.3) + 26))
  const x = clamp(
    peakPoint.value.x,
    (width / 2) + 8,
    canvasWidth.value - (width / 2) - 8,
  )
  const y = Math.max(4, peakPoint.value.y - 58)

  return { label, value, width, x, y }
})

const ariaLabel = computed(() => {
  if (!peakPoint.value) return 'Peak arrival chart unavailable.'
  return `Peak arrivals happened around ${peakPoint.value.label} with ${peakPoint.value.valueLabel} students, or ${peakPoint.value.percentageLabel} of attendees.`
})

let resizeObserver = null

onMounted(() => {
  if (typeof window === 'undefined') return

  const updateWidth = () => {
    const measuredWidth = rootRef.value?.clientWidth || 0
    if (measuredWidth > 0) {
      containerWidth.value = measuredWidth
    }
  }

  updateWidth()

  if (typeof ResizeObserver === 'undefined' || !rootRef.value) return

  resizeObserver = new ResizeObserver(() => {
    updateWidth()
  })
  resizeObserver.observe(rootRef.value)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
})

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function buildSmoothPath(points = []) {
  if (!points.length) return ''
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`

  let path = `M ${points[0].x} ${points[0].y}`

  for (let index = 0; index < points.length - 1; index += 1) {
    const previous = points[index - 1] || points[index]
    const current = points[index]
    const next = points[index + 1]
    const afterNext = points[index + 2] || next

    const controlPointOneX = current.x + ((next.x - previous.x) / 6)
    const controlPointOneY = current.y + ((next.y - previous.y) / 6)
    const controlPointTwoX = next.x - ((afterNext.x - current.x) / 6)
    const controlPointTwoY = next.y - ((afterNext.y - current.y) / 6)

    path += ` C ${controlPointOneX} ${controlPointOneY}, ${controlPointTwoX} ${controlPointTwoY}, ${next.x} ${next.y}`
  }

  return path
}

function buildAreaPath(points = [], baseline = 0) {
  if (!points.length) return ''
  const line = buildSmoothPath(points)
  const first = points[0]
  const last = points[points.length - 1]
  return `${line} L ${last.x} ${baseline} L ${first.x} ${baseline} Z`
}
</script>

<style scoped>
.governance-arrival-curve {
  width: 100%;
  min-width: 0;
}

.governance-arrival-curve__scroller {
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.governance-arrival-curve__scroller::-webkit-scrollbar {
  display: none;
}

.governance-arrival-curve__canvas {
  min-width: 100%;
}

.governance-arrival-curve__chart {
  display: block;
  width: 100%;
  height: auto;
}

.governance-arrival-curve__grid-line {
  stroke: color-mix(in srgb, var(--color-text-muted) 14%, transparent);
  stroke-dasharray: 5 7;
  stroke-linecap: round;
}

.governance-arrival-curve__y-label,
.governance-arrival-curve__x-label {
  font-size: clamp(9px, 2.8vw, 11px);
  line-height: 1;
  font-weight: 700;
  fill: color-mix(in srgb, var(--color-text-muted) 92%, transparent);
}

.governance-arrival-curve__highlight {
  fill: color-mix(in srgb, var(--color-primary) 20%, white);
}

.governance-arrival-curve__area {
  opacity: 0.9;
}

.governance-arrival-curve__line {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.governance-arrival-curve__point {
  fill: color-mix(in srgb, var(--color-primary) 72%, white);
  opacity: 0.25;
}

.governance-arrival-curve__point.is-peak {
  opacity: 1;
  fill: color-mix(in srgb, var(--color-primary) 78%, white);
}

.governance-arrival-curve__peak-core {
  fill: var(--color-surface);
  stroke: color-mix(in srgb, var(--color-primary) 84%, white);
  stroke-width: 2.5;
}

.governance-arrival-curve__badge rect {
  fill: color-mix(in srgb, var(--color-primary) 76%, white);
}

.governance-arrival-curve__badge {
  filter: drop-shadow(0 10px 10px color-mix(in srgb, var(--color-nav) 12%, transparent));
}

.governance-arrival-curve__badge text {
  fill: var(--color-banner-text);
  font-weight: 700;
  letter-spacing: -0.02em;
}

.governance-arrival-curve__badge text:first-of-type {
  font-size: clamp(9px, 2.6vw, 10px);
  opacity: 0.88;
}

.governance-arrival-curve__badge text:last-of-type {
  font-size: clamp(9.5px, 2.8vw, 11px);
}

@media (max-width: 380px) {
  .governance-arrival-curve__y-label,
  .governance-arrival-curve__x-label {
    font-size: 9px;
  }
}
</style>
