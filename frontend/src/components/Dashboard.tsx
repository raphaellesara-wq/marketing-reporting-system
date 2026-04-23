import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend,
} from 'recharts'

interface KPICardProps {
  label: string
  value: string
  change?: string
  positive?: boolean
}

function KPICard({ label, value, change, positive }: KPICardProps) {
  return (
    <div className="card">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      {change && (
        <p className={`text-xs mt-1 font-medium ${positive ? 'text-green-600' : 'text-red-500'}`}>
          {positive ? '▲' : '▼'} {change} vs last period
        </p>
      )}
    </div>
  )
}

const spendData = [
  { date: 'Mon', google: 1200, facebook: 890, tiktok: 430 },
  { date: 'Tue', google: 1400, facebook: 1020, tiktok: 510 },
  { date: 'Wed', google: 980,  facebook: 760,  tiktok: 390 },
  { date: 'Thu', google: 1600, facebook: 1180, tiktok: 620 },
  { date: 'Fri', google: 1900, facebook: 1400, tiktok: 780 },
  { date: 'Sat', google: 1100, facebook: 830,  tiktok: 290 },
  { date: 'Sun', google: 700,  facebook: 540,  tiktok: 190 },
]

const convData = [
  { date: 'Mon', conversions: 34, roas: 3.2 },
  { date: 'Tue', conversions: 42, roas: 3.8 },
  { date: 'Wed', conversions: 28, roas: 2.9 },
  { date: 'Thu', conversions: 51, roas: 4.1 },
  { date: 'Fri', conversions: 63, roas: 4.5 },
  { date: 'Sat', conversions: 39, roas: 3.6 },
  { date: 'Sun', conversions: 22, roas: 3.0 },
]

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Total Spend"       value="$8,380"  change="12.4%" positive />
        <KPICard label="Total Conversions" value="279"     change="8.1%"  positive />
        <KPICard label="Avg ROAS"          value="3.73x"   change="2.3%"  positive />
        <KPICard label="Avg CPC"           value="$1.84"   change="5.2%"  positive={false} />
      </div>

      {/* Spend by Platform */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Daily Spend by Platform ($)</h3>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={spendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="google"   stackId="1" stroke="#4285F4" fill="#4285F4" fillOpacity={0.6} name="Google Ads" />
            <Area type="monotone" dataKey="facebook" stackId="1" stroke="#1877F2" fill="#1877F2" fillOpacity={0.6} name="Facebook" />
            <Area type="monotone" dataKey="tiktok"   stackId="1" stroke="#010101" fill="#010101" fillOpacity={0.4} name="TikTok" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Conversions */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Conversions &amp; ROAS</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={convData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left"  dataKey="conversions" fill="#3B82F6" name="Conversions" radius={[4,4,0,0]} />
            <Bar yAxisId="right" dataKey="roas"        fill="#10B981" name="ROAS"        radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
