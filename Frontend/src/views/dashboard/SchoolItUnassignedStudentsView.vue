<template>
  <section class="school-it-unassigned">
    <div class="school-it-unassigned__shell">
      <SchoolItTopHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="activeSchoolSettings?.school_name || activeUser?.school_name || ''"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <div class="school-it-unassigned__body">
        <h1 class="school-it-unassigned__title dashboard-enter dashboard-enter--2">Unassigned Students</h1>

        <section class="school-it-unassigned__toolbar dashboard-enter dashboard-enter--3">
          <div class="school-it-unassigned__search-shell">
            <input
              v-model="searchQuery"
              class="school-it-unassigned__search-input"
              type="text"
              placeholder=""
              aria-label="Search unassigned students"
            >
            <button class="school-it-unassigned__search-icon" type="button" aria-label="Search">
              <Search :size="18" />
            </button>
          </div>

          <button class="school-it-unassigned__sort-pill" type="button" @click="toggleSort">
            <ChevronDown :size="18" :stroke-width="2.4" />
            Sort
          </button>
        </section>

        <section class="school-it-unassigned__main-card dashboard-enter dashboard-enter--4">
          <h2 class="school-it-unassigned__card-title">Students</h2>

          <div v-if="visibleStudents.length" class="school-it-unassigned__list">
            <article
              v-for="(student, index) in visibleStudents"
              :key="student.id"
              class="school-it-unassigned__row"
            >
              <div class="school-it-unassigned__row-info">
                <span class="school-it-unassigned__id-pill">{{ student.student_profile?.student_id_number || 'No ID' }}</span>
                <span class="school-it-unassigned__name">{{ getFullName(student) }}</span>
                <span 
                  v-if="hasPartialAssignment(student)" 
                  class="school-it-unassigned__warning"
                  title="Partially assigned"
                >
                  <AlertTriangle :size="16" />
                </span>
              </div>
              
              <div class="school-it-unassigned__row-actions">
                <button
                  class="school-it-unassigned__action school-it-unassigned__action--delete"
                  type="button"
                  aria-label="Delete student"
                  @click.stop="promptDeleteStudent(student)"
                >
                  <Trash2 :size="18" />
                </button>

                <button
                  class="school-it-unassigned__action school-it-unassigned__action--edit"
                  type="button"
                  aria-label="Edit student"
                  @click.stop="openEditSheet(student)"
                >
                  <Pencil :size="18" />
                </button>
              </div>
            </article>
          </div>

          <p v-else class="school-it-unassigned__empty">
            {{ emptyMessage }}
          </p>
        </section>
      </div>
    </div>

    <!-- Edit Assignment Sheet -->
    <Transition name="student-council-sheet">
      <div
        v-if="isEditSheetOpen"
        class="school-it-unassigned__sheet-backdrop"
        @click.self="closeEditSheet"
      >
        <div class="school-it-unassigned__sheet">
          <section class="school-it-unassigned__edit-panel">
            <div class="school-it-unassigned__edit-header">
              <h2 class="school-it-unassigned__edit-title">Assign Student</h2>
              <button
                class="school-it-unassigned__edit-close"
                type="button"
                @click="closeEditSheet"
              >
                <X :size="18" />
              </button>
            </div>

            <div class="school-it-unassigned__edit-form">
              <label class="school-it-unassigned__edit-label">College / Department</label>
              <select v-model="editDraft.departmentId" class="school-it-unassigned__edit-select">
                <option :value="null">None</option>
                <option v-for="dept in activeDepartments" :key="dept.id" :value="dept.id">
                  {{ dept.name }}
                </option>
              </select>

              <label class="school-it-unassigned__edit-label">Program</label>
              <select v-model="editDraft.programId" class="school-it-unassigned__edit-select" :disabled="!editDraft.departmentId">
                <option :value="null">None</option>
                <option v-for="prog in availableProgramsForEdit" :key="prog.id" :value="prog.id">
                  {{ prog.name }}
                </option>
              </select>
            </div>

            <button
              class="school-it-unassigned__save-btn"
              type="button"
              :disabled="isSaving"
              @click="saveStudentAssignment"
            >
              {{ isSaving ? 'Saving...' : 'Save Assignment' }}
            </button>
            
            <p v-if="saveError" class="school-it-unassigned__error">{{ saveError }}</p>
          </section>
        </div>
      </div>
    </Transition>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { AlertTriangle, ChevronDown, Pencil, Search, Trash2, X } from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSchoolItWorkspaceData } from '@/composables/useSchoolItWorkspaceData.js'
import { filterWorkspaceEntitiesBySchool } from '@/services/workspaceScope.js'
import { BackendApiError, deleteUser, updateStudentProfile } from '@/services/backendApi.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()
const { logout } = useAuth()
const { currentUser, schoolSettings, apiBaseUrl } = useDashboardSession()
const {
  users,
  departments,
  programs,
  statuses: workspaceStatuses,
  initializeSchoolItWorkspaceData,
  refreshSchoolItWorkspaceData,
  setUsersSnapshot,
} = useSchoolItWorkspaceData()

const searchQuery = ref('')
const sortAscending = ref(true)
const isEditSheetOpen = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)
const saveError = ref('')
const selectedStudent = ref(null)

const editDraft = ref({
  departmentId: null,
  programId: null,
})

const activeUser = computed(() => props.preview ? schoolItPreviewData.user : currentUser.value)
const activeSchoolSettings = computed(() => props.preview ? schoolItPreviewData.schoolSettings : schoolSettings.value)
const schoolId = computed(() => Number(activeUser.value?.school_id ?? activeSchoolSettings.value?.school_id))

const avatarUrl = computed(() => activeUser.value?.avatar_url || '')
const displayName = computed(() => {
  const first = activeUser.value?.first_name || ''
  const middle = activeUser.value?.middle_name || ''
  const last = activeUser.value?.last_name || ''
  return [first, middle, last].filter(Boolean).join(' ') || activeUser.value?.email?.split('@')[0] || 'School IT'
})
const initials = computed(() => {
  const parts = displayName.value.split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return displayName.value.slice(0, 2).toUpperCase()
})

const activeDepartments = computed(() => filterWorkspaceEntitiesBySchool(props.preview ? schoolItPreviewData.departments : departments.value, schoolId.value))
const activePrograms = computed(() => filterWorkspaceEntitiesBySchool(props.preview ? schoolItPreviewData.programs : programs.value, schoolId.value))
const activeUsers = computed(() => filterWorkspaceEntitiesBySchool(props.preview ? schoolItPreviewData.users : users.value, schoolId.value))

const availableProgramsForEdit = computed(() => {
  if (!editDraft.value.departmentId) return []
  return activePrograms.value.filter(p => Array.isArray(p.department_ids) && p.department_ids.includes(Number(editDraft.value.departmentId)))
})

const unassignedStudents = computed(() => {
  return activeUsers.value.filter(user => {
    const roles = Array.isArray(user?.roles) ? user.roles.map((r) => String(r?.role?.name || r?.name || '').toLowerCase()) : []
    const isStudent = Boolean(user?.student_profile) || roles.includes('student')
    if (!isStudent) return false
    
    const hasDept = !!user.student_profile?.department_id
    const hasProg = !!user.student_profile?.program_id
    return !hasDept || !hasProg
  })
})

const visibleStudents = computed(() => {
  let list = [...unassignedStudents.value]
  
  const query = searchQuery.value.trim().toLowerCase()
  if (query) {
    list = list.filter(s => getFullName(s).toLowerCase().includes(query) || String(s.student_profile?.student_id_number || '').toLowerCase().includes(query))
  }
  
  list.sort((a, b) => {
    const nameA = getFullName(a).toLowerCase()
    const nameB = getFullName(b).toLowerCase()
    return sortAscending.value ? nameA.localeCompare(nameB) : nameB.localeCompare(nameA)
  })
  
  return list
})

const emptyMessage = computed(() => {
  if (workspaceStatuses.value?.users === 'loading') return 'Loading students...'
  if (unassignedStudents.value.length === 0) return 'All students have been assigned.'
  if (searchQuery.value) return 'No unassigned students match your search.'
  return 'No unassigned students found.'
})

watch([apiBaseUrl, () => activeUser.value?.id, () => props.preview], async ([resolvedApiBaseUrl, userId, preview]) => {
  if (preview) return
  if (!resolvedApiBaseUrl || !userId) return
  await initializeSchoolItWorkspaceData()
}, { immediate: true })

watch(() => editDraft.value.departmentId, () => {
  editDraft.value.programId = null
})

function getFullName(user) {
  const first = user?.first_name || ''
  const last = user?.last_name || ''
  return [first, last].filter(Boolean).join(' ') || user?.email?.split('@')[0] || 'Unknown Student'
}

function hasPartialAssignment(user) {
  const hasDept = !!user.student_profile?.department_id
  const hasProg = !!user.student_profile?.program_id
  return (hasDept && !hasProg) || (!hasDept && hasProg)
}

function handleLogout() {
  logout()
}

function toggleSort() {
  sortAscending.value = !sortAscending.value
}

function promptDeleteStudent(student) {
  if (confirm(`Delete student ${getFullName(student)}?`)) {
    deleteStudent(student)
  }
}

async function deleteStudent(student) {
  if (isDeleting.value) return
  isDeleting.value = true
  
  try {
    if (!props.preview) {
      await deleteUser(apiBaseUrl.value, localStorage.getItem('aura_token') || '', student.id)
      const nextUsers = activeUsers.value.filter(u => Number(u.id) !== Number(student.id))
      setUsersSnapshot(nextUsers)
      refreshSchoolItWorkspaceData().catch(() => {})
    } else {
      alert('Delete simulated in preview mode.')
    }
  } catch (error) {
    alert(error?.message || 'Unable to delete student.')
  } finally {
    isDeleting.value = false
  }
}

function openEditSheet(student) {
  selectedStudent.value = student
  editDraft.value.departmentId = student.student_profile?.department_id || null
  editDraft.value.programId = student.student_profile?.program_id || null
  saveError.value = ''
  isEditSheetOpen.value = true
}

function closeEditSheet() {
  isEditSheetOpen.value = false
  selectedStudent.value = null
}

async function saveStudentAssignment() {
  if (!selectedStudent.value || isSaving.value) return
  
  isSaving.value = true
  saveError.value = ''
  
  try {
    if (!props.preview) {
      const token = localStorage.getItem('aura_token') || ''
      const profileId = selectedStudent.value.student_profile?.id
      if (!profileId) throw new Error('Student profile ID missing.')
      
      const payload = {
        department_id: editDraft.value.departmentId || null,
        program_id: editDraft.value.programId || null,
      }
      
      const updatedUser = await updateStudentProfile(apiBaseUrl.value, token, profileId, payload)
      
      const nextUsers = activeUsers.value.map(u => Number(u.id) === Number(updatedUser.id) ? updatedUser : u)
      setUsersSnapshot(nextUsers)
      refreshSchoolItWorkspaceData().catch(() => {})
    } else {
      // Simulate preview assignment
      alert(`Student assigned to Dept ${editDraft.value.departmentId}, Prog ${editDraft.value.programId} in preview.`)
    }
    closeEditSheet()
  } catch (error) {
    saveError.value = error instanceof BackendApiError ? error.message : 'Failed to update assignment.'
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
.school-it-unassigned { min-height: 100vh; padding: 30px 28px 120px; font-family: 'Manrope', sans-serif; }
.school-it-unassigned__shell { width: 100%; max-width: 1120px; margin: 0 auto; }
.school-it-unassigned__body { display: flex; flex-direction: column; gap: 24px; margin-top: 24px; }
.school-it-unassigned__title { margin: 0; font-size: 26px; font-weight: 800; line-height: 1; letter-spacing: -0.05em; color: var(--color-text-always-dark); }

.school-it-unassigned__toolbar { display: flex; align-items: stretch; gap: 14px; }
.school-it-unassigned__search-shell { flex: 1; min-width: 0; display: flex; align-items: center; background: #ffffff; border-radius: 999px; padding: 0 16px; height: 56px; }
.school-it-unassigned__search-input { flex: 1; border: none; background: transparent; outline: none; font-size: 14px; font-weight: 500; color: var(--color-text-always-dark); }
.school-it-unassigned__search-icon { display: inline-flex; align-items: center; justify-content: center; background: transparent; border: none; color: var(--color-primary); }

.school-it-unassigned__sort-pill { width: 110px; border: none; border-radius: 999px; background: var(--color-primary); color: var(--color-banner-text); display: inline-flex; align-items: center; justify-content: center; gap: 8px; font-size: 14px; font-weight: 700; cursor: pointer; transition: transform 0.2s ease, filter 0.2s ease; }
.school-it-unassigned__sort-pill:hover { filter: brightness(1.05); }
.school-it-unassigned__sort-pill:active { transform: scale(0.96); }

.school-it-unassigned__main-card { background: #ffffff; border-radius: 36px; padding: 32px 24px; display: flex; flex-direction: column; gap: 24px; box-shadow: 0 8px 24px rgba(0,0,0,0.04); }
.school-it-unassigned__card-title { margin: 0; font-size: 28px; font-weight: 800; color: var(--color-primary); letter-spacing: -0.04em; }

.school-it-unassigned__list { display: flex; flex-direction: column; gap: 16px; }
.school-it-unassigned__row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.school-it-unassigned__row-info { display: flex; align-items: center; gap: 16px; min-width: 0; flex: 1; }
.school-it-unassigned__id-pill { padding: 8px 16px; border-radius: 999px; background: var(--color-primary); color: var(--color-banner-text); font-size: 11px; font-weight: 800; white-space: nowrap; }
.school-it-unassigned__name { font-size: 14px; font-weight: 600; color: var(--color-text-always-dark); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.school-it-unassigned__warning { display: inline-flex; align-items: center; justify-content: center; color: #f5a623; }

.school-it-unassigned__row-actions { display: flex; align-items: center; gap: 16px; flex-shrink: 0; }
.school-it-unassigned__action { display: inline-flex; align-items: center; justify-content: center; border: none; background: transparent; cursor: pointer; transition: transform 0.2s ease, opacity 0.2s ease; opacity: 0.8; }
.school-it-unassigned__action:hover { opacity: 1; }
.school-it-unassigned__action:active { transform: scale(0.9); }
.school-it-unassigned__action--delete { color: #ff3b30; }
.school-it-unassigned__action--edit { color: var(--color-text-always-dark); }

.school-it-unassigned__empty { font-size: 14px; color: var(--color-text-muted); text-align: center; margin: 24px 0; }

.school-it-unassigned__sheet-backdrop { position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,0.4); display: flex; align-items: flex-end; }
.school-it-unassigned__sheet { width: 100%; max-height: 90vh; background: var(--color-surface); border-radius: 32px 32px 0 0; padding: 24px; box-shadow: 0 -8px 32px rgba(0,0,0,0.1); overflow-y: auto; }

.school-it-unassigned__edit-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.school-it-unassigned__edit-title { margin: 0; font-size: 20px; font-weight: 700; color: var(--color-text-always-dark); }
.school-it-unassigned__edit-close { border: none; background: transparent; color: var(--color-text-always-dark); cursor: pointer; }

.school-it-unassigned__edit-form { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }
.school-it-unassigned__edit-label { font-size: 13px; font-weight: 700; color: var(--color-primary); }
.school-it-unassigned__edit-select { width: 100%; height: 52px; border-radius: 12px; border: 1px solid var(--color-surface-border); background: var(--color-bg); padding: 0 16px; font-family: inherit; font-size: 14px; color: var(--color-text-always-dark); outline: none; }
.school-it-unassigned__edit-select:disabled { opacity: 0.5; cursor: not-allowed; }

.school-it-unassigned__save-btn { width: 100%; height: 56px; border-radius: 999px; background: var(--color-primary); color: var(--color-banner-text); font-size: 15px; font-weight: 700; border: none; cursor: pointer; transition: transform 0.2s ease; }
.school-it-unassigned__save-btn:active { transform: scale(0.98); }
.school-it-unassigned__save-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.school-it-unassigned__error { margin-top: 12px; font-size: 13px; color: #ff3b30; text-align: center; }

/* Transitions */
.student-council-sheet-enter-active, .student-council-sheet-leave-active { transition: opacity 0.4s ease; }
.student-council-sheet-enter-active .school-it-unassigned__sheet, .student-council-sheet-leave-active .school-it-unassigned__sheet { transition: transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1); }
.student-council-sheet-enter-from, .student-council-sheet-leave-to { opacity: 0; }
.student-council-sheet-enter-from .school-it-unassigned__sheet, .student-council-sheet-leave-to .school-it-unassigned__sheet { transform: translateY(100%); }

@media (min-width: 768px) {
  .school-it-unassigned { padding: 40px 36px; }
  .school-it-unassigned__toolbar { max-width: 600px; }
  .school-it-unassigned__main-card { max-width: 800px; padding: 40px; }
  .school-it-unassigned__sheet { max-width: 480px; margin: 0 auto 40px; border-radius: 32px; align-self: center; }
  .school-it-unassigned__sheet-backdrop { align-items: center; justify-content: center; }
}
</style>
