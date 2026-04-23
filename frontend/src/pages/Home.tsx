import { useEffect, useState } from 'react'
import Dashboard from '../components/Dashboard'
import api from '../api/client'

interface Stats {
  clients: number
  reports: number
  integrations: number
}

export default function Home() {
  const [stats, setStats] = useState<Stats>({ clients: 0, reports: 0, integrations: 0 })

  useEffect(() => {
    Promise.all([
      api.get('/clients').then((r) => r.data.length),
      api.get('/reports').then((r) => r.data.length),
    ]).then(([clients, reports]) => setStats({ clients, reports, integrations: 0 }))
    .catch(() => {})
  }, [])

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="text-gray-500 text-sm mt-1">Overview of your marketing performance</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-brand-600">{stats.clients}</p>
          <p className="text-sm text-gray-500 mt-1">Active Clients</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-brand-600">{stats.reports}</p>
          <p className="text-sm text-gray-500 mt-1">Reports Generated</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-brand-600">50+</p>
          <p className="text-sm text-gray-500 mt-1">Supported Platforms</p>
        </div>
      </div>

      <Dashboard />
    </div>
  )
}
