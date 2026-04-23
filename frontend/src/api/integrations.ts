import api from './client'

export interface Integration {
  id: number
  client_id: number
  platform: string
  display_name: string | null
  status: string
  last_synced_at: string | null
  error_message: string | null
  config: Record<string, unknown> | null
  created_at: string
}

export interface CreateIntegrationPayload {
  platform: string
  display_name?: string
  credentials: Record<string, string>
  config?: Record<string, unknown>
}

export const integrationsApi = {
  platforms: () =>
    api.get<{ platforms: string[]; total: number }>('/integrations/platforms').then((r) => r.data),

  list: (client_id: number) =>
    api.get<Integration[]>(`/integrations/clients/${client_id}`).then((r) => r.data),

  create: (client_id: number, payload: CreateIntegrationPayload) =>
    api.post<Integration>(`/integrations/clients/${client_id}`, payload).then((r) => r.data),

  get: (id: number) => api.get<Integration>(`/integrations/${id}`).then((r) => r.data),

  update: (id: number, payload: Partial<CreateIntegrationPayload>) =>
    api.put<Integration>(`/integrations/${id}`, payload).then((r) => r.data),

  delete: (id: number) => api.delete(`/integrations/${id}`),

  test: (id: number) => api.post(`/integrations/${id}/test`).then((r) => r.data),
}
