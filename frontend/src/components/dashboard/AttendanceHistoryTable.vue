<template>
  <div class="history">
    <div class="history__header">
      <h3 class="history__title">Attendance History</h3>
      <span v-if="totalPages > 1" class="history__page-info">
        Page {{ currentPage }} of {{ totalPages }}
      </span>
    </div>

    <div v-if="paginatedRecords.length" class="history__table-wrap">
      <table class="history__table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Event</th>
            <th>Type</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="record in paginatedRecords"
            :key="record.key"
          >
            <td class="history__date">{{ record.date }}</td>
            <td class="history__event">{{ record.eventName }}</td>
            <td>
              <span
                class="history__org-tag"
                :class="`history__org-tag--${record.orgKey}`"
              >
                {{ record.orgLabel }}
              </span>
            </td>
            <td>
              <span
                class="history__status"
                :class="`history__status--${record.statusKey}`"
              >
                {{ record.statusLabel }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else class="history__empty">No attendance records yet.</p>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="history__pagination">
      <button
        class="history__page-btn"
        :disabled="currentPage <= 1"
        type="button"
        @click="currentPage -= 1"
      >
        ← Prev
      </button>
      <button
        class="history__page-btn"
        :disabled="currentPage >= totalPages"
        type="button"
        @click="currentPage += 1"
      >
        Next →
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  records: {
    type: Array,
    default: () => [],
  },
  perPage: {
    type: Number,
    default: 6,
  },
})

const currentPage = ref(1)

const totalPages = computed(() => Math.max(1, Math.ceil(props.records.length / props.perPage)))

const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * props.perPage
  return props.records.slice(start, start + props.perPage)
})

watch(() => props.records.length, () => {
  currentPage.value = 1
})
</script>

<style scoped>
.history {
  display: flex;
  flex-direction: column;
  gap: clamp(14px, 3.5vw, 18px);
}

.history__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.history__title {
  margin: 0;
  font-size: clamp(16px, 4.5vw, 20px);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-text-primary);
}

.history__page-info {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.history__table-wrap {
  border-radius: 20px;
  background: var(--color-surface);
  border: 1px solid rgba(10, 10, 10, 0.04);
  overflow: hidden;
}

.history__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.history__table thead {
  background: rgba(10, 10, 10, 0.02);
}

.history__table th {
  padding: 12px 16px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-surface-text-muted);
  text-align: left;
  border-bottom: 1px solid rgba(10, 10, 10, 0.06);
}

.history__table td {
  padding: 14px 16px;
  color: var(--color-surface-text);
  border-bottom: 1px solid rgba(10, 10, 10, 0.04);
  font-weight: 500;
}

.history__table tbody tr:last-child td {
  border-bottom: none;
}

.history__table tbody tr {
  transition: background 0.12s ease;
}

.history__table tbody tr:hover {
  background: rgba(10, 10, 10, 0.015);
}

.history__date {
  white-space: nowrap;
  font-size: 12px;
  color: var(--color-surface-text-muted) !important;
  font-weight: 600 !important;
}

.history__event {
  font-weight: 600 !important;
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history__org-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.history__org-tag--ssg {
  background: rgba(99, 102, 241, 0.12);
  color: #4F46E5;
}

.history__org-tag--sg {
  background: rgba(139, 92, 246, 0.12);
  color: #7C3AED;
}

.history__status {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.history__status--present {
  background: rgba(34, 197, 94, 0.12);
  color: #15803D;
}

.history__status--absent {
  background: rgba(239, 68, 68, 0.12);
  color: #B91C1C;
}

.history__status--excused {
  background: rgba(245, 158, 11, 0.14);
  color: #92400E;
}

.history__status--late {
  background: rgba(249, 115, 22, 0.12);
  color: #C2410C;
}

.history__status--unknown {
  background: rgba(10, 10, 10, 0.06);
  color: var(--color-surface-text-muted);
}

.history__empty {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-muted);
  text-align: center;
  padding: 32px 16px;
  background: var(--color-surface);
  border-radius: 20px;
}

.history__pagination {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.history__page-btn {
  border: 1px solid rgba(10, 10, 10, 0.08);
  border-radius: 999px;
  background: var(--color-surface);
  padding: 8px 20px;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-surface-text);
  cursor: pointer;
  transition: background 0.15s ease, transform 0.1s ease;
}

.history__page-btn:hover:not(:disabled) {
  background: rgba(10, 10, 10, 0.04);
}

.history__page-btn:active:not(:disabled) {
  transform: scale(0.96);
}

.history__page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Mobile: horizontal scroll for table */
@media (max-width: 600px) {
  .history__table-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .history__table {
    min-width: 480px;
  }
}
</style>
