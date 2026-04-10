<template>
  <header class="security-header">
    <button class="security-icon-btn" type="button" :aria-label="backLabel" @click="$emit('back')">
      <ArrowLeft :size="18" />
    </button>

    <div class="security-header__title">
      <component :is="icon" :size="20" />
      <span>{{ title }}</span>
    </div>

    <div class="security-icon-btn security-icon-btn--ghost" aria-hidden="true">
      <Settings :size="18" />
    </div>
  </header>
</template>

<script setup>
import { ArrowLeft, Settings } from 'lucide-vue-next'

defineEmits(['back'])

defineProps({
  title: {
    type: String,
    required: true,
  },
  icon: {
    type: [Object, Function],
    required: true,
  },
  backLabel: {
    type: String,
    default: 'Go back',
  },
})
</script>

<style scoped>
.security-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.security-header__title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text-primary, #0a0a0a);
  font-family: 'Manrope', sans-serif;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.security-icon-btn {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border-radius: 999px;
  border: none;
  background: var(--color-surface, #ffffff);
  color: var(--color-surface-text, #0a0a0a);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.security-icon-btn--ghost {
  pointer-events: none;
}
</style>
