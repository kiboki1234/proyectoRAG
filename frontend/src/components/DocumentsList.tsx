import { useEffect, useState } from 'react';
import { getDocuments, type DocumentInfo } from '../lib/api';
import { FileText, Database, Hash } from 'lucide-react';

export default function DocumentsList() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getDocuments();
      setDocuments(data.documents);
      setTotalChunks(data.total_chunks);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  if (loading) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg border">
        <p className="text-gray-500">Cargando documentos...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-700">❌ Error: {error}</p>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-yellow-700">📁 No hay documentos indexados</p>
        <p className="text-sm text-yellow-600 mt-1">Sube algunos documentos para comenzar</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header con estadísticas */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">📚 Documentos en el Corpus</h3>
          <p className="text-sm text-gray-600">
            {documents.length} documento{documents.length !== 1 ? 's' : ''} · {totalChunks.toLocaleString()} chunks totales
          </p>
        </div>
        <button
          onClick={loadDocuments}
          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          🔄 Actualizar
        </button>
      </div>

      {/* Lista de documentos */}
      <div className="space-y-2">
        {documents.map((doc, idx) => {
          const avgChunkSize = Math.round(doc.total_chars / doc.chunks);
          const isLarge = doc.chunks > 100;
          
          return (
            <div
              key={idx}
              className="p-3 bg-white border rounded-lg hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start gap-3">
                {/* Icono */}
                <div className={`mt-1 ${isLarge ? 'text-purple-500' : 'text-blue-500'}`}>
                  <FileText className="h-5 w-5" />
                </div>

                {/* Información del documento */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 truncate" title={doc.name}>
                    {doc.name}
                  </h4>
                  
                  <div className="flex items-center gap-4 mt-1 text-xs text-gray-600">
                    <div className="flex items-center gap-1">
                      <Hash className="h-3 w-3" />
                      <span>{doc.chunks} chunk{doc.chunks !== 1 ? 's' : ''}</span>
                    </div>
                    
                    <div className="flex items-center gap-1">
                      <Database className="h-3 w-3" />
                      <span>~{avgChunkSize} chars/chunk</span>
                    </div>
                    
                    {doc.has_pages && (
                      <div className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-medium">
                        PDF
                      </div>
                    )}
                  </div>

                  {/* Barra de progreso relativa */}
                  <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full ${
                          isLarge ? 'bg-purple-500' : 'bg-blue-500'
                        }`}
                        style={{
                          width: `${Math.min(100, (doc.chunks / Math.max(...documents.map(d => d.chunks))) * 100)}%`
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Porcentaje del corpus */}
                <div className="text-right">
                  <div className="text-lg font-semibold text-gray-900">
                    {((doc.chunks / totalChunks) * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-gray-500">del corpus</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer con leyenda */}
      <div className="p-3 bg-gray-50 rounded-lg border">
        <div className="flex items-center gap-4 text-xs text-gray-600">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-blue-500"></div>
            <span>Documentos estándar</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-purple-500"></div>
            <span>Documentos grandes (&gt;100 chunks)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
