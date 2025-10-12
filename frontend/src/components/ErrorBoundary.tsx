import { Component, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
  errorInfo?: any
}

/**
 * Error Boundary para capturar errores de React y mostrar UI amigable
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    // Actualizar estado para mostrar UI de fallback
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    // Log del error
    console.error('ErrorBoundary caught error:', error, errorInfo)
    
    // Aquí podrías enviar el error a un servicio de tracking
    // logErrorToService(error, errorInfo)
  }

  handleReload = () => {
    window.location.reload()
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 p-4">
          <div className="max-w-md w-full bg-white rounded-xl shadow-2xl border border-red-100 overflow-hidden">
            {/* Header */}
            <div className="bg-red-50 border-b border-red-100 p-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-red-100 rounded-full">
                  <AlertTriangle className="h-6 w-6 text-red-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Oops! Algo salió mal</h2>
                  <p className="text-sm text-gray-600">Hubo un error inesperado</p>
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="p-6 space-y-4">
              <p className="text-gray-700">
                Lo sentimos, algo no funcionó como esperábamos. Puedes intentar:
              </p>

              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-brand-600 font-bold">•</span>
                  <span>Recargar la página</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-brand-600 font-bold">•</span>
                  <span>Verificar tu conexión a internet</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-brand-600 font-bold">•</span>
                  <span>Limpiar la caché del navegador</span>
                </li>
              </ul>

              {/* Error details (solo en desarrollo) */}
              {this.state.error && (
                <details className="mt-4">
                  <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700">
                    Ver detalles técnicos
                  </summary>
                  <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <pre className="text-xs text-red-600 overflow-auto max-h-40">
                      {this.state.error.toString()}
                      {this.state.error.stack}
                    </pre>
                  </div>
                </details>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={this.handleReload}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors font-medium"
                >
                  <RefreshCw className="h-4 w-4" />
                  Recargar página
                </button>
                <button
                  onClick={this.handleReset}
                  className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                >
                  Intentar de nuevo
                </button>
              </div>
            </div>

            {/* Footer */}
            <div className="bg-gray-50 border-t border-gray-200 px-6 py-4">
              <p className="text-xs text-gray-500 text-center">
                Si el problema persiste, contacta al administrador del sistema
              </p>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
