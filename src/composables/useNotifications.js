import { ref, computed } from 'vue'
import { Download, Hexagon, Flag, Smartphone } from 'lucide-vue-next'

const showNotifications = ref(false)

const mockNotifications = ref([
  {
    id: 1,
    icon: Download,
    iconBgClass: 'bg-[#F4F4F4] text-[#111]',
    title: 'Registration Approved',
    time: '30m ago',
    description: 'Campus Event Confirmed',
    details: 'Ticket ID: #4421 credited to account',
    unread: true,
  },
  {
    id: 2,
    icon: Hexagon,
    iconBgClass: 'bg-[#111] text-white',
    title: 'Aura Token Received',
    time: '1h ago',
    description: 'Participation Reward',
    details: '10 Tokens',
    unread: true,
  },
  {
    id: 3,
    icon: Flag,
    iconBgClass: 'bg-[#F4F4F4] text-[#111]',
    title: 'Attendance Flagged',
    time: '1h ago',
    description: 'Manual Justification Required',
    details: 'Missed latest program assembly',
    unread: false,
    actions: [
      { label: 'Decline', primary: false },
      { label: 'Accept', primary: true }
    ]
  },
  {
    id: 4,
    icon: Hexagon,
    iconBgClass: 'bg-[#111] text-white',
    title: 'Aura Token Sent',
    time: '1.5h ago',
    description: 'Merchandise Redemption',
    details: '16 Tokens',
    unread: false,
  },
  {
    id: 5,
    icon: Smartphone,
    iconBgClass: 'bg-[#F4F4F4] text-[#888]',
    title: 'Security Notice',
    time: '2h ago',
    description: 'New Device Login',
    details: 'Manila, Philippines',
    unread: false,
  }
])

const unreadNotifCount = computed(() => mockNotifications.value.filter(n => n.unread).length)

export function useNotifications() {
  function toggleNotifications() {
    showNotifications.value = !showNotifications.value
  }

  return {
    showNotifications,
    mockNotifications,
    unreadNotifCount,
    toggleNotifications
  }
}
