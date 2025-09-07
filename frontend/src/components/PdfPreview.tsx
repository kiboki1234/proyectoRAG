import { pdfjsViewerUrl } from '@/lib/pdf'
import { FileText, Eye } from 'lucide-react'

export default function PdfPreview({ source, page, highlight }: { source?: string; page?: number; highlight?: string }) {
  const src = source ? pdfjsViewerUrl(source, page, highlight) : ''

  return (
    <div className="flex h-[72vh] flex-col rounded-2xl border bg-white shadow-sm">
      <div className="flex items-center justify-between border-b px-3 py-2">
        <div className="flex items-center gap-2 text-sm text-gray-700">
          <Eye className="h-4 w-4 text-brand-600" /> Vista previa del documento
        </div>
        <div className="text-xs text-gray-500 truncate max-w-[60%]">
          {source ? source : '— Ningún documento seleccionado —'}
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        {source ? (
          <iframe
            key={`${source}-${page ?? ''}-${highlight ?? ''}`} // fuerza recarga al cambiar página/búsqueda
            title={`preview-${source}`}
            src={src}
            className="h-full w-full"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-gray-400">
            <div className="flex flex-col items-center gap-2">
              <FileText className="h-10 w-10" />
              <p className="text-sm">Selecciona un PDF para previsualizarlo</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
