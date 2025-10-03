// Mock API for Phase 2.2 Phase 1 - Will be replaced with real API calls in Phase 2 (Integration)

import {
  Conversation,
  Note,
  NoteSearchResult,
  Metrics,
  ChatMessage
} from '../types'

// === Mock Data ===

const mockNotes: Note[] = [
  {
    id: '1',
    title: 'RAG Architecture Overview',
    text_content: `# RAG Architecture

Retrieval-Augmented Generation (RAG) is a technique for enhancing LLMs with external knowledge...`,
    html_content: '<h1>RAG Architecture</h1><p>Retrieval-Augmented Generation (RAG) is a technique for enhancing LLMs with external knowledge...</p>',
    created_at: new Date(2025, 8, 25),
    updated_at: new Date(2025, 8, 28)
  },
  {
    id: '2',
    title: 'Vector Embeddings Deep Dive',
    text_content: 'Vector embeddings are numerical representations of text...',
    html_content: '<h1>Vector Embeddings</h1><p>Vector embeddings are numerical representations...</p>',
    created_at: new Date(2025, 8, 26),
    updated_at: new Date(2025, 8, 26)
  },
  {
    id: '3',
    title: 'Semantic Search Implementation',
    text_content: 'Semantic search goes beyond keyword matching...',
    html_content: '<h1>Semantic Search</h1><p>Semantic search goes beyond keyword matching...</p>',
    created_at: new Date(2025, 8, 27),
    updated_at: new Date(2025, 8, 29)
  },
  {
    id: '4',
    title: 'LangGraph Orchestration Guide',
    text_content: 'LangGraph is a library for building stateful, multi-actor applications...',
    html_content: '<h1>LangGraph Orchestration</h1><p>LangGraph is a library for building...</p>',
    created_at: new Date(2025, 8, 24),
    updated_at: new Date(2025, 8, 30)
  },
  {
    id: '5',
    title: 'Autogen Multi-Agent Systems',
    text_content: 'AutoGen enables the development of LLM applications using multiple agents...',
    html_content: '<h1>AutoGen Multi-Agent Systems</h1><p>AutoGen enables the development...</p>',
    created_at: new Date(2025, 8, 23),
    updated_at: new Date(2025, 8, 23)
  }
]

const mockConversations: Conversation[] = [
  {
    id: 'conv-1',
    title: 'Recherche sur le RAG',
    note_titles: ['RAG Architecture Overview', 'Vector Embeddings Deep Dive', 'Semantic Search Implementation'],
    updated_at: new Date(), // Today
    message_count: 12
  },
  {
    id: 'conv-2',
    title: 'Discussion agents LangGraph',
    note_titles: ['LangGraph Orchestration Guide'],
    updated_at: new Date(Date.now() - 24 * 3600 * 1000), // Yesterday
    message_count: 8
  },
  {
    id: 'conv-3',
    title: 'Implémentation AutoGen',
    note_titles: ['Autogen Multi-Agent Systems', 'Vector Embeddings Deep Dive'],
    updated_at: new Date(Date.now() - 3 * 24 * 3600 * 1000), // 3 days ago
    message_count: 15
  },
  {
    id: 'conv-4',
    title: 'Optimisation performance RAG',
    note_titles: ['RAG Architecture Overview', 'Semantic Search Implementation'],
    updated_at: new Date(Date.now() - 7 * 24 * 3600 * 1000), // 7 days ago
    message_count: 6
  }
]

const mockMessages: Record<string, ChatMessage[]> = {
  'conv-1': [
    {
      id: 'msg-1',
      role: 'user',
      content: 'Explique-moi le RAG en détail',
      timestamp: new Date(Date.now() - 2 * 3600 * 1000)
    },
    {
      id: 'msg-2',
      role: 'mimir',
      content: 'Le RAG (Retrieval-Augmented Generation) combine la recherche d\'informations avec la génération de texte. J\'ai trouvé des notes pertinentes sur ce sujet.',
      timestamp: new Date(Date.now() - 2 * 3600 * 1000 + 5000),
      metadata: {
        clickable_objects: [
          { type: 'viz_link', note_id: '1', title: 'RAG Architecture Overview' }
        ],
        processing_time: 1234,
        tokens_used: 456,
        cost_eur: 0.0023
      }
    },
    {
      id: 'msg-3',
      role: 'user',
      content: 'Et les embeddings vectoriels ?',
      timestamp: new Date(Date.now() - 1 * 3600 * 1000)
    },
    {
      id: 'msg-4',
      role: 'plume',
      content: 'Les embeddings vectoriels transforment le texte en vecteurs numériques pour permettre des comparaisons sémantiques. Voici une note détaillée que j\'ai créée.',
      timestamp: new Date(Date.now() - 1 * 3600 * 1000 + 3000),
      metadata: {
        clickable_objects: [
          { type: 'viz_link', note_id: '2', title: 'Vector Embeddings Deep Dive' }
        ],
        processing_time: 2567,
        tokens_used: 892,
        cost_eur: 0.0045
      }
    }
  ]
}

// === API Functions ===

/**
 * Get all conversations
 */
export async function getConversations(): Promise<Conversation[]> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 300))
  return mockConversations
}

/**
 * Get a specific conversation with messages
 */
export async function getConversation(id: string): Promise<{ conversation: Conversation, messages: ChatMessage[] }> {
  await new Promise(resolve => setTimeout(resolve, 400))

  const conversation = mockConversations.find(c => c.id === id)
  if (!conversation) {
    throw new Error('Conversation not found')
  }

  const messages = mockMessages[id] || []

  return { conversation, messages }
}

/**
 * Get recent notes (last 5)
 */
export async function getRecentNotes(): Promise<Note[]> {
  await new Promise(resolve => setTimeout(resolve, 200))
  return mockNotes.slice(0, 5)
}

/**
 * Get all notes
 */
export async function getAllNotes(): Promise<Note[]> {
  await new Promise(resolve => setTimeout(resolve, 300))
  return mockNotes
}

/**
 * Get a specific note
 */
export async function getNote(id: string): Promise<Note> {
  await new Promise(resolve => setTimeout(resolve, 200))

  const note = mockNotes.find(n => n.id === id)
  if (!note) {
    throw new Error('Note not found')
  }

  return note
}

/**
 * Search notes by query
 */
export async function searchNotes(query: string): Promise<NoteSearchResult[]> {
  await new Promise(resolve => setTimeout(resolve, 400))

  if (!query.trim()) {
    return []
  }

  const lowerQuery = query.toLowerCase()
  const results = mockNotes
    .filter(note =>
      note.title.toLowerCase().includes(lowerQuery) ||
      note.text_content.toLowerCase().includes(lowerQuery)
    )
    .map(note => ({
      ...note,
      snippet: note.text_content.substring(0, 150) + '...'
    }))

  return results
}

/**
 * Upload text and create note
 */
export async function uploadText(text: string, _context?: string, _contextAudio?: File): Promise<Note> {
  await new Promise(resolve => setTimeout(resolve, 1500))

  const newNote: Note = {
    id: `note-${Date.now()}`,
    title: `Note du ${new Date().toLocaleDateString()}`,
    text_content: text,
    html_content: '',
    created_at: new Date(),
    updated_at: new Date()
  }

  // Add to mock data (in real app, this would be on server)
  mockNotes.unshift(newNote)

  return newNote
}

/**
 * Upload audio and create note (with transcription simulation)
 */
export async function uploadAudio(file: File, _context?: string, _contextAudio?: File): Promise<Note> {
  // Simulate longer processing (transcription + agent processing)
  await new Promise(resolve => setTimeout(resolve, 3000))

  const newNote: Note = {
    id: `note-${Date.now()}`,
    title: `Transcription audio du ${new Date().toLocaleDateString()}`,
    text_content: `[Transcription simulée du fichier ${file.name}]\n\nCeci est une simulation de transcription. En production, ce texte sera généré par Whisper API.`,
    html_content: '',
    created_at: new Date(),
    updated_at: new Date()
  }

  mockNotes.unshift(newNote)

  return newNote
}

/**
 * Convert note to HTML (async operation)
 */
export async function convertToHTML(noteId: string): Promise<string> {
  // Simulate conversion delay
  await new Promise(resolve => setTimeout(resolve, 2000))

  const note = mockNotes.find(n => n.id === noteId)
  if (!note) {
    throw new Error('Note not found')
  }

  // Simulate HTML conversion
  const htmlContent = `<div class="note-html">
    <h1>${note.title}</h1>
    <div class="content">
      ${note.text_content.split('\n').map(line => `<p>${line}</p>`).join('')}
    </div>
  </div>`

  // Update mock data
  note.html_content = htmlContent

  return htmlContent
}

/**
 * Send chat message and get response
 */
export async function sendChatMessage(message: string, _context?: string): Promise<ChatMessage> {
  await new Promise(resolve => setTimeout(resolve, 2000))

  // Simulate agent response
  const agentRole = Math.random() > 0.5 ? 'plume' : 'mimir'
  const response: ChatMessage = {
    id: `msg-${Date.now()}`,
    role: agentRole,
    content: `Réponse simulée de ${agentRole === 'plume' ? 'Plume' : 'Mimir'} à : "${message}"`,
    timestamp: new Date(),
    metadata: {
      processing_time: Math.floor(Math.random() * 3000) + 500,
      tokens_used: Math.floor(Math.random() * 500) + 100,
      cost_eur: Math.random() * 0.01
    }
  }

  return response
}

/**
 * Get usage metrics
 */
export async function getMetrics(): Promise<Metrics> {
  await new Promise(resolve => setTimeout(resolve, 300))

  return {
    total_notes: mockNotes.length,
    total_conversations: mockConversations.length,
    total_tokens: 156432,
    total_cost_eur: 12.34
  }
}
