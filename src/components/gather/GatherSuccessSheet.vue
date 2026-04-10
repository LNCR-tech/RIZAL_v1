<template>
  <div class="gather-success-sheet">
    <div class="gather-success-sheet__accent" aria-hidden="true" />

    <div class="gather-success-sheet__orb" aria-hidden="true">
      <Check :size="34" :stroke-width="3" />
    </div>

    <div class="gather-success-sheet__copy">
      <h2 class="gather-success-sheet__title">{{ title }}</h2>
      <p class="gather-success-sheet__subtitle">{{ subtitle }}</p>
    </div>

    <div v-if="rows.length" class="gather-success-sheet__rows">
      <div
        v-for="row in rows"
        :key="row.label"
        class="gather-success-sheet__row"
      >
        <span class="gather-success-sheet__row-label">{{ row.label }}</span>
        <span class="gather-success-sheet__row-value">{{ row.value }}</span>
      </div>
    </div>

    <button
      type="button"
      class="gather-success-sheet__button"
      @click="$emit('dismiss')"
    >
      Done
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Check } from 'lucide-vue-next'

const props = defineProps({
  title: {
    type: String,
    default: 'Gather complete',
  },
  subtitle: {
    type: String,
    default: '',
  },
  rows: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['dismiss'])

const rows = computed(() => (
  Array.isArray(props.rows)
    ? props.rows.filter((row) => row?.label && row?.value)
    : []
))
</script>

<style scoped>
.gather-success-sheet {
  width: min(100%, 380px);
  border-radius: 34px;
  overflow: hidden;
  padding: 0 22px 22px;
  background:
    linear-gradient(180deg, rgba(10, 10, 10, 0.94) 0%, rgba(8, 8, 8, 0.84) 100%),
    var(--color-nav-glass-bg);
  border: 1px solid color-mix(in srgb, var(--color-nav-glass-border) 82%, transparent);
  box-shadow:
    0 24px 58px rgba(0, 0, 0, 0.44),
    0 0 40px color-mix(in srgb, var(--color-nav-active) 16%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  -webkit-backdrop-filter: blur(30px) saturate(155%);
  backdrop-filter: blur(30px) saturate(155%);
  color: rgba(255, 255, 255, 0.96);
}

.gather-success-sheet__accent {
  width: calc(100% + 44px);
  height: 3px;
  margin: 0 -22px;
  background: linear-gradient(90deg, transparent 0%, var(--color-nav-active) 50%, transparent 100%);
}

.gather-success-sheet__orb {
  width: 78px;
  height: 78px;
  margin: 22px auto 18px;
  border-radius: 999px;
  background:
    radial-gradient(circle at 35% 35%, color-mix(in srgb, var(--color-nav-active) 34%, white) 0%, color-mix(in srgb, var(--color-nav-active) 14%, transparent) 62%);
  border: 1px solid color-mix(in srgb, var(--color-nav-active) 28%, transparent);
  color: var(--color-nav-active);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 30px color-mix(in srgb, var(--color-nav-active) 18%, transparent);
}

.gather-success-sheet__copy {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}

.gather-success-sheet__title {
  margin: 0;
  font-size: clamp(26px, 7vw, 30px);
  line-height: 0.96;
  letter-spacing: -0.06em;
  font-weight: 800;
}

.gather-success-sheet__subtitle {
  margin: 0;
  max-width: 28ch;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.66);
}

.gather-success-sheet__rows {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.gather-success-sheet__row {
  min-height: 54px;
  padding: 0 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.gather-success-sheet__row-label {
  font-size: 11px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.42);
}

.gather-success-sheet__row-value {
  min-width: 0;
  font-size: 14px;
  line-height: 1.2;
  font-weight: 700;
  text-align: right;
}

.gather-success-sheet__button {
  width: 100%;
  min-height: 54px;
  margin-top: 20px;
  border: none;
  border-radius: 999px;
  background: var(--color-nav-active);
  color: var(--color-text-always-dark);
  font: inherit;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: -0.02em;
  box-shadow: 0 0 28px color-mix(in srgb, var(--color-nav-active) 24%, transparent);
  cursor: pointer;
}
</style>
