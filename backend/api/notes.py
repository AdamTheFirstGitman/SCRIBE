"""
Notes API endpoints
Manage notes with search, retrieval, and HTML conversion
"""

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from utils.logger import get_logger
from services.storage import supabase_client

logger = get_logger(__name__)

router = APIRouter(prefix="/notes", tags=["notes"])


# Models
class Note(BaseModel):
    id: str
    title: str
    text_content: str
    html_content: Optional[str] = None  # Can be null in DB
    created_at: datetime
    updated_at: datetime


class NotesListResponse(BaseModel):
    notes: List[Note]


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


class ConvertHTMLResponse(BaseModel):
    status: str
    note_id: str
    message: str


# Helper functions
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


async def process_html_conversion(note_id: str, text_content: str):
    """Background task to convert text to HTML"""

    try:
        logger.info("Starting HTML conversion", note_id=note_id)

        # Use existing text-to-html service if available, otherwise simple conversion
        try:
            from services.text_to_html import convert_text_to_html
            html_content = await convert_text_to_html(text_content)
        except ImportError:
            # Fallback: simple paragraph-based conversion
            html_content = convert_text_to_simple_html(text_content)

        # Update note in database
        supabase_client.client.table('notes') \
            .update({
                'html_content': html_content,
                'updated_at': datetime.now().isoformat()
            }) \
            .eq('id', note_id) \
            .execute()

        logger.info("HTML conversion completed", note_id=note_id)

    except Exception as e:
        logger.error("HTML conversion failed", note_id=note_id, error=str(e))


def convert_text_to_simple_html(text: str) -> str:
    """Simple text to HTML conversion fallback"""
    paragraphs = text.split('\n\n')
    html_paragraphs = [f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()]
    return '\n'.join(html_paragraphs)


# Endpoints
@router.get("/recent", response_model=NotesListResponse)
async def get_recent_notes():
    """Get 5 most recent notes"""

    try:
        logger.info("Getting recent notes")

        result = supabase_client.client.table('notes') \
            .select('*') \
            .eq('user_id', 'king_001') \
            .order('updated_at', desc=True) \
            .limit(5) \
            .execute()

        notes = [Note(**note) for note in result.data]

        logger.info("Recent notes retrieved", count=len(notes))

        return NotesListResponse(notes=notes)

    except Exception as e:
        logger.error("Failed to get recent notes", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get recent notes: {str(e)}")


@router.get("/search", response_model=SearchResponse)
async def search_notes(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100)
):
    """Fulltext search in notes"""

    try:
        logger.info("Searching notes", query=q, limit=limit)

        # Try using PostgreSQL fulltext search function first
        try:
            result = supabase_client.client.rpc('search_notes_fulltext', {
                'search_query': q,
                'user_id_param': 'king_001',
                'limit_param': limit
            }).execute()

            if result.data:
                logger.info("Using fulltext search function")
                results = []
                for note in result.data:
                    snippet = generate_snippet(note['text_content'], q, max_length=150)
                    results.append(SearchResult(
                        id=note['id'],
                        title=note['title'],
                        snippet=snippet,
                        created_at=note['created_at'],
                        updated_at=note['updated_at'],
                        relevance_score=note.get('relevance_score', 0.5)
                    ))

                return SearchResponse(results=results, total=len(results))

        except Exception as rpc_error:
            logger.warning("Fulltext search function not available, using fallback",
                         error=str(rpc_error))

        # Fallback to ILIKE (less performant but works without SQL function)
        result = supabase_client.client.table('notes') \
            .select('*') \
            .eq('user_id', 'king_001') \
            .or_(f'title.ilike.%{q}%,text_content.ilike.%{q}%') \
            .limit(limit) \
            .execute()

        results = []
        for note in result.data:
            snippet = generate_snippet(note['text_content'], q, max_length=150)
            results.append(SearchResult(
                id=note['id'],
                title=note['title'],
                snippet=snippet,
                created_at=note['created_at'],
                updated_at=note['updated_at'],
                relevance_score=0.5  # Default score for ILIKE search
            ))

        logger.info("Search completed", query=q, results_count=len(results))

        return SearchResponse(results=results, total=len(results))

    except Exception as e:
        logger.error("Search failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/{note_id}", response_model=Note)
async def get_note(note_id: str):
    """Get specific note"""

    try:
        logger.info("Getting note", note_id=note_id)

        result = supabase_client.client.table('notes') \
            .select('*') \
            .eq('id', note_id) \
            .eq('user_id', 'king_001') \
            .single() \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Note not found")

        logger.info("Note retrieved successfully", note_id=note_id)

        return Note(**result.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get note", note_id=note_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get note: {str(e)}")


@router.post("/{note_id}/convert-html", response_model=ConvertHTMLResponse, status_code=202)
async def convert_note_to_html(note_id: str, background_tasks: BackgroundTasks):
    """Convert note text to HTML (async)"""

    try:
        logger.info("Requesting HTML conversion", note_id=note_id)

        # Check note exists
        note_result = supabase_client.client.table('notes') \
            .select('id, text_content') \
            .eq('id', note_id) \
            .eq('user_id', 'king_001') \
            .single() \
            .execute()

        if not note_result.data:
            raise HTTPException(status_code=404, detail="Note not found")

        # Launch background task
        background_tasks.add_task(
            process_html_conversion,
            note_id,
            note_result.data['text_content']
        )

        logger.info("HTML conversion task scheduled", note_id=note_id)

        return ConvertHTMLResponse(
            status="processing",
            note_id=note_id,
            message="Conversion HTML en cours..."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to schedule HTML conversion", note_id=note_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule HTML conversion: {str(e)}"
        )
