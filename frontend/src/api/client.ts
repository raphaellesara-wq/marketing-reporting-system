import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401: try once with the refresh token, then redirect to login
let isRefreshing = false
let pendingQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = []

const flushQueue = (token: string | null, err: unknown = null) => {
  pendingQueue.forEach((p) => (token ? p.resolve(token) : p.reject(err)))
  pendingQueue = []
}

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config

    // Only intercept 401s that aren't from the auth endpoints themselves
    if (
      err.response?.status !== 401 ||
      original._retry ||
      original.url?.includes('/auth/login') ||
      original.url?.includes('/auth/refresh')
    ) {
      if (err.response?.status === 401) {
        localStorage.clear()
        window.location.href = '/login'
      }
      return Promise.reject(err)
    }

    original._retry = true

    if (isRefreshing) {
      // Queue concurrent requests until refresh completes
      return new Promise((resolve, reject) => {
        pendingQueue.push({
          resolve: (token) => {
            original.headers.Authorization = `Bearer ${token}`
            resolve(api(original))
          },
          reject,
        })
      })
    }

    isRefreshing = true
    const refreshToken = localStorage.getItem('refresh_token')

    if (!refreshToken) {
      isRefreshing = false
      localStorage.clear()
      window.location.href = '/login'
      return Promise.reject(err)
    }

    try {
      const res = await axios.post('/api/auth/refresh', { refresh_token: refreshToken })
      const { access_token, refresh_token: newRefresh } = res.data

      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', newRefresh)

      api.defaults.headers.common.Authorization = `Bearer ${access_token}`
      original.headers.Authorization = `Bearer ${access_token}`

      flushQueue(access_token)
      return api(original)
    } catch (refreshErr) {
      flushQueue(null, refreshErr)
      localStorage.clear()
      window.location.href = '/login'
      return Promise.reject(refreshErr)
    } finally {
      isRefreshing = false
    }
  },
)

export default api
