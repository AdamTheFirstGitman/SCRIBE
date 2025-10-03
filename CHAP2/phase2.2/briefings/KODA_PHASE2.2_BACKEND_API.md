# 🔧 KODA - Phase 2.2 : Backend API Endpoints

**Agent :** Koda (Backend Specialist)
**Phase :** 2.2 - Phase 1 (Parallèle)
**Durée estimée :** 4-6 heures
**Status :** 🚧 À EXÉCUTER

---

## 🎯 OBJECTIF

Créer l'ensemble des endpoints API nécessaires pour supporter la nouvelle architecture frontend : authentification simple, gestion conversations, gestion notes (CRUD + search + conversion HTML), upload audio avec transcription, et métriques dashboard.

**Priorité :** Endpoints REST robustes, validation stricte, réponses avec metadata riches (objets clickables).

---

## 📊 ARCHITECTURE ACTUELLE

**Endpoints existants :**
- `POST /chat/plume` - Chat direct avec Plume
- `POST /chat/mimir` - Chat direct avec Mimir
- `POST /chat/orchestrated` - Orchestrator LangGraph (Phase 2.1)
- `POST /upload` - Upload documents
- `POST /transcribe` - Transcription Whisper
- `GET /health` - Health check

**Services existants :**
- PlumeAgent, MimirAgent
- PlumeOrchestrator (LangGraph)
- TranscriptionService (Whisper)
- EmbeddingsService
- Memory Service
- Intent Classifier

**Database (Supabase) :**
- Table `notes` : id, title, text_content, html_content, created_at, updated_at, user_id, metadata
- Table `conversations` : id, title, created_at, updated_at, user_id, metadata
- Table `messages` : id, conversation_id, role, content, created_at, metadata
- Table `user_preferences` : user_id, preferences

**À CRÉER :**
- Endpoints auth
- Endpoints conversations management
- Endpoints notes management
- Endpoint audio upload
- Endpoint metrics

---

## 🏗️ NOUVEAUX ENDPOINTS

### **1. AUTHENTIFICATION**

#### **POST /api/v1/auth/login**

**Description :** Authentification simple pour utilisateur unique (King).

**Request Body :**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response Success (200) :**
```json
{
  "success": true,
  "user_id": "king_001",
  "session_id": "uuid-v4",
  "expires_at": "2025-11-30T12:00:00Z"
}
```

**Response Error (401) :**
```json
{
  "success": false,
  "detail": "Identifiants incorrects"
}
```

**Implémentation :**
```python
# backend/api/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    user_id: str
    session_id: str
    expires_at: datetime

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Simple auth check for single user"""

    # Credentials check
    if request.username == "King" and request.password == "Faire la diff":
        return LoginResponse(
            success=True,
            user_id="king_001",
            session_id=str(uuid.uuid4()),
            expires_at=datetime.now() + timedelta(days=30)
        )

    raise HTTPException(
        status_code=401,
        detail="Identifiants incorrects"
    )
```

**Note :** Pas de vraie gestion de session backend pour l'instant (usage solo). Le frontend stocke user_id en localStorage.

---

### **2. CONVERSATIONS**

#### **GET /api/v1/conversations**

**Description :** Liste toutes les conversations de l'utilisateur.

**Query Params :**
- `limit` (int, default=50) : Nombre max de résultats
- `offset` (int, default=0) : Pagination
- `order_by` (str, default="updated_at") : Tri (created_at, updated_at, title)

**Response (200) :**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "title": "string",
      "note_titles": ["Note 1", "Note 2"],
      "note_ids": ["uuid1", "uuid2"],
      "message_count": 12,
      "created_at": "2025-09-30T10:00:00Z",
      "updated_at": "2025-09-30T15:30:00Z",
      "agents_involved": ["plume", "mimir"]
    }
  ],
  "total": 47,
  "limit": 50,
  "offset": 0
}
```

**Implémentation :**
```python
# backend/api/conversations.py
from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/conversations", tags=["conversations"])

class ConversationSummary(BaseModel):
    id: str
    title: str
    note_titles: List[str]
    note_ids: List[str]
    message_count: int
    created_at: datetime
    updated_at: datetime
    agents_involved: List[str]

class ConversationsListResponse(BaseModel):
    conversations: List[ConversationSummary]
    total: int
    limit: int
    offset: int

@router.get("", response_model=ConversationsListResponse)
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    order_by: str = Query("updated_at", regex="^(created_at|updated_at|title)$")
):
    """List all user conversations with summary"""

    # Query Supabase
    from database.supabase_client import get_supabase_client
    supabase = get_supabase_client()

    # Get conversations
    query = supabase.table('conversations') \
        .select('*, messages(count)') \
        .eq('user_id', 'king_001') \
        .order(order_by, desc=(order_by != 'title')) \
        .range(offset, offset + limit - 1)

    result = query.execute()

    conversations = []
    for conv in result.data:
        # Get associated notes from metadata
        note_ids = conv.get('metadata', {}).get('note_ids', [])

        # Get note titles
        note_titles = []
        if note_ids:
            notes_query = supabase.table('notes') \
                .select('title') \
                .in_('id', note_ids)
            notes_result = notes_query.execute()
            note_titles = [n['title'] for n in notes_result.data]

        conversations.append(ConversationSummary(
            id=conv['id'],
            title=conv['title'],
            note_titles=note_titles,
            note_ids=note_ids,
            message_count=conv['messages'][0]['count'],
            created_at=conv['created_at'],
            updated_at=conv['updated_at'],
            agents_involved=conv.get('metadata', {}).get('agents_involved', [])
        ))

    # Get total count
    count_result = supabase.table('conversations') \
        .select('id', count='exact') \
        .eq('user_id', 'king_001') \
        .execute()

    return ConversationsListResponse(
        conversations=conversations,
        total=count_result.count,
        limit=limit,
        offset=offset
    )
```

---

#### **GET /api/v1/conversations/{conversation_id}**

**Description :** Récupérer conversation complète avec tous les messages.

**Response (200) :**
```json
{
  "id": "uuid",
  "title": "string",
  "created_at": "2025-09-30T10:00:00Z",
  "updated_at": "2025-09-30T15:30:00Z",
  "messages": [
    {
      "id": "uuid",
      "role": "user|plume|mimir",
      "content": "string",
      "created_at": "2025-09-30T10:05:00Z",
      "metadata": {
        "processing_time_ms": 1234,
        "tokens_used": 567,
        "cost_eur": 0.0123,
        "clickable_objects": [
          {
            "type": "viz_link",
            "note_id": "uuid",
            "title": "RAG Architecture"
          }
        ]
      }
    }
  ],
  "note_ids": ["uuid1", "uuid2"]
}
```

**Implémentation :**
```python
class Message(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict

class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message]
    note_ids: List[str]

@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str):
    """Get full conversation with all messages"""

    supabase = get_supabase_client()

    # Get conversation
    conv_result = supabase.table('conversations') \
        .select('*') \
        .eq('id', conversation_id) \
        .eq('user_id', 'king_001') \
        .single() \
        .execute()

    if not conv_result.data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = conv_result.data

    # Get all messages
    messages_result = supabase.table('messages') \
        .select('*') \
        .eq('conversation_id', conversation_id) \
        .order('created_at', desc=False) \
        .execute()

    messages = [
        Message(
            id=msg['id'],
            role=msg['role'],
            content=msg['content'],
            created_at=msg['created_at'],
            metadata=msg.get('metadata', {})
        )
        for msg in messages_result.data
    ]

    return ConversationDetail(
        id=conv['id'],
        title=conv['title'],
        created_at=conv['created_at'],
        updated_at=conv['updated_at'],
        messages=messages,
        note_ids=conv.get('metadata', {}).get('note_ids', [])
    )
```

---

#### **POST /api/v1/conversations**

**Description :** Créer nouvelle conversation.

**Request Body :**
```json
{
  "title": "string (optionnel, auto-généré si absent)",
  "first_message": "string (optionnel)"
}
```

**Response (201) :**
```json
{
  "id": "uuid",
  "title": "string",
  "created_at": "2025-09-30T10:00:00Z"
}
```

**Implémentation :**
```python
class CreateConversationRequest(BaseModel):
    title: Optional[str] = None
    first_message: Optional[str] = None

class CreateConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime

@router.post("", response_model=CreateConversationResponse, status_code=201)
async def create_conversation(request: CreateConversationRequest):
    """Create new conversation"""

    supabase = get_supabase_client()

    # Auto-generate title if not provided
    title = request.title or f"Conversation du {datetime.now().strftime('%d/%m/%Y')}"

    # Create conversation
    conv_data = {
        'title': title,
        'user_id': 'king_001',
        'metadata': {
            'agents_involved': [],
            'note_ids': []
        }
    }

    result = supabase.table('conversations').insert(conv_data).execute()
    conv = result.data[0]

    # Add first message if provided
    if request.first_message:
        message_data = {
            'conversation_id': conv['id'],
            'role': 'user',
            'content': request.first_message,
            'metadata': {}
        }
        supabase.table('messages').insert(message_data).execute()

    return CreateConversationResponse(
        id=conv['id'],
        title=conv['title'],
        created_at=conv['created_at']
    )
```

---

#### **DELETE /api/v1/conversations/{conversation_id}**

**Description :** Supprimer conversation et tous ses messages.

**Response (200) :**
```json
{
  "success": true,
  "message": "Conversation supprimée"
}
```

**Implémentation :**
```python
@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete conversation and all messages"""

    supabase = get_supabase_client()

    # Check ownership
    conv_result = supabase.table('conversations') \
        .select('id') \
        .eq('id', conversation_id) \
        .eq('user_id', 'king_001') \
        .single() \
        .execute()

    if not conv_result.data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete messages (cascade should handle this, but explicit is better)
    supabase.table('messages') \
        .delete() \
        .eq('conversation_id', conversation_id) \
        .execute()

    # Delete conversation
    supabase.table('conversations') \
        .delete() \
        .eq('id', conversation_id) \
        .execute()

    return {"success": True, "message": "Conversation supprimée"}
```

---

### **3. NOTES**

#### **GET /api/v1/notes/recent**

**Description :** Récupérer les 5 notes les plus récentes.

**Response (200) :**
```json
{
  "notes": [
    {
      "id": "uuid",
      "title": "string",
      "text_content": "string",
      "html_content": "string",
      "created_at": "2025-09-30T10:00:00Z",
      "updated_at": "2025-09-30T15:30:00Z"
    }
  ]
}
```

**Implémentation :**
```python
# backend/api/notes.py
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/notes", tags=["notes"])

class Note(BaseModel):
    id: str
    title: str
    text_content: str
    html_content: str
    created_at: datetime
    updated_at: datetime

class NotesListResponse(BaseModel):
    notes: List[Note]

@router.get("/recent", response_model=NotesListResponse)
async def get_recent_notes():
    """Get 5 most recent notes"""

    supabase = get_supabase_client()

    result = supabase.table('notes') \
        .select('*') \
        .eq('user_id', 'king_001') \
        .order('updated_at', desc=True) \
        .limit(5) \
        .execute()

    notes = [Note(**note) for note in result.data]

    return NotesListResponse(notes=notes)
```

---

#### **GET /api/v1/notes/search**

**Description :** Recherche fulltext dans notes (titre + contenu).

**Query Params :**
- `q` (str, required) : Query de recherche
- `limit` (int, default=20) : Nombre max résultats

**Response (200) :**
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "string",
      "snippet": "...texte avec match...",
      "created_at": "2025-09-30T10:00:00Z",
      "updated_at": "2025-09-30T15:30:00Z",
      "relevance_score": 0.95
    }
  ],
  "total": 5
}
```

**Implémentation :**
```python
class SearchResult(BaseModel):
    id: str
    title: str
    snippet: str
    created_at: datetime
    updated_at: datetime
    relevance_score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int

@router.get("/search", response_model=SearchResponse)
async def search_notes(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100)
):
    """Fulltext search in notes"""

    supabase = get_supabase_client()

    # Use PostgreSQL fulltext search
    # textsearchquery uses to_tsquery for better search
    result = supabase.rpc('search_notes_fulltext', {
        'search_query': q,
        'user_id_param': 'king_001',
        'limit_param': limit
    }).execute()

    # If RPC not exists, fallback to ILIKE (less performant)
    if not result.data:
        result = supabase.table('notes') \
            .select('*') \
            .eq('user_id', 'king_001') \
            .or_(f'title.ilike.%{q}%,text_content.ilike.%{q}%') \
            .limit(limit) \
            .execute()

    results = []
    for note in result.data:
        # Generate snippet around match
        snippet = generate_snippet(note['text_content'], q, max_length=150)

        results.append(SearchResult(
            id=note['id'],
            title=note['title'],
            snippet=snippet,
            created_at=note['created_at'],
            updated_at=note['updated_at'],
            relevance_score=note.get('relevance_score', 0.5)
        ))

    return SearchResponse(
        results=results,
        total=len(results)
    )

def generate_snippet(text: str, query: str, max_length: int = 150) -> str:
    """Generate snippet with query context"""
    query_lower = query.lower()
    text_lower = text.lower()

    # Find query position
    pos = text_lower.find(query_lower)

    if pos == -1:
        # Query not found, return beginning
        return text[:max_length] + ('...' if len(text) > max_length else '')

    # Extract context around query
    start = max(0, pos - 50)
    end = min(len(text), pos + len(query) + 100)

    snippet = text[start:end]

    if start > 0:
        snippet = '...' + snippet
    if end < len(text):
        snippet = snippet + '...'

    return snippet
```

**SQL Function (créer migration) :**
```sql
-- database/migrations/003_search_function.sql
CREATE OR REPLACE FUNCTION search_notes_fulltext(
    search_query TEXT,
    user_id_param TEXT,
    limit_param INT
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    text_content TEXT,
    html_content TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    relevance_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id,
        n.title,
        n.text_content,
        n.html_content,
        n.created_at,
        n.updated_at,
        ts_rank(
            to_tsvector('french', n.title || ' ' || n.text_content),
            to_tsquery('french', search_query)
        ) AS relevance_score
    FROM notes n
    WHERE
        n.user_id = user_id_param
        AND to_tsvector('french', n.title || ' ' || n.text_content) @@ to_tsquery('french', search_query)
    ORDER BY relevance_score DESC
    LIMIT limit_param;
END;
$$ LANGUAGE plpgsql;
```

---

#### **GET /api/v1/notes/{note_id}**

**Description :** Récupérer note spécifique.

**Response (200) :**
```json
{
  "id": "uuid",
  "title": "string",
  "text_content": "string",
  "html_content": "string",
  "created_at": "2025-09-30T10:00:00Z",
  "updated_at": "2025-09-30T15:30:00Z"
}
```

**Implémentation :**
```python
@router.get("/{note_id}", response_model=Note)
async def get_note(note_id: str):
    """Get specific note"""

    supabase = get_supabase_client()

    result = supabase.table('notes') \
        .select('*') \
        .eq('id', note_id) \
        .eq('user_id', 'king_001') \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Note not found")

    return Note(**result.data)
```

---

#### **POST /api/v1/notes/{note_id}/convert-html**

**Description :** Convertir texte de note en HTML (async avec background task).

**Response (202 Accepted) :**
```json
{
  "status": "processing",
  "note_id": "uuid",
  "message": "Conversion HTML en cours..."
}
```

**Implémentation :**
```python
class ConvertHTMLResponse(BaseModel):
    status: str
    note_id: str
    message: str

@router.post("/{note_id}/convert-html", response_model=ConvertHTMLResponse, status_code=202)
async def convert_note_to_html(note_id: str, background_tasks: BackgroundTasks):
    """Convert note text to HTML (async)"""

    supabase = get_supabase_client()

    # Check note exists
    note_result = supabase.table('notes') \
        .select('id, text_content') \
        .eq('id', note_id) \
        .eq('user_id', 'king_001') \
        .single() \
        .execute()

    if not note_result.data:
        raise HTTPException(status_code=404, detail="Note not found")

    # Launch background task
    background_tasks.add_task(process_html_conversion, note_id, note_result.data['text_content'])

    return ConvertHTMLResponse(
        status="processing",
        note_id=note_id,
        message="Conversion HTML en cours..."
    )

async def process_html_conversion(note_id: str, text_content: str):
    """Background task to convert text to HTML"""

    try:
        # Use existing text-to-html service
        from services.text_to_html import convert_text_to_html

        html_content = await convert_text_to_html(text_content)

        # Update note in database
        supabase = get_supabase_client()
        supabase.table('notes') \
            .update({'html_content': html_content, 'updated_at': datetime.now().isoformat()}) \
            .eq('id', note_id) \
            .execute()

        logger.info(f"HTML conversion completed for note {note_id}")

    except Exception as e:
        logger.error(f"HTML conversion failed for note {note_id}: {str(e)}")
        # TODO: Store error in note metadata
```

**Note :** Frontend peut soit :
- Polling : GET /notes/{id} toutes les 2s jusqu'à html_content non vide
- WebSocket : Recevoir notification quand conversion terminée (Phase 2.2 Integration)

---

### **4. UPLOAD**

#### **POST /api/v1/upload/text**

**Description :** Créer note depuis texte.

**Request Body :**
```json
{
  "text": "string",
  "context": "string (optionnel, info pour Mimir)"
}
```

**Response (201) :**
```json
{
  "note_id": "uuid",
  "title": "string (auto-généré)",
  "created_at": "2025-09-30T10:00:00Z"
}
```

**Implémentation :**
```python
# backend/api/upload.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/upload", tags=["upload"])

class UploadTextRequest(BaseModel):
    text: str
    context: Optional[str] = None

class UploadResponse(BaseModel):
    note_id: str
    title: str
    created_at: datetime

@router.post("/text", response_model=UploadResponse, status_code=201)
async def upload_text(request: UploadTextRequest):
    """Create note from text"""

    # Generate title from first line or first 50 chars
    title = request.text.split('\n')[0][:50]
    if len(title) == 50:
        title += '...'
    if not title.strip():
        title = "Nouvelle note"

    # Create note
    supabase = get_supabase_client()
    note_data = {
        'title': title,
        'text_content': request.text,
        'html_content': '',  # Will be converted on-demand
        'user_id': 'king_001',
        'metadata': {
            'context': request.context or '',
            'source': 'manual_upload'
        }
    }

    result = supabase.table('notes').insert(note_data).execute()
    note = result.data[0]

    # Index for RAG search (background)
    from services.embeddings import embed_and_store
    asyncio.create_task(embed_and_store(note['id'], request.text))

    return UploadResponse(
        note_id=note['id'],
        title=note['title'],
        created_at=note['created_at']
    )
```

---

#### **POST /api/v1/upload/audio**

**Description :** Upload fichier audio → transcription Whisper → agents créent note structurée.

**Request :** Multipart form-data
- `audio_file` : Audio file principal (mp3, wav, m4a, webm, ogg)
- `context_text` : String optionnel (texte de contexte)
- `context_audio` : Audio file optionnel (contexte en audio)

**Response (201) :**
```json
{
  "note_id": "uuid",
  "title": "string (généré par agents)",
  "transcription": "string",
  "created_at": "2025-09-30T10:00:00Z",
  "agent_response": "string (message de confirmation des agents)"
}
```

**Workflow :**
1. (Invisible) Transcription Whisper audio principal
2. (Invisible) Transcription Whisper context audio si présent
3. (Invisible) Envoi aux agents via orchestrator : "Crée une note structurée basée sur : [transcription] + contexte : [context]"
4. (Invisible) Agents (Plume) traitent, améliorent et créent note
5. Retourne note créée avec réponse agents

**Implémentation :**
```python
class UploadAudioResponse(BaseModel):
    note_id: str
    title: str
    transcription: str
    created_at: datetime
    agent_response: str

@router.post("/audio", response_model=UploadAudioResponse, status_code=201)
async def upload_audio(
    fastapi_request: Request,
    audio_file: UploadFile = File(..., description="Audio file principal"),
    context_text: Optional[str] = Form(None),
    context_audio: Optional[UploadFile] = File(None)
):
    """Upload audio, transcribe, and let agents create structured note"""

    # Validate main audio file type
    allowed_types = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/webm', 'audio/ogg']
    if audio_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporté. Formats acceptés : mp3, wav, m4a, webm, ogg"
        )

    import tempfile
    import os
    from services.transcription import TranscriptionService

    transcription_service = TranscriptionService()
    temp_files = []

    try:
        # 1. Transcribe main audio
        temp_audio = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(audio_file.filename)[1]
        )
        temp_files.append(temp_audio.name)

        content = await audio_file.read()
        temp_audio.write(content)
        temp_audio.close()

        main_transcription_result = await transcription_service.transcribe(temp_audio.name)
        main_transcription = main_transcription_result['text']

        logger.info(f"Main audio transcribed: {len(main_transcription)} chars")

        # 2. Build context (text or audio transcription)
        context_content = ""

        if context_audio:
            # Transcribe context audio
            temp_context = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(context_audio.filename)[1]
            )
            temp_files.append(temp_context.name)

            context_audio_content = await context_audio.read()
            temp_context.write(context_audio_content)
            temp_context.close()

            context_transcription_result = await transcription_service.transcribe(temp_context.name)
            context_content = context_transcription_result['text']

            logger.info(f"Context audio transcribed: {len(context_content)} chars")

        elif context_text:
            context_content = context_text

        # 3. Send to agents via orchestrator
        orchestrator: PlumeOrchestrator = fastapi_request.app.state.orchestrator

        # Build prompt for agents
        agent_prompt = f"""Crée une note structurée et bien organisée basée sur cette transcription audio :

{main_transcription}"""

        if context_content:
            agent_prompt += f"""

Informations contextuelles supplémentaires :
{context_content}"""

        agent_prompt += """

Instructions :
- Crée un titre pertinent et descriptif
- Structure le contenu de manière claire (sections, points si nécessaire)
- Corrige les erreurs de transcription éventuelles
- Améliore la lisibilité tout en préservant le sens
"""

        # Process with orchestrator
        result = await orchestrator.process(
            input_text=agent_prompt,
            mode="plume",  # Force Plume pour création note
            user_id="king_001",
            session_id=str(uuid.uuid4())
        )

        # 4. Extract note_id from result
        # Agents should have created note and stored it
        note_id = result.get("note_id")

        if not note_id:
            # Fallback: create note manually if agents didn't
            supabase = get_supabase_client()
            note_data = {
                'title': f"Note audio - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                'text_content': main_transcription,
                'html_content': '',
                'user_id': 'king_001',
                'metadata': {
                    'source': 'audio_upload',
                    'original_filename': audio_file.filename,
                    'context': context_content or ''
                }
            }
            note_result = supabase.table('notes').insert(note_data).execute()
            note_id = note_result.data[0]['id']

        return UploadAudioResponse(
            note_id=note_id,
            title=result.get("title", "Note créée"),
            transcription=main_transcription,
            created_at=datetime.now(),
            agent_response=result["response"]
        )

    except Exception as e:
        logger.error(f"Audio upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement audio : {str(e)}"
        )

    finally:
        # Clean up temp files
        for temp_path in temp_files:
            try:
                os.unlink(temp_path)
            except:
                pass
```

**Note importante :** Les fichiers audio sont **supprimés après transcription** (pas de stockage audio). Seules les transcriptions sont conservées.

---

### **5. METRICS**

#### **GET /api/v1/metrics/dashboard**

**Description :** Récupérer métriques pour dashboard settings.

**Response (200) :**
```json
{
  "total_notes": 47,
  "total_conversations": 23,
  "total_tokens": 156432,
  "total_cost_eur": 12.34,
  "last_30_days": {
    "tokens": 23456,
    "cost_eur": 2.15
  }
}
```

**Implémentation :**
```python
# backend/api/metrics.py
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter(prefix="/metrics", tags=["metrics"])

class MetricsPeriod(BaseModel):
    tokens: int
    cost_eur: float

class DashboardMetrics(BaseModel):
    total_notes: int
    total_conversations: int
    total_tokens: int
    total_cost_eur: float
    last_30_days: MetricsPeriod

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get metrics for dashboard"""

    supabase = get_supabase_client()

    # Count notes
    notes_result = supabase.table('notes') \
        .select('id', count='exact') \
        .eq('user_id', 'king_001') \
        .execute()
    total_notes = notes_result.count

    # Count conversations
    convs_result = supabase.table('conversations') \
        .select('id', count='exact') \
        .eq('user_id', 'king_001') \
        .execute()
    total_conversations = convs_result.count

    # Get token usage from messages metadata
    messages_result = supabase.table('messages') \
        .select('metadata') \
        .execute()

    total_tokens = 0
    total_cost = 0.0
    last_30_days_tokens = 0
    last_30_days_cost = 0.0

    cutoff_date = datetime.now() - timedelta(days=30)

    for msg in messages_result.data:
        metadata = msg.get('metadata', {})
        tokens = metadata.get('tokens_used', 0)
        cost = metadata.get('cost_eur', 0.0)
        created_at = datetime.fromisoformat(msg.get('created_at', '2000-01-01'))

        total_tokens += tokens
        total_cost += cost

        if created_at >= cutoff_date:
            last_30_days_tokens += tokens
            last_30_days_cost += cost

    return DashboardMetrics(
        total_notes=total_notes,
        total_conversations=total_conversations,
        total_tokens=total_tokens,
        total_cost_eur=round(total_cost, 2),
        last_30_days=MetricsPeriod(
            tokens=last_30_days_tokens,
            cost_eur=round(last_30_days_cost, 2)
        )
    )
```

---

## 🔄 MODIFICATION ORCHESTRATOR (Clickable Objects)

**Fichier :** `backend/agents/orchestrator.py`

**Objectif :** Ajouter metadata avec objets clickables dans les réponses des agents.

**Modification dans `finalize_node` :**
```python
async def finalize_node(self, state: AgentState) -> AgentState:
    """Finalize response with metadata"""

    response = state.get("response", "")
    agent_used = state.get("agent_used", "unknown")

    # Extract clickable objects from response
    clickable_objects = extract_clickable_objects(
        response=response,
        context_note_ids=state.get("context_ids", [])
    )

    # Calculate metrics
    total_tokens = sum(state.get("tokens_used_per_step", {}).values())
    total_cost = total_tokens * 0.00001  # Approximate cost per token

    # Update state with metadata
    state["metadata"] = {
        "clickable_objects": clickable_objects,
        "processing_time_ms": state.get("processing_time_ms", 0),
        "tokens_used": total_tokens,
        "cost_eur": round(total_cost, 6),
        "agent_used": agent_used,
        "agents_involved": state.get("agents_involved", [])
    }

    return state

def extract_clickable_objects(response: str, context_note_ids: List[str]) -> List[Dict]:
    """Extract clickable objects from agent response"""

    objects = []

    # Pattern 1: Explicit note references
    # Ex: "Voir la note [[RAG Architecture]]" ou "Note #uuid"
    import re

    # Match [[Note Title]]
    note_refs = re.findall(r'\[\[([^\]]+)\]\]', response)
    for title in note_refs:
        # Find note by title
        supabase = get_supabase_client()
        result = supabase.table('notes') \
            .select('id, title') \
            .eq('title', title) \
            .eq('user_id', 'king_001') \
            .limit(1) \
            .execute()

        if result.data:
            objects.append({
                'type': 'viz_link',
                'note_id': result.data[0]['id'],
                'title': result.data[0]['title']
            })

    # Pattern 2: URLs
    urls = re.findall(r'https?://[^\s]+', response)
    for url in urls:
        objects.append({
            'type': 'web_link',
            'url': url,
            'title': url.split('/')[2]  # Extract domain
        })

    # Pattern 3: Context notes (if referenced in conversation)
    if context_note_ids:
        for note_id in context_note_ids:
            result = supabase.table('notes') \
                .select('id, title') \
                .eq('id', note_id) \
                .single() \
                .execute()

            if result.data:
                objects.append({
                    'type': 'viz_link',
                    'note_id': result.data['id'],
                    'title': result.data['title']
                })

    return objects
```

---

## 📋 CHECKLIST DE TÂCHES

### **Setup**
- [ ] Créer fichiers routers : `api/auth.py`, `api/conversations.py`, `api/notes.py`, `api/upload.py`, `api/metrics.py`
- [ ] Créer migration SQL : `003_search_function.sql`
- [ ] Créer helper `extract_clickable_objects()` dans `utils/`

### **Endpoints Auth**
- [ ] POST /auth/login avec validation King/password

### **Endpoints Conversations**
- [ ] GET /conversations avec pagination
- [ ] GET /conversations/{id} avec messages complets
- [ ] POST /conversations (création)
- [ ] DELETE /conversations/{id}

### **Endpoints Notes**
- [ ] GET /notes/recent (5 dernières)
- [ ] GET /notes/search (fulltext avec snippet)
- [ ] GET /notes/{id}
- [ ] POST /notes/{id}/convert-html (background task)

### **Endpoints Upload**
- [ ] POST /upload/text
- [ ] POST /upload/audio (Whisper + suppression fichier)

### **Endpoints Metrics**
- [ ] GET /metrics/dashboard

### **Orchestrator**
- [ ] Ajouter `extract_clickable_objects()` dans finalize_node
- [ ] Tester avec patterns [[Note]], URLs, context_ids

### **Database**
- [ ] Créer function SQL `search_notes_fulltext()`
- [ ] Vérifier tables conversations/messages/notes existent
- [ ] Vérifier indexes sur user_id, created_at, updated_at

### **Tests**
- [ ] Tester tous endpoints avec curl/Postman
- [ ] Vérifier clickable_objects dans réponses orchestrator
- [ ] Tester upload audio end-to-end (+ suppression fichier)
- [ ] Tester search avec accents français

### **Déploiement**
- [ ] Ajouter routes dans main.py
- [ ] Vérifier variables env (SUPABASE_*, OPENAI_API_KEY)
- [ ] Push vers Render
- [ ] Tester health check

---

## 🎯 CRITÈRES DE SUCCÈS

**Endpoints :**
- ✅ Tous les endpoints répondent correctement
- ✅ Validation Pydantic stricte
- ✅ Error handling avec messages clairs

**Fonctionnalités :**
- ✅ Auth simple fonctionnelle
- ✅ Search fulltext rapide (< 200ms)
- ✅ Upload audio → transcription → note (fichier supprimé)
- ✅ Conversion HTML async non-bloquante
- ✅ Clickable objects extraits dans réponses agents

**Qualité :**
- ✅ Code TypeHinted (mypy clean)
- ✅ Logging approprié
- ✅ Tests unitaires endpoints critiques

**Performance :**
- ✅ GET /conversations < 100ms
- ✅ Search < 200ms
- ✅ Upload audio < 10s (selon taille fichier)

**Déploiement :**
- ✅ Déployé sur Render sans erreurs
- ✅ Health check vert
- ✅ Logs propres

---

## 📝 NOTES IMPORTANTES

1. **Auth Simple :** Pas de JWT/session backend. Juste validation username/password. Le frontend gère session en localStorage.

2. **Clickable Objects :** Format flexible. Préparer pour extensions futures (charts, images, etc.).

3. **Audio Upload :** Fichier supprimé après transcription pour économiser storage. Seul le texte transcrit est conservé.

4. **HTML Conversion :** Background task async. Frontend peut polling GET /notes/{id} ou attendre notification WebSocket (Phase 2).

5. **Search Function :** Nécessite PostgreSQL fulltext. Fallback ILIKE si function pas disponible (moins performant).

6. **Metrics :** Calculées en temps réel depuis messages metadata. Pas de table metrics séparée pour l'instant (optimisation future si lent).

7. **Conversation Title :** Auto-généré si pas fourni. Peut être régénéré par LLM plus tard (feature future).

---

**Document créé par :** Leo (Architecture)
**Pour agent :** Koda (Backend Specialist)
**Phase :** 2.2 Phase 1 (Parallèle)
**Date :** 30 septembre 2025
