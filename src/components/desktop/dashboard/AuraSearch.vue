<template>
  <div 
    class="aura-search" 
    :class="{ 'aura-search--active': hasQuery || isFocused }"
    :style="{ '--aura-search-max-width': width }"
  >
    <div class="aura-search__shell" :class="{ 'aura-search__shell--open': hasResults }">
      <div class="aura-search__input-row">
        <input
          :value="modelValue"
          type="text"
          :placeholder="placeholder"
          class="aura-search__input"
          @input="$emit('update:modelValue', $event.target.value)"
          @focus="handleFocus"
          @blur="handleBlur"
        >
        <button class="aura-search__icon" type="button" aria-label="Search">
          <Search :size="18" />
        </button>
      </div>

      <div class="aura-search__results">
        <div class="aura-search__results-inner">
          <template v-if="hasResults">
            <slot name="results" :results="results">
              <button
                v-for="result in results"
                :key="result.key || result.id"
                class="aura-search__result"
                type="button"
                @click="handleSelect(result)"
              >
                <div class="aura-search__result-top">
                  <span class="aura-search__result-name">{{ result.name }}</span>
                  <span v-if="result.type" class="aura-search__result-type">{{ result.type }}</span>
                </div>
                <span v-if="result.meta" class="aura-search__result-meta">{{ result.meta }}</span>
              </button>
            </slot>
            <p v-if="!results.length && hasQuery" class="aura-search__empty">
              <slot name="empty">No matching results found.</slot>
            </p>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Search } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Search...'
  },
  results: {
    type: Array,
    default: () => []
  },
  width: {
    type: String,
    default: '100%'
  }
})

const emit = defineEmits(['update:modelValue', 'select', 'focus', 'blur'])

const isFocused = ref(false)
const hasQuery = computed(() => props.modelValue.trim().length > 0)
const hasResults = computed(() => hasQuery.value)

function handleFocus(event) {
  isFocused.value = true
  emit('focus', event)
}

function handleBlur(event) {
  isFocused.value = false
  emit('blur', event)
}

function handleSelect(result) {
  emit('select', result)
}
</script>

<style scoped>
.aura-search {
  width: var(--aura-search-max-width, 100%);
}

.aura-search__shell {
  display: grid;
  grid-template-rows: auto 0fr;
  padding: 12px 18px;
  border-radius: 28px;
  background: var(--aura-glass-bg);
  border: 1px solid var(--aura-glass-border);
  backdrop-filter: blur(var(--nav-glass-blur));
  -webkit-backdrop-filter: blur(var(--nav-glass-blur));
  transition: grid-template-rows 0.32s cubic-bezier(0.22, 1, 0.36, 1), border-radius 0.32s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.3s ease;
  box-shadow: var(--aura-shadow-soft);
}

.aura-search__shell--open {
  grid-template-rows: auto 1fr;
  border-radius: 24px;
  background: var(--color-surface);
}

.aura-search__input-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  min-height: 40px;
}

.aura-search__input {
  flex: 1;
  min-width: 0;
  border: none;
  background: transparent;
  outline: none;
  color: var(--color-text-always-dark);
  font-size: 15px;
  font-weight: 500;
}

.aura-search__input::placeholder {
  color: var(--color-text-muted);
}

.aura-search__icon {
  width: 34px;
  height: 34px;
  padding: 0;
  border: 1px solid var(--color-surface-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.aura-search__results {
  overflow: hidden;
  min-height: 0;
}

.aura-search__results-inner {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 0 8px;
}

.aura-search__result {
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 20px;
  background: color-mix(in srgb, var(--color-surface) 94%, var(--color-bg));
  display: flex; flex-direction: column;
  gap: 6px;
  text-align: left;
  transition: transform 0.2s ease, background 0.2s ease;
}

.aura-search__result:hover {
  background: color-mix(in srgb, var(--color-surface) 88%, var(--color-bg));
  transform: translateX(4px);
}

.aura-search__result-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.aura-search__result-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-always-dark);
}

.aura-search__result-type {
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 15%, white);
  color: var(--color-text-always-dark);
  display: inline-flex;
  align-items: center;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
}

.aura-search__result-meta {
  font-size: 12px;
  color: var(--color-text-muted);
}

.aura-search__empty {
  font-size: 13px;
  color: var(--color-text-muted);
  padding: 10px 4px;
}
</style>
