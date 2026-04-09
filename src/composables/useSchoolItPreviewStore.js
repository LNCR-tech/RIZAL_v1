import { reactive, watch } from 'vue'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'

const SESSION_KEY = 'aura_school_it_preview_v1'

const initialState = {
  user: schoolItPreviewData.user,
  schoolSettings: schoolItPreviewData.schoolSettings,
  departments: [...schoolItPreviewData.departments],
  programs: [...schoolItPreviewData.programs],
  users: [...schoolItPreviewData.users],
  events: [...schoolItPreviewData.events],
  attendanceSummary: { ...schoolItPreviewData.attendanceSummary },
}

function loadState() {
  try {
    const stored = sessionStorage.getItem(SESSION_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.error('Failed to load preview state', e)
  }
  return initialState
}

const state = reactive(loadState())

watch(state, (next) => {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(next))
  } catch (e) {
    console.error('Failed to sync preview state', e)
  }
}, { deep: true })

export function useSchoolItPreviewStore() {
  const resetStore = () => {
    Object.assign(state, JSON.parse(JSON.stringify(initialState)))
  }

  const deleteStudent = (studentId) => {
    state.users = state.users.filter(u => Number(u.id) !== Number(studentId))
  }

  const updateStudentAssignment = (userId, departmentId, programId) => {
    const user = state.users.find(u => Number(u.id) === Number(userId))
    if (user && user.student_profile) {
      user.student_profile.department_id = departmentId
      user.student_profile.program_id = programId
    }
  }

  const addEvent = (event) => {
    const id = state.events.length > 0 ? Math.max(...state.events.map(e => e.id)) + 1 : 1
    state.events.unshift({
      ...event,
      id,
      attendances: [],
      attendance_summary: {
        total_attendance_records: 0,
        present_count: 0,
        late_count: 0,
        absent_count: 0,
        excused_count: 0,
      }
    })
  }

  const updateEvent = (eventId, payload) => {
    const index = state.events.findIndex(e => Number(e.id) === Number(eventId))
    if (index !== -1) {
      state.events[index] = { ...state.events[index], ...payload }
    }
  }

  const deleteEvent = (eventId) => {
    state.events = state.events.filter(e => Number(e.id) !== Number(eventId))
  }

  const updateSettings = (payload) => {
    state.schoolSettings = { ...state.schoolSettings, ...payload }
  }

  return {
    state,
    resetStore,
    deleteStudent,
    updateStudentAssignment,
    addEvent,
    updateEvent,
    deleteEvent,
    updateSettings,
  }
}
