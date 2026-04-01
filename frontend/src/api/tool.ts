import { api } from './index'

export const toolApi = {
  list: () => api.get('/tools'),
  listBuiltin: () => api.get('/tools/builtin'),
  get: (name: string) => api.get(`/tools/${name}`),
  create: (data: any) => api.post('/tools', data),
  update: (name: string, data: any) => api.put(`/tools/${name}`, data),
  delete: (name: string) => api.delete(`/tools/${name}`),
  addReference: (name: string, filename: string, content: string) =>
    api.post(`/tools/${name}/references`, { filename, content }),
  addScript: (name: string, filename: string, content: string) =>
    api.post(`/tools/${name}/scripts`, { filename, content })
}
