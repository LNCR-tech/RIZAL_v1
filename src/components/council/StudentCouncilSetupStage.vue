<template>
  <div class="student-council-setup-stage">
    <div class="student-council-setup-stage__hero">
      <span v-if="eyebrow" class="student-council-setup-stage__eyebrow">{{ eyebrow }}</span>
      <h2 class="student-council-setup-stage__title">{{ titleLines[0] }}<br>{{ titleLines[1] }}</h2>
      <p v-if="description" class="student-council-setup-stage__description">{{ description }}</p>
    </div>

    <label class="student-council-setup-stage__field">
      <span class="student-council-setup-stage__field-label">Organization Acronym</span>
      <input
        :value="draft.acronym"
        type="text"
        class="student-council-setup-stage__field-input"
        placeholder="e.g., SSG, USC, CSC"
        @input="updateDraft('acronym', $event.target.value)"
      >
    </label>

    <label class="student-council-setup-stage__field">
      <span class="student-council-setup-stage__field-label">Official Governing Body Name</span>
      <input
        :value="draft.name"
        type="text"
        class="student-council-setup-stage__field-input"
        placeholder="e.g., Supreme Student Government"
        @input="updateDraft('name', $event.target.value)"
      >
    </label>

    <label class="student-council-setup-stage__field">
      <span class="student-council-setup-stage__field-label">Description</span>
      <textarea
        :value="draft.description"
        class="student-council-setup-stage__field-input student-council-setup-stage__field-input--textarea"
        placeholder="Briefly describe the role of this governing body on campus..."
        @input="updateDraft('description', $event.target.value)"
      />
    </label>

    <label v-if="showScopeField" class="student-council-setup-stage__field">
      <span class="student-council-setup-stage__field-label">{{ scopeLabel }}</span>
      <div class="student-council-setup-stage__select-shell" :class="{ 'student-council-setup-stage__select-shell--disabled': scopeDisabled }">
        <select
          :value="draft.scopeId || ''"
          class="student-council-setup-stage__field-input student-council-setup-stage__field-select"
          :disabled="scopeDisabled"
          @change="updateDraft('scopeId', $event.target.value)"
        >
          <option value="" disabled>{{ scopePlaceholder }}</option>
          <option
            v-for="option in normalizedScopeOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
        <ChevronDown :size="18" class="student-council-setup-stage__select-chevron" />
      </div>
      <span v-if="scopeHelper" class="student-council-setup-stage__field-helper">{{ scopeHelper }}</span>
    </label>

    <div class="student-council-setup-stage__actions">
      <button
        class="student-council-setup-stage__primary-pill"
        type="button"
        :disabled="submitDisabled"
        @click="$emit('submit')"
      >
        <span class="student-council-setup-stage__primary-pill-icon">
          <component :is="isEditing ? SquarePen : SquarePlus" :size="18" />
        </span>
        {{ submitLabel }}
      </button>

      <button
        v-if="showDelete"
        class="student-council-setup-stage__danger-pill"
        type="button"
        :disabled="deleteDisabled"
        @click="$emit('delete')"
      >
        <span class="student-council-setup-stage__danger-pill-icon">
          <Trash2 :size="18" />
        </span>
        {{ deleteLabel }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChevronDown, SquarePen, SquarePlus, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  draft: {
    type: Object,
    default: () => ({
      acronym: '',
      name: '',
      description: '',
      scopeId: '',
    }),
  },
  eyebrow: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    default: 'Student Council',
  },
  description: {
    type: String,
    default: '',
  },
  scopeLabel: {
    type: String,
    default: '',
  },
  scopeOptions: {
    type: Array,
    default: () => [],
  },
  scopePlaceholder: {
    type: String,
    default: 'Select an option',
  },
  scopeHelper: {
    type: String,
    default: '',
  },
  scopeDisabled: {
    type: Boolean,
    default: false,
  },
  isEditing: {
    type: Boolean,
    default: false,
  },
  submitLabel: {
    type: String,
    default: 'Add Student Council',
  },
  submitDisabled: {
    type: Boolean,
    default: false,
  },
  showDelete: {
    type: Boolean,
    default: false,
  },
  deleteLabel: {
    type: String,
    default: 'Delete Student Council',
  },
  deleteDisabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['submit', 'delete', 'update:draft'])

const titleLines = computed(() => {
  const text = String(props.title || 'Student Council').trim()
  if (!text) return ['Student', 'Council']

  const words = text.split(/\s+/).filter(Boolean)
  if (words.length <= 1) return [text, '']

  const midpoint = Math.ceil(words.length / 2)
  return [
    words.slice(0, midpoint).join(' '),
    words.slice(midpoint).join(' '),
  ]
})

const normalizedScopeOptions = computed(() => (
  Array.isArray(props.scopeOptions)
    ? props.scopeOptions
      .map((option) => ({
        value: String(option?.value ?? '').trim(),
        label: String(option?.label ?? '').trim(),
      }))
      .filter((option) => option.value && option.label)
    : []
))

const showScopeField = computed(() => Boolean(props.scopeLabel) || normalizedScopeOptions.value.length > 0)

function updateDraft(field, value) {
  emit('update:draft', {
    ...props.draft,
    [field]: value,
  })
}
</script>

<style scoped>
.student-council-setup-stage{display:flex;flex-direction:column;gap:18px;min-height:472px}
.student-council-setup-stage__hero{display:flex;flex-direction:column;gap:8px}
.student-council-setup-stage__eyebrow{display:inline-flex;align-self:flex-start;padding:7px 12px;border-radius:999px;background:color-mix(in srgb,var(--color-primary) 10%, var(--color-surface));color:var(--color-primary);font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.student-council-setup-stage__title{margin:0;font-size:clamp(36px,10vw,64px);line-height:.92;letter-spacing:-.08em;font-weight:700;color:var(--color-text-always-dark)}
.student-council-setup-stage__description{margin:0;max-width:34ch;font-size:13px;line-height:1.55;color:var(--color-text-muted)}
.student-council-setup-stage__field{display:flex;flex-direction:column;gap:10px}
.student-council-setup-stage__field-label{font-size:14px;font-weight:500;color:var(--color-text-always-dark)}
.student-council-setup-stage__field-input{width:100%;min-height:54px;padding:0 18px;border:none;border-radius:999px;background:var(--color-field-surface);outline:none;font-size:14px;font-weight:500;color:var(--color-text-always-dark);resize:none;box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 16%, transparent);transition:background-color .18s ease,box-shadow .18s ease}
.student-council-setup-stage__field-input:focus{background:var(--color-field-surface);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 28%, transparent)}
.student-council-setup-stage__field-input--textarea{min-height:82px;padding:16px 18px;border-radius:26px}
.student-council-setup-stage__field-input::placeholder{color:var(--color-text-muted)}
.student-council-setup-stage__select-shell{position:relative}
.student-council-setup-stage__field-select{padding-right:46px;appearance:none;cursor:pointer}
.student-council-setup-stage__select-shell--disabled .student-council-setup-stage__field-select{cursor:not-allowed;opacity:.72}
.student-council-setup-stage__select-chevron{position:absolute;right:18px;top:50%;transform:translateY(-50%);pointer-events:none;color:var(--color-text-muted)}
.student-council-setup-stage__field-helper{font-size:12px;line-height:1.5;color:var(--color-text-muted)}
.student-council-setup-stage__actions{display:flex;flex-direction:column;align-items:flex-start;gap:12px;margin-top:auto}
.student-council-setup-stage__primary-pill{width:fit-content;min-height:58px;padding:0 22px 0 8px;border:none;border-radius:999px;background:var(--color-primary);color:var(--color-banner-text);display:inline-flex;align-items:center;gap:14px;font-size:13px;font-weight:700;box-shadow:0 14px 28px color-mix(in srgb,var(--color-primary) 18%, transparent);transition:transform .18s ease,box-shadow .18s ease}
.student-council-setup-stage__primary-pill:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 18px 32px color-mix(in srgb,var(--color-primary) 24%, transparent)}
.student-council-setup-stage__primary-pill:disabled{opacity:.48;cursor:not-allowed}
.student-council-setup-stage__primary-pill-icon{width:42px;height:42px;border-radius:999px;background:var(--color-nav);color:var(--color-nav-text);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
.student-council-setup-stage__danger-pill{width:fit-content;min-height:54px;padding:0 20px 0 8px;border:1.5px solid rgba(217,45,32,.16);border-radius:999px;background:rgba(217,45,32,.06);color:#B42318;display:inline-flex;align-items:center;gap:14px;font-size:13px;font-weight:700}
.student-council-setup-stage__danger-pill:disabled{opacity:.48;cursor:not-allowed}
.student-council-setup-stage__danger-pill-icon{width:38px;height:38px;border-radius:999px;background:#D92D20;color:#FFFFFF;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}

@media (min-width:768px){
  .student-council-setup-stage{min-height:500px}
}
</style>
