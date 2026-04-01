import { api } from './index'

export const skillApi = {
  list: () => api.get('/skills'),
  get: (name: string) => api.get(`/skills/${name}`),
  create: (data: any) => api.post('/skills', data),
  update: (name: string, data: any) => api.put(`/skills/${name}`, data),
  delete: (name: string) => api.delete(`/skills/${name}`)
}
