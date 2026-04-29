import { ref, watch } from 'vue'

export function useAiDemo(searchQuery) {
  const isAiCreating = ref(false)
  const aiResult = ref(null)
  
  let timeoutId = null

  watch(searchQuery, (query) => {
    const q = (query || '').trim().toLowerCase()
    
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    
    if (q.includes('create a college') || q.includes('college of engineering')) {
      isAiCreating.value = true
      aiResult.value = null
      
      timeoutId = setTimeout(() => {
        isAiCreating.value = false
        aiResult.value = {
          id: 'ai-mock-1',
          type: 'ai-action',
          label: 'Success! College of Engineering created.',
          sublabel: 'Click here to view the new college in Admin Workspace.',
          route: '/exposed/admin/schools',
        }
      }, 1500)
    } else {
      isAiCreating.value = false
      aiResult.value = null
    }
  })

  return {
    isAiCreating,
    aiResult
  }
}
