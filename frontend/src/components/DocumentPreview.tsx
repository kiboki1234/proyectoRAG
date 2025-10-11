import PdfPreview from './PdfPreview'
import TxtPreview from './TxtPreview'
import MarkdownPreview from './MarkdownPreview'

/**
 * Componente que detecta el tipo de archivo y muestra el visor apropiado
 */
export default function DocumentPreview({
  source,
  page,
  highlight,
}: {
  source?: string
  page?: number
  highlight?: string
}) {
  // Detectar tipo de archivo por extensión
  const fileType = source ? getFileType(source) : null

  switch (fileType) {
    case 'pdf':
      return <PdfPreview source={source} page={page} highlight={highlight} />
    
    case 'txt':
      return <TxtPreview source={source} highlight={highlight} />
    
    case 'markdown':
      return <MarkdownPreview source={source} highlight={highlight} />
    
    default:
      // Si no hay source o tipo no reconocido
      return <PdfPreview source={source} page={page} highlight={highlight} />
  }
}

/**
 * Determina el tipo de archivo basado en la extensión
 */
function getFileType(fileName: string): 'pdf' | 'txt' | 'markdown' | null {
  const ext = fileName.split('.').pop()?.toLowerCase()
  
  switch (ext) {
    case 'pdf':
      return 'pdf'
    
    case 'txt':
      return 'txt'
    
    case 'md':
    case 'markdown':
      return 'markdown'
    
    default:
      return null
  }
}
