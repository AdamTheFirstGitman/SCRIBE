"""
Document Models
Pydantic models for document handling in SCRIBE system
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class ProcessingStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentCreate(BaseModel):
    """Model for creating a new document"""
    filename: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    content_text: str = Field(..., min_length=1)
    content_html: str = Field(..., min_length=1)
    file_type: str = Field(default="text/plain")
    file_size: Optional[int] = Field(default=None, ge=0)
    upload_source: str = Field(default="manual")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "hackathon_notes.txt",
                "title": "Hackathon Notes - AI & Machine Learning",
                "content_text": "Hackathon Vierzon\nCursor\nv0.dev\n\nHackathon LLMxLaw...",
                "content_html": "<article><h2>Hackathon Vierzon</h2><ul><li>Cursor</li>...</article>",
                "file_type": "text/plain",
                "file_size": 2048,
                "tags": ["hackathon", "AI", "notes"],
                "metadata": {
                    "word_count": 150,
                    "has_links": True,
                    "topics": ["AI", "LLM", "Hackathon"]
                }
            }
        }

class DocumentResponse(BaseModel):
    """Model for document responses"""
    id: str = Field(..., description="Unique document identifier")
    filename: str
    title: str
    content_text: str
    content_html: str
    file_type: str
    file_size: Optional[int] = None
    processing_status: ProcessingStatus
    upload_source: str = Field(default="manual")
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_deleted: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "hackathon_notes.txt",
                "title": "Hackathon Notes - AI & Machine Learning",
                "content_text": "Hackathon Vierzon\nCursor\nv0.dev...",
                "content_html": "<article><h2>Hackathon Vierzon</h2>...",
                "file_type": "text/plain",
                "file_size": 2048,
                "processing_status": "completed",
                "created_at": "2024-01-15T10:30:00Z",
                "tags": ["hackathon", "AI", "notes"],
                "metadata": {
                    "word_count": 150,
                    "char_count": 1024,
                    "has_links": True,
                    "topics": ["AI", "LLM", "Hackathon"]
                }
            }
        }

class DocumentPreview(BaseModel):
    """Lightweight document preview model"""
    id: str
    filename: str
    title: str
    file_type: str
    file_size: Optional[int] = None
    processing_status: ProcessingStatus
    created_at: datetime
    tags: List[str] = Field(default_factory=list)
    word_count: Optional[int] = None
    has_links: bool = False
    has_structure: bool = False

    @classmethod
    def from_document(cls, doc: DocumentResponse) -> "DocumentPreview":
        """Create preview from full document"""
        return cls(
            id=doc.id,
            filename=doc.filename,
            title=doc.title,
            file_type=doc.file_type,
            file_size=doc.file_size,
            processing_status=doc.processing_status,
            created_at=doc.created_at,
            tags=doc.tags,
            word_count=doc.metadata.get("word_count"),
            has_links=doc.metadata.get("has_links", False),
            has_structure=doc.metadata.get("has_structure", False)
        )

class DocumentUpdate(BaseModel):
    """Model for updating document metadata"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ChunkData(BaseModel):
    """Model for document chunks"""
    index: int = Field(..., ge=0)
    text: str = Field(..., min_length=1)
    char_count: int = Field(..., ge=0)
    word_count: int = Field(..., ge=0)
    embedding: Optional[List[float]] = None

class EmbeddingData(BaseModel):
    """Model for embedding data"""
    id: str
    document_id: str
    note_id: Optional[str] = None
    chunk_text: str
    embedding: List[float]
    chunk_index: int
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

class UploadStats(BaseModel):
    """Model for upload statistics"""
    total_documents: int
    total_size_bytes: int
    total_size_mb: float
    by_file_type: Dict[str, int]
    by_processing_status: Dict[ProcessingStatus, int]
    recent_uploads: List[DocumentPreview]
    average_file_size: Optional[float] = None

    @classmethod
    def calculate_stats(cls, documents: List[DocumentResponse]) -> "UploadStats":
        """Calculate statistics from document list"""
        if not documents:
            return cls(
                total_documents=0,
                total_size_bytes=0,
                total_size_mb=0.0,
                by_file_type={},
                by_processing_status={},
                recent_uploads=[]
            )

        total_size = sum(doc.file_size or 0 for doc in documents)

        # Count by file type
        by_file_type = {}
        for doc in documents:
            by_file_type[doc.file_type] = by_file_type.get(doc.file_type, 0) + 1

        # Count by status
        by_processing_status = {}
        for doc in documents:
            status = doc.processing_status
            by_processing_status[status] = by_processing_status.get(status, 0) + 1

        # Recent uploads (last 5)
        recent = sorted(documents, key=lambda x: x.created_at, reverse=True)[:5]
        recent_previews = [DocumentPreview.from_document(doc) for doc in recent]

        return cls(
            total_documents=len(documents),
            total_size_bytes=total_size,
            total_size_mb=round(total_size / (1024 * 1024), 2),
            by_file_type=by_file_type,
            by_processing_status=by_processing_status,
            recent_uploads=recent_previews,
            average_file_size=round(total_size / len(documents), 2) if documents else 0
        )

# Utility functions for validation
def validate_document_id(document_id: str) -> bool:
    """Validate document UUID format"""
    try:
        uuid.UUID(document_id)
        return True
    except ValueError:
        return False

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for storage"""
    import re
    # Remove or replace unsafe characters
    safe_name = re.sub(r'[^\w\-_\.]', '_', filename)
    # Limit length
    if len(safe_name) > 255:
        name_part = safe_name[:240]
        ext_part = safe_name[-10:] if '.' in safe_name[-10:] else ''
        safe_name = name_part + ext_part
    return safe_name

def extract_file_info(filename: str, content: str) -> Dict[str, Any]:
    """Extract basic file information"""
    from pathlib import Path

    file_path = Path(filename)

    return {
        "extension": file_path.suffix.lower(),
        "stem": file_path.stem,
        "size_bytes": len(content.encode('utf-8')),
        "line_count": len(content.split('\n')),
        "word_count": len(content.split()),
        "char_count": len(content)
    }