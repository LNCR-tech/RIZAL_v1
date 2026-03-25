<template>
  <section class="school-it-reports">
    <div class="school-it-reports__shell">
      <SchoolItTopHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="activeSchoolSettings?.school_name || activeUser?.school_name || ''"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <div class="school-it-reports__body">
        <header class="school-it-reports__header dashboard-enter dashboard-enter--2">
          <button class="school-it-reports__back" type="button" @click="goBack" aria-label="Go Back">
            <ArrowLeft :size="20" />
          </button>
          <div class="school-it-reports__header-copy">
            <h1 class="school-it-reports__title">Event Reports</h1>
            <p class="school-it-reports__subtitle">View and download school-scoped attendance reports for events across your campus.</p>
          </div>
        </header>

        <section class="school-it-reports__content dashboard-enter dashboard-enter--3">
          <div class="school-it-reports__toolbar">
            <div class="school-it-reports__search-shell">
              <input
                v-model="searchQuery"
                class="school-it-reports__search-input"
                type="text"
                placeholder="Search events by name or location"
              >
              <button class="school-it-reports__search-icon" type="button" aria-label="Search">
                <Search :size="18" :stroke-width="2.5" color="#9ca3af" />
              </button>
            </div>
          </div>

          <div class="school-it-reports__table-wrap">
            <table class="school-it-reports__table">
              <thead>
                <tr>
                  <th>Event Name</th>
                  <th>Date</th>
                  <th>Location</th>
                  <th class="school-it-reports__cell--actions">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="event in filteredEvents" :key="event.id">
                  <td>
                    <div class="school-it-reports__event-name">{{ event.name }}</div>
                  </td>
                  <td>
                    <div class="school-it-reports__event-date">{{ formatDate(event.start_datetime) }}</div>
                  </td>
                  <td>
                    <div class="school-it-reports__event-loc">{{ event.location || 'Unspecified Location' }}</div>
                  </td>
                  <td class="school-it-reports__cell--actions">
                    <div class="school-it-reports__actions-tray">
                      <button class="school-it-reports__btn school-it-reports__btn--view" type="button" @click="viewEvent(event)">
                        View
                      </button>
                      <button class="school-it-reports__btn school-it-reports__btn--download" type="button" @click="downloadReport(event)" :disabled="isDownloading === event.id">
                        <Download v-if="isDownloading !== event.id" :size="14" :stroke-width="2.5" />
                        {{ isDownloading === event.id ? 'Exporting...' : 'Download' }}
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!filteredEvents.length">
                  <td colspan="4" class="school-it-reports__empty">
                    {{ isLoading ? 'Loading events...' : 'No events found matching your search.' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Search, Download } from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { filterWorkspaceEntitiesBySchool } from '@/services/workspaceScope.js'
import { getEvents, getEventAttendance, resolveApiBaseUrl } from '@/services/backendApi.js'
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

const searchQuery = ref('')
const isDownloading = ref(null)
const eventsList = ref([])
const isLoadingEvents = ref(true)

console.log('Mounting SchoolItEventReportsView: HMR Sync', Date.now())

const activeUser = computed(() => props.preview ? schoolItPreviewData.user : currentUser.value)
const activeSchoolSettings = computed(() => props.preview ? schoolItPreviewData.schoolSettings : schoolSettings.value)
const schoolId = computed(() => Number(activeUser.value?.school_id ?? activeSchoolSettings.value?.school_id))

const activeEvents = computed(() => props.preview ? (Array.isArray(schoolItPreviewData.events) ? schoolItPreviewData.events : []) : eventsList.value)
const filteredBySchoolEvents = computed(() => filterWorkspaceEntitiesBySchool(activeEvents.value, schoolId.value))

const isLoading = computed(() => isLoadingEvents.value)

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

const filteredEvents = computed(() => {
  let list = filteredBySchoolEvents.value
  const query = searchQuery.value.trim().toLowerCase()
  if (query) {
    list = list.filter(e => 
      (e.name && e.name.toLowerCase().includes(query)) ||
      (e.location && e.location.toLowerCase().includes(query))
    )
  }
  return [...list].sort((a, b) => new Date(b.start_datetime || 0) - new Date(a.start_datetime || 0))
})

onMounted(() => {
  fetchEvents()
})

async function fetchEvents() {
  isLoadingEvents.value = true
  if (props.preview) {
    isLoadingEvents.value = false
    return
  }
  try {
    const token = localStorage.getItem('aura_token') || ''
    eventsList.value = await getEvents(resolveApiBaseUrl(), token)
  } catch (err) {
    console.error('Failed to fetch events for reports:', err)
  } finally {
    isLoadingEvents.value = false
  }
}

function formatDate(isoString) {
  if (!isoString) return 'Unspecified Date'
  const date = new Date(isoString)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }).format(date)
}

function viewEvent(event) {
  if (props.preview) {
    router.push({ name: 'PreviewSchoolItEventDetail', params: { id: event.id } })
  } else {
    router.push({ name: 'SchoolItEventDetail', params: { id: event.id } })
  }
}

async function downloadReport(event) {
  if (isDownloading.value === event.id) return
  isDownloading.value = event.id
  
  try {
    const token = localStorage.getItem('aura_token') || ''
    const attendanceRecords = props.preview 
      ? [] 
      : await getEventAttendance(apiBaseUrl.value, token, event.id)
    
    // Generate CSV locally from actual data
    const csvHeader = 'Student ID,Student Name,College,Program,Check-in Time,Status\n'
    
    const rows = attendanceRecords.map(record => {
      const studentProfile = record.student_profile || record.user?.student_profile || record.student?.student_profile || {}
      const userObj = record.user || record.student || {}
      
      const rawStudentId = studentProfile.student_id || record.student_id
      const studentId = rawStudentId ? String(rawStudentId).replace(/"/g, '""') : 'N/A'
      
      const firstName = userObj.first_name || ''
      const lastName = userObj.last_name || ''
      const rawName = record.student_name || [firstName, lastName].filter(Boolean).join(' ')
      const studentName = String(rawName || 'Unknown Student').replace(/"/g, '""')
      
      const college = String(studentProfile.department_name || record.department_name || record.college || 'N/A').replace(/"/g, '""')
      const program = String(studentProfile.program_name || record.program_name || record.program || 'N/A').replace(/"/g, '""')
      
      let checkInTime = 'N/A'
      if (record.status && record.status.toLowerCase() !== 'absent') {
          checkInTime = record.time_in ? new Date(record.time_in).toLocaleTimeString('en-US') : 'Pre-registered / Check-in Time Unknown'
      }
      const status = String(record.status || 'Present').replace(/^\w/, c => c.toUpperCase())
      
      return `"${studentId}","${studentName}","${college}","${program}","${checkInTime}","${status}"`
    }).join('\n')
    
    const csvContent = csvHeader + (rows || 'N/A,No attendees fetched,N/A,N/A,N/A,N/A\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    const cleanTitle = event.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()
    
    link.setAttribute('href', url)
    link.setAttribute('download', `${cleanTitle}_attendance_report.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
  } catch (error) {
    console.error('Download failed', error)
    alert('There was an issue generating the report. Please try again.')
  } finally {
    isDownloading.value = null
  }
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
.school-it-reports {
  min-height: 100vh;
  padding: 30px 28px 120px;
  font-family: 'Manrope', sans-serif;
  background: var(--color-bg, #f3f4f6);
}

.school-it-reports__shell {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
}

.school-it-reports__body {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-top: 32px;
}

.school-it-reports__header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.school-it-reports__back {
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
  flex-shrink: 0;
}

.school-it-reports__back:hover {
  background: rgba(0, 0, 0, 0.05);
}

.school-it-reports__header-copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.school-it-reports__title {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.04em;
  color: var(--color-text-always-dark, #111827);
}

.school-it-reports__subtitle {
  margin: 0;
  font-size: 15px;
  font-weight: 500;
  color: #6b7280;
}

.school-it-reports__content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: #ffffff;
  border-radius: 32px;
  padding: 28px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.02);
}

.school-it-reports__toolbar {
  display: flex;
  justify-content: flex-end;
}

.school-it-reports__search-shell {
  display: flex;
  align-items: center;
  width: 320px;
  height: 46px;
  border-radius: 999px;
  background: #f9fafb;
  border: 1px solid #f3f4f6;
  padding: 0 6px 0 20px;
  transition: border-color 0.2s;
}

.school-it-reports__search-shell:focus-within {
  border-color: #e5e7eb;
}

.school-it-reports__search-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  border: none;
  outline: none;
  font-size: 14px;
  color: #111827;
  background: transparent;
}

.school-it-reports__search-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: transparent;
  border: none;
  flex-shrink: 0;
}

.school-it-reports__table-wrap {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.school-it-reports__table {
  width: 100%;
  min-width: 700px;
  border-collapse: separate;
  border-spacing: 0;
}

.school-it-reports__table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #f3f4f6;
}

.school-it-reports__table td {
  padding: 16px;
  vertical-align: middle;
  border-bottom: 1px solid #f3f4f6;
}

.school-it-reports__event-name {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}

.school-it-reports__event-date,
.school-it-reports__event-loc {
  font-size: 14px;
  font-weight: 500;
  color: #4b5563;
}

.school-it-reports__cell--actions {
  text-align: right;
  width: 220px;
}

.school-it-reports__actions-tray {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.school-it-reports__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 36px;
  padding: 0 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  border: none;
  transition: transform 0.1s, filter 0.2s;
}

.school-it-reports__btn:active {
  transform: scale(0.96);
}

.school-it-reports__btn--view {
  background: #f3f4f6;
  color: #4b5563;
}

.school-it-reports__btn--view:hover {
  background: #e5e7eb;
}

.school-it-reports__btn--download {
  background: #111827;
  color: #ffffff;
}

.school-it-reports__btn--download:hover {
  background: #1f2937;
}

.school-it-reports__btn--download:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.school-it-reports__empty {
  text-align: center !important;
  color: #6b7280;
  padding: 40px !important;
  font-size: 14px;
  font-weight: 500;
}
</style>
