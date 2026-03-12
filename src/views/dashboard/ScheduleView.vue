<template>
  <div class="px-6 py-10 max-w-4xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-extrabold text-gray-900">Attendance Schedule</h1>
      <div class="px-4 py-1.5 bg-[var(--color-primary)]/10 text-[var(--color-primary)] rounded-full text-xs font-bold uppercase tracking-tight">
        {{ attendanceRecords.length }} Total Records
      </div>
    </div>

    <div v-if="isLoading" class="flex justify-center items-center min-h-[40vh]">
       <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>
    
    <div v-else-if="attendanceRecords.length > 0" class="space-y-4">
      <div 
        v-for="record in attendanceRecords" 
        :key="record.id"
        class="bg-white rounded-[24px] p-5 shadow-sm border border-gray-100 flex items-center gap-4 hover:shadow-md transition-shadow"
      >
        <!-- Date Block -->
        <div class="flex flex-col items-center justify-center w-14 h-14 bg-gray-50 rounded-2xl border border-gray-100">
          <span class="text-[10px] font-bold text-gray-400 uppercase">{{ formatMonth(record.time_in) }}</span>
          <span class="text-xl font-black text-gray-900 leading-none">{{ formatDay(record.time_in) }}</span>
        </div>

        <!-- Info -->
        <div class="flex-1 min-w-0">
          <h3 class="font-bold text-gray-900 truncate">{{ record.event_name || 'Event #' + record.event_id }}</h3>
          <p class="text-[13px] text-gray-500 font-medium">
            {{ formatTime(record.time_in) }} 
            <span v-if="record.time_out"> — {{ formatTime(record.time_out) }}</span>
          </p>
        </div>

        <!-- Status -->
        <div class="flex flex-col items-end gap-1">
          <span 
            class="px-3 py-1 rounded-full text-[11px] font-extrabold uppercase tracking-wider"
            :class="statusClass(record.status)"
          >
            {{ record.status }}
          </span>
          <span class="text-[10px] text-gray-400 font-medium">{{ record.method }}</span>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-20 bg-white rounded-[32px] border border-dashed border-gray-200">
      <p class="text-gray-400 font-medium">No attendance records found yet.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { eventService } from '@/services/eventService.js'

const attendanceRecords = ref([])
const isLoading = ref(true)

onMounted(async () => {
  try {
    isLoading.value = true
    const data = await eventService.getMyAttendance()
    // The API might return the array directly or wrapped in an object
    attendanceRecords.value = data?.attendances || data || []
  } catch (error) {
    console.error('Error fetching attendance:', error)
  } finally {
    isLoading.value = false
  }
})

function formatMonth(date) {
  return new Date(date).toLocaleString('en-US', { month: 'short' })
}

function formatDay(date) {
  return new Date(date).getDate()
}

function formatTime(date) {
  return new Date(date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

function statusClass(status) {
  switch (status?.toLowerCase()) {
    case 'present': return 'bg-green-100 text-green-700'
    case 'absent':  return 'bg-red-100 text-red-700'
    case 'excused': return 'bg-blue-100 text-blue-700'
    default:        return 'bg-gray-100 text-gray-700'
  }
}
</script>
