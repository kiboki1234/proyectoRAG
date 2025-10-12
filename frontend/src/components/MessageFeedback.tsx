import { useState } from 'react'
import { ThumbsUp, ThumbsDown } from 'lucide-react'
import { getBaseUrl } from '@/lib/storage'
import { toast } from 'sonner'

interface MessageFeedbackProps {
  messageId: string
  question?: string
  answer?: string
}

export function MessageFeedback({ messageId, question, answer }: MessageFeedbackProps) {
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null)
  const [loading, setLoading] = useState(false)

  const handleFeedback = async (type: 'positive' | 'negative') => {
    if (loading) return
    
    setLoading(true)
    try {
      const response = await fetch(`${getBaseUrl()}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message_id: messageId,
          feedback: type,
          question,
          answer
        })
      })

      if (!response.ok) throw new Error('Failed to submit feedback')

      setFeedback(type)
      toast.success('¡Gracias por tu feedback!')
    } catch (error) {
      console.error('Error submitting feedback:', error)
      toast.error('Error al enviar feedback')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex gap-1 mt-2">
      <button
        onClick={() => handleFeedback('positive')}
        disabled={loading || feedback !== null}
        className={`p-1.5 rounded hover:bg-gray-100 transition-colors disabled:opacity-50 ${
          feedback === 'positive' ? 'text-green-600 bg-green-50' : 'text-gray-400'
        }`}
        title="Respuesta útil"
      >
        <ThumbsUp className="h-3.5 w-3.5" />
      </button>
      <button
        onClick={() => handleFeedback('negative')}
        disabled={loading || feedback !== null}
        className={`p-1.5 rounded hover:bg-gray-100 transition-colors disabled:opacity-50 ${
          feedback === 'negative' ? 'text-red-600 bg-red-50' : 'text-gray-400'
        }`}
        title="Respuesta no útil"
      >
        <ThumbsDown className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}
