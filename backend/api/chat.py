"""
Chat API Endpoints
Real-time communication with Plume and Mimir agents
Supports REST, SSE streaming, and WebSocket connections
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import uuid
import json
import asyncio
import time

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

from agents.plume import PlumeAgent
from agents.mimir import MimirAgent
from agents.orchestrator import PlumeOrchestrator
# from services.conversation_manager import ConversationManager  # TODO: Create this service
# from services.storage import supabase_client  # TODO: Create this service
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
plume_agent = PlumeAgent()
mimir_agent = MimirAgent()
# conversation_manager = ConversationManager()  # TODO: Implement

# Models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    stream: bool = False

class ChatResponse(BaseModel):
    message: str
    agent: str
    conversation_id: str
    metadata: Dict[str, Any]
    timestamp: datetime

class ConversationSummary(BaseModel):
    id: str
    title: str
    message_count: int
    agents_used: List[str]
    created_at: datetime
    updated_at: datetime
    last_message_preview: str

class OrchestratedChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    mode: str = Field(default="auto", description="Routing mode: auto, plume, mimir, or discussion")
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    voice_data: Optional[str] = None
    audio_format: Optional[str] = None
    context_ids: Optional[List[str]] = None

class OrchestratedChatResponse(BaseModel):
    response: str
    html: Optional[str] = None
    agent_used: str
    agents_involved: List[str]
    session_id: str
    note_id: Optional[str] = None
    processing_time_ms: float
    tokens_used: int
    cost_eur: float
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    ui_metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str, user_id: str = None):
        await websocket.accept()
        self.active_connections[client_id] = websocket

        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(client_id)

    def disconnect(self, client_id: str, user_id: str = None):
        self.active_connections.pop(client_id, None)

        if user_id and user_id in self.user_connections:
            if client_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(client_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def send_personal_message(self, message: dict, client_id: str):
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except:
                self.disconnect(client_id)

    async def broadcast_to_user(self, message: dict, user_id: str):
        if user_id in self.user_connections:
            for client_id in self.user_connections[user_id][:]:
                await self.send_personal_message(message, client_id)

manager = ConnectionManager()

# Helper functions
def get_agent(agent_name: str):
    """Get agent instance by name"""
    agents = {
        "plume": plume_agent,
        "mimir": mimir_agent
    }

    if agent_name not in agents:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_name}")

    return agents[agent_name]

async def process_message(agent_name: str, message: str, conversation_id: str = None, context: Dict = None) -> Dict[str, Any]:
    """Process message with specified agent"""

    agent = get_agent(agent_name)
    start_time = time.time()

    try:
        # Get or create conversation
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            await conversation_manager.create_conversation(conversation_id, [agent_name])

        # Add user message to conversation
        await conversation_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
            metadata={"timestamp": datetime.now().isoformat()}
        )

        # Process with agent
        response = await agent.process_message(
            message=message,
            conversation_id=conversation_id,
            context=context or {}
        )

        processing_time = time.time() - start_time

        # Add agent response to conversation
        await conversation_manager.add_message(
            conversation_id=conversation_id,
            role=agent_name,
            content=response.get("message", ""),
            metadata={
                "processing_time": processing_time,
                "sources": response.get("sources", []),
                "confidence": response.get("confidence"),
                "timestamp": datetime.now().isoformat()
            }
        )

        return {
            "message": response.get("message", ""),
            "agent": agent_name,
            "conversation_id": conversation_id,
            "metadata": {
                "processing_time": processing_time,
                "sources": response.get("sources", []),
                "confidence": response.get("confidence"),
                "agent_reasoning": response.get("reasoning")
            },
            "timestamp": datetime.now()
        }

    except Exception as e:
        # Log error and add error message to conversation
        await conversation_manager.add_message(
            conversation_id=conversation_id or str(uuid.uuid4()),
            role="system",
            content=f"Error: {str(e)}",
            metadata={"error": True, "timestamp": datetime.now().isoformat()}
        )
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

# REST Endpoints

@router.post("/plume", response_model=ChatResponse)
async def chat_with_plume(request: ChatRequest):
    """Chat with Plume agent - Perfect restitution and reformulation"""

    result = await process_message(
        agent_name="plume",
        message=request.message,
        conversation_id=request.conversation_id,
        context=request.context
    )

    return ChatResponse(**result)

@router.post("/mimir", response_model=ChatResponse)
async def chat_with_mimir(request: ChatRequest):
    """Chat with Mimir agent - RAG search and knowledge connections"""

    result = await process_message(
        agent_name="mimir",
        message=request.message,
        conversation_id=request.conversation_id,
        context=request.context
    )

    return ChatResponse(**result)

# Orchestrated endpoint - uses LangGraph workflow
@router.post("/orchestrated", response_model=OrchestratedChatResponse)
async def chat_orchestrated(request: OrchestratedChatRequest, fastapi_request: Request):
    """
    Orchestrated chat using LangGraph workflow

    Supports intelligent routing between Plume and Mimir agents,
    with optional AutoGen multi-agent discussion mode.

    Mode options:
    - auto: Intelligent routing based on intent classification
    - plume: Force Plume agent (restitution)
    - mimir: Force Mimir agent (RAG search)
    - discussion: AutoGen multi-agent discussion
    """

    try:
        # Get orchestrator from app state
        orchestrator: PlumeOrchestrator = fastapi_request.app.state.orchestrator

        # Process message through orchestrator with conversation memory
        result = await orchestrator.process(
            input_text=request.message,
            mode=request.mode,
            voice_data=request.voice_data,
            audio_format=request.audio_format,
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            context_ids=request.context_ids
        )

        # Return formatted response
        return OrchestratedChatResponse(
            response=result["response"],
            html=result.get("html"),
            agent_used=result["agent_used"],
            agents_involved=result.get("agents_involved", []),
            session_id=result["session_id"],
            note_id=result.get("note_id"),
            processing_time_ms=result["processing_time_ms"],
            tokens_used=result["tokens_used"],
            cost_eur=result["cost_eur"],
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            ui_metadata=result.get("ui_metadata", {}),
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Orchestrated chat failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Orchestrated chat processing failed: {str(e)}"
        )

# Orchestrated SSE Streaming - AutoGen Discussion Visibility
@router.post("/orchestrated/stream")
async def chat_orchestrated_stream(request: OrchestratedChatRequest, fastapi_request: Request):
    """
    Orchestrated chat with Server-Sent Events streaming

    Streams agent messages in real-time, making AutoGen discussion between
    Plume and Mimir visible to the user.

    SSE Event Types:
    - start: Connection established
    - processing: Node processing status
    - agent_message: Message from Plume or Mimir
    - complete: Processing complete with final result
    - error: Error occurred
    - keepalive: Connection keepalive ping
    """

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generate SSE events for orchestrated chat"""

        logger.info("SSE: Starting event stream generator")

        # Create async queue for messages
        message_queue = asyncio.Queue()

        try:
            # Get orchestrator from app state
            orchestrator: PlumeOrchestrator = fastapi_request.app.state.orchestrator
            logger.info("SSE: Orchestrator retrieved from app state")

            # Send initial start event
            logger.info("SSE: Sending start event")
            yield f"data: {json.dumps({'type': 'start', 'session_id': request.session_id or 'new', 'timestamp': datetime.now().isoformat()}, cls=DateTimeEncoder)}\n\n"
            logger.info("SSE: Start event sent successfully")

            # Start processing in background task
            async def process_with_queue():
                """Process request with SSE queue"""
                logger.info("SSE: Background process_with_queue started")
                try:
                    logger.info("SSE: Calling orchestrator.process", message_length=len(request.message), mode=request.mode)
                    result = await orchestrator.process(
                        input_text=request.message,
                        mode=request.mode,
                        voice_data=request.voice_data,
                        audio_format=request.audio_format,
                        session_id=request.session_id,
                        conversation_id=request.conversation_id,
                        user_id=request.user_id,
                        context_ids=request.context_ids,
                        # Pass queue through state for discussion_node to use
                        _sse_queue=message_queue
                    )
                    logger.info("SSE: Orchestrator.process completed successfully", agent_used=result.get('agent_used'))
                    # Signal completion by putting None
                    await message_queue.put(None)
                    logger.info("SSE: Sent completion signal (None) to queue")
                    return result
                except Exception as e:
                    logger.error(f"SSE: Processing error in stream: {str(e)}")
                    await message_queue.put({'type': 'error', 'error': str(e), 'timestamp': datetime.now()})
                    await message_queue.put(None)
                    return None

            # Start background processing
            logger.info("SSE: Creating background process_task")
            process_task = asyncio.create_task(process_with_queue())
            logger.info("SSE: Background process_task created and started")

            # Stream messages from queue
            logger.info("SSE: Entering message streaming loop")
            last_keepalive = time.time()
            keepalive_interval = 15  # seconds
            message_count = 0

            while True:
                try:
                    # Wait for message with timeout for keepalive
                    try:
                        logger.debug("SSE: Waiting for message from queue (timeout 1s)")
                        message = await asyncio.wait_for(message_queue.get(), timeout=1.0)
                        message_count += 1
                        logger.info("SSE: Received message from queue", message_number=message_count, message_type=message.get('type') if message else 'None')
                    except asyncio.TimeoutError:
                        logger.debug("SSE: Queue timeout (no message), checking status")
                        # Check if we need to send keepalive
                        if time.time() - last_keepalive > keepalive_interval:
                            logger.info("SSE: Sending keepalive event")
                            yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.now()}, cls=DateTimeEncoder)}\n\n"
                            last_keepalive = time.time()

                        # Check if processing is done
                        if process_task.done():
                            logger.info("SSE: Background process_task completed, exiting loop")
                            break

                        continue

                    # None signals completion
                    if message is None:
                        logger.info("SSE: Received completion signal (None), exiting loop")
                        break

                    # Send message as SSE event
                    logger.info("SSE: Yielding message to client", message_type=message.get('type'))
                    yield f"data: {json.dumps(message, cls=DateTimeEncoder)}\n\n"
                    last_keepalive = time.time()

                except Exception as e:
                    logger.error(f"SSE: Stream error in loop: {str(e)}")
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'timestamp': datetime.now()}, cls=DateTimeEncoder)}\n\n"
                    break

            # Get final result
            logger.info("SSE: Retrieving final result from process_task")
            try:
                result = await process_task
                logger.info("SSE: Final result retrieved", has_result=result is not None)

                if result:
                    # Send complete event with final result
                    logger.info("SSE: Sending complete event with final result")
                    complete_event = {
                        'type': 'complete',
                        'result': {
                            'response': result['response'],
                            'html': result.get('html'),
                            'agent_used': result['agent_used'],
                            'agents_involved': result.get('agents_involved', []),
                            'discussion_history': result.get('discussion_history', []),
                            'session_id': result['session_id'],
                            'note_id': result.get('note_id'),
                            'processing_time_ms': result['processing_time_ms'],
                            'tokens_used': result['tokens_used'],
                            'cost_eur': result['cost_eur'],
                            'errors': result.get('errors', []),
                            'warnings': result.get('warnings', [])
                        },
                        'timestamp': datetime.now()
                    }
                    yield f"data: {json.dumps(complete_event, cls=DateTimeEncoder)}\n\n"
                    logger.info("SSE: Complete event sent successfully")

            except Exception as e:
                logger.error(f"SSE: Error getting final result: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'timestamp': datetime.now()}, cls=DateTimeEncoder)}\n\n"

            # Send termination signal
            logger.info("SSE: Sending [DONE] termination signal")
            yield "data: [DONE]\n\n"
            logger.info("SSE: Event stream generator completed successfully", total_messages_sent=message_count)

        except Exception as e:
            logger.error(f"SSE: Critical stream error in event_stream: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'timestamp': datetime.now()}, cls=DateTimeEncoder)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for Render
            "Content-Type": "text/event-stream"
        }
    )

# Server-Sent Events (SSE) Endpoints

@router.post("/plume/stream")
async def chat_with_plume_stream(request: ChatRequest):
    """Stream chat with Plume agent using Server-Sent Events"""

    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            agent = get_agent("plume")
            conversation_id = request.conversation_id or str(uuid.uuid4())

            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id})}\\n\\n"

            # Add user message to conversation
            await conversation_manager.add_message(
                conversation_id=conversation_id,
                role="user",
                content=request.message,
                metadata={"timestamp": datetime.now().isoformat()}
            )

            # Stream response from agent
            async for chunk in agent.stream_message(
                message=request.message,
                conversation_id=conversation_id,
                context=request.context
            ):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\\n\\n"
                await asyncio.sleep(0.01)  # Small delay for smooth streaming

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'agent': 'plume'})}\\n\\n"
            yield "data: [DONE]\\n\\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\\n\\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.post("/mimir/stream")
async def chat_with_mimir_stream(request: ChatRequest):
    """Stream chat with Mimir agent using Server-Sent Events"""

    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            agent = get_agent("mimir")
            conversation_id = request.conversation_id or str(uuid.uuid4())

            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id})}\\n\\n"

            # Add user message to conversation
            await conversation_manager.add_message(
                conversation_id=conversation_id,
                role="user",
                content=request.message,
                metadata={"timestamp": datetime.now().isoformat()}
            )

            # Stream response from agent
            async for chunk in agent.stream_message(
                message=request.message,
                conversation_id=conversation_id,
                context=request.context
            ):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\\n\\n"
                await asyncio.sleep(0.01)

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'agent': 'mimir'})}\\n\\n"
            yield "data: [DONE]\\n\\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\\n\\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

# Conversation Management Endpoints

@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(limit: int = 50, offset: int = 0):
    """List recent conversations"""

    try:
        conversations = await conversation_manager.list_conversations(limit=limit, offset=offset)

        summaries = []
        for conv in conversations:
            messages = conv.get("messages", [])

            # Get last message preview
            last_message = ""
            if messages:
                last_msg = messages[-1]
                last_message = last_msg.get("content", "")[:100]
                if len(last_msg.get("content", "")) > 100:
                    last_message += "..."

            summaries.append(ConversationSummary(
                id=conv["id"],
                title=conv.get("title", f"Conversation {conv['id'][:8]}"),
                message_count=len(messages),
                agents_used=conv.get("agents_involved", []),
                created_at=datetime.fromisoformat(conv["created_at"]),
                updated_at=datetime.fromisoformat(conv["updated_at"]),
                last_message_preview=last_message
            ))

        return summaries

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get specific conversation with all messages"""

    try:
        conversation = await conversation_manager.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return conversation

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""

    try:
        success = await conversation_manager.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

# WebSocket Endpoint

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, user_id: str = None):
    """WebSocket endpoint for real-time chat"""

    await manager.connect(websocket, client_id, user_id)

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to SCRIBE chat",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })

        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message_type = data.get("type", "chat")

            if message_type == "chat":
                # Process chat message
                agent_name = data.get("agent", "plume")
                message = data.get("message", "")
                conversation_id = data.get("conversation_id")
                context = data.get("context", {})

                if not message.strip():
                    await websocket.send_json({
                        "type": "error",
                        "error": "Message cannot be empty"
                    })
                    continue

                # Send acknowledgment
                await websocket.send_json({
                    "type": "processing",
                    "agent": agent_name,
                    "message": "Agent is processing your message..."
                })

                try:
                    # Process message with agent
                    result = await process_message(
                        agent_name=agent_name,
                        message=message,
                        conversation_id=conversation_id,
                        context=context
                    )

                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        **result
                    })

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Processing failed: {str(e)}"
                    })

            elif message_type == "ping":
                # Respond to ping
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id, user_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": f"WebSocket error: {str(e)}"
        })
        manager.disconnect(client_id, user_id)

# Health Check

@router.get("/health")
async def chat_health():
    """Chat service health check"""

    try:
        # Test agent availability
        agents_status = {}

        for agent_name in ["plume", "mimir"]:
            try:
                agent = get_agent(agent_name)
                # Simple health check - could be expanded
                agents_status[agent_name] = {
                    "status": "healthy",
                    "model": getattr(agent, 'model_name', 'unknown')
                }
            except Exception as e:
                agents_status[agent_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }

        # Overall status
        overall_status = "healthy" if all(
            agent["status"] == "healthy" for agent in agents_status.values()
        ) else "degraded"

        return {
            "status": overall_status,
            "agents": agents_status,
            "websocket_connections": len(manager.active_connections),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )