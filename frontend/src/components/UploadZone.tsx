import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { ingestFiles } from '@/lib/api'
import { addLocalSources } from '@/lib/storage'
import { documentEvents } from '@/lib/events'

export default function UploadZone() {
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)

  const onDrop = useCallback((accepted: File[]) => {
    setFiles(prev => [...prev, ...accepted])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/markdown': ['.md', '.markdown'], 'text/plain': ['.txt'] },
  })

  const remove = (name: string) => setFiles(prev => prev.filter(f => f.name !== name))

  const upload = async () => {
    if (!files.length) return toast.info('Selecciona archivos primero')
    try {
      setLoading(true)
      const res = await ingestFiles(files)
      addLocalSources(files.map(f => f.name))
      toast.success(`Ingesta completa: ${res.chunks_indexed} chunks indexados`)
      setFiles([])
      // Emitir evento para que otros componentes se actualicen
      documentEvents.emit('document-uploaded')
    } catch (e: any) {
      toast.error(`Error al ingerir: ${e.message || e}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 shadow-sm">
      <div
        {...getRootProps()}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-8 text-center transition ${
          isDragActive ? 'border-brand-500 dark:border-brand-600 bg-brand-50 dark:bg-brand-900/20' : 'border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="h-8 w-8 text-brand-600 dark:text-brand-500" />
        <p className="text-sm text-gray-600 dark:text-gray-400">Arrastra y suelta PDFs/MD/TXT aquí, o haz clic para seleccionar.</p>
        <p className="text-xs text-gray-400 dark:text-gray-600">Privado y local. Se indexan por fragmentos para búsqueda semántica.</p>
      </div>

      {files.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Archivos seleccionados</div>
          <ul className="space-y-2">
            {files.map(f => (
              <li key={f.name} className="flex items-center justify-between rounded-lg border border-gray-200 dark:border-gray-800 px-3 py-2">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                  <span className="text-sm text-gray-900 dark:text-gray-100">{f.name}</span>
                </div>
                <button className="rounded-lg p-1 hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => remove(f.name)}>
                  <X className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                </button>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex justify-end">
            <button
              onClick={upload}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 dark:bg-brand-700 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:hover:bg-brand-600 disabled:opacity-60"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Ingerir documentos
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
