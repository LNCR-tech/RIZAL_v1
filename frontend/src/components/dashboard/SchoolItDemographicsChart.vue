<template>
  <div class="demographics-chart">
    <div class="demographics-chart__header">
      <h3 class="demographics-chart__title">College Demographics</h3>
      <button class="demographics-chart__icon" aria-label="Expand">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="7" y1="17" x2="17" y2="7"></line>
          <polyline points="7 7 17 7 17 17"></polyline>
        </svg>
      </button>
    </div>

    <!-- The Chart Area -->
    <div class="demographics-chart__body">
      <div class="demographics-chart__ring-container">
        <!-- Pointers (Pseudo-elements or absolute positioned spans based on data order for top/left/right approx if wanted, but standard donut is fine) -->
        <div v-for="(segment, index) in renderedSegments" :key="`ptr-${segment.id}`"
             class="demographics-chart__pointer"
             :class="`demographics-chart__pointer--${index}`"
             v-show="segment.percentage > 0 && renderedSegments.length <= 4">
          {{ segment.percentage }}%
        </div>

        <svg class="demographics-chart__svg" viewBox="0 0 220 220" aria-hidden="true">
          <circle class="demographics-chart__track" cx="110" cy="110" :r="radius" />

          <g :transform="`rotate(${startAngle} 110 110)`">
            <circle
              v-for="segment in renderedSegments"
              :key="segment.id"
              class="demographics-chart__segment"
              cx="110"
              cy="110"
              :r="radius"
              :stroke-dasharray="segment.dasharray"
              :stroke-dashoffset="segment.dashoffset"
              :style="{ stroke: segment.color }"
            />
          </g>
        </svg>

        <div class="demographics-chart__center">
          <span class="demographics-chart__total">{{ formattedTotal }}</span>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="demographics-chart__legend">
      <div v-for="item in normalizedItems" :key="item.id" class="demographics-chart__legend-item">
        <span class="demographics-chart__legend-dot" :style="{ background: item.color }"></span>
        <span class="demographics-chart__legend-label">{{ item.shortLabel }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: {
    type: Number,
    default: 0,
  },
  items: {
    type: Array,
    default: () => [],
  },
})

const radius = 72
const gapDegrees = 6
const circumference = 2 * Math.PI * radius
const startAngle = -90

const formattedTotal = computed(() => new Intl.NumberFormat('en-US').format(props.total))

const normalizedItems = computed(() => {
  return Array.isArray(props.items)
    ? props.items.filter((item) => item && item.id != null).map((item) => {
        const pct = item.count > 0 && props.total > 0 ? (item.count / props.total) * 100 : 0
        return {
          ...item,
          percentage: Number(pct.toFixed(1)),
        }
      })
    : []
})

const renderedSegments = computed(() => {
  const rankedItems = normalizedItems.value
    .filter((item) => item.percentage > 0)
    .sort((a, b) => b.percentage - a.percentage) // Largest first

  if (!rankedItems.length) return []

  if (rankedItems.length === 1) {
    const onlyItem = rankedItems[0]
    const segmentLength = circumference * (onlyItem.percentage / 100)
    return [{
      ...onlyItem,
      dasharray: `${segmentLength} ${Math.max(circumference - segmentLength, 0)}`,
      dashoffset: 0,
    }]
  }

  const gapLength = circumference * (gapDegrees / 360)
  const totalGapLength = rankedItems.length * gapLength
  const availableLength = Math.max(circumference - totalGapLength, 0)

  let offset = 0
  return rankedItems.map((item) => {
    const segmentLength = Math.max(availableLength * (item.percentage / 100), 0)
    const safeLength = Number.isFinite(segmentLength) ? segmentLength : 0
    const segment = {
      ...item,
      dasharray: `${safeLength} ${Math.max(circumference - safeLength, 0)}`,
      dashoffset: -offset,
    }

    offset += safeLength + gapLength
    return segment
  })
})
</script>

<style scoped>
.demographics-chart {
  display: flex;
  flex-direction: column;
  background: var(--color-surface, #ffffff);
  border-radius: 24px;
  padding: 24px;
  width: 100%;
  box-sizing: border-box;
}

.demographics-chart__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.demographics-chart__title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-always-dark, #171717);
}

.demographics-chart__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--color-surface-border, #e5e5e5);
  background: transparent;
  color: var(--color-text-muted, #737373);
  cursor: pointer;
  transition: background 0.2s;
}

.demographics-chart__icon:hover {
  background: var(--color-bg, #f5f5f5);
}

.demographics-chart__body {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px 0;
}

.demographics-chart__ring-container {
  position: relative;
  width: clamp(180px, 45vw, 220px);
  aspect-ratio: 1;
  display: grid;
  place-items: center;
}

.demographics-chart__svg {
  width: 100%;
  height: 100%;
  overflow: visible;
  position: relative;
  z-index: 2;
}

.demographics-chart__track,
.demographics-chart__segment {
  fill: none;
  stroke-width: 24;
}

.demographics-chart__track {
  stroke: var(--color-surface-border, #f3f4f6);
}

.demographics-chart__segment {
  stroke-linecap: round;
  transition: stroke-dasharray 1s ease-out, stroke-dashoffset 1s ease-out;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.05));
}

.demographics-chart__center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.demographics-chart__total {
  font-size: clamp(26px, 7vw, 34px);
  line-height: 1;
  font-weight: 700;
  color: var(--color-text-always-dark, #171717);
}

/* Hardcoded pointers for exact visual match of the 4 segments in the image */
.demographics-chart__pointer {
  position: absolute;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-always-dark, #171717);
  z-index: 1;
}

/* Roughly placing percentages around the circle for top 4 items */
.demographics-chart__pointer--0 { top: 32%; left: -14%; } /* Largest segment, usually left */
.demographics-chart__pointer--1 { top: 22%; right: -12%; } /* Top right */
.demographics-chart__pointer--2 { bottom: 20%; left: -5%; } /* Bottom left */
.demographics-chart__pointer--3 { bottom: 18%; right: 5%; } /* Bottom right */

.demographics-chart__legend {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px 24px;
  margin-top: 32px;
  padding: 0 12px;
}

.demographics-chart__legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.demographics-chart__legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 4px; /* Slightly rounded square like the image */
  flex-shrink: 0;
}

.demographics-chart__legend-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-always-dark, #171717);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
