'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import {
  Mic,
  MicOff,
  Send,
  MessageSquare,
  Brain,
  Feather,
  User,
  Loader2,
  Upload,
  Settings
} from 'lucide-react'
import { toast } from 'sonner'

// Types
type Agent = 'plume' | 'mimir'
type MessageRole = 'user' | 'plume' | 'mimir'

interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: Date
  isLoading?: boolean
}

export default function ChatPage() {
  // State management
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'plume',
      content: '🖋️ Salut ! Je suis **Plume**, ton agent de restitution parfaite. Je peux capturer, transcrire et reformuler tes idées avec précision.',
      timestamp: new Date()
    },
    {
      id: '2',
      role: 'mimir',
      content: '🧠 Et moi **Mimir**, ton archiviste intelligent ! Je recherche dans tes connaissances avec RAG et trouve les connections entre tes notes.',
      timestamp: new Date()
    }
  ])

  const [inputText, setInputText] = useState('')
  const [selectedAgent, setSelectedAgent] = useState<Agent>('plume')
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  // Refs
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [inputText])

  // Send message
  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date()
    }

    // Add user message
    setMessages(prev => [...prev, userMessage])
    const currentInput = inputText
    setInputText('')
    setIsLoading(true)

    // Add loading message from selected agent
    const loadingMessage: ChatMessage = {
      id: `loading-${Date.now()}`,
      role: selectedAgent,
      content: '',
      timestamp: new Date(),
      isLoading: true
    }
    setMessages(prev => [...prev, loadingMessage])

    try {
      // Simulate API call to agent
      await simulateAgentResponse(currentInput, selectedAgent, loadingMessage.id)
    } catch (error) {
      console.error('Chat error:', error)
      toast.error('Erreur de communication avec l\\'agent')

      // Remove loading message on error
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id))
    } finally {
      setIsLoading(false)
    }
  }

  // Simulate agent response (replace with real API calls)
  const simulateAgentResponse = async (input: string, agent: Agent, loadingId: string) => {
    await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 1500))

    const responses = {
      plume: [
        `🖋️ J'ai bien capturé ton message : "${input}". Veux-tu que je le reformule ou l'enrichisse ?`,
        '✨ Message traité avec précision ! Je peux maintenant le structurer selon tes besoins.',
        '📝 Parfait ! Ton idée est maintenant claire et bien organisée. Autre chose à traiter ?'
      ],
      mimir: [
        `🧠 J'ai cherché "${input}" dans tes connaissances. Voici ce que j'ai trouvé...`,
        '🔍 Analyse terminée ! J\\'ai trouvé plusieurs connections avec tes notes précédentes.',
        '💡 Intéressant ! Cette requête me rappelle d\\'autres éléments de ta base de connaissances.'
      ]
    }

    const agentResponse = responses[agent][Math.floor(Math.random() * responses[agent].length)]

    // Replace loading message with actual response
    setMessages(prev => prev.map(msg =>
      msg.id === loadingId
        ? { ...msg, content: agentResponse, isLoading: false }
        : msg
    ))
  }

  // Handle voice recording
  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false)
      toast.success('Enregistrement arrêté')
      // TODO: Process voice recording
    } else {
      setIsRecording(true)
      toast.info('🎙️ Enregistrement en cours...')
      // TODO: Start voice recording
    }
  }

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Get agent info
  const getAgentInfo = (agent: Agent) => {
    return {
      plume: {
        name: 'Plume',
        icon: Feather,
        color: 'text-purple-500',
        bgColor: 'bg-purple-100',
        description: 'Restitution parfaite'
      },
      mimir: {
        name: 'Mimir',
        icon: Brain,
        color: 'text-emerald-500',
        bgColor: 'bg-emerald-100',
        description: 'Archiviste RAG'
      }
    }[agent]
  }

  const selectedAgentInfo = getAgentInfo(selectedAgent)

  return (
    <div className=\"min-h-screen bg-gray-50 flex flex-col\">

      {/* Header */}
      <div className=\"bg-white border-b border-gray-200 p-4\">
        <div className=\"max-w-4xl mx-auto flex items-center justify-between\">
          <div className=\"flex items-center gap-3\">
            <MessageSquare className=\"h-6 w-6 text-purple-600\" />
            <h1 className=\"text-xl font-bold text-gray-900\">SCRIBE Chat</h1>
          </div>

          <div className=\"flex items-center gap-2\">
            <Button variant=\"ghost\" size=\"sm\">
              <Upload className=\"h-4 w-4 mr-2\" />
              Docs
            </Button>
            <Button variant=\"ghost\" size=\"sm\">
              <Settings className=\"h-4 w-4\" />
            </Button>
          </div>
        </div>
      </div>

      {/* Agent Selection */}
      <div className=\"bg-white border-b border-gray-200 p-4\">
        <div className=\"max-w-4xl mx-auto\">
          <div className=\"flex items-center gap-2 mb-3\">
            <span className=\"text-sm font-medium text-gray-700\">Parler avec :</span>
          </div>

          <div className=\"grid grid-cols-2 gap-3\">
            {(['plume', 'mimir'] as Agent[]).map((agent) => {
              const info = getAgentInfo(agent)
              const Icon = info.icon
              const isSelected = selectedAgent === agent

              return (
                <button
                  key={agent}
                  onClick={() => setSelectedAgent(agent)}
                  className={`
                    p-3 rounded-lg border-2 transition-all text-left
                    \${isSelected
                      ? 'border-purple-300 bg-purple-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                    }
                  `}
                >
                  <div className=\"flex items-center gap-3\">
                    <div className={`p-2 rounded-full \${info.bgColor}`}>
                      <Icon className={`h-4 w-4 \${info.color}`} />
                    </div>
                    <div>
                      <div className=\"font-medium text-gray-900\">{info.name}</div>
                      <div className=\"text-xs text-gray-500\">{info.description}</div>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className=\"flex-1 overflow-y-auto p-4\">
        <div className=\"max-w-4xl mx-auto space-y-4\">
          {messages.map((message) => {
            const isUser = message.role === 'user'
            const agentInfo = !isUser ? getAgentInfo(message.role as Agent) : null
            const AgentIcon = agentInfo?.icon

            return (
              <div
                key={message.id}
                className={`flex items-start gap-3 \${isUser ? 'flex-row-reverse' : ''}`}
              >
                {/* Avatar */}
                <div className={`
                  flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                  \${isUser
                    ? 'bg-blue-500'
                    : agentInfo?.bgColor || 'bg-gray-200'
                  }
                `}>
                  {isUser ? (
                    <User className=\"h-4 w-4 text-white\" />
                  ) : AgentIcon ? (
                    <AgentIcon className={`h-4 w-4 \${agentInfo?.color}`} />
                  ) : null}
                </div>

                {/* Message bubble */}
                <Card className={`
                  max-w-[80%] shadow-sm
                  \${isUser ? 'bg-blue-500 text-white' : 'bg-white'}
                `}>
                  <CardContent className=\"p-3\">
                    {message.isLoading ? (
                      <div className=\"flex items-center gap-2 text-gray-500\">
                        <Loader2 className=\"h-4 w-4 animate-spin\" />
                        <span className=\"text-sm\">{agentInfo?.name} réfléchit...</span>
                      </div>
                    ) : (
                      <div
                        className=\"text-sm whitespace-pre-wrap\"
                        dangerouslySetInnerHTML={{
                          __html: message.content.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
                        }}
                      />
                    )}
                  </CardContent>
                </Card>

                {/* Timestamp */}
                <div className=\"text-xs text-gray-400 mt-2 min-w-fit\">
                  {message.timestamp.toLocaleTimeString('fr-FR', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
              </div>
            )
          })}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className=\"bg-white border-t border-gray-200 p-4\">
        <div className=\"max-w-4xl mx-auto\">

          {/* Selected agent indicator */}
          <div className=\"flex items-center gap-2 mb-3\">
            <div className={`p-1.5 rounded-full \${selectedAgentInfo.bgColor}`}>
              <selectedAgentInfo.icon className={`h-3 w-3 \${selectedAgentInfo.color}`} />
            </div>
            <span className=\"text-sm text-gray-600\">
              Message pour <strong>{selectedAgentInfo.name}</strong>
            </span>
          </div>

          <div className=\"flex items-end gap-2\">

            {/* Voice Recording Button */}
            <Button
              variant={isRecording ? \"destructive\" : \"outline\"}
              size=\"icon\"
              onClick={toggleRecording}
              className=\"flex-shrink-0\"
            >
              {isRecording ? (
                <MicOff className=\"h-4 w-4\" />
              ) : (
                <Mic className=\"h-4 w-4\" />
              )}
            </Button>

            {/* Text Input */}
            <div className=\"flex-1 relative\">
              <Textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={`Écris ton message pour ${selectedAgentInfo.name}...`}
                className=\"min-h-[44px] max-h-32 resize-none pr-12\"
                rows={1}
              />

              {/* Character counter */}
              {inputText.length > 0 && (
                <div className=\"absolute bottom-2 right-2 text-xs text-gray-400\">
                  {inputText.length}
                </div>
              )}
            </div>

            {/* Send Button */}
            <Button
              onClick={sendMessage}
              disabled={!inputText.trim() || isLoading}
              className=\"flex-shrink-0\"
            >
              {isLoading ? (
                <Loader2 className=\"h-4 w-4 animate-spin\" />
              ) : (
                <Send className=\"h-4 w-4\" />
              )}
            </Button>
          </div>

          {/* Input hints */}
          <div className=\"mt-2 text-xs text-gray-500 text-center\">
            <kbd className=\"px-2 py-1 bg-gray-100 rounded text-xs\">Enter</kbd> pour envoyer •
            <kbd className=\"px-2 py-1 bg-gray-100 rounded text-xs ml-1\">Shift+Enter</kbd> pour nouvelle ligne
          </div>
        </div>
      </div>
    </div>
  )
}