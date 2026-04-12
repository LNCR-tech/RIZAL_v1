<template>
  <section class="sg-sub-page">
    <header class="sg-sub-header dashboard-enter dashboard-enter--1">
      <button class="sg-sub-back" type="button" @click="goBack">
        <ArrowLeft :size="20" />
      </button>
      <h1 class="sg-sub-title">Sanctioned Students</h1>
    </header>

    <div v-if="isLoading" class="sg-sub-loading dashboard-enter dashboard-enter--2">
      <p>Loading sanctioned students...</p>
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
            placeholder="Search student, email, ID"
          >
          <Search :size="14" style="color: var(--color-text-muted);" />
        </div>

        <button class="sg-sub-action" type="button" :disabled="isExporting" @click="exportExcel">
          <Download :size="14" />
          <span>{{ isExporting ? 'Exporting...' : 'Export Excel' }}</span>
        </button>
      </div>

      <div class="sg-sub-card dashboard-enter dashboard-enter--3">
        <div class="sanctions-filters">
          <label class="sanctions-filter-field">
            <span>Status</span>
            <select v-model="statusFilter">
              <option value="all">All</option>
              <option value="pending">Pending</option>
              <option value="complied">Complied</option>
            </select>
          </label>

          <label class="sanctions-filter-field">
            <span>Department</span>
            <select v-model="departmentFilter">
              <option value="">All</option>
              <option v-for="department in departmentOptions" :key="department" :value="department">
                {{ department }}
              </option>
            </select>
          </label>

          <label class="sanctions-filter-field">
            <span>Course</span>
            <select v-model="programFilter">
              <option value="">All</option>
              <option v-for="program in programOptions" :key="program" :value="program">
                {{ program }}
              </option>
            </select>
          </label>

          <label class="sanctions-filter-field">
            <span>Year</span>
            <select v-model="yearFilter">
              <option value="">All</option>
              <option v-for="year in yearOptions" :key="year" :value="String(year)">
                {{ year }}
              </option>
            </select>
          </label>
        </div>
      </div>

      <div class="sg-sub-card dashboard-enter dashboard-enter--4">
        <h2 class="sg-sub-card-title">Students ({{ filteredRecords.length }})</h2>

        <div v-if="pagedRecords.length" class="sanctions-table-wrap">
          <table class="sanctions-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Department</th>
                <th>Course</th>
                <th>Year</th>
                <th>Status</th>
                <th>Items</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="record in pagedRecords" :key="record.id">
                <td>
                  <button class="sanctions-link" type="button" @click="openStudent(record.student.user_id)">
                    <strong>{{ formatStudentName(record.student) }}</strong>
                    <span>{{ record.student.student_id || record.student.email }}</span>
                  </button>
                </td>
                <td>{{ record.student.department_name || 'N/A' }}</td>
                <td>{{ record.student.program_name || 'N/A' }}</td>
                <td>{{ record.student.year_level || 'N/A' }}</td>
                <td>
                  <span class="sanctions-status" :class="`sanctions-status--${record.status}`">
                    {{ record.status }}
                  </span>
                </td>
                <td>{{ record.items.length }}</td>
                <td class="sanctions-actions">
                  <button
                    class="sg-sub-action"
                    type="button"
                    :disabled="isApprovingUserId === record.student.user_id || record.status !== 'pending'"
                    @click="approveStudent(record)"
                  >
                    {{ isApprovingUserId === record.student.user_id ? 'Approving...' : 'Approve' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-else class="sg-sub-empty">No sanctioned students match your filters.</p>

        <div v-if="totalPages > 1" class="sanctions-pagination">
          <button
            class="sanctions-page-btn"
            type="button"
            :disabled="currentPage === 1"
            @click="currentPage -= 1"
          >
            Previous
          </button>
          <span>Page {{ currentPage }} / {{ totalPages }}</span>
          <button
            class="sanctions-page-btn"
            type="button"
            :disabled="currentPage === totalPages"
            @click="currentPage += 1"
          >
            Next
          </button>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Download, Search } from 'lucide-vue-next'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import {
  approveEventStudentSanction,
  downloadEventSanctionsExport,
  getEventSanctionedStudents,
} from '@/services/backendApi.js'
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
const { isLoading: sgLoading } = useSgDashboard(props.preview)
const { previewBundle } = useSgPreviewBundle(() => props.preview)

const isLoading = ref(true)
const loadError = ref('')
const records = ref([])
const searchQuery = ref('')
const statusFilter = ref('all')
const departmentFilter = ref('')
const programFilter = ref('')
const yearFilter = ref('')
const currentPage = ref(1)
const pageSize = 20
const isApprovingUserId = ref(null)
const isExporting = ref(false)

const eventId = computed(() => Number(route.params.eventId))

const departmentOptions = computed(() => [...new Set(
  records.value
    .map((record) => String(record?.student?.department_name || '').trim())
    .filter(Boolean)
)].sort())

const programOptions = computed(() => [...new Set(
  records.value
    .map((record) => String(record?.student?.program_name || '').trim())
    .filter(Boolean)
)].sort())

const yearOptions = computed(() => [...new Set(
  records.value
    .map((record) => Number(record?.student?.year_level))
    .filter(Number.isFinite)
)].sort((left, right) => left - right))

const filteredRecords = computed(() => {
  const search = String(searchQuery.value || '').trim().toLowerCase()
  const department = String(departmentFilter.value || '').trim().toLowerCase()
  const program = String(programFilter.value || '').trim().toLowerCase()
  const year = String(yearFilter.value || '').trim()

  return records.value.filter((record) => {
    const student = record.student || {}
    const fullName = formatStudentName(student).toLowerCase()
    const recordSearchBlob = [
      fullName,
      student.student_id,
      student.email,
      student.department_name,
      student.program_name,
      record.status,
    ].filter(Boolean).join(' ').toLowerCase()

    if (search && !recordSearchBlob.includes(search)) return false
    if (department && String(student.department_name || '').trim().toLowerCase() !== department) return false
    if (program && String(student.program_name || '').trim().toLowerCase() !== program) return false
    if (year && String(student.year_level || '') !== year) return false
    return true
  })
})

const totalPages = computed(() => (
  Math.max(1, Math.ceil(filteredRecords.value.length / pageSize))
))

const pagedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredRecords.value.slice(start, start + pageSize)
})

watch(
  [statusFilter, searchQuery, departmentFilter, programFilter, yearFilter],
  () => {
    currentPage.value = 1
  }
)

watch(
  [eventId, apiBaseUrl, () => sgLoading.value, () => route.query?.variant, statusFilter],
  async ([resolvedEventId, url]) => {
    if (!url || sgLoading.value || !Number.isFinite(resolvedEventId)) return
    await loadRecords(url)
  },
  { immediate: true }
)

function formatStudentName(student = null) {
  const firstName = String(student?.first_name || '').trim()
  const middleName = String(student?.middle_name || '').trim()
  const lastName = String(student?.last_name || '').trim()
  return [firstName, middleName, lastName].filter(Boolean).join(' ') || student?.email || 'Student'
}

function goBack() {
  if (props.preview) {
    router.push(withPreservedGovernancePreviewQuery(route, '/exposed/governance/events/sanctions'))
    return
  }
  router.push('/governance/events/sanctions')
}

function openStudent(userId) {
  if (props.preview) {
    router.push(withPreservedGovernancePreviewQuery(route, {
      name: 'PreviewSgStudentSanctionDetail',
      params: {
        eventId: String(eventId.value),
        userId: String(userId),
      },
    }))
    return
  }

  router.push({
    name: 'SgStudentSanctionDetail',
    params: {
      eventId: String(eventId.value),
      userId: String(userId),
    },
  })
}

function buildPreviewRecords(bundle = null, resolvedEventId = null) {
  const previewStudents = Array.isArray(bundle?.students) ? bundle.students : []

  return previewStudents.slice(0, 40).map((student, index) => {
    const pending = index % 3 !== 0
    return {
      id: 9000 + index,
      event_id: resolvedEventId,
      status: pending ? 'pending' : 'complied',
      notes: pending ? 'Pending validation by assigned governance member.' : 'Approved in preview mode.',
      complied_at: pending ? null : new Date(Date.now() - (index * 3600000)).toISOString(),
      assigned_by_user_id: 0,
      delegated_governance_unit_id: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      student: {
        user_id: Number(student?.id),
        student_profile_id: Number(student?.student_profile?.id ?? student?.id ?? index + 1),
        student_id: String(student?.student_profile?.student_id || student?.id || ''),
        email: String(student?.email || ''),
        first_name: String(student?.first_name || ''),
        middle_name: String(student?.middle_name || ''),
        last_name: String(student?.last_name || ''),
        department_name: student?.student_profile?.department_name || null,
        program_name: student?.student_profile?.program_name || null,
        year_level: student?.student_profile?.year_level || null,
      },
      items: [
        {
          id: (index + 1) * 10 + 1,
          item_name: 'Community Service',
          status: pending ? 'pending' : 'complied',
        },
        {
          id: (index + 1) * 10 + 2,
          item_name: 'Reflection Paper',
          status: pending ? 'pending' : 'complied',
        },
      ],
    }
  })
}

async function loadRecords(url) {
  isLoading.value = true
  loadError.value = ''

  try {
    if (props.preview) {
      records.value = buildPreviewRecords(previewBundle.value, eventId.value)
      return
    }

    const response = await getEventSanctionedStudents(url, token.value, eventId.value, {
      skip: 0,
      limit: 250,
      status: statusFilter.value === 'all' ? null : statusFilter.value,
    })
    records.value = Array.isArray(response?.items) ? response.items : []
  } catch (error) {
    loadError.value = error?.message || 'Unable to load sanctioned students.'
  } finally {
    isLoading.value = false
  }
}

async function approveStudent(record) {
  if (!record?.student?.user_id || record.status !== 'pending') return

  if (props.preview) {
    records.value = records.value.map((entry) => (
      entry.id === record.id
        ? {
          ...entry,
          status: 'complied',
          complied_at: new Date().toISOString(),
          items: entry.items.map((item) => ({ ...item, status: 'complied' })),
        }
        : entry
    ))
    return
  }

  isApprovingUserId.value = record.student.user_id
  try {
    const updated = await approveEventStudentSanction(
      apiBaseUrl.value,
      token.value,
      eventId.value,
      record.student.user_id
    )
    records.value = records.value.map((entry) => (
      entry.id === updated.id ? updated : entry
    ))
  } catch (error) {
    loadError.value = error?.message || 'Unable to approve sanction compliance.'
  } finally {
    isApprovingUserId.value = null
  }
}

async function exportExcel() {
  if (!Number.isFinite(eventId.value) || isExporting.value) return

  isExporting.value = true
  try {
    if (props.preview) {
      const blob = new Blob(['Preview sanctions export'], { type: 'text/plain;charset=utf-8;' })
      triggerBlobDownload(blob, `sanctions_event_${eventId.value}_preview.txt`)
      return
    }

    const blob = await downloadEventSanctionsExport(apiBaseUrl.value, token.value, eventId.value)
    triggerBlobDownload(blob, `sanctions_event_${eventId.value}.xlsx`)
  } catch (error) {
    loadError.value = error?.message || 'Unable to export sanctions report.'
  } finally {
    isExporting.value = false
  }
}

function triggerBlobDownload(blob, fileName) {
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = fileName
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(objectUrl)
}

async function reload() {
  if (!apiBaseUrl.value) return
  await loadRecords(apiBaseUrl.value)
}
</script>

<style scoped>
@import '@/assets/css/sg-sub-views.css';

.sanctions-filters {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.sanctions-filter-field {
  display: grid;
  gap: 6px;
}

.sanctions-filter-field span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.sanctions-filter-field select {
  width: 100%;
  min-height: 40px;
  border: 1px solid color-mix(in srgb, var(--color-text-muted) 20%, transparent);
  border-radius: 12px;
  background: #fff;
  padding: 0 10px;
  font-family: inherit;
  font-size: 13px;
  color: var(--color-text-primary);
  outline: none;
}

.sanctions-table-wrap {
  overflow-x: auto;
}

.sanctions-table {
  width: 100%;
  min-width: 840px;
  border-collapse: collapse;
}

.sanctions-table thead th {
  text-align: left;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  padding: 0 10px 10px;
}

.sanctions-table tbody td {
  padding: 12px 10px;
  border-top: 1px solid color-mix(in srgb, var(--color-text-muted) 18%, transparent);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.sanctions-link {
  border: none;
  background: transparent;
  padding: 0;
  display: grid;
  gap: 3px;
  text-align: left;
  cursor: pointer;
}

.sanctions-link strong {
  font-size: 13px;
}

.sanctions-link span {
  font-size: 11px;
  color: var(--color-text-muted);
}

.sanctions-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.sanctions-status--pending {
  color: #b45309;
  background: rgba(245, 158, 11, 0.14);
}

.sanctions-status--complied {
  color: #166534;
  background: rgba(34, 197, 94, 0.16);
}

.sanctions-actions .sg-sub-action {
  min-height: 34px;
  padding: 0 12px;
  font-size: 12px;
}

.sanctions-pagination {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.sanctions-pagination span {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.sanctions-page-btn {
  min-height: 34px;
  border: none;
  border-radius: 999px;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 800;
  font-family: inherit;
  background: var(--color-nav);
  color: var(--color-nav-text);
  cursor: pointer;
}

.sanctions-page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .sanctions-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
