<template>
  <section class="sg-sub-page">
    <header class="sg-sub-header dashboard-enter dashboard-enter--1">
      <button class="sg-sub-back" type="button" @click="goBack">
        <ArrowLeft :size="20" />
      </button>
      <h1 class="sg-sub-title">Student Sanction Detail</h1>
    </header>

    <div v-if="isLoading" class="sg-sub-loading dashboard-enter dashboard-enter--2">
      <p>Loading sanction detail...</p>
    </div>

    <div v-else-if="loadError" class="sg-sub-error dashboard-enter dashboard-enter--2">
      <p>{{ loadError }}</p>
      <button class="sg-sub-action" type="button" @click="reload">Try Again</button>
    </div>

    <template v-else-if="targetRecord">
      <div class="sg-sub-card dashboard-enter dashboard-enter--2">
        <h2 class="sg-sub-card-title">Student Profile</h2>
        <div class="student-profile-grid">
          <div class="student-profile-row">
            <span>Name</span>
            <strong>{{ formatStudentName(targetRecord.student) }}</strong>
          </div>
          <div class="student-profile-row">
            <span>Student ID</span>
            <strong>{{ targetRecord.student.student_id || 'N/A' }}</strong>
          </div>
          <div class="student-profile-row">
            <span>Email</span>
            <strong>{{ targetRecord.student.email || 'N/A' }}</strong>
          </div>
          <div class="student-profile-row">
            <span>Department</span>
            <strong>{{ targetRecord.student.department_name || 'N/A' }}</strong>
          </div>
          <div class="student-profile-row">
            <span>Course</span>
            <strong>{{ targetRecord.student.program_name || 'N/A' }}</strong>
          </div>
          <div class="student-profile-row">
            <span>Year</span>
            <strong>{{ targetRecord.student.year_level || 'N/A' }}</strong>
          </div>
        </div>
      </div>

      <div class="sg-sub-card dashboard-enter dashboard-enter--3">
        <div class="detail-header">
          <h2 class="sg-sub-card-title">Sanction Items</h2>
          <span class="detail-status" :class="`detail-status--${targetRecord.status}`">
            {{ targetRecord.status }}
          </span>
        </div>

        <div v-if="targetRecord.items.length" class="detail-items">
          <article v-for="item in targetRecord.items" :key="item.id" class="detail-item">
            <div class="detail-item__main">
              <strong>{{ item.item_name }}</strong>
              <p v-if="item.item_description">{{ item.item_description }}</p>
            </div>
            <span class="detail-item__status" :class="`detail-item__status--${item.status}`">
              {{ item.status }}
            </span>
          </article>
        </div>
        <p v-else class="sg-sub-empty">No sanction items found for this record.</p>

        <div class="detail-actions">
          <button
            class="sg-sub-action"
            type="button"
            :disabled="targetRecord.status !== 'pending' || isApproving"
            @click="approve"
          >
            {{ isApproving ? 'Approving...' : 'Approve Compliance' }}
          </button>
        </div>
      </div>
    </template>

    <div v-else class="sg-sub-card dashboard-enter dashboard-enter--2">
      <p class="sg-sub-empty">No sanction record was found for this student in the selected event.</p>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import {
  approveEventStudentSanction,
  getStudentSanctionsDetail,
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
const sanctions = ref([])
const isApproving = ref(false)

const eventId = computed(() => Number(route.params.eventId))
const userId = computed(() => Number(route.params.userId))

const targetRecord = computed(() => (
  sanctions.value.find((record) => Number(record.event_id) === eventId.value)
  || sanctions.value[0]
  || null
))

watch(
  [eventId, userId, apiBaseUrl, () => sgLoading.value, () => route.query?.variant],
  async ([resolvedEventId, resolvedUserId, url]) => {
    if (!url || sgLoading.value || !Number.isFinite(resolvedEventId) || !Number.isFinite(resolvedUserId)) return
    await loadDetail(url)
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
    router.push(withPreservedGovernancePreviewQuery(route, {
      name: 'PreviewSgSanctionedStudents',
      params: { eventId: String(eventId.value) },
    }))
    return
  }

  router.push({
    name: 'SgSanctionedStudents',
    params: { eventId: String(eventId.value) },
  })
}

function buildPreviewSanctions(bundle = null, resolvedUserId = null, resolvedEventId = null) {
  const previewStudents = Array.isArray(bundle?.students) ? bundle.students : []
  const previewStudent = previewStudents.find((student) => Number(student?.id) === resolvedUserId)
  if (!previewStudent) return []

  const isPending = resolvedUserId % 2 === 1
  return [
    {
      id: 70000 + resolvedUserId,
      event_id: resolvedEventId,
      status: isPending ? 'pending' : 'complied',
      notes: isPending ? 'Waiting for governance review.' : 'Approved by delegated council.',
      complied_at: isPending ? null : new Date().toISOString(),
      student: {
        user_id: Number(previewStudent.id),
        student_profile_id: Number(previewStudent.student_profile?.id || previewStudent.id),
        student_id: previewStudent.student_profile?.student_id || null,
        email: previewStudent.email || '',
        first_name: previewStudent.first_name || null,
        middle_name: previewStudent.middle_name || null,
        last_name: previewStudent.last_name || null,
        department_name: previewStudent.student_profile?.department_name || null,
        program_name: previewStudent.student_profile?.program_name || null,
        year_level: previewStudent.student_profile?.year_level || null,
      },
      items: [
        {
          id: 1,
          item_name: 'Community Service',
          item_description: 'Complete required service hours assigned by the governance unit.',
          status: isPending ? 'pending' : 'complied',
        },
        {
          id: 2,
          item_name: 'Reflection Paper',
          item_description: 'Submit reflection on event absence and corrective action.',
          status: isPending ? 'pending' : 'complied',
        },
      ],
    },
  ]
}

async function loadDetail(url) {
  isLoading.value = true
  loadError.value = ''

  try {
    if (props.preview) {
      sanctions.value = buildPreviewSanctions(previewBundle.value, userId.value, eventId.value)
      return
    }

    const detail = await getStudentSanctionsDetail(url, token.value, userId.value)
    sanctions.value = Array.isArray(detail?.sanctions) ? detail.sanctions : []
  } catch (error) {
    loadError.value = error?.message || 'Unable to load the student sanction detail.'
  } finally {
    isLoading.value = false
  }
}

async function approve() {
  if (!targetRecord.value || targetRecord.value.status !== 'pending' || isApproving.value) return

  if (props.preview) {
    sanctions.value = sanctions.value.map((record) => (
      record.id === targetRecord.value.id
        ? {
          ...record,
          status: 'complied',
          complied_at: new Date().toISOString(),
          items: record.items.map((item) => ({ ...item, status: 'complied' })),
        }
        : record
    ))
    return
  }

  isApproving.value = true
  try {
    const updated = await approveEventStudentSanction(
      apiBaseUrl.value,
      token.value,
      eventId.value,
      userId.value
    )
    sanctions.value = sanctions.value.map((record) => (
      record.id === updated.id ? updated : record
    ))
  } catch (error) {
    loadError.value = error?.message || 'Unable to approve sanction compliance.'
  } finally {
    isApproving.value = false
  }
}

async function reload() {
  if (!apiBaseUrl.value) return
  await loadDetail(apiBaseUrl.value)
}
</script>

<style scoped>
@import '@/assets/css/sg-sub-views.css';

.student-profile-grid {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.student-profile-row {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--color-bg) 58%, var(--color-surface));
}

.student-profile-row span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.student-profile-row strong {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.4;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.detail-status {
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.detail-status--pending {
  color: #b45309;
  background: rgba(245, 158, 11, 0.14);
}

.detail-status--complied {
  color: #166534;
  background: rgba(34, 197, 94, 0.16);
}

.detail-items {
  display: grid;
  gap: 10px;
}

.detail-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 12px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--color-bg) 58%, var(--color-surface));
}

.detail-item__main {
  display: grid;
  gap: 4px;
}

.detail-item__main strong {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.detail-item__main p {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-muted);
}

.detail-item__status {
  min-height: 22px;
  padding: 0 9px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.detail-item__status--pending {
  color: #b45309;
  background: rgba(245, 158, 11, 0.14);
}

.detail-item__status--complied {
  color: #166534;
  background: rgba(34, 197, 94, 0.16);
}

.detail-actions {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .student-profile-grid {
    grid-template-columns: 1fr;
  }

  .detail-item {
    flex-direction: column;
  }
}
</style>
