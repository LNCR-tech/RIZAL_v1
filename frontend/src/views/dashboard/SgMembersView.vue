<template>
  <section class="sg-members-page">
    <header class="sg-members-hero dashboard-enter dashboard-enter--1">
      <div class="sg-members-hero__top">
        <button class="sg-members-back" type="button" @click="goBack">
          <ArrowLeft :size="18" />
        </button>
        <span class="sg-members-hero__eyebrow">Governance Member Management</span>
      </div>

      <div class="sg-members-hero__body">
        <div class="sg-members-hero__copy">
          <h1 class="sg-members-hero__title">
            {{ managedUnitName ? `${managedUnitName} Members` : 'Manage Members' }}
          </h1>
          <p class="sg-members-hero__description">{{ heroDescription }}</p>
        </div>

        <div class="sg-members-hero__chips">
          <span class="sg-members-chip">{{ managedUnitType || 'GOV' }}</span>
          <span class="sg-members-chip">{{ filteredMembers.length }} {{ filteredMembers.length === 1 ? 'Member' : 'Members' }}</span>
          <span class="sg-members-chip" :class="{ 'sg-members-chip--muted': !canAssignMemberPermissions }">
            {{ canAssignMemberPermissions ? 'Permissions Editable' : 'Permissions Read Only' }}
          </span>
        </div>
      </div>
    </header>

    <div v-if="isLoading" class="sg-members-state dashboard-enter dashboard-enter--2">
      <p>Loading governance members...</p>
    </div>

    <div v-else-if="loadError" class="sg-members-state sg-members-state--error dashboard-enter dashboard-enter--2">
      <p>{{ loadError }}</p>
      <button class="sg-members-action" type="button" @click="reload">Try Again</button>
    </div>

    <template v-else>
      <section class="sg-members-overview dashboard-enter dashboard-enter--2">
        <article class="sg-members-panel">
          <div class="sg-members-panel__header">
            <div>
              <p class="sg-members-panel__eyebrow">Hierarchy</p>
              <h2 class="sg-members-panel__title">Who manages this unit</h2>
            </div>
            <Building2 :size="18" :stroke-width="2.2" class="sg-members-panel__icon" />
          </div>

          <div class="sg-members-hierarchy">
            <article
              v-for="step in hierarchySteps"
              :key="step.key"
              class="sg-members-hierarchy__item"
              :class="`sg-members-hierarchy__item--${step.tone}`"
            >
              <span class="sg-members-hierarchy__tag">{{ step.label }}</span>
              <strong class="sg-members-hierarchy__name">{{ step.title }}</strong>
              <p class="sg-members-hierarchy__caption">{{ step.caption }}</p>
            </article>
          </div>
        </article>

        <article class="sg-members-panel">
          <div class="sg-members-panel__header">
            <div>
              <p class="sg-members-panel__eyebrow">Rules</p>
              <h2 class="sg-members-panel__title">Backend authority</h2>
            </div>
            <ShieldCheck :size="18" :stroke-width="2.2" class="sg-members-panel__icon" />
          </div>

          <div class="sg-members-facts">
            <div class="sg-members-fact">
              <span class="sg-members-fact__label">Managed By</span>
              <strong class="sg-members-fact__value">{{ managedByLabel }}</strong>
              <p class="sg-members-fact__caption">{{ managedByCaption }}</p>
            </div>

            <div class="sg-members-fact">
              <span class="sg-members-fact__label">Child Tier</span>
              <strong class="sg-members-fact__value">{{ childTierLabel }}</strong>
              <p class="sg-members-fact__caption">{{ childTierCaption }}</p>
            </div>

            <div class="sg-members-fact">
              <span class="sg-members-fact__label">Candidate Source</span>
              <strong class="sg-members-fact__value">{{ candidateScopeLabel }}</strong>
              <p class="sg-members-fact__caption">Only existing scoped students can be assigned here.</p>
            </div>

            <div class="sg-members-fact">
              <span class="sg-members-fact__label">Permission Grants</span>
              <strong class="sg-members-fact__value">{{ permissionPolicyValue }}</strong>
              <p class="sg-members-fact__caption">{{ permissionPolicyCaption }}</p>
            </div>
          </div>
        </article>
      </section>

      <section class="sg-members-toolbar dashboard-enter dashboard-enter--3">
        <div class="sg-members-search">
          <label class="sg-members-search__label" for="sg-member-search">Search officers</label>
          <div class="sg-members-search__shell">
            <Search :size="16" :stroke-width="2.1" class="sg-members-search__icon" />
            <input
              id="sg-member-search"
              v-model="searchQuery"
              type="text"
              class="sg-members-search__input"
              placeholder="Search by student ID, name, or position"
            />
          </div>
        </div>

        <button
          class="sg-members-action"
          type="button"
          :disabled="!canManageMembers"
          @click="openAddSheet"
        >
          <UserPlus :size="16" />
          <span>Add Member</span>
        </button>
      </section>

      <p class="sg-members-note dashboard-enter dashboard-enter--3">
        This screen assigns existing students to governance membership. It does not create new platform user accounts.
      </p>

      <section class="sg-members-list-shell dashboard-enter dashboard-enter--4">
        <div class="sg-members-list-shell__header">
          <div>
            <p class="sg-members-panel__eyebrow">Roster</p>
            <h2 class="sg-members-list-shell__title">Unit Officers</h2>
          </div>
          <span class="sg-members-list-shell__badge">{{ filteredMembers.length }}</span>
        </div>

        <div v-if="filteredMembers.length" class="sg-member-list">
          <article
            v-for="member in filteredMembers"
            :key="member.id"
            class="sg-member-card"
            @click="openMemberDetail(member)"
          >
            <div class="sg-member-card__avatar">{{ buildInitials(member.fullName) }}</div>

            <div class="sg-member-card__body">
              <div class="sg-member-card__top">
                <div class="sg-member-card__heading">
                  <strong class="sg-member-card__name">{{ member.fullName }}</strong>
                  <span class="sg-member-card__position">{{ member.position }}</span>
                </div>

                <button
                  class="sg-member-card__edit"
                  type="button"
                  aria-label="Edit member"
                  @click.stop="startEditing(member)"
                >
                  <SquarePen :size="16" />
                </button>
              </div>

              <div class="sg-member-card__meta">
                <span>{{ member.studentId || 'No student ID' }}</span>
                <span>{{ permissionCountLabel(member) }}</span>
              </div>

              <div class="sg-member-card__permissions">
                <template v-if="memberPermissionPreview(member).length">
                  <span
                    v-for="permission in memberPermissionPreview(member)"
                    :key="`${member.id}-${permission}`"
                    class="sg-member-card__permission"
                  >
                    {{ permission }}
                  </span>
                  <span
                    v-if="memberPermissionOverflowCount(member) > 0"
                    class="sg-member-card__permission sg-member-card__permission--muted"
                  >
                    +{{ memberPermissionOverflowCount(member) }} more
                  </span>
                </template>

                <span v-else class="sg-member-card__permission sg-member-card__permission--muted">
                  No permissions assigned
                </span>
              </div>
            </div>
          </article>
        </div>

        <div v-else class="sg-members-empty">
          <UsersRound :size="18" :stroke-width="2.1" />
          <p>No members match your search.</p>
        </div>
      </section>
    </template>

    <Transition name="sg-sheet">
      <div
        v-if="isSheetOpen"
        class="sg-sheet-backdrop"
        @click.self="closeSheet"
      >
        <div class="sg-sheet">
          <StudentCouncilMemberStage
            class="sg-sheet__content"
            :title="editingMemberId ? 'Edit Member' : 'Add Member'"
            :subtitle="sheetSubtitle"
            :search-query="memberDraft.searchQuery"
            :search-placeholder="sheetSearchPlaceholder"
            :selected-student="selectedStudent"
            :position="memberDraft.position"
            :filtered-students="candidateResults"
            :search-expanded="isCandidateSearchOpen && !selectedStudent"
            :show-permissions="showPermissions && canAssignMemberPermissions && permissionCatalog.length > 0"
            :permission-catalog="permissionCatalog"
            :permissions-title="permissionsTitle"
            :selected-permission-ids="memberDraft.permissionIds"
            :submit-label="submitLabel"
            :submit-disabled="submitDisabled"
            :is-editing="Boolean(editingMemberId)"
            :show-delete="Boolean(editingMemberId)"
            :delete-disabled="isDeleting || isSaving"
            delete-label="Delete member"
            show-close
            @cancel="closeSheet"
            @delete="handleDelete"
            @focus-search="isCandidateSearchOpen = true"
            @select-student="selectCandidate"
            @submit="handleSubmit"
            @toggle-permission="togglePermission"
            @update:position="memberDraft.position = $event"
            @update:searchQuery="updateCandidateQuery"
          />
        </div>
      </div>
    </Transition>

    <Transition name="sg-sheet">
      <div
        v-if="isDetailOpen && detailMember"
        class="sg-sheet-backdrop"
        @click.self="closeDetail"
      >
        <div class="sg-sheet sg-sheet--detail">
          <section class="sg-detail">
            <div class="sg-detail__header">
              <div class="sg-detail__identity">
                <div class="sg-detail__avatar">{{ buildInitials(detailMember.fullName) }}</div>
                <div>
                  <p class="sg-members-panel__eyebrow">Member Detail</p>
                  <h2 class="sg-detail__title">{{ detailMember.fullName }}</h2>
                  <p class="sg-detail__subtitle">{{ detailMember.position }}</p>
                </div>
              </div>

              <button class="sg-detail__close" type="button" @click="closeDetail">
                <X :size="18" />
              </button>
            </div>

            <div class="sg-detail__grid">
              <div class="sg-detail__field">
                <span class="sg-detail__label">Student ID</span>
                <div class="sg-detail__value">{{ detailMember.studentId || 'Unavailable' }}</div>
              </div>

              <div class="sg-detail__field">
                <span class="sg-detail__label">Permission Access</span>
                <div class="sg-detail__value">{{ permissionCountLabel(detailMember) }}</div>
              </div>

              <div class="sg-detail__field sg-detail__field--wide">
                <span class="sg-detail__label">Permissions</span>
                <div class="sg-detail__permissions">
                  <span
                    v-for="perm in detailMemberPermLabels"
                    :key="perm"
                    class="sg-detail__permission"
                  >
                    {{ perm }}
                  </span>
                  <span
                    v-if="!detailMemberPermLabels.length"
                    class="sg-detail__permission sg-detail__permission--muted"
                  >
                    No permissions assigned
                  </span>
                </div>
              </div>
            </div>

            <div class="sg-detail__actions">
              <button class="sg-members-action" type="button" @click="startEditing(detailMember)">
                <SquarePen :size="16" />
                <span>Edit Member</span>
              </button>

              <button
                class="sg-detail__delete"
                type="button"
                :disabled="isDeleting"
                @click="handleDeleteDetail"
              >
                {{ isDeleting ? 'Deleting...' : 'Delete Member' }}
              </button>
            </div>
          </section>
        </div>
      </div>
    </Transition>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  Building2,
  Search,
  ShieldCheck,
  SquarePen,
  UserPlus,
  UsersRound,
  X,
} from 'lucide-vue-next'
import StudentCouncilMemberStage from '@/components/council/StudentCouncilMemberStage.vue'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import {
  assignGovernanceMember,
  deleteGovernanceMember,
  getGovernanceAccess,
  getGovernanceUnitDetail,
  getGovernanceUnits,
  searchGovernanceStudentCandidates,
  updateGovernanceMember,
} from '@/services/backendApi.js'
import {
  createEmptyCouncilMemberDraft,
  formatGovernancePermissionLabel,
  getGovernancePermissionCatalogForUnitType,
  mapGovernanceMemberToCouncilMember,
  mapGovernanceStudentCandidateToCouncilCandidate,
  mapUiPermissionIdsToBackend,
} from '@/services/studentCouncilManagement.js'
import { resolvePreferredGovernanceUnit } from '@/services/governanceScope.js'
import { withPreservedGovernancePreviewQuery } from '@/services/routeWorkspace.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()
const { apiBaseUrl, currentUser, isSchoolItSession } = useDashboardSession()
const { previewBundle } = useSgPreviewBundle(() => props.preview)
const { isLoading: sgLoading, error: sgError, permissionCodes } = useSgDashboard(props.preview)

const isLoading = ref(true)
const loadError = ref('')
const members = ref([])
const managedUnit = ref(null)
const searchQuery = ref('')
const isSheetOpen = ref(false)
const isDetailOpen = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)
const editingMemberId = ref(null)
const detailMember = ref(null)
const isCandidateSearchOpen = ref(false)
const showPermissions = ref(false)
const candidateResults = ref([])
const governanceUnitId = ref(null)
let candidateTimer = null

const memberDraft = ref({ ...createEmptyCouncilMemberDraft(), searchQuery: '', selectedStudent: null })

const permissionCodeSet = computed(() => new Set(
  (Array.isArray(permissionCodes.value) ? permissionCodes.value : [])
    .map((code) => String(code || '').trim().toLowerCase())
    .filter(Boolean)
))

const managedUnitName = computed(() => String(
  managedUnit.value?.unit_name
  || previewBundle.value?.activeUnit?.unit_name
  || ''
).trim())

const managedUnitType = computed(() => String(
  managedUnit.value?.unit_type
  || previewBundle.value?.activeUnit?.unit_type
  || ''
).trim().toUpperCase())

const canManageMembers = computed(() => (
  props.preview
    ? true
    : isSchoolItSession(currentUser.value) || permissionCodeSet.value.has('manage_members')
))

const canAssignMemberPermissions = computed(() => (
  props.preview
    ? true
    : isSchoolItSession(currentUser.value) || permissionCodeSet.value.has('assign_permissions')
))

const permissionCatalog = computed(() => (
  canAssignMemberPermissions.value
    ? getGovernancePermissionCatalogForUnitType(managedUnitType.value)
    : []
))

const selectedStudent = computed(() => {
  const id = Number(memberDraft.value.studentId)
  return candidateResults.value.find((candidate) => candidate.userId === id) || memberDraft.value.selectedStudent || null
})

const submitLabel = computed(() => {
  if (isSaving.value) return editingMemberId.value ? 'Saving...' : 'Adding...'
  if (canAssignMemberPermissions.value && !showPermissions.value && permissionCatalog.value.length) {
    return 'Continue'
  }
  return editingMemberId.value ? 'Save Member' : 'Add Member'
})

const submitDisabled = computed(() => (
  !selectedStudent.value?.userId
  || !memberDraft.value.position.trim()
  || isSaving.value
))

const filteredMembers = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return members.value

  return members.value.filter((member) => (
    [member.studentId, member.fullName, member.position]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
      .includes(query)
  ))
})

const detailMemberPermLabels = computed(() => {
  if (!detailMember.value) return []
  return (detailMember.value.permissionIds || [])
    .map((id) => formatGovernancePermissionLabel(id))
    .filter(Boolean)
})

const managedByLabel = computed(() => {
  if (managedUnitType.value === 'SSG') return 'Campus Admin'
  if (managedUnitType.value === 'SG') return 'SSG officers'
  if (managedUnitType.value === 'ORG') return 'SG officers'
  return 'Authorized parent officers'
})

const managedByCaption = computed(() => {
  if (managedUnitType.value === 'SSG') return 'Only Campus Admin can add, edit, or remove SSG members.'
  if (managedUnitType.value === 'SG') return 'Active SSG members with manage_members can maintain SG membership.'
  if (managedUnitType.value === 'ORG') return 'Active SG members with manage_members can maintain ORG membership.'
  return 'Membership authority comes from the parent governance tier.'
})

const childTierLabel = computed(() => {
  if (managedUnitType.value === 'SSG') return 'SG'
  if (managedUnitType.value === 'SG') return 'ORG'
  if (managedUnitType.value === 'ORG') return 'None'
  return 'Pending'
})

const childTierCaption = computed(() => {
  if (managedUnitType.value === 'SSG') return 'SSG can create and manage SG child units.'
  if (managedUnitType.value === 'SG') return 'SG can create and manage ORG child units.'
  if (managedUnitType.value === 'ORG') return 'ORG is the last governance tier in the backend hierarchy.'
  return 'Child management rules will follow the backend scope.'
})

const candidateScopeLabel = computed(() => {
  if (managedUnitType.value === 'SSG') return 'School-wide students'
  if (managedUnitType.value === 'SG') return 'Department-scoped students'
  if (managedUnitType.value === 'ORG') return 'Program-scoped students'
  return 'Governance-scoped students'
})

const permissionPolicyValue = computed(() => (
  canAssignMemberPermissions.value ? 'Optional grants' : 'Read-only grants'
))

const permissionPolicyCaption = computed(() => (
  canAssignMemberPermissions.value
    ? 'The backend allows member assignment even when no permission codes are granted.'
    : 'You can still add or edit the member record, but you cannot change permission codes from this account.'
))

const heroDescription = computed(() => {
  if (!managedUnitType.value) {
    return 'Assign existing students to governance membership and keep the unit roster aligned to the backend hierarchy.'
  }

  return `${managedUnitType.value} membership is assigned from existing student records inside its governance scope. ${managedByLabel.value} manage this unit.`
})

const hierarchySteps = computed(() => {
  const activeType = managedUnitType.value
  const steps = [
    { key: 'SSG', label: 'Tier 1', title: 'SSG', caption: 'Campus-wide governance' },
    { key: 'SG', label: 'Tier 2', title: 'SG', caption: 'Department-level councils' },
    { key: 'ORG', label: 'Tier 3', title: 'ORG', caption: 'Program organizations' },
  ]

  return steps.map((step) => ({
    ...step,
    tone: resolveHierarchyTone(step.key, activeType),
  }))
})

const sheetSubtitle = computed(() => (
  canAssignMemberPermissions.value
    ? `Select an existing student from ${candidateScopeLabel.value.toLowerCase()} and optionally assign ${managedUnitType.value || 'governance'} permissions.`
    : `Select an existing student from ${candidateScopeLabel.value.toLowerCase()}. Permission grants are read-only for your account.`
))

const sheetSearchPlaceholder = computed(() => `Search ${candidateScopeLabel.value.toLowerCase()}`)

const permissionsTitle = computed(() => `${managedUnitType.value || 'Governance'} Permissions`)

watch(
  [() => sgLoading.value, () => sgError.value],
  () => {
    if (sgLoading.value) return
    if (sgError.value) {
      loadError.value = sgError.value
      isLoading.value = false
    }
  },
  { immediate: true }
)

watch(
  [apiBaseUrl, () => sgLoading.value, () => route.query?.variant, () => route.query?.unit_id],
  async ([url]) => {
    if (!url || sgLoading.value) return
    await loadUnit(url)
  },
  { immediate: true }
)

watch(
  [() => memberDraft.value.searchQuery, isCandidateSearchOpen, selectedStudent],
  ([query, open, selected]) => {
    clearTimeout(candidateTimer)
    if (!open || selected) return
    candidateTimer = setTimeout(() => searchCandidates(query), 200)
  }
)

function resolveHierarchyTone(stepType, activeType) {
  if (!activeType) return 'muted'
  if (stepType === activeType) return 'current'

  if (
    (activeType === 'SG' && stepType === 'SSG')
    || (activeType === 'ORG' && (stepType === 'SSG' || stepType === 'SG'))
  ) {
    return 'upstream'
  }

  if (
    (activeType === 'SSG' && (stepType === 'SG' || stepType === 'ORG'))
    || (activeType === 'SG' && stepType === 'ORG')
  ) {
    return 'downstream'
  }

  return 'muted'
}

function applyManagedUnit(detail = null) {
  managedUnit.value = detail && typeof detail === 'object' ? { ...detail } : null
  governanceUnitId.value = Number(detail?.id || null)
  members.value = Array.isArray(detail?.members)
    ? detail.members.map(mapGovernanceMemberToCouncilMember)
    : []
}

async function loadUnit(url) {
  if (props.preview) {
    const previewUnit = previewBundle.value?.activeUnit || null
    governanceUnitId.value = Number(previewUnit?.id || null)
    managedUnit.value = previewUnit ? {
      ...previewUnit,
      members: Array.isArray(previewBundle.value?.members) ? previewBundle.value.members : [],
    } : null
    members.value = Array.isArray(previewBundle.value?.members)
      ? previewBundle.value.members.map((member) => ({ ...member }))
      : []
    isLoading.value = false
    return
  }

  isLoading.value = true
  loadError.value = ''
  const token = localStorage.getItem('aura_token') || ''

  try {
    const routeUnitId = Number(route.query?.unit_id) || null

    if (routeUnitId) {
      const detail = await getGovernanceUnitDetail(url, token, routeUnitId)
      applyManagedUnit(detail)
      return
    }

    const access = await getGovernanceAccess(url, token)
    const parentUnit = resolvePreferredGovernanceUnit(access, {
      requiredPermissionCode: 'manage_members',
    })

    if (!parentUnit) {
      loadError.value = 'No governance unit with member management access was found.'
      return
    }

    const childTypeMap = { SSG: 'SG', SG: 'ORG' }
    const childUnitType = childTypeMap[parentUnit.unit_type]

    if (!childUnitType) {
      loadError.value = 'Please select a specific unit from the Governance Admin panel to manage its members.'
      return
    }

    const childUnits = await getGovernanceUnits(url, token, {
      unit_type: childUnitType,
      parent_unit_id: parentUnit.governance_unit_id,
    })

    if (!childUnits.length) {
      loadError.value = `No ${childUnitType} units were found under your governance unit. Create one first.`
      return
    }

    const targetUnit = childUnits[0]
    const detail = await getGovernanceUnitDetail(url, token, targetUnit.id)
    applyManagedUnit(detail)
  } catch (error) {
    loadError.value = error?.message || 'Unable to load members.'
  } finally {
    isLoading.value = false
  }
}

async function reload() {
  if (apiBaseUrl.value) await loadUnit(apiBaseUrl.value)
}

function goBack() {
  if (props.preview) {
    router.push(withPreservedGovernancePreviewQuery(route, '/exposed/governance'))
    return
  }
  router.push('/governance')
}

function resetDraft() {
  memberDraft.value = { ...createEmptyCouncilMemberDraft(), searchQuery: '', selectedStudent: null }
  editingMemberId.value = null
  showPermissions.value = false
  isCandidateSearchOpen.value = false
  candidateResults.value = []
}

function openAddSheet() {
  if (!canManageMembers.value) return
  resetDraft()
  isSheetOpen.value = true
}

function closeSheet() {
  isSheetOpen.value = false
  resetDraft()
}

function openMemberDetail(member) {
  detailMember.value = member
  isDetailOpen.value = true
}

function closeDetail() {
  isDetailOpen.value = false
  detailMember.value = null
}

function startEditing(member) {
  closeDetail()
  resetDraft()
  editingMemberId.value = member.id
  memberDraft.value.studentId = member.userId
  memberDraft.value.position = member.position || ''
  memberDraft.value.permissionIds = [...(member.permissionIds || [])]
  memberDraft.value.searchQuery = member.fullName
  memberDraft.value.selectedStudent = {
    userId: member.userId,
    fullName: member.fullName,
    studentId: member.studentId,
  }
  showPermissions.value = canAssignMemberPermissions.value && permissionCatalog.value.length > 0
  isSheetOpen.value = true
}

function selectCandidate(candidate) {
  memberDraft.value.studentId = Number(candidate.userId)
  memberDraft.value.searchQuery = candidate.fullName
  memberDraft.value.selectedStudent = candidate
  isCandidateSearchOpen.value = false
  candidateResults.value = [candidate]
}

function togglePermission(id) {
  const next = new Set(memberDraft.value.permissionIds)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  memberDraft.value.permissionIds = [...next]
}

function updateCandidateQuery(value) {
  memberDraft.value.searchQuery = value
  isCandidateSearchOpen.value = true
}

async function searchCandidates(query) {
  if (props.preview) {
    const needle = String(query || '').trim().toLowerCase()
    candidateResults.value = buildPreviewCandidateResults(needle).filter((candidate) => (
      !members.value.some((member) => member.userId === candidate.userId)
    ))
    return
  }

  if (!apiBaseUrl.value || !governanceUnitId.value) return

  try {
    const token = localStorage.getItem('aura_token') || ''
    const results = await searchGovernanceStudentCandidates(apiBaseUrl.value, token, {
      q: query || null,
      governance_unit_id: governanceUnitId.value,
      limit: 12,
    })
    candidateResults.value = results
      .map(mapGovernanceStudentCandidateToCouncilCandidate)
      .filter((candidate) => !candidate.isCurrentGovernanceMember)
      .filter((candidate) => !members.value.some((member) => member.userId === candidate.userId))
  } catch {
    candidateResults.value = []
  }
}

async function handleSubmit() {
  if (submitDisabled.value) return

  if (canAssignMemberPermissions.value && !showPermissions.value && permissionCatalog.value.length) {
    showPermissions.value = true
    return
  }

  const nextPermissionIds = canAssignMemberPermissions.value ? [...memberDraft.value.permissionIds] : []

  if (props.preview) {
    const nextMember = {
      id: editingMemberId.value || resolveNextPreviewMemberId(),
      userId: Number(selectedStudent.value?.userId),
      studentId: String(selectedStudent.value?.studentId || ''),
      fullName: selectedStudent.value?.fullName || 'Student',
      position: memberDraft.value.position.trim(),
      permissionIds: nextPermissionIds,
      isActive: true,
    }

    members.value = editingMemberId.value
      ? members.value.map((member) => (
        Number(member.id) === Number(editingMemberId.value) ? nextMember : member
      ))
      : [nextMember, ...members.value]

    closeSheet()
    return
  }

  isSaving.value = true
  const token = localStorage.getItem('aura_token') || ''
  const payload = {
    user_id: Number(memberDraft.value.studentId),
    position_title: memberDraft.value.position.trim(),
  }

  if (canAssignMemberPermissions.value) {
    payload.permission_codes = mapUiPermissionIdsToBackend(memberDraft.value.permissionIds)
  }

  try {
    if (editingMemberId.value) {
      await updateGovernanceMember(apiBaseUrl.value, token, editingMemberId.value, payload)
    } else {
      await assignGovernanceMember(apiBaseUrl.value, token, governanceUnitId.value, payload)
    }
    closeSheet()
    await reload()
  } catch (error) {
    loadError.value = error?.message || 'Unable to save member.'
  } finally {
    isSaving.value = false
  }
}

async function handleDelete() {
  if (props.preview) {
    members.value = members.value.filter((member) => Number(member.id) !== Number(editingMemberId.value))
    closeSheet()
    return
  }

  if (!editingMemberId.value || isDeleting.value) return
  isDeleting.value = true

  try {
    const token = localStorage.getItem('aura_token') || ''
    await deleteGovernanceMember(apiBaseUrl.value, token, editingMemberId.value)
    closeSheet()
    await reload()
  } catch (error) {
    loadError.value = error?.message || 'Unable to delete member.'
  } finally {
    isDeleting.value = false
  }
}

async function handleDeleteDetail() {
  if (props.preview) {
    members.value = members.value.filter((member) => Number(member.id) !== Number(detailMember.value?.id))
    closeDetail()
    return
  }

  if (!detailMember.value?.id || isDeleting.value) return
  isDeleting.value = true

  try {
    const token = localStorage.getItem('aura_token') || ''
    await deleteGovernanceMember(apiBaseUrl.value, token, detailMember.value.id)
    closeDetail()
    await reload()
  } catch (error) {
    loadError.value = error?.message || 'Unable to delete member.'
  } finally {
    isDeleting.value = false
  }
}

function buildPreviewCandidateResults(query = '') {
  const previewStudents = Array.isArray(previewBundle.value?.students) ? previewBundle.value.students : []
  return previewStudents
    .map((student) => ({
      id: Number(student.id),
      userId: Number(student.id),
      studentId: String(student.student_profile?.student_id || student.id || ''),
      fullName: [student.first_name, student.last_name].filter(Boolean).join(' ').trim() || student.email || 'Student',
      programName: student.student_profile?.program_name || '',
      departmentName: student.student_profile?.department_name || '',
      email: student.email || '',
      searchText: [
        student.student_profile?.student_id,
        student.first_name,
        student.last_name,
        student.email,
        student.student_profile?.program_name,
        student.student_profile?.department_name,
      ].filter(Boolean).join(' ').toLowerCase(),
    }))
    .filter((candidate) => !query || candidate.searchText.includes(query))
}

function resolveNextPreviewMemberId() {
  return Math.max(0, ...members.value.map((member) => Number(member.id) || 0)) + 1
}

function buildInitials(name = '') {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return 'GM'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0] || ''}${parts[parts.length - 1][0] || ''}`.toUpperCase()
}

function memberPermissionPreview(member = {}) {
  return (member.permissionIds || [])
    .map((id) => formatGovernancePermissionLabel(id))
    .filter(Boolean)
    .slice(0, 3)
}

function memberPermissionOverflowCount(member = {}) {
  const count = (member.permissionIds || []).filter(Boolean).length
  return Math.max(0, count - 3)
}

function permissionCountLabel(member = {}) {
  const count = (member.permissionIds || []).filter(Boolean).length
  return count === 0 ? 'No permission grants' : `${count} permission${count === 1 ? '' : 's'}`
}

onBeforeUnmount(() => clearTimeout(candidateTimer))
</script>

<style scoped>
.sg-members-page {
  min-height: 100vh;
  padding: 28px 22px 110px;
  display: grid;
  gap: 18px;
}

.sg-members-hero,
.sg-members-panel,
.sg-members-toolbar,
.sg-members-list-shell,
.sg-members-state,
.sg-sheet,
.sg-detail {
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, rgba(15, 23, 42, 0.08));
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.95) 100%);
  box-shadow: 0 20px 42px rgba(15, 23, 42, 0.06);
}

.sg-members-hero {
  position: relative;
  overflow: hidden;
  border-radius: 30px;
  padding: 22px;
  display: grid;
  gap: 18px;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-primary) 16%, transparent), transparent 42%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.96) 100%);
}

.sg-members-hero__top,
.sg-members-hero__body,
.sg-members-panel__header,
.sg-members-toolbar,
.sg-members-list-shell__header,
.sg-member-card__top,
.sg-detail__header,
.sg-detail__actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.sg-members-back {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.86);
  color: var(--color-text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: inset 0 0 0 1px rgba(226, 232, 240, 0.88);
}

.sg-members-hero__eyebrow,
.sg-members-panel__eyebrow,
.sg-members-fact__label,
.sg-detail__label {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.sg-members-hero__body {
  flex-wrap: wrap;
}

.sg-members-hero__copy {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 12px;
}

.sg-members-hero__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: clamp(28px, 7vw, 38px);
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
}

.sg-members-hero__description,
.sg-members-note,
.sg-members-hierarchy__caption,
.sg-members-fact__caption,
.sg-detail__subtitle {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.sg-members-hero__chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.sg-members-chip,
.sg-members-list-shell__badge,
.sg-member-card__permission,
.sg-detail__permission {
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.sg-members-chip,
.sg-members-list-shell__badge {
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
}

.sg-members-chip--muted {
  background: rgba(148, 163, 184, 0.14);
  color: #475569;
}

.sg-members-overview {
  display: grid;
  gap: 14px;
}

.sg-members-panel {
  border-radius: 28px;
  padding: 20px;
  display: grid;
  gap: 18px;
}

.sg-members-panel__title,
.sg-members-list-shell__title,
.sg-detail__title {
  margin: 6px 0 0;
  color: var(--color-text-primary);
  font-size: clamp(20px, 5vw, 24px);
  line-height: 1.08;
  letter-spacing: -0.04em;
  font-weight: 800;
}

.sg-members-panel__icon {
  color: color-mix(in srgb, var(--color-primary-dark) 70%, #334155);
  flex-shrink: 0;
}

.sg-members-hierarchy {
  display: grid;
  gap: 12px;
}

.sg-members-hierarchy__item {
  border-radius: 22px;
  padding: 16px;
  border: 1px solid rgba(226, 232, 240, 0.88);
  background: rgba(255, 255, 255, 0.82);
  display: grid;
  gap: 8px;
}

.sg-members-hierarchy__item--current {
  border-color: color-mix(in srgb, var(--color-primary) 28%, rgba(226, 232, 240, 0.88));
  background: color-mix(in srgb, var(--color-primary) 10%, rgba(255, 255, 255, 0.96));
}

.sg-members-hierarchy__item--upstream {
  background: rgba(241, 245, 249, 0.9);
}

.sg-members-hierarchy__item--downstream {
  background: rgba(248, 250, 252, 0.92);
}

.sg-members-hierarchy__tag {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.sg-members-hierarchy__name,
.sg-members-fact__value {
  color: var(--color-text-primary);
  font-size: 16px;
  line-height: 1.2;
  letter-spacing: -0.03em;
  font-weight: 800;
}

.sg-members-facts {
  display: grid;
  gap: 12px;
}

.sg-members-fact {
  border-radius: 20px;
  padding: 15px 16px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(226, 232, 240, 0.88);
  display: grid;
  gap: 8px;
}

.sg-members-toolbar,
.sg-members-list-shell,
.sg-members-state {
  border-radius: 28px;
  padding: 18px 20px;
}

.sg-members-toolbar {
  align-items: end;
}

.sg-members-search {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 10px;
}

.sg-members-search__label {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.sg-members-search__shell {
  min-height: 52px;
  border-radius: 20px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(226, 232, 240, 0.92);
}

.sg-members-search__icon {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.sg-members-search__input {
  flex: 1;
  min-width: 0;
  border: none;
  background: transparent;
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 700;
  outline: none;
}

.sg-members-search__input::placeholder {
  color: var(--color-text-muted);
  font-weight: 600;
}

.sg-members-action {
  min-height: 52px;
  padding: 0 18px;
  border: none;
  border-radius: 18px;
  background: var(--color-nav);
  color: var(--color-nav-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.18s ease, opacity 0.18s ease;
}

.sg-members-action:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px rgba(15, 23, 42, 0.14);
}

.sg-members-action:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.sg-members-note {
  padding: 0 4px;
}

.sg-members-list-shell {
  display: grid;
  gap: 18px;
}

.sg-member-list {
  display: grid;
  gap: 12px;
}

.sg-member-card {
  border-radius: 24px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(226, 232, 240, 0.92);
  display: flex;
  gap: 14px;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.sg-member-card:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-primary) 18%, rgba(226, 232, 240, 0.92));
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.08);
}

.sg-member-card__avatar,
.sg-detail__avatar {
  width: 48px;
  height: 48px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--color-primary) 16%, rgba(255, 255, 255, 0.96));
  color: var(--color-primary-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.06em;
  flex-shrink: 0;
}

.sg-member-card__body,
.sg-member-card__heading {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 8px;
}

.sg-member-card__name {
  color: var(--color-text-primary);
  font-size: 15px;
  line-height: 1.35;
  font-weight: 800;
}

.sg-member-card__position {
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.45;
  font-weight: 700;
}

.sg-member-card__edit {
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.96);
  color: var(--color-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}

.sg-member-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 700;
}

.sg-member-card__permissions,
.sg-detail__permissions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sg-member-card__permission,
.sg-detail__permission {
  background: color-mix(in srgb, var(--color-primary) 12%, rgba(255, 255, 255, 0.96));
  color: var(--color-primary-dark);
}

.sg-member-card__permission--muted,
.sg-detail__permission--muted {
  background: rgba(148, 163, 184, 0.14);
  color: #475569;
}

.sg-members-empty,
.sg-members-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 14px;
}

.sg-members-state--error {
  color: #b91c1c;
}

.sg-sheet-backdrop {
  position: fixed;
  inset: 0;
  z-index: 900;
  background: rgba(15, 23, 42, 0.38);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  backdrop-filter: blur(6px);
}

.sg-sheet {
  width: min(100%, 560px);
  max-height: 88vh;
  overflow-y: auto;
  border-radius: 28px 28px 0 0;
  padding: 20px;
}

.sg-sheet--detail {
  width: min(100%, 520px);
}

.sg-sheet__content {
  min-height: 0;
}

.sg-detail {
  border-radius: 28px 28px 0 0;
  padding: 22px;
  display: grid;
  gap: 18px;
}

.sg-detail__identity {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 14px;
}

.sg-detail__close {
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.96);
  color: var(--color-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}

.sg-detail__grid {
  display: grid;
  gap: 12px;
}

.sg-detail__field {
  display: grid;
  gap: 8px;
}

.sg-detail__field--wide {
  grid-column: 1 / -1;
}

.sg-detail__value {
  min-height: 50px;
  border-radius: 18px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(226, 232, 240, 0.92);
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 700;
  line-height: 1.5;
}

.sg-detail__delete {
  min-height: 52px;
  padding: 0 18px;
  border: none;
  border-radius: 18px;
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.sg-detail__delete:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.sg-sheet-enter-active,
.sg-sheet-leave-active {
  transition: opacity 0.22s ease;
}

.sg-sheet-enter-from,
.sg-sheet-leave-to {
  opacity: 0;
}

.dashboard-enter {
  opacity: 0;
  transform: translateY(16px);
  animation: sg-members-fade-up 0.48s ease forwards;
}

.dashboard-enter--1 { animation-delay: 0ms; }
.dashboard-enter--2 { animation-delay: 70ms; }
.dashboard-enter--3 { animation-delay: 140ms; }
.dashboard-enter--4 { animation-delay: 210ms; }

@keyframes sg-members-fade-up {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (min-width: 768px) {
  .sg-members-page {
    padding: 34px 34px 128px;
    gap: 20px;
  }

  .sg-members-overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sg-members-hierarchy {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .sg-members-facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sg-detail__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .sg-members-page {
    padding-inline: 18px;
  }

  .sg-members-toolbar,
  .sg-members-list-shell__header,
  .sg-detail__actions {
    flex-direction: column;
    align-items: stretch;
  }

  .sg-members-action,
  .sg-detail__delete {
    width: 100%;
  }

  .sg-member-card {
    flex-direction: column;
  }

  .sg-member-card__top {
    align-items: center;
  }
}

@media (prefers-reduced-motion: reduce) {
  .dashboard-enter,
  .sg-members-action,
  .sg-member-card,
  .sg-sheet-enter-active,
  .sg-sheet-leave-active {
    animation: none;
    transition: none;
  }
}
</style>
