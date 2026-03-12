import { ref, watch } from 'vue'
import { mockCampuses } from '@/data/mockData.js'

// Try to load from localStorage, otherwise use mock data
let initialCampuses = mockCampuses
try {
    const saved = localStorage.getItem('aura_campuses')
    if (saved) {
        initialCampuses = JSON.parse(saved)
    }
} catch (e) {
    console.error('Failed to parse saved campuses:', e)
}

// Create a globally shared ref
const campuses = ref(initialCampuses)

// Watch for changes and save to localStorage
watch(campuses, (newVal) => {
    localStorage.setItem('aura_campuses', JSON.stringify(newVal))
}, { deep: true })

export function useCampuses() {
    function addCampus(campus) {
        campuses.value.unshift({
            ...campus,
            id: Date.now(), // Unique ID
            students: 0,
            staff: 0,
            status: 'Active'
        })
    }

    function updateCampus(id, updatedData) {
        const index = campuses.value.findIndex(c => c.id === id)
        if (index !== -1) {
            campuses.value[index] = { ...campuses.value[index], ...updatedData }
        }
    }

    return {
        campuses,
        addCampus,
        updateCampus
    }
}
