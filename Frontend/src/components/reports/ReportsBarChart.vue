<template>
  <div class="reports-chart">
    <Bar :data="resolvedData" :options="resolvedOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js'
import { Bar } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const props = defineProps({
  data: {
    type: Object,
    default: () => ({
      labels: [],
      datasets: [],
    }),
  },
  options: {
    type: Object,
    default: () => ({}),
  },
})

const resolvedData = computed(() => ({
  labels: Array.isArray(props.data?.labels) ? props.data.labels : [],
  datasets: Array.isArray(props.data?.datasets) ? props.data.datasets : [],
}))

const resolvedOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'bottom',
    },
  },
  ...props.options,
}))
</script>

<style scoped>
.reports-chart {
  width: 100%;
  min-height: clamp(220px, 36vw, 300px);
}
</style>
