import { useState, useCallback } from 'react'
import api from './client'

export interface User {
  id: number
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string
}

export function useAuth() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'))
  const [user, setUser] = useState<User | null>(() => {
    const u = localStorage.getItem('user')
    return u ? JSON.parse(u) : null
  })

  const login = useCallback(async (email: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    const res = await api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    const { access_token, refresh_token, user: u } = res.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    localStorage.setItem('user', JSON.stringify(u))
    setToken(access_token)
    setUser(u)
    return u
  }, [])

  const signup = useCallback(async (email: string, password: string, full_name?: string) => {
    const res = await api.post('/auth/signup', { email, password, full_name })
    return res.data
  }, [])

  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      // Best-effort — invalidate on server; ignore errors
      await api.post('/auth/logout', { refresh_token: refreshToken }).catch(() => {})
    }
    localStorage.clear()
    setToken(null)
    setUser(null)
  }, [])

  return { token, user, login, signup, logout }
}
