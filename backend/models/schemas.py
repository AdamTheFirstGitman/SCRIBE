"""
Pydantic schemas for Plume & Mimir API
Request/Response models with validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import uuid

# =============================================================================
# ENUMS
# =============================================================================

class AgentMode(str, Enum):
    """Available agent modes"""
    AUTO = "auto"
    PLUME = "plume"
    MIMIR = "mimir"
    DISCUSSION = "discussion"

class MessageRole(str, Enum):
    """Message roles in conversations"""
    USER = "user"
    PLUME = "plume"
    MIMIR = "mimir"
    SYSTEM = "system"

class AudioFormat(str, Enum):
    """Supported audio formats"""
    WEBM = "webm"
    MP3 = "mp3"
    WAV = "wav"
    M4A = "m4a"
    OGG = "ogg"

class SearchType(str, Enum):
    """Search types"""
    VECTOR = "vector"
    FULLTEXT = "fulltext"
    HYBRID = "hybrid"

# =============================================================================
# BASE MODELS
# =============================================================================

class TimestampedModel(BaseModel):
    """Base model with timestamps"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class UUIDModel(BaseModel):
    """Base model with UUID"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

# =============================================================================
# CHAT MODELS
# =============================================================================

class MessageContent(BaseModel):
    """Individual message content"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    """Chat request from user"""
    message: Optional[str] = None
    voice_data: Optional[str] = Field(None, description="Base64 encoded audio data")
    audio_format: AudioFormat = AudioFormat.WEBM
    mode: AgentMode = AgentMode.AUTO
    context_ids: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None

    @validator('message', 'voice_data')
    def validate_input(cls, v, values):
        """Ensure either message or voice_data is provided"""
        if not v and not values.get('voice_data') and not values.get('message'):
            raise ValueError('Either message or voice_data must be provided')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "message": "How does photosynthesis work?",
                "mode": "auto",
                "context_ids": [],
                "session_id": "session_123"
            }
        }

class AgentResponse(BaseModel):
    """Response from an agent"""
    agent: str
    content: str
    html: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    sources: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    """Chat response to user"""
    response: str
    html: Optional[str] = None
    agent_used: str
    agents_involved: List[str] = Field(default_factory=list)
    session_id: str
    sources: List[str] = Field(default_factory=list)
    processing_time_ms: float
    tokens_used: int = 0
    cost_eur: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Photosynthesis is the process by which plants convert light energy into chemical energy...",
                "agent_used": "mimir",
                "agents_involved": ["mimir"],
                "session_id": "session_123",
                "sources": ["note_456", "note_789"],
                "processing_time_ms": 1250.5,
                "tokens_used": 150,
                "cost_eur": 0.02
            }
        }

# =============================================================================
# TRANSCRIPTION MODELS
# =============================================================================

class TranscriptionRequest(BaseModel):
    """Audio transcription request"""
    audio_data: str = Field(..., description="Base64 encoded audio data")
    format: AudioFormat = AudioFormat.WEBM
    language: Optional[str] = Field(None, description="Language hint (e.g., 'fr', 'en')")

class TranscriptionResponse(BaseModel):
    """Audio transcription response"""
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    duration_seconds: float
    language: Optional[str] = None
    processing_time_ms: float

# =============================================================================
# NOTE MODELS
# =============================================================================

class NoteCreate(BaseModel):
    """Create new note"""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    html: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Tag length must be <= 50 characters')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Understanding Photosynthesis",
                "content": "Photosynthesis is a crucial biological process...",
                "tags": ["biology", "plants", "energy"],
                "metadata": {"source": "conversation", "complexity": "intermediate"}
            }
        }

class NoteUpdate(BaseModel):
    """Update existing note"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    html: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        if v:
            for tag in v:
                if len(tag) > 50:
                    raise ValueError('Tag length must be <= 50 characters')
        return v

class NoteResponse(UUIDModel, TimestampedModel):
    """Note response model"""
    title: str
    content: str
    html: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_deleted: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Understanding Photosynthesis",
                "content": "Photosynthesis is a crucial biological process...",
                "html": "<p>Photosynthesis is a crucial biological process...</p>",
                "tags": ["biology", "plants", "energy"],
                "metadata": {"source": "conversation", "complexity": "intermediate"},
                "created_at": "2023-12-01T10:00:00Z",
                "updated_at": "2023-12-01T10:00:00Z",
                "is_deleted": False
            }
        }

class NoteList(BaseModel):
    """Paginated list of notes"""
    notes: List[NoteResponse]
    total: int
    page: int = 1
    per_page: int = 20
    has_next: bool
    has_prev: bool

# =============================================================================
# SEARCH MODELS
# =============================================================================

class SearchRequest(BaseModel):
    """Search request"""
    query: str = Field(..., min_length=1, max_length=1000)
    search_type: SearchType = SearchType.HYBRID
    limit: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.78, ge=0.0, le=1.0)
    filters: Dict[str, Any] = Field(default_factory=dict)
    include_content: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning algorithms",
                "search_type": "hybrid",
                "limit": 10,
                "similarity_threshold": 0.78,
                "filters": {"tags": ["ai", "technology"]},
                "include_content": True
            }
        }

class SearchResult(BaseModel):
    """Individual search result"""
    id: uuid.UUID
    note_id: uuid.UUID
    title: str
    chunk_text: Optional[str] = None
    content_preview: Optional[str] = None
    similarity_score: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchResponse(BaseModel):
    """Search response"""
    results: List[SearchResult]
    total_found: int
    query: str
    search_type: SearchType
    processing_time_ms: float
    used_cache: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "note_id": "660e8400-e29b-41d4-a716-446655440000",
                        "title": "Machine Learning Fundamentals",
                        "chunk_text": "Machine learning algorithms can be categorized into...",
                        "similarity_score": 0.92,
                        "relevance_score": 0.85,
                        "tags": ["ai", "ml", "algorithms"],
                        "created_at": "2023-12-01T10:00:00Z"
                    }
                ],
                "total_found": 15,
                "query": "machine learning algorithms",
                "search_type": "hybrid",
                "processing_time_ms": 125.5,
                "used_cache": False
            }
        }

# =============================================================================
# CONVERSATION MODELS
# =============================================================================

class ConversationCreate(BaseModel):
    """Create new conversation"""
    messages: List[MessageContent] = Field(default_factory=list)
    agents_involved: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None

class ConversationResponse(UUIDModel, TimestampedModel):
    """Conversation response model"""
    messages: List[MessageContent]
    agents_involved: List[str]
    session_id: Optional[str] = None

# =============================================================================
# ERROR MODELS
# =============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    status_code: int
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Validation error",
                "status_code": 422,
                "request_id": "req_123456",
                "timestamp": "2023-12-01T10:00:00Z",
                "details": {"field": "message", "issue": "Required field missing"}
            }
        }

# =============================================================================
# HEALTH MODELS
# =============================================================================

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    services: Dict[str, str] = Field(default_factory=dict)

class DetailedHealthCheck(HealthCheck):
    """Detailed health check with service status"""
    database: Dict[str, Any] = Field(default_factory=dict)
    cache: Dict[str, Any] = Field(default_factory=dict)
    external_apis: Dict[str, Any] = Field(default_factory=dict)
    performance: Dict[str, Any] = Field(default_factory=dict)