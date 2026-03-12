import api from './api'

export const eventService = {
  async getEvents(params = {}) {
    if (localStorage.getItem('aura_token') === 'aura_dev_token_superadmin') {
      const { mockEvents } = await import('@/data/mockData.js')
      return mockEvents
    }
    const response = await api.get('/events/', { params })
    return response.data
  },
  
  async getOngoingEvents() {
    const response = await api.get('/events/ongoing')
    return response.data
  },
  
  async getMyAttendance() {
    if (localStorage.getItem('aura_token') === 'aura_dev_token_superadmin') {
      return [] // Super admins don't have attendance records in dev mode
    }
    const response = await api.get('/attendance/me/records')
    return response.data
  }
}
