// Types for the SCRIBE application - Phase 2.2

// === Authentication ===
export interface Session {
  user_id: string
  logged_in: boolean
  expires: number
}

// === Chat & Messages ===
export interface ClickableObject {
  type: 'viz_link' | 'web_link'
  note_id?: string
  title?: string
  url?: string
}

export interface UiMetadata {
  processing_time?: string        // "⏱️ Réponse en 2s"
  context_info?: string           // "└─ 5 notes liées trouvées"
  sources_found?: string          // "🔍 3 documents trouvés [Voir sources ↓]"
  detailed_metrics?: {
    tokens?: number
    cost_eur?: number
    processing_time_ms?: number
  }
}

export interface MessageMetadata {
  clickable_objects?: ClickableObject[]
  processing_time?: number
  tokens_used?: number
  cost_eur?: number
  ui_metadata?: UiMetadata        // User-friendly formatted metadata
}

export interface ChatMessage {
  id: string
  role: 'user' | 'plume' | 'mimir'
  content: string
  timestamp: Date
  metadata?: MessageMetadata
}

// === Conversations ===
export interface Conversation {
  id: string
  title: string
  note_titles: string[]
  updated_at: Date
  message_count: number
}

// === Notes ===
export interface Note {
  id: string
  title: string
  text_content: string
  html_content: string
  created_at: Date
  updated_at: Date
}

export interface NoteSearchResult extends Note {
  snippet?: string
}

// === Metrics ===
export interface Metrics {
  total_notes: number
  total_conversations: number
  total_tokens: number
  total_cost_eur: number
}

// === Upload ===
export interface UploadTextRequest {
  text: string
  context?: string
  contextAudio?: File
}

export interface UploadAudioRequest {
  audio: File
  context?: string
  contextAudio?: File
}

// === API Responses ===
export interface ApiResponse<T> {
  data?: T
  error?: string
  success: boolean
}
