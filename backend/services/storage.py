"""
Supabase storage service for Plume & Mimir
Handles database operations and realtime subscriptions
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import asyncio

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from config import settings
from utils.logger import get_logger, performance_logger

logger = get_logger(__name__)

class SupabaseService:
    """Supabase database service"""

    def __init__(self):
        self.client: Optional[Client] = None
        self._initialized = False

    async def initialize(self):
        """Initialize Supabase client"""
        try:
            # Configure client options for better performance
            options = ClientOptions(
                auto_refresh_token=True,
                persist_session=True,
                storage_key="plume_mimir_session",
                realtime={"params": {"eventsPerSecond": 10}}
            )

            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY,
                options=options
            )

            # Test connection
            await self.test_connection()
            self._initialized = True
            logger.info("Supabase client initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Supabase client", error=str(e))
            raise

    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if not self.client:
                await self.initialize()

            # Simple test query
            result = self.client.table('notes').select('id').limit(1).execute()

            logger.debug("Database connection test successful")
            return True

        except Exception as e:
            logger.error("Database connection test failed", error=str(e))
            return False

    # =============================================================================
    # NOTE OPERATIONS
    # =============================================================================

    async def create_note(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new note"""
        try:
            result = self.client.table('notes').insert(note_data).execute()

            if result.data:
                note = result.data[0]
                logger.info("Note created", note_id=note['id'], title=note.get('title', '')[:50])
                return note
            else:
                raise Exception("Failed to create note: No data returned")

        except Exception as e:
            logger.error("Failed to create note", error=str(e), note_data=note_data)
            raise

    async def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """Get a note by ID"""
        try:
            result = self.client.table('notes').select('*').eq('id', note_id).eq('is_deleted', False).single().execute()

            if result.data:
                logger.debug("Note retrieved", note_id=note_id)
                return result.data
            else:
                logger.warning("Note not found", note_id=note_id)
                return None

        except Exception as e:
            logger.error("Failed to retrieve note", note_id=note_id, error=str(e))
            raise

    async def update_note(self, note_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a note"""
        try:
            # Add updated_at timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()

            result = self.client.table('notes').update(update_data).eq('id', note_id).eq('is_deleted', False).execute()

            if result.data:
                note = result.data[0]
                logger.info("Note updated", note_id=note_id, title=note.get('title', '')[:50])
                return note
            else:
                logger.warning("Note not found for update", note_id=note_id)
                return None

        except Exception as e:
            logger.error("Failed to update note", note_id=note_id, error=str(e))
            raise

    async def delete_note(self, note_id: str, soft_delete: bool = True) -> bool:
        """Delete a note (soft delete by default)"""
        try:
            if soft_delete:
                result = self.client.table('notes').update({
                    'is_deleted': True,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', note_id).execute()
            else:
                result = self.client.table('notes').delete().eq('id', note_id).execute()

            if result.data:
                logger.info("Note deleted", note_id=note_id, soft_delete=soft_delete)
                return True
            else:
                logger.warning("Note not found for deletion", note_id=note_id)
                return False

        except Exception as e:
            logger.error("Failed to delete note", note_id=note_id, error=str(e))
            raise

    async def list_notes(
        self,
        limit: int = 20,
        offset: int = 0,
        search_query: Optional[str] = None,
        tags_filter: Optional[List[str]] = None,
        order_by: str = 'created_at',
        order_direction: str = 'desc'
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List notes with pagination and filters"""
        try:
            query = self.client.table('notes').select('*', count='exact').eq('is_deleted', False)

            # Apply search filter
            if search_query:
                # Use full-text search
                query = query.text_search('title,content', f"'{search_query}'", type_='websearch', config='french')

            # Apply tags filter
            if tags_filter:
                query = query.overlaps('tags', tags_filter)

            # Apply ordering
            if order_direction.lower() == 'desc':
                query = query.order(order_by, desc=True)
            else:
                query = query.order(order_by, desc=False)

            # Apply pagination
            query = query.range(offset, offset + limit - 1)

            result = query.execute()

            notes = result.data or []
            total = result.count or 0

            logger.debug("Notes listed", count=len(notes), total=total, search_query=search_query)
            return notes, total

        except Exception as e:
            logger.error("Failed to list notes", error=str(e))
            raise

    async def duplicate_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """Duplicate an existing note"""
        try:
            # Get original note
            original = await self.get_note(note_id)
            if not original:
                return None

            # Create duplicate
            duplicate_data = {
                'title': f"{original['title']} (Copy)",
                'content': original['content'],
                'html': original.get('html'),
                'tags': original.get('tags', []),
                'metadata': {
                    **original.get('metadata', {}),
                    'duplicated_from': note_id,
                    'duplicated_at': datetime.utcnow().isoformat()
                }
            }

            return await self.create_note(duplicate_data)

        except Exception as e:
            logger.error("Failed to duplicate note", note_id=note_id, error=str(e))
            raise

    # =============================================================================
    # EMBEDDING OPERATIONS
    # =============================================================================

    async def create_embeddings(self, embeddings_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple embeddings"""
        try:
            result = self.client.table('embeddings').insert(embeddings_data).execute()

            if result.data:
                logger.info("Embeddings created", count=len(result.data))
                return result.data
            else:
                raise Exception("Failed to create embeddings: No data returned")

        except Exception as e:
            logger.error("Failed to create embeddings", error=str(e))
            raise

    async def delete_embeddings_for_note(self, note_id: str) -> bool:
        """Delete all embeddings for a note"""
        try:
            result = self.client.table('embeddings').delete().eq('note_id', note_id).execute()

            logger.info("Embeddings deleted for note", note_id=note_id)
            return True

        except Exception as e:
            logger.error("Failed to delete embeddings", note_id=note_id, error=str(e))
            raise

    # =============================================================================
    # CONVERSATION OPERATIONS
    # =============================================================================

    async def create_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new conversation"""
        try:
            result = self.client.table('conversations').insert(conversation_data).execute()

            if result.data:
                conversation = result.data[0]
                logger.info("Conversation created", conversation_id=conversation['id'])
                return conversation
            else:
                raise Exception("Failed to create conversation: No data returned")

        except Exception as e:
            logger.error("Failed to create conversation", error=str(e))
            raise

    async def update_conversation(self, conversation_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a conversation"""
        try:
            update_data['updated_at'] = datetime.utcnow().isoformat()

            result = self.client.table('conversations').update(update_data).eq('id', conversation_id).execute()

            if result.data:
                conversation = result.data[0]
                logger.info("Conversation updated", conversation_id=conversation_id)
                return conversation
            else:
                logger.warning("Conversation not found for update", conversation_id=conversation_id)
                return None

        except Exception as e:
            logger.error("Failed to update conversation", conversation_id=conversation_id, error=str(e))
            raise

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID"""
        try:
            result = self.client.table('conversations').select('*').eq('id', conversation_id).single().execute()

            if result.data:
                logger.debug("Conversation retrieved", conversation_id=conversation_id)
                return result.data
            else:
                logger.warning("Conversation not found", conversation_id=conversation_id)
                return None

        except Exception as e:
            logger.error("Failed to retrieve conversation", conversation_id=conversation_id, error=str(e))
            raise

    async def get_conversations_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a session"""
        try:
            result = self.client.table('conversations').select('*').eq('session_id', session_id).order('created_at', desc=True).execute()

            conversations = result.data or []
            logger.debug("Conversations retrieved for session", session_id=session_id, count=len(conversations))
            return conversations

        except Exception as e:
            logger.error("Failed to retrieve conversations by session", session_id=session_id, error=str(e))
            raise

    # =============================================================================
    # SEARCH OPERATIONS (RPC Functions)
    # =============================================================================

    async def vector_search(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.78,
        match_count: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        try:
            start_time = datetime.utcnow()

            result = self.client.rpc('match_documents', {
                'query_embedding': query_embedding,
                'match_threshold': match_threshold,
                'match_count': match_count
            }).execute()

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            performance_logger.log_database_query("vector_search", processing_time)

            results = result.data or []
            logger.debug("Vector search completed", results_count=len(results), processing_time_ms=processing_time)
            return results

        except Exception as e:
            logger.error("Vector search failed", error=str(e))
            raise

    async def hybrid_search(
        self,
        query_text: str,
        query_embedding: Optional[List[float]] = None,
        match_threshold: float = 0.78,
        match_count: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search (vector + full-text)"""
        try:
            start_time = datetime.utcnow()

            params = {
                'query_text': query_text,
                'match_threshold': match_threshold,
                'match_count': match_count
            }

            if query_embedding:
                params['query_embedding'] = query_embedding

            result = self.client.rpc('hybrid_search', params).execute()

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            performance_logger.log_database_query("hybrid_search", processing_time)

            results = result.data or []
            logger.debug("Hybrid search completed", results_count=len(results), processing_time_ms=processing_time)
            return results

        except Exception as e:
            logger.error("Hybrid search failed", error=str(e))
            raise

    # =============================================================================
    # ANALYTICS & MONITORING
    # =============================================================================

    async def log_search_query(self, query: str, results_count: int, execution_time_ms: int):
        """Log search query for analytics"""
        try:
            search_data = {
                'query': query,
                'results_count': results_count,
                'execution_time_ms': execution_time_ms
            }

            self.client.table('search_queries').insert(search_data).execute()
            logger.debug("Search query logged for analytics")

        except Exception as e:
            # Don't fail the main operation if analytics logging fails
            logger.warning("Failed to log search query", error=str(e))

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        try:
            result = self.client.table('performance_stats').select('*').execute()

            stats = {}
            if result.data:
                for row in result.data:
                    stats[row['table_name']] = {
                        'row_count': row['row_count'],
                        'size': row['size']
                    }

            logger.debug("Performance stats retrieved", tables=len(stats))
            return stats

        except Exception as e:
            logger.error("Failed to retrieve performance stats", error=str(e))
            return {}

# Global instance
supabase_client = SupabaseService()