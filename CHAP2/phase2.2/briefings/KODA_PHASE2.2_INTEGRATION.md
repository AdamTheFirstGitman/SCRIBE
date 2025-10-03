# 🔗 KODA - Phase 2.2 : Frontend ↔ Backend Integration

**Agent :** Koda (Integration Specialist)
**Phase :** 2.2 - Phase 2 (Séquentiel APRÈS Phase 1)
**Durée estimée :** 3-4 heures
**Status :** 🚧 À EXÉCUTER

---

## 🎯 OBJECTIF

Connecter le frontend (réalisé par KodaF) et le backend (réalisé par Koda) pour créer une application end-to-end fonctionnelle.

**Mission :** Remplacer les mocks par de vrais appels API, implémenter le streaming SSE, gérer la session et les conversations persistantes.

---

## 📋 CONTEXTE - PHASE 1 TERMINÉE

### ✅ Frontend (KodaF) - FAIT
- Pages : Login, Home (chat), Works, Archives, Viz, Settings
- Composants : InputZone, ChatMessage avec clickable objects
- API mockée (`lib/api/mock.ts`)
- Session localStorage
- **CR :** `/CHAP2/CR_KODAF_PHASE2.2_FRONTEND_UX.md`

### ✅ Backend API (Koda) - FAIT
- 12 endpoints (auth, conversations, notes, upload, metrics)
- Upload audio → Whisper → orchestrator → note structurée
- Clickable objects extraction
- Migration SQL fulltext search
- **CR :** `/CHAP2/CR_KODA_PHASE2.2_BACKEND_API.md`

### ✅ AutoGen Streaming (Koda) - FAIT
- SSE endpoint `/orchestrated/stream`
- AutoGen v0.4 avec fallback
- Messages Plume ↔ Mimir visibles
- **Code :** `/backend/api/chat.py` + `/backend/agents/autogen_agents.py`

### 📊 Analyse Complète
**Fichier :** `/CHAP2/ANALYSE_INTEGRATION_PHASE2.2.md`
- Récapitulatif détaillé Phase 1
- Liste exhaustive ce qui reste à faire
- Priorités P0/P1/P2

---

## 🚀 PRIORITÉS D'INTÉGRATION

### **P0 - CRITICAL (Must Have)** ⚠️

#### 1. Migration SQL (10min) 🔥 **CRITIQUE**
```bash
# AVANT TOUT AUTRE TRAVAIL
psql $SUPABASE_URL -f /Users/adamdahan/Documents/SCRIBE/database/migrations/003_search_function.sql

# Vérification
psql $SUPABASE_URL -c "SELECT search_notes_fulltext('test', 'king_001', 5);"
```

**⚠️ Sans cette migration, le search ne fonctionnera PAS.**

---

#### 2. Client API Basique (1h)

**Fichier à créer :** `frontend/lib/api/client.ts`

**Remplacer TOUS les imports :**
```typescript
// ❌ Supprimer partout
import { ... } from '@/lib/api/mock'

// ✅ Remplacer par
import { ... } from '@/lib/api/client'
```

**Endpoints prioritaires P0 :**
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Helper user_id
function getUserId(): string {
  const session = JSON.parse(localStorage.getItem('session') || '{}')
  return session.user_id || 'king_001'
}

// Auth
export async function login(username: string, password: string): Promise<LoginResponse>
  → POST /api/v1/auth/login

// Conversations
export async function getConversations(limit = 50): Promise<{conversations: Conversation[]}>
  → GET /api/v1/conversations?limit={limit}

export async function getConversation(id: string): Promise<ConversationDetail>
  → GET /api/v1/conversations/{id}

// Notes
export async function getRecentNotes(): Promise<{notes: Note[]}>
  → GET /api/v1/notes/recent

export async function getNote(id: string): Promise<Note>
  → GET /api/v1/notes/{id}

export async function searchNotes(query: string): Promise<{results: SearchResult[]}>
  → GET /api/v1/notes/search?q={query}

// Metrics
export async function getMetrics(): Promise<Metrics>
  → GET /api/v1/metrics/dashboard
```

**Pages à modifier immédiatement :**
- `/app/works/page.tsx` → `getConversations()`
- `/app/works/[id]/page.tsx` → `getConversation(id)`
- `/app/archives/page.tsx` → `getRecentNotes()`, `searchNotes()`
- `/app/viz/[id]/page.tsx` → `getNote(id)`
- `/app/settings/page.tsx` → `getMetrics()`

---

#### 3. Chat Streaming SSE (1h)

**Fonction à créer :** `sendOrchestratedMessageStream()`

```typescript
export async function sendOrchestratedMessageStream(
  request: {
    message: string
    mode?: 'auto' | 'plume' | 'mimir' | 'discussion'
    conversation_id?: string
    user_id?: string
  },
  onMessage: (message: SSEMessage) => void,
  onComplete: (result: any) => void,
  onError: (error: Error) => void
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/chat/orchestrated/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...request,
      user_id: request.user_id || getUserId()
    })
  })

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader!.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.trim() && line.startsWith('data: ')) {
        const jsonStr = line.slice(6)
        if (jsonStr === '[DONE]') return

        const data: SSEMessage = JSON.parse(jsonStr)

        if (data.type === 'complete') {
          onComplete(data.result)
        } else if (data.type === 'error') {
          onError(new Error(data.error))
        } else {
          onMessage(data)
        }
      }
    }
  }
}
```

**Modifier `/app/page.tsx` :**
```typescript
const sendMessage = async () => {
  const userMessage = { id: Date.now().toString(), role: 'user', content: inputText, ... }
  setMessages(prev => [...prev, userMessage])

  const loadingId = `loading-${Date.now()}`
  setMessages(prev => [...prev, { id: loadingId, role: 'plume', content: '', isLoading: true }])

  await sendOrchestratedMessageStream(
    {
      message: inputText,
      mode: 'auto',
      conversation_id: conversationId || undefined
    },
    // onMessage: Afficher messages agents temps réel
    (sseMsg) => {
      if (sseMsg.type === 'agent_message') {
        setMessages(prev => {
          const filtered = prev.filter(m => m.id !== loadingId)
          return [...filtered, {
            id: `${sseMsg.agent}-${Date.now()}`,
            role: sseMsg.agent as 'plume' | 'mimir',
            content: sseMsg.content || '',
            created_at: new Date().toISOString()
          }]
        })
      }
    },
    // onComplete
    (result) => {
      setMessages(prev => prev.filter(m => m.id !== loadingId))
      if (!conversationId) setConversationId(result.conversation_id)
    },
    // onError
    (error) => toast.error(error.message)
  )
}
```

---

#### 4. Upload Audio Workflow (30min)

**Fonction à créer :**
```typescript
export async function uploadAudio(
  audioFile: File,
  contextText?: string,
  contextAudio?: File
): Promise<{
  note_id: string
  title: string
  transcription: string
  agent_response: string
}> {
  const formData = new FormData()
  formData.append('audio_file', audioFile)
  if (contextText) formData.append('context_text', contextText)
  if (contextAudio) formData.append('context_audio', contextAudio)

  const response = await fetch(`${API_BASE_URL}/api/v1/upload/audio`, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) throw new Error('Upload audio failed')
  return await response.json()
}
```

**Modifier `/app/archives/page.tsx` :**
```typescript
const handleAudioUpload = async () => {
  if (!audioFile) return

  setIsProcessing(true)
  try {
    const result = await uploadAudio(
      audioFile,
      contextText || undefined,
      contextAudio || undefined
    )

    toast.success(`Note créée : ${result.title}`)
    router.push(`/viz/${result.note_id}`)
  } catch (error) {
    toast.error('Échec upload audio')
  } finally {
    setIsProcessing(false)
  }
}
```

---

#### 5. CORS Configuration (5min)

**Fichier :** `backend/main.py`

**Vérifier/ajouter :**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://scribe-frontend-qk6s.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

---

### **P1 - IMPORTANT (Should Have)**

#### 6. HTML Conversion Polling (20min)

```typescript
export async function convertToHTML(noteId: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/v1/notes/${noteId}/convert-html`, {
    method: 'POST'
  })
}
```

**Modifier `/app/viz/[id]/page.tsx` :**
```typescript
const handleToggleHTML = async () => {
  if (viewMode === 'html' && !note.html_content) {
    setIsConverting(true)

    try {
      await convertToHTML(note.id)

      // Polling toutes les 2s
      const interval = setInterval(async () => {
        const updated = await getNote(note.id)
        if (updated.html_content) {
          setNote(updated)
          setViewMode('html')
          setIsConverting(false)
          clearInterval(interval)
        }
      }, 2000)

      // Timeout 30s
      setTimeout(() => {
        clearInterval(interval)
        setIsConverting(false)
        toast.error('Conversion timeout')
      }, 30000)

    } catch (error) {
      setIsConverting(false)
      toast.error('Conversion failed')
    }
  } else {
    setViewMode(viewMode === 'text' ? 'html' : 'text')
  }
}
```

---

#### 7. Clickable Objects (10min)

**Déjà prêt !** ✅

Le composant `ChatMessage.tsx` parse déjà `metadata.clickable_objects`.

**Vérifier juste que backend retourne bon format :**
```json
{
  "metadata": {
    "clickable_objects": [
      {"type": "viz_link", "note_id": "...", "title": "..."},
      {"type": "web_link", "url": "...", "title": "..."}
    ]
  }
}
```

---

#### 8. Context Chat depuis Viz (20min)

**Modifier `/app/page.tsx` :**
```typescript
const searchParams = useSearchParams()
const context = searchParams.get('context')

useEffect(() => {
  if (context?.startsWith('note:')) {
    const noteId = context.split(':')[1]
    loadNoteContext(noteId)
  }
}, [context])

const loadNoteContext = async (noteId: string) => {
  const note = await getNote(noteId)
  // Afficher banner contexte
  setContextBanner(`📎 Contexte : ${note.title}`)
  // Ajouter note_id dans context_ids du message
  setContextIds([noteId])
}
```

---

#### 9. Error Handling Global (15min)

**Créer :** `lib/api/error-handler.ts`
```typescript
export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

export async function handleResponse(response: Response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new APIError(response.status, error.detail || response.statusText)
  }
  return response.json()
}
```

**Wrapper toutes les fonctions API :**
```typescript
export async function getNote(id: string): Promise<Note> {
  const res = await fetch(`${API_BASE_URL}/api/v1/notes/${id}`)
  return handleResponse(res)
}
```

---

### **P2 - NICE TO HAVE (Can Wait)**

#### 10. Voice Recording (1h) - OPTIONNEL

Peut attendre. Pour l'instant, micro = upload fichier audio.

#### 11. Tests E2E (1h) - OPTIONNEL

Peut attendre Phase 2.3.

#### 12. Pagination - OPTIONNEL

Peut attendre Phase 2.3.

---

## 🔧 VARIABLES ENVIRONNEMENT

### Frontend `.env.production`
```bash
NEXT_PUBLIC_API_URL=https://scribe-api.onrender.com
```

### Backend (Render)
Vérifier que toutes existent :
```bash
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...
OPENAI_API_KEY=...
CLAUDE_API_KEY=...
```

---

## ✅ CHECKLIST EXÉCUTION

### Setup (15min)
- [ ] Appliquer migration SQL 003 ⚠️ **CRITIQUE**
- [ ] Créer `frontend/lib/api/client.ts`
- [ ] Créer `frontend/lib/api/error-handler.ts`
- [ ] Variables environnement configurées
- [ ] CORS configuré backend

### P0 - Critical (2h)
- [ ] Client API : login, conversations, notes, metrics
- [ ] Chat streaming SSE dans `/app/page.tsx`
- [ ] Upload audio dans `/app/archives/page.tsx`
- [ ] Remplacer mocks dans toutes pages
- [ ] Tests manuels toutes fonctionnalités P0

### P1 - Important (1h)
- [ ] HTML conversion polling
- [ ] Context chat depuis Viz
- [ ] Error handling global
- [ ] Tests manuels P1

### Déploiement (30min)
- [ ] Build frontend production
- [ ] Build backend production
- [ ] Deploy Render frontend
- [ ] Deploy Render backend
- [ ] Tester URLs production
- [ ] Appliquer migration SQL production

---

## 🎯 CRITÈRES DE SUCCÈS

**Fonctionnel :**
- ✅ Login fonctionne avec backend
- ✅ Chat envoie messages et reçoit réponses SSE
- ✅ Streaming messages agents visible
- ✅ Upload audio → transcription → note créée
- ✅ Search notes fonctionne
- ✅ Conversations listées et accessibles
- ✅ Metrics dashboard affiche vraies données

**Qualité :**
- ✅ Pas d'erreurs console browser
- ✅ Pas d'erreurs logs backend
- ✅ Error handling gracieux (toast)
- ✅ Build production sans warnings

**Déploiement :**
- ✅ Frontend accessible : https://scribe-frontend-qk6s.onrender.com
- ✅ Backend accessible : https://scribe-api.onrender.com
- ✅ CORS fonctionne entre les deux
- ✅ Health check OK

---

## 📝 NOTES IMPORTANTES

1. **Migration SQL** : OBLIGATOIRE avant tout. Sans elle, search ne marche pas.

2. **SSE Streaming** : Header `X-Accel-Buffering: no` déjà ajouté backend. Tester keepalive fonctionne.

3. **Upload Audio** :
   - 3 fichiers possibles : audio_file, context_text, context_audio
   - Ordre important dans FormData
   - Limite 25MB Whisper API

4. **AutoGen Discussion** :
   - Mode `discussion` affiche Plume ↔ Mimir temps réel
   - Frontend parse `discussion_history` dans event `complete`

5. **Clickable Objects** :
   - Composant déjà prêt
   - Backend doit retourner format correct dans metadata

6. **Polling HTML** :
   - Préféré vs WebSocket (plus simple)
   - Timeout 30s suffisant (conversions rapides)

---

**Prêt pour exécution !** 🚀

**Durée estimée totale :** 3-4h (P0+P1)
