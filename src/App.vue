<template>
  <RouterView />
  <Transition name="mobile-fullscreen-hint">
    <button
      v-if="mobileFullscreenHintVisible"
      type="button"
      class="mobile-fullscreen-hint"
      @click="requestMobileFullscreen"
    >
      Tap anywhere to enter fullscreen
    </button>
  </Transition>
</template>

<script setup>
import { RouterView } from 'vue-router'
import { mobileFullscreenHintVisible, requestMobileFullscreen } from '@/services/mobileFullscreen.js'
</script>
