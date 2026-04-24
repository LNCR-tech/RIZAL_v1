<template>
  <div class="student-council-member-stage">
    <div class="student-council-member-stage__header">
      <div class="student-council-member-stage__heading">
        <h2 class="student-council-member-stage__title">{{ title }}</h2>
        <p v-if="subtitle" class="student-council-member-stage__subtitle">{{ subtitle }}</p>
      </div>

      <button
        v-if="showClose"
        class="student-council-member-stage__close"
        type="button"
        aria-label="Close"
        @click="$emit('cancel')"
      >
        <X :size="18" />
      </button>
    </div>

    <!-- Scrollable Content Area -->
    <div class="student-council-member-stage__scroll-area">
      <div class="student-council-member-stage__scroll-content">
        <div class="student-council-member-stage__search-shell" :class="{ 'student-council-member-stage__search-shell--open': searchExpanded }">
          <div class="student-council-member-stage__search-input-row">
            <template v-if="selectedStudent">
              <div class="student-council-member-stage__selected-pill" aria-live="polite">
                <span class="student-council-member-stage__selected-id">{{ selectedStudent.studentId }}</span>
                <span class="student-council-member-stage__selected-name">{{ selectedStudent.fullName }}</span>
              </div>
            </template>
            <template v-else>
              <input
                :value="searchQuery"
                v-bind="memberSearchInputAttrs"
                type="text"
                class="student-council-member-stage__search-input"
                :placeholder="searchPlaceholder"
                @focus="$emit('focus-search')"
                @input="$emit('update:searchQuery', $event.target.value)"
              >
            </template>

            <button class="student-council-member-stage__search-icon" type="button" aria-label="Search student">
              <Search :size="20" />
            </button>
          </div>

          <div class="student-council-member-stage__search-results">
            <div class="student-council-member-stage__search-results-inner">
              <button
                v-for="student in filteredStudents"
                :key="student.id"
                class="student-council-member-stage__result"
                type="button"
                @click="$emit('select-student', student)"
              >
                <span class="student-council-member-stage__result-id">{{ student.studentId }}</span>
                <span class="student-council-member-stage__result-name">{{ student.fullName }}</span>
              </button>

              <p v-if="searchExpanded && !filteredStudents.length" class="student-council-member-stage__empty">
                No matching students found.
              </p>
            </div>
          </div>
        </div>

        <label class="student-council-member-stage__field">
          <span class="student-council-member-stage__field-label">Position</span>
          <input
            :value="position"
            type="text"
            class="student-council-member-stage__field-input"
            placeholder="e.g., President, Secretary, Treasurer"
            @input="$emit('update:position', $event.target.value)"
          >
        </label>

        <Transition
          name="student-council-permissions"
          @before-enter="onPermissionsBeforeEnter"
          @enter="onPermissionsEnter"
          @after-enter="onPermissionsAfterEnter"
          @before-leave="onPermissionsBeforeLeave"
          @leave="onPermissionsLeave"
          @after-leave="onPermissionsAfterLeave"
        >
          <section v-if="showPermissions" class="student-council-member-stage__permissions">
            <h3 class="student-council-member-stage__permissions-title">{{ permissionsTitle }}</h3>

            <div
              v-for="category in permissionCatalog"
              :key="category.id"
              class="student-council-member-stage__permission-group"
            >
              <p class="student-council-member-stage__permission-label">{{ category.label }}</p>
              <div class="student-council-member-stage__permission-pills">
                <button
                  v-for="permission in category.permissions"
                  :key="permission.id"
                  type="button"
                  class="student-council-member-stage__permission-pill"
                  :class="{ 'student-council-member-stage__permission-pill--selected': selectedPermissionIds.includes(permission.id) }"
                  @click="$emit('toggle-permission', permission.id)"
                >
                  {{ permission.label }}
                </button>
              </div>
            </div>
          </section>
        </Transition>
      </div>
    </div>

    <!-- Fixed Actions Area -->
    <div class="student-council-member-stage__actions" :class="{ 'student-council-member-stage__actions--danger': showDelete }">
      <button
        class="student-council-member-stage__primary"
        type="button"
        :disabled="submitDisabled"
        @click="$emit('submit')"
      >
        <span class="student-council-member-stage__primary-icon">
          <component :is="submitIcon" :size="18" />
        </span>
        {{ submitLabel }}
      </button>

      <button
        v-if="showDelete"
        class="student-council-member-stage__danger"
        type="button"
        :disabled="deleteDisabled"
        :aria-label="deleteLabel"
        @click="$emit('delete')"
      >
        <Trash2 :size="20" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Check, Search, SquarePlus, Trash2, X } from 'lucide-vue-next'
import { createSearchFieldAttrs } from '@/services/searchFieldAttrs.js'

const props = defineProps({
  title: {
    type: String,
    default: 'Add Member',
  },
  subtitle: {
    type: String,
    default: '',
  },
  searchQuery: {
    type: String,
    default: '',
  },
  searchPlaceholder: {
    type: String,
    default: 'Search enrolled students',
  },
  selectedStudent: {
    type: Object,
    default: null,
  },
  position: {
    type: String,
    default: '',
  },
  filteredStudents: {
    type: Array,
    default: () => [],
  },
  searchExpanded: {
    type: Boolean,
    default: false,
  },
  showPermissions: {
    type: Boolean,
    default: false,
  },
  permissionsTitle: {
    type: String,
    default: 'Permissions',
  },
  permissionCatalog: {
    type: Array,
    default: () => [],
  },
  selectedPermissionIds: {
    type: Array,
    default: () => [],
  },
  submitLabel: {
    type: String,
    default: 'Continue',
  },
  submitDisabled: {
    type: Boolean,
    default: false,
  },
  showClose: {
    type: Boolean,
    default: false,
  },
  isEditing: {
    type: Boolean,
    default: false,
  },
  showDelete: {
    type: Boolean,
    default: false,
  },
  deleteDisabled: {
    type: Boolean,
    default: false,
  },
  deleteLabel: {
    type: String,
    default: 'Delete member',
  },
})

defineEmits([
  'cancel',
  'delete',
  'focus-search',
  'select-student',
  'submit',
  'toggle-permission',
  'update:position',
  'update:searchQuery',
])

const submitIcon = computed(() => (props.isEditing ? Check : SquarePlus))
const memberSearchInputAttrs = createSearchFieldAttrs('student-council-member-search')

const nextFrame = (callback) => requestAnimationFrame(() => requestAnimationFrame(callback))

function onPermissionsBeforeEnter(element) {
  element.style.height = '0px'
  element.style.opacity = '0'
  element.style.transform = 'translateY(-8px)'
  element.style.willChange = 'height, opacity, transform'
}

function onPermissionsEnter(element) {
  const height = element.scrollHeight
  element.style.transition = 'height 480ms cubic-bezier(0.22, 1, 0.36, 1), opacity 280ms ease, transform 380ms cubic-bezier(0.22, 1, 0.36, 1)'
  nextFrame(() => {
    element.style.height = `${height}px`
    element.style.opacity = '1'
    element.style.transform = 'translateY(0)'
  })
}

function onPermissionsAfterEnter(element) {
  element.style.height = 'auto'
  element.style.transition = ''
  element.style.willChange = ''
}

function onPermissionsBeforeLeave(element) {
  element.style.height = `${element.scrollHeight}px`
  element.style.opacity = '1'
  element.style.transform = 'translateY(0)'
  element.style.willChange = 'height, opacity, transform'
}

function onPermissionsLeave(element) {
  element.style.transition = 'height 320ms ease, opacity 220ms ease, transform 240ms ease'
  nextFrame(() => {
    element.style.height = '0px'
    element.style.opacity = '0'
    element.style.transform = 'translateY(-6px)'
  })
}

function onPermissionsAfterLeave(element) {
  element.style.transition = ''
  element.style.height = ''
  element.style.opacity = ''
  element.style.transform = ''
  element.style.willChange = ''
}
</script>

<style scoped>
.student-council-member-stage{display:flex;flex-direction:column;gap:16px;min-height:0;flex:1}
.student-council-member-stage__header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-shrink:0}
.student-council-member-stage__heading{display:grid;gap:10px;min-width:0}
.student-council-member-stage__title{margin:0;font-size:clamp(36px,10vw,64px);line-height:.92;letter-spacing:-.08em;font-weight:700;color:var(--color-text-always-dark)}
.student-council-member-stage__subtitle{margin:0;max-width:42ch;font-size:13px;line-height:1.6;font-weight:600;color:var(--color-text-muted)}
.student-council-member-stage__close{width:42px;height:42px;border:none;border-radius:999px;background:var(--color-field-surface);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 14%, transparent);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;color:var(--color-text-always-dark)}

.student-council-member-stage__scroll-area{flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;padding-right:6px;margin-right:-6px}
.student-council-member-stage__scroll-content{display:flex;flex-direction:column;gap:20px;padding-bottom:12px}

.student-council-member-stage__search-shell{display:grid;grid-template-rows:auto 0fr;gap:0;padding:16px 18px;border-radius:30px;background:var(--color-field-surface);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 16%, transparent);transition:grid-template-rows .4s cubic-bezier(.22,1,.36,1),border-radius .4s cubic-bezier(.22,1,.36,1),box-shadow .18s ease}
.student-council-member-stage__search-shell--open{grid-template-rows:auto 1fr;border-radius:32px}
.student-council-member-stage__search-input-row{display:flex;align-items:center;gap:12px;min-height:52px}
.student-council-member-stage__search-input{flex:1;min-width:0;border:none;background:transparent;outline:none;font-size:14px;font-weight:500;color:var(--color-text-always-dark)}
.student-council-member-stage__search-input::placeholder{color:var(--color-text-muted)}
.student-council-member-stage__search-icon{width:40px;height:40px;border:none;border-radius:999px;background:transparent;color:var(--color-primary);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
.student-council-member-stage__search-results{overflow:hidden;min-height:0}
.student-council-member-stage__search-results-inner{display:flex;flex-direction:column;gap:10px;padding-top:12px}
.student-council-member-stage__result{display:flex;align-items:center;gap:10px;padding:0;border:none;background:transparent;text-align:left}
.student-council-member-stage__result-id,.student-council-member-stage__selected-id{min-width:76px;padding:10px 14px;border-radius:999px;background:var(--color-primary);font-size:11px;font-weight:700;line-height:1;color:var(--color-banner-text);text-align:center;flex-shrink:0}
.student-council-member-stage__result-name,.student-council-member-stage__selected-name{font-size:14px;font-weight:500;line-height:1.2;color:var(--color-text-always-dark)}
.student-council-member-stage__selected-pill{display:flex;align-items:center;gap:10px;min-width:0;flex:1}
.student-council-member-stage__empty{margin:0;font-size:13px;color:var(--color-text-muted)}
.student-council-member-stage__field{display:flex;flex-direction:column;gap:10px}
.student-council-member-stage__field-label{font-size:14px;font-weight:600;color:var(--color-text-always-dark)}
.student-council-member-stage__field-input{width:100%;min-height:52px;padding:0 18px;border:none;border-radius:999px;background:var(--color-field-surface);outline:none;font-size:14px;font-weight:500;color:var(--color-text-always-dark);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 16%, transparent);transition:background-color .18s ease,box-shadow .18s ease}
.student-council-member-stage__field-input:focus{background:var(--color-field-surface);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 28%, transparent)}
.student-council-member-stage__field-input::placeholder{color:var(--color-text-muted)}
.student-council-member-stage__permissions{overflow:hidden}
.student-council-member-stage__permissions-title{margin:0 0 16px;font-size:20px;line-height:1;font-weight:700;color:var(--color-text-always-dark)}
.student-council-member-stage__permission-group{display:flex;flex-direction:column;gap:10px}
.student-council-member-stage__permission-group + .student-council-member-stage__permission-group{margin-top:12px}
.student-council-member-stage__permission-label{margin:0;font-size:14px;font-weight:500;color:var(--color-text-always-dark)}
.student-council-member-stage__permission-pills{display:flex;flex-wrap:wrap;gap:8px}
.student-council-member-stage__permission-pill{min-height:42px;padding:0 20px;border:none;border-radius:999px;background:var(--color-field-surface);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 14%, transparent);font-size:13px;font-weight:500;color:var(--color-text-always-dark);transition:background .22s ease,color .22s ease,transform .18s ease,box-shadow .22s ease}
.student-council-member-stage__permission-pill--selected{background:var(--color-pill-row-active-bg);color:var(--color-pill-row-active-text)}
.student-council-member-stage__permission-pill:active{transform:scale(.97)}
.student-council-member-stage__actions{display:flex;flex-direction:column;gap:12px;padding-top:16px;flex-shrink:0;border-top:1px solid color-mix(in srgb, var(--color-field-surface-strong) 40%, transparent)}
.student-council-member-stage__actions--danger{flex-direction:row;align-items:center}
.student-council-member-stage__secondary,.student-council-member-stage__primary{min-height:56px;border:none;border-radius:999px;font-family:'Manrope',sans-serif;font-size:13px;font-weight:700}
.student-council-member-stage__secondary{background:var(--color-field-surface);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 14%, transparent);color:var(--color-text-always-dark)}
.student-council-member-stage__primary{display:inline-flex;align-items:center;gap:14px;padding:0 24px 0 8px;background:var(--color-primary);color:var(--color-banner-text);align-self:flex-start}
.student-council-member-stage__actions--danger .student-council-member-stage__primary{flex:1;min-width:0}
.student-council-member-stage__primary:disabled{opacity:.48;cursor:not-allowed}
.student-council-member-stage__primary-icon{width:40px;height:40px;border-radius:999px;background:var(--color-nav);color:var(--color-nav-text);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
.student-council-member-stage__danger{width:56px;height:56px;border:none;border-radius:999px;background:var(--color-field-surface);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 14%, transparent);display:inline-flex;align-items:center;justify-content:center;color:#E5332A}
.student-council-member-stage__danger:disabled{opacity:.48;cursor:not-allowed}

@media (min-width:768px){
  .student-council-member-stage__title{font-size:clamp(42px,5vw,64px)}
}
</style>
