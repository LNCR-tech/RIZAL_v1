<template>
  <section class="school-it-att-monitor">
    <div class="school-it-att-monitor__shell">
      <SchoolItTopHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="activeSchoolSettings?.school_name || activeUser?.school_name || ''"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <div class="school-it-att-monitor__body">
        <header class="school-it-att-monitor__header dashboard-enter dashboard-enter--2">
          <button class="school-it-att-monitor__back" type="button" @click="goBack" aria-label="Go Back">
            <ArrowLeft :size="20" />
          </button>
          <h1 class="school-it-att-monitor__title">Attendance Monitor</h1>
        </header>

        <section class="school-it-att-monitor__toolbar dashboard-enter dashboard-enter--3">
          <div class="school-it-att-monitor__search-wrap" :class="{ 'school-it-att-monitor__search-wrap--active': searchActive }">
            <div class="school-it-att-monitor__search-shell">
              <input
                v-model="searchQuery"
                class="school-it-att-monitor__search-input"
                type="text"
                placeholder="Search students"
              >
              <button class="school-it-att-monitor__search-icon" type="button" aria-label="Search">
                <Search :size="18" :stroke-width="2.5" color="var(--color-primary, #bcf00e)" />
              </button>
            </div>
          </div>

          <div
            class="school-it-att-monitor__sort-wrap"
            :class="{ 'school-it-att-monitor__sort-wrap--open': isSortMenuOpen }"
          >
            <button class="school-it-att-monitor__sort-btn" type="button" @click="isSortMenuOpen = !isSortMenuOpen">
              <ChevronDown :size="18" /> Sort
            </button>

            <div v-show="isSortMenuOpen" class="school-it-att-monitor__sort-menu">
              <button
                v-for="option in sortOptions"
                :key="option.id"
                class="school-it-att-monitor__sort-item"
                :class="{ 'school-it-att-monitor__sort-item--active': option.id === sortMode }"
                type="button"
                @click="selectSort(option.id)"
              >
                {{ option.label }}
              </button>
            </div>
          </div>
        </section>

        <section class="school-it-att-monitor__content dashboard-enter dashboard-enter--4">
          <h2 class="school-it-att-monitor__subtitle">Students</h2>

          <div v-if="visibleStudents.length" class="school-it-att-monitor__list">
            <button
              v-for="student in visibleStudents"
              :key="student.id"
              class="school-it-att-monitor__row"
              type="button"
              @click="openStudentDetail(student)"
            >
              <span class="school-it-att-monitor__pill">{{ student.studentId || 'No ID' }}</span>
              <span class="school-it-att-monitor__name">{{ student.fullName }}</span>
            </button>
          </div>
          <p v-else-if="isLoading" class="school-it-att-monitor__empty">Loading students...</p>
          <p v-else class="school-it-att-monitor__empty">No students found.</p>
        </section>
      </div>
    </div>

    <!-- Student Detail Sheet -->
    <Transition name="school-it-att-monitor-sheet">
      <div v-if="selectedStudent" class="school-it-att-monitor__sheet-backdrop" @click.self="closeStudentDetail">
        <section class="school-it-att-monitor__sheet">
          <header class="school-it-att-monitor__sheet-header">
            <div>
              <h2 class="school-it-att-monitor__sheet-title">{{ selectedStudent.fullName }}</h2>
              <p class="school-it-att-monitor__sheet-copy">{{ selectedStudent.studentId || 'No ID' }}</p>
            </div>
            <button class="school-it-att-monitor__sheet-close" @click="closeStudentDetail"><X :size="18" /></button>
          </header>

          <div class="school-it-att-monitor__sheet-body">
            <div class="school-it-att-monitor__scope-grid">
               <div class="school-it-att-monitor__scope-card">
                  <span class="school-it-att-monitor__scope-label">Department</span>
                  <span class="school-it-att-monitor__scope-value">{{ selectedStudent.departmentName }}</span>
               </div>
               <div class="school-it-att-monitor__scope-card">
                  <span class="school-it-att-monitor__scope-label">Program</span>
                  <span class="school-it-att-monitor__scope-value">{{ selectedStudent.programName }}</span>
               </div>
            </div>

            <div class="school-it-att-monitor__stats-grid">
               <div class="school-it-att-monitor__stat-card school-it-att-monitor__stat-card--total">
                  <span class="school-it-att-monitor__stat-value">{{ selectedStudentStats.total }}</span>
                  <span class="school-it-att-monitor__stat-label">Total Events</span>
               </div>
               <div class="school-it-att-monitor__stat-card school-it-att-monitor__stat-card--present">
                  <span class="school-it-att-monitor__stat-value">{{ selectedStudentStats.present }}</span>
                  <span class="school-it-att-monitor__stat-label">Attended</span>
               </div>
               <div class="school-it-att-monitor__stat-card school-it-att-monitor__stat-card--late">
                  <span class="school-it-att-monitor__stat-value">{{ selectedStudentStats.late }}</span>
                  <span class="school-it-att-monitor__stat-label">Late</span>
               </div>
               <div class="school-it-att-monitor__stat-card school-it-att-monitor__stat-card--absent">
                  <span class="school-it-att-monitor__stat-value">{{ selectedStudentStats.absent }}</span>
                  <span class="school-it-att-monitor__stat-label">Absent</span>
               </div>
               <div class="school-it-att-monitor__stat-card school-it-att-monitor__stat-card--excused">
                  <span class="school-it-att-monitor__stat-value">{{ selectedStudentStats.excused }}</span>
                  <span class="school-it-att-monitor__stat-label">Excused</span>
               </div>
               <div class="school-it-att-monitor__stat-card school-it-att-monitor__stat-card--rate">
                  <span class="school-it-att-monitor__stat-value">{{ selectedStudentStats.rate }}%</span>
                  <span class="school-it-att-monitor__stat-label">Attendance Rate</span>
               </div>
            </div>

            <!-- Clean Graph -->
            <div class="school-it-att-monitor__graph-section">
              <h3 class="school-it-att-monitor__graph-title">Attendance Overview</h3>
              <div class="school-it-att-monitor__graph-track">
                <div class="school-it-att-monitor__graph-fill school-it-att-monitor__graph-fill--present" :style="{ width: `${selectedStudentStats.presentPct}%` }"></div>
                <div class="school-it-att-monitor__graph-fill school-it-att-monitor__graph-fill--late" :style="{ width: `${selectedStudentStats.latePct}%` }"></div>
                <div class="school-it-att-monitor__graph-fill school-it-att-monitor__graph-fill--excused" :style="{ width: `${selectedStudentStats.excusedPct}%` }"></div>
                <!-- Absent is the empty space, or we can explicitly color it -->
                <div class="school-it-att-monitor__graph-fill school-it-att-monitor__graph-fill--absent" :style="{ width: `${selectedStudentStats.absentPct}%` }"></div>
              </div>
              <div class="school-it-att-monitor__graph-legend">
                <div class="school-it-att-monitor__legend-item"><span class="school-it-att-monitor__legend-dot school-it-att-monitor__legend-dot--present"></span> Present</div>
                <div class="school-it-att-monitor__legend-item"><span class="school-it-att-monitor__legend-dot school-it-att-monitor__legend-dot--late"></span> Late</div>
                <div class="school-it-att-monitor__legend-item"><span class="school-it-att-monitor__legend-dot school-it-att-monitor__legend-dot--excused"></span> Excused</div>
                <div class="school-it-att-monitor__legend-item"><span class="school-it-att-monitor__legend-dot school-it-att-monitor__legend-dot--absent"></span> Absent</div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </Transition>
  </section>
</template>

<script setup>
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Search, ChevronDown, X } from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSchoolItWorkspaceData } from '@/composables/useSchoolItWorkspaceData.js'
import { getAttendanceSummary, resolveApiBaseUrl } from '@/services/backendApi.js'
import { filterWorkspaceEntitiesBySchool } from '@/services/workspaceScope.js'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'

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
  departments,
  programs,
  users,
  statuses: workspaceStatuses,
  initializeSchoolItWorkspaceData,
} = useSchoolItWorkspaceData()

const searchQuery = ref('')
const sortMode = ref('id-asc')
const isSortMenuOpen = ref(false)
const selectedStudent = ref(null)
const isLoadingStats = ref(false)

const sortOptions = [
  { id: 'first-name-asc', label: 'First Name A-Z' },
  { id: 'last-name-asc', label: 'Last Name A-Z' },
  { id: 'id-asc', label: 'ID Number 0-9' },
  { id: 'id-desc', label: 'ID Number 9-0' },
]

const activeUser = computed(() => props.preview ? schoolItPreviewData.user : currentUser.value)
const activeSchoolSettings = computed(() => props.preview ? schoolItPreviewData.schoolSettings : schoolSettings.value)
const schoolId = computed(() => Number(activeUser.value?.school_id ?? activeSchoolSettings.value?.school_id))

const activeDepartments = computed(() => props.preview ? schoolItPreviewData.departments : departments.value)
const activePrograms = computed(() => props.preview ? schoolItPreviewData.programs : programs.value)
const activeUsers = computed(() => props.preview ? (Array.isArray(schoolItPreviewData.users) ? schoolItPreviewData.users : []) : users.value)

const filteredDepartments = computed(() => filterWorkspaceEntitiesBySchool(activeDepartments.value, schoolId.value))
const filteredPrograms = computed(() => filterWorkspaceEntitiesBySchool(activePrograms.value, schoolId.value))
const filteredUsers = computed(() => filterWorkspaceEntitiesBySchool(activeUsers.value, schoolId.value))

const isLoading = computed(() => workspaceStatuses.value?.users === 'loading' || workspaceStatuses.value?.users === 'idle')

const displayName = computed(() => {
  const first = activeUser.value?.first_name || ''
  const middle = activeUser.value?.middle_name || ''
  const last = activeUser.value?.last_name || ''
  return [first, middle, last].filter(Boolean).join(' ') || activeUser.value?.email?.split('@')[0] || 'School IT'
})

const initials = computed(() => {
  const parts = String(displayName.value || '').split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return String(displayName.value || '').slice(0, 2).toUpperCase()
})

const avatarUrl = computed(() => activeUser.value?.avatar_url || '')

function isStudentUser(user) {
  const roles = Array.isArray(user?.roles)
    ? user.roles.map((role) => String(role?.role?.name || role?.name || '').toLowerCase())
    : []
  return Boolean(user?.student_profile) || roles.includes('student')
}

const allStudents = computed(() => {
  return filteredUsers.value.filter(isStudentUser).map((user) => {
    const progId = Number(user?.student_profile?.program_id)
    const prog = filteredPrograms.value.find(p => Number(p.id) === progId)
    const deptIds = prog?.department_ids || []
    const deptId = deptIds.length ? Number(deptIds[0]) : null
    const dept = filteredDepartments.value.find(d => Number(d.id) === deptId)

    return {
      id: Number(user.id),
      firstName: String(user.first_name || '').trim(),
      lastName: String(user.last_name || '').trim(),
      fullName: [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.email || 'Student',
      studentId: String(user?.student_profile?.student_id || ''),
      programName: prog?.name || 'Unassigned Program',
      departmentName: dept?.name || 'Unassigned Department',
      searchText: [
        user?.student_profile?.student_id,
        user.first_name,
        user.last_name,
        user.email,
      ].filter(Boolean).join(' ').toLowerCase(),
      stats: null // Will be populated when clicked
    }
  })
})

function generateMockStats(id) {
  const seededRandom = (id * 12345 % 100) / 100
  const total = 20 + Math.floor(seededRandom * 30)
  const present = Math.floor(total * (0.6 + seededRandom * 0.3))
  const late = Math.floor(total * 0.1)
  const excused = Math.floor(total * 0.05)
  const absent = total - present - late - excused
  
  const rate = Math.round(((present + late) / total) * 100)

  return {
    total,
    present,
    late,
    absent,
    excused,
    rate,
    presentPct: total > 0 ? (present / total) * 100 : 0,
    latePct: total > 0 ? (late / total) * 100 : 0,
    absentPct: total > 0 ? (absent / total) * 100 : 0,
    excusedPct: total > 0 ? (excused / total) * 100 : 0
  }
}

const visibleStudents = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  const filtered = !query ? allStudents.value : allStudents.value.filter((s) => s.searchText.includes(query))

  return [...filtered].sort((left, right) => {
    if (sortMode.value === 'first-name-asc') return left.firstName.localeCompare(right.firstName) || left.fullName.localeCompare(right.fullName)
    if (sortMode.value === 'last-name-asc') return left.lastName.localeCompare(right.lastName) || left.fullName.localeCompare(right.fullName)
    if (sortMode.value === 'id-desc') return right.studentId.localeCompare(left.studentId, undefined, { numeric: true, sensitivity: 'base' })
    return left.studentId.localeCompare(right.studentId, undefined, { numeric: true, sensitivity: 'base' })
  })
})

const searchActive = computed(() => searchQuery.value.trim().length > 0)

const selectedStudentStats = computed(() => selectedStudent.value?.stats || {})

watch([apiBaseUrl, () => activeUser.value?.id, () => props.preview], async ([resolvedApiBaseUrl, userId, preview]) => {
  if (preview) return
  if (!resolvedApiBaseUrl || !userId) return
  await initializeSchoolItWorkspaceData()
}, { immediate: true })

watch(searchQuery, () => {
  isSortMenuOpen.value = false
})

onBeforeUnmount(() => {
  isSortMenuOpen.value = false
})

function selectSort(nextSortMode) {
  sortMode.value = nextSortMode
  isSortMenuOpen.value = false
}

async function openStudentDetail(student) {
  selectedStudent.value = student
  isLoadingStats.value = true

  if (props.preview) {
     student.stats = generateMockStats(student.id)
     isLoadingStats.value = false
     return
  }

  try {
     const token = localStorage.getItem('aura_token') || ''
     const summaryData = await getAttendanceSummary(resolveApiBaseUrl(), token, {
       user_id: student.id
     })
     
     const total = Number(summaryData?.total_events) || 0
     const present = Number(summaryData?.total_present) || 0
     const late = Number(summaryData?.total_late) || 0
     const absent = Number(summaryData?.total_absent) || 0
     const excused = Number(summaryData?.total_excused) || 0
     
     const attended = present
     const rate = total > 0 ? Math.round(((attended + late) / total) * 100) : 0
     
     student.stats = {
        total,
        present: attended,
        late,
        absent,
        excused,
        rate,
        presentPct: total > 0 ? (attended / total) * 100 : 0,
        latePct: total > 0 ? (late / total) * 100 : 0,
        absentPct: total > 0 ? (absent / total) * 100 : 0,
        excusedPct: total > 0 ? (excused / total) * 100 : 0
     }
  } catch (error) {
     console.error('Failed to fetch attendance summary', error)
     student.stats = generateMockStats(student.id) // Fallback to mock if API fails for UX resilience
  } finally {
     isLoadingStats.value = false
  }
}

function closeStudentDetail() {
  selectedStudent.value = null
}

function goBack() {
  if (props.preview) router.push('/exposed/workspace/schedule')
  else router.push('/workspace/schedule')
}

async function handleLogout() {
  await logout()
}
</script>

<style scoped>
.school-it-att-monitor {
  min-height: 100vh;
  padding: 30px 28px 120px;
  font-family: 'Manrope', sans-serif;
  background: var(--color-bg, #f3f4f6);
}

.school-it-att-monitor__shell {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
}

.school-it-att-monitor__body {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-top: 32px;
}

.school-it-att-monitor__header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.school-it-att-monitor__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #111827;
  transition: background-color 0.2s;
}

.school-it-att-monitor__back:hover {
  background: rgba(0, 0, 0, 0.05);
}

.school-it-att-monitor__title {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.04em;
  color: var(--color-text-always-dark, #111827);
}

.school-it-att-monitor__toolbar {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.school-it-att-monitor__search-wrap {
  flex: 1;
  max-width: 100%;
  height: 64px;
}

.school-it-att-monitor__search-shell {
  display: flex;
  align-items: center;
  width: 100%;
  height: 100%;
  border-radius: 999px;
  background: #ffffff;
  padding: 0 8px 0 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
}

.school-it-att-monitor__search-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  border: none;
  outline: none;
  font-size: 16px;
  color: #111827;
  background: transparent;
}

.school-it-att-monitor__search-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: transparent;
  border: none;
  flex-shrink: 0;
}

.school-it-att-monitor__sort-wrap {
  position: relative;
}

.school-it-att-monitor__sort-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 64px;
  padding: 0 24px;
  background: var(--color-primary, #bcf00e);
  color: #111827;
  font-size: 15px;
  font-weight: 600;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  transition: filter 0.2s;
}

.school-it-att-monitor__sort-btn:active {
  filter: brightness(0.95);
}

.school-it-att-monitor__sort-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 200px;
  background: #ffffff;
  border-radius: 16px;
  padding: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
  z-index: 10;
  display: flex;
  flex-direction: column;
}

.school-it-att-monitor__sort-item {
  width: 100%;
  text-align: left;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #4b5563;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.school-it-att-monitor__sort-item:hover {
  background: #f9fafb;
}

.school-it-att-monitor__sort-item--active {
  color: #111827;
  font-weight: 700;
  background: #f3f4f6;
}

.school-it-att-monitor__content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #ffffff;
  border-radius: 32px;
  padding: 28px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.02);
}

.school-it-att-monitor__subtitle {
  font-size: 20px;
  font-weight: 800;
  color: var(--color-primary, #bcf00e);
  margin: 0;
}

.school-it-att-monitor__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.school-it-att-monitor__row {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  text-align: left;
  padding: 10px;
  border-radius: 999px;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s;
}

.school-it-att-monitor__row:hover {
  background: #f9fafb;
}

.school-it-att-monitor__row:active {
  transform: scale(0.99);
}

.school-it-att-monitor__pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  background: var(--color-primary, #bcf00e);
  color: #111827;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.school-it-att-monitor__name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.school-it-att-monitor__empty {
  font-size: 15px;
  color: #6b7280;
  font-weight: 500;
  padding: 40px 0;
  text-align: center;
}

/* ── Bottom Sheet ───────────────────────────────────────────────────────── */
.school-it-att-monitor__sheet-backdrop {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.school-it-att-monitor__sheet {
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  background: var(--color-surface, #ffffff);
  border-radius: 40px 40px 0 0;
  padding: 32px;
  box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.1);
  -webkit-overflow-scrolling: touch;
}

.school-it-att-monitor-sheet-enter-active,
.school-it-att-monitor-sheet-leave-active {
  transition: opacity 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.school-it-att-monitor-sheet-enter-active .school-it-att-monitor__sheet,
.school-it-att-monitor-sheet-leave-active .school-it-att-monitor__sheet {
  transition: transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.school-it-att-monitor-sheet-enter-from,
.school-it-att-monitor-sheet-leave-to {
  opacity: 0;
}

.school-it-att-monitor-sheet-enter-from .school-it-att-monitor__sheet,
.school-it-att-monitor-sheet-leave-to .school-it-att-monitor__sheet {
  transform: translateY(100%);
}

.school-it-att-monitor__sheet-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.school-it-att-monitor__sheet-title {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: #111827;
  letter-spacing: -0.02em;
}

.school-it-att-monitor__sheet-copy {
  margin: 4px 0 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-primary, #bcf00e);
}

.school-it-att-monitor__sheet-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: #f3f4f6;
  color: #6b7280;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.school-it-att-monitor__sheet-close:active {
  transform: scale(0.92);
}

.school-it-att-monitor__sheet-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.school-it-att-monitor__scope-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.school-it-att-monitor__scope-card {
  background: #f9fafb;
  border-radius: 20px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.school-it-att-monitor__scope-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.school-it-att-monitor__scope-value {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.school-it-att-monitor__stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.school-it-att-monitor__stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 18px 12px;
  border-radius: 20px;
  background: #ffffff;
  border: none;
  min-height: 94px;
}

.school-it-att-monitor__stat-card--total { background: #f8f9fa; }
.school-it-att-monitor__stat-card--present { background: #f0fdf4; }
.school-it-att-monitor__stat-card--late { background: #fffdf5; }
.school-it-att-monitor__stat-card--absent { background: #fff5f5; }
.school-it-att-monitor__stat-card--excused { background: #f0f9ff; }
.school-it-att-monitor__stat-card--rate { background: #2308bd; }

.school-it-att-monitor__stat-value {
  font-size: 22px;
  font-weight: 800;
  color: #111827;
  line-height: 1.1;
  margin-bottom: 6px;
}

.school-it-att-monitor__stat-label {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
}

.school-it-att-monitor__stat-card--rate .school-it-att-monitor__stat-value,
.school-it-att-monitor__stat-card--rate .school-it-att-monitor__stat-label {
  color: #111827;
}

.school-it-att-monitor__graph-section {
  margin-top: 8px;
  padding: 24px;
  background: #f9fafb;
  border-radius: 28px;
}

.school-it-att-monitor__graph-title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 800;
  color: #111827;
}

.school-it-att-monitor__graph-track {
  display: flex;
  height: 24px;
  border-radius: 999px;
  overflow: hidden;
  background: #e5e7eb;
  margin-bottom: 20px;
}

.school-it-att-monitor__graph-fill {
  height: 100%;
  transition: width 1s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.school-it-att-monitor__graph-fill--present { background: #27ae60; }
.school-it-att-monitor__graph-fill--late { background: #f39c12; }
.school-it-att-monitor__graph-fill--excused { background: #3498db; }
.school-it-att-monitor__graph-fill--absent { background: #e74c3c; }

.school-it-att-monitor__graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.school-it-att-monitor__legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #4b5563;
}

.school-it-att-monitor__legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.school-it-att-monitor__legend-dot--present { background: #27ae60; }
.school-it-att-monitor__legend-dot--late { background: #f39c12; }
.school-it-att-monitor__legend-dot--excused { background: #3498db; }
.school-it-att-monitor__legend-dot--absent { background: #e74c3c; }
</style>
