<template>
  <div class="w-full">
    <button
      type="button"
      class="google-btn"
      :disabled="isLoading || !available"
      @click="handleClick"
    >
      <span v-if="isLoading" class="spinner" aria-hidden="true"></span>
      <svg v-else width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" class="google-icon">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
      <span class="btn-text">{{ isLoading ? 'Signing in…' : 'Continue with Google' }}</span>
    </button>
    <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { isGoogleLoginAvailable } from '@/config/googleAuth.js'
import { ensureGoogleClientReady } from '@/services/googleSignIn.js'

const emit = defineEmits(['credential', 'unavailable'])

const isLoading = ref(false)
const available = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  if (!isGoogleLoginAvailable()) {
    emit('unavailable')
    return
  }
  try {
    await ensureGoogleClientReady()
    available.value = true
  } catch {
    emit('unavailable')
  }
})

async function handleClick() {
  if (isLoading.value || !available.value) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    const { google, clientId } = await ensureGoogleClientReady()
    const credential = await new Promise((resolve, reject) => {
      google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
          if (response?.credential) resolve(response.credential)
          else reject(new Error('No credential returned by Google.'))
        },
        ux_mode: 'popup',
        auto_select: false,
      })
      google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed?.() || notification.isSkippedMoment?.()) {
          reject(new Error('Google sign-in was cancelled.'))
        }
      })
    })
    emit('credential', credential)
  } catch (err) {
    errorMessage.value = err?.message || 'Google sign-in failed.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.google-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: transparent;
  border: 1.5px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  padding: 10px 16px;
  cursor: pointer;
  color: #e0e0e0;
  font-family: 'Manrope', sans-serif;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.01em;
  transition: border-color 0.2s ease, background 0.2s ease, opacity 0.2s ease;
  min-height: 44px;
}

.google-btn:hover:not(:disabled) {
  border-color: rgba(255, 255, 255, 0.32);
  background: rgba(255, 255, 255, 0.04);
}

.google-btn:active:not(:disabled) {
  background: rgba(255, 255, 255, 0.07);
}

.google-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.google-icon {
  flex-shrink: 0;
}

.btn-text {
  flex: 1;
  text-align: center;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #e0e0e0;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-msg {
  color: #f87171;
  font-size: 12px;
  text-align: center;
  margin-top: 6px;
}
</style>
