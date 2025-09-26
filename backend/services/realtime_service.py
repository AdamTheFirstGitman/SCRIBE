"""
Realtime Service with Supabase Subscriptions
Real-time synchronization for collaborative features
"""

import asyncio
import json
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from enum import Enum

from ..database.supabase_client import get_supabase_client
from ..config import get_settings

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Real-time event types"""
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"
    MESSAGE_SENT = "message_sent"
    USER_TYPING = "user_typing"
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    SEARCH_PERFORMED = "search_performed"
    AGENT_RESPONSE = "agent_response"

@dataclass
class RealtimeEvent:
    """Real-time event structure"""
    event_type: EventType
    table: str
    record: Dict[str, Any]
    old_record: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class RealtimeService:
    """
    Real-time synchronization service using Supabase subscriptions
    Handles collaborative features and live updates
    """

    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_client()
        self.subscriptions: Dict[str, Any] = {}
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.active_users: Dict[str, Dict[str, Any]] = {}
        self.typing_users: Dict[str, Dict[str, datetime]] = {}

    async def initialize(self):
        """Initialize real-time subscriptions"""
        try:
            logger.info("Initializing realtime subscriptions...")

            # Subscribe to documents table
            await self._subscribe_documents()

            # Subscribe to conversations table
            await self._subscribe_conversations()

            # Subscribe to search queries (for collaboration)
            await self._subscribe_search_queries()

            logger.info("✅ Realtime service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize realtime service: {e}")
            raise

    async def _subscribe_documents(self):
        """Subscribe to documents table changes"""
        try:
            # Create subscription for documents
            subscription = self.supabase.table('documents') \
                .on('INSERT', self._handle_document_insert) \
                .on('UPDATE', self._handle_document_update) \
                .on('DELETE', self._handle_document_delete) \
                .subscribe()

            self.subscriptions['documents'] = subscription
            logger.info("Subscribed to documents table")

        except Exception as e:
            logger.error(f"Failed to subscribe to documents: {e}")

    async def _subscribe_conversations(self):
        """Subscribe to conversations table changes"""
        try:
            subscription = self.supabase.table('conversations') \
                .on('INSERT', self._handle_conversation_insert) \
                .on('UPDATE', self._handle_conversation_update) \
                .subscribe()

            self.subscriptions['conversations'] = subscription
            logger.info("Subscribed to conversations table")

        except Exception as e:
            logger.error(f"Failed to subscribe to conversations: {e}")

    async def _subscribe_search_queries(self):
        """Subscribe to search queries for collaboration insights"""
        try:
            subscription = self.supabase.table('search_queries') \
                .on('INSERT', self._handle_search_insert) \
                .subscribe()

            self.subscriptions['search_queries'] = subscription
            logger.info("Subscribed to search queries table")

        except Exception as e:
            logger.error(f"Failed to subscribe to search queries: {e}")

    # Event Handlers
    async def _handle_document_insert(self, payload):
        """Handle new document creation"""
        try:
            record = payload.get('new', {})

            event = RealtimeEvent(
                event_type=EventType.DOCUMENT_CREATED,
                table='documents',
                record=record
            )

            await self._broadcast_event(event)
            logger.info(f"Document created: {record.get('title', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error handling document insert: {e}")

    async def _handle_document_update(self, payload):
        """Handle document updates"""
        try:
            new_record = payload.get('new', {})
            old_record = payload.get('old', {})

            event = RealtimeEvent(
                event_type=EventType.DOCUMENT_UPDATED,
                table='documents',
                record=new_record,
                old_record=old_record
            )

            await self._broadcast_event(event)
            logger.info(f"Document updated: {new_record.get('title', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error handling document update: {e}")

    async def _handle_document_delete(self, payload):
        """Handle document deletion"""
        try:
            record = payload.get('old', {})

            event = RealtimeEvent(
                event_type=EventType.DOCUMENT_DELETED,
                table='documents',
                record=record
            )

            await self._broadcast_event(event)
            logger.info(f"Document deleted: {record.get('title', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error handling document delete: {e}")

    async def _handle_conversation_insert(self, payload):
        """Handle new conversation messages"""
        try:
            record = payload.get('new', {})
            messages = record.get('messages', [])

            if messages:
                last_message = messages[-1]

                event = RealtimeEvent(
                    event_type=EventType.MESSAGE_SENT,
                    table='conversations',
                    record={
                        'conversation_id': record['id'],
                        'message': last_message,
                        'message_count': len(messages)
                    }
                )

                await self._broadcast_event(event)

        except Exception as e:
            logger.error(f"Error handling conversation insert: {e}")

    async def _handle_conversation_update(self, payload):
        """Handle conversation updates (new messages)"""
        try:
            new_record = payload.get('new', {})
            old_record = payload.get('old', {})

            new_messages = new_record.get('messages', [])
            old_messages = old_record.get('messages', [])

            # Check if new messages were added
            if len(new_messages) > len(old_messages):
                new_message = new_messages[-1]

                event = RealtimeEvent(
                    event_type=EventType.MESSAGE_SENT,
                    table='conversations',
                    record={
                        'conversation_id': new_record['id'],
                        'message': new_message,
                        'message_count': len(new_messages)
                    }
                )

                await self._broadcast_event(event)

        except Exception as e:
            logger.error(f"Error handling conversation update: {e}")

    async def _handle_search_insert(self, payload):
        """Handle search queries for collaboration insights"""
        try:
            record = payload.get('new', {})

            event = RealtimeEvent(
                event_type=EventType.SEARCH_PERFORMED,
                table='search_queries',
                record=record
            )

            await self._broadcast_event(event)

        except Exception as e:
            logger.error(f"Error handling search insert: {e}")

    # Event Broadcasting
    async def _broadcast_event(self, event: RealtimeEvent):
        """Broadcast event to all registered handlers"""
        try:
            handlers = self.event_handlers.get(event.event_type, [])

            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")

        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")

    # Public API
    def subscribe_to_event(self, event_type: EventType, handler: Callable):
        """Subscribe to specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)
        logger.info(f"Handler registered for {event_type}")

    def unsubscribe_from_event(self, event_type: EventType, handler: Callable):
        """Unsubscribe from event type"""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
                logger.info(f"Handler unregistered for {event_type}")
            except ValueError:
                pass

    async def broadcast_user_typing(self, user_id: str, conversation_id: str):
        """Broadcast user typing indicator"""
        try:
            # Update typing status
            if conversation_id not in self.typing_users:
                self.typing_users[conversation_id] = {}

            self.typing_users[conversation_id][user_id] = datetime.now()

            event = RealtimeEvent(
                event_type=EventType.USER_TYPING,
                table='realtime',
                record={
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'action': 'typing'
                }
            )

            await self._broadcast_event(event)

            # Auto-clear typing indicator after 3 seconds
            await asyncio.sleep(3)
            if (conversation_id in self.typing_users and
                user_id in self.typing_users[conversation_id]):
                del self.typing_users[conversation_id][user_id]

        except Exception as e:
            logger.error(f"Error broadcasting typing indicator: {e}")

    async def broadcast_user_status(self, user_id: str, status: str, metadata: Dict[str, Any] = None):
        """Broadcast user online/offline status"""
        try:
            if status == 'online':
                self.active_users[user_id] = {
                    'timestamp': datetime.now(),
                    'metadata': metadata or {}
                }
                event_type = EventType.USER_ONLINE
            else:
                self.active_users.pop(user_id, None)
                event_type = EventType.USER_OFFLINE

            event = RealtimeEvent(
                event_type=event_type,
                table='realtime',
                record={
                    'user_id': user_id,
                    'status': status,
                    'metadata': metadata or {}
                }
            )

            await self._broadcast_event(event)

        except Exception as e:
            logger.error(f"Error broadcasting user status: {e}")

    async def get_active_users(self) -> List[Dict[str, Any]]:
        """Get list of active users"""
        try:
            # Clean up stale users (older than 5 minutes)
            now = datetime.now()
            stale_users = []

            for user_id, data in self.active_users.items():
                time_diff = now - data['timestamp']
                if time_diff.total_seconds() > 300:  # 5 minutes
                    stale_users.append(user_id)

            for user_id in stale_users:
                del self.active_users[user_id]

            # Return active users
            active_users = []
            for user_id, data in self.active_users.items():
                active_users.append({
                    'user_id': user_id,
                    'online_since': data['timestamp'].isoformat(),
                    'metadata': data['metadata']
                })

            return active_users

        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []

    async def get_typing_users(self, conversation_id: str) -> List[str]:
        """Get users currently typing in a conversation"""
        try:
            if conversation_id not in self.typing_users:
                return []

            # Clean up stale typing indicators (older than 5 seconds)
            now = datetime.now()
            stale_users = []

            for user_id, timestamp in self.typing_users[conversation_id].items():
                time_diff = now - timestamp
                if time_diff.total_seconds() > 5:
                    stale_users.append(user_id)

            for user_id in stale_users:
                del self.typing_users[conversation_id][user_id]

            return list(self.typing_users[conversation_id].keys())

        except Exception as e:
            logger.error(f"Error getting typing users: {e}")
            return []

    async def broadcast_agent_response(self, agent_name: str, response: str, metadata: Dict[str, Any]):
        """Broadcast agent response for real-time updates"""
        try:
            event = RealtimeEvent(
                event_type=EventType.AGENT_RESPONSE,
                table='realtime',
                record={
                    'agent': agent_name,
                    'response': response,
                    'metadata': metadata
                }
            )

            await self._broadcast_event(event)

        except Exception as e:
            logger.error(f"Error broadcasting agent response: {e}")

    async def get_realtime_stats(self) -> Dict[str, Any]:
        """Get real-time service statistics"""
        try:
            active_subscriptions = len(self.subscriptions)
            registered_handlers = sum(len(handlers) for handlers in self.event_handlers.values())
            active_users_count = len(await self.get_active_users())

            # Count typing users across all conversations
            typing_count = sum(len(users) for users in self.typing_users.values())

            return {
                'status': 'healthy',
                'active_subscriptions': active_subscriptions,
                'registered_handlers': registered_handlers,
                'active_users': active_users_count,
                'typing_users': typing_count,
                'event_types': list(self.event_handlers.keys()),
                'subscribed_tables': list(self.subscriptions.keys()),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def cleanup(self):
        """Clean up subscriptions and resources"""
        try:
            logger.info("Cleaning up realtime service...")

            # Close all subscriptions
            for table, subscription in self.subscriptions.items():
                try:
                    subscription.unsubscribe()
                    logger.info(f"Unsubscribed from {table}")
                except Exception as e:
                    logger.error(f"Error unsubscribing from {table}: {e}")

            # Clear data structures
            self.subscriptions.clear()
            self.event_handlers.clear()
            self.active_users.clear()
            self.typing_users.clear()

            logger.info("✅ Realtime service cleanup completed")

        except Exception as e:
            logger.error(f"Error during realtime cleanup: {e}")

# Singleton instance
_realtime_service = None

def get_realtime_service() -> RealtimeService:
    """Get singleton realtime service instance"""
    global _realtime_service
    if _realtime_service is None:
        _realtime_service = RealtimeService()
    return _realtime_service