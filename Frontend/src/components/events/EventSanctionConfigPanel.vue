<template>
  <section class="sanction-config-panel">
    <header class="sanction-config-panel__header">
      <h3 class="sanction-config-panel__title">Event Sanctions</h3>
      <p class="sanction-config-panel__copy">
        Enable sanctions for absentees and define the required compliance items.
      </p>
    </header>

    <label v-if="showEnabledToggle" class="sanction-config-panel__toggle">
      <input
        :checked="normalizedValue.sanctions_enabled"
        :disabled="disabled"
        type="checkbox"
        @change="handleEnabledChange"
      >
      <span>Enable sanctions for this event</span>
    </label>

    <div v-if="isConfigEnabled" class="sanction-config-panel__body">
      <article
        v-for="(item, index) in normalizedValue.items"
        :key="`sanction-item-${index}`"
        class="sanction-config-panel__item"
      >
        <div class="sanction-config-panel__item-grid">
          <label class="sanction-config-panel__field">
            <span>Item Name</span>
            <input
              :value="item.item_name"
              :disabled="disabled"
              type="text"
              placeholder="e.g. Community Service"
              @input="updateItem(index, 'item_name', $event.target.value)"
            >
          </label>

          <label class="sanction-config-panel__field">
            <span>Item Code (Optional)</span>
            <input
              :value="item.item_code"
              :disabled="disabled"
              type="text"
              placeholder="e.g. community_service"
              @input="updateItem(index, 'item_code', $event.target.value)"
            >
          </label>
        </div>

        <label class="sanction-config-panel__field">
          <span>Description (Optional)</span>
          <textarea
            :value="item.item_description"
            :disabled="disabled"
            rows="2"
            placeholder="Add guidance for this sanction item."
            @input="updateItem(index, 'item_description', $event.target.value)"
          />
        </label>

        <button
          class="sanction-config-panel__remove"
          type="button"
          :disabled="disabled"
          @click="removeItem(index)"
        >
          Remove Item
        </button>
      </article>

      <button
        class="sanction-config-panel__add"
        type="button"
        :disabled="disabled"
        @click="addItem"
      >
        Add Sanction Item
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      sanctions_enabled: false,
      items: [],
    }),
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  showEnabledToggle: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:modelValue'])

function createEmptyItem() {
  return {
    item_code: '',
    item_name: '',
    item_description: '',
  }
}

function normalizeItem(item = null) {
  if (!item || typeof item !== 'object') {
    return createEmptyItem()
  }

  return {
    item_code: String(item.item_code || '').trim(),
    item_name: String(item.item_name || '').trim(),
    item_description: String(item.item_description || '').trim(),
  }
}

function normalizeValue(value = null) {
  const sanitizedItems = Array.isArray(value?.items)
    ? value.items.map(normalizeItem)
    : []

  return {
    sanctions_enabled: Boolean(value?.sanctions_enabled),
    items: sanitizedItems,
  }
}

const normalizedValue = computed(() => normalizeValue(props.modelValue))
const isConfigEnabled = computed(() => (
  props.showEnabledToggle ? normalizedValue.value.sanctions_enabled : true
))

function updateValue(nextValue = {}) {
  emit('update:modelValue', normalizeValue(nextValue))
}

function handleEnabledChange(event) {
  const nextEnabled = Boolean(event?.target?.checked)
  const current = normalizeValue(props.modelValue)
  updateValue({
    ...current,
    sanctions_enabled: nextEnabled,
    items: nextEnabled
      ? (current.items.length ? current.items : [createEmptyItem()])
      : [],
  })
}

function addItem() {
  const current = normalizeValue(props.modelValue)
  updateValue({
    ...current,
    items: [...current.items, createEmptyItem()],
  })
}

function removeItem(index) {
  const current = normalizeValue(props.modelValue)
  const nextItems = current.items.filter((_, itemIndex) => itemIndex !== index)
  updateValue({
    ...current,
    items: nextItems,
  })
}

function updateItem(index, key, value) {
  const current = normalizeValue(props.modelValue)
  const nextItems = current.items.map((item, itemIndex) => {
    if (itemIndex !== index) return item
    return {
      ...item,
      [key]: String(value || ''),
    }
  })
  updateValue({
    ...current,
    items: nextItems,
  })
}
</script>

<style scoped>
.sanction-config-panel {
  display: grid;
  gap: 12px;
  padding: 14px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-surface) 92%, transparent);
}

.sanction-config-panel__header {
  display: grid;
  gap: 4px;
}

.sanction-config-panel__title {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: var(--color-text-primary);
}

.sanction-config-panel__copy {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-muted);
}

.sanction-config-panel__toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.sanction-config-panel__body {
  display: grid;
  gap: 12px;
}

.sanction-config-panel__item {
  display: grid;
  gap: 10px;
  padding: 12px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--color-bg) 62%, var(--color-surface));
}

.sanction-config-panel__item-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.sanction-config-panel__field {
  display: grid;
  gap: 6px;
}

.sanction-config-panel__field span {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.sanction-config-panel__field input,
.sanction-config-panel__field textarea {
  width: 100%;
  border: 1px solid color-mix(in srgb, var(--color-text-muted) 20%, transparent);
  border-radius: 12px;
  background: #fff;
  padding: 10px 12px;
  font-family: inherit;
  font-size: 13px;
  color: var(--color-text-primary);
  outline: none;
  box-sizing: border-box;
}

.sanction-config-panel__field textarea {
  resize: vertical;
}

.sanction-config-panel__remove,
.sanction-config-panel__add {
  border: none;
  border-radius: 999px;
  min-height: 36px;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
}

.sanction-config-panel__remove {
  justify-self: flex-start;
  background: rgba(220, 38, 38, 0.08);
  color: #b91c1c;
}

.sanction-config-panel__add {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.sanction-config-panel__remove:disabled,
.sanction-config-panel__add:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 760px) {
  .sanction-config-panel__item-grid {
    grid-template-columns: 1fr;
  }
}
</style>
