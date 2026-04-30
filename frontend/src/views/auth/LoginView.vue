<template>
  <div class="login-page min-h-dvh flex flex-col font-[Manrope] overflow-auto" style="background: var(--color-bg);">
    <!-- Main centered content -->
    <div class="flex-1 flex flex-col items-center justify-center px-8 relative z-10">
      <div class="w-full max-w-[340px] flex flex-col gap-6 login-form-area">

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
            tone="neutral"
            :disabled="isLoading || googleLoading"
          />

          <!-- Password -->
          <BaseInput
            id="password"
            v-model="password"
            type="password"
            placeholder="Password"
            autocomplete="current-password"
            tone="neutral"
            :disabled="isLoading || googleLoading"
            @enter="handleLogin"
          />

          <!-- Forgot Password Link -->
          <div class="flex justify-end -mt-1">
            <a
              href="#"
              class="text-[12px] font-medium transition-colors"
              style="color: var(--color-text-secondary);"
              @click.prevent="goToForgotPassword"
            >
              Forgot password?
            </a>
          </div>

          <!-- Error message -->
          <Transition name="fade">
            <p v-if="visibleMessage" class="text-red-500 text-xs text-center mt-1">
              {{ visibleMessage }}
            </p>
          </Transition>

          <!-- Login Button -->
          <BaseButton
            type="submit"
            variant="primary"
            size="md"
            class="mt-1 group"
            :loading="isLoading"
            :disabled="googleLoading"
          >
            Log In
          </BaseButton>

          <!-- Google Sign-In below Log In -->
          <template v-if="!googleUnavailable">
            <div class="flex items-center gap-3 my-1" aria-hidden="true">
              <div class="flex-1 h-px" style="background: var(--color-border, #2a2a2a);"></div>
              <span class="text-[11px] uppercase tracking-wide" style="color: var(--color-text-secondary);">or</span>
              <div class="flex-1 h-px" style="background: var(--color-border, #2a2a2a);"></div>
            </div>

            <GoogleSignInButton
              @credential="handleGoogleCredential"
              @unavailable="googleUnavailable = true"
            />
          </template>
        </form>

        <!-- Powered by Aura -->
        <div 
          class="flex flex-col items-center justify-center gap-3 mt-1 transition-all duration-700 delay-200 ease-[cubic-bezier(0.22,1,0.36,1)]"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'"
        >
          <div class="flex items-center justify-center gap-2">
            <img
              :src="surfaceAuraLogo"
              alt="Aura"
              class="h-8 w-auto object-contain"
            />
            <span class="text-[13px] font-medium tracking-tight" style="color: var(--color-text-primary);">
              Powered by Aura Ai
            </span>
          </div>
          
          <a
            href="https://aura-landing-page-iota.vercel.app/"
            target="_blank"
            rel="noopener noreferrer"
            class="text-[12px] font-medium transition-colors"
            style="color: var(--color-text-secondary);"
          >
            Learn more about Aura Project
          </a>
        </div>

      </div>
    </div>

    <!-- Terms Modal -->
    <TermsModal 
      :isOpen="showTermsModal" 
      @agree="handleAgree"
      @decline="handleDecline" 
    />
  </div>
</template>

<script setup>
import { computed, ref, onBeforeMount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import TermsModal from '@/components/auth/TermsModal.vue'
import GoogleSignInButton from '@/components/auth/GoogleSignInButton.vue'
import { useAuth } from '@/composables/useAuth.js'
import { useGoogleLogin } from '@/composables/useGoogleLogin.js'
import { applyTheme, loadUnbrandedTheme, surfaceAuraLogo } from '@/config/theme.js'
import { consumeSessionExpiredNotice } from '@/services/sessionExpiry.js'

const email = ref('')
const password = ref('')
const showTermsModal = ref(false)
const isMounted = ref(false)
const sessionNotice = ref('')
const googleUnavailable = ref(false)
const router = useRouter()

const { login, logout, isLoading, error } = useAuth()
const {
  loginWithGoogleCredential,
  isLoading: googleLoading,
  error: googleError,
} = useGoogleLogin()
const visibleMessage = computed(() => error.value || googleError.value || sessionNotice.value)

const nextRoute = ref(null)

onBeforeMount(() => {
  applyTheme(loadUnbrandedTheme())
})

onMounted(() => {
  sessionNotice.value = consumeSessionExpiredNotice()

  setTimeout(() => {
    isMounted.value = true
  }, 50)
})

async function handleLogin() {
  // TEMPORARY TESTING BYPASS: If you type "test" in both fields, it will skip the backend
  if (email.value === 'test' && password.value === 'test') {
    nextRoute.value = { name: 'PreviewHome' }
    showTermsModal.value = true
    return
  }

  const route = await login(email.value, password.value, { preventRedirect: true })
  
  if (route) {
    // Login succeeded, token stored, session initialized.
    // Pause routing and show Terms Modal.
    nextRoute.value = route
    showTermsModal.value = true
  }
}

async function handleGoogleCredential(credential) {
  const route = await loginWithGoogleCredential(credential, { preventRedirect: true })

  if (route) {
    nextRoute.value = route
    showTermsModal.value = true
  }
}

function handleAgree() {
  showTermsModal.value = false
  localStorage.setItem('aura_terms_agreed', 'true')
  if (nextRoute.value) {
    router.push(nextRoute.value)
  }
}

function handleDecline() {
  showTermsModal.value = false
  // Log them out and clear session
  logout()
}

function goToForgotPassword() {
  router.push({ name: 'ForgotPassword' })
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

/* Ensure form area scrolls above keyboard on mobile */
.login-form-area {
  padding-bottom: env(safe-area-inset-bottom, 16px);
}

/* When keyboard is open (viewport shrinks), allow scrolling */
.login-page {
  -webkit-overflow-scrolling: touch;
}
</style>
