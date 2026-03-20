<template>
  <div class="relative">
    <input
      :id="id"
      :type="inputType"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :autocomplete="autocomplete"
      :style="inputStyleVars"
      class="base-input w-full bg-[var(--color-surface)] border border-[var(--field-border-color)] rounded-full px-5 py-4 text-[15px] font-medium text-[var(--color-surface-text)] placeholder-[var(--color-surface-text-muted)] outline-none transition-all duration-150 focus:border-[var(--field-focus-color)] focus:ring-2 focus:ring-[var(--field-focus-color)] focus:ring-offset-0 disabled:opacity-50 disabled:cursor-not-allowed pr-12"
      @input="$emit('update:modelValue', $event.target.value)"
      @keyup.enter="$emit('enter')"
    />
    <!-- Password toggle -->
    <button
      v-if="type === 'password'"
      type="button"
      tabindex="-1"
      class="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--color-surface-text-muted)] hover:text-[var(--color-surface-text)] transition-colors p-1"
      @click="togglePasswordVisibility"
      aria-label="Toggle password visibility"
    >
      <!-- Eye open -->
      <svg v-if="!showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M1 12C1 12 5 4 12 4C19 4 23 12 23 12C23 12 19 20 12 20C5 20 1 12 1 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <!-- Eye closed -->
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20C5 20 1 12 1 12A18.45 18.45 0 0 1 5.06 5.06M9.9 4.24A9.12 9.12 0 0 1 12 4C19 4 23 12 23 12A18.5 18.5 0 0 1 20.71 16.59M1 1L23 23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  id: {
    type: String,
    default: '',
  },
  modelValue: {
    type: String,
    default: '',
  },
  type: {
    type: String,
    default: 'text',
  },
  placeholder: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  autocomplete: {
    type: String,
    default: 'off',
  },
  tone: {
    type: String,
    default: 'accent',
  },
})

defineEmits(['update:modelValue', 'enter'])

const showPassword = ref(false)

const inputType = computed(() => {
  if (props.type === 'password') {
    return showPassword.value ? 'text' : 'password'
  }
  return props.type
})

const inputStyleVars = computed(() => {
  const isNeutralTone = props.tone === 'neutral'

  return {
    '--field-border-color': isNeutralTone
      ? 'var(--color-text-primary)'
      : 'var(--color-surface-border-strong)',
    '--field-focus-color': isNeutralTone
      ? 'var(--color-text-primary)'
      : 'var(--color-primary)',
  }
})

function togglePasswordVisibility() {
  showPassword.value = !showPassword.value
}
</script>

<style scoped>
.base-input:-webkit-autofill,
.base-input:-webkit-autofill:hover,
.base-input:-webkit-autofill:focus {
  -webkit-text-fill-color: var(--color-surface-text);
  caret-color: var(--color-surface-text);
  border-color: var(--field-focus-color);
  -webkit-box-shadow:
    0 0 0 1000px var(--color-surface) inset,
    0 0 0 2px var(--field-focus-color);
  box-shadow:
    0 0 0 1000px var(--color-surface) inset,
    0 0 0 2px var(--field-focus-color);
  transition: background-color 9999s ease-out 0s;
}
</style>
