/**
 * 类型定义
 */

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
}

export interface ChatRequest {
  message: string
  session_id?: string
}

export interface ChatResponse {
  reply: string
  sources: string[]
  session_id: string
}

export interface DocumentInfo {
  id: string
  filename: string
  chunk_count: number
  indexed_at: string
}

export interface DocumentListResponse {
  documents: DocumentInfo[]
  total: number
}
