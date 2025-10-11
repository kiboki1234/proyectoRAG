import { Citation } from '@/lib/api'

export type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  timestamp: Date
  cached?: boolean
  searchMode?: string
  temperature?: number
}

export type ChatHistory = Message[]
