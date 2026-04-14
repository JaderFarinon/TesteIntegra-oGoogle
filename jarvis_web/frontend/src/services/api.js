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

export const dashboardApi = {
  tasks: () => moduleApi.list('tasks'),
  appointments: () => moduleApi.list('appointments'),
  expenses: () => moduleApi.list('expenses'),
  reminders: () => moduleApi.list('reminders'),
}

export const chatApi = {
  listConversations: () => api.get('/api/conversations'),
  createConversation: (title) => api.post('/api/conversations', { title }),
  listMessages: (conversationId) => api.get('/api/messages', { params: { conversation_id: conversationId } }),
  sendAssistantMessage: (message, conversationId = null) =>
    api.post('/api/assistant/chat', {
      message,
      conversation_id: conversationId,
    }),
}

export const settingsApi = {
  fetch: () => api.get('/api/settings/openai'),
  save: (payload) => api.put('/api/settings/openai', payload),
}

export default api
