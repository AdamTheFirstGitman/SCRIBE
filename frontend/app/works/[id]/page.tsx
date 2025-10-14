'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import { ProtectedRoute } from '../../../components/auth/ProtectedRoute'
import { Navigation } from '../../../components/layout/Navigation'
import { InputZone } from '../../../components/chat/InputZone'
import { ChatMessage } from '../../../components/chat/ChatMessage'
import { Button } from '../../../components/ui/button'
import { ChatMessage as ChatMessageType, Conversation } from '../../../lib/types'
import { getConversation, sendChatMessage } from '../../../lib/api/client'
import { getErrorMessage } from '../../../lib/api/error-handler'
import { toast } from 'sonner'

function ConversationPage() {
  const router = useRouter()
  const params = useParams()
  const conversationId = params['id'] as string

  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadConversation()
  }, [conversationId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadConversation = async () => {
    try {
      const { conversation: conv, messages: msgs } = await getConversation(conversationId)
      setConversation(conv)
      setMessages(msgs)
    } catch (error) {
      console.error('Failed to load conversation:', error)
      toast.error('Conversation introuvable')
      router.push('/')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSend = async () => {
    if (!inputValue.trim() || isSending) return

    const userMessage: ChatMessageType = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsSending(true)

    try {
      const agentResponse = await sendChatMessage(inputValue)
      setMessages(prev => [...prev, agentResponse])
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setIsSending(false)
    }
  }

  const handleVoiceRecord = () => {
    setIsRecording(!isRecording)
    console.log('Voice recording not yet implemented')
  }

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen">
          <Navigation />
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-200"></div>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  if (!conversation) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen">
          <Navigation />
          <div className="max-w-4xl mx-auto p-4 text-center">
            <p className="text-gray-400">Conversation introuvable</p>
            <Button
              variant="outline"
              onClick={() => router.push('/works')}
              className="mt-4"
            >
              Retour aux conversations
            </Button>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />

      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900/50 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto p-4 flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/works')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h1 className="font-semibold truncate">{conversation.title}</h1>
            <p className="text-xs text-gray-500">{messages.length} messages</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto pb-32">
        <div className="max-w-4xl mx-auto space-y-4 p-4">
          {messages.map(msg => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {isSending && (
            <div className="flex gap-2 items-center text-sm text-gray-400">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
              <span>Réflexion en cours...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Zone */}
      <InputZone
        value={inputValue}
        onChange={setInputValue}
        onSend={handleSend}
        onVoiceRecord={handleVoiceRecord}
        isRecording={isRecording}
        disabled={isSending}
        fixed={true}
      />
    </div>
  )
}

export default function Page() {
  return (
    <ProtectedRoute>
      <ConversationPage />
    </ProtectedRoute>
  )
}
