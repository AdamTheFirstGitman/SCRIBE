"""
File Upload API Endpoints
Handles document upload and processing for SCRIBE system
Includes text and audio upload for note creation
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
from pathlib import Path
import asyncio
from datetime import datetime
import tempfile
import os

from services.document_processor import DocumentProcessor
from services.embedding_service import EmbeddingService
from services.storage import supabase_client
from models.document import DocumentResponse, DocumentCreate, ProcessingStatus
from services.storage import supabase_client
from services.transcription import TranscriptionService
from agents.orchestrator import PlumeOrchestrator
from utils.logger import get_logger

logger = get_logger(__name__)

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
    # Removed dependency - use global supabase_client
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
    # Removed dependency - use global supabase_client
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
    # Removed dependency - use global supabase_client
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
    # Removed dependency - use global supabase_client
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
        supabase = supabase_client

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

# =============================================================================
# PHASE 2.2: TEXT AND AUDIO UPLOAD ENDPOINTS
# =============================================================================

# Models for Phase 2.2
class UploadTextRequest(BaseModel):
    text: str
    context: Optional[str] = None


class UploadResponse(BaseModel):
    note_id: str
    title: str
    created_at: datetime


class UploadAudioResponse(BaseModel):
    note_id: str
    title: str
    transcription: str
    created_at: datetime
    agent_response: str


@router.post("/text", response_model=UploadResponse, status_code=201)
async def upload_text(request: UploadTextRequest):
    """Create note from text"""

    try:
        logger.info("Creating note from text", text_length=len(request.text))

        # Generate title from first line or first 50 chars
        title = request.text.split('\n')[0][:50]
        if len(title) == 50:
            title += '...'
        if not title.strip():
            title = "Nouvelle note"

        # Create note
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

        result = supabase_client.client.table('notes').insert(note_data).execute()
        note = result.data[0]

        # Index for RAG search (background)
        try:
            from services.embeddings import embed_and_store
            asyncio.create_task(embed_and_store(note['id'], request.text))
        except ImportError:
            logger.warning("Embeddings service not available for indexing")

        logger.info("Note created successfully", note_id=note['id'], title=note['title'])

        return UploadResponse(
            note_id=note['id'],
            title=note['title'],
            created_at=note['created_at']
        )

    except Exception as e:
        logger.error("Failed to create note from text", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create note: {str(e)}"
        )


@router.post("/audio", response_model=UploadAudioResponse, status_code=201)
async def upload_audio(
    fastapi_request: Request,
    audio_file: UploadFile = File(..., description="Audio file principal"),
    context_text: Optional[str] = Form(None),
    context_audio: Optional[UploadFile] = File(None)
):
    """Upload audio, transcribe, and let agents create structured note"""

    # Validate main audio file type
    allowed_types = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/webm', 'audio/ogg', 'audio/x-m4a']
    if audio_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporté. Formats acceptés : mp3, wav, m4a, webm, ogg"
        )

    transcription_service = TranscriptionService()
    temp_files = []

    try:
        logger.info("Processing audio upload", filename=audio_file.filename)

        # 1. Transcribe main audio
        temp_audio = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(audio_file.filename)[1]
        )
        temp_files.append(temp_audio.name)

        content = await audio_file.read()
        temp_audio.write(content)
        temp_audio.close()

        # Call transcription service (it expects file path)
        # We need to adapt since the service expects base64 encoded data
        # Let's create a wrapper method or read as base64
        import base64
        with open(temp_audio.name, 'rb') as f:
            audio_bytes = f.read()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Get file extension for format
        file_ext = os.path.splitext(audio_file.filename)[1].lstrip('.')

        main_transcription_result = await transcription_service.transcribe_audio(
            audio_data=audio_base64,
            format=file_ext or 'mp3',
            language='fr'
        )
        main_transcription = main_transcription_result['text']

        logger.info("Main audio transcribed", length=len(main_transcription))

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

            # Convert to base64
            with open(temp_context.name, 'rb') as f:
                context_audio_bytes = f.read()
            context_audio_base64 = base64.b64encode(context_audio_bytes).decode('utf-8')

            context_ext = os.path.splitext(context_audio.filename)[1].lstrip('.')

            context_transcription_result = await transcription_service.transcribe_audio(
                audio_data=context_audio_base64,
                format=context_ext or 'mp3',
                language='fr'
            )
            context_content = context_transcription_result['text']

            logger.info("Context audio transcribed", length=len(context_content))

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
        note_id = result.get("note_id")

        if not note_id:
            # Fallback: create note manually if agents didn't
            logger.warning("Agents did not create note, creating manually")
            supabase = supabase_client
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
            note_result = supabase.client.table('notes').insert(note_data).execute()
            note_id = note_result.data[0]['id']

        logger.info("Audio upload processed successfully", note_id=note_id)

        return UploadAudioResponse(
            note_id=note_id,
            title=result.get("title", "Note créée"),
            transcription=main_transcription,
            created_at=datetime.now(),
            agent_response=result["response"]
        )

    except Exception as e:
        logger.error("Audio upload failed", error=str(e))
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