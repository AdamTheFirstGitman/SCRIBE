/**
 * Chat API Client
 * Handles communication with Plume and Mimir agents
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export type Agent = 'plume' | 'mimir'
export type MessageRole = 'user' | 'plume' | 'mimir'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: Date
  metadata?: {
    agent_used?: string
    processing_time?: number
    sources?: string[]
    confidence?: number
  }
}

export interface ChatRequest {
  message: string
  agent: Agent
  conversation_id?: string
  context?: {
    recent_uploads?: string[]
    search_query?: string
  }
}

export interface ChatResponse {
  message: string
  agent: Agent
  conversation_id: string
  metadata: {
    processing_time: number
    sources?: string[]
    confidence?: number
    agent_reasoning?: string
  }
}

export interface ConversationHistory {
  id: string
  messages: ChatMessage[]
  created_at: string
  updated_at: string
  agents_involved: Agent[]
}

class ChatAPIError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: any
  ) {
    super(message)
    this.name = 'ChatAPIError'
  }
}

/**
 * Send message to an agent
 */
export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/${request.agent}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: request.message,
        conversation_id: request.conversation_id,
        context: request.context || {}
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new ChatAPIError(
        response.status,
        errorData?.detail || `Chat failed: ${response.statusText}`,
        errorData
      )
    }

    const data = await response.json()
    return data

  } catch (error) {
    if (error instanceof ChatAPIError) {
      throw error
    }

    throw new ChatAPIError(
      0,
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

/**
 * Send message with streaming response
 */
export async function sendMessageStream(
  request: ChatRequest,
  onChunk: (chunk: string) => void,
  onComplete: (response: ChatResponse) => void,
  onError: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/${request.agent}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: request.message,
        conversation_id: request.conversation_id,
        context: request.context || {}
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new ChatAPIError(
        response.status,
        errorData?.detail || `Stream failed: ${response.statusText}`,
        errorData
      )
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response stream available')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\\n')

        // Keep the last incomplete line in buffer
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.trim()) {
            try {
              // Handle SSE format
              if (line.startsWith('data: ')) {
                const jsonStr = line.slice(6)

                if (jsonStr === '[DONE]') {
                  break
                }

                const data = JSON.parse(jsonStr)

                if (data.type === 'chunk') {
                  onChunk(data.content)
                } else if (data.type === 'complete') {
                  onComplete(data.response)
                }
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE line:', line)
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }

  } catch (error) {
    if (error instanceof ChatAPIError) {
      onError(error)
    } else {
      onError(new ChatAPIError(
        0,
        `Stream error: ${error instanceof Error ? error.message : 'Unknown error'}`
      ))
    }
  }
}

/**
 * Get conversation history
 */
export async function getConversation(conversationId: string): Promise<ConversationHistory> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}`)

    if (!response.ok) {
      if (response.status === 404) {
        throw new ChatAPIError(404, 'Conversation not found')
      }

      const errorData = await response.json().catch(() => null)
      throw new ChatAPIError(
        response.status,
        errorData?.detail || `Failed to get conversation: ${response.statusText}`,
        errorData
      )
    }

    return await response.json()

  } catch (error) {
    if (error instanceof ChatAPIError) {
      throw error
    }

    throw new ChatAPIError(
      0,
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

/**
 * List recent conversations
 */
export async function listConversations(limit: number = 20): Promise<ConversationHistory[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/conversations?limit=${limit}`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new ChatAPIError(
        response.status,
        errorData?.detail || `Failed to list conversations: ${response.statusText}`,
        errorData
      )
    }

    return await response.json()

  } catch (error) {
    if (error instanceof ChatAPIError) {
      throw error
    }

    throw new ChatAPIError(
      0,
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

/**
 * Delete conversation
 */
export async function deleteConversation(conversationId: string): Promise<{ message: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      if (response.status === 404) {
        throw new ChatAPIError(404, 'Conversation not found')
      }

      const errorData = await response.json().catch(() => null)
      throw new ChatAPIError(
        response.status,
        errorData?.detail || `Failed to delete conversation: ${response.statusText}`,
        errorData
      )
    }

    return await response.json()

  } catch (error) {
    if (error instanceof ChatAPIError) {
      throw error
    }

    throw new ChatAPIError(
      0,
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

/**
 * Transcribe audio to text (for voice input)
 */
export async function transcribeAudio(audioBlob: Blob): Promise<{ text: string; confidence: number }> {
  try {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')

    const response = await fetch(`${API_BASE_URL}/transcribe`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new ChatAPIError(
        response.status,
        errorData?.detail || `Transcription failed: ${response.statusText}`,
        errorData
      )
    }

    return await response.json()

  } catch (error) {
    if (error instanceof ChatAPIError) {
      throw error
    }

    throw new ChatAPIError(
      0,
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

/**
 * Get chat service health status
 */
export async function getChatHealth(): Promise<{
  status: string
  agents: Record<Agent, { status: string; model: string }>
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/health`)

    if (!response.ok) {
      throw new ChatAPIError(
        response.status,
        `Health check failed: ${response.statusText}`
      )
    }

    return await response.json()

  } catch (error) {
    if (error instanceof ChatAPIError) {
      throw error
    }

    throw new ChatAPIError(
      0,
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

/**
 * React hook for managing chat state
 */
export function useChatMessages() {
  const [messages, setMessages] = React.useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = React.useState(false)
  const [conversationId, setConversationId] = React.useState<string | null>(null)

  const addMessage = (message: ChatMessage) => {
    setMessages(prev => [...prev, message])
  }

  const updateMessage = (id: string, updates: Partial<ChatMessage>) => {
    setMessages(prev => prev.map(msg =>
      msg.id === id ? { ...msg, ...updates } : msg
    ))
  }

  const removeMessage = (id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id))
  }

  const sendChatMessage = async (text: string, agent: Agent) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date()
    }

    addMessage(userMessage)
    setIsLoading(true)

    // Add loading message
    const loadingMessage: ChatMessage = {
      id: `loading-${Date.now()}`,
      role: agent,
      content: '',
      timestamp: new Date()
    }
    addMessage(loadingMessage)

    try {
      const response = await sendMessage({
        message: text,
        agent,
        conversation_id: conversationId || ''
      })

      // Update loading message with response
      updateMessage(loadingMessage.id, {
        content: response.message,
        metadata: response.metadata
      })

      if (!conversationId) {
        setConversationId(response.conversation_id)
      }

    } catch (error) {
      removeMessage(loadingMessage.id)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  return {
    messages,
    isLoading,
    conversationId,
    addMessage,
    updateMessage,
    removeMessage,
    sendChatMessage,
    setMessages,
    setConversationId
  }
}

// Export error class for external use
export { ChatAPIError }

// Import React for the hook
import React from 'react'