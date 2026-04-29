<template>
  <div class="w-full flex flex-col items-center gap-2">
    <div ref="buttonHost" class="w-full flex justify-center min-h-[44px]"></div>
    <p v-if="errorMessage" class="text-red-500 text-xs text-center">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { renderGoogleButton } from '@/services/googleSignIn.js'
import { isGoogleLoginAvailable } from '@/config/googleAuth.js'

const emit = defineEmits(['credential', 'unavailable'])
const buttonHost = ref(null)
const errorMessage = ref('')
let hasMountedButton = false

async function mountButton() {
    if (!buttonHost.value) return
    if (hasMountedButton) return
    hasMountedButton = true
    if (!isGoogleLoginAvailable()) {
        errorMessage.value = 'Google login is not configured.'
        emit('unavailable')
        return
    }
    try {
        await renderGoogleButton(buttonHost.value, {
            onCredential: (credential) => emit('credential', credential),
        })
    } catch (err) {
        errorMessage.value = err?.message || 'Failed to load Google Sign-In.'
        emit('unavailable')
    }
}

onMounted(mountButton)
watch(buttonHost, (el) => { if (el) mountButton() })
</script>
