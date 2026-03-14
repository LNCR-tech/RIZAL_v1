<template>
  <div class="min-h-screen flex flex-col font-[Manrope] overflow-hidden" style="background: var(--color-bg);">
    <!-- Main centered content -->
    <div class="flex-1 flex flex-col items-center justify-center px-8 relative z-10">
      <div class="w-full max-w-[340px] flex flex-col gap-6">

        <!-- Heading -->
        <h1 
          class="text-[22px] font-semibold leading-[1.4] tracking-[-0.3px] transition-all duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] relative"
          style="color: var(--color-text-primary);"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
        >
          Welcome to the portal. Log in to access your dashboard.
        </h1>

        <!-- Form -->
        <form 
          class="flex flex-col gap-3 transition-all duration-700 delay-100 ease-[cubic-bezier(0.22,1,0.36,1)] relative" 
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
          @submit.prevent="handleLogin"
        >
          <!-- Email -->
          <BaseInput
            id="email"
            v-model="email"
            type="email"
            placeholder="Gmail"
            autocomplete="email"
            :disabled="isLoading"
          />

          <!-- Password -->
          <BaseInput
            id="password"
            v-model="password"
            type="password"
            placeholder="Password"
            autocomplete="current-password"
            :disabled="isLoading"
            @enter="handleLogin"
          />

          <!-- Error message -->
          <Transition name="fade">
            <p v-if="error" class="text-red-500 text-xs text-center mt-1">
              {{ error }}
            </p>
          </Transition>

          <!-- Login Button -->
          <BaseButton
            type="submit"
            variant="primary"
            size="md"
            class="mt-1 group"
            :loading="isLoading"
          >
            Log In
          </BaseButton>
        </form>

        <!-- Powered by Aura -->
        <div 
          class="flex items-center justify-center gap-2 mt-1 transition-all duration-700 delay-200 ease-[cubic-bezier(0.22,1,0.36,1)]"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'"
        >
          <img
            :src="activeAuraLogo"
            alt="Aura"
            class="h-8 w-auto object-contain"
          />
          <span class="text-[13px] font-medium tracking-tight" style="color: var(--color-text-primary);">
            Powered by Aura Ai
          </span>
        </div>

      </div>
    </div>

    <!-- Footer -->
    <footer 
      class="pb-8 flex justify-center transition-all duration-1000 delay-300 ease-out relative z-10"
      :class="isMounted ? 'opacity-100' : 'opacity-0'"
    >
      <a
        href="#"
        class="text-[12px] font-medium transition-colors"
        style="color: var(--color-text-secondary);"
      >
        Learn more about Aura Project
      </a>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import { useAuth } from '@/composables/useAuth.js'
import { activeAuraLogo } from '@/config/theme.js'

const email = ref('')
const password = ref('')
const isMounted = ref(false)

const { login, isLoading, error } = useAuth()

onMounted(() => {
  // Wait a tiny bit on load to ensure the browser paints the initial opacity-0 state
  // before we flip it to mount the animation, making it extremely crisp.
  setTimeout(() => {
    isMounted.value = true
  }, 50)
})

async function handleLogin() {
  await login(email.value, password.value)
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
