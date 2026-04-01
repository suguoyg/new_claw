import { api } from './index'

export const modelApi = {
  list: () => api.get('/models'),
  addDialog: (data: any) => api.post('/models/dialog', data),
  addEmbedding: (data: any) => api.post('/models/embedding', data),
  deleteDialog: (provider: string) => api.delete(`/models/dialog/${provider}`),
  deleteEmbedding: (provider: string) => api.delete(`/models/embedding/${provider}`),
  test: (data: any) => api.post('/models/test', data)
}
