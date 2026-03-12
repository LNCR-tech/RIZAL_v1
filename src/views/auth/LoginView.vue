<template>
  <div class="min-h-screen flex bg-white font-['Manrope'] overflow-hidden">
    <!-- Left: Decorative Visual Side (Hidden on Mobile) -->
    <div class="hidden lg:flex lg:w-[55%] relative overflow-hidden bg-zinc-950">
      <!-- Animated Background Image -->
      <img 
        src="/images/login-aura-logo.jpg" 
        alt="Aura" 
        class="absolute inset-0 w-full h-full object-contain p-20 z-0 scale-100 animate-slow-zoom"
      />
      
      <!-- Gradient Overlays for depth -->
      <div class="absolute inset-0 bg-gradient-to-tr from-black via-black/20 to-transparent"></div>
      <div class="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/60"></div>

      <!-- Floating Glass Card Info -->
      <div class="absolute bottom-16 left-16 right-16 p-8 rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl animate-fade-in-up">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center border border-white/20">
            <svg viewBox="0 0 24 24" class="w-7 h-7 fill-white" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 22h4l3-6h6l3 6h4L12 2zm-1.5 12l1.5-3 1.5 3h-3z"/>
            </svg>
          </div>
          <div>
            <h3 class="text-white font-bold text-xl leading-none">Aura Ecosystem</h3>
            <p class="text-white/40 text-sm mt-1">Next-gen Education Intelligence</p>
          </div>
        </div>
        <h2 class="text-4xl font-bold text-white mb-4 leading-tight tracking-tight">
          Modernizing campus attendance and analytics.
        </h2>
        <p class="text-white/70 text-lg max-w-lg leading-relaxed">
          Access your centralized dashboard to monitor global trends, manage institutions, and drive academic excellence.
        </p>
      </div>

      <!-- Branding top-left -->
      <div class="absolute top-12 left-12 flex items-center gap-2">
         <span class="text-white/20 text-xs font-bold tracking-[0.3em] uppercase">Enterprise Portal v1.0</span>
      </div>
    </div>

    <!-- Right: Login Form Side -->
    <div class="w-full lg:w-[45%] flex flex-col justify-center px-8 sm:px-16 lg:px-24 bg-zinc-50 relative">
      <!-- Background subtle dots/texture -->
      <div class="absolute inset-0 opacity-[0.03] pointer-events-none" style="background-image: radial-gradient(#000 1px, transparent 1px); background-size: 24px 24px;"></div>

      <!-- Form Container -->
      <div class="max-w-md w-full mx-auto relative z-10 transition-all duration-1000" :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'">
        
        <!-- Mobile Header (Visible on small screens) -->
        <div class="lg:hidden flex flex-col items-center mb-10">
          <div class="w-14 h-14 bg-zinc-900 rounded-2xl flex items-center justify-center mb-4 shadow-xl shadow-zinc-200">
             <svg viewBox="0 0 24 24" class="w-8 h-8 fill-white" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 22h4l3-6h6l3 6h4L12 2zm-1.5 12l1.5-3 1.5 3h-3z"/>
              </svg>
          </div>
          <h2 class="text-2xl font-black text-zinc-900">AURA</h2>
        </div>

        <!-- Section Heading -->
        <div class="mb-10 lg:text-left text-center">
          <h1 class="text-4xl font-black text-zinc-900 mb-3 tracking-tight">Welcome back</h1>
          <p class="text-zinc-500 font-medium text-lg italic">Please sign in to continue to your dashboard.</p>
        </div>

        <!-- The Form -->
        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- Email Field -->
          <div class="space-y-2">
            <label for="email" class="text-sm font-bold text-zinc-600 uppercase tracking-widest ml-1">Email</label>
            <div class="relative group">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-400 group-focus-within:text-zinc-900 transition-colors">
                <MailIcon class="w-5 h-5 stroke-[2.5]" />
              </div>
              <input
                id="email"
                v-model="email"
                type="email"
                required
                placeholder="admin@aura.edu"
                class="block w-full pl-12 pr-4 py-4 bg-white border-2 border-zinc-100 rounded-3xl text-zinc-900 font-semibold placeholder-zinc-300 focus:ring-4 focus:ring-zinc-900/5 focus:border-zinc-900 outline-none transition-all shadow-sm group-hover:border-zinc-200"
                :disabled="isLoading"
              />
            </div>
          </div>

          <!-- Password Field -->
          <div class="space-y-2">
            <div class="flex items-center justify-between ml-1">
              <label for="password" class="text-sm font-bold text-zinc-600 uppercase tracking-widest">Password</label>
              <a href="#" class="text-xs font-black text-zinc-400 hover:text-zinc-900 transition-colors">Recover?</a>
            </div>
            <div class="relative group">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-400 group-focus-within:text-zinc-900 transition-colors">
                <LockIcon class="w-5 h-5 stroke-[2.5]" />
              </div>
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                placeholder="••••••••"
                class="block w-full pl-12 pr-12 py-4 bg-white border-2 border-zinc-100 rounded-3xl text-zinc-900 font-semibold placeholder-zinc-300 focus:ring-4 focus:ring-zinc-900/5 focus:border-zinc-900 outline-none transition-all shadow-sm group-hover:border-zinc-200"
                :disabled="isLoading"
              />
              <button 
                type="button" 
                @click="showPassword = !showPassword"
                class="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 transition-colors p-2"
              >
                <EyeIcon v-if="!showPassword" class="w-5 h-5" />
                <EyeOffIcon v-else class="w-5 h-5" />
              </button>
            </div>
          </div>

          <!-- Extra Options -->
          <div class="flex items-center gap-3 py-1">
            <div class="relative flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                id="remember" 
                class="peer h-6 w-6 cursor-pointer appearance-none rounded-lg border-2 border-zinc-200 checked:bg-zinc-900 checked:border-zinc-900 transition-all"
              >
              <svg class="absolute h-4 w-4 text-white opacity-0 peer-checked:opacity-100 top-1 left-1 pointer-events-none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </div>
            <label for="remember" class="text-sm text-zinc-500 font-bold cursor-pointer">Stay authenticated</label>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="isLoading"
            class="w-full bg-zinc-900 text-white py-5 rounded-3xl font-black text-lg flex items-center justify-center gap-3 hover:bg-black active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-xl shadow-zinc-900/20 group mt-4 overflow-hidden relative"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-white/0 via-white/5 to-white/0 -translate-x-full group-hover:animate-shimmer"></div>
            <span v-if="!isLoading" class="relative z-10">Sign into Portal</span>
            <span v-else class="relative z-10 flex items-center gap-3">
              <div class="w-5 h-5 border-3 border-white/20 border-t-white rounded-full animate-spin"></div>
              Verifying...
            </span>
            <ArrowRightIcon v-if="!isLoading" class="w-5 h-5 relative z-10 group-hover:translate-x-1.5 transition-transform duration-300" />
          </button>
        </form>

        <!-- Error Feedback -->
        <Transition name="slide-up">
          <div v-if="error" class="mt-8 p-5 bg-red-50 border-l-4 border-red-500 rounded-2xl flex items-start gap-4">
            <div class="p-2 bg-red-100 rounded-xl">
              <AlertCircleIcon class="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p class="text-red-900 font-bold text-sm">Security Alert</p>
              <p class="text-red-600/80 text-xs font-semibold mt-0.5 leading-relaxed">{{ error }}</p>
            </div>
          </div>
        </Transition>

        <!-- Branding Footer -->
        <div class="mt-16 pt-12 border-t border-zinc-100 flex flex-col items-center gap-6">
           <div class="flex items-center gap-2">
            <div class="w-5 h-5 flex items-center justify-center">
              <svg viewBox="0 0 24 24" class="w-full h-full fill-zinc-300 animate-pulse" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 22h4l3-6h6l3 6h4L12 2zm-1.5 12l1.5-3 1.5 3h-3z"/>
              </svg>
            </div>
            <span class="text-[10px] font-black text-zinc-300 tracking-[0.2em] uppercase">Powered by Aura Intelligence</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuth } from '@/composables/useAuth.js'
import { 
  Mail as MailIcon, 
  Lock as LockIcon, 
  Eye as EyeIcon, 
  EyeOff as EyeOffIcon, 
  ArrowRight as ArrowRightIcon,
  AlertCircle as AlertCircleIcon
} from 'lucide-vue-next'

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const isMounted = ref(false)

const { login, isLoading, error } = useAuth()

onMounted(() => {
  // Trigger animations
  setTimeout(() => {
    isMounted.value = true
  }, 100)
})

async function handleLogin() {
  await login(email.value, password.value)
}
</script>

<style scoped>
@keyframes slow-zoom {
  from { transform: scale(1.0); }
  to { transform: scale(1.15); }
}

@keyframes shimmer {
  100% { transform: translateX(100%); }
}

.animate-slow-zoom {
  animation: slow-zoom 20s ease-in-out infinite alternate;
}

.animate-shimmer {
  animation: shimmer 2s infinite;
}

.animate-fade-in-up {
  animation: fadeInUp 1s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Custom checkbox animation */
input[type="checkbox"]:checked {
  background-image: url("data:image/svg+xml,%3csvg viewBox='0 0 16 16' fill='white' xmlns='http://www.w3.org/2000/svg'%3e%3cpath d='M12.207 4.793a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L6.5 9.086l4.293-4.293a1 1 0 011.414 0z'/%3e%3c/svg%3e");
}
</style>
