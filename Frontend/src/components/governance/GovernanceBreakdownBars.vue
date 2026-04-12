<template>
  <div class="governance-breakdown">
    <div class="governance-breakdown__header">
      <h2 class="governance-breakdown__title">{{ title }}</h2>

      <div class="governance-breakdown__view-switch" role="tablist" :aria-label="`${title} view`">
        <button
          type="button"
          class="governance-breakdown__view-button"
          :class="{ 'is-active': viewMode === 'chart' }"
          role="tab"
          :aria-selected="viewMode === 'chart' ? 'true' : 'false'"
          @click="viewMode = 'chart'"
        >
          Chart
        </button>
        <button
          type="button"
          class="governance-breakdown__view-button"
          :class="{ 'is-active': viewMode === 'table' }"
          role="tab"
          :aria-selected="viewMode === 'table' ? 'true' : 'false'"
          @click="viewMode = 'table'"
        >
          Table
        </button>
      </div>
    </div>

    <div
      v-if="viewMode === 'chart'"
      class="governance-breakdown__chart-shell"
      :class="{ 'is-scrollable': shouldScroll }"
    >
      <div
        class="governance-breakdown__chart"
        :class="{ 'is-scrollable': shouldScroll }"
        role="img"
        :aria-label="chartAriaLabel"
      >
        <article
          v-for="item in normalizedItems"
          :key="item.key"
          class="governance-breakdown__column"
          :class="{ 'is-highlighted': item.isHighlighted }"
        >
          <span
            class="governance-breakdown__value-pill"
            :class="{ 'is-highlighted': item.isHighlighted }"
          >
            {{ item.valueLabel }}
          </span>

          <div class="governance-breakdown__track">
            <span
              class="governance-breakdown__fill"
              :style="{ height: `${Math.max(item.ratio, 8)}%` }"
            />
          </div>

          <div class="governance-breakdown__column-copy">
            <strong>{{ item.label }}</strong>
          </div>
        </article>
      </div>
    </div>

    <div v-else class="governance-breakdown__table" role="table" :aria-label="`${title} table`">
      <article
        v-for="item in normalizedItems"
        :key="item.key"
        class="governance-breakdown__table-row"
        role="row"
      >
        <div class="governance-breakdown__table-label" role="cell">
          <span class="governance-breakdown__table-dot" :class="{ 'is-highlighted': item.isHighlighted }" />
          <div>
            <strong>{{ item.label }}</strong>
            <small>{{ item.meta }}</small>
          </div>
        </div>

        <div class="governance-breakdown__table-metrics" role="cell">
          <span>{{ item.shareLabel }}</span>
          <strong>{{ item.valueLabel }}</strong>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: 'College Reach',
  },
  items: {
    type: Array,
    default: () => [],
  },
})

const viewMode = ref('chart')

const normalizedItems = computed(() => {
  const sourceItems = Array.isArray(props.items) ? props.items : []
  const total = sourceItems.reduce((sum, item) => sum + (Number(item?.value) || 0), 0)

  return sourceItems.map((item, index) => {
    const numericValue = Math.max(0, Number(item?.value) || 0)
    const share = total > 0 ? Math.round((numericValue / total) * 100) : 0

    return {
      key: item?.key || `${item?.label || 'row'}-${index}`,
      label: String(item?.label || 'Untitled'),
      meta: String(item?.meta || '').trim() || 'No additional detail',
      ratio: Math.max(0, Math.min(100, Number(item?.ratio) || 0)),
      valueLabel: String(item?.valueLabel || item?.value || '0'),
      shareLabel: `${share}%`,
      isHighlighted: index === 0,
    }
  })
})

const shouldScroll = computed(() => normalizedItems.value.length > 5)

const chartAriaLabel = computed(() => (
  normalizedItems.value
    .map((item) => `${item.label}: ${item.valueLabel}, ${item.shareLabel} of visible participation`)
    .join('. ')
))
</script>

<style scoped>
.governance-breakdown {
  display: grid;
  gap: 18px;
}

.governance-breakdown__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.governance-breakdown__title {
  margin: 0;
  font-size: 18px;
  line-height: 1;
  letter-spacing: -0.04em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-breakdown__view-switch {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.governance-breakdown__view-button {
  min-width: 0;
  height: 32px;
  padding: 0 14px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.governance-breakdown__view-button.is-active {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.governance-breakdown__chart {
  min-height: 236px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(56px, 1fr));
  gap: 12px;
  align-items: stretch;
}

.governance-breakdown__chart-shell {
  width: 100%;
}

.governance-breakdown__chart-shell.is-scrollable {
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.governance-breakdown__chart-shell.is-scrollable::-webkit-scrollbar {
  display: none;
}

.governance-breakdown__chart.is-scrollable {
  width: max-content;
  min-width: 100%;
  grid-auto-flow: column;
  grid-auto-columns: minmax(60px, 60px);
}

.governance-breakdown__column {
  min-width: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 174px) minmax(42px, auto);
  gap: 8px;
  justify-items: center;
}

.governance-breakdown__value-pill {
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-bg) 54%, var(--color-surface));
  color: var(--color-text-primary);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.governance-breakdown__value-pill.is-highlighted {
  background: color-mix(in srgb, var(--color-primary) 76%, white);
  color: var(--color-nav);
}

.governance-breakdown__track {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 8px 8px 10px;
  overflow: hidden;
  border-radius: 999px;
  background:
    repeating-linear-gradient(
      135deg,
      color-mix(in srgb, var(--color-text-muted) 6%, transparent) 0 4px,
      transparent 4px 10px
    ),
    color-mix(in srgb, white 82%, var(--color-surface) 18%);
}

.governance-breakdown__fill {
  position: relative;
  z-index: 1;
  width: 100%;
  min-height: 10px;
  border-radius: 999px;
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, white 28%, var(--color-primary) 72%) 0%,
      color-mix(in srgb, white 74%, var(--color-primary) 26%) 100%
    );
}

.governance-breakdown__column-copy {
  width: 100%;
  display: grid;
  justify-items: center;
  align-content: start;
  text-align: center;
}

.governance-breakdown__column-copy strong {
  font-size: 11px;
  line-height: 1.15;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--color-text-primary);
}

.governance-breakdown__table {
  display: grid;
  gap: 10px;
}

.governance-breakdown__table-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-bg) 54%, var(--color-surface));
}

.governance-breakdown__table-label {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.governance-breakdown__table-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  flex-shrink: 0;
  background: color-mix(in srgb, var(--color-primary) 18%, transparent);
}

.governance-breakdown__table-dot.is-highlighted {
  background: var(--color-primary);
  box-shadow: 0 0 0 5px color-mix(in srgb, var(--color-primary) 16%, transparent);
}

.governance-breakdown__table-label strong,
.governance-breakdown__table-metrics strong {
  display: block;
  font-size: 14px;
  line-height: 1.2;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-breakdown__table-label small,
.governance-breakdown__table-metrics span {
  display: block;
  margin-top: 3px;
  font-size: 12px;
  line-height: 1.3;
  color: var(--color-text-muted);
}

.governance-breakdown__table-metrics {
  text-align: right;
  flex-shrink: 0;
}

@media (max-width: 767px) {
  .governance-breakdown {
    gap: 16px;
  }

  .governance-breakdown__header {
    flex-wrap: wrap;
  }

  .governance-breakdown__view-switch {
    margin-left: auto;
  }

  .governance-breakdown__chart {
    grid-template-columns: repeat(auto-fit, minmax(52px, 1fr));
    gap: 10px;
  }

  .governance-breakdown__chart.is-scrollable {
    grid-auto-columns: minmax(56px, 56px);
  }

  .governance-breakdown__column {
    grid-template-rows: auto minmax(0, 158px) minmax(48px, auto);
  }

  .governance-breakdown__track {
    min-height: 0;
  }

  .governance-breakdown__table-row {
    padding: 13px 14px;
  }

  .governance-breakdown__table-label strong,
  .governance-breakdown__table-metrics strong {
    font-size: 13px;
  }
}
</style>
