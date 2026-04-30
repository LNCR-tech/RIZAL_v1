<template>
  <div class="google-btn-wrapper">
    <div ref="buttonHost" class="google-btn-host"></div>
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

onMounted(async () => {
  if (!isGoogleLoginAvailable()) {
    emit('unavailable')
    return
  }
  try {
    await nextTick()
    await renderGoogleButton(buttonHost.value, {
      theme: 'outline',
      size: 'large',
      onCredential: (idToken) => emit('credential', idToken),
    })
  } catch (err) {
    errorMessage.value = err?.message || 'Google sign-in unavailable.'
    emit('unavailable')
  }
})
</script>

<style scoped>
.google-btn-wrapper {
  width: 100%;
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
