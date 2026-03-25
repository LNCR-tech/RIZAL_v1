<template>
  <section class="sg-sub-page">
    <header class="sg-sub-header dashboard-enter dashboard-enter--1">
      <button class="sg-sub-back" type="button" @click="goBack">
        <ArrowLeft :size="20" />
      </button>
      <h1 class="sg-sub-title">Manage Events</h1>
    </header>

    <div v-if="isLoading" class="sg-sub-loading dashboard-enter dashboard-enter--2">
      <p>Loading events...</p>
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
            placeholder="Search events"
          />
          <Search :size="14" style="color: var(--color-text-muted);" />
        </div>
      </div>

      <div class="sg-sub-card dashboard-enter dashboard-enter--3">
        <h2 class="sg-sub-card-title">Events ({{ filteredEvents.length }})</h2>
        <div v-if="filteredEvents.length" class="sg-events-list">
          <article
            v-for="event in filteredEvents"
            :key="event.id"
            class="sg-event-row"
            @click="goToEvent(event)"
          >
            <div class="sg-event-info">
              <h3 class="sg-event-name">{{ event.title || event.name || 'Untitled' }}</h3>
              <div class="sg-event-meta">
                <span v-if="event.start_time" class="sg-event-date">{{ formatDate(event.start_time) }}</span>
                <span v-if="event.status" class="sg-event-status" :class="`sg-event-status--${event.status}`">{{ event.status }}</span>
              </div>
            </div>
            <ArrowRight :size="16" class="sg-event-arrow" />
          </article>
        </div>
        <p v-else class="sg-sub-empty">No events found for this governance unit.</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, Search } from 'lucide-vue-next'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import { getGovernanceAccess, getEvents } from '@/services/backendApi.js'

const router = useRouter()
const { apiBaseUrl } = useDashboardSession()
const { isLoading: sgLoading } = useSgDashboard()

const isLoading = ref(true)
const loadError = ref('')
const events = ref([])
const searchQuery = ref('')

const filteredEvents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return events.value
  return events.value.filter((e) =>
    [e.title, e.name, e.status].filter(Boolean).join(' ').toLowerCase().includes(q)
  )
})

function formatDate(d) {
  if (!d) return ''
  try { return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }
  catch { return d }
}

function goBack() { router.push('/sg') }

function goToEvent(event) {
  router.push({ name: 'DashboardEventDetail', params: { id: event.id } })
}

watch(
  [apiBaseUrl, () => sgLoading.value],
  async ([url]) => {
    if (!url || sgLoading.value) return
    await loadEvents(url)
  },
  { immediate: true }
)

async function loadEvents(url) {
  isLoading.value = true
  loadError.value = ''
  try {
    const token = localStorage.getItem('aura_token') || ''
    const access = await getGovernanceAccess(url, token)
    const units = Array.isArray(access?.units) ? access.units : []
    const ssg = units.find((u) => String(u?.unit_type || '').toUpperCase() === 'SSG')
    const params = ssg?.governance_unit_id ? { governance_unit_id: ssg.governance_unit_id } : {}
    events.value = await getEvents(url, token, params)
  } catch (e) {
    loadError.value = e?.message || 'Unable to load events.'
  } finally { isLoading.value = false }
}

async function reload() { if (apiBaseUrl.value) await loadEvents(apiBaseUrl.value) }
</script>

<style scoped>
@import '@/assets/css/sg-sub-views.css';

.sg-events-list { display: flex; flex-direction: column; gap: 8px; }
.sg-event-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 16px; border-radius: 14px; background: var(--color-surface-border); cursor: pointer; transition: transform 0.12s; }
.sg-event-row:hover { transform: scale(1.01); }
.sg-event-info { flex: 1; min-width: 0; }
.sg-event-name { font-size: 14px; font-weight: 700; color: var(--color-text-primary); margin-bottom: 4px; }
.sg-event-meta { display: flex; gap: 8px; align-items: center; }
.sg-event-date { font-size: 12px; color: var(--color-text-muted); }
.sg-event-status { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 8px; text-transform: capitalize; }
.sg-event-status--upcoming { background: #3498db33; color: #3498db; }
.sg-event-status--active { background: #27ae6033; color: #27ae60; }
.sg-event-status--completed { background: #95a5a633; color: #95a5a6; }
.sg-event-arrow { color: var(--color-text-muted); flex-shrink: 0; }
</style>
