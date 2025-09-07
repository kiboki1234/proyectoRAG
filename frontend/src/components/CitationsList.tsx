import { Citation } from '@/lib/api'
import { FileSearch } from 'lucide-react'

export default function CitationsList({
  items,
  onJump,
}: {
  items: Citation[]
  onJump?: (c: Citation) => void
}) {
  if (!items?.length) return null
  return (
    <div className="mt-4">
      <div className="mb-2 flex items-center gap-2 text-sm font-medium text-gray-700">
        <FileSearch className="h-4 w-4" /> Citas
      </div>
      <ul className="space-y-2">
        {items.map((c) => (
          <li
            key={c.id}
            className="cursor-pointer rounded-lg border bg-white p-3 shadow-sm transition hover:bg-gray-50"
            onClick={() => onJump?.(c)}
            title={c.page ? `Ir a la página ${c.page}` : 'Abrir en documento'}
          >
            <div className="mb-1 text-xs text-gray-500">
              ID: [{c.id}] {typeof c.page === 'number' ? `• Página ${c.page}` : ''} {c.source ? `• ${c.source}` : ''}
            </div>
            <p className="text-sm leading-relaxed">{c.text}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}
