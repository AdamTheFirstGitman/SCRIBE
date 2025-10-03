"""
Conversations API endpoints
Manage conversations and messages
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from utils.logger import get_logger
from services.storage import supabase_client

logger = get_logger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


# Models
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


class CreateConversationRequest(BaseModel):
    title: Optional[str] = None
    first_message: Optional[str] = None


class CreateConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime


# Endpoints
@router.get("", response_model=ConversationsListResponse)
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    order_by: str = Query("updated_at", regex="^(created_at|updated_at|title)$")
):
    """List all user conversations with summary"""

    try:
        logger.info("Listing conversations", limit=limit, offset=offset, order_by=order_by)

        # Get conversations
        # Note: Supabase Python client doesn't support complex joins, so we'll do multiple queries
        query = supabase_client.client.table('conversations') \
            .select('*') \
            .eq('user_id', 'king_001') \
            .order(order_by, desc=(order_by != 'title')) \
            .range(offset, offset + limit - 1)

        result = query.execute()

        conversations = []
        for conv in result.data:
            # Get message count
            messages_query = supabase_client.client.table('messages') \
                .select('id', count='exact') \
                .eq('conversation_id', conv['id'])
            messages_result = messages_query.execute()
            message_count = messages_result.count or 0

            # Get associated notes from metadata
            metadata = conv.get('metadata', {})
            note_ids = metadata.get('note_ids', [])

            # Get note titles
            note_titles = []
            if note_ids:
                notes_query = supabase_client.client.table('notes') \
                    .select('title') \
                    .in_('id', note_ids)
                notes_result = notes_query.execute()
                note_titles = [n['title'] for n in notes_result.data]

            conversations.append(ConversationSummary(
                id=conv['id'],
                title=conv['title'],
                note_titles=note_titles,
                note_ids=note_ids,
                message_count=message_count,
                created_at=conv['created_at'],
                updated_at=conv['updated_at'],
                agents_involved=metadata.get('agents_involved', [])
            ))

        # Get total count
        count_result = supabase_client.client.table('conversations') \
            .select('id', count='exact') \
            .eq('user_id', 'king_001') \
            .execute()

        total = count_result.count or 0

        logger.info("Conversations listed successfully", total=total, returned=len(conversations))

        return ConversationsListResponse(
            conversations=conversations,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error("Failed to list conversations", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str):
    """Get full conversation with all messages"""

    try:
        logger.info("Getting conversation", conversation_id=conversation_id)

        # Get conversation
        conv_result = supabase_client.client.table('conversations') \
            .select('*') \
            .eq('id', conversation_id) \
            .eq('user_id', 'king_001') \
            .single() \
            .execute()

        if not conv_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conv = conv_result.data

        # Get all messages
        messages_result = supabase_client.client.table('messages') \
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

        logger.info("Conversation retrieved successfully",
                   conversation_id=conversation_id,
                   message_count=len(messages))

        return ConversationDetail(
            id=conv['id'],
            title=conv['title'],
            created_at=conv['created_at'],
            updated_at=conv['updated_at'],
            messages=messages,
            note_ids=conv.get('metadata', {}).get('note_ids', [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get conversation",
                    conversation_id=conversation_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.post("", response_model=CreateConversationResponse, status_code=201)
async def create_conversation(request: CreateConversationRequest):
    """Create new conversation"""

    try:
        # Auto-generate title if not provided
        title = request.title or f"Conversation du {datetime.now().strftime('%d/%m/%Y')}"

        logger.info("Creating conversation", title=title)

        # Create conversation
        conv_data = {
            'title': title,
            'user_id': 'king_001',
            'metadata': {
                'agents_involved': [],
                'note_ids': []
            }
        }

        result = supabase_client.client.table('conversations').insert(conv_data).execute()
        conv = result.data[0]

        # Add first message if provided
        if request.first_message:
            message_data = {
                'conversation_id': conv['id'],
                'role': 'user',
                'content': request.first_message,
                'metadata': {}
            }
            supabase_client.client.table('messages').insert(message_data).execute()
            logger.info("First message added to conversation", conversation_id=conv['id'])

        logger.info("Conversation created successfully", conversation_id=conv['id'])

        return CreateConversationResponse(
            id=conv['id'],
            title=conv['title'],
            created_at=conv['created_at']
        )

    except Exception as e:
        logger.error("Failed to create conversation", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete conversation and all messages"""

    try:
        logger.info("Deleting conversation", conversation_id=conversation_id)

        # Check ownership
        conv_result = supabase_client.client.table('conversations') \
            .select('id') \
            .eq('id', conversation_id) \
            .eq('user_id', 'king_001') \
            .single() \
            .execute()

        if not conv_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Delete messages (cascade should handle this, but explicit is better)
        supabase_client.client.table('messages') \
            .delete() \
            .eq('conversation_id', conversation_id) \
            .execute()

        # Delete conversation
        supabase_client.client.table('conversations') \
            .delete() \
            .eq('id', conversation_id) \
            .execute()

        logger.info("Conversation deleted successfully", conversation_id=conversation_id)

        return {"success": True, "message": "Conversation supprimée"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete conversation",
                    conversation_id=conversation_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")
