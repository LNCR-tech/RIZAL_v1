<template>
  <div class="ssg-sg">
    <h3 class="ssg-sg__title">SSG vs SG Breakdown</h3>

    <div class="ssg-sg__bars">
      <!-- SSG -->
      <div class="ssg-sg__bar-card">
        <div class="ssg-sg__bar-header">
          <span class="ssg-sg__tag ssg-sg__tag--ssg">SSG</span>
          <span class="ssg-sg__rate">{{ ssgRate }}%</span>
        </div>
        <div class="ssg-sg__track">
          <div
            class="ssg-sg__fill ssg-sg__fill--ssg"
            :style="{ width: `${ssgRate}%` }"
          />
        </div>
        <span class="ssg-sg__detail">{{ ssgAttended }}/{{ ssgTotal }} events attended</span>
      </div>

      <!-- SG -->
      <div class="ssg-sg__bar-card">
        <div class="ssg-sg__bar-header">
          <span class="ssg-sg__tag ssg-sg__tag--sg">SG</span>
          <span class="ssg-sg__rate">{{ sgRate }}%</span>
        </div>
        <div class="ssg-sg__track">
          <div
            class="ssg-sg__fill ssg-sg__fill--sg"
            :style="{ width: `${sgRate}%` }"
          />
        </div>
        <span class="ssg-sg__detail">{{ sgAttended }}/{{ sgTotal }} events attended</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  ssgAttended: { type: Number, default: 0 },
  ssgTotal: { type: Number, default: 0 },
  sgAttended: { type: Number, default: 0 },
  sgTotal: { type: Number, default: 0 },
})

const ssgRate = computed(() => (props.ssgTotal > 0 ? Math.round((props.ssgAttended / props.ssgTotal) * 100) : 0))
const sgRate = computed(() => (props.sgTotal > 0 ? Math.round((props.sgAttended / props.sgTotal) * 100) : 0))
</script>

<style scoped>
.ssg-sg {
  padding: clamp(20px, 5vw, 28px);
  border-radius: 24px;
  background: var(--color-surface);
  border: 1px solid rgba(10, 10, 10, 0.05);
}

.ssg-sg__title {
  margin: 0 0 clamp(16px, 4vw, 22px);
  font-size: clamp(15px, 4vw, 18px);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-surface-text);
}

.ssg-sg__bars {
  display: flex;
  gap: clamp(14px, 4vw, 20px);
}

.ssg-sg__bar-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ssg-sg__bar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ssg-sg__tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.ssg-sg__tag--ssg {
  background: rgba(99, 102, 241, 0.12);
  color: #4F46E5;
}

.ssg-sg__tag--sg {
  background: rgba(139, 92, 246, 0.12);
  color: #7C3AED;
}

.ssg-sg__rate {
  font-size: clamp(20px, 5.5vw, 26px);
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--color-surface-text);
}

.ssg-sg__track {
  height: 10px;
  border-radius: 999px;
  background: rgba(10, 10, 10, 0.05);
  overflow: hidden;
}

.ssg-sg__fill {
  height: 100%;
  border-radius: 999px;
  transition: width 1s cubic-bezier(0.22, 1, 0.36, 1);
  min-width: 10px;
}

.ssg-sg__fill--ssg {
  background: var(--color-ssg-accent);
}

.ssg-sg__fill--sg {
  background: var(--color-sg-accent);
}

.ssg-sg__detail {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-surface-text-muted);
}

@media (max-width: 520px) {
  .ssg-sg__bars {
    flex-direction: column;
  }
}
</style>
