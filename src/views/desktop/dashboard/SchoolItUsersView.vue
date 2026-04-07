<template>
  <section class="school-it-users">
    <div class="school-it-users__shell">
      <StandardHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="activeSchoolSettings?.school_name || activeUser?.school_name || ''"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />
      <div class="school-it-users__breadcrumbs">
        <Breadcrumbs />
      </div>

      <div class="school-it-users__body">
        <h1 class="school-it-users__title dashboard-enter dashboard-enter--2">Students</h1>

        <div class="school-it-users__layout">
          <div class="school-it-users__main">
            <section class="school-it-users__search dashboard-enter dashboard-enter--3">
              <div class="school-it-users__search-row">
                <div class="school-it-users__search-wrap">
                  <AuraSearch
                    v-model="searchQuery"
                    placeholder="Search school data"
                    :results="searchResults"
                    @select="openSearchResult"
                  />
                </div>

              <button
                v-show="!searchActive && !isAddCollegeOpen"
                class="school-it-users__add-college-pill"
                type="button"
                aria-label="Add College"
                :aria-expanded="isAddCollegeOpen ? 'true' : 'false'"
                aria-controls="school-it-users-college-panel"
                @click="openAddCollegePanel"
              >
                <Plus :size="18" :stroke-width="2.4" />
                <span class="school-it-users__add-college-copy">Add<br>College</span>
              </button>
            </div>

            <Transition
              name="school-it-users-college-panel"
              @before-enter="onCollegePanelBeforeEnter"
              @enter="onCollegePanelEnter"
              @after-enter="onCollegePanelAfterEnter"
              @before-leave="onCollegePanelBeforeLeave"
              @leave="onCollegePanelLeave"
              @after-leave="onCollegePanelAfterLeave"
            >
              <div
                v-if="isAddCollegeOpen && !searchActive"
                id="school-it-users-college-panel"
                class="school-it-users__college-panel"
                role="region"
                :aria-label="collegePanelAriaLabel"
              >
                <div class="school-it-users__college-panel-inner">
                  <div class="school-it-users__college-shell">
                    <div class="school-it-users__college-header">
                      <button
                        class="school-it-users__college-close"
                        type="button"
                        aria-label="Close college panel"
                        @click="closeAddCollegePanel"
                      >
                        <X :size="18" :stroke-width="2.4" />
                      </button>
                      <span class="school-it-users__college-title">{{ collegePanelTitle }}</span>
                    </div>

                    <div class="school-it-users__college-form">
                      <div class="school-it-users__college-input-shell">
                        <input
                          ref="collegeInputEl"
                          v-model="collegeDraftName"
                          class="school-it-users__college-input"
                          type="text"
                          placeholder="e.g., College of Engineering"
                          :disabled="isSavingCollege"
                          @keyup.enter="submitCollege"
                        >
                      </div>

                      <button
                        class="school-it-users__college-submit"
                        type="button"
                        :disabled="collegeSubmitDisabled"
                        @click="submitCollege"
                      >
                        {{ collegeSubmitLabel }}
                      </button>
                    </div>

                    <p
                      v-if="collegePanelMessage"
                      class="school-it-users__college-message"
                      :class="{ 'school-it-users__college-message--error': collegePanelError }"
                    >
                      {{ collegePanelMessage }}
                    </p>
                  </div>
                </div>
              </div>
            </Transition>
          </section>

          <section v-if="departmentCards.length" class="school-it-users__department-list">
            <div
              v-for="(department, index) in departmentCards"
              :key="department.id"
              class="school-it-users__department-swipe dashboard-enter"
              :class="[
                `dashboard-enter--${Math.min(index + 6, 9)}`,
                { 'school-it-users__department-swipe--open': isDepartmentSwipeOpen(department.id) },
              ]"
            >
              <div class="school-it-users__department-actions" aria-hidden="true">
                <button
                  class="school-it-users__department-action school-it-users__department-action--delete"
                  type="button"
                  :disabled="isSavingCollege"
                  aria-label="Delete college"
                  @click.stop="deleteCollege(department)"
                >
                  <Trash2 :size="18" />
                </button>

                <button
                  class="school-it-users__department-action school-it-users__department-action--edit"
                  type="button"
                  :disabled="isSavingCollege"
                  aria-label="Edit college"
                  @click.stop="openEditCollegePanel(department)"
                >
                  <Pencil :size="18" />
                </button>
              </div>

              <article
                class="school-it-users__department-card"
                :style="getDepartmentSwipeStyle(department.id)"
                @click.capture="handleDepartmentCardClick(department.id, $event)"
                @pointerdown="onDepartmentPointerDown(department.id, $event)"
                @pointermove="onDepartmentPointerMove(department.id, $event)"
                @pointerup="onDepartmentPointerEnd(department.id, $event)"
                @pointercancel="onDepartmentPointerCancel(department.id, $event)"
                @lostpointercapture="onDepartmentPointerCancel(department.id, $event)"
              >
                <div class="school-it-users__department-main">
                  <h2 class="school-it-users__department-title">{{ department.name }}</h2>
                  <button
                    class="school-it-users__action-pill school-it-users__action-pill--inline"
                    type="button"
                    @pointerdown.stop
                    @click.stop="openDepartment(department)"
                  >
                    <span class="school-it-users__action-pill-icon">
                      <ArrowRight :size="18" />
                    </span>
                    View
                  </button>
                </div>

                <div class="school-it-users__department-panel">
                  <p class="school-it-users__department-label">Programs:</p>
                  <ul v-if="department.programs.length" class="school-it-users__program-list">
                    <li
                      v-for="program in department.programs"
                      :key="program.id"
                      class="school-it-users__program-item"
                    >
                      {{ program.name }}
                    </li>
                  </ul>
                  <p v-else class="school-it-users__program-empty">No programs yet.</p>
                </div>
              </article>
            </div>
          </section>

          <p v-else class="school-it-users__department-empty dashboard-enter dashboard-enter--6">
            {{ departmentEmptyMessage }}
          </p>
        </div>

        <aside class="school-it-users__side">
          <section class="school-it-users__overview dashboard-enter dashboard-enter--4">
            <article
              v-for="card in overviewCards"
              :key="card.id"
              class="school-it-users__hero-card"
              :class="[
                card.variant === 'primary'
                  ? 'school-it-users__hero-card--primary'
                  : 'school-it-users__hero-card--surface',
              ]"
            >
              <div class="school-it-users__hero-card-copy">
                <h2 class="school-it-users__overview-title" v-html="card.titleHtml" />
                <span v-if="card.meta" class="school-it-users__overview-meta">{{ card.meta }}</span>
              </div>

              <button
                class="school-it-users__hero-card-pill"
                :class="{
                  'school-it-users__hero-card-pill--surface': card.variant === 'primary',
                }"
                type="button"
                @click="handleOverviewAction(card)"
              >
                <span class="school-it-users__hero-card-pill-icon">
                  <ArrowRight :size="18" />
                </span>
                {{ card.actionLabel }}
              </button>
            </article>
          </section>

          <div class="school-it-users__alerts">
            <section
              class="school-it-users__alert dashboard-enter dashboard-enter--5"
            >
              <div class="school-it-users__alert-copy school-it-users__alert-copy--management">
                <h2
                  class="school-it-users__alert-org-name"
                  :class="{ 'school-it-users__alert-org-name--placeholder': !hasStudentCouncilAssigned }"
                >
                  {{ studentCouncilEntryText }}
                </h2>
              </div>

              <button
                class="school-it-users__action-pill"
                type="button"
                @click="openCouncilManagement"
              >
                <span class="school-it-users__action-pill-icon">
                  <ArrowRight :size="18" />
                </span>
                Manage
              </button>
            </section>

            <section class="school-it-users__alert dashboard-enter dashboard-enter--5">
              <div class="school-it-users__alert-copy school-it-users__alert-copy--management">
                <h2 class="school-it-users__alert-org-name school-it-users__alert-org-name--placeholder">
                  Unassigned<br>Students
                </h2>
              </div>

              <button
                class="school-it-users__action-pill"
                type="button"
                @click="openUnassignedStudents"
              >
                <span class="school-it-users__action-pill-icon">
                  <ArrowRight :size="18" />
                </span>
                Manage
              </button>
            </section>
          </div>
        </aside>
      </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Pencil, Plus, Trash2, X } from 'lucide-vue-next'
import StandardHeader from '@/components/desktop/dashboard/StandardHeader.vue'
import Breadcrumbs from '@/components/desktop/dashboard/Breadcrumbs.vue'
import AuraSearch from '@/components/desktop/dashboard/AuraSearch.vue'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { useSchoolItWorkspaceData } from '@/composables/useSchoolItWorkspaceData.js'
import { BackendApiError, createDepartment, deleteDepartment, updateDepartment } from '@/services/backendApi.js'
import {
  createStudentCouncilStorageKey,
  loadStudentCouncilState,
  resolveStudentCouncilAcronym,
} from '@/services/studentCouncilManagement.js'
import { filterWorkspaceEntitiesBySchool } from '@/services/workspaceScope.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()
const searchQuery = ref('')
const isAddCollegeOpen = ref(false)
const collegeInputEl = ref(null)
const collegeDraftName = ref('')
const collegePanelMessage = ref('')
const collegePanelError = ref(false)
const isSavingCollege = ref(false)
const collegePanelMode = ref('create')
const editingDepartmentId = ref(null)
const previewDepartmentOverrides = ref([])
const departmentSwipeOffsets = ref({})
const departmentSwipeDragId = ref(null)
const departmentSwipePointerId = ref(null)
const departmentSwipeStartX = ref(0)
const departmentSwipeStartY = ref(0)
const departmentSwipeStartOffset = ref(0)
const departmentSwipeAxisLock = ref(null)
const departmentSwipeDidDrag = ref(false)
const DEPARTMENT_SWIPE_ACTION_WIDTH = 70
const DEPARTMENT_SWIPE_OPEN_THRESHOLD = 28
const DEPARTMENT_SWIPE_GESTURE_THRESHOLD = 8

const { currentUser, schoolSettings, apiBaseUrl } = useDashboardSession()
const {
  departments,
  programs,
  users,
  campusSsgSetup,
  statuses: workspaceStatuses,
  initializeSchoolItWorkspaceData,
  refreshSchoolItWorkspaceData,
  setDepartmentsSnapshot,
} = useSchoolItWorkspaceData()
const { logout } = useAuth()

const activeUser = computed(() => props.preview ? schoolItPreviewData.user : currentUser.value)
const activeSchoolSettings = computed(() => props.preview ? schoolItPreviewData.schoolSettings : schoolSettings.value)
const activeDepartments = computed(() => props.preview ? previewDepartments.value : departments.value)
const activePrograms = computed(() => props.preview ? schoolItPreviewData.programs : programs.value)
const activeUsers = computed(() => props.preview ? schoolItPreviewData.users : users.value)

usePreviewTheme(() => props.preview, activeSchoolSettings)
const departmentsStatus = computed(() => props.preview ? 'ready' : workspaceStatuses.value?.departments || 'idle')

const schoolId = computed(() => Number(activeUser.value?.school_id ?? activeSchoolSettings.value?.school_id))
const avatarUrl = computed(() => activeUser.value?.avatar_url || '')
const displayName = computed(() => {
  const first = activeUser.value?.first_name || ''
  const middle = activeUser.value?.middle_name || ''
  const last = activeUser.value?.last_name || ''
  return [first, middle, last].filter(Boolean).join(' ') || activeUser.value?.email?.split('@')[0] || 'School IT'
})
const initials = computed(() => buildInitials(displayName.value))
const importRouteName = computed(() => props.preview ? 'PreviewSchoolItImportStudents' : 'SchoolItImportStudents')
const councilRouteName = computed(() => props.preview ? 'PreviewSchoolItStudentCouncil' : 'SchoolItStudentCouncil')
const usersRouteName = computed(() => props.preview ? 'PreviewSchoolItUsers' : 'SchoolItUsers')
const unassignedRouteName = computed(() => props.preview ? 'PreviewSchoolItUnassignedStudents' : 'SchoolItUnassignedStudents')
const departmentProgramsRouteName = computed(() => props.preview ? 'PreviewSchoolItDepartmentPrograms' : 'SchoolItDepartmentPrograms')
const previewCouncilState = computed(() => (
  props.preview
    ? loadStudentCouncilState(createStudentCouncilStorageKey(schoolId.value, true))
    : null
))
const previewDepartmentStorageKey = computed(() => (
  Number.isFinite(schoolId.value)
    ? `aura_exposed_departments_${schoolId.value}`
    : 'aura_exposed_departments'
))
const previewDepartments = computed(() => (
  previewDepartmentOverrides.value.length
    ? previewDepartmentOverrides.value
    : schoolItPreviewData.departments
))

const filteredDepartments = computed(() => filterWorkspaceEntitiesBySchool(activeDepartments.value, schoolId.value))
const filteredPrograms = computed(() => filterWorkspaceEntitiesBySchool(activePrograms.value, schoolId.value))
const filteredUsers = computed(() => filterWorkspaceEntitiesBySchool(activeUsers.value, schoolId.value))
const studentUsers = computed(() => filteredUsers.value.filter(isStudentUser))
const pendingResetUsers = computed(() => studentUsers.value.filter((user) => user.must_change_password))
const pendingResetsCountLabel = computed(() => String(pendingResetUsers.value.length))
const pendingResetsMeta = computed(() => {
  const count = pendingResetUsers.value.length
  if (count <= 0) return ''
  return `${count} pending`
})
const overviewCards = computed(() => ([
  {
    id: 'import-users',
    titleHtml: 'Import<br>User',
    variant: 'primary',
    actionLabel: 'Import',
    route: { name: importRouteName.value },
    meta: '',
  },
  {
    id: 'pending-resets',
    titleHtml: 'Pending<br>Resets',
    variant: 'surface',
    actionLabel: 'Review',
    route: { name: usersRouteName.value, query: { filter: 'pending-resets' } },
    meta: pendingResetsMeta.value,
  },
]))
const studentCouncilRecord = computed(() => {
  if (props.preview) return previewCouncilState.value?.council || null
  return campusSsgSetup.value?.unit || null
})
const studentCouncilAssignedMemberCount = computed(() => {
  if (props.preview) {
    return Array.isArray(previewCouncilState.value?.members)
      ? previewCouncilState.value.members.length
      : 0
  }

  const rawMembers = Array.isArray(campusSsgSetup.value?.unit?.members)
    ? campusSsgSetup.value.unit.members
    : []

  return rawMembers.filter((member) => member?.is_active !== false).length
})
const studentCouncilState = computed(() => (
  props.preview
    ? (studentCouncilRecord.value?.id ? 'ready' : 'absent')
    : workspaceStatuses.value?.council || 'idle'
))
const hasStudentCouncilAssigned = computed(() => (
  studentCouncilState.value === 'ready'
  && Boolean(studentCouncilRecord.value?.id)
  && studentCouncilAssignedMemberCount.value > 0
))
const studentCouncilEntryText = computed(() => {
  const acronym = resolveStudentCouncilAcronym(studentCouncilRecord.value)
  if (!acronym) return 'Student Council'
  return hasStudentCouncilAssigned.value ? `${acronym} is set` : acronym
})

const departmentCards = computed(() => (
  filteredDepartments.value
    .map((department) => ({
      ...department,
      programs: filteredPrograms.value
        .filter((program) => Array.isArray(program.department_ids) && program.department_ids.includes(Number(department.id)))
        .slice(0, 3),
    }))
    .sort((left, right) => String(left?.name || '').localeCompare(String(right?.name || '')))
))
const departmentEmptyMessage = computed(() => {
  if (['idle', 'loading'].includes(departmentsStatus.value)) {
    return 'Loading departments...'
  }

  if (departmentsStatus.value === 'blocked') {
    return 'Departments are unavailable until privileged verification is completed.'
  }

  if (departmentsStatus.value === 'error') {
    return 'Departments could not be loaded right now.'
  }

  return 'No departments please add.'
})

const searchActive = computed(() => searchQuery.value.trim().length > 0)
const resolvedEditingDepartmentId = computed(() => normalizeWorkspaceEntityId(editingDepartmentId.value))
const isEditingCollege = computed(() => collegePanelMode.value === 'edit' && resolvedEditingDepartmentId.value != null)
const collegePanelAriaLabel = computed(() => isEditingCollege.value ? 'Edit college' : 'Add college')
const collegePanelTitle = computed(() => isEditingCollege.value ? 'Edit College' : 'Add College')
const collegeSubmitLabel = computed(() => isEditingCollege.value ? 'Save' : 'Add')
const collegeSubmitDisabled = computed(() => {
  const normalizedName = collegeDraftName.value.trim()
  return isSavingCollege.value || normalizedName.length < 2 || normalizedName.length > 100
})
const departmentNameLookup = computed(() => new Map(
  filteredDepartments.value
    .map((department) => [String(department?.name || '').trim().toLowerCase(), Number(department?.id)])
    .filter(([name]) => Boolean(name))
))
const searchResults = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return []

  const departmentResults = filteredDepartments.value
    .filter((department) => department.name.toLowerCase().includes(query))
    .map((department) => ({
      key: `department-${department.id}`,
      name: department.name,
      type: 'College',
      meta: `${filteredPrograms.value.filter((program) => program.department_ids?.includes(Number(department.id))).length} linked programs`,
      action: () => openDepartment(department),
    }))

  return departmentResults.slice(0, 8)
})

const nextFrame = (callback) => requestAnimationFrame(() => requestAnimationFrame(callback))

const hasOpenDepartmentSwipe = computed(() => Object.values(departmentSwipeOffsets.value).some((offset) => offset > 0))

watch([apiBaseUrl, () => activeUser.value?.id, schoolId, () => props.preview], async ([resolvedApiBaseUrl, userId, , preview]) => {
  if (preview) return
  if (!resolvedApiBaseUrl || !userId) return
  await initializeSchoolItWorkspaceData()
}, { immediate: true })

watch(() => props.preview, (preview) => {
  if (!preview) {
    previewDepartmentOverrides.value = []
    return
  }
  previewDepartmentOverrides.value = readPreviewDepartments()
}, { immediate: true })

watch(isAddCollegeOpen, (open) => {
  if (!open) return
  nextTick(() => {
    setTimeout(() => collegeInputEl.value?.focus(), 220)
  })
})

watch(searchActive, (active) => {
  if (active) {
    isAddCollegeOpen.value = false
    closeAllDepartmentSwipes()
  }
})

watch(isAddCollegeOpen, (open) => {
  if (open) closeAllDepartmentSwipes()
})

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
})

function buildInitials(value) {
  const parts = String(value || '').split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return String(value || '').slice(0, 2).toUpperCase()
}

function normalizeWorkspaceEntityId(value) {
  const normalizedValue = Number(value)
  return Number.isInteger(normalizedValue) && normalizedValue > 0 ? normalizedValue : null
}

function isStudentUser(user) {
  const roles = Array.isArray(user?.roles)
    ? user.roles.map((role) => String(role?.role?.name || role?.name || '').toLowerCase())
    : []
  return Boolean(user?.student_profile) || roles.includes('student')
}

function openSearchResult(result) {
  searchQuery.value = ''
  result.action?.()
}

function openDepartment(department) {
  if (!department?.id) return
  router.push({
    name: departmentProgramsRouteName.value,
    params: {
      departmentId: department.id,
    },
  })
}

function openCouncilManagement() {
  router.push({ name: councilRouteName.value })
}

function openUnassignedStudents() {
  router.push({ name: unassignedRouteName.value })
}

function handleOverviewAction(card) {
  if (!card?.route) return
  router.push(card.route)
}

function openAddCollegePanel() {
  closeAllDepartmentSwipes()
  collegePanelMode.value = 'create'
  editingDepartmentId.value = null
  collegeDraftName.value = ''
  collegePanelMessage.value = ''
  collegePanelError.value = false
  isAddCollegeOpen.value = true
}

function openEditCollegePanel(department) {
  const normalizedDepartmentId = normalizeWorkspaceEntityId(department?.id)
  if (normalizedDepartmentId == null) return
  closeAllDepartmentSwipes()
  collegePanelMode.value = 'edit'
  editingDepartmentId.value = normalizedDepartmentId
  collegeDraftName.value = String(department.name || '')
  collegePanelMessage.value = ''
  collegePanelError.value = false
  isAddCollegeOpen.value = true
}

function closeAddCollegePanel() {
  isAddCollegeOpen.value = false
  collegePanelMode.value = 'create'
  collegePanelMessage.value = ''
  collegePanelError.value = false
  collegeDraftName.value = ''
  editingDepartmentId.value = null
}

async function submitCollege() {
  if (collegeSubmitDisabled.value) return

  const normalizedName = collegeDraftName.value.trim()
  const resolvedDepartmentId = resolvedEditingDepartmentId.value
  const mutationMode = isEditingCollege.value ? 'update' : 'create'
  const existingDepartmentId = departmentNameLookup.value.get(normalizedName.toLowerCase())
  if (existingDepartmentId != null && existingDepartmentId !== resolvedDepartmentId) {
    collegePanelError.value = true
    collegePanelMessage.value = `${normalizedName} already exists.`
    return
  }

  isSavingCollege.value = true
  collegePanelMessage.value = ''
  collegePanelError.value = false

  try {
    const authToken = localStorage.getItem('aura_token') || ''
    const createdDepartment = mutationMode === 'update'
      ? (
        props.preview
          ? {
            ...(activeDepartments.value.find((department) => Number(department.id) === resolvedDepartmentId) || {}),
            id: resolvedDepartmentId,
            school_id: schoolId.value,
            name: normalizedName,
          }
          : await updateDepartment(apiBaseUrl.value, authToken, resolvedDepartmentId, {
            name: normalizedName,
          })
      )
      : (
        props.preview
          ? createPreviewDepartment(normalizedName)
          : await createDepartment(apiBaseUrl.value, authToken, {
            name: normalizedName,
          })
      )

    const nextDepartments = sortDepartmentsByName([
      ...activeDepartments.value.filter((department) => Number(department.id) !== Number(createdDepartment.id)),
      createdDepartment,
    ])

    if (props.preview) {
      previewDepartmentOverrides.value = nextDepartments
      persistPreviewDepartments(nextDepartments)
    } else {
      setDepartmentsSnapshot(nextDepartments)
      refreshSchoolItWorkspaceData().catch(() => {})
    }

    collegePanelMessage.value = mutationMode === 'update'
      ? `${createdDepartment.name} updated successfully.`
      : `${createdDepartment.name} added successfully.`
    collegeDraftName.value = ''
    window.setTimeout(() => {
      closeAddCollegePanel()
    }, 420)
  } catch (error) {
    collegePanelError.value = true
    collegePanelMessage.value = resolveDepartmentMutationErrorMessage(error, mutationMode)
  } finally {
    isSavingCollege.value = false
  }
}

async function deleteCollege(department) {
  if (!department?.id || isSavingCollege.value) return

  const confirmed = window.confirm(`Delete ${department.name}?`)
  if (!confirmed) return

  isSavingCollege.value = true
  closeAllDepartmentSwipes()

  try {
    const nextDepartments = activeDepartments.value.filter((item) => Number(item.id) !== Number(department.id))

    if (props.preview) {
      previewDepartmentOverrides.value = sortDepartmentsByName(nextDepartments)
      persistPreviewDepartments(previewDepartmentOverrides.value)
    } else {
      await deleteDepartment(apiBaseUrl.value, localStorage.getItem('aura_token') || '', department.id)
      setDepartmentsSnapshot(sortDepartmentsByName(nextDepartments))
      refreshSchoolItWorkspaceData().catch(() => {})
    }

    if (resolvedEditingDepartmentId.value === Number(department.id)) {
      closeAddCollegePanel()
    }
  } catch (error) {
    window.alert(resolveDepartmentMutationErrorMessage(error, 'delete'))
  } finally {
    isSavingCollege.value = false
  }
}

function onCollegePanelBeforeEnter(element) {
  element.style.height = '0px'
  element.style.opacity = '0'
  element.style.transform = 'translateY(-8px)'
  element.style.willChange = 'height, opacity, transform'
}

function onCollegePanelEnter(element) {
  const height = element.scrollHeight
  element.style.transition = 'height 560ms cubic-bezier(0.22, 1, 0.36, 1), opacity 320ms ease, transform 460ms cubic-bezier(0.22, 1, 0.36, 1)'
  nextFrame(() => {
    element.style.height = `${height}px`
    element.style.opacity = '1'
    element.style.transform = 'translateY(0)'
  })
}

function onCollegePanelAfterEnter(element) {
  element.style.height = 'auto'
  element.style.transition = ''
  element.style.willChange = ''
}

function onCollegePanelBeforeLeave(element) {
  element.style.height = `${element.scrollHeight}px`
  element.style.opacity = '1'
  element.style.transform = 'translateY(0)'
  element.style.willChange = 'height, opacity, transform'
}

function onCollegePanelLeave(element) {
  element.style.transition = 'height 420ms cubic-bezier(0.4, 0, 0.2, 1), opacity 240ms ease, transform 300ms ease'
  nextFrame(() => {
    element.style.height = '0px'
    element.style.opacity = '0'
    element.style.transform = 'translateY(-6px)'
  })
}

function onCollegePanelAfterLeave(element) {
  element.style.transition = ''
  element.style.height = ''
  element.style.opacity = ''
  element.style.transform = ''
  element.style.willChange = ''
}

function createPreviewDepartment(name) {
  return {
    id: Date.now(),
    school_id: schoolId.value,
    name,
  }
}

function sortDepartmentsByName(items) {
  return [...items].sort((left, right) => String(left?.name || '').localeCompare(String(right?.name || '')))
}

function readPreviewDepartments() {
  try {
    const raw = localStorage.getItem(previewDepartmentStorageKey.value)
    if (!raw) return schoolItPreviewData.departments
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? sortDepartmentsByName(parsed) : schoolItPreviewData.departments
  } catch {
    return schoolItPreviewData.departments
  }
}

function persistPreviewDepartments(items) {
  localStorage.setItem(previewDepartmentStorageKey.value, JSON.stringify(items))
}

function resolveDepartmentMutationErrorMessage(error, mode = 'create') {
  const verb = mode === 'delete'
    ? 'delete'
    : mode === 'update'
      ? 'update'
      : 'add'

  if (!(error instanceof BackendApiError)) {
    return `Unable to ${verb} this college right now.`
  }

  const validationDetail = Array.isArray(error?.details?.detail)
    ? error.details.detail.find((item) => item && typeof item === 'object')
    : null
  const validationMessage = typeof validationDetail?.msg === 'string'
    ? validationDetail.msg
    : null
  const validationPath = Array.isArray(validationDetail?.loc)
    ? validationDetail.loc.map((segment) => String(segment).toLowerCase())
    : []

  if (error.status === 422) {
    if (validationPath.includes('name')) {
      return 'College name must be between 2 and 100 characters.'
    }
    if (validationPath.includes('department_id')) {
      return 'The selected college could not be resolved. Please reopen the panel and try again.'
    }
    if (validationMessage) {
      return validationMessage
    }
    if (typeof error?.details?.detail === 'string') {
      return error.details.detail
    }
    if (typeof error?.details?.message === 'string') {
      return error.details.message
    }
    if (error.message && error.message !== '[object Object]') {
      return error.message
    }
    return 'Invalid college details provided.'
  }

  if (error.status === 400 && /already exists/i.test(String(error.message || ''))) {
    return 'A college with this name already exists.'
  }

  if (error.status === 400 && mode === 'delete' && /cannot delete department|referenced by programs/i.test(String(error.message || ''))) {
    return 'This college is still linked to programs and cannot be deleted yet.'
  }

  if (error.status === 403) {
    return `This session is not allowed to ${verb} colleges right now.`
  }

  if (error.status === 409) {
    return 'This college is still linked to other records and cannot be deleted yet.'
  }

  return error.message || `Unable to ${verb} this college right now.`
}

async function handleLogout() {
  await logout()
}

function getDepartmentSwipeOffset(departmentId) {
  return Number(departmentSwipeOffsets.value[departmentId] || 0)
}

function isDepartmentSwipeOpen(departmentId) {
  return getDepartmentSwipeOffset(departmentId) > 0
}

function getDepartmentSwipeStyle(departmentId) {
  return {
    '--department-swipe-offset': `${getDepartmentSwipeOffset(departmentId)}px`,
  }
}

function setDepartmentSwipeOffset(departmentId, offset) {
  const normalizedOffset = Math.max(0, Math.min(DEPARTMENT_SWIPE_ACTION_WIDTH, Number(offset) || 0))
  if (normalizedOffset <= 0) {
    if (!Object.keys(departmentSwipeOffsets.value).length) return
    departmentSwipeOffsets.value = {}
    return
  }

  departmentSwipeOffsets.value = {
    [departmentId]: normalizedOffset,
  }
}

function closeAllDepartmentSwipes() {
  if (!hasOpenDepartmentSwipe.value) return
  departmentSwipeOffsets.value = {}
}

function handleDocumentPointerDown(event) {
  if (!hasOpenDepartmentSwipe.value) return
  if (!(event.target instanceof Element)) return
  if (event.target.closest('.school-it-users__department-swipe')) return
  closeAllDepartmentSwipes()
}

function handleDepartmentCardClick(departmentId, event) {
  if (isDepartmentInteractiveTarget(event.target)) {
    return
  }

  if (departmentSwipeDidDrag.value) {
    event.preventDefault()
    event.stopPropagation()
    departmentSwipeDidDrag.value = false
    return
  }

  if (!isDepartmentSwipeOpen(departmentId)) return
  if (event.target instanceof Element && event.target.closest('.school-it-users__action-pill')) return

  event.preventDefault()
  event.stopPropagation()
  setDepartmentSwipeOffset(departmentId, 0)
}

function onDepartmentPointerDown(departmentId, event) {
  if (event.pointerType === 'mouse' && event.button !== 0) return
  if (!(event.currentTarget instanceof HTMLElement)) return
  if (isDepartmentInteractiveTarget(event.target)) return

  departmentSwipeDragId.value = departmentId
  departmentSwipePointerId.value = event.pointerId
  departmentSwipeStartX.value = event.clientX
  departmentSwipeStartY.value = event.clientY
  departmentSwipeStartOffset.value = getDepartmentSwipeOffset(departmentId)
  departmentSwipeAxisLock.value = null
  departmentSwipeDidDrag.value = false
  event.currentTarget.setPointerCapture?.(event.pointerId)
}

function onDepartmentPointerMove(departmentId, event) {
  if (departmentSwipeDragId.value !== departmentId) return
  if (departmentSwipePointerId.value !== event.pointerId) return

  const deltaX = event.clientX - departmentSwipeStartX.value
  const deltaY = event.clientY - departmentSwipeStartY.value

  if (!departmentSwipeAxisLock.value) {
    if (
      Math.abs(deltaX) < DEPARTMENT_SWIPE_GESTURE_THRESHOLD
      && Math.abs(deltaY) < DEPARTMENT_SWIPE_GESTURE_THRESHOLD
    ) {
      return
    }

    departmentSwipeAxisLock.value = Math.abs(deltaX) > Math.abs(deltaY) ? 'x' : 'y'
  }

  if (departmentSwipeAxisLock.value !== 'x') return

  departmentSwipeDidDrag.value = true
  event.preventDefault()
  setDepartmentSwipeOffset(departmentId, departmentSwipeStartOffset.value - deltaX)
}

function onDepartmentPointerEnd(departmentId, event) {
  if (departmentSwipeDragId.value !== departmentId) return
  if (departmentSwipePointerId.value !== event.pointerId) return

  const currentOffset = getDepartmentSwipeOffset(departmentId)
  const shouldOpen = currentOffset >= DEPARTMENT_SWIPE_OPEN_THRESHOLD
  setDepartmentSwipeOffset(departmentId, shouldOpen ? DEPARTMENT_SWIPE_ACTION_WIDTH : 0)

  if (event.currentTarget instanceof HTMLElement) {
    event.currentTarget.releasePointerCapture?.(event.pointerId)
  }

  resetDepartmentSwipeGesture()
}

function onDepartmentPointerCancel(departmentId, event) {
  if (departmentSwipeDragId.value !== departmentId) return
  if (departmentSwipePointerId.value !== event.pointerId) return

  const currentOffset = getDepartmentSwipeOffset(departmentId)
  const shouldOpen = currentOffset >= DEPARTMENT_SWIPE_OPEN_THRESHOLD
  setDepartmentSwipeOffset(departmentId, shouldOpen ? DEPARTMENT_SWIPE_ACTION_WIDTH : 0)
  resetDepartmentSwipeGesture()
}

function resetDepartmentSwipeGesture() {
  window.setTimeout(() => {
    departmentSwipeDidDrag.value = false
  }, 0)
  departmentSwipeDragId.value = null
  departmentSwipePointerId.value = null
  departmentSwipeAxisLock.value = null
}

function isDepartmentInteractiveTarget(target) {
  if (!(target instanceof Element)) return false
  return Boolean(
    target.closest(
      '.school-it-users__action-pill, .school-it-users__department-action, button, a, input, textarea, select, label'
    )
  )
}
</script>

<style scoped>
.school-it-users {
  min-height: 100vh;
  padding: 80px 28px 120px;
  font-family: 'Manrope', sans-serif;
  background: var(--color-bg);
}

.school-it-users__shell {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
}

.school-it-users__breadcrumbs {
  margin: 12px 0 24px;
  padding: 0 4px;
}

.school-it-users__layout {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.school-it-users__body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.school-it-users__title {
  margin: 0 0 4px;
  font-size: 26px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.05em;
  color: var(--color-text-primary);
}

/* ── Search & Add ── */
.school-it-users__search {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.school-it-users__search-row {
  display: flex;
  align-items: stretch;
  gap: 12px;
}

.school-it-users__search-wrap {
  flex: 1;
  min-width: 0;
}

.school-it-users__search-results {
  overflow: hidden;
  min-height: 0;
}

.school-it-users__search-results-inner {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 0 8px;
}

.school-it-users__search-result {
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 20px;
  background: color-mix(in srgb, var(--color-surface) 94%, var(--color-bg));
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
  transition: transform 0.2s ease, background 0.2s ease;
}

.school-it-users__search-result:hover {
  background: color-mix(in srgb, var(--color-surface) 88%, var(--color-bg));
  transform: translateX(4px);
}

.school-it-users__search-result-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.school-it-users__search-result-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-always-dark);
}

.school-it-users__search-result-type {
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

.school-it-users__add-college-pill {
  width: 128px;
  min-height: 60px;
  padding: 0 16px;
  border: none;
  border-radius: 999px;
  background: var(--color-search-pill-bg);
  color: var(--color-search-pill-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-shrink: 0;
  box-shadow: var(--aura-shadow-soft);
  transition: transform 0.2s ease, filter 0.2s ease;
}

.school-it-users__add-college-pill:hover {
  filter: brightness(1.08);
  transform: translateY(-2px);
}

.school-it-users__add-college-copy {
  font-size: 13px;
  font-weight: 800;
  line-height: 0.95;
  text-align: left;
}

/* ── Panels ── */
.school-it-users__college-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
  border-radius: 32px;
  background: var(--color-primary);
  color: var(--color-banner-text);
  box-shadow: var(--aura-shadow-premium);
}

.school-it-users__college-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.school-it-users__college-title {
  font-size: 20px;
  font-weight: 800;
}

.school-it-users__college-input-shell {
  min-height: 58px;
  padding: 0 20px;
  border-radius: 999px;
  background: var(--color-surface);
  display: flex;
  align-items: center;
}

.school-it-users__college-submit {
  min-height: 52px;
  padding: 0 32px;
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  font-weight: 700;
  border: none;
  transition: transform 0.2s ease;
}

/* ── Hero Cards ── */
.school-it-users__overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.school-it-users__hero-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 28px 24px;
  border-radius: 32px;
  min-height: 180px;
  background: var(--color-surface);
  box-shadow: var(--aura-shadow-soft);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.school-it-users__hero-card:hover {
  transform: scale(1.02);
}

.school-it-users__hero-card--primary {
  background: var(--color-primary);
  color: var(--color-banner-text);
}

.school-it-users__overview-title {
  margin: 0;
  font-size: 38px;
  font-weight: 800;
  line-height: 0.9;
  letter-spacing: -0.06em;
}

.school-it-users__hero-card-pill {
  width: fit-content;
  min-height: 48px;
  padding: 0 16px 0 6px;
  border-radius: 999px;
  background: var(--color-primary);
  color: var(--color-banner-text);
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 800;
  border: none;
}

.school-it-users__hero-card-pill--surface {
  background: var(--color-bg);
  color: var(--color-text-primary);
}

.school-it-users__hero-card-pill-icon {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  background: var(--color-nav);
  color: var(--color-nav-text);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ── Alerts ── */
.school-it-users__alerts {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.school-it-users__alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-radius: 28px;
  background: var(--aura-glass-bg);
  border: 1px solid var(--aura-glass-border);
  backdrop-filter: blur(var(--nav-glass-blur));
  -webkit-backdrop-filter: blur(var(--nav-glass-blur));
  box-shadow: var(--aura-shadow-soft);
}

.school-it-users__alert-org-name {
  margin: 0;
  font-size: 32px;
  font-weight: 800;
  line-height: 0.95;
  letter-spacing: -0.06em;
  color: var(--color-text-always-dark);
}

.school-it-users__alert-org-name--placeholder {
  color: var(--color-primary);
}

.school-it-users__action-pill {
  min-height: 52px;
  padding: 0 20px 0 6px;
  border-radius: 999px;
  background: var(--color-primary);
  color: var(--color-banner-text);
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 800;
  border: none;
  transition: transform 0.2s ease;
}

.school-it-users__action-pill:active {
  transform: scale(0.96);
}

.school-it-users__action-pill-icon {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: var(--color-nav);
  color: var(--color-nav-text);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ── Department List ── */
.school-it-users__department-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  margin-top: 20px;
}

.school-it-users__department-swipe {
  position: relative;
  border-radius: 32px;
  overflow: hidden;
  background: var(--color-surface);
  box-shadow: var(--aura-shadow-soft);
  transition: transform 0.3s ease;
}

.school-it-users__department-card {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  padding: 12px;
  transition: transform 0.42s cubic-bezier(0.22, 1, 0.36, 1);
  transform: translate3d(calc(var(--department-swipe-offset, 0px) * -1), 0, 0);
}

.school-it-users__department-main {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 180px;
  padding: 16px 8px;
}

.school-it-users__department-title {
  margin: 0;
  font-size: 38px;
  font-weight: 800;
  line-height: 0.9;
  letter-spacing: -0.06em;
  color: var(--color-text-always-dark);
}

.school-it-users__department-panel {
  width: 160px;
  padding: 20px;
  border-radius: 24px;
  background: var(--color-bg);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.school-it-users__department-label {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  color: var(--color-primary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.school-it-users__program-item {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.school-it-users__department-actions {
  position: absolute;
  inset: 0 0 0 auto;
  width: 70px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 8px;
  z-index: 1;
}

.school-it-users__department-action {
  width: 48px;
  height: 48px;
  border-radius: 999px;
  border: none;
  background: var(--color-surface);
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--aura-shadow-soft);
}

.school-it-users__department-action--delete {
  color: #ef4444;
}

/* ── Responsive Customization ── */

@media (min-width: 1024px) {
  .school-it-users__layout {
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 32px;
    align-items: start;
  }

  .school-it-users__department-list {
    grid-template-columns: repeat(auto-fill, minmax(440px, 1fr));
  }

  .school-it-users__side {
    position: sticky;
    top: 100px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .school-it-users__department-swipe:hover {
    transform: translateY(-4px);
    box-shadow: var(--aura-shadow-premium);
  }
}

@media (max-width: 767px) {
  .school-it-users {
    padding: 30px 20px 100px;
  }
  
  .school-it-users__department-title {
    font-size: 32px;
  }
  
  .school-it-users__department-panel {
    width: 130px;
    padding: 16px;
  }

  .school-it-users__add-college-pill {
    width: 110px;
  }
}
</style>
