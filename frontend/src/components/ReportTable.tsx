import { Report } from '../api/reports'
import clsx from 'clsx'

interface Props {
  reports: Report[]
  onDelete?: (id: number) => void
}

const statusColor: Record<string, string> = {
  pending:    'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  completed:  'bg-green-100 text-green-800',
  failed:     'bg-red-100 text-red-800',
}

const formatIcon: Record<string, string> = {
  pdf:        '📄',
  excel:      '📊',
  powerpoint: '📑',
  dashboard:  '🖥️',
}

export default function ReportTable({ reports, onDelete }: Props) {
  if (reports.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-4xl mb-2">📊</p>
        <p className="text-sm">No reports yet. Generate your first report!</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            {['Title', 'Format', 'Frequency', 'Status', 'Generated', 'Actions'].map((h) => (
              <th key={h} className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {reports.map((r) => (
            <tr key={r.id} className="hover:bg-gray-50 transition-colors">
              <td className="py-3 px-4 font-medium text-gray-900">{r.title}</td>
              <td className="py-3 px-4">
                {formatIcon[r.format] ?? '📄'} {r.format.toUpperCase()}
              </td>
              <td className="py-3 px-4 capitalize">{r.frequency}</td>
              <td className="py-3 px-4">
                <span className={clsx('badge', statusColor[r.status] ?? 'bg-gray-100 text-gray-800')}>
                  {r.status}
                </span>
              </td>
              <td className="py-3 px-4 text-gray-500">
                {r.generated_at ? new Date(r.generated_at).toLocaleDateString() : '—'}
              </td>
              <td className="py-3 px-4 flex items-center gap-2">
                {r.file_url && (
                  <a href={r.file_url} className="text-brand-600 hover:underline text-xs" target="_blank" rel="noreferrer">
                    Download
                  </a>
                )}
                {onDelete && (
                  <button
                    onClick={() => onDelete(r.id)}
                    className="text-red-500 hover:text-red-700 text-xs"
                  >
                    Delete
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
