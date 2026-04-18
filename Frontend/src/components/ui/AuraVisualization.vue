<template>
  <div class="aura-visualization" :class="[`aura-visualization--${type}`]">
    <div v-if="title" class="viz-header">
      <h4 class="viz-title">{{ title }}</h4>
    </div>

    <div class="viz-content">
      <!-- Chart.js Containers -->
      <div v-if="isChartType" class="chart-container">
        <Bar v-if="type === 'bar'" :data="payload" :options="chartOptions" />
        <Line v-else-if="type === 'line'" :data="payload" :options="chartOptions" />
        <Pie v-else-if="type === 'pie'" :data="payload" :options="chartOptions" />
        <Doughnut v-else-if="type === 'doughnut'" :data="payload" :options="chartOptions" />
      </div>

      <!-- Raw SVG Mode -->
      <div v-else-if="type === 'svg'" class="svg-container" v-html="source"></div>

      <!-- Raw HTML Mode -->
      <div v-else-if="type === 'html'" class="html-container" v-html="sanitizedHtml"></div>
    </div>

    <div v-if="footer" class="viz-footer">
      <p class="viz-footer-text">{{ footer }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
} from 'chart.js'
import { Bar, Line, Pie, Doughnut } from 'vue-chartjs'
import DOMPurify from 'dompurify'

// Register Chart.js components
ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement
)

const props = defineProps({
  type: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    default: '',
  },
  payload: {
    type: Object,
    default: () => ({ labels: [], datasets: [] }),
  },
  source: {
    type: String,
    default: '',
  },
  options: {
    type: Object,
    default: () => ({}),
  },
  footer: {
    type: String,
    default: '',
  },
})

const isChartType = computed(() =>
  ['bar', 'line', 'pie', 'doughnut'].includes(props.type)
)

const sanitizedHtml = computed(() => DOMPurify.sanitize(props.source))

const chartOptions = computed(() => {
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: props.options.showLegend !== false,
        position: 'bottom',
        labels: {
          color: 'rgba(255, 255, 255, 0.7)',
          font: { family: 'Inter', size: 11 },
          usePointStyle: true,
          padding: 15,
        },
      },
      tooltip: {
        backgroundColor: '#161b22',
        titleFont: { family: 'Inter', size: 12, weight: 'bold' },
        bodyFont: { family: 'Inter', size: 12 },
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        boxPadding: 5,
      },
    },
  }

  // Adjust scales for non-circular charts
  if (['bar', 'line'].includes(props.type)) {
    baseOptions.scales = {
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: 'rgba(255, 255, 255, 0.5)', font: { size: 10 } },
      },
      x: {
        grid: { display: false },
        ticks: { color: 'rgba(255, 255, 255, 0.5)', font: { size: 10 } },
      },
    }
  }

  return { ...baseOptions, ...props.options.chartJS }
})
</script>

<style scoped>
.aura-visualization {
  background: rgba(22, 27, 34, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  margin: 16px 0;
  padding: 14px;
  width: 100%;
  max-width: 100%;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.viz-header {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.viz-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.2px;
}

.viz-content {
  min-height: 200px;
  max-height: 320px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container {
  width: 100%;
  height: 260px;
  position: relative;
}

.svg-container, .html-container {
  width: 100%;
  max-width: 100%;
  overflow: auto;
}

.svg-container :deep(svg) {
  width: 100%;
  height: auto;
  display: block;
}

.viz-footer {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.viz-footer-text {
  margin: 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  font-style: italic;
}
</style>
