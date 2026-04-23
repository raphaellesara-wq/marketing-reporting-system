import { useEffect, useState } from 'react'
import { reportsApi, Report, CreateReportPayload } from '../api/reports'
import ReportTable from '../components/ReportTable'
import api from '../api/client'
import toast from 'react-hot-toast'

interface Client { id: number; name: string }

export default function Reports() {
  const [reports, setReports] = useState<Report[]>([])
  const [clients, setClients] = useState<Client[]>([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState<CreateReportPayload>({
    client_id: 0,
    title: '',
    frequency: 'manual',
    format: 'pdf',
  })

  const load = () => {
    setLoading(true)
    Promise.all([reportsApi.list(), api.get('/clients').then((r) => r.data)])
      .then(([reps, cls]) => { setReports(reps); setClients(cls) })
      .catch(() => toast.error('Failed to load reports'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await reportsApi.create(form)
      toast.success('Report queued!')
      setShowForm(false)
      load()
    } catch {
      toast.error('Failed to create report')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this report?')) return
    await reportsApi.delete(id)
    toast.success('Deleted')
    load()
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Reports</h2>
          <p className="text-gray-500 text-sm mt-1">{reports.length} reports total</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(true)}>+ Generate Report</button>
      </div>

      {showForm && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">New Report</h3>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Client *</label>
                <select
                  className="input"
                  required
                  value={form.client_id}
                  onChange={(e) => setForm({ ...form, client_id: Number(e.target.value) })}
                >
                  <option value={0}>Select client…</option>
                  {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                <input
                  className="input"
                  required
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="Monthly Performance Report"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
                <select
                  className="input"
                  value={form.format}
                  onChange={(e) => setForm({ ...form, format: e.target.value })}
                >
                  {['pdf','excel','powerpoint','dashboard'].map((f) => (
                    <option key={f} value={f}>{f.toUpperCase()}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Frequency</label>
                <select
                  className="input"
                  value={form.frequency}
                  onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                >
                  {['manual','daily','weekly','monthly'].map((f) => (
                    <option key={f} value={f}>{f.charAt(0).toUpperCase() + f.slice(1)}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-3 justify-end">
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button type="submit" className="btn-primary">Generate</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        {loading
          ? <div className="text-center py-8 text-gray-400">Loading…</div>
          : <ReportTable reports={reports} onDelete={handleDelete} />
        }
      </div>
    </div>
  )
}
