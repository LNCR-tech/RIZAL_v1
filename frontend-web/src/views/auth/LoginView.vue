<template>
  <div class="login-page min-h-dvh flex flex-col font-[Manrope] overflow-hidden relative" style="background: var(--color-bg);">
    <!-- Decorative Background -->
    <div class="absolute inset-0 z-0 pointer-events-none overflow-hidden">
      <div class="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full blur-[120px] opacity-20 transition-opacity duration-1000" style="background: var(--color-primary);"></div>
      <div class="absolute top-[60%] -right-[10%] w-[40%] h-[60%] rounded-full blur-[150px] opacity-10 transition-opacity duration-1000" style="background: var(--color-primary);"></div>
    </div>

    <!-- Main centered content -->
    <div class="flex-1 flex flex-col lg:flex-row items-center justify-center px-6 lg:px-12 py-12 relative z-10 gap-16 lg:gap-24 w-full max-w-[1200px] mx-auto overflow-y-auto h-full">
      
      <!-- Login Section -->
      <div class="w-full max-w-[360px] flex flex-col gap-8 login-form-area shrink-0 relative">

        <!-- Heading -->
        <div 
          class="flex flex-col gap-2 transition-all duration-1000 ease-[cubic-bezier(0.22,1,0.36,1)] relative"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'"
        >
          <div class="flex items-center gap-2 mb-2">
            <div class="h-[1px] w-6 opacity-30" style="background: var(--color-text-primary);"></div>
            <span class="text-[11px] font-bold tracking-[0.2em] uppercase opacity-60" style="color: var(--color-text-primary);">
              Enterprise OS
            </span>
          </div>
          <h1 
            class="text-[32px] lg:text-[36px] font-extrabold leading-[1.1] tracking-[-0.03em]"
            style="color: var(--color-text-primary);"
          >
            The Intelligence <br /> of your Campus.
          </h1>
          <p class="text-[14px] font-medium opacity-60 mt-1" style="color: var(--color-text-secondary);">
            Log in to the Institutional Operating System.
          </p>
        </div>

        <!-- Form Box -->
        <div 
          class="p-6 sm:p-8 rounded-3xl border transition-all duration-1000 delay-150 ease-[cubic-bezier(0.22,1,0.36,1)] relative overflow-hidden backdrop-blur-xl"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'"
          style="background: color-mix(in srgb, var(--color-surface) 60%, transparent); border-color: color-mix(in srgb, var(--color-border) 50%, transparent); box-shadow: 0 20px 40px -20px rgba(0,0,0,0.1);"
        >
          <form 
            class="flex flex-col gap-4 relative z-10" 
            @submit.prevent="handleLogin"
          >
            <!-- Email -->
            <div class="flex flex-col gap-1.5">
              <label for="email" class="text-[12px] font-semibold opacity-70 ml-1" style="color: var(--color-text-primary);">Work Email</label>
              <BaseInput
                id="email"
                v-model="email"
                type="email"
                placeholder="name@institution.edu"
                autocomplete="email"
                tone="neutral"
                :disabled="isLoading || googleLoading"
                class="!rounded-xl"
              />
            </div>

            <!-- Password -->
            <div class="flex flex-col gap-1.5">
              <div class="flex justify-between items-center ml-1">
                <label for="password" class="text-[12px] font-semibold opacity-70" style="color: var(--color-text-primary);">Password</label>
                <a
                  href="#"
                  class="text-[11px] font-bold transition-colors opacity-60 hover:opacity-100"
                  style="color: var(--color-text-primary);"
                  @click.prevent="goToForgotPassword"
                >
                  Forgot?
                </a>
              </div>
              <BaseInput
                id="password"
                v-model="password"
                type="password"
                placeholder="••••••••"
                autocomplete="current-password"
                tone="neutral"
                :disabled="isLoading || googleLoading"
                @enter="handleLogin"
                class="!rounded-xl"
              />
            </div>

            <!-- Error message -->
            <Transition name="fade">
              <p v-if="visibleMessage" class="text-red-500 text-[12px] font-medium text-center mt-1">
                {{ visibleMessage }}
              </p>
            </Transition>

            <!-- Login Button -->
            <BaseButton
              type="submit"
              variant="primary"
              size="lg"
              class="mt-2 !rounded-xl text-[14px] font-bold shadow-lg shadow-primary/20"
              :loading="isLoading"
              :disabled="googleLoading"
            >
              Log In securely
            </BaseButton>

            <!-- Google Sign-In below Log In -->
            <template v-if="!googleUnavailable">
              <div class="flex items-center gap-3 my-2" aria-hidden="true">
                <div class="flex-1 h-[1px]" style="background: linear-gradient(90deg, transparent, var(--color-border), transparent);"></div>
                <span class="text-[10px] font-bold uppercase tracking-widest opacity-40" style="color: var(--color-text-primary);">or continue with</span>
                <div class="flex-1 h-[1px]" style="background: linear-gradient(90deg, transparent, var(--color-border), transparent);"></div>
              </div>

              <GoogleSignInButton
                @credential="handleGoogleCredential"
                @unavailable="googleUnavailable = true"
                class="!rounded-xl"
              />
            </template>
          </form>
        </div>

        <!-- Powered by Aura -->
        <div 
          class="flex flex-col items-center justify-center gap-3 mt-4 transition-all duration-1000 delay-300 ease-[cubic-bezier(0.22,1,0.36,1)]"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'"
        >
          <div class="flex items-center justify-center gap-2 opacity-80 hover:opacity-100 transition-opacity">
            <img
              :src="surfaceAuraLogo"
              alt="Aura"
              class="h-6 w-auto object-contain grayscale opacity-60"
            />
            <span class="text-[12px] font-bold tracking-tight" style="color: var(--color-text-secondary);">
              Powered by Aura Ai
            </span>
          </div>
        </div>

      </div>

      <!-- Feature Cards Section -->
      <div 
        class="flex-1 w-full max-w-[640px] grid grid-cols-1 sm:grid-cols-2 gap-5 transition-all duration-1000 delay-400 ease-[cubic-bezier(0.22,1,0.36,1)]"
        :class="isMounted ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-12'"
      >
        <div v-for="(card, index) in featureCards" :key="index" 
             class="group p-7 rounded-[24px] border backdrop-blur-md transition-all duration-500 hover:-translate-y-1 hover:shadow-2xl flex flex-col justify-between"
             style="background: color-mix(in srgb, var(--color-surface) 40%, transparent); border-color: color-mix(in srgb, var(--color-border) 40%, transparent); box-shadow: 0 10px 30px -10px rgba(0,0,0,0.05);"
        >
          <div class="flex items-center justify-between mb-8">
            <div class="w-12 h-12 rounded-2xl flex items-center justify-center transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3 shadow-inner" 
                 style="background: color-mix(in srgb, var(--color-primary) 10%, transparent); color: var(--color-primary);">
              <component :is="card.icon" :size="24" stroke-width="1.5" />
            </div>
            <div class="w-8 h-8 rounded-full border flex items-center justify-center opacity-0 -translate-x-4 transition-all duration-500 group-hover:opacity-100 group-hover:translate-x-0" style="border-color: color-mix(in srgb, var(--color-primary) 30%, transparent); color: var(--color-primary);">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>
            </div>
          </div>
          <div>
            <h3 class="text-[18px] font-extrabold mb-2 tracking-tight transition-colors duration-300 group-hover:text-primary" style="color: var(--color-text-primary);">{{ card.title }}</h3>
            <p class="text-[14px] leading-[1.6] opacity-60 font-medium" style="color: var(--color-text-secondary);">{{ card.description }}</p>
          </div>
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
import { 
  Users, 
  ShieldCheck, 
  BarChart3, 
  BrainCircuit 
} from 'lucide-vue-next'
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

const featureCards = [
  {
    title: 'Smart Attendance',
    description: 'Face recognition, QR, and geolocation check-ins for seamless student tracking.',
    icon: Users
  },
  {
    title: 'Governance & Safety',
    description: 'Automated sanctions, clearance workflows, and institutional hierarchy management.',
    icon: ShieldCheck
  },
  {
    title: 'Advanced Analytics',
    description: 'Real-time reporting and predictive insights into campus attendance trends.',
    icon: BarChart3
  },
  {
    title: 'Aura AI Assistant',
    description: 'Natural language queries to interact with your institutional data instantly.',
    icon: BrainCircuit
  }
]

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
