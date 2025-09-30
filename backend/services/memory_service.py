"""
Conversation Memory Service
Manages short-term and long-term conversation memory
Provides context-aware conversation history and user preferences
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from services.storage import supabase_client
from services.embeddings import embedding_service
from services.rag import rag_service
from utils.logger import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    """
    Manages conversation memory with short-term and long-term strategies

    Features:
    - Short-term: Recent messages in conversation
    - Long-term: RAG search on conversation history
    - User preferences: Topics, preferred agents, interaction patterns
    """

    def __init__(
        self,
        short_term_limit: int = 10,
        long_term_search_limit: int = 5,
        similarity_threshold: float = 0.75
    ):
        """
        Initialize conversation memory

        Args:
            short_term_limit: Number of recent messages to keep
            long_term_search_limit: Number of similar past conversations to retrieve
            similarity_threshold: Minimum similarity for long-term retrieval
        """
        self.short_term_limit = short_term_limit
        self.long_term_search_limit = long_term_search_limit
        self.similarity_threshold = similarity_threshold

        logger.info(
            "Conversation memory initialized",
            short_term_limit=short_term_limit,
            long_term_search_limit=long_term_search_limit
        )

    async def get_conversation_context(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        include_long_term: bool = True
    ) -> Dict[str, Any]:
        """
        Get complete conversation context (short + long term + preferences)

        Args:
            conversation_id: Current conversation ID
            user_id: User ID for preferences and long-term memory
            include_long_term: Whether to include similar past conversations

        Returns:
            {
                "recent_messages": [...],
                "similar_past_conversations": [...],
                "user_preferences": {...},
                "conversation_summary": str
            }
        """

        try:
            logger.info("Retrieving conversation context", conversation_id=conversation_id)

            # Get short-term memory (recent messages)
            recent_messages = await self.get_recent_messages(
                conversation_id=conversation_id,
                limit=self.short_term_limit
            )

            context = {
                "recent_messages": recent_messages,
                "similar_past_conversations": [],
                "user_preferences": {},
                "conversation_summary": ""
            }

            # Extract current topic from recent messages
            current_topic = self._extract_topic(recent_messages)
            context["conversation_summary"] = current_topic

            # Get user preferences if user_id provided
            if user_id:
                preferences = await self.get_user_preferences(user_id)
                context["user_preferences"] = preferences

                # Get long-term memory if requested
                if include_long_term and current_topic:
                    similar_past = await self.search_conversation_history(
                        user_id=user_id,
                        query=current_topic,
                        limit=self.long_term_search_limit,
                        exclude_conversation_id=conversation_id
                    )
                    context["similar_past_conversations"] = similar_past

            logger.info(
                "Conversation context retrieved",
                recent_messages_count=len(recent_messages),
                similar_past_count=len(context["similar_past_conversations"])
            )

            return context

        except Exception as e:
            logger.error("Failed to retrieve conversation context", error=str(e))
            return {
                "recent_messages": [],
                "similar_past_conversations": [],
                "user_preferences": {},
                "conversation_summary": ""
            }

    async def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages from a conversation (short-term memory)

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries
        """

        try:
            # Query messages table ordered by timestamp
            response = await supabase_client.client.table("messages").select(
                "id, role, content, metadata, created_at"
            ).eq("conversation_id", conversation_id).order(
                "created_at", desc=True
            ).limit(limit).execute()

            messages = response.data if response.data else []

            # Reverse to get chronological order (oldest to newest)
            messages.reverse()

            logger.info(
                "Retrieved recent messages",
                conversation_id=conversation_id,
                count=len(messages)
            )

            return messages

        except Exception as e:
            logger.error(
                "Failed to retrieve recent messages",
                conversation_id=conversation_id,
                error=str(e)
            )
            return []

    async def search_conversation_history(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        exclude_conversation_id: Optional[str] = None,
        time_window_days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Search similar past conversations using RAG (long-term memory)

        Args:
            user_id: User ID
            query: Search query (typically current topic)
            limit: Maximum results to return
            exclude_conversation_id: Exclude current conversation
            time_window_days: Only search conversations within this time window

        Returns:
            List of similar past conversation excerpts
        """

        try:
            # Calculate time window
            cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)

            # Get query embedding
            query_embedding = await embedding_service.get_embedding(query)

            # Search messages with embeddings (using pgvector similarity)
            # NOTE: This requires messages.embedding column (see migration)
            query = f"""
                SELECT
                    m.id,
                    m.conversation_id,
                    m.role,
                    m.content,
                    m.created_at,
                    c.title as conversation_title,
                    1 - (m.embedding <=> $1::vector) as similarity
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE
                    c.user_id = $2
                    AND m.created_at > $3
                    {f"AND m.conversation_id != $4" if exclude_conversation_id else ""}
                    AND m.embedding IS NOT NULL
                ORDER BY m.embedding <=> $1::vector
                LIMIT $5
            """

            params = [
                str(query_embedding),
                user_id,
                cutoff_date.isoformat(),
            ]

            if exclude_conversation_id:
                params.append(exclude_conversation_id)

            params.append(limit)

            # Execute raw SQL query
            response = await supabase_client.client.rpc(
                "search_similar_messages",
                {
                    "query_embedding": query_embedding,
                    "p_user_id": user_id,
                    "p_cutoff_date": cutoff_date.isoformat(),
                    "p_exclude_conversation_id": exclude_conversation_id,
                    "p_limit": limit
                }
            ).execute()

            results = response.data if response.data else []

            logger.info(
                "Searched conversation history",
                user_id=user_id,
                query_length=len(query),
                results_found=len(results)
            )

            return results

        except Exception as e:
            logger.error(
                "Failed to search conversation history",
                user_id=user_id,
                error=str(e)
            )
            return []

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences and interaction patterns

        Args:
            user_id: User ID

        Returns:
            User preferences dictionary
        """

        try:
            # Query user_preferences table
            response = await supabase_client.client.table("user_preferences").select(
                "*"
            ).eq("user_id", user_id).single().execute()

            if response.data:
                preferences = response.data

                logger.info("Retrieved user preferences", user_id=user_id)
                return preferences
            else:
                # Create default preferences
                default_preferences = {
                    "user_id": user_id,
                    "preferred_agent": "auto",
                    "topics_of_interest": [],
                    "interaction_patterns": {},
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }

                # Insert default preferences
                await supabase_client.client.table("user_preferences").insert(
                    default_preferences
                ).execute()

                logger.info("Created default user preferences", user_id=user_id)
                return default_preferences

        except Exception as e:
            logger.error("Failed to retrieve user preferences", user_id=user_id, error=str(e))
            return {
                "preferred_agent": "auto",
                "topics_of_interest": [],
                "interaction_patterns": {}
            }

    async def update_user_preferences(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update user preferences

        Args:
            user_id: User ID
            updates: Dictionary of preference updates

        Returns:
            Success boolean
        """

        try:
            updates["updated_at"] = datetime.utcnow().isoformat()

            response = await supabase_client.client.table("user_preferences").update(
                updates
            ).eq("user_id", user_id).execute()

            success = response.data is not None

            logger.info(
                "Updated user preferences",
                user_id=user_id,
                success=success
            )

            return success

        except Exception as e:
            logger.error(
                "Failed to update user preferences",
                user_id=user_id,
                error=str(e)
            )
            return False

    async def store_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        create_embedding: bool = True
    ) -> Optional[str]:
        """
        Store a message in conversation history

        Args:
            conversation_id: Conversation ID
            role: Message role (user, plume, mimir, system)
            content: Message content
            metadata: Additional metadata
            create_embedding: Whether to create embedding for long-term memory

        Returns:
            Message ID if successful
        """

        try:
            message_data = {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }

            # Insert message
            response = await supabase_client.client.table("messages").insert(
                message_data
            ).execute()

            if response.data and len(response.data) > 0:
                message_id = response.data[0]["id"]

                # Create embedding asynchronously if requested
                if create_embedding and content.strip():
                    asyncio.create_task(
                        self._create_message_embedding(message_id, content)
                    )

                logger.info(
                    "Message stored",
                    message_id=message_id,
                    conversation_id=conversation_id,
                    role=role
                )

                return message_id
            else:
                logger.warning("Message storage returned no data", conversation_id=conversation_id)
                return None

        except Exception as e:
            logger.error(
                "Failed to store message",
                conversation_id=conversation_id,
                error=str(e)
            )
            return None

    async def _create_message_embedding(self, message_id: str, content: str):
        """
        Create and store embedding for a message (for long-term memory RAG)

        Args:
            message_id: Message ID
            content: Message content
        """

        try:
            # Get embedding
            embedding = await embedding_service.get_embedding(content)

            # Update message with embedding
            await supabase_client.client.table("messages").update({
                "embedding": embedding
            }).eq("id", message_id).execute()

            logger.info("Message embedding created", message_id=message_id)

        except Exception as e:
            logger.error(
                "Failed to create message embedding",
                message_id=message_id,
                error=str(e)
            )

    def _extract_topic(self, messages: List[Dict[str, Any]]) -> str:
        """
        Extract current conversation topic from recent messages

        Args:
            messages: List of recent messages

        Returns:
            Topic summary string
        """

        if not messages:
            return ""

        # Concatenate recent user messages
        user_messages = [
            msg.get("content", "")
            for msg in messages
            if msg.get("role") == "user"
        ]

        if not user_messages:
            return ""

        # Take last 3 user messages and join
        recent_topics = " ".join(user_messages[-3:])

        # Truncate if too long
        max_length = 200
        if len(recent_topics) > max_length:
            recent_topics = recent_topics[:max_length] + "..."

        return recent_topics


# Global memory service instance
memory_service = ConversationMemory(
    short_term_limit=10,
    long_term_search_limit=5,
    similarity_threshold=0.75
)