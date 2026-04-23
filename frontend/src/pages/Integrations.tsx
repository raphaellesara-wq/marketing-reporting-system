import { useEffect, useState } from 'react'
import { integrationsApi, Integration } from '../api/integrations'
import IntegrationForm from '../components/IntegrationForm'
import api from '../api/client'
import toast from 'react-hot-toast'
import clsx from 'clsx'

interface Client { id: number; name: string }

const statusColor: Record<string, string> = {
  active:   'bg-green-100 text-green-800',
  inactive: 'bg-gray-100 text-gray-700',
  error:    'bg-red-100 text-red-800',
  pending:  'bg-yellow-100 text-yellow-800',
}

const platformIcon: Record<string, string> = {
  google_ads:         '🔵',
  facebook_ads:       '🔷',
  instagram_ads:      '📸',
  tiktok_ads:         '🎵',
  linkedin_ads:       '💼',
  pinterest_ads:      '📌',
  amazon_ads:         '🛒',
  microsoft_ads:      '🪟',
  snapchat_ads:       '👻',
  youtube_ads:        '▶️',
  google_analytics_4: '📊',
  mixpanel:           '📈',
  amplitude:          '📉',
  heap:               '🗄️',
  segment:            '⚙️',
  hotjar:             '🔥',
  clarity:            '🔍',
  mailchimp:          '🐵',
  klaviyo:            '📧',
  hubspot:            '🧡',
  shopify:            '🛍️',
  stripe:             '💳',
}

export default function Integrations() {
  const [clients, setClients] = useState<Client[]>([])
  const [selectedClient, setSelectedClient] = useState<number | null>(null)
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState<number | null>(null)

  useEffect(() => {
    api.get('/clients').then((r) => {
      setClients(r.data)
      if (r.data.length > 0) setSelectedClient(r.data[0].id)
    })
  }, [])

  useEffect(() => {
    if (!selectedClient) return
    setLoading(true)
    integrationsApi.list(selectedClient)
      .then(setIntegrations)
      .catch(() => toast.error('Failed to load integrations'))
      .finally(() => setLoading(false))
  }, [selectedClient])

  const handleTest = async (id: number) => {
    setTesting(id)
    try {
      const res = await integrationsApi.test(id)
      toast.success(res.message ?? 'Connection OK!')
      if (selectedClient) {
        const updated = await integrationsApi.list(selectedClient)
        setIntegrations(updated)
      }
    } catch {
      toast.error('Connection test failed')
    } finally {
      setTesting(null)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Remove this integration?')) return
    await integrationsApi.delete(id)
    toast.success('Integration removed')
    if (selectedClient) setIntegrations(await integrationsApi.list(selectedClient))
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Integrations</h2>
          <p className="text-gray-500 text-sm mt-1">Connect your marketing platforms</p>
        </div>
        {selectedClient && (
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            + Connect Platform
          </button>
        )}
      </div>

      {/* Client selector */}
      {clients.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {clients.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedClient(c.id)}
              className={clsx(
                'px-4 py-1.5 rounded-full text-sm font-medium border transition-colors',
                selectedClient === c.id
                  ? 'bg-brand-600 text-white border-brand-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-brand-400',
              )}
            >
              {c.name}
            </button>
          ))}
        </div>
      )}

      {/* Add integration form */}
      {showForm && selectedClient && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Connect New Platform</h3>
          <IntegrationForm
            clientId={selectedClient}
            onCreated={async () => {
              setShowForm(false)
              setIntegrations(await integrationsApi.list(selectedClient))
            }}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {/* Integrations grid */}
      {!selectedClient ? (
        <div className="text-center py-12 text-gray-400">
          <p className="text-4xl mb-2">👥</p>
          <p className="text-sm">Create a client first to add integrations.</p>
        </div>
      ) : loading ? (
        <div className="text-center py-12 text-gray-400">Loading…</div>
      ) : integrations.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p className="text-4xl mb-2">🔗</p>
          <p className="text-sm">No integrations yet. Connect your first platform!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {integrations.map((i) => (
            <div key={i.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{platformIcon[i.platform] ?? '🔌'}</span>
                  <div>
                    <p className="font-semibold text-gray-900 text-sm">
                      {i.display_name ?? i.platform.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                    </p>
                    <p className="text-xs text-gray-400">{i.platform}</p>
                  </div>
                </div>
                <span className={clsx('badge', statusColor[i.status] ?? 'bg-gray-100 text-gray-700')}>
                  {i.status}
                </span>
              </div>

              {i.last_synced_at && (
                <p className="text-xs text-gray-400 mb-3">
                  Last synced: {new Date(i.last_synced_at).toLocaleString()}
                </p>
              )}
              {i.error_message && (
                <p className="text-xs text-red-500 mb-3 truncate" title={i.error_message}>
                  ⚠ {i.error_message}
                </p>
              )}

              <div className="flex gap-2 mt-3">
                <button
                  onClick={() => handleTest(i.id)}
                  disabled={testing === i.id}
                  className="btn-secondary text-xs py-1 px-3"
                >
                  {testing === i.id ? 'Testing…' : '⚡ Test'}
                </button>
                <button
                  onClick={() => handleDelete(i.id)}
                  className="text-xs py-1 px-3 text-red-500 hover:text-red-700 border border-red-200 hover:border-red-400 rounded-lg transition-colors"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Platform coverage banner */}
      <div className="card bg-gradient-to-r from-brand-50 to-blue-50 border-brand-200">
        <h3 className="text-sm font-semibold text-brand-800 mb-3">50+ Supported Platforms</h3>
        <div className="flex flex-wrap gap-2">
          {[
            'Google Ads','Facebook','Instagram','TikTok','LinkedIn','Pinterest',
            'Amazon Ads','Microsoft Ads','Snapchat','YouTube','GA4','Mixpanel',
            'Amplitude','Heap','Segment','Hotjar','Clarity','Mailchimp','Klaviyo',
            'HubSpot','Salesforce','Shopify','WooCommerce','Stripe','PayPal','Zapier',
          ].map((p) => (
            <span key={p} className="px-2 py-1 bg-white rounded-md text-xs text-gray-600 border border-gray-200 shadow-sm">
              {p}
            </span>
          ))}
          <span className="px-2 py-1 bg-white rounded-md text-xs text-brand-600 border border-brand-200 font-medium">
            +25 more
          </span>
        </div>
      </div>
    </div>
  )
}
