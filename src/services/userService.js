import api from './api'

export const userService = {
  async getMe() {
    // Development bypass for Super Admin
    if (localStorage.getItem('aura_token') === 'aura_dev_token_superadmin') {
      const { mockSuperAdminUser } = await import('@/data/mockData.js')
      const impersonateId = localStorage.getItem('aura_impersonate_school_id')
      
      if (impersonateId) {
        return { 
          ...mockSuperAdminUser, 
          school_id: parseInt(impersonateId),
          impersonating: true 
        }
      }
      return mockSuperAdminUser
    }
    
    const response = await api.get('/users/me/')
    return response.data
  },
  
  async updateProfile(profileId, data) {
    const response = await api.patch(`/users/student-profiles/${profileId}`, data)
    return response.data
  }
}
