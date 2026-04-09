<template>
  <MobileDashboardHome v-bind="$attrs" />
  <!-- TEMPORARY MOBILE VIEW BANNER -->
  <div style="position:fixed;top:0;left:0;right:0;z-index:99999;background:#f59e0b;color:#1c1917;text-align:center;font-size:11px;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;padding:4px 8px;pointer-events:none;">
    ⚠ Temporary Mobile View
  </div>
</template>

<script setup>
import MobileDashboardHome from '@/components/mobile/dashboard/MobileDashboardHome.vue'
</script>
