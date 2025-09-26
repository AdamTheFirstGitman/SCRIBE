'use client'

import React, { useState, useRef, useCallback } from 'react'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import {
  Mic,
  Square,
  Loader2,
  Volume2,
  VolumeX
} from 'lucide-react'
import { toast } from 'sonner'
import { transcribeAudio } from '../../lib/api/chat'

interface VoiceRecorderProps {
  onTranscription: (text: string, confidence: number) => void
  onError: (error: Error) => void
  disabled?: boolean
  className?: string
}

export function VoiceRecorder({
  onTranscription,
  onError,
  disabled = false,
  className = ''
}: VoiceRecorderProps) {
  // State
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioLevel, setAudioLevel] = useState(0)
  const [hasAudio, setHasAudio] = useState(false)

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  // Check if audio is supported
  const isAudioSupported = typeof navigator !== 'undefined' &&
                          navigator.mediaDevices &&
                          navigator.mediaDevices.getUserMedia

  // Start recording
  const startRecording = useCallback(async () => {
    if (!isAudioSupported) {
      toast.error('Enregistrement audio non supporté par ce navigateur')
      return
    }

    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100
        }
      })

      streamRef.current = stream
      audioChunksRef.current = []

      // Setup audio context for level monitoring
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const analyser = audioContext.createAnalyser()
      const microphone = audioContext.createMediaStreamSource(stream)

      analyser.fftSize = 256
      microphone.connect(analyser)

      audioContextRef.current = audioContext
      analyserRef.current = analyser

      // Setup MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })

      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        if (audioChunksRef.current.length > 0) {
          await processRecording()
        }
      }

      // Start recording
      mediaRecorder.start(100) // Collect data every 100ms
      setIsRecording(true)
      setRecordingTime(0)
      setHasAudio(false)

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)

      // Start audio level monitoring
      monitorAudioLevel()

      toast.success('🎙️ Enregistrement démarré')

    } catch (error) {
      console.error('Failed to start recording:', error)
      toast.error('Impossible d\'accéder au microphone')
      onError(error as Error)
    }
  }, [isAudioSupported, onError])

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)

      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }

      // Stop all tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
        streamRef.current = null
      }

      // Close audio context
      if (audioContextRef.current) {
        audioContextRef.current.close()
        audioContextRef.current = null
      }

      analyserRef.current = null
      setAudioLevel(0)

      toast.info('⏸️ Enregistrement arrêté, traitement en cours...')
    }
  }, [isRecording])

  // Monitor audio levels
  const monitorAudioLevel = useCallback(() => {
    if (!analyserRef.current) return

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)

    const updateLevel = () => {
      if (!analyserRef.current || !isRecording) return

      analyserRef.current.getByteFrequencyData(dataArray)

      // Calculate average volume
      const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length
      const normalizedLevel = average / 255

      setAudioLevel(normalizedLevel)

      // Detect if there's actual audio input
      if (normalizedLevel > 0.01) {
        setHasAudio(true)
      }

      requestAnimationFrame(updateLevel)
    }

    updateLevel()
  }, [isRecording])

  // Process the recorded audio
  const processRecording = useCallback(async () => {
    if (audioChunksRef.current.length === 0) {
      toast.warning('Aucun audio enregistré')
      return
    }

    setIsProcessing(true)

    try {
      // Create audio blob
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })

      // Check minimum file size (avoid empty recordings)
      if (audioBlob.size < 1000) {
        toast.warning('Enregistrement trop court')
        setIsProcessing(false)
        return
      }

      // Send to transcription API
      const result = await transcribeAudio(audioBlob)

      if (result.text && result.text.trim()) {
        onTranscription(result.text.trim(), result.confidence || 0.8)
        toast.success('🎯 Transcription réussie')
      } else {
        toast.warning('Aucun texte détecté dans l\'audio')
      }

    } catch (error) {
      console.error('Transcription failed:', error)
      toast.error('Erreur lors de la transcription')
      onError(error as Error)
    } finally {
      setIsProcessing(false)
      audioChunksRef.current = []
    }
  }, [onTranscription, onError])

  // Format time display
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Toggle recording
  const toggleRecording = () => {
    if (disabled || isProcessing) return

    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  if (!isAudioSupported) {
    return (
      <div className={`flex items-center gap-2 text-gray-500 ${className}`}>
        <VolumeX className="h-4 w-4" />
        <span className="text-sm">Audio non supporté</span>
      </div>
    )
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Recording button */}
      <Button
        onClick={toggleRecording}
        disabled={disabled || isProcessing}
        variant={isRecording ? "destructive" : "outline"}
        size="icon"
        className={`
          relative transition-all duration-200
          ${isRecording
            ? 'animate-pulse shadow-lg shadow-red-500/30'
            : 'hover:scale-105'
          }
        `}
      >
        {isProcessing ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : isRecording ? (
          <Square className="h-4 w-4" />
        ) : (
          <Mic className="h-4 w-4" />
        )}

        {/* Audio level indicator */}
        {isRecording && (
          <div
            className="absolute inset-0 rounded-full border-2 border-red-400 animate-ping"
            style={{
              opacity: Math.max(0.3, audioLevel),
              transform: `scale(${1 + audioLevel * 0.5})`
            }}
          />
        )}
      </Button>

      {/* Recording status */}
      {(isRecording || isProcessing) && (
        <div className="flex items-center gap-2">
          {isRecording && (
            <>
              <Badge
                variant="danger"
                className="animate-pulse"
              >
                REC {formatTime(recordingTime)}
              </Badge>

              {/* Audio level bars */}
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className={`
                      w-1 h-3 rounded-full transition-all duration-150
                      ${audioLevel > (i + 1) * 0.2
                        ? 'bg-red-500'
                        : 'bg-gray-600'
                      }
                    `}
                  />
                ))}
              </div>

              {hasAudio && (
                <Volume2 className="h-4 w-4 text-green-500" />
              )}
            </>
          )}

          {isProcessing && (
            <Badge variant="secondary">
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              Transcription...
            </Badge>
          )}
        </div>
      )}
    </div>
  )
}