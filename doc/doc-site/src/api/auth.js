import axios from 'axios';

// Docusaurus uses different env variable pattern
const BACKEND_URL = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8001'
  : (typeof process !== 'undefined' && process.env?.DOCUSAURUS_BACKEND_URL) || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const login = async (email, password, rememberMe = false) => {
  const response = await apiClient.post('/auth/login', {
    email,
    password,
    remember_me: rememberMe,
  });
  return response.data;
};

export const setAuthToken = (token) => {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
};

export default apiClient;
