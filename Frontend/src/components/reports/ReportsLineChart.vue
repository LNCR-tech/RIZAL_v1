<template>
  <div class="reports-chart">
    <Line :data="resolvedData" :options="resolvedOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Chart as ChartJS,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  CategoryScale,
  Tooltip,
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

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
