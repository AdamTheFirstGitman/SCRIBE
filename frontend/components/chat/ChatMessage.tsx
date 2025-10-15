'use client'

import { useRouter } from 'next/navigation'
import { FileText, ExternalLink, User, Bot } from 'lucide-react'
import { ChatMessage as ChatMessageType, ClickableObject } from '../../lib/types'
import { Card, CardContent } from '../ui/card'
import { Button } from '../ui/button'
import { cn } from '../../lib/utils'

interface ChatMessageProps {
  message: ChatMessageType
}

function ClickableObjectButton({ object }: { object: ClickableObject }) {
  const router = useRouter()

  const handleClick = () => {
    if (object.type === 'viz_link' && object.note_id) {
      router.push(`/viz/${object.note_id}`)
    } else if (object.type === 'web_link' && object.url) {
      window.open(object.url, '_blank')
    }
  }

  return (
    <Button
      size="sm"
      variant="outline"
      onClick={handleClick}
      className="gap-2"
    >
      {object.type === 'viz_link' ? (
        <>
          <FileText className="h-3 w-3" />
          {object.title || 'Voir la note'}
        </>
      ) : (
        <>
          <ExternalLink className="h-3 w-3" />
          {object.title || 'Lien externe'}
        </>
      )}
    </Button>
  )
}

function getAgentInfo(role: 'plume' | 'mimir') {
  if (role === 'plume') {
    return {
      name: 'Plume',
      color: 'text-plume-500',
      bgColor: 'bg-plume-500/10'
    }
  }
  return {
    name: 'Mimir',
    color: 'text-mimir-500',
    bgColor: 'bg-mimir-500/10'
  }
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const agentInfo = !isUser ? getAgentInfo(message.role as 'plume' | 'mimir') : null

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div className={cn(
        'flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center',
        isUser ? 'bg-gray-300 dark:bg-gray-700' : agentInfo?.bgColor
      )}>
        {isUser ? (
          <User className="h-4 w-4 text-gray-700 dark:text-gray-300" />
        ) : (
          <Bot className={cn('h-4 w-4', agentInfo?.color)} />
        )}
      </div>

      {/* Message content */}
      <div className="flex-1 max-w-[80%]">
        <Card className={cn(
          'transition-colors',
          !isUser && 'bg-gray-50 dark:bg-gray-800/50'
        )}>
          <CardContent className="p-3">
            {/* Agent name */}
            {!isUser && agentInfo && (
              <p className={cn('text-xs font-medium mb-1', agentInfo.color)}>
                {agentInfo.name}
              </p>
            )}

            {/* Message content */}
            <p className="text-sm whitespace-pre-wrap">
              {message.content}
            </p>

            {/* Clickable objects */}
            {message.metadata?.clickable_objects && message.metadata.clickable_objects.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {message.metadata.clickable_objects.map((obj, idx) => (
                  <ClickableObjectButton key={idx} object={obj} />
                ))}
              </div>
            )}

            {/* User-friendly metadata from backend */}
            {message.metadata?.ui_metadata && (
              <div className="flex flex-col gap-1 text-xs text-gray-600 dark:text-gray-400 mt-3 border-t border-gray-200 dark:border-gray-700 pt-2">
                {message.metadata.ui_metadata.processing_time && (
                  <span>{message.metadata.ui_metadata.processing_time}</span>
                )}
                {message.metadata.ui_metadata.context_info && (
                  <span className="ml-2">{message.metadata.ui_metadata.context_info}</span>
                )}
                {message.metadata.ui_metadata.sources_found && (
                  <span>{message.metadata.ui_metadata.sources_found}</span>
                )}
              </div>
            )}

            {/* Fallback: Technical metadata (if no ui_metadata) */}
            {!message.metadata?.ui_metadata && message.metadata && (message.metadata.processing_time || message.metadata.tokens_used || message.metadata.cost_eur) && (
              <div className="flex gap-3 text-xs text-gray-500 mt-2 border-t border-gray-200 dark:border-gray-700 pt-2">
                {message.metadata.processing_time && (
                  <span>{message.metadata.processing_time}ms</span>
                )}
                {message.metadata.tokens_used && (
                  <span>{message.metadata.tokens_used} tokens</span>
                )}
                {message.metadata.cost_eur && (
                  <span>{message.metadata.cost_eur.toFixed(4)}€</span>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Timestamp */}
        <p className={cn(
          'text-xs text-gray-500 mt-1',
          isUser ? 'text-right' : 'text-left'
        )}>
          {formatTime(message.timestamp)}
        </p>
      </div>
    </div>
  )
}
