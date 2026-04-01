import { api } from './index'

export const memoryApi = {
  list: (params?: any) => api.get('/memory', { params }),
  get: (id: string) => api.get(`/memory/${id}`),
  create: (data: any) => api.post('/memory', data),
  update: (id: string, data: any) => api.put(`/memory/${id}`, data),
  delete: (id: string) => api.delete(`/memory/${id}`),
  search: (q: string) => api.get('/memory/search', { params: { q } })
}
