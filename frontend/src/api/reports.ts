import api from './client'

export interface Report {
  id: number
  client_id: number
  title: string
  frequency: string
  format: string
  status: string
  date_from: string | null
  date_to: string | null
  platforms: string[] | null
  file_url: string | null
  error_message: string | null
  generated_at: string | null
  created_at: string
}

export interface CreateReportPayload {
  client_id: number
  title: string
  frequency?: string
  format?: string
  date_from?: string
  date_to?: string
  platforms?: string[]
}

export const reportsApi = {
  list: (client_id?: number) =>
    api.get<Report[]>('/reports', { params: client_id ? { client_id } : {} }).then((r) => r.data),

  create: (payload: CreateReportPayload) =>
    api.post<Report>('/reports', payload).then((r) => r.data),

  get: (id: number) => api.get<Report>(`/reports/${id}`).then((r) => r.data),

  delete: (id: number) => api.delete(`/reports/${id}`),

  status: (id: number) => api.get(`/reports/${id}/status`).then((r) => r.data),
}
