"""
LangGraph Orchestrator for Plume & Mimir
Main workflow coordinator that routes between agents
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
# from langgraph.checkpoint.postgres import PostgresSaver  # TODO: Re-enable when implementing async context manager

from agents.state import AgentState, add_processing_step, add_error, add_model_call, finalize_state
from services.transcription import transcription_service
from services.embeddings import embedding_service
from services.rag import rag_service
from services.storage import supabase_client
from services.cache import cache_manager
from services.intent_classifier import intent_classifier
from services.memory_service import memory_service
from utils.logger import get_agent_logger, get_logger
from utils.message_filter import filter_for_ui, filter_tool_for_ui, should_create_archive_note
from utils.tool_message_formatter import format_tool_activity_for_ui
from config import settings

logger = get_logger(__name__)

class PlumeOrchestrator:
    """
    Main orchestrator using LangGraph to coordinate agent workflow
    Routes between Plume (restitution), Mimir (archive), and discussion modes
    """

    def __init__(self):
        self.graph = None
        self.app = None
        self._initialized = False
        self._current_sse_queue = None  # Store SSE queue as instance variable to avoid msgpack serialization

    async def initialize(self):
        """Initialize the orchestrator and compile the workflow"""
        if self._initialized:
            return

        logger.info("Initializing Plume & Mimir orchestrator")

        try:
            # Build the workflow graph
            self.graph = self._build_graph()

            # Use in-memory checkpointing (temporary)
            # TODO: Implement PostgreSQL checkpointing with proper async context manager
            # async with PostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
            #     await checkpointer.setup()
            #     self.app = self.graph.compile(checkpointer=checkpointer)
            checkpointer = MemorySaver()
            logger.warning("Using in-memory checkpointing (PostgreSQL checkpointing disabled temporarily)")

            # Compile the workflow with checkpointing
            self.app = self.graph.compile(checkpointer=checkpointer)

            self._initialized = True
            logger.info("Orchestrator initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize orchestrator", error=str(e))
            raise

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""

        # Define the graph
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("intake", self.intake_node)
        graph.add_node("transcription", self.transcription_node)
        graph.add_node("router", self.router_node)
        graph.add_node("context_retrieval", self.context_retrieval_node)
        graph.add_node("plume", self.plume_node)
        graph.add_node("mimir", self.mimir_node)
        graph.add_node("discussion", self.discussion_node)
        graph.add_node("storage", self.storage_node)
        graph.add_node("finalize", self.finalize_node)

        # Define workflow edges
        graph.add_edge(START, "intake")

        # From intake: transcribe if voice, otherwise route
        graph.add_conditional_edges(
            "intake",
            self.intake_decision,
            {
                "transcription": "transcription",
                "router": "router"
            }
        )

        # From transcription: always go to router
        graph.add_edge("transcription", "router")

        # From router: decide which agent(s) to use
        graph.add_conditional_edges(
            "router",
            self.router_decision,
            {
                "plume_only": "plume",
                "mimir_only": "context_retrieval",
                "discussion": "context_retrieval",
                "error": "finalize"
            }
        )

        # From context_retrieval: go to mimir or discussion
        graph.add_conditional_edges(
            "context_retrieval",
            self.context_decision,
            {
                "mimir": "mimir",
                "discussion": "discussion"
            }
        )

        # All agent nodes go to storage
        graph.add_edge("plume", "storage")
        graph.add_edge("mimir", "storage")
        graph.add_edge("discussion", "storage")

        # From storage: finalize
        graph.add_edge("storage", "finalize")

        # From finalize: end
        graph.add_edge("finalize", END)

        return graph

    # =============================================================================
    # WORKFLOW NODES
    # =============================================================================

    async def intake_node(self, state: AgentState) -> AgentState:
        """
        Initial processing of user input with conversation memory loading
        """
        logger.info("Processing intake", input_length=len(state.get("input", "")))

        add_processing_step(state, "intake_processing")

        try:
            # Basic input validation
            input_text = state.get("input", "").strip()
            if not input_text and not state.get("voice_data"):
                add_error(state, "No input provided (text or voice)")
                return state

            # Set session ID if not provided
            if not state.get("session_id"):
                state["session_id"] = f"session_{int(time.time())}"

            # Load conversation memory if conversation_id provided
            conversation_id = state.get("conversation_id")
            user_id = state.get("user_id")

            if conversation_id:
                try:
                    # Get conversation context (short + long term + preferences)
                    memory_context = await memory_service.get_conversation_context(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        include_long_term=True
                    )

                    # Enrich state with memory context
                    state["recent_messages"] = memory_context.get("recent_messages", [])
                    state["similar_past_conversations"] = memory_context.get("similar_past_conversations", [])
                    state["user_preferences"] = memory_context.get("user_preferences", {})
                    state["conversation_summary"] = memory_context.get("conversation_summary", "")

                    logger.info(
                        "Conversation memory loaded",
                        conversation_id=conversation_id,
                        recent_messages_count=len(state["recent_messages"]),
                        similar_past_count=len(state["similar_past_conversations"])
                    )

                except Exception as e:
                    logger.warning("Failed to load conversation memory", error=str(e))
                    # Continue without memory context

            logger.info("Intake processing completed", session_id=state["session_id"])
            return state

        except Exception as e:
            logger.error("Intake node failed", error=str(e))
            add_error(state, f"Intake processing failed: {str(e)}")
            return state

    async def transcription_node(self, state: AgentState) -> AgentState:
        """Transcribe voice input to text"""
        logger.info("Processing voice transcription")

        add_processing_step(state, "voice_transcription")

        try:
            voice_data = state.get("voice_data")
            audio_format = state.get("audio_format", "webm")

            if not voice_data:
                add_error(state, "No voice data provided for transcription")
                return state

            # Transcribe using the transcription service
            start_time = time.time()
            result = await transcription_service.transcribe_audio(voice_data, audio_format)
            duration_ms = (time.time() - start_time) * 1000

            # Update state with transcription
            state["input"] = result["text"]
            add_processing_step(state, "transcription_completed")

            # Record token usage (estimate for Whisper)
            estimated_tokens = len(result["text"]) // 4  # Rough estimate
            add_model_call(state, "whisper-1", estimated_tokens, 0.006 * (result.get("duration_seconds", 0) / 60), "transcription", duration_ms)

            logger.info("Voice transcription completed",
                       text_length=len(result["text"]),
                       confidence=result.get("confidence", 0),
                       duration_ms=duration_ms)

            return state

        except Exception as e:
            logger.error("Transcription failed", error=str(e))
            add_error(state, f"Voice transcription failed: {str(e)}")
            return state

    async def router_node(self, state: AgentState) -> AgentState:
        """Route to appropriate agent based on input, mode, and explicit agent mentions"""
        logger.info("Routing request", mode=state.get("mode", "auto"))

        add_processing_step(state, "routing_decision")

        try:
            input_text = state.get("input", "")
            mode = state.get("mode", "auto")
            input_lower = input_text.lower()

            # Check for explicit agent mention by name (highest priority)
            plume_mentioned = "plume" in input_lower
            mimir_mentioned = "mimir" in input_lower

            if plume_mentioned and mimir_mentioned:
                # Both mentioned → discussion mode
                state["agent_used"] = "discussion"
                state["routing_reason"] = "both_agents_mentioned"
                logger.info("Routed to Discussion (both agents mentioned)")
                return state

            elif plume_mentioned and not mimir_mentioned:
                # Only Plume mentioned
                state["agent_used"] = "plume"
                state["routing_reason"] = "explicit_mention_plume"
                logger.info("Routed to Plume (explicit mention)")
                return state

            elif mimir_mentioned and not plume_mentioned:
                # Only Mimir mentioned
                state["agent_used"] = "mimir"
                state["routing_reason"] = "explicit_mention_mimir"
                logger.info("Routed to Mimir (explicit mention)")
                return state

            # No explicit mention → check mode
            # Explicit mode selection
            if mode == "plume":
                state["agent_used"] = "plume"
                state["routing_reason"] = "forced_mode_plume"
                logger.info("Routed to Plume (explicit mode)")
                return state

            elif mode == "mimir":
                state["agent_used"] = "mimir"
                state["routing_reason"] = "forced_mode_mimir"
                logger.info("Routed to Mimir (explicit mode)")
                return state

            elif mode == "discussion":
                state["agent_used"] = "discussion"
                state["routing_reason"] = "forced_mode_discussion"
                logger.info("Routed to Discussion (explicit mode)")
                return state

            # Auto-routing logic - Always use discussion mode (agents decide with tools)
            elif mode == "auto":
                state["agent_used"] = "discussion"
                state["routing_reason"] = "auto_discussion_with_tools"
                logger.info("Auto-routed to discussion (agents will decide with tools)")
                return state

            else:
                add_error(state, f"Unknown mode: {mode}")
                return state

        except Exception as e:
            logger.error("Routing failed", error=str(e))
            add_error(state, f"Routing failed: {str(e)}")
            return state

    def _is_simple_query(self, query: str) -> bool:
        """Detect if query is simple (greeting/short question) and doesn't need RAG"""
        query_lower = query.lower().strip()

        # Salutations communes
        greetings = [
            "salut", "coucou", "hello", "hi", "bonjour", "bonsoir",
            "hey", "yo", "cc", "slt", "bjr"
        ]

        # Questions très courtes (< 15 caractères) sans mots-clés de recherche
        if len(query_lower) < 15:
            # Si c'est juste une salutation
            if any(greeting in query_lower for greeting in greetings):
                return True
            # Si c'est très court ET sans mots de recherche
            search_keywords = ["recherche", "trouve", "cherche", "montre", "liste", "quoi", "comment", "pourquoi"]
            if not any(keyword in query_lower for keyword in search_keywords):
                return True

        return False

    async def context_retrieval_node(self, state: AgentState) -> AgentState:
        """Retrieve relevant context for Mimir or discussion"""
        query = state.get("input", "")

        # Skip RAG for simple queries (greetings, very short questions)
        if self._is_simple_query(query):
            logger.info("Simple query detected - skipping RAG search", query_length=len(query))
            state["context"] = []
            state["search_results"] = []
            state["search_query"] = query
            return state

        logger.info("Retrieving context for knowledge-based response")
        add_processing_step(state, "context_retrieval")

        try:
            context_ids = state.get("context_ids", [])

            # Perform RAG search
            start_time = time.time()
            search_results = await rag_service.search_knowledge(
                query=query,
                limit=10,
                similarity_threshold=0.75,
                include_context_ids=context_ids
            )
            duration_ms = (time.time() - start_time) * 1000

            # Update state with context
            state["context"] = search_results
            state["search_results"] = search_results
            state["search_query"] = query

            logger.info("Context retrieval completed",
                       results_found=len(search_results),
                       duration_ms=duration_ms)

            return state

        except Exception as e:
            logger.error("Context retrieval failed", error=str(e))
            add_error(state, f"Context retrieval failed: {str(e)}")
            return state

    async def plume_node(self, state: AgentState) -> AgentState:
        """Plume agent - Perfect restitution and reformulation"""
        agent_logger = get_agent_logger("plume", state.get("session_id"))
        agent_logger.log_agent_start("restitution_task")

        add_processing_step(state, "plume_processing")

        # Get SSE queue for streaming
        sse_queue = self._current_sse_queue

        try:
            # Send processing started event if SSE available
            if sse_queue:
                await sse_queue.put({
                    'type': 'processing',
                    'node': 'plume',
                    'status': 'started',
                    'timestamp': datetime.now().isoformat()
                })

            from agents.plume import plume_agent
            input_text = state.get("input", "")

            start_time = time.time()
            response = await plume_agent.process(input_text, state)
            duration_ms = (time.time() - start_time) * 1000

            # Update state
            state["plume_response"] = response["content"]
            state["final_output"] = response["content"]
            state["final_html"] = response.get("html")
            state["agents_involved"] = ["plume"]

            # Record usage
            add_model_call(state, response.get("model", "claude-3-opus"), response.get("tokens", 0),
                          response.get("cost", 0.0), "plume", duration_ms)

            # Send processing completed event if SSE available
            if sse_queue:
                await sse_queue.put({
                    'type': 'processing',
                    'node': 'plume',
                    'status': 'completed',
                    'timestamp': datetime.now().isoformat()
                })

            agent_logger.log_agent_complete("restitution_task", duration_ms)
            logger.info("Plume processing completed", response_length=len(response["content"]))

            return state

        except Exception as e:
            logger.error("Plume processing failed", error=str(e))
            add_error(state, f"Plume processing failed: {str(e)}")

            # Send error event to SSE if available
            if sse_queue:
                try:
                    await sse_queue.put({
                        'type': 'error',
                        'node': 'plume',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                except:
                    pass

            return state

    async def mimir_node(self, state: AgentState) -> AgentState:
        """Mimir agent - Knowledge archiving and retrieval"""
        agent_logger = get_agent_logger("mimir", state.get("session_id"))
        agent_logger.log_agent_start("knowledge_task")

        add_processing_step(state, "mimir_processing")

        # Get SSE queue for streaming
        sse_queue = self._current_sse_queue

        try:
            # Send processing started event if SSE available
            if sse_queue:
                await sse_queue.put({
                    'type': 'processing',
                    'node': 'mimir',
                    'status': 'started',
                    'timestamp': datetime.now().isoformat()
                })

            from agents.mimir import mimir_agent
            input_text = state.get("input", "")
            context = state.get("context", [])

            start_time = time.time()
            response = await mimir_agent.process(input_text, context, state)
            duration_ms = (time.time() - start_time) * 1000

            # Update state
            state["mimir_response"] = response["content"]
            state["final_output"] = response["content"]
            state["final_html"] = response.get("html")
            state["agents_involved"] = ["mimir"]

            # Record usage
            add_model_call(state, response.get("model", "claude-3-opus"), response.get("tokens", 0),
                          response.get("cost", 0.0), "mimir", duration_ms)

            # Send processing completed event if SSE available
            if sse_queue:
                await sse_queue.put({
                    'type': 'processing',
                    'node': 'mimir',
                    'status': 'completed',
                    'timestamp': datetime.now().isoformat()
                })

            agent_logger.log_agent_complete("knowledge_task", duration_ms)
            logger.info("Mimir processing completed", response_length=len(response["content"]))

            return state

        except Exception as e:
            logger.error("Mimir processing failed", error=str(e))
            add_error(state, f"Mimir processing failed: {str(e)}")

            # Send error event to SSE if available
            if sse_queue:
                try:
                    await sse_queue.put({
                        'type': 'error',
                        'node': 'mimir',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                except:
                    pass

            return state

    async def discussion_node(self, state: AgentState) -> AgentState:
        """
        AutoGen discussion between Plume and Mimir with SSE streaming support
        Captures internal messages for real-time visibility
        """
        agent_logger = get_agent_logger("discussion", state.get("session_id"))
        agent_logger.log_agent_start("multi_agent_discussion")

        add_processing_step(state, "autogen_discussion")

        try:
            from agents.autogen_agents import autogen_discussion
            input_text = state.get("input", "")
            context = state.get("context", [])
            sse_queue = self._current_sse_queue  # SSE queue for streaming

            # Initialize discussion if needed
            if not autogen_discussion._initialized:
                autogen_discussion.initialize()

            start_time = time.time()

            # Prepare context summary
            context_summary = autogen_discussion._prepare_context_summary(context)

            # Format the initial task message (simplified - just user input)
            # Agents have detailed system messages, no need for verbose instructions
            task_message = input_text

            discussion_history = []

            # Run discussion with message capture for SSE streaming
            if autogen_discussion._initialized and autogen_discussion.group_chat:
                # Send processing event to SSE if available
                if sse_queue:
                    await sse_queue.put({
                        'type': 'processing',
                        'node': 'discussion',
                        'status': 'started',
                        'timestamp': datetime.now().isoformat()
                    })

                # Run the group chat with retry on rate limit/overload
                max_retries = 3
                retry_delay = 2  # seconds
                result = None

                for attempt in range(max_retries):
                    try:
                        result = await autogen_discussion.group_chat.run(task=task_message)
                        break  # Success
                    except Exception as api_error:
                        error_msg = str(api_error).lower()
                        if "overloaded" in error_msg or "rate" in error_msg:
                            if attempt < max_retries - 1:
                                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                                logger.warning(f"API overloaded, retry {attempt+1}/{max_retries} after {wait_time}s")
                                await asyncio.sleep(wait_time)
                            else:
                                raise  # Final attempt failed
                        else:
                            raise  # Not a rate limit error

                if result is None:
                    raise Exception("Discussion failed after retries")

                # Extract messages from result
                messages = result.messages if hasattr(result, 'messages') else []

                # Process each message and stream if SSE available
                for msg in messages:
                    content = ""
                    source = ""

                    if hasattr(msg, 'content'):
                        content = str(msg.content)
                    elif hasattr(msg, 'text'):
                        content = str(msg.text)
                    elif isinstance(msg, dict):
                        content = msg.get('content', '')

                    if hasattr(msg, 'source'):
                        source = str(msg.source)
                    elif hasattr(msg, 'name'):
                        source = str(msg.name)
                    elif isinstance(msg, dict):
                        source = msg.get('source', msg.get('name', ''))

                    # Skip user messages and empty messages
                    if source in ["User", "user"] or not content.strip():
                        continue

                    # Store UNFILTERED message in history (for backend logging)
                    message_data = {
                        'agent': source.lower(),
                        'message': content,
                        'timestamp': datetime.now().isoformat(),
                        'to': 'mimir' if source.lower() == 'plume' else 'plume'
                    }
                    discussion_history.append(message_data)

                    # FILTER message for frontend UI (Layer 2)
                    # Step 1: Replace tool calls with UI-friendly phrases (deterministic)
                    cleaned_content = format_tool_activity_for_ui(content, source.lower())
                    # Step 2: Apply standard filtering (keywords, condensing)
                    filtered_msg = filter_for_ui(source.lower(), cleaned_content)

                    # Stream FILTERED message to SSE if queue exists
                    if sse_queue:
                        await sse_queue.put({
                            'type': 'agent_message',
                            'agent': filtered_msg['agent'],
                            'content': filtered_msg['content'],
                            'action_summary': filtered_msg.get('action_summary'),
                            'timestamp': filtered_msg['timestamp']
                        })

                # Extract final response
                final_response = autogen_discussion._extract_final_response_v4(messages)

                # Calculate usage
                total_tokens = autogen_discussion._estimate_tokens([
                    {'content': m.get('message', '')} for m in discussion_history
                ])
                total_cost = autogen_discussion._calculate_cost(total_tokens)

            else:
                # Fallback to run_discussion function
                from agents.autogen_agents import run_discussion
                discussion_result = await run_discussion(input_text, context, state)

                discussion_history = discussion_result["messages"]
                final_response = discussion_result["final_response"]
                total_tokens = discussion_result.get("total_tokens", 0)
                total_cost = discussion_result.get("total_cost", 0.0)

                # Stream fallback messages if SSE available
                if sse_queue:
                    for msg in discussion_history:
                        await sse_queue.put({
                            'type': 'agent_message',
                            **msg
                        })

            duration_ms = (time.time() - start_time) * 1000

            # Update state
            state["discussion_history"] = discussion_history
            state["final_output"] = final_response

            # Filter messages for HTML display
            # Step 1: Replace tool calls with fixed UI phrases (deterministic)
            # Step 2: Apply additional filtering (keywords, condensing)
            filtered_discussion = []
            for m in discussion_history:
                agent = m['agent']
                message = m['message']

                # Replace tool calls with UI-friendly phrases
                cleaned_message = format_tool_activity_for_ui(message, agent)

                # Apply standard filtering (keywords, etc.)
                filtered_msg = filter_for_ui(agent, cleaned_message)

                filtered_discussion.append({
                    'name': agent.title(),
                    'content': filtered_msg['content']
                })

            # Filter final response
            cleaned_final = format_tool_activity_for_ui(final_response, 'system')
            filtered_final_response = filter_for_ui('system', cleaned_final)['content']

            state["final_html"] = autogen_discussion._generate_discussion_html_v4(
                filtered_discussion,
                filtered_final_response
            )
            state["agents_involved"] = ["plume", "mimir"]

            # Record usage
            add_model_call(state, settings.MODEL_PLUME, total_tokens, total_cost, "discussion", duration_ms)

            # Send processing complete event to SSE if available
            if sse_queue:
                await sse_queue.put({
                    'type': 'processing',
                    'node': 'discussion',
                    'status': 'completed',
                    'timestamp': datetime.now().isoformat()
                })

            agent_logger.log_agent_complete("multi_agent_discussion", duration_ms)
            logger.info("Discussion completed",
                       turns=len(discussion_history),
                       final_response_length=len(final_response))

            return state

        except Exception as e:
            logger.error("Discussion failed", error=str(e))
            error_msg = str(e).lower()

            # User-friendly error message
            if "overloaded" in error_msg or "rate" in error_msg:
                user_error = "🔄 L'API IA est surchargée. Réessaye dans quelques secondes."
            elif "timeout" in error_msg:
                user_error = "⏱️ Le traitement a pris trop de temps. Simplifie ta demande."
            else:
                user_error = f"❌ Erreur : {str(e)}"

            add_error(state, user_error)

            # Send user-friendly error to SSE
            if self._current_sse_queue:
                try:
                    await self._current_sse_queue.put({
                        'type': 'error',
                        'error': user_error,
                        'timestamp': datetime.now().isoformat()
                    })
                except:
                    pass

            # Add fallback response in state
            state["final_output"] = user_error
            state["final_html"] = f"<p>{user_error}</p>"

            # CRITICAL: Set end_time to calculate correct processing_time_ms
            state["end_time"] = datetime.utcnow()
            if state.get("start_time"):
                duration = state["end_time"] - state["start_time"]
                state["processing_time_ms"] = duration.total_seconds() * 1000

            return state

    async def storage_node(self, state: AgentState) -> AgentState:
        """
        Store conversation and results with memory persistence

        WORKS vs ARCHIVES strategy:
        - ALWAYS store in conversations (Works) → 100% chat history
        - CONDITIONALLY create note in Archives → IF create_note tool used OR explicit request
        """
        logger.info("Storing conversation results")

        add_processing_step(state, "storage_operation")

        try:
            if not state.get("should_save", True):
                state["storage_status"] = "skipped"
                return state

            conversation_id = state.get("conversation_id")
            user_id = state.get("user_id", "king_001")

            # ========== WORKS (ALWAYS) ==========
            # Store conversation in Works (conversations table) - 100% of chats

            # Create or get conversation
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                state["conversation_id"] = conversation_id

            # Generate title from user input
            conversation_title = self._generate_title(state.get("input", ""))

            # Check if conversation exists, if not create it
            try:
                existing_conv = await supabase_client.client.table("conversations").select("id").eq("id", conversation_id).execute()

                if not existing_conv.data or len(existing_conv.data) == 0:
                    # Create new conversation entry
                    await supabase_client.client.table("conversations").insert({
                        "id": conversation_id,
                        "user_id": user_id,
                        "title": conversation_title,
                        "message_count": 0,
                        "agents_involved": [state.get("agent_used", "system")],
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }).execute()
                    logger.info("Conversation created in Works", conversation_id=conversation_id, title=conversation_title)
            except Exception as e:
                logger.error("Failed to create conversation", error=str(e))

            # Store user message
            user_message_id = await memory_service.store_message(
                conversation_id=conversation_id,
                role="user",
                content=state.get("input", ""),
                metadata={
                    "session_id": state.get("session_id"),
                    "timestamp": datetime.utcnow().isoformat()
                },
                create_embedding=True
            )

            if user_message_id:
                logger.info("User message stored in Works", message_id=user_message_id)

            # Store agent response
            agent_message_id = await memory_service.store_message(
                conversation_id=conversation_id,
                role=state.get("agent_used", "system"),
                content=state.get("final_output", ""),
                metadata={
                    "processing_time_ms": state.get("processing_time_ms"),
                    "tokens_used": state.get("tokens_used", 0),
                    "cost_eur": state.get("cost_eur", 0.0),
                    "timestamp": datetime.utcnow().isoformat()
                },
                create_embedding=True
            )

            if agent_message_id:
                logger.info("Agent response stored in Works", message_id=agent_message_id)

            # Update conversation message_count
            try:
                await supabase_client.client.table("conversations").update({
                    "message_count": 2,  # user + agent
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", conversation_id).execute()
            except Exception as e:
                logger.error("Failed to update conversation count", error=str(e))

            # ========== ARCHIVES (CONDITIONAL) ==========
            # Only create note in Archives if create_note tool was used OR explicit user request
            if should_create_archive_note({
                "user_input": state.get("input", ""),
                "tools_used": state.get("tools_used", [])  # TODO: Track tools used in state
            }):
                logger.info("Creating note in Archives (create_note tool used or explicit request)")

                # Prepare note data for Archives
                note_data = {
                    "title": self._generate_title(state.get("input", "")),
                    "text_content": state.get("final_output", ""),
                    "html_content": state.get("final_html"),
                    "metadata": {
                        "agent_used": state.get("agent_used"),
                        "agents_involved": state.get("agents_involved", []),
                        "session_id": state.get("session_id"),
                        "conversation_id": conversation_id,
                        "processing_time_ms": state.get("processing_time_ms"),
                        "tokens_used": state.get("tokens_used", 0),
                        "cost_eur": state.get("cost_eur", 0.0),
                        "source": "conversation"
                    },
                    "tags": ["conversation", state.get("agent_used", "unknown")]
                }

                # Store in Archives (notes table)
                start_time = time.time()
                result = await supabase_client.create_note(note_data)
                duration_ms = (time.time() - start_time) * 1000

                if result:
                    state["note_id"] = result["id"]
                    logger.info("Note created in Archives", note_id=result["id"])

                    # Create embeddings for future retrieval
                    asyncio.create_task(self._create_embeddings_async(result["id"], note_data["text_content"]))

            state["storage_status"] = "success"
            return state

        except Exception as e:
            logger.error("Storage failed", error=str(e))
            add_error(state, f"Storage failed: {str(e)}")
            state["storage_status"] = "error"
            return state

    async def finalize_node(self, state: AgentState) -> AgentState:
        """Finalize processing and prepare response"""
        logger.info("Finalizing workflow")

        add_processing_step(state, "workflow_finalization")

        try:
            # Finalize timing
            finalize_state(state)

            # Ensure we have a final output
            if not state.get("final_output"):
                if state.get("errors"):
                    state["final_output"] = "Je suis désolé, une erreur s'est produite lors du traitement de votre demande."
                else:
                    state["final_output"] = "Aucune réponse générée."

            # Set agent used if not set
            if not state.get("agent_used"):
                state["agent_used"] = "system"

            # Extract clickable objects from response (Phase 2.2)
            response = state.get("final_output", "")
            context_ids = state.get("context_ids", [])
            clickable_objects = self._extract_clickable_objects(response, context_ids, state)

            # Enrich metadata with clickable objects
            if not state.get("metadata"):
                state["metadata"] = {}

            state["metadata"]["clickable_objects"] = clickable_objects
            state["metadata"]["processing_time_ms"] = state.get("processing_time_ms", 0)
            state["metadata"]["tokens_used"] = state.get("tokens_used", 0)
            state["metadata"]["cost_eur"] = state.get("cost_eur", 0.0)
            state["metadata"]["agent_used"] = state.get("agent_used", "unknown")
            state["metadata"]["agents_involved"] = state.get("agents_involved", [])

            logger.info("Workflow finalized",
                       processing_time_ms=state.get("processing_time_ms"),
                       tokens_used=state.get("tokens_used", 0),
                       final_output_length=len(state.get("final_output", "")),
                       clickable_objects_count=len(clickable_objects))

            return state

        except Exception as e:
            logger.error("Finalization failed", error=str(e))
            add_error(state, f"Finalization failed: {str(e)}")
            return state

    # =============================================================================
    # DECISION FUNCTIONS
    # =============================================================================

    def intake_decision(self, state: AgentState) -> str:
        """Decide whether to transcribe voice or go directly to routing"""
        if state.get("voice_data"):
            return "transcription"
        return "router"

    def router_decision(self, state: AgentState) -> str:
        """Decide which path to take based on agent selection"""
        if state.get("errors"):
            return "error"

        agent = state.get("agent_used", "auto")

        if agent == "plume":
            return "plume_only"
        elif agent in ["mimir", "discussion"]:
            return agent if agent == "discussion" else "mimir_only"
        else:
            return "error"

    def context_decision(self, state: AgentState) -> str:
        """Decide whether to use Mimir or discussion after context retrieval"""
        agent = state.get("agent_used", "mimir")
        return "discussion" if agent == "discussion" else "mimir"

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    def _extract_clickable_objects(self, response: str, context_note_ids: List[str] = None, state: AgentState = None) -> List[Dict[str, Any]]:
        """
        Extract clickable objects from agent response

        Detects:
        - Created notes (from state.note_id)
        - [[Note Title]] references
        - URLs (web links)
        - Context notes used in RAG

        Args:
            response: Agent response text
            context_note_ids: Note IDs used as context
            state: Agent state (to detect created notes)

        Returns:
            List of clickable object dictionaries
        """
        import re
        objects = []

        try:
            # Pattern 0: Created note (Priority - from tool execution)
            if state and state.get("note_id"):
                created_note_id = state["note_id"]
                try:
                    result = supabase_client.client.table('notes') \
                        .select('id, title') \
                        .eq('id', created_note_id) \
                        .single() \
                        .execute()

                    if result.data:
                        objects.append({
                            'type': 'viz_link',
                            'note_id': result.data['id'],
                            'title': result.data['title']
                        })
                        logger.info("Added created note to clickable_objects", note_id=created_note_id)
                except Exception as e:
                    logger.warning(f"Failed to fetch created note: {created_note_id}", error=str(e))
            # Pattern 1: Explicit note references [[Note Title]]
            note_refs = re.findall(r'\[\[([^\]]+)\]\]', response)
            for title in note_refs:
                try:
                    # Find note by title
                    result = supabase_client.client.table('notes') \
                        .select('id, title') \
                        .eq('title', title) \
                        .eq('user_id', 'king_001') \
                        .limit(1) \
                        .execute()

                    if result.data:
                        objects.append({
                            'type': 'viz_link',
                            'note_id': result.data[0]['id'],
                            'title': result.data[0]['title']
                        })
                except Exception as e:
                    logger.warning(f"Failed to resolve note reference: {title}", error=str(e))

            # Pattern 2: URLs
            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', response)
            for url in urls:
                # Clean trailing punctuation
                url = url.rstrip('.,;:!?)')
                objects.append({
                    'type': 'web_link',
                    'url': url,
                    'title': url.split('/')[2] if len(url.split('/')) > 2 else url  # Extract domain
                })

            # Pattern 3: Context notes (if referenced in conversation)
            if context_note_ids:
                for note_id in context_note_ids:
                    try:
                        result = supabase_client.client.table('notes') \
                            .select('id, title') \
                            .eq('id', note_id) \
                            .single() \
                            .execute()

                        if result.data:
                            # Check if not already added
                            if not any(obj.get('note_id') == note_id for obj in objects):
                                objects.append({
                                    'type': 'viz_link',
                                    'note_id': result.data['id'],
                                    'title': result.data['title']
                                })
                    except Exception as e:
                        logger.warning(f"Failed to get context note: {note_id}", error=str(e))

            logger.debug(f"Extracted {len(objects)} clickable objects from response")

        except Exception as e:
            logger.error("Failed to extract clickable objects", error=str(e))

        return objects

    async def _analyze_input_for_routing(self, input_text: str, state: AgentState = None) -> str:
        """
        Analyze input to determine optimal routing using intent classification

        Args:
            input_text: User input to classify
            state: Current state (for conversation context)

        Returns:
            Agent name: "plume", "mimir", or "discussion"
        """
        try:
            # Get conversation context if available
            conversation_context = state.get("context", []) if state else None

            # Classify intent
            classification = await intent_classifier.classify(
                input_text=input_text,
                conversation_context=conversation_context
            )

            intent = classification["intent"]
            confidence = classification["confidence"]
            reasoning = classification["reasoning"]

            logger.info(
                "Intent classification for routing",
                intent=intent,
                confidence=confidence,
                reasoning=reasoning,
                method=classification.get("method")
            )

            # Map intent to agent
            intent_to_agent = {
                "restitution": "plume",
                "recherche": "mimir",
                "discussion": "discussion"
            }

            agent = intent_to_agent.get(intent, "plume")

            # Store classification result in state for debugging/monitoring
            if state:
                if "routing_metadata" not in state:
                    state["routing_metadata"] = {}
                state["routing_metadata"]["classification"] = classification

            logger.info(
                "Routing decision",
                agent=agent,
                intent=intent,
                confidence=confidence
            )

            return agent

        except Exception as e:
            logger.warning("Failed to analyze input for routing, defaulting to Plume", error=str(e))
            return "plume"

    def _generate_title(self, input_text: str, max_length: int = 50) -> str:
        """Generate a title from input text"""
        # Clean and truncate
        title = input_text.strip()
        if len(title) > max_length:
            title = title[:max_length-3] + "..."

        # Remove line breaks
        title = title.replace('\n', ' ').replace('\r', ' ')

        return title or "Conversation"

    async def _create_embeddings_async(self, note_id: str, content: str):
        """Create embeddings for stored note (async background task)"""
        try:
            await embedding_service.create_embeddings_for_note(note_id, content)
            logger.info("Embeddings created for note", note_id=note_id)
        except Exception as e:
            logger.error("Failed to create embeddings", note_id=note_id, error=str(e))

    # =============================================================================
    # PUBLIC INTERFACE
    # =============================================================================

    async def process(
        self,
        input_text: str,
        mode: str = "auto",
        voice_data: Optional[str] = None,
        audio_format: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        context_ids: Optional[List[str]] = None,
        _sse_queue: Optional[asyncio.Queue] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing user input with conversation memory

        Args:
            input_text: User input message
            mode: Routing mode (auto, plume, mimir, discussion)
            voice_data: Base64 audio data if voice input
            audio_format: Audio format (webm, mp3, etc.)
            session_id: Session identifier for checkpointing
            conversation_id: Conversation ID for memory context
            user_id: User ID for preferences and long-term memory
            context_ids: Specific document IDs to use as context
            _sse_queue: Optional asyncio.Queue for SSE streaming

        Returns:
            Response dictionary with agent output and metadata
        """

        if not self._initialized:
            await self.initialize()

        # Create initial state
        from agents.state import create_initial_state
        initial_state = create_initial_state(
            input_text=input_text,
            mode=mode,
            voice_data=voice_data,
            audio_format=audio_format,
            session_id=session_id,
            conversation_id=conversation_id,
            user_id=user_id,
            context_ids=context_ids
        )

        # Store SSE queue as instance variable (not in state to avoid msgpack serialization)
        self._current_sse_queue = _sse_queue

        try:
            # Run the workflow
            config = {"configurable": {"thread_id": session_id or "default"}}
            final_state = await self.app.ainvoke(initial_state, config)

            # Return formatted response
            return {
                "response": final_state.get("final_output", ""),
                "html": final_state.get("final_html"),
                "agent_used": final_state.get("agent_used", "unknown"),
                "agents_involved": final_state.get("agents_involved", []),
                "discussion_history": final_state.get("discussion_history", []),
                "session_id": final_state.get("session_id"),
                "note_id": final_state.get("note_id"),
                "processing_time_ms": final_state.get("processing_time_ms", 0),
                "tokens_used": final_state.get("tokens_used", 0),
                "cost_eur": final_state.get("cost_eur", 0.0),
                "errors": final_state.get("errors", []),
                "warnings": final_state.get("warnings", []),
                "metadata": final_state.get("metadata", {}),  # Phase 2.2: include metadata with clickable objects
                "ui_metadata": final_state.get("ui_metadata", {})  # User-friendly formatted metadata
            }

        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            return {
                "response": "Une erreur s'est produite lors du traitement de votre demande.",
                "html": None,
                "agent_used": "error",
                "agents_involved": [],
                "session_id": session_id,
                "note_id": None,
                "processing_time_ms": 0,
                "tokens_used": 0,
                "cost_eur": 0.0,
                "errors": [{"message": str(e), "timestamp": datetime.utcnow()}],
                "warnings": []
            }
        finally:
            # Clean up SSE queue reference
            self._current_sse_queue = None

# Global orchestrator instance
orchestrator = PlumeOrchestrator()