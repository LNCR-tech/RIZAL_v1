<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <Transition name="fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[100] bg-black/40 backdrop-blur-[2px]"
        @click="$emit('close')"
      ></div>
    </Transition>

    <!-- Panel -->
    <Transition name="slide-up">
      <div
        v-if="isOpen"
        class="fixed z-[101] bottom-0 left-0 right-0 md:top-24 md:bottom-auto md:left-auto md:right-8 md:w-[420px] w-full bg-[#FCFCFC] rounded-t-[32px] md:rounded-[32px] flex flex-col max-h-[85vh] md:max-h-[80vh] shadow-[0_8px_40px_rgba(0,0,0,0.12)] overflow-hidden font-sans"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-6 pt-6 pb-4 bg-[#FCFCFC]">
          <h2 class="text-[20px] font-bold text-[#111] tracking-tight">Notifications</h2>
          <div class="flex items-center bg-[#F1F1F1] rounded-full p-1 border border-gray-100/50">
            <button
              class="px-4 py-1.5 rounded-full text-[13px] font-semibold transition-all duration-200"
              :class="activeTab === 'all' ? 'bg-white shadow-sm text-[#111]' : 'text-gray-500 hover:text-gray-900'"
              @click="activeTab = 'all'"
            >
              All
            </button>
            <button
              class="px-4 py-1.5 rounded-full text-[13px] font-semibold transition-all duration-200"
              @click="activeTab = 'unread'"
              :class="activeTab === 'unread' ? 'bg-white shadow-sm text-[#111]' : 'text-gray-500 hover:text-gray-900'"
            >
              Unread
            </button>
          </div>
        </div>

        <!-- List -->
        <div class="overflow-y-auto px-6 pb-8 flex-1 custom-scrollbar bg-[#FCFCFC]">
          <div v-if="filteredNotifications.length === 0" class="py-12 text-center text-gray-400 text-sm font-medium">
            No notifications to show.
          </div>
          <div class="flex flex-col gap-3">
            <div
              v-for="item in filteredNotifications"
              :key="item.id"
              class="p-4 rounded-[24px] bg-white flex gap-4 items-start relative transition-transform active:scale-[0.98] cursor-pointer hover:bg-[#FAFAFA]"
              style="box-shadow: 0 2px 10px rgba(0,0,0,0.02);"
            >
              <!-- Unread Indicator (Orange Dot) -->
              <div v-if="item.unread" class="absolute top-5 right-5 w-2 h-2 rounded-full bg-[#FF5A36]"></div>

              <!-- Icon -->
              <div 
                class="flex-shrink-0 w-11 h-11 rounded-full flex items-center justify-center transition-colors shadow-sm" 
                :class="item.iconBgClass || 'bg-[#F4F4F4] text-[#111]'"
              >
                <!-- Render icon dynamically -->
                <component v-if="item.icon" :is="item.icon" :size="20" stroke-width="2.5" />
              </div>

              <!-- Content -->
              <div class="flex-1 min-w-0 pt-0.5">
                <div class="flex items-center gap-2 mb-0.5 pr-4">
                  <h3 class="font-bold text-[15px] text-[#111] truncate tracking-tight">{{ item.title }}</h3>
                  <span class="text-[12px] font-medium text-[#A1A1A1] whitespace-nowrap">{{ item.time }}</span>
                </div>
                <!-- Description might be short or long -->
                <p class="text-[14px] text-[#444] leading-snug mb-1">{{ item.description }}</p>
                
                <!-- Extra Details -->
                <div v-if="item.details" class="text-[13px] text-[#999] font-medium mt-0.5">
                  {{ item.details }}
                </div>

                <!-- Action buttons -->
                <div v-if="item.actions" class="flex gap-2.5 mt-3.5">
                  <button
                    v-for="(action, idx) in item.actions"
                    :key="idx"
                    class="px-5 py-2 rounded-full text-[13px] font-bold transition-transform active:scale-95"
                    :class="action.primary ? 'bg-[#111] text-white shadow-md' : 'bg-[#F6F6F6] text-[#111] hover:bg-[#EBEBEB]'"
                    @click.stop
                  >
                    {{ action.label }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  notifications: { type: Array, default: () => [] }
})

const emit = defineEmits(['close'])

const activeTab = ref('all')

const filteredNotifications = computed(() => {
  if (activeTab.value === 'unread') {
    return props.notifications.filter(n => n.unread)
  }
  return props.notifications
})

watch(() => props.isOpen, (val) => {
  if (typeof document !== 'undefined') {
    if (val) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  }
})

onUnmounted(() => {
  if (typeof document !== 'undefined') {
    document.body.style.overflow = ''
  }
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.4s ease;
}
.slide-up-enter-from, .slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
  @media (max-width: 767px) {
    transform: translateY(100%);
  }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #E0E0E0;
  border-radius: 4px;
}
</style>
