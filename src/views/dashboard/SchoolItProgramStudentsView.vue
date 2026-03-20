<template>
  <section class="school-it-program-students">
    <div class="school-it-program-students__shell">
      <SchoolItTopHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="activeSchoolSettings?.school_name || activeUser?.school_name || ''"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <div class="school-it-program-students__body">
        <h1 class="school-it-program-students__title dashboard-enter dashboard-enter--2">
          {{ selectedProgram?.name || 'Program' }}
        </h1>

        <section class="school-it-program-students__toolbar dashboard-enter dashboard-enter--3">
          <div class="school-it-program-students__search-wrap" :class="{ 'school-it-program-students__search-wrap--active': searchActive }">
            <div
              class="school-it-program-students__search-shell"
              :class="{ 'school-it-program-students__search-shell--open': searchActive }"
            >
              <div class="school-it-program-students__search-input-row">
                <input
                  v-model="searchQuery"
                  class="school-it-program-students__search-input"
                  type="text"
                  placeholder="Search students"
                >
                <span class="school-it-program-students__search-icon-wrap" aria-hidden="true">
                  <Search class="school-it-program-students__search-icon" :size="14" />
                </span>
              </div>

              <div class="school-it-program-students__search-results">
                <div class="school-it-program-students__search-results-inner">
                  <template v-if="searchActive">
                    <button
                      v-for="student in searchResults"
                      :key="student.id"
                      class="school-it-program-students__search-result"
                      type="button"
                      @click="handleSearchResult(student)"
                    >
                      <span class="school-it-program-students__search-pill">{{ student.studentId }}</span>
                      <span class="school-it-program-students__search-result-name">{{ student.fullName }}</span>
                    </button>

                    <p
                      v-if="!searchResults.length"
                      class="school-it-program-students__search-empty"
                    >
                      No matching students.
                    </p>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <div class="school-it-program-students__sort-wrap">
            <button
              class="school-it-program-students__sort-pill"
              type="button"
              :aria-expanded="isSortMenuOpen ? 'true' : 'false'"
              @click="isSortMenuOpen = !isSortMenuOpen"
            >
              <ChevronDown :size="18" />
              Sort
            </button>

            <Transition name="school-it-program-students-sort">
              <div
                v-if="isSortMenuOpen"
                class="school-it-program-students__sort-menu"
                role="menu"
                aria-label="Sort students"
              >
                <button
                  v-for="option in sortOptions"
                  :key="option.id"
                  class="school-it-program-students__sort-option"
                  :class="{ 'school-it-program-students__sort-option--active': option.id === sortMode }"
                  type="button"
                  role="menuitemradio"
                  :aria-checked="option.id === sortMode ? 'true' : 'false'"
                  @click="selectSortMode(option.id)"
                >
                  {{ option.label }}
                </button>
              </div>
            </Transition>
          </div>
        </section>

        <section
          v-if="selectedProgram"
          class="school-it-program-students__card dashboard-enter dashboard-enter--4"
        >
          <h2 class="school-it-program-students__section-title">Students</h2>

          <div v-if="visibleStudents.length" class="school-it-program-students__list">
            <article
              v-for="student in visibleStudents"
              :key="student.id"
              :ref="(element) => setStudentRowRef(student.id, element)"
              class="school-it-program-students__row"
              :class="{ 'school-it-program-students__row--highlighted': highlightedStudentId === student.id }"
            >
              <div class="school-it-program-students__row-copy">
                <span class="school-it-program-students__student-id">{{ student.studentId }}</span>
                <span class="school-it-program-students__student-name">{{ student.fullName }}</span>
              </div>

              <div class="school-it-program-students__row-actions">
                <button
                  class="school-it-program-students__icon-button school-it-program-students__icon-button--danger"
                  type="button"
                  :disabled="student.isMutating || props.preview"
                  aria-label="Remove student from program"
                  @click="removeStudentFromProgram(student)"
                >
                  <Trash2 :size="18" />
                </button>

                <button
                  class="school-it-program-students__icon-button"
                  type="button"
                  aria-label="Edit student"
                  @click="editStudent(student)"
                >
                  <Pencil :size="18" />
                </button>
              </div>
            </article>
          </div>

          <p v-else class="school-it-program-students__empty">
            {{ emptyMessage }}
          </p>

          <p
            v-if="feedbackMessage"
            class="school-it-program-students__feedback"
            :class="{ 'school-it-program-students__feedback--error': feedbackTone === 'error' }"
          >
            {{ feedbackMessage }}
          </p>
        </section>

        <p
          v-else-if="isProgramDataLoading"
          class="school-it-program-students__empty dashboard-enter dashboard-enter--4"
        >
          Loading program details...
        </p>

        <p
          v-else-if="isProgramDataUnavailable"
          class="school-it-program-students__empty dashboard-enter dashboard-enter--4"
        >
          Program data is unavailable right now.
        </p>

        <p
          v-else
          class="school-it-program-students__empty dashboard-enter dashboard-enter--4"
        >
          This program could not be found.
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronDown, Pencil, Search, Trash2 } from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { useSchoolItWorkspaceData } from '@/composables/useSchoolItWorkspaceData.js'
import { BackendApiError, updateStudentProfile } from '@/services/backendApi.js'
import { filterWorkspaceEntitiesBySchool } from '@/services/workspaceScope.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const sortOptions = [
  { id: 'name-asc', label: 'A-Z' },
  { id: 'name-desc', label: 'Z-A' },
  { id: 'id-asc', label: 'ID Number' },
]

const route = useRoute()
const router = useRouter()
const searchQuery = ref('')
const sortMode = ref(sortOptions[0].id)
const isSortMenuOpen = ref(false)
const feedbackMessage = ref('')
const feedbackTone = ref('info')
const mutatingStudentIds = ref([])
const highlightedStudentId = ref(null)
const studentRowRefs = ref(new Map())
const isSelectingSearchResult = ref(false)

const { logout } = useAuth()
const { currentUser, schoolSettings, apiBaseUrl } = useDashboardSession()
const {
  departments,
  programs,
  users,
  statuses: workspaceStatuses,
  initializeSchoolItWorkspaceData,
  setUsersSnapshot,
} = useSchoolItWorkspaceData()

const departmentId = computed(() => normalizeRouteId(route.params.departmentId))
const programId = computed(() => normalizeRouteId(route.params.programId))
const activeUser = computed(() => props.preview ? schoolItPreviewData.user : currentUser.value)
const activeSchoolSettings = computed(() => props.preview ? schoolItPreviewData.schoolSettings : schoolSettings.value)
const activeDepartments = computed(() => props.preview ? schoolItPreviewData.departments : departments.value)
const activePrograms = computed(() => props.preview ? schoolItPreviewData.programs : programs.value)
const activeUsers = computed(() => props.preview ? schoolItPreviewData.users : users.value)

usePreviewTheme(() => props.preview, activeSchoolSettings)
const schoolId = computed(() => Number(activeUser.value?.school_id ?? activeSchoolSettings.value?.school_id))
const filteredDepartments = computed(() => filterWorkspaceEntitiesBySchool(activeDepartments.value, schoolId.value))
const filteredPrograms = computed(() => filterWorkspaceEntitiesBySchool(activePrograms.value, schoolId.value))
const filteredUsers = computed(() => filterWorkspaceEntitiesBySchool(activeUsers.value, schoolId.value))
const studentUsers = computed(() => filteredUsers.value.filter(isStudentUser))
const departmentsStatus = computed(() => workspaceStatuses.value?.departments || 'idle')
const programsStatus = computed(() => workspaceStatuses.value?.programs || 'idle')
const usersStatus = computed(() => workspaceStatuses.value?.users || 'idle')
const settingsRouteName = computed(() => props.preview ? 'PreviewSchoolItSettings' : 'SchoolItSettings')
const avatarUrl = computed(() => activeUser.value?.avatar_url || '')
const displayName = computed(() => {
  const first = activeUser.value?.first_name || ''
  const middle = activeUser.value?.middle_name || ''
  const last = activeUser.value?.last_name || ''
  return [first, middle, last].filter(Boolean).join(' ') || activeUser.value?.email?.split('@')[0] || 'School IT'
})
const initials = computed(() => buildInitials(displayName.value))

const selectedDepartment = computed(() => (
  filteredDepartments.value.find((department) => Number(department.id) === departmentId.value) || null
))

const selectedProgram = computed(() => {
  const match = filteredPrograms.value.find((program) => Number(program.id) === programId.value)
  if (!match) return null

  const programDepartmentIds = Array.isArray(match.department_ids) ? match.department_ids.map(Number) : []
  if (departmentId.value != null && programDepartmentIds.length && !programDepartmentIds.includes(departmentId.value)) {
    return null
  }

  return match
})

const isProgramDataLoading = computed(() => (
  !selectedProgram.value &&
  ['idle', 'loading'].includes(programsStatus.value)
))

const isProgramDataUnavailable = computed(() => (
  !selectedProgram.value &&
  ['blocked', 'error'].includes(programsStatus.value)
))

const programStudents = computed(() => (
  studentUsers.value
    .filter((user) => Number(user?.student_profile?.program_id) === programId.value)
    .map((user) => ({
      id: Number(user.id),
      userId: Number(user.id),
      fullName: [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.email || 'Student',
      studentId: String(user?.student_profile?.student_id || user.id || ''),
      profileId: Number(user?.student_profile?.id),
      profile: user?.student_profile || null,
      searchText: [
        user?.student_profile?.student_id,
        user.first_name,
        user.last_name,
        user.email,
      ].filter(Boolean).join(' ').toLowerCase(),
      isMutating: mutatingStudentIds.value.includes(Number(user.id)),
    }))
))

const visibleStudents = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  const filtered = !query
    ? programStudents.value
    : programStudents.value.filter((student) => student.searchText.includes(query))

  return [...filtered].sort((left, right) => {
    if (sortMode.value === 'name-asc') {
      return left.fullName.localeCompare(right.fullName)
    }
    if (sortMode.value === 'name-desc') {
      return right.fullName.localeCompare(left.fullName)
    }
    return left.studentId.localeCompare(right.studentId, undefined, { numeric: true, sensitivity: 'base' })
  })
})

const searchActive = computed(() => searchQuery.value.trim().length > 0)
const searchResults = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return []
  return programStudents.value
    .filter((student) => student.searchText.includes(query))
    .slice(0, 8)
})

const emptyMessage = computed(() => {
  if (searchQuery.value.trim()) {
    return 'No students match this search.'
  }
  if ((usersStatus.value === 'idle' || usersStatus.value === 'loading') && programStudents.value.length <= 0) {
    return 'Loading students...'
  }
  if (['blocked', 'error'].includes(usersStatus.value) && programStudents.value.length <= 0) {
    return 'Students are unavailable right now.'
  }
  return 'No students are assigned to this program yet.'
})

watch([apiBaseUrl, () => activeUser.value?.id, () => props.preview], async ([resolvedApiBaseUrl, userId, preview]) => {
  if (preview) return
  if (!resolvedApiBaseUrl || !userId) return
  await initializeSchoolItWorkspaceData()
}, { immediate: true })

watch(searchQuery, () => {
  feedbackMessage.value = ''
  if (!isSelectingSearchResult.value) {
    highlightedStudentId.value = null
  }
  isSortMenuOpen.value = false
})

function normalizeRouteId(value) {
  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized : null
}

function buildInitials(value) {
  const parts = String(value || '').split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return String(value || '').slice(0, 2).toUpperCase()
}

function isStudentUser(user) {
  const roles = Array.isArray(user?.roles)
    ? user.roles.map((role) => String(role?.role?.name || role?.name || '').toLowerCase())
    : []
  return Boolean(user?.student_profile) || roles.includes('student')
}

function selectSortMode(nextSortMode) {
  sortMode.value = nextSortMode
  isSortMenuOpen.value = false
}

function setStudentRowRef(studentId, element) {
  const nextMap = new Map(studentRowRefs.value)
  if (element) {
    nextMap.set(Number(studentId), element)
  } else {
    nextMap.delete(Number(studentId))
  }
  studentRowRefs.value = nextMap
}

async function handleSearchResult(student) {
  isSelectingSearchResult.value = true
  highlightedStudentId.value = student.id
  searchQuery.value = ''
  await nextTick()
  const row = studentRowRefs.value.get(Number(student.id))
  row?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  window.setTimeout(() => {
    isSelectingSearchResult.value = false
  }, 180)
}

async function removeStudentFromProgram(student) {
  if (props.preview || student.isMutating || !student.profileId || !student.profile) return

  const confirmed = window.confirm(`Remove ${student.fullName} from ${selectedProgram.value?.name || 'this program'}?`)
  if (!confirmed) return

  mutatingStudentIds.value = [...mutatingStudentIds.value, student.id]
  feedbackMessage.value = ''

  try {
    const updatedUser = await updateStudentProfile(
      apiBaseUrl.value,
      localStorage.getItem('aura_token') || '',
      student.profileId,
      {
        department_id: student.profile.department_id ?? selectedDepartment.value?.id ?? null,
        program_id: null,
        student_id: student.profile.student_id ?? null,
        year_level: student.profile.year_level ?? null,
      },
    )

    const nextUsers = activeUsers.value
      .map((user) => Number(user.id) === Number(updatedUser.id) ? updatedUser : user)
      .sort((left, right) => String(left?.last_name || '').localeCompare(String(right?.last_name || '')))

    setUsersSnapshot(nextUsers)
    feedbackTone.value = 'info'
    feedbackMessage.value = `${student.fullName} was removed from ${selectedProgram.value?.name || 'this program'}.`
  } catch (error) {
    feedbackTone.value = 'error'
    feedbackMessage.value = resolveStudentMutationError(error)
  } finally {
    mutatingStudentIds.value = mutatingStudentIds.value.filter((userId) => userId !== student.id)
  }
}

function editStudent(student) {
  router.push({
    name: settingsRouteName.value,
    query: {
      department: departmentId.value,
      program: programId.value,
      student: student.userId,
    },
  })
}

function resolveStudentMutationError(error) {
  if (!(error instanceof BackendApiError)) {
    return 'Unable to update this student right now.'
  }

  if (error.status === 403) {
    return 'This session is not allowed to update students right now.'
  }

  if (error.status === 422) {
    return 'Student profile data is invalid. Please refresh and try again.'
  }

  return error.message || 'Unable to update this student right now.'
}

async function handleLogout() {
  await logout()
}
</script>

<style scoped>
.school-it-program-students {
  min-height: 100vh;
  padding: 30px 28px 120px;
  font-family: 'Manrope', sans-serif;
}

.school-it-program-students__shell {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
}

.school-it-program-students__body {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-top: 24px;
}

.school-it-program-students__title {
  margin: 0;
  font-size: clamp(26px, 7.4vw, 42px);
  line-height: 0.94;
  letter-spacing: -0.06em;
  font-weight: 700;
  color: var(--color-text-primary);
  word-break: break-word;
}

.school-it-program-students__toolbar {
  position: relative;
  z-index: 5;
  display: flex;
  align-items: stretch;
  gap: clamp(8px, 3vw, 12px);
}

.school-it-program-students__search-wrap {
  flex: 1;
  min-width: 0;
  transition: flex 0.3s ease;
}

.school-it-program-students__search-wrap--active {
  flex: 1 1 100%;
}

.school-it-program-students__search-shell {
  display: grid;
  grid-template-rows: auto 0fr;
  min-height: clamp(60px, 15vw, 64px);
  padding: 12px clamp(14px, 4vw, 18px);
  border-radius: 30px;
  background: var(--color-surface);
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
  transition:
    grid-template-rows 0.32s cubic-bezier(0.22, 1, 0.36, 1),
    border-radius 0.32s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.28s ease;
}

.school-it-program-students__search-shell--open {
  grid-template-rows: auto 1fr;
  border-radius: 28px;
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.1);
}

.school-it-program-students__search-input-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: clamp(8px, 2.5vw, 10px);
  min-height: clamp(36px, 9vw, 40px);
}

.school-it-program-students__search-input {
  width: 100%;
  min-width: 0;
  border: none;
  background: transparent;
  outline: none;
  color: var(--color-text-always-dark);
  font-size: clamp(13px, 3.8vw, 14px);
  font-weight: 500;
}

.school-it-program-students__search-input::placeholder {
  color: var(--color-text-muted);
}

.school-it-program-students__search-icon-wrap {
  width: clamp(30px, 8vw, 32px);
  height: clamp(30px, 8vw, 32px);
  border-radius: 999px;
  border: 1px solid var(--color-surface-border);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  flex-shrink: 0;
  place-self: center;
}

.school-it-program-students__search-icon {
  display: block;
  width: clamp(15px, 4.2vw, 18px);
  height: clamp(15px, 4.2vw, 18px);
}

.school-it-program-students__search-results {
  overflow: hidden;
  min-height: 0;
}

.school-it-program-students__search-results-inner {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 0 6px;
}

.school-it-program-students__search-result {
  width: 100%;
  padding: 12px 14px;
  border: none;
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-surface) 88%, var(--color-bg));
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  text-align: left;
}

.school-it-program-students__search-pill {
  min-width: 88px;
  min-height: 30px;
  padding: 0 14px;
  border-radius: 999px;
  background: var(--color-search-pill-bg);
  color: var(--color-search-pill-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.school-it-program-students__search-result-name {
  min-width: 0;
  font-size: 13px;
  line-height: 1.2;
  font-weight: 600;
  color: var(--color-text-always-dark);
}

.school-it-program-students__search-empty {
  margin: 0;
  padding: 4px 6px 2px;
  font-size: 13px;
  line-height: 1.35;
  font-weight: 600;
  color: var(--color-text-muted);
  text-align: center;
}

.school-it-program-students__sort-wrap {
  position: relative;
  flex-shrink: 0;
  z-index: 6;
}

.school-it-program-students__sort-pill {
  width: clamp(118px, 31vw, 132px);
  min-height: clamp(60px, 15vw, 64px);
  padding: 0 clamp(14px, 4vw, 18px);
  border: none;
  border-radius: 999px;
  background: var(--color-primary);
  color: var(--color-banner-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: clamp(13px, 3.5vw, 14px);
  font-weight: 700;
}

.school-it-program-students__sort-menu {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 20;
  min-width: 172px;
  padding: 10px;
  border-radius: 22px;
  background: var(--color-surface);
  border: 1px solid var(--color-surface-border);
  box-shadow: 0 18px 36px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.school-it-program-students__sort-option {
  min-height: 44px;
  padding: 0 14px;
  border: none;
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-surface) 88%, var(--color-bg));
  color: var(--color-text-always-dark);
  text-align: left;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.school-it-program-students__sort-option--active {
  background: color-mix(in srgb, var(--color-primary) 18%, var(--color-surface));
}

.school-it-program-students__card {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 28px 20px 22px;
  border-radius: 32px;
  background: var(--color-surface);
}

.school-it-program-students__section-title {
  margin: 0;
  font-size: clamp(18px, 5.2vw, 20px);
  line-height: 1;
  letter-spacing: -0.04em;
  font-weight: 700;
  color: var(--color-primary);
}

.school-it-program-students__list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.school-it-program-students__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 6px 8px;
  border-radius: 22px;
  transition: background 0.24s ease, transform 0.24s ease;
}

.school-it-program-students__row--highlighted {
  background: color-mix(in srgb, var(--color-primary) 14%, var(--color-surface));
  transform: translateY(-1px);
}

.school-it-program-students__row-copy {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 12px;
}

.school-it-program-students__student-id {
  min-width: 88px;
  min-height: 30px;
  padding: 0 14px;
  border-radius: 999px;
  background: var(--color-primary);
  color: var(--color-banner-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.school-it-program-students__student-name {
  min-width: 0;
  font-size: 13px;
  line-height: 1.2;
  font-weight: 500;
  color: var(--color-text-always-dark);
}

.school-it-program-students__row-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.school-it-program-students__icon-button {
  width: 34px;
  height: 34px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-always-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
}

.school-it-program-students__icon-button--danger {
  color: #FF3B30;
}

.school-it-program-students__icon-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.school-it-program-students__empty {
  margin: 0;
  padding: 10px 4px 2px;
  font-size: 14px;
  line-height: 1.4;
  font-weight: 600;
  color: var(--color-text-muted);
  text-align: center;
}

.school-it-program-students__feedback {
  margin: 0;
  font-size: 13px;
  line-height: 1.35;
  font-weight: 600;
  color: var(--color-text-muted);
}

.school-it-program-students__feedback--error {
  color: #B42318;
}

.school-it-program-students-sort-enter-active,
.school-it-program-students-sort-leave-active {
  transition: opacity 0.2s ease, transform 0.22s ease;
}

.school-it-program-students-sort-enter-from,
.school-it-program-students-sort-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (min-width: 768px) {
  .school-it-program-students {
    padding: 40px 36px 56px;
  }

  .school-it-program-students__body {
    margin-top: 30px;
    gap: 22px;
  }

  .school-it-program-students__toolbar,
  .school-it-program-students__card {
    max-width: 820px;
  }

  .school-it-program-students__card {
    padding: 32px 24px 26px;
  }

  .school-it-program-students__student-name {
    font-size: 14px;
  }

  .school-it-program-students__search-result-name {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .school-it-program-students__toolbar {
    gap: 10px;
  }

  .school-it-program-students__sort-pill {
    width: clamp(108px, 32vw, 120px);
    padding-inline: 14px;
  }

  .school-it-program-students__search-result {
    grid-template-columns: 1fr;
    gap: 8px;
    align-items: stretch;
  }

  .school-it-program-students__search-pill {
    width: fit-content;
  }

  .school-it-program-students__search-empty {
    padding-inline: 10px;
  }
}
</style>
