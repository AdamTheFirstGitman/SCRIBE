"""
LangGraph Orchestrator for Plume & Mimir
Main workflow coordinator that routes between agents
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState, add_processing_step, add_error, add_model_call, finalize_state
from ..services.transcription import transcription_service
from ..services.embeddings import embedding_service
from ..services.rag import rag_service
from ..services.storage import supabase_client
from ..services.cache import cache_manager
from ..utils.logger import get_agent_logger, get_logger

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

    async def initialize(self):
        """Initialize the orchestrator and compile the workflow"""
        if self._initialized:
            return

        logger.info("Initializing Plume & Mimir orchestrator")

        try:
            # Build the workflow graph
            self.graph = self._build_graph()

            # Compile the workflow with memory
            memory = MemorySaver()
            self.app = self.graph.compile(checkpointer=memory)

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
        """Initial processing of user input"""
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
        """Route to appropriate agent based on input and mode"""
        logger.info("Routing request", mode=state.get("mode", "auto"))

        add_processing_step(state, "routing_decision")

        try:
            input_text = state.get("input", "")
            mode = state.get("mode", "auto")

            # Explicit mode selection
            if mode == "plume":
                state["agent_used"] = "plume"
                logger.info("Routed to Plume (explicit)")
                return state

            elif mode == "mimir":
                state["agent_used"] = "mimir"
                logger.info("Routed to Mimir (explicit)")
                return state

            elif mode == "discussion":
                state["agent_used"] = "discussion"
                logger.info("Routed to Discussion (explicit)")
                return state

            # Auto-routing logic
            elif mode == "auto":
                # Analyze input to decide routing
                routing_decision = await self._analyze_input_for_routing(input_text)

                state["agent_used"] = routing_decision
                logger.info("Auto-routed", decision=routing_decision)
                return state

            else:
                add_error(state, f"Unknown mode: {mode}")
                return state

        except Exception as e:
            logger.error("Routing failed", error=str(e))
            add_error(state, f"Routing failed: {str(e)}")
            return state

    async def context_retrieval_node(self, state: AgentState) -> AgentState:
        """Retrieve relevant context for Mimir or discussion"""
        logger.info("Retrieving context for knowledge-based response")

        add_processing_step(state, "context_retrieval")

        try:
            query = state.get("input", "")
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

        try:
            from .plume import plume_agent
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

            agent_logger.log_agent_complete("restitution_task", duration_ms)
            logger.info("Plume processing completed", response_length=len(response["content"]))

            return state

        except Exception as e:
            logger.error("Plume processing failed", error=str(e))
            add_error(state, f"Plume processing failed: {str(e)}")
            return state

    async def mimir_node(self, state: AgentState) -> AgentState:
        """Mimir agent - Knowledge archiving and retrieval"""
        agent_logger = get_agent_logger("mimir", state.get("session_id"))
        agent_logger.log_agent_start("knowledge_task")

        add_processing_step(state, "mimir_processing")

        try:
            from .mimir import mimir_agent
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

            agent_logger.log_agent_complete("knowledge_task", duration_ms)
            logger.info("Mimir processing completed", response_length=len(response["content"]))

            return state

        except Exception as e:
            logger.error("Mimir processing failed", error=str(e))
            add_error(state, f"Mimir processing failed: {str(e)}")
            return state

    async def discussion_node(self, state: AgentState) -> AgentState:
        """AutoGen discussion between Plume and Mimir"""
        agent_logger = get_agent_logger("discussion", state.get("session_id"))
        agent_logger.log_agent_start("multi_agent_discussion")

        add_processing_step(state, "autogen_discussion")

        try:
            from .autogen_agents import run_discussion
            input_text = state.get("input", "")
            context = state.get("context", [])

            start_time = time.time()
            discussion_result = await run_discussion(input_text, context, state)
            duration_ms = (time.time() - start_time) * 1000

            # Update state
            state["discussion_history"] = discussion_result["messages"]
            state["final_output"] = discussion_result["final_response"]
            state["final_html"] = discussion_result.get("html")
            state["agents_involved"] = ["plume", "mimir"]

            # Record usage
            total_tokens = discussion_result.get("total_tokens", 0)
            total_cost = discussion_result.get("total_cost", 0.0)
            add_model_call(state, "claude-3-opus", total_tokens, total_cost, "discussion", duration_ms)

            agent_logger.log_agent_complete("multi_agent_discussion", duration_ms)
            logger.info("Discussion completed",
                       turns=len(discussion_result["messages"]),
                       final_response_length=len(discussion_result["final_response"]))

            return state

        except Exception as e:
            logger.error("Discussion failed", error=str(e))
            add_error(state, f"AutoGen discussion failed: {str(e)}")
            return state

    async def storage_node(self, state: AgentState) -> AgentState:
        """Store conversation and results"""
        logger.info("Storing conversation results")

        add_processing_step(state, "storage_operation")

        try:
            if not state.get("should_save", True):
                state["storage_status"] = "skipped"
                return state

            # Prepare note data
            note_data = {
                "title": self._generate_title(state.get("input", "")),
                "content": state.get("final_output", ""),
                "html": state.get("final_html"),
                "metadata": {
                    "agent_used": state.get("agent_used"),
                    "agents_involved": state.get("agents_involved", []),
                    "session_id": state.get("session_id"),
                    "processing_time_ms": state.get("processing_time_ms"),
                    "tokens_used": state.get("tokens_used", 0),
                    "cost_eur": state.get("cost_eur", 0.0),
                    "source": "conversation"
                },
                "tags": ["conversation", state.get("agent_used", "unknown")]
            }

            # Store in database
            start_time = time.time()
            result = await supabase_client.create_note(note_data)
            duration_ms = (time.time() - start_time) * 1000

            if result:
                state["note_id"] = result["id"]
                state["storage_status"] = "success"
                logger.info("Note stored successfully", note_id=result["id"])

                # Create embeddings for future retrieval
                asyncio.create_task(self._create_embeddings_async(result["id"], note_data["content"]))

            else:
                state["storage_status"] = "failed"
                add_error(state, "Failed to store note")

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

            logger.info("Workflow finalized",
                       processing_time_ms=state.get("processing_time_ms"),
                       tokens_used=state.get("tokens_used", 0),
                       final_output_length=len(state.get("final_output", "")))

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

    async def _analyze_input_for_routing(self, input_text: str) -> str:
        """Analyze input to determine optimal routing"""
        try:
            # Simple heuristics for now (could be enhanced with ML)
            lower_input = input_text.lower()

            # Questions typically go to Mimir for knowledge retrieval
            question_indicators = ["?", "comment", "pourquoi", "qu'est", "que", "qui", "où", "quand", "combien"]
            if any(indicator in lower_input for indicator in question_indicators):
                return "mimir"

            # Complex topics might benefit from discussion
            complex_indicators = ["expliquer", "analyser", "comparer", "différence", "avantages", "inconvénients"]
            if any(indicator in lower_input for indicator in complex_indicators) and len(input_text) > 100:
                return "discussion"

            # Default to Plume for simple restitution
            return "plume"

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
        context_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Main entry point for processing user input"""

        if not self._initialized:
            await self.initialize()

        # Create initial state
        from .state import create_initial_state
        initial_state = create_initial_state(
            input_text=input_text,
            mode=mode,
            voice_data=voice_data,
            audio_format=audio_format,
            session_id=session_id,
            context_ids=context_ids
        )

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
                "session_id": final_state.get("session_id"),
                "note_id": final_state.get("note_id"),
                "processing_time_ms": final_state.get("processing_time_ms", 0),
                "tokens_used": final_state.get("tokens_used", 0),
                "cost_eur": final_state.get("cost_eur", 0.0),
                "errors": final_state.get("errors", []),
                "warnings": final_state.get("warnings", [])
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

# Global orchestrator instance
orchestrator = PlumeOrchestrator()