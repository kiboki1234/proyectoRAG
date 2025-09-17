import { Citation } from '@/lib/api'
import { BookOpen, CornerDownRight } from 'lucide-react'

export default function CitationsList({
  items,
  onJump,
}: {
  items: Citation[]
  onJump: (c: Citation) => void
}) {
  if (!items?.length) return null
  return (
    <div className="mt-4">
      <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-brand-900">
        <BookOpen className="h-4 w-4" /> Citas
      </div>
      <ul className="space-y-2">
        {items.map((c, idx) => (
          <li key={`${c.id}-${idx}`} className="rounded-lg border bg-white p-3 text-sm">
            <div className="flex items-center justify-between gap-2">
              <div className="text-gray-600">
                <span className="font-medium">ID:</span> [{c.id}] · <span className="font-medium">Página:</span> {c.page ?? '—'}
                {c.source ? <> · <span className="font-medium">Archivo:</span> {c.source}</> : null}
              </div>
              {typeof c.page === 'number' && (
                <button
                  className="inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-xs hover:bg-gray-50"
                  onClick={() => onJump(c)}
                  title="Abrir en el visor"
                >
                  <CornerDownRight className="h-3 w-3" /> Ver
                </button>
              )}
            </div>
            <div className="mt-2 line-clamp-3 text-gray-700">{c.text}</div>
          </li>
        ))}
      </ul>
    </div>
  )
}
