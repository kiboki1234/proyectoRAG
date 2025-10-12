import { useMemo } from 'react'
import { pdfjsViewerUrl } from '@/lib/pdf'

export default function PdfPreview({
  source,
  page,
  highlight,
}: {
  source?: string
  page?: number
  highlight?: string
}) {
  const url = useMemo(() => {
    if (!source) return null
    return pdfjsViewerUrl(source, page, highlight)
  }, [source, page, highlight])

  if (!source) {
    return (
      <div className="flex h-[72vh] items-center justify-center rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 text-sm text-gray-500 dark:text-gray-400 shadow-sm">
        Selecciona un documento para previsualizarlo aquí.
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm overflow-hidden">
      {/* La key fuerza reload cuando cambia la URL (evita caches del iframe) */}
      <iframe key={url || 'empty'} src={url!} className="h-[72vh] w-full" />
    </div>
  )
}
