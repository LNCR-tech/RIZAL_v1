<template>
  <div class="google-btn-wrapper">
    <div v-if="!available && !errorMessage" class="google-btn-placeholder" aria-hidden="true"></div>
    <div v-show="available" ref="buttonHost" class="google-btn-host"></div>
    <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref, nextTick } from 'vue'
import { isGoogleLoginAvailable } from '@/config/googleAuth.js'
import { renderGoogleButton } from '@/services/googleSignIn.js'

const emit = defineEmits(['credential', 'unavailable'])

const available = ref(false)
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
    available.value = true
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
  display: flex;
  justify-content: center;
}

.google-btn-placeholder {
  width: 100%;
  height: 44px;
}

.error-msg {
  color: #f87171;
  font-size: 12px;
  text-align: center;
  margin-top: 6px;
}
</style>
