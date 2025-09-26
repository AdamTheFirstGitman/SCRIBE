'use client'

import React, { useState, useRef, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Mic,
  MicOff,
  Square,
  Loader2,
  Volume2,
  VolumeX
} from 'lucide-react'
import { toast } from 'sonner'
import { transcribeAudio } from '@/lib/api/chat'

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
      onError(new Error('Audio recording not supported'))
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100
        }
      })

      streamRef.current = stream

      // Create audio context for level monitoring
      audioContextRef.current = new AudioContext()
      const source = audioContextRef.current.createMediaStreamSource(stream)
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 256
      source.connect(analyserRef.current)

      // Monitor audio levels
      const monitorLevels = () => {
        if (analyserRef.current && isRecording) {
          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
          analyserRef.current.getByteFrequencyData(dataArray)
          const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length
          setAudioLevel(Math.min(100, (average / 128) * 100))
          requestAnimationFrame(monitorLevels)
        }
      }

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
      })

      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        setIsProcessing(true)

        try {
          const audioBlob = new Blob(audioChunksRef.current, {
            type: mediaRecorder.mimeType
          })

          // Check if we have actual audio data
          if (audioBlob.size < 1000) {
            throw new Error('Recording too short or empty')
          }

          setHasAudio(true)

          // Transcribe audio
          const result = await transcribeAudio(audioBlob)

          if (result.text.trim()) {
            onTranscription(result.text, result.confidence)
            toast.success(`Transcription réussie (${Math.round(result.confidence * 100)}% confiance)`)
          } else {
            throw new Error('No speech detected in recording')
          }

        } catch (error) {
          console.error('Transcription error:', error)
          const errorMessage = error instanceof Error ? error.message : 'Transcription failed'
          onError(new Error(errorMessage))
          toast.error('Échec de la transcription')
        } finally {
          setIsProcessing(false)
          setHasAudio(false)
        }
      }

      // Start recording
      mediaRecorder.start(100) // Collect data every 100ms
      setIsRecording(true)
      setRecordingTime(0)

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)

      // Start level monitoring
      monitorLevels()

      toast.info('🎙️ Enregistrement démarré')

    } catch (error) {
      console.error('Failed to start recording:', error)
      onError(new Error('Impossible d\\'accéder au microphone'))
      toast.error('Échec d\\'accès au microphone')
    }
  }, [isAudioSupported, onError, onTranscription, isRecording])

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setAudioLevel(0)

      // Stop timer
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }

      // Clean up audio context
      if (audioContextRef.current) {
        audioContextRef.current.close()
        audioContextRef.current = null
      }

      // Stop media stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
        streamRef.current = null
      }

      toast.info('Enregistrement arrêté, transcription...')
    }
  }, [isRecording])

  // Toggle recording
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  // Format recording time
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // Clean up on unmount
  React.useEffect(() => {
    return () => {
      if (isRecording) {
        stopRecording()
      }
    }
  }, [isRecording, stopRecording])

  if (!isAudioSupported) {
    return (
      <Button variant=\"outline\" size=\"icon\" disabled className={className}>
        <VolumeX className=\"h-4 w-4\" />
      </Button>
    )
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>

      {/* Recording indicator */}
      {isRecording && (
        <div className=\"flex items-center gap-2\">
          <Badge variant=\"destructive\" className=\"animate-pulse\">
            <div className=\"w-2 h-2 bg-white rounded-full mr-1\" />
            {formatTime(recordingTime)}
          </Badge>

          {/* Audio level indicator */}
          <div className=\"w-16 h-2 bg-gray-200 rounded-full overflow-hidden\">
            <div
              className=\"h-full bg-green-500 transition-all duration-100\"
              style={{ width: `${audioLevel}%` }}
            />
          </div>
        </div>
      )}

      {/* Record/Stop Button */}
      <Button
        variant={isRecording ? \"destructive\" : \"outline\"}
        size=\"icon\"
        onClick={toggleRecording}
        disabled={disabled || isProcessing}
        className=\"flex-shrink-0\"
        title={isRecording ? 'Arrêter l\\'enregistrement' : 'Commencer l\\'enregistrement'}
      >
        {isProcessing ? (
          <Loader2 className=\"h-4 w-4 animate-spin\" />
        ) : isRecording ? (
          <Square className=\"h-4 w-4\" />
        ) : (
          <Mic className=\"h-4 w-4\" />
        )}
      </Button>

      {/* Processing indicator */}
      {isProcessing && (
        <div className=\"flex items-center gap-2\">
          <Loader2 className=\"h-4 w-4 animate-spin\" />
          <span className=\"text-sm text-gray-600\">Transcription...</span>
        </div>
      )}
    </div>
  )
}

// Hook for managing voice recording state
export function useVoiceRecording() {
  const [isSupported, setIsSupported] = useState(false)
  const [permission, setPermission] = useState<PermissionState | null>(null)

  React.useEffect(() => {
    // Check if audio recording is supported
    const supported = typeof navigator !== 'undefined' &&
                     navigator.mediaDevices &&
                     navigator.mediaDevices.getUserMedia

    setIsSupported(supported)

    // Check microphone permission
    if (supported && navigator.permissions) {
      navigator.permissions.query({ name: 'microphone' as PermissionName })
        .then(permissionStatus => {
          setPermission(permissionStatus.state)

          permissionStatus.addEventListener('change', () => {
            setPermission(permissionStatus.state)
          })
        })
        .catch(() => {
          // Permission API not supported, assume we need to request
          setPermission(null)
        })
    }
  }, [])

  const requestPermission = async (): Promise<boolean> => {
    if (!isSupported) return false

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop()) // Stop immediately
      setPermission('granted')
      return true
    } catch (error) {
      setPermission('denied')
      return false
    }
  }

  return {
    isSupported,
    permission,
    requestPermission,
    hasPermission: permission === 'granted'
  }
}