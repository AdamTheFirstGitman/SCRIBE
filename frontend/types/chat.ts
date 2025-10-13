/**
 * Chat types for orchestrated agent interactions
 */

// === SSE Event Types ===

export type SSEEventType =
  | 'start'
  | 'agent_message'
  | 'tool_start'
  | 'tool_complete'
  | 'complete'
  | 'error'

export type AgentName = 'plume' | 'mimir'

export type ToolName =
  | 'search_knowledge'
  | 'web_search'
  | 'get_related_content'
  | 'create_note'
  | 'update_note'

// === Tool Activity Types ===

export interface ToolStartEvent {
  type: 'tool_start'
  agent: AgentName
  tool: ToolName
  params?: Record<string, any>
  timestamp?: number
}

export interface ToolCompleteEvent {
  type: 'tool_complete'
  agent: AgentName
  tool: ToolName
  result: {
    success: boolean
    error?: string
    results_count?: number
    duration_ms?: number
    note_id?: string
    title?: string
    [key: string]: any
  }
  timestamp?: number
}

export interface AgentMessageEvent {
  type: 'agent_message'
  agent: AgentName
  content: string
  timestamp?: number
}

export interface CompleteEvent {
  type: 'complete'
  result: {
    response: string
    agent: AgentName
    conversation_id: string
    clickable_objects?: ClickableObject[]
    metadata?: {
      processing_time?: number
      tokens_used?: number
      cost_eur?: number
    }
  }
}

export interface ErrorEvent {
  type: 'error'
  error: string
}

export type SSEEvent =
  | ToolStartEvent
  | ToolCompleteEvent
  | AgentMessageEvent
  | CompleteEvent
  | ErrorEvent

// === Clickable Objects ===

export interface ClickableObject {
  type: 'viz_link' | 'web_link'
  note_id?: string
  title?: string
  url?: string
}

// === Tool Activity State ===

export interface ToolActivity {
  id: string
  agent: AgentName
  tool: ToolName
  status: 'running' | 'completed' | 'failed'
  params?: Record<string, any>
  result?: {
    success: boolean
    error?: string
    results_count?: number
    duration_ms?: number
    note_id?: string
    title?: string
    [key: string]: any
  }
  startTime: number
  endTime?: number
}

// === Chat Message Types ===

export interface ChatMessageMetadata {
  clickable_objects?: ClickableObject[]
  processing_time?: number
  tokens_used?: number
  cost_eur?: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'plume' | 'mimir'
  content: string
  timestamp: Date
  isLoading?: boolean
  metadata?: ChatMessageMetadata
  toolActivities?: ToolActivity[]
}
