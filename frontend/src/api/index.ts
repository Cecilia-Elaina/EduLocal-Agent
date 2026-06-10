/**
 * API 调用模块
 */

import axios from 'axios'
import type { ChatRequest, ChatResponse, DocumentListResponse } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

/**
 * 发送聊天消息
 */
export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/chat/', request)
  return response.data
}

/**
 * 流式发送聊天消息
 */
export async function sendMessageStream(
  request: ChatRequest,
  callbacks: {
    onAgent?: (agent: string) => void
    onRetrieval?: (count: number) => void
    onContent?: (content: string) => void
    onDone?: (sources: string[]) => void
    onError?: (error: string) => void
  }
): Promise<string> {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  let fullReply = ''

  if (reader) {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            switch (data.type) {
              case 'agent':
                callbacks.onAgent?.(data.agent)
                break
              case 'retrieval':
                callbacks.onRetrieval?.(data.count)
                break
              case 'content':
                fullReply += data.content
                callbacks.onContent?.(data.content)
                break
              case 'done':
                callbacks.onDone?.(data.sources)
                break
              case 'error':
                callbacks.onError?.(data.message)
                break
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  }

  return fullReply
}

/**
 * 获取对话历史
 */
export async function getChatHistory(sessionId: string) {
  const response = await api.get(`/chat/history/${sessionId}`)
  return response.data
}

/**
 * 获取会话列表
 */
export async function getSessions() {
  const response = await api.get('/chat/sessions')
  return response.data
}

/**
 * 上传文档（带进度回调）
 */
export async function uploadDocument(
  file: File,
  onProgress?: (percent: number) => void
) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress?.(percent)
      }
    },
  })
  return response.data
}

/**
 * 获取文档列表
 */
export async function getDocuments(): Promise<DocumentListResponse> {
  const response = await api.get<DocumentListResponse>('/documents/')
  return response.data
}

/**
 * 删除文档
 */
export async function deleteDocument(documentId: string) {
  const response = await api.delete(`/documents/${documentId}`)
  return response.data
}

/**
 * 获取设置
 */
export async function getSettings() {
  const response = await api.get('/settings/')
  return response.data
}

/**
 * 获取可用模型列表
 */
export async function getModels(provider: string = 'deepseek') {
  const response = await api.get(`/settings/models?provider=${provider}`)
  return response.data
}

/**
 * 更新 LLM 设置
 */
export async function updateLLMSettings(settings: {
  provider: string
  api_key?: string
  model_name: string
  base_url?: string
  temperature?: number
}) {
  const response = await api.put('/settings/llm', settings)
  return response.data
}

/**
 * 获取系统状态
 */
export async function getSystemStatus() {
  const response = await api.get('/settings/status')
  return response.data
}
