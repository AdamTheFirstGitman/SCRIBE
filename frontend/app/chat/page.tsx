'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '../../components/ui/button'
import { Card, CardContent } from '../../components/ui/card'
import { Textarea } from '../../components/ui/textarea'
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
  Settings,
  FileText,
  Search,
  CheckCircle2,
  XCircle
} from 'lucide-react'
import { OfflineUtils } from '../../lib/offline'
import { toast } from 'sonner'
import { sendOrchestratedMessageStream, SSEMessage } from '../../lib/api/client'
import {
  ChatMessage,
  ToolActivity,
  AgentName
} from '../../types/chat'
import { AgentAction, AgentActionProps } from '../../components/chat/AgentAction'

// Legacy types for getAgentInfo
type Agent = 'plume' | 'mimir'

// Mapping tool technique → phrase UI française
const TOOL_ACTION_TEXT: Record<string, string> = {
  'search_knowledge': 'recherche dans les archives',
  'web_search': 'recherche sur le web',
  'get_related_content': 'explore les contenus liés',
  'create_note': 'a créé une note',
  'update_note': 'a mis à jour une note'
}

export default function ChatPage() {
  const router = useRouter()

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
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isOnline, setIsOnline] = useState(true)
  const [currentToolActivities, setCurrentToolActivities] = useState<Map<string, ToolActivity>>(new Map())
  const [agentActions, setAgentActions] = useState<AgentActionProps[]>([])

  // Refs
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Handle network status changes - SSR safe
  useEffect(() => {
    // Set initial value after component mounts (client-side only)
    setIsOnline(navigator.onLine)

    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

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

  // Send message with orchestrated API
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

    // Add loading message (agents will decide who responds)
    const loadingMessageId = `loading-${Date.now()}`
    const loadingMessage: ChatMessage = {
      id: loadingMessageId,
      role: 'plume', // Placeholder, will be replaced
      content: '',
      timestamp: new Date(),
      isLoading: true
    }
    setMessages(prev => [...prev, loadingMessage])

    try {
      if (!isOnline) {
        // Handle offline message - store for later sync
        await OfflineUtils.storage.init()
        const offlineMessage = {
          id: Date.now().toString(),
          text: currentInput,
          timestamp: Date.now(),
          retries: 0
        }

        // Store in IndexedDB
        const db = await new Promise<IDBDatabase>((resolve, reject) => {
          const request = indexedDB.open('scribe-offline', 1)
          request.onsuccess = () => resolve(request.result)
          request.onerror = () => reject(request.error)
        })

        const transaction = db.transaction(['pendingMessages'], 'readwrite')
        const store = transaction.objectStore('pendingMessages')
        await new Promise((resolve, reject) => {
          const request = store.add(offlineMessage)
          request.onsuccess = () => resolve(request.result)
          request.onerror = () => reject(request.error)
        })

        // Remove loading message and add offline response
        setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id))
        const offlineResponseMessage: ChatMessage = {
          id: `offline-${Date.now()}`,
          role: 'plume',
          content: `📴 Message sauvegardé hors ligne. Il sera envoyé dès la reconnexion.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, offlineResponseMessage])

        toast.info('Message sauvegardé pour synchronisation')
        return
      }

      // Online - call orchestrated API with SSE
      let agentMessagesBuffer: Map<AgentName, string> = new Map()

      await sendOrchestratedMessageStream(
        {
          message: currentInput,
          mode: 'auto' // Agents decide automatically
        },
        // onMessage: Handle SSE events
        (event: SSEMessage) => {
          console.log('[DEBUG] SSE Event:', event)

          if (event.type === 'agent_action' && event.agent && event.action) {
            console.log('[DEBUG] Agent action detected!', event)
            // NEW: Agent action notification (WhatsApp-style)
            // Translate technical action name to French UI text
            const actionText = TOOL_ACTION_TEXT[event.action] || event.action
            const action: AgentActionProps = {
              agent: event.agent as 'plume' | 'mimir',
              actionText: actionText,
              status: event.status as 'running' | 'completed',
              timestamp: new Date()
            }
            console.log('[DEBUG] Adding action to state:', action)
            setAgentActions(prev => {
              const newState = [...prev, action]
              console.log('[DEBUG] New agentActions state:', newState)
              return newState
            })
          } else if (event.type === 'tool_activity' && event.tool) {
            // Backend envoie tool activities FILTRÉES (badges UI-friendly)
            // Format: { tool, label, status, summary, timestamp }
            const activityId = `${event.tool}-${Date.now()}`
            const activity: ToolActivity = {
              id: activityId,
              agent: (event.agent || 'plume') as AgentName,
              tool: event.tool as any,
              status: event.status || 'running',
              startTime: Date.now(),
              ...(event.label && { label: event.label }),
              ...(event.summary && { summary: event.summary })
            }
            setCurrentToolActivities(prev => new Map(prev).set(activityId, activity))
          } else if (event.type === 'tool_start' && event.agent && event.tool) {
            // Fallback legacy tool_start (si backend n'utilise pas tool_activity)
            const activityId = `${event.agent}-${event.tool}-${Date.now()}`
            const activity: ToolActivity = {
              id: activityId,
              agent: event.agent,
              tool: event.tool as any,
              status: 'running',
              startTime: Date.now()
            }
            setCurrentToolActivities(prev => new Map(prev).set(activityId, activity))
          } else if (event.type === 'tool_complete' && event.agent && event.tool) {
            // Update tool activity to completed
            setCurrentToolActivities(prev => {
              const updated = new Map(prev)
              const existingActivity = Array.from(updated.values()).find(
                a => a.agent === event.agent && a.tool === event.tool && a.status === 'running'
              )
              if (existingActivity && event.result) {
                updated.set(existingActivity.id, {
                  ...existingActivity,
                  status: event.result.success ? 'completed' : 'failed',
                  result: event.result,
                  endTime: Date.now()
                })
              }
              return updated
            })
          } else if (event.type === 'agent_message' && event.agent && event.content) {
            // Backend envoie messages FILTRÉS (Layer 2)
            // Pas de reasoning/debug/tool_params ici
            const existing = agentMessagesBuffer.get(event.agent) || ''
            agentMessagesBuffer.set(event.agent, existing + event.content)
          }
        },
        // onComplete: Replace loading with final response
        (result) => {
          setIsLoading(false)

          // Convert current tool activities to array
          const toolActivities = Array.from(currentToolActivities.values())

          // Remove loading message and add final response
          setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId))

          // Add messages from all agents who participated
          const finalMessages: ChatMessage[] = []
          agentMessagesBuffer.forEach((content, agent) => {
            if (content.trim()) {
              finalMessages.push({
                id: `msg-${agent}-${Date.now()}`,
                role: agent,
                content: content.trim(),
                timestamp: new Date(),
                toolActivities: toolActivities.filter(a => a.agent === agent),
                metadata: result.metadata
              })
            }
          })

          // If no buffered messages, use result.response
          if (finalMessages.length === 0) {
            finalMessages.push({
              id: `msg-${result.agent}-${Date.now()}`,
              role: result.agent,
              content: result.response,
              timestamp: new Date(),
              toolActivities,
              metadata: {
                clickable_objects: result.clickable_objects,
                ...result.metadata
              }
            })
          } else {
            // Add clickable_objects to last message
            if (result.clickable_objects && finalMessages.length > 0) {
              const lastMsg = finalMessages[finalMessages.length - 1]
              if (lastMsg) {
                lastMsg.metadata = {
                  ...(lastMsg.metadata || {}),
                  clickable_objects: result.clickable_objects
                }
              }
            }
          }

          setMessages(prev => [...prev, ...finalMessages])

          // Clear tool activities immediately
          setCurrentToolActivities(new Map())

          // Keep agent actions visible for 2 seconds after completion
          setTimeout(() => {
            setAgentActions([])
          }, 2000)
        },
        // onError
        (error) => {
          console.error('Chat error:', error)
          toast.error("Erreur de communication avec l'agent")
          setIsLoading(false)

          // Remove loading message
          setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId))

          // Clear tool activities immediately
          setCurrentToolActivities(new Map())

          // Clear agent actions after delay (user should see what failed)
          setTimeout(() => {
            setAgentActions([])
          }, 3000)
        }
      )
    } catch (error) {
      console.error('Chat error:', error)
      toast.error("Erreur de communication avec l'agent")

      // Remove loading message on error
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId))
      setIsLoading(false)
      setCurrentToolActivities(new Map())

      // Clear agent actions after delay
      setTimeout(() => {
        setAgentActions([])
      }, 3000)
    }
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
        color: 'text-plume-500',
        bgColor: 'bg-plume-500/20',
        description: 'Restitution parfaite'
      },
      mimir: {
        name: 'Mimir',
        icon: Brain,
        color: 'text-mimir-500',
        bgColor: 'bg-mimir-500/20',
        description: 'Archiviste RAG'
      }
    }[agent]
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">

      {/* Header */}
      <div className="bg-gray-900/50 border-b border-gray-800 p-4 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MessageSquare className="h-6 w-6 text-plume-500" />
            <h1 className="text-xl font-bold text-gray-50">SCRIBE Chat</h1>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm">
              <Upload className="h-4 w-4 mr-2" />
              Docs
            </Button>
            <Button variant="ghost" size="sm">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Info Banner - Mode Auto */}
      <div className="bg-gray-900/30 border-b border-gray-800 p-4 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Brain className="h-4 w-4 text-plume-500" />
            <span>
              Mode <strong className="text-gray-200">Auto</strong> : Les agents décident intelligemment qui répond
            </span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {/* Agent Actions (WhatsApp-style notifications) */}
          {console.log('[DEBUG] Rendering - agentActions.length:', agentActions.length, agentActions)}
          {agentActions.length > 0 && (
            <div className="space-y-2">
              {console.log('[DEBUG] Rendering AgentAction components')}
              {agentActions.map((action, idx) => (
                <AgentAction key={`action-${idx}`} {...action} />
              ))}
            </div>
          )}

          {messages.map((message) => {
            const isUser = message.role === 'user'
            const agentInfo = !isUser ? getAgentInfo(message.role as Agent) : null
            const AgentIcon = agentInfo?.icon

            return (
              <div
                key={message.id}
                className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
              >
                {/* Avatar */}
                <div className={`
                  flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                  ${isUser
                    ? 'bg-plume-500'
                    : agentInfo?.bgColor || 'bg-gray-800'
                  }
                `}>
                  {isUser ? (
                    <User className="h-4 w-4 text-white" />
                  ) : AgentIcon ? (
                    <AgentIcon className={`h-4 w-4 ${agentInfo?.color}`} />
                  ) : null}
                </div>

                {/* Message bubble */}
                <Card className={`
                  max-w-[80%] shadow-sm
                  ${isUser ? 'bg-plume-500/20 border-plume-500/30' : 'bg-gray-800/50 border-gray-700'}
                `}>
                  <CardContent className="p-3 space-y-2">
                    {message.isLoading ? (
                      <div className="flex items-center gap-2 text-gray-400">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">{agentInfo?.name} réfléchit...</span>
                      </div>
                    ) : (
                      <>
                        {/* Tool Activities Badges */}
                        {message.toolActivities && message.toolActivities.length > 0 && (
                          <div className="space-y-1.5 pb-2 border-b border-gray-700/50">
                            {message.toolActivities.map((activity) => {
                              const getToolIcon = (tool: string) => {
                                switch (tool) {
                                  case 'search_knowledge':
                                  case 'web_search':
                                    return Search
                                  case 'create_note':
                                  case 'update_note':
                                    return FileText
                                  default:
                                    return Brain
                                }
                              }

                              const getToolLabel = (tool: string) => {
                                switch (tool) {
                                  case 'search_knowledge':
                                    return 'Recherche dans les archives'
                                  case 'web_search':
                                    return 'Recherche web'
                                  case 'get_related_content':
                                    return 'Contenus similaires'
                                  case 'create_note':
                                    return 'Création de note'
                                  case 'update_note':
                                    return 'Mise à jour de note'
                                  default:
                                    return tool
                                }
                              }

                              const ToolIcon = getToolIcon(activity.tool)

                              if (activity.status === 'running') {
                                return (
                                  <div
                                    key={activity.id}
                                    className="flex items-center gap-2 text-xs text-gray-400"
                                  >
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                    <span>{getToolLabel(activity.tool)} en cours...</span>
                                  </div>
                                )
                              }

                              if (activity.status === 'completed') {
                                const result = activity.result
                                let resultText = ''

                                if (result?.results_count !== undefined) {
                                  resultText = `${result.results_count} résultat${result.results_count > 1 ? 's' : ''}`
                                } else if (result?.note_id) {
                                  resultText = 'Note créée'
                                } else {
                                  resultText = 'Terminé'
                                }

                                const duration = activity.endTime
                                  ? ` (${activity.endTime - activity.startTime}ms)`
                                  : ''

                                return (
                                  <div
                                    key={activity.id}
                                    className="flex items-center gap-2 text-xs text-green-400"
                                  >
                                    <CheckCircle2 className="h-3 w-3" />
                                    <ToolIcon className="h-3 w-3" />
                                    <span>
                                      {resultText}
                                      {duration && <span className="text-gray-500">{duration}</span>}
                                    </span>
                                  </div>
                                )
                              }

                              if (activity.status === 'failed') {
                                return (
                                  <div
                                    key={activity.id}
                                    className="flex items-center gap-2 text-xs text-red-400"
                                  >
                                    <XCircle className="h-3 w-3" />
                                    <span>{getToolLabel(activity.tool)} échoué</span>
                                  </div>
                                )
                              }

                              return null
                            })}
                          </div>
                        )}

                        {/* Message content */}
                        <div
                          className={`text-sm whitespace-pre-wrap ${isUser ? 'text-plume-50' : 'text-gray-200'}`}
                          dangerouslySetInnerHTML={{
                            __html: message.content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                          }}
                        />

                        {/* Clickable Objects (Viz Links) */}
                        {message.metadata?.clickable_objects && message.metadata.clickable_objects.length > 0 && (
                          <div className="pt-2 border-t border-gray-700/50 space-y-2">
                            {message.metadata.clickable_objects.map((obj, idx) => {
                              if (obj.type === 'viz_link' && obj.note_id) {
                                return (
                                  <Button
                                    key={idx}
                                    variant="outline"
                                    size="sm"
                                    onClick={() => router.push(`/viz/${obj.note_id}`)}
                                    className="w-full justify-start gap-2 text-plume-400 border-plume-500/30 hover:bg-plume-500/10"
                                  >
                                    <FileText className="h-4 w-4" />
                                    {obj.title || 'Voir la note'} →
                                  </Button>
                                )
                              }
                              return null
                            })}
                          </div>
                        )}
                      </>
                    )}
                  </CardContent>
                </Card>

                {/* Timestamp */}
                <div className="text-xs text-gray-500 mt-2 min-w-fit">
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
      <div className="bg-gray-900/50 border-t border-gray-800 p-4 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end gap-2">

            {/* Voice Recording Button */}
            <Button
              variant={isRecording ? "destructive" : "outline"}
              size="icon"
              onClick={toggleRecording}
              className="flex-shrink-0"
            >
              {isRecording ? (
                <MicOff className="h-4 w-4" />
              ) : (
                <Mic className="h-4 w-4" />
              )}
            </Button>

            {/* Text Input */}
            <div className="flex-1 relative">
              <Textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Écris ton message pour les agents..."
                className="min-h-[44px] max-h-32 resize-none pr-12"
                rows={1}
              />

              {/* Character counter */}
              {inputText.length > 0 && (
                <div className="absolute bottom-2 right-2 text-xs text-gray-500">
                  {inputText.length}
                </div>
              )}
            </div>

            {/* Send Button */}
            <Button
              onClick={sendMessage}
              disabled={!inputText.trim() || isLoading}
              className="flex-shrink-0"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Input hints */}
          <div className="mt-2 text-xs text-gray-500 text-center">
            <kbd className="px-2 py-1 bg-gray-800 rounded text-xs">Enter</kbd> pour envoyer •
            <kbd className="px-2 py-1 bg-gray-800 rounded text-xs ml-1">Shift+Enter</kbd> pour nouvelle ligne
          </div>
        </div>
      </div>
    </div>
  )
}