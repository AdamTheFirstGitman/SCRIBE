'use client'

import { KeyboardEvent } from 'react'
import { Mic, MicOff, Send } from 'lucide-react'
import { Button } from '../ui/button'
import { Textarea } from '../ui/textarea'
import { cn } from '../../lib/utils'

interface InputZoneProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  onVoiceRecord: () => void
  isRecording?: boolean
  disabled?: boolean
  fixed?: boolean
  placeholder?: string
}

export function InputZone({
  value,
  onChange,
  onSend,
  onVoiceRecord,
  isRecording = false,
  disabled = false,
  fixed = false,
  placeholder = 'Écrivez votre message...'
}: InputZoneProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (value.trim() && !disabled) {
        onSend()
      }
    }
  }

  return (
    <div
      className={cn(
        'bg-white/95 dark:bg-gray-900/95 backdrop-blur border-t border-gray-200 dark:border-gray-800 p-4',
        fixed && 'fixed bottom-20 lg:bottom-0 left-0 right-0 z-40'
      )}
    >
      <div className="max-w-4xl mx-auto">
        <div className="flex items-end gap-2">
          {/* Textarea with auto-resize */}
          <Textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="flex-1 min-h-[44px] max-h-32 resize-none"
          />

          {/* Voice button */}
          <Button
            size="icon"
            variant={isRecording ? 'destructive' : 'outline'}
            onClick={onVoiceRecord}
            disabled={disabled}
            className="flex-shrink-0"
            title={isRecording ? 'Arrêter l\'enregistrement' : 'Enregistrer un message vocal'}
          >
            {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </Button>

          {/* Send button */}
          <Button
            onClick={onSend}
            disabled={disabled || !value.trim()}
            className="flex-shrink-0"
            title="Envoyer le message"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>

        {/* Character counter */}
        {value.length > 0 && (
          <p className="text-xs text-gray-500 text-right mt-2">
            {value.length} caractères
          </p>
        )}
      </div>
    </div>
  )
}
