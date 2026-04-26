<template>
  <span class="gather-brand-mark" aria-hidden="true">
    <DotLottieVue
      class="gather-brand-mark__player"
      autoplay
      loop
      :src="societyAnimationUrl"
    />
  </span>
</template>

<script setup>
import { DotLottieVue } from '@lottiefiles/dotlottie-vue'
import societyAnimationUrl from '@/assets/animations/society.lottie?url'
</script>

<style scoped>
.gather-brand-mark {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.gather-brand-mark__player {
  width: 38px;
  height: 38px;
  display: block;
}
</style>
