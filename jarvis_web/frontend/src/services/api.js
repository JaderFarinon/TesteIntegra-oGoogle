import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const moduleApi = {
  list: (module) => api.get(`/api/${module}`),
  create: (module, payload) => api.post(`/api/${module}`, payload),
  update: (module, id, payload) => api.put(`/api/${module}/${id}`, payload),
  remove: (module, id) => api.delete(`/api/${module}/${id}`),
}

export const chatApi = {
  history: () => api.get('/api/chat/history'),
  send: (message) => api.post('/api/chat', { message }),
}

export const settingsApi = {
  fetch: () => api.get('/api/settings'),
}
