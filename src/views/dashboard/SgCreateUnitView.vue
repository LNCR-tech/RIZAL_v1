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
      <div class="sg-sub-card sg-create-intro dashboard-enter dashboard-enter--2">
        <div class="sg-create-intro__icon">
          <component :is="childTypeIcon" :size="22" />
        </div>
        <div class="sg-create-intro__copy">
          <span class="sg-create-intro__eyebrow">{{ introEyebrow }}</span>
          <h2 class="sg-create-intro__title">{{ introTitle }}</h2>
          <p class="sg-create-intro__description">{{ introDescription }}</p>
        </div>
        <div class="sg-create-intro__badge">
          <strong>{{ scopeOptions.length }}</strong>
          <span>{{ scopeBadgeLabel }}</span>
        </div>
      </div>

      <div class="sg-sub-card dashboard-enter dashboard-enter--3">
        <StudentCouncilSetupStage
          :draft="draft"
          :eyebrow="stageEyebrow"
          :title="childTypeName"
          :description="stageDescription"
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

      <p v-if="formError" class="sg-create-error dashboard-enter dashboard-enter--4">{{ formError }}</p>
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
  if (childType.value === 'SG') return 'College-Level Council'
  if (childType.value === 'ORG') return 'Organization'
  return 'Unit'
})

const pageTitle = computed(() => `Create ${childTypeName.value}`)
const childTypeIcon = computed(() => {
  if (childType.value === 'SG') return Building2
  if (childType.value === 'ORG') return GraduationCap
  return Layers3
})
const introEyebrow = computed(() => childType.value === 'SG' ? 'SSG Workspace' : 'SG Workspace')
const introTitle = computed(() => {
  if (childType.value === 'SG') return 'Create a department-wide student council'
  if (childType.value === 'ORG') return 'Create one program organization under your SG'
  return 'Create a governance unit'
})
const introDescription = computed(() => {
  if (childType.value === 'SG') {
    return 'Each college-level council belongs to one department under your active SSG. Departments that already have an active council are automatically hidden.'
  }

  if (childType.value === 'ORG') {
    return 'Each organization belongs to one program inside your SG department. Programs that already have an active organization are automatically hidden.'
  }

  return 'Governance scope is resolved from the live backend structure before creation.'
})
const stageEyebrow = computed(() => childType.value === 'SG' ? 'Department Scope' : 'Program Scope')
const stageDescription = computed(() => {
  if (isResolvingScope.value) {
    return 'Loading the live governance scope for this unit...'
  }

  if (childType.value === 'SG') {
    return 'This council will represent one department. The backend currently allows one active SG per department.'
  }

  if (childType.value === 'ORG') {
    return 'This organization will represent one program under your SG department. The backend currently allows one active ORG per program.'
  }

  return 'Complete the required details below.'
})
const scopeLabel = computed(() => {
  if (childType.value === 'SG') return 'College / Department Scope'
  if (childType.value === 'ORG') return 'Program Scope'
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
    return 'We are reading the current governance hierarchy and filtering out scopes that already have an active council.'
  }

  if (!parentUnitId.value) {
    return 'Your parent governance unit is still being resolved from backend access.'
  }

  if (childType.value === 'SG') {
    return scopeOptions.value.length
      ? `${scopeOptions.value.length} department(s) are still available for a new council under your SSG.`
      : 'Every department already has an active college-level council under this SSG.'
  }

  if (childType.value === 'ORG') {
    return scopeOptions.value.length
      ? `${scopeOptions.value.length} program(s) are still available for a new organization under your SG.`
      : 'Every eligible program in this SG department already has an active organization.'
  }

  return ''
})
const scopeBadgeLabel = computed(() => {
  if (childType.value === 'SG') return scopeOptions.value.length === 1 ? 'department left' : 'departments left'
  if (childType.value === 'ORG') return scopeOptions.value.length === 1 ? 'program left' : 'programs left'
  return 'options'
})
const submitLabel = computed(() => {
  if (isSaving.value) return 'Creating...'
  if (isResolvingScope.value) return 'Preparing scope...'
  return `Create ${childTypeName.value}`
})
const submitDisabled = computed(() => {
  if (isSaving.value || isResolvingScope.value || !childType.value || !parentUnitId.value) return true
  const d = draft.value
  return !d?.acronym?.trim() || !d?.name?.trim() || !d?.scopeId
})

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
    return 'Choose the department this college-level council will represent. SG units are department-scoped in the current backend structure.'
  }

  if (normalizedMessage.includes('must include program_id')) {
    return 'Choose the program this organization will represent. ORG units are program-scoped in the current backend structure.'
  }

  if (normalizedMessage.includes('only one sg unit is allowed per department')) {
    return 'That department already has an active college-level council. Pick another department.'
  }

  if (normalizedMessage.includes('only one org unit is allowed per program')) {
    return 'That program already has an active organization. Pick another program.'
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

.sg-create-intro {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 16px;
  align-items: center;
  padding: 22px 18px;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-primary) 18%, transparent), transparent 50%),
    linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 10%, var(--color-surface)) 0%, var(--color-surface) 70%);
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, transparent);
}

.sg-create-intro::after {
  content: '';
  position: absolute;
  inset: auto -12% -62% 42%;
  height: 170px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  filter: blur(20px);
  pointer-events: none;
}

.sg-create-intro__icon {
  position: relative;
  z-index: 1;
  width: 54px;
  height: 54px;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-banner-text);
  box-shadow: 0 16px 30px color-mix(in srgb, var(--color-primary) 24%, transparent);
}

.sg-create-intro__copy {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sg-create-intro__eyebrow {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.sg-create-intro__title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: var(--color-text-primary);
}

.sg-create-intro__description {
  margin: 0;
  max-width: 48ch;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.sg-create-intro__badge {
  position: relative;
  z-index: 1;
  min-width: 92px;
  padding: 14px 16px;
  border-radius: 20px;
  background: color-mix(in srgb, var(--color-primary) 10%, var(--color-surface));
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.sg-create-intro__badge strong {
  font-size: 26px;
  line-height: 1;
  font-weight: 800;
  color: var(--color-text-primary);
}

.sg-create-intro__badge span {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.sg-create-success { text-align: center; padding: 32px 24px; }
.sg-create-success-title { font-size: 20px; font-weight: 800; color: var(--color-primary); margin-bottom: 6px; }
.sg-create-success-copy { font-size: 14px; color: var(--color-text-muted); margin-bottom: 20px; }
.sg-create-success-actions { display: flex; gap: 12px; justify-content: center; }
.sg-create-back { background: none; border: none; color: var(--color-text-muted); font-size: 13px; font-weight: 600; cursor: pointer; }
.sg-create-error { color: #e74c3c; font-size: 13px; text-align: center; line-height: 1.6; }

@media (max-width: 640px) {
  .sg-create-intro {
    grid-template-columns: 1fr;
    justify-items: flex-start;
  }

  .sg-create-intro__badge {
    min-width: 0;
  }
}
</style>
