<template>
  <section class="sg-sub-page">
    <header class="sg-sub-header dashboard-enter dashboard-enter--1">
      <button class="sg-sub-back" type="button" @click="goBack">
        <ArrowLeft :size="20" />
      </button>
      <h1 class="sg-sub-title">{{ readOnly ? 'View Students' : 'Manage Students' }}</h1>
    </header>

    <div v-if="isLoading" class="sg-sub-loading dashboard-enter dashboard-enter--2">
      <p>Loading students...</p>
    </div>

    <div v-else-if="loadError" class="sg-sub-error dashboard-enter dashboard-enter--2">
      <p>{{ loadError }}</p>
      <button class="sg-sub-action" type="button" @click="reload">Try Again</button>
    </div>

    <template v-else>
      <div class="sg-sub-toolbar dashboard-enter dashboard-enter--2">
        <div class="sg-sub-search-shell">
          <input
            v-model="searchQuery"
            type="text"
            class="sg-sub-search-input"
            placeholder="Search students"
          />
          <Search :size="14" style="color: var(--color-text-muted);" />
        </div>
      </div>

      <div class="sg-sub-card dashboard-enter dashboard-enter--3">
        <h2 class="sg-sub-card-title">Students ({{ filteredStudents.length }})</h2>
        <div v-if="filteredStudents.length" class="sg-students-list">
          <article
            v-for="student in filteredStudents"
            :key="student.user_id || student.id"
            class="sg-student-row"
          >
            <span class="sg-student-id">{{ studentProfile(student)?.student_id || student.id }}</span>
            <div class="sg-student-info">
              <span class="sg-student-name">{{ studentName(student) }}</span>
              <span class="sg-student-email">{{ studentUser(student)?.email || '' }}</span>
            </div>
          </article>
        </div>
        <p v-else class="sg-sub-empty">No students found.</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Search } from 'lucide-vue-next'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import { getGovernanceStudents } from '@/services/backendApi.js'
import { withPreservedGovernancePreviewQuery } from '@/services/routeWorkspace.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()
const { apiBaseUrl } = useDashboardSession()
const { previewBundle } = useSgPreviewBundle(() => props.preview)
const { permissionCodes, isLoading: sgLoading } = useSgDashboard(props.preview)

const isLoading = ref(true)
const loadError = ref('')
const students = ref([])
const searchQuery = ref('')

const readOnly = computed(() => {
  const codes = new Set(permissionCodes.value)
  return !codes.has('manage_students') && codes.has('view_students')
})

const filteredStudents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return students.value
  return students.value.filter((s) =>
    [
      studentProfile(s)?.student_id,
      studentUser(s)?.first_name,
      studentUser(s)?.last_name,
      studentUser(s)?.email,
      studentProfile(s)?.department_name,
      studentProfile(s)?.program_name,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
      .includes(q)
  )
})

function studentUser(student) {
  return student?.user || student || null
}

function studentProfile(student) {
  return student?.student_profile || student?.user?.student_profile || null
}

function studentName(s) {
  const user = studentUser(s)
  return [user?.first_name, user?.last_name].filter(Boolean).join(' ').trim() || user?.email || 'Student'
}

function goBack() {
  router.push(
    props.preview
      ? withPreservedGovernancePreviewQuery(route, '/exposed/governance')
      : '/governance'
  )
}

watch(
  [apiBaseUrl, () => sgLoading.value, () => route.query?.variant],
  async ([url]) => {
    if (!url || sgLoading.value) return
    await loadStudents(url)
  },
  { immediate: true }
)

async function loadStudents(url) {
  isLoading.value = true
  loadError.value = ''
  try {
    if (props.preview) {
      students.value = Array.isArray(previewBundle.value?.students)
        ? previewBundle.value.students.map((student) => ({ ...student }))
        : []
      return
    }

    const token = localStorage.getItem('aura_token') || ''
    students.value = await getGovernanceStudents(url, token)
  } catch (e) {
    loadError.value = e?.message || 'Unable to load students.'
  } finally {
    isLoading.value = false
  }
}

async function reload() {
  if (apiBaseUrl.value) await loadStudents(apiBaseUrl.value)
}
</script>

<style scoped>
@import '@/assets/css/sg-sub-views.css';

.sg-students-list { display: flex; flex-direction: column; gap: 2px; }
.sg-student-row { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 14px; }
.sg-student-row:nth-child(odd) { background: var(--color-surface-border); }
.sg-student-id { font-size: 12px; font-weight: 700; color: var(--color-primary); background: var(--color-surface); padding: 4px 10px; border-radius: 10px; white-space: nowrap; }
.sg-student-info { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.sg-student-name { font-size: 14px; font-weight: 600; color: var(--color-text-primary); }
.sg-student-email { font-size: 12px; color: var(--color-text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
