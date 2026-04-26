<template>
  <button
    class="security-pill"
    :class="{
      'security-pill--full': fullWidth,
      'security-pill--disabled': disabled,
    }"
    :type="type"
    :disabled="disabled"
  >
    <span class="security-pill__icon">
      <LoaderCircle v-if="loading" class="security-pill__spinner" :size="18" />
      <component :is="icon" v-else :size="18" />
    </span>
    <span class="security-pill__label">{{ label }}</span>
  </button>
</template>

<script setup>
import { LoaderCircle } from 'lucide-vue-next'

defineProps({
  icon: {
    type: [Object, Function],
    required: true,
  },
  label: {
    type: String,
    required: true,
  },
  type: {
    type: String,
    default: 'button',
  },
  fullWidth: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.security-pill {
  display: inline-flex;
  align-items: center;
  gap: 16px;
  min-height: 64px;
  padding: 4px 24px 4px 4px;
  border: none;
  border-radius: 999px;
  background: var(--color-primary, #aaff00);
  color: var(--color-primary-text, #0a0a0a);
  font-family: 'Manrope', sans-serif;
  cursor: pointer;
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.security-pill--full {
  width: 100%;
  justify-content: flex-start;
}

.security-pill:active:not(:disabled) {
  transform: scale(0.98);
}

.security-pill--disabled,
.security-pill:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.security-pill__icon {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  border-radius: 999px;
  background: var(--color-nav, #0a0a0a);
  color: var(--color-nav-text, #ffffff);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.security-pill__label {
  font-size: 15px;
  font-weight: 500;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.security-pill__spinner {
  animation: security-spin 0.9s linear infinite;
}

@keyframes security-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
