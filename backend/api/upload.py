"""
File Upload API Endpoints
Handles document upload and processing for SCRIBE system
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from typing import Optional, List
import uuid
from pathlib import Path
import asyncio
from datetime import datetime

from ..services.document_processor import DocumentProcessor
from ..services.embedding_service import EmbeddingService
from ..database.supabase_client import get_supabase_client
from ..models.document import DocumentResponse, DocumentCreate, ProcessingStatus

router = APIRouter(prefix="/upload", tags=["upload"])

# Initialize services
document_processor = DocumentProcessor()
embedding_service = EmbeddingService()

ALLOWED_FILE_TYPES = {
    "text/plain": [".txt", ".text"],
    "text/markdown": [".md", ".markdown"],
    "application/json": [".json"],
    # Future: PDF, DOCX support
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/document", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated
    supabase = Depends(get_supabase_client)
):
    """
    Upload and process a text document

    - Validates file type and size
    - Converts text to HTML
    - Generates embeddings for RAG
    - Stores in database
    """

    try:
        # Validate file
        await _validate_upload(file)

        # Read content
        content = await file.read()
        text_content = content.decode('utf-8')

        # Process document
        processed = document_processor.process_document(
            content=text_content,
            filename=file.filename,
            file_type=file.content_type or "text/plain"
        )

        # Override title if provided
        if title:
            processed["title"] = title

        # Parse tags
        document_tags = []
        if tags:
            document_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
        processed["tags"] = document_tags

        # Store in database
        document_id = await _store_document(supabase, processed)

        # Generate embeddings asynchronously
        asyncio.create_task(_generate_embeddings_async(document_id, processed["chunks"]))

        # Return response
        return DocumentResponse(
            id=document_id,
            title=processed["title"],
            filename=processed["filename"],
            content_text=processed["content_text"],
            content_html=processed["content_html"],
            file_type=processed["file_type"],
            file_size=processed["file_size"],
            processing_status=ProcessingStatus.COMPLETED,
            created_at=datetime.now(),
            metadata=processed["metadata"],
            tags=processed["tags"]
        )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be valid UTF-8 text"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

@router.get("/document/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    supabase = Depends(get_supabase_client)
):
    """Retrieve a processed document by ID"""

    try:
        # Query document
        result = supabase.table("documents").select("*").eq("id", document_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = result.data[0]

        return DocumentResponse(
            id=doc["id"],
            title=doc["title"],
            filename=doc["filename"],
            content_text=doc["content_text"],
            content_html=doc["content_html"],
            file_type=doc["file_type"],
            file_size=doc["file_size"],
            processing_status=ProcessingStatus(doc["processing_status"]),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            metadata=doc["metadata"],
            tags=doc["tags"] or []
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document: {str(e)}"
        )

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    tag: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """List all uploaded documents with optional filtering"""

    try:
        query = supabase.table("documents").select("*").eq("is_deleted", False)

        # Filter by tag if provided
        if tag:
            query = query.contains("tags", [tag])

        # Apply pagination
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        documents = []
        for doc in result.data:
            documents.append(DocumentResponse(
                id=doc["id"],
                title=doc["title"],
                filename=doc["filename"],
                content_text=doc["content_text"],
                content_html=doc["content_html"],
                file_type=doc["file_type"],
                file_size=doc["file_size"],
                processing_status=ProcessingStatus(doc["processing_status"]),
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
                metadata=doc["metadata"],
                tags=doc["tags"] or []
            ))

        return documents

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )

@router.delete("/document/{document_id}")
async def delete_document(
    document_id: str,
    supabase = Depends(get_supabase_client)
):
    """Soft delete a document"""

    try:
        # Mark as deleted
        result = supabase.table("documents").update({
            "is_deleted": True,
            "updated_at": datetime.now().isoformat()
        }).eq("id", document_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"message": "Document deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )

async def _validate_upload(file: UploadFile):
    """Validate uploaded file"""

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset

    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Check file type
    file_ext = Path(file.filename).suffix.lower()
    content_type = file.content_type or "text/plain"

    allowed = False
    for mime_type, extensions in ALLOWED_FILE_TYPES.items():
        if content_type == mime_type or file_ext in extensions:
            allowed = True
            break

    if not allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {list(ALLOWED_FILE_TYPES.keys())}"
        )

async def _store_document(supabase, processed_data: dict) -> str:
    """Store processed document in database"""

    document_id = str(uuid.uuid4())

    document_data = {
        "id": document_id,
        "filename": processed_data["filename"],
        "title": processed_data["title"],
        "content_text": processed_data["content_text"],
        "content_html": processed_data["content_html"],
        "file_type": processed_data["file_type"],
        "file_size": processed_data["file_size"],
        "processing_status": processed_data["processing_status"],
        "metadata": processed_data["metadata"],
        "tags": processed_data.get("tags", []),
        "upload_source": "manual",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    result = supabase.table("documents").insert(document_data).execute()

    if not result.data:
        raise Exception("Failed to store document in database")

    return document_id

async def _generate_embeddings_async(document_id: str, chunks: List[dict]):
    """Generate embeddings for document chunks asynchronously"""

    try:
        supabase = get_supabase_client()

        # Update status to processing
        supabase.table("documents").update({
            "processing_status": "processing"
        }).eq("id", document_id).execute()

        # Generate embeddings for each chunk
        embeddings_data = []

        for chunk in chunks:
            # Generate embedding
            embedding = await embedding_service.generate_embedding(chunk["text"])

            embeddings_data.append({
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "chunk_text": chunk["text"],
                "embedding": embedding,
                "chunk_index": chunk["index"],
                "chunk_metadata": {
                    "char_count": chunk["char_count"],
                    "word_count": chunk["word_count"]
                },
                "created_at": datetime.now().isoformat()
            })

        # Bulk insert embeddings
        if embeddings_data:
            supabase.table("embeddings").insert(embeddings_data).execute()

        # Update status to completed
        supabase.table("documents").update({
            "processing_status": "completed"
        }).eq("id", document_id).execute()

    except Exception as e:
        # Mark as failed
        supabase.table("documents").update({
            "processing_status": "failed",
            "metadata": {"error": str(e)}
        }).eq("id", document_id).execute()

        print(f"Embedding generation failed for document {document_id}: {e}")

# Health check endpoint
@router.get("/health")
async def upload_health():
    """Health check for upload service"""
    return {
        "status": "healthy",
        "service": "document_upload",
        "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024,
        "supported_formats": list(ALLOWED_FILE_TYPES.keys())
    }