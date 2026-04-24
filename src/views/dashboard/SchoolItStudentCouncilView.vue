<template>
  <section class="student-council-view">
    <div class="student-council-view__shell">
      <SchoolItTopHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="activeSchoolSettings?.school_name || activeUser?.school_name || ''"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <div class="student-council-view__body">
        <template v-if="isLoadingCouncilState">
          <div class="student-council-view__dashboard dashboard-enter dashboard-enter--2">
            <h1 class="student-council-view__dashboard-title">{{ loadingTitle }}</h1>

            <section class="student-council-view__dashboard-top dashboard-enter dashboard-enter--3">
              <div class="student-council-view__dashboard-search student-council-view__dashboard-search--loading" />
              <div class="student-council-view__dashboard-actions">
                <div class="student-council-view__dashboard-secondary student-council-view__dashboard-secondary--loading" />
                <div class="student-council-view__dashboard-secondary student-council-view__dashboard-secondary--loading" />
              </div>
            </section>

            <section class="student-council-view__dashboard-card dashboard-enter dashboard-enter--4">
              <div class="student-council-view__dashboard-card-header">
                <h2 class="student-council-view__dashboard-card-title">{{ loadingMembersHeading }}</h2>
              </div>

              <div class="student-council-view__member-list">
                <div class="student-council-view__member-row student-council-view__member-row--loading" />
                <div class="student-council-view__member-row student-council-view__member-row--loading" />
              </div>
            </section>
          </div>
        </template>

        <template v-else-if="showDashboard">
          <div class="student-council-view__dashboard dashboard-enter dashboard-enter--2">
            <h1 class="student-council-view__dashboard-title">{{ dashboardTitle }}</h1>

            <section class="student-council-view__dashboard-top dashboard-enter dashboard-enter--3">
              <div class="student-council-view__dashboard-search">
                <input
                  v-model="dashboardSearchQuery"
                  v-bind="officerSearchInputAttrs"
                  type="text"
                  class="student-council-view__dashboard-search-input"
                  placeholder="Search officers"
                >
                <button class="student-council-view__dashboard-search-icon" type="button" aria-label="Search officers">
                  <Search :size="18" />
                </button>
              </div>

              <div class="student-council-view__dashboard-actions">
                <button class="student-council-view__dashboard-secondary" type="button" @click="openCouncilSheet">
                  <SquarePen :size="16" :stroke-width="2.2" />
                  <span>Edit Student Council</span>
                </button>

                <button class="student-council-view__dashboard-secondary" type="button" @click="openOfficerSheet">
                  <SquarePlus :size="16" :stroke-width="2.2" />
                  <span>Add Officer</span>
                </button>
              </div>
            </section>

            <section class="student-council-view__dashboard-card dashboard-enter dashboard-enter--4">
              <div class="student-council-view__dashboard-card-header">
                <h2 class="student-council-view__dashboard-card-title">{{ membersHeading }}</h2>
              </div>

              <div class="student-council-view__member-list">
                <article
                  v-for="member in filteredCouncilMembers"
                  :key="member.id"
                  class="student-council-view__member-row"
                  role="button"
                  tabindex="0"
                  :aria-label="`View ${member.fullName}`"
                  @click="openMemberDetail(member)"
                  @keydown.enter.prevent="openMemberDetail(member)"
                  @keydown.space.prevent="openMemberDetail(member)"
                >
                  <span class="student-council-view__member-id">{{ member.studentId }}</span>
                  <div class="student-council-view__member-copy">
                    <span class="student-council-view__member-name">{{ member.fullName }}</span>
                    <span class="student-council-view__member-position">{{ member.position }}</span>
                  </div>
                  <button
                    class="student-council-view__member-edit"
                    type="button"
                    :aria-label="`Edit ${member.fullName}`"
                    @click.stop="startEditingMember(member)"
                  >
                    <SquarePen :size="17" />
                  </button>
                </article>

                <p v-if="!filteredCouncilMembers.length" class="student-council-view__member-empty">
                  No officers match your search yet.
                </p>
              </div>
            </section>
          </div>
        </template>

        <template v-else>
          <div class="student-council-view__stage-shell">
            <article class="student-council-view__stage-frame dashboard-enter dashboard-enter--2">
              <div class="student-council-view__stage-pane">
                <Transition name="student-council-stage" mode="out-in">
                  <div :key="currentPrimaryStage" class="student-council-view__stage-content">
                    <section
                      v-if="currentPrimaryStage === 'unavailable'"
                      class="student-council-view__unavailable"
                    >
                      <h2 class="student-council-view__unavailable-title">Student Council</h2>
                      <p class="student-council-view__unavailable-copy">
                        {{ stageMessage || 'Student Council data is unavailable right now.' }}
                      </p>
                      <button
                        class="student-council-view__unavailable-action"
                        type="button"
                        @click="retryCouncilLoad"
                      >
                        Try Again
                      </button>
                    </section>

                    <template v-else-if="currentPrimaryStage === 'setup'">
                      <div class="student-council-view__hierarchy-strip" aria-label="Governance hierarchy">
                        <span class="student-council-view__hierarchy-step student-council-view__hierarchy-step--active">SSG</span>
                        <span class="student-council-view__hierarchy-step">SG</span>
                        <span class="student-council-view__hierarchy-step">ORG</span>
                      </div>

                      <StudentCouncilSetupStage
                        compact
                        :draft="councilDraft"
                        eyebrow="Campus Level"
                        title="SSG"
                        description="Parent governance unit."
                        acronym-label="Acronym"
                        acronym-placeholder="e.g. SSG"
                        name-label="Name"
                        name-placeholder="e.g. Supreme Student Government"
                        description-label="Notes (optional)"
                        description-placeholder="Short campus role"
                        :submit-label="isSavingCouncil ? 'Creating SSG...' : 'Create SSG'"
                        :submit-disabled="isSavingCouncil || !canSubmitCouncilDraft(councilDraft)"
                        @update:draft="councilDraft = $event"
                        @submit="handleCreateCouncil"
                      />
                    </template>

                    <StudentCouncilMemberStage
                      v-else
                      title="Add Member"
                      :search-query="memberDraft.searchQuery"
                      :selected-student="selectedStudent"
                      :position="memberDraft.position"
                      :filtered-students="candidateResults"
                      :search-expanded="isCandidateSearchOpen && !selectedStudent"
                      :show-permissions="showPermissions"
                      :permission-catalog="permissionCatalog"
                      :selected-permission-ids="memberDraft.permissionIds"
                      :submit-label="memberSubmitLabel"
                      :submit-disabled="memberSubmitDisabled"
                      @focus-search="handleCandidateSearchFocus"
                      @select-student="selectCandidate"
                      @submit="handleMemberSubmit"
                      @toggle-permission="togglePermission"
                      @update:position="memberDraft.position = $event"
                      @update:searchQuery="updateCandidateQuery"
                    />
                  </div>
                </Transition>
              </div>
            </article>

            <p
              v-if="stageMessage"
              class="student-council-view__status"
              :class="{ 'student-council-view__status--error': stageError }"
            >
              {{ stageMessage }}
            </p>
          </div>
        </template>
      </div>
    </div>

    <Transition name="student-council-sheet">
      <div
        v-if="isOfficerSheetOpen"
        class="student-council-view__sheet-backdrop"
        @click.self="closeOfficerSheet"
      >
        <div class="student-council-view__sheet">
          <StudentCouncilMemberStage
            class="student-council-view__sheet-member-stage"
            :title="editingMemberId ? 'Edit Member' : 'Add Member'"
            :search-query="memberDraft.searchQuery"
            :selected-student="selectedStudent"
            :position="memberDraft.position"
            :filtered-students="candidateResults"
            :search-expanded="isCandidateSearchOpen && !selectedStudent"
            :show-permissions="showPermissions"
            :permission-catalog="permissionCatalog"
            :selected-permission-ids="memberDraft.permissionIds"
            :submit-label="memberSubmitLabel"
            :submit-disabled="memberSubmitDisabled"
            :is-editing="Boolean(editingMemberId)"
            :show-delete="Boolean(editingMemberId)"
            :delete-disabled="isDeletingMember || isSavingMember"
            delete-label="Delete member"
            show-close
            @cancel="closeOfficerSheet"
            @delete="handleDeleteEditingMember"
            @focus-search="handleCandidateSearchFocus"
            @select-student="selectCandidate"
            @submit="handleMemberSubmit"
            @toggle-permission="togglePermission"
            @update:position="memberDraft.position = $event"
            @update:searchQuery="updateCandidateQuery"
          />
        </div>
      </div>
    </Transition>

    <Transition name="student-council-sheet">
      <div
        v-if="isMemberDetailOpen && selectedMemberDetail"
        class="student-council-view__sheet-backdrop"
        @click.self="closeMemberDetail"
      >
        <div class="student-council-view__sheet student-council-view__sheet--detail">
          <section class="student-council-view__member-detail">
            <div class="student-council-view__member-detail-header">
              <h2 class="student-council-view__member-detail-title">SSG Member</h2>
              <button
                class="student-council-view__member-detail-close"
                type="button"
                aria-label="Close member details"
                @click="closeMemberDetail"
              >
                <X :size="18" />
              </button>
            </div>

            <div class="student-council-view__member-detail-field">
              <span class="student-council-view__member-detail-label">Name</span>
              <div class="student-council-view__member-detail-value">{{ selectedMemberDetail.fullName }}</div>
            </div>

            <div class="student-council-view__member-detail-field">
              <span class="student-council-view__member-detail-label">ID Number</span>
              <div class="student-council-view__member-detail-value">{{ selectedMemberDetail.studentId }}</div>
            </div>

            <div class="student-council-view__member-detail-field">
              <span class="student-council-view__member-detail-label">Position</span>
              <div class="student-council-view__member-detail-value">{{ selectedMemberDetail.position }}</div>
            </div>

            <div class="student-council-view__member-detail-field">
              <span class="student-council-view__member-detail-label">Permissions</span>
              <div class="student-council-view__member-detail-permissions">
                <span
                  v-for="permissionLabel in selectedMemberPermissionLabels"
                  :key="permissionLabel"
                  class="student-council-view__member-detail-permission"
                >
                  {{ permissionLabel }}
                </span>
                <span
                  v-if="!selectedMemberPermissionLabels.length"
                  class="student-council-view__member-detail-permission student-council-view__member-detail-permission--empty"
                >
                  No permissions assigned
                </span>
              </div>
            </div>

            <div class="student-council-view__member-detail-actions">
              <button class="student-council-view__dashboard-secondary" type="button" @click="startEditingMember(selectedMemberDetail)">
                <SquarePen :size="16" :stroke-width="2.2" />
                <span>Edit Member</span>
              </button>

              <button
                class="student-council-view__member-delete"
                type="button"
                :disabled="isDeletingMember"
                @click="handleDeleteMember"
              >
                {{ isDeletingMember ? 'Deleting Member...' : 'Delete Member' }}
              </button>
            </div>
          </section>
        </div>
      </div>
    </Transition>

    <Transition name="student-council-sheet">
      <div
        v-if="isCouncilSheetOpen"
        class="student-council-view__sheet-backdrop"
        @click.self="closeCouncilSheet"
      >
        <div class="student-council-view__sheet">
          <StudentCouncilSetupStage
            class="student-council-view__sheet-setup-stage"
            compact
            :draft="councilSheetDraft"
            eyebrow="Campus Level"
            title="SSG"
            description="Parent governance unit."
            acronym-label="Acronym"
            acronym-placeholder="e.g. SSG"
            name-label="Name"
            name-placeholder="e.g. Supreme Student Government"
            description-label="Notes (optional)"
            description-placeholder="Short campus role"
            :is-editing="hasCouncil"
            :submit-label="councilSheetSubmitLabel"
            :submit-disabled="councilSheetSubmitDisabled"
            :show-delete="hasCouncil"
            :delete-label="councilSheetDeleteLabel"
            :delete-disabled="councilSheetDeleteDisabled"
            @update:draft="councilSheetDraft = $event"
            @submit="handleCouncilSheetSubmit"
            @delete="handleCouncilSheetDelete"
          />
        </div>
      </div>
    </Transition>
  </section>
</template>

<script setup>
import {
  computed,
  onBeforeUnmount,
  ref,
  watch,
} from 'vue'
import { useRouter } from 'vue-router'
import { Search, SquarePen, SquarePlus, X } from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import StudentCouncilMemberStage from '@/components/council/StudentCouncilMemberStage.vue'
import StudentCouncilSetupStage from '@/components/council/StudentCouncilSetupStage.vue'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSchoolItWorkspaceData } from '@/composables/useSchoolItWorkspaceData.js'
import { createSearchFieldAttrs } from '@/services/searchFieldAttrs.js'
import {
  BackendApiError,
  assignGovernanceMember,
  createGovernanceUnit,
  deleteGovernanceMember,
  deleteGovernanceUnit,
  getCampusSsgSetup,
  searchGovernanceStudentCandidates,
  updateGovernanceMember,
  updateGovernanceUnit,
} from '@/services/backendApi.js'
import {
  createEmptyCouncilDraft,
  createEmptyCouncilMemberDraft,
  createStudentCouncilStorageKey,
  defaultStudentCouncilPermissionCatalog,
  buildStudentCouncilCandidates,
  loadStudentCouncilState,
  formatGovernancePermissionLabel,
  mapGovernanceMemberToCouncilMember,
  mapGovernanceStudentCandidateToCouncilCandidate,
  mapGovernanceUnitToCouncilRecord,
  mapUiPermissionIdsToBackend,
  normalizePermissionCatalog,
  resolveStudentCouncilAcronym,
  saveStudentCouncilState,
} from '@/services/studentCouncilManagement.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()
const officerSearchInputAttrs = createSearchFieldAttrs('school-it-officer-search')
const { currentUser, schoolSettings, apiBaseUrl } = useDashboardSession()
const {
  campusSsgSetup: sharedCampusSsgSetup,
  statuses: sharedWorkspaceStatuses,
  setCampusSsgSetupSnapshot,
} = useSchoolItWorkspaceData()
const { logout } = useAuth()

const councilDraft = ref(createEmptyCouncilDraft())
const councilSheetDraft = ref(createEmptyCouncilDraft())
const memberDraft = ref({
  ...createEmptyCouncilMemberDraft(),
  searchQuery: '',
  selectedStudent: null,
})
const currentCouncil = ref(null)
const councilMembers = ref([])
const candidateResults = ref([])
const isCandidateSearchOpen = ref(false)
const showPermissions = ref(false)
const setupStage = ref('setup')
const isInitialSetupFlow = ref(false)
const stageMessage = ref('')
const stageError = ref(false)
const councilLoadStatus = ref('idle')
const isSavingCouncil = ref(false)
const isUpdatingCouncil = ref(false)
const isDeletingCouncil = ref(false)
const isSavingMember = ref(false)
const isLoadingCouncilState = ref(false)
const dashboardSearchQuery = ref('')
const isOfficerSheetOpen = ref(false)
const isCouncilSheetOpen = ref(false)
const isMemberDetailOpen = ref(false)
const isDeletingMember = ref(false)
const editingMemberId = ref(null)
const selectedMemberDetail = ref(null)

let candidateSearchTimer = null
let councilLoadRequestId = 0

const permissionCatalog = computed(() => normalizePermissionCatalog(defaultStudentCouncilPermissionCatalog))
const activeUser = computed(() => currentUser.value)
const activeSchoolSettings = computed(() => schoolSettings.value)
const schoolId = computed(() => Number(activeUser.value?.school_id ?? activeSchoolSettings.value?.school_id))
const displayName = computed(() => {
  const first = activeUser.value?.first_name || ''
  const middle = activeUser.value?.middle_name || ''
  const last = activeUser.value?.last_name || ''
  return [first, middle, last].filter(Boolean).join(' ') || activeUser.value?.email?.split('@')[0] || 'School IT'
})
const avatarUrl = computed(() => activeUser.value?.avatar_url || '')
const initials = computed(() => buildInitials(displayName.value))
const storageKey = computed(() => createStudentCouncilStorageKey(schoolId.value, props.preview))
const selectedStudent = computed(() => {
  const selectedUserId = Number(memberDraft.value.studentId)
  return candidateResults.value.find((candidate) => candidate.userId === selectedUserId)
    || memberDraft.value.selectedStudent
    || null
})
const hasCouncil = computed(() => Boolean(currentCouncil.value?.id))
const councilAcronym = computed(() => resolveStudentCouncilAcronym(currentCouncil.value))
const hasCouncilAcronym = computed(() => councilAcronym.value.length > 0)
const hasAssignedCouncilMembers = computed(() => (
  councilMembers.value.some((member) => member?.isActive !== false)
))
const previewCandidatePool = computed(() => (
  props.preview
    ? buildStudentCouncilCandidates({
      users: schoolItPreviewData.users,
      programs: schoolItPreviewData.programs,
      departments: schoolItPreviewData.departments,
    })
    : []
))
const currentPrimaryStage = computed(() => {
  if (isInitialSetupFlow.value && setupStage.value === 'member') return 'member'
  if (!props.preview && !hasCouncil.value && ['blocked', 'error'].includes(councilLoadStatus.value)) {
    return 'unavailable'
  }
  if (!hasCouncil.value) return 'setup'
  return 'dashboard'
})
const showDashboard = computed(() => currentPrimaryStage.value === 'dashboard')
const dashboardTitle = computed(() => {
  const acronym = councilAcronym.value
  return acronym ? `${acronym} Management` : 'Acronym Management'
})
const membersHeading = computed(() => {
  const acronym = councilAcronym.value
  return acronym ? `${acronym} Members` : 'Acronym Members'
})
const loadingTitle = computed(() => {
  const acronym = councilAcronym.value
  return acronym ? `${acronym} Management` : 'Acronym Management'
})
const loadingMembersHeading = computed(() => {
  const acronym = councilAcronym.value
  return acronym ? `${acronym} Members` : 'Acronym Members'
})
const candidateSearchQuery = computed(() => memberDraft.value.searchQuery.trim())
const memberSubmitLabel = computed(() => {
  if (isSavingMember.value) return editingMemberId.value ? 'Saving...' : 'Adding Student...'
  if (!showPermissions.value) return 'Continue'
  return editingMemberId.value ? 'Save Student' : 'Add Student'
})
const memberSubmitDisabled = computed(() => {
  const hasStudent = Boolean(selectedStudent.value?.userId)
  const hasPosition = memberDraft.value.position.trim().length > 0
  if (!hasStudent || !hasPosition || isSavingMember.value) return true
  if (!showPermissions.value) return false
  return memberDraft.value.permissionIds.length === 0
})
const councilSheetSubmitLabel = computed(() => {
  if (isUpdatingCouncil.value) return 'Saving Council...'
  if (isSavingCouncil.value) return 'Creating Council...'
  return hasCouncil.value ? 'Save Student Council' : 'Add Student Council'
})
const councilSheetSubmitDisabled = computed(() => {
  if (isSavingCouncil.value || isUpdatingCouncil.value || isDeletingCouncil.value) return true
  return !canSubmitCouncilDraft(councilSheetDraft.value)
})
const councilSheetDeleteLabel = computed(() => {
  if (isDeletingCouncil.value) return 'Deleting Student Council...'
  return 'Delete Student Council'
})
const councilSheetDeleteDisabled = computed(() => (
  !hasCouncil.value
  || isSavingCouncil.value
  || isUpdatingCouncil.value
  || isDeletingCouncil.value
))
const filteredCouncilMembers = computed(() => {
  const query = dashboardSearchQuery.value.trim().toLowerCase()
  if (!query) return councilMembers.value

  return councilMembers.value.filter((member) => [member.studentId, member.fullName, member.position]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
    .includes(query))
})
const selectedMemberPermissionLabels = computed(() => {
  const member = selectedMemberDetail.value
  if (!member) return []

  return (Array.isArray(member.permissionIds) ? member.permissionIds : [])
    .map((permissionId) => resolvePermissionLabel(permissionId))
    .filter(Boolean)
})

watch(
  [apiBaseUrl, () => activeUser.value?.id, schoolId, () => props.preview],
  async ([resolvedApiBaseUrl, userId, activeSchoolId]) => {
    if (!resolvedApiBaseUrl || !userId || !activeSchoolId) return
    await loadCouncilState(resolvedApiBaseUrl)
  },
  { immediate: true }
)

watch([storageKey, currentCouncil, councilMembers, () => props.preview], () => {
  if (!props.preview) return
  saveStudentCouncilState(storageKey.value, {
    council: currentCouncil.value,
    members: councilMembers.value,
  })
}, { deep: true })

watch(
  [candidateSearchQuery, isCandidateSearchOpen, selectedStudent],
  ([query, open, selected]) => {
    clearCandidateSearchTimer()
    if (!open || selected) {
      if (!selected) candidateResults.value = []
      return
    }

    candidateSearchTimer = setTimeout(() => {
      void fetchCandidateResults(query)
    }, 180)
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  clearCandidateSearchTimer()
})

function applyCouncilSetup(setup) {
  currentCouncil.value = setup?.unit ? mapGovernanceUnitToCouncilRecord(setup.unit) : null
  councilMembers.value = Array.isArray(setup?.unit?.members)
    ? setup.unit.members.map(mapGovernanceMemberToCouncilMember)
    : []
  councilDraft.value = currentCouncil.value
    ? createCouncilDraftFromRecord(currentCouncil.value)
    : createEmptyCouncilDraft()
  setupStage.value = currentCouncil.value?.id ? 'dashboard' : 'setup'
  isInitialSetupFlow.value = false
}

async function fetchLatestCouncilSetup(token) {
  const setup = await getCampusSsgSetup(apiBaseUrl.value, token)
  setCampusSsgSetupSnapshot(setup)
  applyCouncilSetup(setup)
  return setup
}

async function loadCouncilState(resolvedApiBaseUrl) {
  clearStageMessage()
  councilLoadStatus.value = 'loading'
  const requestId = ++councilLoadRequestId
  const sharedSetup = sharedCampusSsgSetup.value?.unit ? sharedCampusSsgSetup.value : null
  const sharedCouncilStatus = sharedWorkspaceStatuses.value?.council || 'idle'

  if (sharedCouncilStatus === 'ready' && sharedSetup?.unit) {
    applyCouncilSetup(sharedSetup)
    councilLoadStatus.value = 'ready'
    isLoadingCouncilState.value = false
  } else {
    isLoadingCouncilState.value = true
  }

  try {
    if (props.preview) {
      const stored = loadStudentCouncilState(storageKey.value)
      if (requestId !== councilLoadRequestId) return
      currentCouncil.value = stored?.council || null
      councilMembers.value = Array.isArray(stored?.members) ? stored.members : []
      councilDraft.value = currentCouncil.value
        ? createCouncilDraftFromRecord(currentCouncil.value)
        : createEmptyCouncilDraft()
      setupStage.value = currentCouncil.value?.id ? 'dashboard' : 'setup'
      isInitialSetupFlow.value = false
      councilLoadStatus.value = currentCouncil.value?.id ? 'ready' : 'absent'
      return
    }

    const token = localStorage.getItem('aura_token') || ''
    const setup = await getCampusSsgSetup(resolvedApiBaseUrl, token)
    if (requestId !== councilLoadRequestId) return
    setCampusSsgSetupSnapshot(setup)
    applyCouncilSetup(setup)
    councilLoadStatus.value = currentCouncil.value?.id ? 'ready' : 'absent'
  } catch (error) {
    if (requestId !== councilLoadRequestId) return
    const isMissingCouncil = error instanceof BackendApiError && error.status === 404

    if (isMissingCouncil && !sharedSetup?.unit) {
      setCampusSsgSetupSnapshot(null)
      applyCouncilSetup(null)
      councilLoadStatus.value = 'absent'
    } else if (sharedSetup?.unit) {
      applyCouncilSetup(sharedSetup)
      councilLoadStatus.value = 'ready'
    } else {
      councilLoadStatus.value = error instanceof BackendApiError && error.status === 403
        ? 'blocked'
        : 'error'
    }

    setStageMessage(error?.message || 'Unable to load Student Council data right now.', true)
  } finally {
    if (requestId !== councilLoadRequestId) return
    isLoadingCouncilState.value = false
  }
}

async function retryCouncilLoad() {
  if (!apiBaseUrl.value || !activeUser.value?.id || !schoolId.value) return
  await loadCouncilState(apiBaseUrl.value)
}

async function fetchCandidateResults(query) {
  if (props.preview) {
    const normalizedQuery = String(query || '').trim().toLowerCase()
    candidateResults.value = previewCandidatePool.value
      .filter((candidate) => !normalizedQuery || candidate.searchText.includes(normalizedQuery))
      .filter((candidate) => !councilMembers.value.some((member) => member.userId === candidate.userId))
      .slice(0, 12)
    return
  }

  if (!apiBaseUrl.value) return

  try {
    const token = localStorage.getItem('aura_token') || ''
    const results = await searchGovernanceStudentCandidates(apiBaseUrl.value, token, {
      q: query || null,
      governance_unit_id: Number(currentCouncil.value?.id) || null,
      limit: 12,
    })

    candidateResults.value = results
      .map(mapGovernanceStudentCandidateToCouncilCandidate)
      .filter((candidate) => !candidate.isCurrentGovernanceMember)
      .filter((candidate) => !councilMembers.value.some((member) => member.userId === candidate.userId))
  } catch (error) {
    candidateResults.value = []
    setStageMessage(error?.message || 'Unable to search students right now.', true)
  }
}

function handleCandidateSearchFocus() {
  isCandidateSearchOpen.value = true
}

function updateCandidateQuery(value) {
  memberDraft.value.searchQuery = value
  isCandidateSearchOpen.value = true
}

function selectCandidate(candidate) {
  memberDraft.value.studentId = Number(candidate.userId)
  memberDraft.value.searchQuery = candidate.fullName
  memberDraft.value.selectedStudent = candidate
  isCandidateSearchOpen.value = false
  candidateResults.value = [candidate]
}

function togglePermission(permissionId) {
  const nextIds = new Set(memberDraft.value.permissionIds)
  if (nextIds.has(permissionId)) nextIds.delete(permissionId)
  else nextIds.add(permissionId)
  memberDraft.value.permissionIds = [...nextIds]
}

async function handleCreateCouncil() {
  if (!canSubmitCouncilDraft(councilDraft.value) || isSavingCouncil.value) return

  clearStageMessage()
  isSavingCouncil.value = true
  const wasExistingCouncil = Boolean(currentCouncil.value?.id)

  try {
    const savedCouncil = await saveInitialCouncilRecord(councilDraft.value)
    currentCouncil.value = savedCouncil
    if (!props.preview) {
      setCampusSsgSetupSnapshot({
        ...(sharedCampusSsgSetup.value || {}),
        unit: {
          ...(sharedCampusSsgSetup.value?.unit || {}),
          id: Number(savedCouncil.id),
          unit_code: savedCouncil.acronym,
          unit_name: savedCouncil.name,
          description: savedCouncil.description || null,
          members: [],
        },
      })
    }
    councilDraft.value = createCouncilDraftFromRecord(savedCouncil)
    resetMemberStage()
    isInitialSetupFlow.value = true
    setupStage.value = 'member'
    setStageMessage(
      wasExistingCouncil
        ? 'Student Council saved. Add the first officer next.'
        : 'Student Council created. Add the first officer next.',
      false
    )
  } catch (error) {
    setStageMessage(error?.message || 'Unable to create the Student Council right now.', true)
  } finally {
    isSavingCouncil.value = false
  }
}

async function handleCouncilSheetSubmit() {
  if (councilSheetSubmitDisabled.value) return

  clearStageMessage()

  if (!hasCouncil.value) {
    isSavingCouncil.value = true

    try {
      const savedCouncil = await saveCouncilRecord(councilSheetDraft.value)
      currentCouncil.value = savedCouncil
      if (!props.preview) {
        setCampusSsgSetupSnapshot({
          ...(sharedCampusSsgSetup.value || {}),
          unit: {
            ...(sharedCampusSsgSetup.value?.unit || {}),
            id: Number(savedCouncil.id),
            unit_code: savedCouncil.acronym,
            unit_name: savedCouncil.name,
            description: savedCouncil.description || null,
            members: [],
          },
        })
      }
      councilDraft.value = createEmptyCouncilDraft()
      closeCouncilSheet()
      resetMemberStage()
      isInitialSetupFlow.value = true
      setupStage.value = 'member'
      setStageMessage('Student Council created. Add the first officer next.', false)
    } catch (error) {
      setStageMessage(error?.message || 'Unable to create the Student Council right now.', true)
    } finally {
      isSavingCouncil.value = false
    }

    return
  }

  isUpdatingCouncil.value = true

  try {
    if (props.preview) {
      currentCouncil.value = {
        ...currentCouncil.value,
        ...normalizeCouncilDraft(councilSheetDraft.value),
      }
    } else {
      const token = localStorage.getItem('aura_token') || ''
      const response = await updateGovernanceUnit(
        apiBaseUrl.value,
        token,
        Number(currentCouncil.value?.id),
        buildGovernanceUnitPayload(councilSheetDraft.value)
      )

      currentCouncil.value = {
        ...currentCouncil.value,
        ...mapGovernanceUnitToCouncilRecord(response),
      }
      setCampusSsgSetupSnapshot({
        ...(sharedCampusSsgSetup.value || {}),
        unit: response,
      })
    }

    closeCouncilSheet()
    setStageMessage('Student Council details updated.', false)
  } catch (error) {
    setStageMessage(error?.message || 'Unable to update the Student Council right now.', true)
  } finally {
    isUpdatingCouncil.value = false
  }
}

async function handleCouncilSheetDelete() {
  if (councilSheetDeleteDisabled.value || !hasCouncil.value) return

  clearStageMessage()
  const confirmed = typeof window === 'undefined'
    ? true
    : window.confirm('Delete this Student Council? This action cannot be undone.')
  if (!confirmed) return

  isDeletingCouncil.value = true

  try {
    if (!props.preview) {
      const token = localStorage.getItem('aura_token') || ''
      const governanceUnitId = Number(currentCouncil.value?.id || sharedCampusSsgSetup.value?.unit?.id)

      if (!Number.isFinite(governanceUnitId)) {
        throw new BackendApiError('Student Council ID is missing, so the delete request could not be sent.', {
          status: 400,
        })
      }

      await deleteGovernanceUnit(apiBaseUrl.value, token, governanceUnitId)
      await waitForCouncilDeletion(token)
      setCampusSsgSetupSnapshot(null)
    }

    currentCouncil.value = null
    councilMembers.value = []
    dashboardSearchQuery.value = ''
    councilDraft.value = createEmptyCouncilDraft()
    councilSheetDraft.value = createEmptyCouncilDraft()
    resetMemberStage()
    closeOfficerSheet()
    closeMemberDetail()
    closeCouncilSheet()
    setupStage.value = 'setup'
    isInitialSetupFlow.value = false
    setStageMessage('Student Council deleted.', false)
    if (!props.preview) {
      await router.replace({ name: 'SchoolItUsers' })
    }
  } catch (error) {
    setStageMessage(error?.message || 'Unable to delete the Student Council right now.', true)
  } finally {
    isDeletingCouncil.value = false
  }
}

async function handleMemberSubmit() {
  if (memberSubmitDisabled.value) return

  clearStageMessage()

  if (!showPermissions.value) {
    showPermissions.value = true
    return
  }

  isSavingMember.value = true

  try {
    const isEditing = Boolean(editingMemberId.value)
    const activeSelectedStudent = selectedStudent.value

    if (props.preview) {
      savePreviewMember(activeSelectedStudent)
    } else {
      await saveRemoteMember(activeSelectedStudent)
    }

    resetMemberStage()
    isOfficerSheetOpen.value = false
    isInitialSetupFlow.value = false
    setupStage.value = 'dashboard'
    setStageMessage(isEditing ? 'Officer updated.' : 'Officer added to the Student Council.', false)
  } catch (error) {
    setStageMessage(error?.message || 'Unable to save this officer right now.', true)
  } finally {
    isSavingMember.value = false
  }
}

function savePreviewMember(activeSelectedStudent) {
  if (editingMemberId.value) {
    const updatedMember = {
      ...councilMembers.value.find((member) => member.id === editingMemberId.value),
      position: memberDraft.value.position.trim(),
      permissionIds: [...memberDraft.value.permissionIds],
    }
    councilMembers.value = councilMembers.value.map((member) => (
      member.id === editingMemberId.value ? updatedMember : member
    ))
    return
  }

  councilMembers.value = [...councilMembers.value, {
    id: Date.now(),
    userId: activeSelectedStudent.userId,
    studentId: activeSelectedStudent.studentId,
    fullName: activeSelectedStudent.fullName,
    position: memberDraft.value.position.trim(),
    permissionIds: [...memberDraft.value.permissionIds],
  }]
}

async function saveRemoteMember(activeSelectedStudent) {
  const token = localStorage.getItem('aura_token') || ''
  const governanceUnitId = Number(currentCouncil.value?.id)
  if (!Number.isFinite(governanceUnitId)) {
    throw new BackendApiError('Student Council ID is missing, so the officer could not be saved.', {
      status: 400,
    })
  }

  const payload = {
    user_id: Number(activeSelectedStudent.userId),
    position_title: memberDraft.value.position.trim(),
    permission_codes: mapUiPermissionIdsToBackend(memberDraft.value.permissionIds),
  }

  try {
    const response = editingMemberId.value
      ? await updateGovernanceMember(apiBaseUrl.value, token, editingMemberId.value, payload)
      : await createGovernanceMemberWithPermissionsFallback(governanceUnitId, token, payload)

    try {
      await fetchLatestCouncilSetup(token)
      return
    } catch {
      // Fall back to the write response if the follow-up refresh is temporarily unavailable.
    }

    const savedMember = mapGovernanceMemberToCouncilMember(response)
    if (editingMemberId.value) {
      councilMembers.value = councilMembers.value.map((member) => (
        member.id === editingMemberId.value ? savedMember : member
      ))
      return
    }

    councilMembers.value = [...councilMembers.value, savedMember]
  } catch (error) {
    await reconcileFailedMemberSave(activeSelectedStudent, token, error)
  }
}

async function createGovernanceMemberWithPermissionsFallback(governanceUnitId, token, payload) {
  const requestedPermissionCodes = Array.isArray(payload?.permission_codes)
    ? payload.permission_codes.filter(Boolean)
    : []

  try {
    const response = await assignGovernanceMember(apiBaseUrl.value, token, governanceUnitId, payload)
    return await finalizeCreatedGovernanceMember(token, response, payload, requestedPermissionCodes)
  } catch (error) {
    const canRetryWithoutPermissions = error instanceof BackendApiError
      && error.status >= 500
      && requestedPermissionCodes.length > 0

    if (!canRetryWithoutPermissions) {
      throw error
    }

    const fallbackResponse = await assignGovernanceMember(apiBaseUrl.value, token, governanceUnitId, {
      user_id: payload.user_id,
      position_title: payload.position_title,
    })

    return await finalizeCreatedGovernanceMember(token, fallbackResponse, payload, requestedPermissionCodes)
  }
}

async function finalizeCreatedGovernanceMember(token, response, payload, requestedPermissionCodes) {
  const createdMemberId = Number(response?.id)
  const hasRequestedPermissions = requestedPermissionCodes.length === 0
    || requestedPermissionCodes.every((permissionCode) => (
      Array.isArray(response?.member_permissions)
        && response.member_permissions.some((permission) => permission?.permission_code === permissionCode)
    ))

  if (!Number.isFinite(createdMemberId)) {
    return response
  }

  if (response?.is_active !== false && hasRequestedPermissions) {
    return response
  }

  return await updateGovernanceMember(apiBaseUrl.value, token, createdMemberId, payload)
}

function openOfficerSheet() {
  clearStageMessage()
  resetMemberStage()
  closeMemberDetail()
  isOfficerSheetOpen.value = true
}

function closeOfficerSheet() {
  resetMemberStage()
  isOfficerSheetOpen.value = false
}

function openCouncilSheet() {
  clearStageMessage()
  councilSheetDraft.value = hasCouncil.value
    ? createCouncilDraftFromRecord(currentCouncil.value)
    : { ...councilDraft.value }
  isCouncilSheetOpen.value = true
}

function closeCouncilSheet() {
  isCouncilSheetOpen.value = false
  councilSheetDraft.value = createEmptyCouncilDraft()
}

function openMemberDetail(member) {
  selectedMemberDetail.value = {
    ...member,
    permissionIds: Array.isArray(member.permissionIds) ? [...member.permissionIds] : [],
  }
  isMemberDetailOpen.value = true
}

function closeMemberDetail() {
  isMemberDetailOpen.value = false
  selectedMemberDetail.value = null
}

function startEditingMember(member) {
  clearStageMessage()
  closeMemberDetail()
  editingMemberId.value = Number(member.id)
  memberDraft.value = {
    studentId: Number(member.userId),
    position: member.position || '',
    permissionIds: [...member.permissionIds],
    searchQuery: member.fullName || '',
    selectedStudent: {
      userId: Number(member.userId),
      fullName: member.fullName,
      studentId: member.studentId,
    },
  }
  showPermissions.value = true
  isCandidateSearchOpen.value = false
  candidateResults.value = [memberDraft.value.selectedStudent]
  isOfficerSheetOpen.value = true
}

async function handleDeleteMember() {
  if (!selectedMemberDetail.value || isDeletingMember.value) return

  await performMemberDeletion(selectedMemberDetail.value)
}

async function handleDeleteEditingMember() {
  if (!editingMemberId.value || isDeletingMember.value) return

  const member = councilMembers.value.find((entry) => Number(entry.id) === Number(editingMemberId.value))
  if (!member) {
    setStageMessage('This officer could not be found anymore.', true)
    return
  }

  await performMemberDeletion(member, { closeOfficer: true })
}

async function performMemberDeletion(member, { closeOfficer = false } = {}) {
  const confirmed = typeof window === 'undefined'
    ? true
    : window.confirm(`Delete ${member.fullName} from the Student Council?`)
  if (!confirmed) return

  isDeletingMember.value = true
  clearStageMessage()

  try {
    if (!props.preview) {
      const token = localStorage.getItem('aura_token') || ''
      await deleteGovernanceMember(apiBaseUrl.value, token, Number(member.id))
      const refreshedSetup = await waitForMemberDeletion(Number(member.userId), token)
      setCampusSsgSetupSnapshot(refreshedSetup)
      applyCouncilSetup(refreshedSetup)
    } else {
      councilMembers.value = councilMembers.value.filter((entry) => Number(entry.id) !== Number(member.id))
    }

    if (closeOfficer) {
      closeOfficerSheet()
    } else {
      closeMemberDetail()
    }
    setStageMessage('Officer deleted.', false)
  } catch (error) {
    setStageMessage(error?.message || 'Unable to delete this officer right now.', true)
  } finally {
    isDeletingMember.value = false
  }
}

function resetMemberStage() {
  editingMemberId.value = null
  memberDraft.value = {
    ...createEmptyCouncilMemberDraft(),
    searchQuery: '',
    selectedStudent: null,
  }
  showPermissions.value = false
  isCandidateSearchOpen.value = false
  candidateResults.value = []
}

function setStageMessage(message, isError = false) {
  stageMessage.value = message
  stageError.value = Boolean(isError)
}

function clearStageMessage() {
  stageMessage.value = ''
  stageError.value = false
}

function clearCandidateSearchTimer() {
  if (!candidateSearchTimer) return
  clearTimeout(candidateSearchTimer)
  candidateSearchTimer = null
}

function resolvePermissionLabel(permissionId) {
  const normalizedPermissionId = String(permissionId || '').trim()
  for (const category of permissionCatalog.value) {
    const match = category.permissions.find((permission) => permission.id === normalizedPermissionId)
    if (match) return match.label
  }
  return formatGovernancePermissionLabel(normalizedPermissionId)
}

function buildInitials(value) {
  const parts = String(value || '').split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return (parts[0]?.slice(0, 2) || 'SI').toUpperCase()
}

function canSubmitCouncilDraft(draft) {
  const normalizedDraft = normalizeCouncilDraft(draft)
  return normalizedDraft.acronym.length >= 2 && normalizedDraft.name.length >= 2
}

function normalizeCouncilDraft(draft) {
  return {
    acronym: String(draft?.acronym || '').trim(),
    name: String(draft?.name || '').trim(),
    description: String(draft?.description || '').trim(),
  }
}

function wait(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

async function waitForCouncilDeletion(token) {
  const verificationAttempts = [0, 450, 900, 1500, 2200]
  let latestSetup = null
  let latestError = null

  for (const delayMs of verificationAttempts) {
    if (delayMs > 0) {
      await wait(delayMs)
    }

    try {
      const setup = await getCampusSsgSetup(apiBaseUrl.value, token)
      latestSetup = setup

      if (!setup?.unit?.id) {
        return
      }
    } catch (error) {
      if (error instanceof BackendApiError && error.status === 404) {
        return
      }

      latestError = error
      if (error instanceof BackendApiError && error.status === 403) {
        throw error
      }
    }
  }

  if (latestError) {
    throw latestError
  }

  throw new BackendApiError('Student Council still exists on the backend after the delete request.', {
    status: 409,
    details: latestSetup,
  })
}

async function waitForMemberDeletion(memberUserId, token) {
  const verificationAttempts = [0, 350, 700, 1200, 1800]
  let latestSetup = null
  let latestError = null

  for (const delayMs of verificationAttempts) {
    if (delayMs > 0) {
      await wait(delayMs)
    }

    try {
      const setup = await getCampusSsgSetup(apiBaseUrl.value, token)
      latestSetup = setup

      const members = Array.isArray(setup?.unit?.members) ? setup.unit.members : []
      const memberStillExists = members.some((entry) => Number(entry?.user?.id ?? entry?.user_id) === memberUserId)
      if (!memberStillExists) {
        return setup
      }
    } catch (error) {
      latestError = error
      if (error instanceof BackendApiError && error.status === 404) {
        return null
      }
      if (error instanceof BackendApiError && error.status === 403) {
        throw error
      }
    }
  }

  if (latestError) {
    throw latestError
  }

  throw new BackendApiError('The backend still reports this officer as active after deletion.', {
    status: 409,
    details: latestSetup,
  })
}

async function reconcileFailedMemberSave(activeSelectedStudent, token, originalError) {
  if (!(originalError instanceof BackendApiError) || originalError.status !== 500) {
    throw originalError
  }

  try {
    const setup = await fetchLatestCouncilSetup(token)
    const members = Array.isArray(setup?.unit?.members) ? setup.unit.members : []
    const duplicateMember = members.find((entry) => Number(entry?.user?.id ?? entry?.user_id) === Number(activeSelectedStudent?.userId))

    if (duplicateMember) {
      throw new BackendApiError(
        `${activeSelectedStudent?.fullName || 'This student'} still appears as an active Student Council member on the backend. Please refresh or wait a moment before adding them again.`,
        {
          status: 409,
          details: setup,
        }
      )
    }
  } catch (refreshError) {
    if (refreshError instanceof BackendApiError && refreshError.status === 409) {
      throw refreshError
    }
  }

  throw originalError
}

function createCouncilDraftFromRecord(council) {
  return {
    acronym: String(council?.acronym || '').trim(),
    name: String(council?.name || '').trim(),
    description: String(council?.description || '').trim(),
  }
}

function buildGovernanceUnitPayload(draft) {
  const normalizedDraft = normalizeCouncilDraft(draft)
  return {
    unit_code: normalizedDraft.acronym,
    unit_name: normalizedDraft.name,
    description: normalizedDraft.description || null,
    unit_type: 'SSG',
    parent_unit_id: null,
    department_id: null,
    program_id: null,
  }
}

async function saveCouncilRecord(draft) {
  const normalizedDraft = normalizeCouncilDraft(draft)

  if (props.preview) {
    return {
      id: Date.now(),
      ...normalizedDraft,
    }
  }

  const token = localStorage.getItem('aura_token') || ''
  const response = await createGovernanceUnit(apiBaseUrl.value, token, buildGovernanceUnitPayload(normalizedDraft))
  return mapGovernanceUnitToCouncilRecord(response)
}

async function saveInitialCouncilRecord(draft) {
  if (!currentCouncil.value?.id || props.preview) {
    return await saveCouncilRecord(draft)
  }

  const token = localStorage.getItem('aura_token') || ''
  const response = await updateGovernanceUnit(
    apiBaseUrl.value,
    token,
    Number(currentCouncil.value.id),
    buildGovernanceUnitPayload(draft)
  )

  return mapGovernanceUnitToCouncilRecord(response)
}

async function handleLogout() {
  await logout()
}
</script>

<style scoped>
.student-council-view{min-height:100vh;padding:30px 28px 120px;font-family:'Manrope',sans-serif;background:var(--color-bg)}
.student-council-view__shell{width:100%;max-width:1120px;margin:0 auto}
.student-council-view__body{display:flex;flex-direction:column;gap:18px;margin-top:24px}
.student-council-view__stage-shell{display:flex;flex-direction:column;align-items:center;gap:18px;padding-top:74px}
.student-council-view__stage-frame{width:min(100%,690px);min-height:380px;padding:28px 28px 40px;border-radius:34px;background:var(--color-surface);overflow:hidden}
.student-council-view__stage-pane{width:100%}
.student-council-view__stage-content{display:flex;flex-direction:column;gap:22px}
.student-council-view__hierarchy-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
.student-council-view__hierarchy-step{min-height:34px;border-radius:14px;background:color-mix(in srgb,var(--color-field-surface) 78%,var(--color-surface));color:var(--color-text-muted);display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;letter-spacing:0}
.student-council-view__hierarchy-step--active{background:var(--color-primary);color:var(--color-banner-text)}
.student-council-view__unavailable{display:flex;flex-direction:column;gap:16px;min-height:280px}
.student-council-view__unavailable-title{margin:0;font-size:clamp(34px,10vw,60px);line-height:.92;letter-spacing:-.07em;font-weight:700;color:var(--color-text-always-dark)}
.student-council-view__unavailable-copy{margin:0;max-width:28ch;font-size:15px;line-height:1.5;color:var(--color-text-muted)}
.student-council-view__unavailable-action{width:fit-content;min-height:52px;margin-top:auto;padding:0 22px;border:none;border-radius:999px;background:var(--color-primary);color:var(--color-banner-text);font-family:'Manrope',sans-serif;font-size:14px;font-weight:700}
.student-council-view__intro{display:flex;flex-direction:column;gap:18px;min-height:312px}
.student-council-view__stage-title{margin:0;font-size:clamp(36px,10vw,64px);line-height:.92;letter-spacing:-.08em;font-weight:700;color:var(--color-text-always-dark)}
.student-council-view__stage-copy{margin:0;max-width:18ch;font-size:17px;line-height:1.45;color:var(--color-text-always-dark)}
.student-council-view__primary-pill{width:fit-content;min-height:58px;margin-top:auto;padding:0 22px 0 8px;border:none;border-radius:999px;background:var(--color-primary);color:var(--color-banner-text);display:inline-flex;align-items:center;gap:14px;font-size:13px;font-weight:700}
.student-council-view__primary-pill-icon{width:42px;height:42px;border-radius:999px;background:var(--color-nav);color:var(--color-nav-text);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
.student-council-view__status{margin:0;font-size:14px;font-weight:600;color:var(--color-text-always-dark)}
.student-council-view__status--error{color:#D92D20}
.student-council-view__dashboard{display:flex;flex-direction:column;gap:18px}
.student-council-view__dashboard-title{margin:0;font-size:22px;font-weight:800;line-height:1;letter-spacing:-.05em;color:var(--color-text-primary)}
.student-council-view__dashboard-top{display:flex;flex-direction:column;gap:12px}
.student-council-view__dashboard-search{width:100%;display:flex;align-items:center;gap:10px;min-height:56px;padding:0 16px;border-radius:999px;background:var(--color-surface)}
.student-council-view__dashboard-search-input{flex:1;min-width:0;border:none;background:transparent;outline:none;font-size:14px;font-weight:500;color:var(--color-text-always-dark)}
.student-council-view__dashboard-search-input::placeholder{color:var(--color-text-muted)}
.student-council-view__dashboard-search-icon{width:34px;height:34px;border:none;border-radius:999px;background:transparent;color:var(--color-primary);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
.student-council-view__dashboard-search--loading{padding:0}
.student-council-view__dashboard-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;width:100%}
.student-council-view__dashboard-secondary{min-height:52px;padding:0 18px;border:none;border-radius:999px;background:var(--color-surface);color:var(--color-text-always-dark);display:inline-flex;align-items:center;justify-content:center;gap:10px;font-family:'Manrope',sans-serif;font-size:14px;font-weight:600;line-height:1.05;text-align:center}
.student-council-view__dashboard-secondary--loading{min-height:52px}
.student-council-view__dashboard-card{padding:28px;border-radius:34px;background:var(--color-surface)}
.student-council-view__dashboard-card-header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:20px}
.student-council-view__dashboard-card-title{margin:0;font-size:clamp(32px,9vw,52px);line-height:.94;letter-spacing:-.07em;font-weight:700;color:var(--color-text-always-dark)}
.student-council-view__member-list{display:flex;flex-direction:column;gap:12px}
.student-council-view__member-row{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:12px;min-height:72px;padding:10px 14px;border-radius:999px;background:color-mix(in srgb,var(--color-surface) 88%,var(--color-bg));cursor:pointer}
.student-council-view__member-row--loading{grid-template-columns:1fr;min-height:72px}
.student-council-view__member-id{min-width:88px;padding:10px 14px;border-radius:999px;background:var(--color-primary);font-size:11px;font-weight:700;line-height:1;color:var(--color-banner-text);text-align:center}
.student-council-view__member-copy{display:flex;flex-direction:column;min-width:0;gap:2px}
.student-council-view__member-name{min-width:0;font-size:14px;font-weight:600;color:var(--color-text-always-dark)}
.student-council-view__member-position{min-width:0;font-size:12px;font-weight:500;color:var(--color-text-muted)}
.student-council-view__member-edit{width:34px;height:34px;border:none;border-radius:999px;background:transparent;color:var(--color-text-always-dark);display:inline-flex;align-items:center;justify-content:center}
.student-council-view__member-empty{margin:0;padding:18px;border-radius:22px;background:color-mix(in srgb,var(--color-surface) 88%,var(--color-bg));font-size:14px;color:var(--color-text-muted)}
.student-council-view__sheet-backdrop{position:fixed;inset:0;z-index:70;display:flex;align-items:flex-end;justify-content:center;padding:24px;background:rgba(10,10,10,.28);backdrop-filter:blur(12px);overflow-y:auto;overscroll-behavior:contain}
.student-council-view__sheet{width:min(100%,690px);max-height:calc(100dvh - env(safe-area-inset-top,0px) - env(safe-area-inset-bottom,0px) - 48px);padding:28px;border-radius:34px;background:var(--color-surface);display:flex;flex-direction:column;overflow:hidden}
.student-council-view__sheet--detail{padding:28px}
.student-council-view__sheet-member-stage,.student-council-view__sheet-setup-stage,.student-council-view__member-detail{flex:1;min-height:0;overflow-y:auto;padding-right:4px}
.student-council-view__member-detail{display:flex;flex-direction:column;gap:18px}
.student-council-view__member-detail-header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}
.student-council-view__member-detail-title{margin:0;font-size:clamp(30px,8vw,42px);line-height:.95;letter-spacing:-.06em;font-weight:700;color:var(--color-text-always-dark)}
.student-council-view__member-detail-close{width:42px;height:42px;border:none;border-radius:999px;background:var(--color-field-surface);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 14%, transparent);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;color:var(--color-text-always-dark)}
.student-council-view__member-detail-field{display:flex;flex-direction:column;gap:10px}
.student-council-view__member-detail-label{font-size:13px;font-weight:600;color:var(--color-text-muted)}
.student-council-view__member-detail-value{min-height:52px;padding:0 18px;border-radius:999px;background:var(--color-field-surface);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 16%, transparent);display:flex;align-items:center;font-size:14px;font-weight:600;color:var(--color-text-always-dark)}
.student-council-view__member-detail-permissions{display:flex;flex-wrap:wrap;gap:8px}
.student-council-view__member-detail-permission{min-height:40px;padding:0 16px;border-radius:999px;background:var(--color-field-surface);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-field-surface-strong) 14%, transparent);display:inline-flex;align-items:center;font-size:13px;font-weight:600;color:var(--color-text-always-dark)}
.student-council-view__member-detail-permission--empty{color:var(--color-text-muted);font-weight:500}
.student-council-view__member-detail-actions{display:flex;flex-direction:column;gap:12px;padding-top:4px}
.student-council-view__member-delete{min-height:52px;border:1.5px solid rgba(217,45,32,.16);border-radius:999px;background:rgba(217,45,32,.06);font-family:'Manrope',sans-serif;font-size:14px;font-weight:700;color:#B42318}
.student-council-view__member-delete:disabled{opacity:.5;cursor:not-allowed}
.student-council-stage-enter-active,.student-council-stage-leave-active{transition:opacity .34s ease,transform .42s cubic-bezier(.22,1,.36,1)}
.student-council-stage-enter-from,.student-council-stage-leave-to{opacity:0;transform:translateY(10px)}
.student-council-sheet-enter-active,.student-council-sheet-leave-active{transition:opacity .28s ease}
.student-council-sheet-enter-active .student-council-view__sheet,.student-council-sheet-leave-active .student-council-view__sheet{transition:transform .48s cubic-bezier(.22,1,.36,1),opacity .28s ease}
.student-council-sheet-enter-from,.student-council-sheet-leave-to{opacity:0}
.student-council-sheet-enter-from .student-council-view__sheet,.student-council-sheet-leave-to .student-council-view__sheet{transform:translateY(28px);opacity:0}

@media (min-width:768px){
  .student-council-view{padding:40px 36px 56px}
  .student-council-view__body{margin-top:30px}
  .student-council-view__stage-shell{padding-top:52px}
  .student-council-view__stage-frame{min-height:420px;padding:40px 54px 52px}
  .student-council-view__intro{min-height:330px}
  .student-council-view__dashboard{max-width:720px}
  .student-council-view__dashboard-secondary{min-height:56px}
  .student-council-view__member-detail-actions{flex-direction:row}
}

@media (max-width:767px){
  .student-council-view__sheet-backdrop{padding:12px 12px calc(12px + env(safe-area-inset-bottom,0px))}
  .student-council-view__sheet{width:100%;max-height:calc(100dvh - env(safe-area-inset-top,0px) - env(safe-area-inset-bottom,0px) - 24px);padding:20px 18px 18px;border-radius:30px}
  .student-council-view__sheet-member-stage,.student-council-view__sheet-setup-stage,.student-council-view__member-detail{padding-right:2px;padding-bottom:max(6px, env(safe-area-inset-bottom,0px))}
  .student-council-view__member-detail-header{position:sticky;top:0;z-index:2;padding-bottom:6px;background:linear-gradient(to bottom,var(--color-surface) 78%,transparent)}
  .student-council-view__member-detail-actions{flex-direction:column}
}

@media (prefers-reduced-motion:reduce){
  .student-council-stage-enter-active,
  .student-council-stage-leave-active,
  .student-council-sheet-enter-active,
  .student-council-sheet-leave-active,
  .student-council-sheet-enter-active .student-council-view__sheet,
  .student-council-sheet-leave-active .student-council-view__sheet{
    transition:none
  }
}
</style>
