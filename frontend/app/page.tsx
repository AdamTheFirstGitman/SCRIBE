'use client'

import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import { MessageSquare, X } from 'lucide-react'
import { ProtectedRoute } from '../components/auth/ProtectedRoute'
import { Navigation } from '../components/layout/Navigation'
import { InputZone } from '../components/chat/InputZone'
import { ChatMessage } from '../components/chat/ChatMessage'
import { EmptyState } from '../components/ui/empty-state'
import { ChatMessage as ChatMessageType } from '../lib/types'
import { sendOrchestratedMessageStream, getNote } from '../lib/api/client'
import { getErrorMessage } from '../lib/api/error-handler'
import { toast } from 'sonner'

function HomePage() {
  const searchParams = useSearchParams()
  const context = searchParams?.get('context')

  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [contextBanner, setContextBanner] = useState<string | null>(null)
  const [contextNoteId, setContextNoteId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load context note if provided in URL
  useEffect(() => {
    if (context?.startsWith('note:')) {
      const noteId = context.split(':')[1]
      loadNoteContext(noteId)
    }
  }, [context])

  const loadNoteContext = async (noteId: string) => {
    try {
      const note = await getNote(noteId)
      setContextBanner(`📎 Contexte: ${note.title}`)
      setContextNoteId(noteId)
    } catch (error) {
      console.error('Failed to load note context:', error)
      toast.error(getErrorMessage(error))
    }
  }

  const clearContext = () => {
    setContextBanner(null)
    setContextNoteId(null)
    // Clear URL params
    if (typeof window !== 'undefined') {
      window.history.replaceState({}, '', '/')
    }
  }

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    const userContent = inputValue
    const userMessage: ChatMessageType = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: userContent,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    // Create loading message
    const loadingId = `loading-${Date.now()}`
    setMessages(prev => [...prev, {
      id: loadingId,
      role: 'plume',
      content: '',
      timestamp: new Date()
    }])

    try {
      await sendOrchestratedMessageStream(
        {
          message: userContent,
          mode: 'auto',
          conversation_id: conversationId || undefined
        },
        // onMessage: Display agent messages in real-time
        (sseMsg) => {
          if (sseMsg.type === 'agent_message' && sseMsg.agent && sseMsg.content) {
            setMessages(prev => {
              // Remove loading message
              const filtered = prev.filter(m => m.id !== loadingId)

              // Check if message from this agent already exists
              const agentMsgId = `${sseMsg.agent}-${Date.now()}`
              const existingAgentMsg = filtered.find(m =>
                m.role === sseMsg.agent && m.timestamp.getTime() > userMessage.timestamp.getTime()
              )

              if (existingAgentMsg) {
                // Update existing message
                return filtered.map(m =>
                  m.id === existingAgentMsg.id
                    ? { ...m, content: sseMsg.content || '' }
                    : m
                )
              } else {
                // Add new agent message
                return [...filtered, {
                  id: agentMsgId,
                  role: sseMsg.agent as 'plume' | 'mimir',
                  content: sseMsg.content,
                  timestamp: new Date(),
                  metadata: sseMsg.metadata
                }]
              }
            })
          }
        },
        // onComplete
        (result) => {
          setMessages(prev => {
            // Remove loading message
            const filtered = prev.filter(m => m.id !== loadingId)

            // Add agent response if not already added via agent_message events
            if (result && result.response) {
              // Check if response already exists from agent_message events
              const hasResponse = filtered.some(m =>
                m.role !== 'user' && m.timestamp.getTime() > userMessage.timestamp.getTime()
              )

              if (!hasResponse) {
                // Add final response message
                return [...filtered, {
                  id: `complete-${Date.now()}`,
                  role: result.agent_used || 'plume',
                  content: result.response,
                  timestamp: new Date(),
                  metadata: {
                    processing_time: result.processing_time_ms,
                    tokens_used: result.tokens_used,
                    cost_eur: result.cost_eur,
                    clickable_objects: result.metadata?.clickable_objects
                  }
                }]
              }
            }

            return filtered
          })

          // Save conversation_id for next messages
          if (result && result.session_id) {
            setConversationId(result.session_id)
          }

          setIsLoading(false)
        },
        // onError
        (error) => {
          setMessages(prev => prev.filter(m => m.id !== loadingId))
          toast.error(`Erreur: ${error.message}`)
          setIsLoading(false)
        }
      )
    } catch (error) {
      setMessages(prev => prev.filter(m => m.id !== loadingId))
      toast.error('Échec de l\'envoi du message')
      setIsLoading(false)
    }
  }

  const handleVoiceRecord = () => {
    // TODO: Implement voice recording in Phase 2 (Integration)
    setIsRecording(!isRecording)
    console.log('Voice recording not yet implemented')
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />

      <main className="flex-1 overflow-y-auto pb-40 lg:pb-32">
        <div className="max-w-4xl mx-auto space-y-4 p-4">
          {/* Context Banner */}
          {contextBanner && (
            <div className="bg-mimir-100 dark:bg-mimir-500/10 border border-mimir-200 dark:border-mimir-500/30 rounded-lg p-3 flex items-center justify-between">
              <span className="text-sm text-mimir-700 dark:text-mimir-300">{contextBanner}</span>
              <button
                onClick={clearContext}
                className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {messages.length === 0 && (
            <EmptyState
              icon={MessageSquare}
              title="Nouvelle conversation"
              description="Posez une question à Plume et Mimir"
            />
          )}

          {messages.map(msg => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex gap-2 items-center text-sm text-gray-600 dark:text-gray-400">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 dark:border-gray-400"></div>
              <span>Réflexion en cours...</span>
            </div>
          )}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Zone fixe en bas */}
      <InputZone
        value={inputValue}
        onChange={setInputValue}
        onSend={handleSend}
        onVoiceRecord={handleVoiceRecord}
        isRecording={isRecording}
        disabled={isLoading}
        fixed={true}
      />
    </div>
  )
}

export default function Page() {
  return (
    <ProtectedRoute>
      <HomePage />
    </ProtectedRoute>
  )
}
