<template>
  <component :is="activeLayout" />
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import DesktopAppLayout from '@/layouts/desktop/DesktopAppLayout.vue'
import MobileAppLayout from '@/layouts/mobile/MobileAppLayout.vue'
import { useDeviceStore } from '@/stores/device.js'

const deviceStore = useDeviceStore()
const { isMobile } = storeToRefs(deviceStore)
const activeLayout = computed(() => (isMobile.value ? MobileAppLayout : DesktopAppLayout))
</script>
