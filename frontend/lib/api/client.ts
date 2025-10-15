/**
 * SCRIBE API Client
 * Real API integration - replaces mock.ts
 */

import {
  Conversation,
  Note,
  NoteSearchResult,
  Metrics,
  ChatMessage
} from '../types'
import { handleResponse } from './error-handler'

// === Configuration ===

const API_BASE_URL = process.env['NEXT_PUBLIC_API_URL'] || 'http://localhost:8000'

/**
 * Get user_id from localStorage session
 */
function getUserId(): string {
  if (typeof window === 'undefined') return 'king_001' // SSR default

  try {
    const session = JSON.parse(localStorage.getItem('session') || '{}')
    return session.user_id || 'king_001'
  } catch {
    return 'king_001'
  }
}

// === Types for API Responses ===

interface LoginResponse {
  user_id: string
  session_id: string
  logged_in: boolean
  expires_at: string
}

interface ConversationsListResponse {
  conversations: Array<{
    id: string
    user_id: string
    title: string
    note_titles: string[]
    message_count: number
    created_at: string
    updated_at: string
  }>
  total: number
}

interface ConversationDetailResponse {
  conversation: {
    id: string
    user_id: string
    title: string
    note_titles: string[]
    message_count: number
    created_at: string
    updated_at: string
  }
  messages: Array<{
    id: string
    role: 'user' | 'plume' | 'mimir'
    content: string
    created_at: string
    metadata?: {
      clickable_objects?: Array<{
        type: 'viz_link' | 'web_link'
        note_id?: string
        title?: string
        url?: string
      }>
      processing_time?: number
      tokens_used?: number
      cost_eur?: number
    }
  }>
}

interface NotesListResponse {
  notes: Array<{
    id: string
    user_id: string
    title: string
    text_content: string
    html_content: string | null
    created_at: string
    updated_at: string
  }>
  total: number
}

interface SearchResponse {
  results: Array<{
    id: string
    title: string
    text_content: string
    html_content: string | null
    created_at: string
    updated_at: string
    relevance_score: number
    snippet: string
  }>
  total: number
  query: string
}

interface DashboardMetrics {
  total_conversations: number
  total_messages: number
  total_notes: number
  total_tokens_used: number
  total_cost_eur: number
  period_start: string
  period_end: string
}

interface UploadAudioResponse {
  note_id: string
  title: string
  transcription: string
  agent_response: string
  processing_time: number
  cost_eur: number
}

interface ConvertHTMLResponse {
  note_id: string
  status: 'processing' | 'completed' | 'failed'
  message: string
}

// === SSE Types ===

export interface SSEMessage {
  type: 'agent_message' | 'agent_action' | 'processing' | 'complete' | 'error' | 'tool_start' | 'tool_complete' | 'tool_activity' | 'start'
  agent?: 'plume' | 'mimir'
  content?: string
  tool?: string
  params?: Record<string, any>
  result?: any
  error?: string
  // Agent action fields (WhatsApp-style notifications)
  action?: string  // Technical action name from backend (e.g., "search_knowledge", "create_note")
  action_text?: string  // DEPRECATED: Legacy field, use action + frontend mapping instead
  // Filtered tool activity from backend (Layer 2)
  label?: string  // UI-friendly label (e.g., "🔍 Recherche archives")
  summary?: string  // UI-friendly summary (e.g., "5 résultats")
  status?: 'running' | 'completed' | 'failed'
  details?: string  // Additional details from backend
  metadata?: {
    processing_time?: number
    tokens_used?: number
    cost_eur?: number
    [key: string]: any  // Allow additional metadata fields
  }
}

// === Helper Functions ===

function parseDate(dateStr: string | Date): Date {
  return dateStr instanceof Date ? dateStr : new Date(dateStr)
}

// === AUTH ===

export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })

  return handleResponse<LoginResponse>(response)
}

// === CONVERSATIONS ===

export async function getConversations(limit = 50): Promise<Conversation[]> {
  const userId = getUserId()
  const response = await fetch(
    `${API_BASE_URL}/api/v1/conversations?user_id=${userId}&limit=${limit}`
  )

  const data = await handleResponse<ConversationsListResponse>(response)

  return data.conversations.map(c => ({
    id: c.id,
    title: c.title,
    note_titles: c.note_titles,
    updated_at: parseDate(c.updated_at),
    message_count: c.message_count
  }))
}

export async function getConversation(id: string): Promise<{ conversation: Conversation, messages: ChatMessage[] }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/conversations/${id}`)

  const data = await handleResponse<ConversationDetailResponse>(response)

  return {
    conversation: {
      id: data.conversation.id,
      title: data.conversation.title,
      note_titles: data.conversation.note_titles,
      updated_at: parseDate(data.conversation.updated_at),
      message_count: data.conversation.message_count
    },
    messages: data.messages.map(m => ({
      id: m.id,
      role: m.role,
      content: m.content,
      timestamp: parseDate(m.created_at),
      ...(m.metadata ? { metadata: m.metadata } : {})
    }))
  }
}

// === NOTES ===

export async function getRecentNotes(limit = 50): Promise<Note[]> {
  const userId = getUserId()
  const response = await fetch(
    `${API_BASE_URL}/api/v1/notes/recent?user_id=${userId}&limit=${limit}`
  )

  const data = await handleResponse<NotesListResponse>(response)

  return data.notes.map(n => ({
    id: n.id,
    title: n.title,
    text_content: n.text_content,
    html_content: n.html_content || '',
    created_at: parseDate(n.created_at),
    updated_at: parseDate(n.updated_at)
  }))
}

export async function getAllNotes(): Promise<Note[]> {
  return getRecentNotes(1000) // Get large limit for "all"
}

export async function getNote(id: string): Promise<Note> {
  const response = await fetch(`${API_BASE_URL}/api/v1/notes/${id}`)

  const data = await handleResponse<{
    id: string
    user_id: string
    title: string
    text_content: string
    html_content: string | null
    created_at: string
    updated_at: string
  }>(response)

  return {
    id: data.id,
    title: data.title,
    text_content: data.text_content,
    html_content: data.html_content || '',
    created_at: parseDate(data.created_at),
    updated_at: parseDate(data.updated_at)
  }
}

export async function searchNotes(query: string): Promise<NoteSearchResult[]> {
  if (!query.trim()) return []

  const userId = getUserId()
  const response = await fetch(
    `${API_BASE_URL}/api/v1/notes/search?q=${encodeURIComponent(query)}&user_id=${userId}`
  )

  const data = await handleResponse<SearchResponse>(response)

  return data.results.map(r => ({
    id: r.id,
    title: r.title,
    text_content: r.text_content,
    html_content: r.html_content || '',
    created_at: parseDate(r.created_at),
    updated_at: parseDate(r.updated_at),
    snippet: r.snippet || r.text_content.substring(0, 150) + '...'
  }))
}

export async function convertToHTML(noteId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/notes/${noteId}/convert-html`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })

  await handleResponse<ConvertHTMLResponse>(response)
}

// === UPLOAD ===

export async function uploadAudio(
  audioFile: File,
  contextText?: string,
  contextAudio?: File
): Promise<UploadAudioResponse> {
  const formData = new FormData()
  formData.append('audio_file', audioFile)

  if (contextText) {
    formData.append('context_text', contextText)
  }

  if (contextAudio) {
    formData.append('context_audio', contextAudio)
  }

  const userId = getUserId()
  formData.append('user_id', userId)

  const response = await fetch(`${API_BASE_URL}/api/v1/upload/audio`, {
    method: 'POST',
    body: formData
  })

  return handleResponse<UploadAudioResponse>(response)
}

export async function uploadText(text: string, context?: string): Promise<Note> {
  const userId = getUserId()

  const response = await fetch(`${API_BASE_URL}/api/v1/upload/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text,
      context,
      user_id: userId
    })
  })

  const data = await handleResponse<{
    note_id: string
    title: string
    text_content: string
    html_content: string | null
  }>(response)

  return {
    id: data.note_id,
    title: data.title,
    text_content: data.text_content,
    html_content: data.html_content || '',
    created_at: new Date(),
    updated_at: new Date()
  }
}

// === CHAT ===

/**
 * Send orchestrated chat message with SSE streaming
 */
export async function sendOrchestratedMessageStream(
  request: {
    message: string
    mode?: 'auto' | 'plume' | 'mimir' | 'discussion'
    conversation_id?: string
    user_id?: string
  },
  onMessage: (message: SSEMessage) => void,
  onComplete: (result: any) => void,
  onError: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/orchestrated/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...request,
        user_id: request.user_id || getUserId()
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    if (!response.body) {
      throw new Error('Response body is null')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.trim() && line.startsWith('data: ')) {
          const jsonStr = line.slice(6)

          if (jsonStr === '[DONE]') {
            return
          }

          try {
            const data: SSEMessage = JSON.parse(jsonStr)

            if (data.type === 'complete') {
              onComplete(data.result)
            } else if (data.type === 'error') {
              onError(new Error(data.error || 'Unknown error'))
            } else {
              onMessage(data)
            }
          } catch (e) {
            console.error('Failed to parse SSE message:', jsonStr, e)
          }
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error : new Error('Unknown error'))
  }
}

/**
 * Send chat message (non-streaming, fallback)
 */
export async function sendChatMessage(message: string, context?: string): Promise<ChatMessage> {
  const userId = getUserId()

  const response = await fetch(`${API_BASE_URL}/api/v1/chat/orchestrated`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      mode: 'auto',
      user_id: userId,
      context
    })
  })

  const data = await handleResponse<{
    response: string
    agent: 'plume' | 'mimir'
    conversation_id: string
    metadata: {
      processing_time: number
      tokens_used: number
      cost_eur: number
      clickable_objects?: Array<{
        type: 'viz_link' | 'web_link'
        note_id?: string
        title?: string
        url?: string
      }>
    }
  }>(response)

  return {
    id: `msg-${Date.now()}`,
    role: data.agent,
    content: data.response,
    timestamp: new Date(),
    metadata: {
      ...(data.metadata.clickable_objects ? { clickable_objects: data.metadata.clickable_objects } : {}),
      ...(data.metadata.processing_time !== undefined ? { processing_time: data.metadata.processing_time } : {}),
      ...(data.metadata.tokens_used !== undefined ? { tokens_used: data.metadata.tokens_used } : {}),
      ...(data.metadata.cost_eur !== undefined ? { cost_eur: data.metadata.cost_eur } : {})
    }
  }
}

// === METRICS ===

export async function getMetrics(): Promise<Metrics> {
  const userId = getUserId()
  const response = await fetch(
    `${API_BASE_URL}/api/v1/metrics/dashboard?user_id=${userId}`
  )

  const data = await handleResponse<DashboardMetrics>(response)

  return {
    total_notes: data.total_notes,
    total_conversations: data.total_conversations,
    total_tokens: data.total_tokens_used,
    total_cost_eur: data.total_cost_eur
  }
}
