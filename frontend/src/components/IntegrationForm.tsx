import { useState, useEffect } from 'react'
import { integrationsApi } from '../api/integrations'
import toast from 'react-hot-toast'

interface Props {
  clientId: number
  onCreated: () => void
  onCancel: () => void
}

const CREDENTIAL_FIELDS: Record<string, { key: string; label: string; placeholder: string }[]> = {
  google_ads: [
    { key: 'developer_token',  label: 'Developer Token',  placeholder: 'ABcDeFgHiJkLmN' },
    { key: 'client_id',        label: 'OAuth Client ID',  placeholder: 'xxx.apps.googleusercontent.com' },
    { key: 'client_secret',    label: 'OAuth Secret',     placeholder: 'GOCSPX-...' },
    { key: 'refresh_token',    label: 'Refresh Token',    placeholder: '1//...' },
    { key: 'customer_id',      label: 'Customer ID',      placeholder: '123-456-7890' },
  ],
  facebook_ads: [
    { key: 'access_token',   label: 'Access Token',   placeholder: 'EAA...' },
    { key: 'ad_account_id',  label: 'Ad Account ID',  placeholder: 'act_123456' },
  ],
  default: [
    { key: 'api_key',    label: 'API Key',    placeholder: 'Your API key' },
    { key: 'account_id', label: 'Account ID', placeholder: 'Your account ID' },
  ],
}

export default function IntegrationForm({ clientId, onCreated, onCancel }: Props) {
  const [platforms, setPlatforms] = useState<string[]>([])
  const [platform, setPlatform] = useState('')
  const [credentials, setCredentials] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    integrationsApi.platforms().then((d) => setPlatforms(d.platforms))
  }, [])

  const fields = CREDENTIAL_FIELDS[platform] ?? CREDENTIAL_FIELDS.default

  const handlePlatformChange = (p: string) => {
    setPlatform(p)
    setCredentials({})
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await integrationsApi.create(clientId, { platform, credentials })
      toast.success(`${platform} integration added!`)
      onCreated()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to add integration'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Platform *</label>
        <select
          className="input"
          required
          value={platform}
          onChange={(e) => handlePlatformChange(e.target.value)}
        >
          <option value="">Select platform…</option>
          {platforms.map((p) => (
            <option key={p} value={p}>
              {p.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </option>
          ))}
        </select>
      </div>

      {platform && fields.map(({ key, label, placeholder }) => (
        <div key={key}>
          <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
          <input
            className="input font-mono text-xs"
            type="password"
            required
            placeholder={placeholder}
            value={credentials[key] ?? ''}
            onChange={(e) => setCredentials({ ...credentials, [key]: e.target.value })}
          />
        </div>
      ))}

      <div className="flex gap-3 justify-end pt-2">
        <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
        <button type="submit" disabled={loading || !platform} className="btn-primary">
          {loading ? 'Connecting…' : 'Connect'}
        </button>
      </div>
    </form>
  )
}
