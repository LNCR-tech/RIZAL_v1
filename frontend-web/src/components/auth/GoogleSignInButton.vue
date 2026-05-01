<template>
  <div class="google-btn-wrapper">
    <button
      v-if="showFallback"
      type="button"
      class="google-btn-fallback"
      @click="handleFallbackClick"
    >
      <span class="google-btn-fallback__logo" aria-hidden="true">G</span>
      <span class="google-btn-fallback__text">Continue with Google</span>
    </button>
    <div v-show="!showFallback" ref="buttonHost" class="google-btn-host"></div>
    <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import { onMounted, nextTick, ref } from 'vue'
import { isGoogleLoginAvailable } from '@/config/googleAuth.js'
import { renderGoogleButton } from '@/services/googleSignIn.js'

const emit = defineEmits(['credential', 'unavailable'])

const errorMessage = ref('')
const buttonHost = ref(null)
const showFallback = ref(true)

onMounted(async () => {
  try {
    if (!isGoogleLoginAvailable()) {
      errorMessage.value = 'Google sign-in is not configured in this environment yet.'
      emit('unavailable')
      return
    }
    await nextTick()
    await renderGoogleButton(buttonHost.value, {
      theme: 'outline',
      size: 'large',
      onCredential: (idToken) => emit('credential', idToken),
    })
    showFallback.value = false
    errorMessage.value = ''
  } catch (err) {
    showFallback.value = true
    errorMessage.value = err?.message || 'Google sign-in unavailable.'
    emit('unavailable')
  }
})

function handleFallbackClick() {
  if (!isGoogleLoginAvailable()) {
    errorMessage.value = 'Google sign-in is not configured in this environment yet.'
  } else {
    errorMessage.value = 'Google sign-in is temporarily unavailable.'
  }
  emit('unavailable')
}
</script>

<style scoped>
.google-btn-wrapper {
  width: 100%;
}

.google-btn-fallback {
  width: 100%;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px solid #dadce0;
  border-radius: 999px;
  background: #ffffff;
  color: #3c4043;
  font-size: 14px;
  font-weight: 600;
  font-family: Roboto, Arial, sans-serif;
  cursor: pointer;
  padding: 0 16px;
}

.google-btn-fallback__logo {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #ffffff;
  color: #4285f4;
  font-size: 14px;
  font-weight: 700;
}

.google-btn-host {
  width: 100%;
  min-height: 44px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.error-msg {
  color: #f87171;
  font-size: 12px;
  text-align: center;
  margin-top: 6px;
}
</style>
