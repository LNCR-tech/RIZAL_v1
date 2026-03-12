import axios from 'axios'
import router from '@/router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://backend-c65g.onrender.com',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: add token to headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('aura_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isDevToken = localStorage.getItem('aura_token') === 'aura_dev_token_superadmin'
    
    if (error.response?.status === 401 && !isDevToken) {
      localStorage.removeItem('aura_token')
      localStorage.removeItem('aura_user_roles')
      router.push({ name: 'Login' })
    }
    return Promise.reject(error)
  }
)

export default api
