<template>
  <div class="px-6 py-10 max-w-4xl mx-auto space-y-8">
    <h1 class="text-2xl font-extrabold text-gray-900">Attendance Analytics</h1>

    <div v-if="isLoading" class="flex justify-center items-center min-h-[40vh]">
       <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Attendance Rate Card -->
      <div class="md:col-span-3 bg-white rounded-[32px] p-8 shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center space-y-4">
        <div class="relative w-48 h-48 flex items-center justify-center">
          <svg class="w-full h-full -rotate-90">
            <circle cx="96" cy="96" r="88" stroke="currentColor" stroke-width="12" fill="transparent" class="text-gray-100" />
            <circle cx="96" cy="96" r="88" stroke="currentColor" stroke-width="12" fill="transparent" class="text-[var(--color-primary)]" 
              :style="{ strokeDasharray: 552.92, strokeDashoffset: 552.92 * (1 - attendanceRate / 100) }"
            />
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <span class="text-4xl font-black text-gray-900">{{ Math.round(attendanceRate) }}%</span>
            <span class="text-xs font-bold text-gray-400 uppercase tracking-widest">Attendance Rate</span>
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div class="bg-white rounded-[24px] p-6 shadow-sm border border-gray-100 text-center space-y-1">
        <p class="text-3xl font-black text-green-600">{{ stats.present }}</p>
        <p class="text-xs font-bold text-gray-400 uppercase">Present</p>
      </div>
      <div class="bg-white rounded-[24px] p-6 shadow-sm border border-gray-100 text-center space-y-1">
        <p class="text-3xl font-black text-red-600">{{ stats.absent }}</p>
        <p class="text-xs font-bold text-gray-400 uppercase">Absent</p>
      </div>
      <div class="bg-white rounded-[24px] p-6 shadow-sm border border-gray-100 text-center space-y-1">
        <p class="text-3xl font-black text-blue-600">{{ stats.excused }}</p>
        <p class="text-xs font-bold text-gray-400 uppercase">Excused</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { eventService } from '@/services/eventService.js'

const attendanceRecords = ref([])
const isLoading = ref(true)

onMounted(async () => {
  try {
    isLoading.value = true
    const data = await eventService.getMyAttendance()
    attendanceRecords.value = data?.attendances || data || []
  } catch (error) {
    console.error('Error fetching analytics:', error)
  } finally {
    isLoading.value = false
  }
})

const stats = computed(() => {
  const result = { present: 0, absent: 0, excused: 0 }
  attendanceRecords.value.forEach(r => {
    const s = r.status?.toLowerCase()
    if (s === 'present') result.present++
    else if (s === 'absent') result.absent++
    else if (s === 'excused') result.excused++
  })
  return result
})

const attendanceRate = computed(() => {
  const total = attendanceRecords.value.length
  if (total === 0) return 100
  return (stats.value.present / total) * 100
})
</script>
