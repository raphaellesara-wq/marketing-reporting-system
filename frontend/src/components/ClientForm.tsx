import { useState } from 'react'
import api from '../api/client'
import toast from 'react-hot-toast'

interface Props {
  onCreated: () => void
  onCancel: () => void
}

export default function ClientForm({ onCreated, onCancel }: Props) {
  const [form, setForm] = useState({
    name: '',
    company: '',
    email: '',
    phone: '',
    brand_color_primary: '#3B82F6',
    brand_color_secondary: '#1E40AF',
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/clients', form)
      toast.success('Client created!')
      onCreated()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to create client'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
          <input
            className="input"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Client name"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
          <input
            className="input"
            value={form.company}
            onChange={(e) => setForm({ ...form, company: e.target.value })}
            placeholder="Company name"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            className="input"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            placeholder="client@example.com"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
          <input
            className="input"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            placeholder="+1 555 000 0000"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Primary Color</label>
          <div className="flex gap-2 items-center">
            <input
              type="color"
              value={form.brand_color_primary}
              onChange={(e) => setForm({ ...form, brand_color_primary: e.target.value })}
              className="h-9 w-16 rounded border border-gray-300 cursor-pointer"
            />
            <input
              className="input"
              value={form.brand_color_primary}
              onChange={(e) => setForm({ ...form, brand_color_primary: e.target.value })}
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Secondary Color</label>
          <div className="flex gap-2 items-center">
            <input
              type="color"
              value={form.brand_color_secondary}
              onChange={(e) => setForm({ ...form, brand_color_secondary: e.target.value })}
              className="h-9 w-16 rounded border border-gray-300 cursor-pointer"
            />
            <input
              className="input"
              value={form.brand_color_secondary}
              onChange={(e) => setForm({ ...form, brand_color_secondary: e.target.value })}
            />
          </div>
        </div>
      </div>

      <div className="flex gap-3 justify-end pt-2">
        <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? 'Creating…' : 'Create Client'}
        </button>
      </div>
    </form>
  )
}
