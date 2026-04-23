import { useEffect, useState } from 'react'
import api from '../api/client'
import ClientForm from '../components/ClientForm'
import toast from 'react-hot-toast'

interface Client {
  id: number
  name: string
  company: string | null
  email: string | null
  brand_color_primary: string
  is_active: boolean
  created_at: string
}

export default function Clients() {
  const [clients, setClients] = useState<Client[]>([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.get('/clients')
      .then((r) => setClients(r.data))
      .catch(() => toast.error('Failed to load clients'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this client?')) return
    await api.delete(`/clients/${id}`)
    toast.success('Client deleted')
    load()
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Clients</h2>
          <p className="text-gray-500 text-sm mt-1">{clients.length} active clients</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(true)}>
          + New Client
        </button>
      </div>

      {showForm && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">New Client</h3>
          <ClientForm onCreated={() => { setShowForm(false); load() }} onCancel={() => setShowForm(false)} />
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading…</div>
      ) : clients.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p className="text-4xl mb-2">👥</p>
          <p className="text-sm">No clients yet. Add your first client!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {clients.map((c) => (
            <div key={c.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm"
                    style={{ backgroundColor: c.brand_color_primary }}
                  >
                    {c.name[0]}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{c.name}</p>
                    <p className="text-xs text-gray-500">{c.company ?? '—'}</p>
                  </div>
                </div>
                <button onClick={() => handleDelete(c.id)} className="text-gray-400 hover:text-red-500 text-xs">✕</button>
              </div>
              {c.email && <p className="text-xs text-gray-500 mt-3">{c.email}</p>}
              <p className="text-xs text-gray-400 mt-2">
                Added {new Date(c.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
