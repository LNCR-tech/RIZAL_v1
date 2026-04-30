<template>
  <section class="sg-sub-page">
    <header class="sg-sub-header dashboard-enter dashboard-enter--1">
      <button class="sg-sub-back" type="button" @click="goBack">
        <ArrowLeft :size="20" />
      </button>
      <h1 class="sg-sub-title">{{ pageTitle }}</h1>
    </header>

    <div v-if="isCreated" class="sg-sub-card sg-create-success dashboard-enter dashboard-enter--2">
      <h2 class="sg-create-success-title">{{ childTypeName }} created!</h2>
      <p class="sg-create-success-copy">{{ createdUnit?.unit_name || '' }} has been created successfully.</p>
      <div class="sg-create-success-actions">
        <button class="sg-sub-action" type="button" @click="resetForm">Create Another</button>
        <button class="sg-create-back" type="button" @click="goBack">Back to Dashboard</button>
      </div>
    </div>

    <template v-else>
      <div class="sg-sub-card sg-create-card dashboard-enter dashboard-enter--2">
        <div class="sg-create-hierarchy" aria-label="Governance hierarchy">
          <span
            v-for="step in hierarchySteps"
            :key="step.id"
            class="sg-create-hierarchy__step"
            :class="`sg-create-hierarchy__step--${step.state}`"
          >
            {{ step.label }}
          </span>
        </div>

        <div class="sg-create-head">
          <span class="sg-create-head__icon">
            <component :is="childTypeIcon" :size="18" />
          </span>
          <div class="sg-create-head__copy">
            <span class="sg-create-head__eyebrow">{{ workspaceLabel }}</span>
            <h2 class="sg-create-head__title">{{ childTypeName }}</h2>
            <p class="sg-create-head__meta">{{ contextCopy }}</p>
          </div>
          <span class="sg-create-head__status">{{ scopeCountLabel }}</span>
        </div>

        <StudentCouncilSetupStage
          compact
          :show-header="false"
          :draft="draft"
          acronym-label="Acronym"
          :acronym-placeholder="acronymPlaceholder"
          name-label="Name"
          :name-placeholder="namePlaceholder"
          description-label="Notes (optional)"
          :description-placeholder="descriptionPlaceholder"
          :scope-label="scopeLabel"
          :scope-options="scopeOptions"
          :scope-placeholder="scopePlaceholder"
          :scope-helper="scopeHelper"
          :scope-disabled="scopeDisabled"
          :submit-label="submitLabel"
          :submit-disabled="submitDisabled"
          @update:draft="draft = $event"
          @submit="handleCreate"
        />
      </div>

      <p v-if="formError" class="sg-create-error dashboard-enter dashboard-enter--3">{{ formError }}</p>
    </template>
  </section>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Building2, GraduationCap, Layers3 } from 'lucide-vue-next'
import StudentCouncilSetupStage from '@/components/council/StudentCouncilSetupStage.vue'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import {
  createGovernanceUnit,
  getDepartments,
  getGovernanceAccess,
  getGovernanceUnitDetail,
  getGovernanceUnits,
  getPrograms,
} from '@/services/backendApi.js'
import { resolvePreferredGovernanceUnit } from '@/services/governanceScope.js'
import { createEmptyCouncilDraft } from '@/services/studentCouncilManagement.js'
import { withPreservedGovernancePreviewQuery } from '@/services/routeWorkspace.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()
const { apiBaseUrl, token } = useDashboardSession()
const { previewBundle } = useSgPreviewBundle(() => props.preview)
const { permissionCodes, isLoading: sgLoading } = useSgDashboard(props.preview)

const draft = ref(createEmptyCouncilDraft())
const isSaving = ref(false)
const isResolvingScope = ref(false)
const formError = ref('')
const isCreated = ref(false)
const createdUnit = ref(null)
const parentUnitId = ref(null)
const parentUnit = ref(null)
const scopeOptions = ref([])

// Determine child type from permission codes:
// create_sg → creates SG unit (SSG context)
// create_org → creates ORG unit (SG context)
const childType = computed(() => {
  const codes = new Set(permissionCodes.value)
  if (codes.has('create_sg')) return 'SG'
  if (codes.has('create_org')) return 'ORG'
  return null
})

const childTypeName = computed(() => {
  if (childType.value === 'SG') return 'SG Council'
  if (childType.value === 'ORG') return 'ORG'
  return 'Unit'
})

const pageTitle = computed(() => {
  if (childType.value === 'SG') return 'Create SG'
  if (childType.value === 'ORG') return 'Create ORG'
  return 'Create Unit'
})
const childTypeIcon = computed(() => {
  if (childType.value === 'SG') return Building2
  if (childType.value === 'ORG') return GraduationCap
  return Layers3
})
const scopeLabel = computed(() => {
  if (childType.value === 'SG') return 'Department'
  if (childType.value === 'ORG') return 'Program'
  return ''
})
const scopePlaceholder = computed(() => {
  if (isResolvingScope.value) {
    return childType.value === 'SG' ? 'Loading departments...' : 'Loading programs...'
  }

  if (childType.value === 'SG') {
    return scopeOptions.value.length ? 'Choose a department' : 'No available departments'
  }

  if (childType.value === 'ORG') {
    return scopeOptions.value.length ? 'Choose a program' : 'No available programs'
  }

  return 'Select a scope'
})
const scopeDisabled = computed(() => isResolvingScope.value || scopeOptions.value.length === 0)
const scopeHelper = computed(() => {
  if (isResolvingScope.value) {
    return 'Loading available scopes.'
  }

  if (!parentUnitId.value) {
    return 'Parent unit unavailable.'
  }

  if (childType.value === 'SG') {
    return scopeOptions.value.length
      ? `${scopeOptions.value.length} department${scopeOptions.value.length === 1 ? '' : 's'} available.`
      : 'No departments left.'
  }

  if (childType.value === 'ORG') {
    return scopeOptions.value.length
      ? `${scopeOptions.value.length} program${scopeOptions.value.length === 1 ? '' : 's'} available.`
      : 'No programs left.'
  }

  return ''
})
const submitLabel = computed(() => {
  if (isSaving.value) return 'Creating...'
  if (isResolvingScope.value) return 'Loading...'
  if (childType.value === 'SG') return 'Create SG'
  if (childType.value === 'ORG') return 'Create ORG'
  return 'Create Unit'
})
const submitDisabled = computed(() => {
  if (isSaving.value || isResolvingScope.value || !childType.value || !parentUnitId.value) return true
  const d = draft.value
  return !d?.acronym?.trim() || !d?.name?.trim() || !d?.scopeId
})
const hierarchySteps = computed(() => {
  const order = ['SSG', 'SG', 'ORG']
  const activeIndex = Math.max(0, order.indexOf(childType.value || 'SSG'))

  return order.map((label, index) => ({
    id: label,
    label,
    state: index < activeIndex ? 'done' : index === activeIndex ? 'active' : 'pending',
  }))
})
const workspaceLabel = computed(() => {
  if (childType.value === 'SG') return 'SSG creates SG'
  if (childType.value === 'ORG') return 'SG creates ORG'
  return 'Governance'
})
const parentUnitLabel = computed(() => (
  parentUnit.value?.unit_code
  || parentUnit.value?.unit_name
  || (childType.value === 'SG' ? 'SSG' : 'SG')
))
const contextCopy = computed(() => {
  if (isResolvingScope.value) return 'Loading hierarchy.'
  return `Parent: ${parentUnitLabel.value}`
})
const scopeCountLabel = computed(() => {
  if (isResolvingScope.value) return 'Loading'
  const count = scopeOptions.value.length
  if (count <= 0) return 'None left'
  const noun = childType.value === 'SG' ? 'dept' : 'program'
  return `${count} ${noun}${count === 1 ? '' : 's'}`
})
const acronymPlaceholder = computed(() => childType.value === 'SG' ? 'e.g. CSC' : 'e.g. JPCS')
const namePlaceholder = computed(() => childType.value === 'SG' ? 'e.g. Computing Student Council' : 'e.g. Junior Philippine Computer Society')
const descriptionPlaceholder = computed(() => childType.value === 'SG' ? 'Short council purpose' : 'Short organization purpose')

function goBack() {
  router.push(
    props.preview
      ? withPreservedGovernancePreviewQuery(route, '/exposed/governance')
      : '/governance'
  )
}

watch(
  [apiBaseUrl, token, () => sgLoading.value, childType, () => props.preview, () => route.query?.variant],
  async ([url, authToken, isLoading, currentChildType, preview]) => {
    if (isLoading || !currentChildType) return
    if (preview) {
      resolvePreviewCreateContext(currentChildType)
      return
    }
    if (!url || !authToken) return
    await resolveCreateContext(url, authToken, currentChildType)
  },
  { immediate: true }
)

function normalizeOptions(options = []) {
  return [...options].sort((left, right) => left.label.localeCompare(right.label))
}

function syncDraftScopeSelection() {
  const availableValues = scopeOptions.value.map((option) => String(option.value))
  const currentScopeId = String(draft.value?.scopeId || '')
  const nextScopeId = availableValues.includes(currentScopeId) ? currentScopeId : (availableValues[0] || '')

  if (draft.value.scopeId !== nextScopeId) {
    draft.value = {
      ...draft.value,
      scopeId: nextScopeId,
    }
  }
}

function formatCreateError(error) {
  const rawMessage = String(error?.message || '').trim()
  const normalizedMessage = rawMessage.toLowerCase()

  if (!rawMessage) {
    return `Unable to create ${childTypeName.value}.`
  }

  if (normalizedMessage.includes('must include department_id')) {
    return 'Choose a department for this SG.'
  }

  if (normalizedMessage.includes('must include program_id')) {
    return 'Choose a program for this ORG.'
  }

  if (normalizedMessage.includes('only one sg unit is allowed per department')) {
    return 'That department already has an SG.'
  }

  if (normalizedMessage.includes('only one org unit is allowed per program')) {
    return 'That program already has an ORG.'
  }

  return rawMessage
}

async function loadScopeOptions(url, authToken, currentChildType, resolvedParentUnit) {
  if (currentChildType === 'SG') {
    const [departments, childUnits] = await Promise.all([
      getDepartments(url, authToken),
      getGovernanceUnits(url, authToken, {
        unit_type: 'SG',
        parent_unit_id: Number(resolvedParentUnit.id),
      }),
    ])

    const coveredDepartmentIds = new Set(
      childUnits
        .filter((unit) => unit?.is_active !== false)
        .map((unit) => Number(unit.department_id))
        .filter((value) => Number.isFinite(value))
    )

    return normalizeOptions(
      departments
        .filter((department) => !coveredDepartmentIds.has(Number(department.id)))
        .map((department) => ({
          value: String(department.id),
          label: department.name,
        }))
    )
  }

  if (currentChildType === 'ORG') {
    const parentDepartmentId = Number(resolvedParentUnit?.department_id)
    if (!Number.isFinite(parentDepartmentId)) {
      throw new Error('Your SG must have a department scope before it can create program organizations.')
    }

    const [programs, childUnits] = await Promise.all([
      getPrograms(url, authToken),
      getGovernanceUnits(url, authToken, {
        unit_type: 'ORG',
        parent_unit_id: Number(resolvedParentUnit.id),
      }),
    ])

    const coveredProgramIds = new Set(
      childUnits
        .filter((unit) => unit?.is_active !== false)
        .map((unit) => Number(unit.program_id))
        .filter((value) => Number.isFinite(value))
    )

    return normalizeOptions(
      programs
        .filter((program) => Array.isArray(program.department_ids) && program.department_ids.includes(parentDepartmentId))
        .filter((program) => !coveredProgramIds.has(Number(program.id)))
        .map((program) => ({
          value: String(program.id),
          label: program.name,
        }))
    )
  }

  return []
}

async function resolveCreateContext(url, authToken, currentChildType) {
  parentUnitId.value = null
  parentUnit.value = null
  scopeOptions.value = []
  isResolvingScope.value = true
  formError.value = ''

  try {
    const access = await getGovernanceAccess(url, authToken)
    const resolvedParentAccessUnit = resolvePreferredGovernanceUnit(access, {
      requiredPermissionCode: currentChildType === 'SG' ? 'create_sg' : 'create_org',
    })

    const resolvedParentUnitId = Number(resolvedParentAccessUnit?.governance_unit_id)
    if (!Number.isFinite(resolvedParentUnitId)) {
      throw new Error(`You do not have a parent governance unit that can create ${childTypeName.value}.`)
    }

    parentUnitId.value = resolvedParentUnitId
    parentUnit.value = await getGovernanceUnitDetail(url, authToken, resolvedParentUnitId)
    scopeOptions.value = await loadScopeOptions(url, authToken, currentChildType, parentUnit.value)
    syncDraftScopeSelection()
  } catch (error) {
    formError.value = formatCreateError(error)
  } finally {
    isResolvingScope.value = false
  }
}

function resolvePreviewCreateContext(currentChildType) {
  parentUnit.value = previewBundle.value?.activeUnit || null
  parentUnitId.value = Number(parentUnit.value?.id || null)
  formError.value = ''
  isResolvingScope.value = false

  const availableScopes = Array.isArray(previewBundle.value?.createUnit?.scopeOptions)
    ? previewBundle.value.createUnit.scopeOptions
    : []

  if (previewBundle.value?.createUnit?.childType !== currentChildType) {
    scopeOptions.value = []
    formError.value = `Preview data for ${childTypeName.value} is unavailable right now.`
    return
  }

  scopeOptions.value = normalizeOptions(
    availableScopes.map((option) => ({
      value: String(option.value),
      label: option.label,
    }))
  )
  syncDraftScopeSelection()
}

async function resetForm() {
  draft.value = createEmptyCouncilDraft()
  formError.value = ''
  isCreated.value = false
  createdUnit.value = null

  if (props.preview && childType.value) {
    resolvePreviewCreateContext(childType.value)
    return
  }

  if (apiBaseUrl.value && token.value && childType.value) {
    await resolveCreateContext(apiBaseUrl.value, token.value, childType.value)
  } else {
    syncDraftScopeSelection()
  }
}

async function handleCreate() {
  if (submitDisabled.value) return

  if (props.preview) {
    createdUnit.value = {
      id: Date.now(),
      unit_code: draft.value.acronym.trim(),
      unit_name: draft.value.name.trim(),
      unit_type: childType.value,
      parent_unit_id: parentUnitId.value || null,
      department_id: childType.value === 'SG' ? Number(draft.value.scopeId) : Number(parentUnit.value?.department_id) || null,
      program_id: childType.value === 'ORG' ? Number(draft.value.scopeId) : null,
    }
    isCreated.value = true
    return
  }

  isSaving.value = true
  formError.value = ''

  const normalizedScopeId = Number(draft.value.scopeId)
  const payload = {
    unit_code: draft.value.acronym.trim(),
    unit_name: draft.value.name.trim(),
    description: (draft.value.description || '').trim() || null,
    unit_type: childType.value,
    parent_unit_id: parentUnitId.value || null,
  }

  if (childType.value === 'SG') {
    payload.department_id = Number.isFinite(normalizedScopeId) ? normalizedScopeId : null
  }

  if (childType.value === 'ORG') {
    payload.department_id = Number(parentUnit.value?.department_id) || null
    payload.program_id = Number.isFinite(normalizedScopeId) ? normalizedScopeId : null
  }

  try {
    const result = await createGovernanceUnit(apiBaseUrl.value, token.value, payload)
    createdUnit.value = result
    isCreated.value = true
  } catch (e) {
    formError.value = formatCreateError(e)
  } finally { isSaving.value = false }
}
</script>

<style scoped>
@import '@/assets/css/sg-sub-views.css';

.sg-create-card { display: flex; flex-direction: column; gap: 16px; padding: 18px 16px 20px; }
.sg-create-hierarchy { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }
.sg-create-hierarchy__step { min-height: 34px; border-radius: 14px; background: color-mix(in srgb, var(--color-field-surface) 78%, var(--color-surface)); color: var(--color-text-muted); display: inline-flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800; letter-spacing: 0; }
.sg-create-hierarchy__step--done { color: var(--color-text-primary); background: color-mix(in srgb, var(--color-primary) 9%, var(--color-surface)); }
.sg-create-hierarchy__step--active { color: var(--color-banner-text); background: var(--color-primary); }
.sg-create-head { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 12px; }
.sg-create-head__icon { width: 42px; height: 42px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; background: var(--color-nav); color: var(--color-nav-text); }
.sg-create-head__copy { min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.sg-create-head__eyebrow { font-size: 10px; font-weight: 800; color: var(--color-primary); text-transform: uppercase; letter-spacing: 0.04em; }
.sg-create-head__title { margin: 0; font-size: 20px; line-height: 1.1; font-weight: 800; color: var(--color-text-primary); letter-spacing: 0; }
.sg-create-head__meta { margin: 0; font-size: 12px; line-height: 1.25; color: var(--color-text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sg-create-head__status { min-height: 32px; padding: 0 10px; border-radius: 999px; display: inline-flex; align-items: center; justify-content: center; background: color-mix(in srgb, var(--color-primary) 10%, var(--color-surface)); color: var(--color-text-primary); font-size: 11px; font-weight: 800; white-space: nowrap; }

.sg-create-success { text-align: center; padding: 32px 24px; }
.sg-create-success-title { font-size: 20px; font-weight: 800; color: var(--color-primary); margin-bottom: 6px; }
.sg-create-success-copy { font-size: 14px; color: var(--color-text-muted); margin-bottom: 20px; }
.sg-create-success-actions { display: flex; gap: 12px; justify-content: center; }
.sg-create-back { background: none; border: none; color: var(--color-text-muted); font-size: 13px; font-weight: 600; cursor: pointer; }
.sg-create-error { color: var(--color-status-non-compliant); font-size: 13px; text-align: center; line-height: 1.6; }

@media (max-width: 640px) {
  .sg-create-head { grid-template-columns: auto minmax(0, 1fr); }
  .sg-create-head__status { grid-column: 1 / -1; width: fit-content; }
}
</style>
