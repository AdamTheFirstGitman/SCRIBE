"""
Agent State Management for Plume & Mimir
TypedDict definitions for LangGraph workflow state
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime

# =============================================================================
# AGENT STATE DEFINITIONS
# =============================================================================

class AgentState(TypedDict, total=False):
    """
    Main state object passed between LangGraph nodes
    Contains all information needed for the conversation workflow
    """

    # Input and mode
    input: str                              # User input (text or transcribed)
    mode: Literal["auto", "plume", "mimir", "discussion"]  # Agent selection mode
    voice_data: Optional[str]               # Base64 audio data if voice input
    audio_format: Optional[str]             # Audio format (webm, mp3, etc.)

    # Context and metadata
    context: List[Dict[str, Any]]          # Retrieved context documents
    context_ids: List[str]                 # IDs of documents used as context
    session_id: Optional[str]              # Session identifier
    conversation_id: Optional[str]         # Conversation identifier
    user_id: Optional[str]                 # User identifier for memory/preferences
    user_metadata: Dict[str, Any]          # User-specific metadata

    # Memory context (loaded by memory_service)
    recent_messages: List[Dict[str, Any]]  # Recent conversation messages
    similar_past_conversations: List[Dict[str, Any]]  # Similar past conversations
    user_preferences: Dict[str, Any]       # User preferences
    conversation_summary: str              # Current conversation topic summary
    routing_metadata: Dict[str, Any]       # Intent classification metadata

    # Agent responses
    plume_response: Optional[str]          # Response from Plume agent
    mimir_response: Optional[str]          # Response from Mimir agent
    discussion_history: List[Dict[str, Any]]  # AutoGen discussion messages

    # Final output
    final_output: str                      # Final response to user
    final_html: Optional[str]              # HTML formatted response
    agent_used: str                        # Which agent generated final response
    agents_involved: List[str]             # All agents that participated

    # Processing metadata
    processing_steps: List[str]            # Steps taken in processing
    start_time: datetime                   # When processing started
    end_time: Optional[datetime]           # When processing completed
    processing_time_ms: Optional[float]    # Total processing time

    # Storage and persistence
    storage_status: Optional[str]          # Status of storage operation
    note_id: Optional[str]                # ID of created/updated note
    should_save: bool                      # Whether to save to database
    save_metadata: Dict[str, Any]         # Metadata for saving

    # Error handling
    errors: List[Dict[str, Any]]          # Any errors encountered
    warnings: List[str]                   # Non-fatal warnings
    retry_count: int                      # Number of retries attempted

    # Costs and usage
    tokens_used: int                      # Total tokens consumed
    cost_eur: float                       # Estimated cost in EUR
    model_calls: List[Dict[str, Any]]     # Details of all model calls

    # Search and retrieval
    search_results: List[Dict[str, Any]]  # RAG search results
    search_query: Optional[str]           # Query used for search
    search_type: Optional[str]            # Type of search performed
    similarity_scores: List[float]        # Similarity scores for results

class TranscriptionState(TypedDict, total=False):
    """State for audio transcription workflow"""

    audio_data: str                       # Base64 encoded audio
    audio_format: str                     # Audio format
    audio_duration: Optional[float]       # Duration in seconds

    transcription_text: str               # Transcribed text
    transcription_confidence: float       # Confidence score
    transcription_language: Optional[str] # Detected language

    processing_time_ms: float             # Transcription processing time
    cached: bool                          # Whether result was cached

class SearchState(TypedDict, total=False):
    """State for search and retrieval workflow"""

    query: str                           # Search query
    query_embedding: Optional[List[float]]  # Query embedding vector
    search_type: Literal["vector", "fulltext", "hybrid"]  # Search method

    results: List[Dict[str, Any]]        # Search results
    total_found: int                     # Total number of results
    similarity_threshold: float          # Minimum similarity score
    limit: int                          # Maximum results to return

    processing_time_ms: float           # Search processing time
    cached: bool                        # Whether results were cached

class StorageState(TypedDict, total=False):
    """State for storage operations"""

    operation: Literal["create", "update", "delete", "retrieve"]  # Operation type
    note_data: Dict[str, Any]           # Note data to store
    note_id: Optional[str]              # ID of note being operated on

    success: bool                       # Whether operation succeeded
    result: Optional[Dict[str, Any]]    # Operation result
    error: Optional[str]                # Error message if failed

class ConversationState(TypedDict, total=False):
    """State for conversation management"""

    messages: List[Dict[str, Any]]      # Conversation messages
    session_id: str                     # Session identifier
    conversation_id: Optional[str]      # Conversation identifier

    agents_involved: List[str]          # Agents in conversation
    turn_count: int                     # Number of turns

    created_at: datetime                # When conversation started
    updated_at: datetime                # Last update time

# =============================================================================
# STATE HELPERS AND UTILITIES
# =============================================================================

def create_initial_state(
    input_text: str,
    mode: str = "auto",
    voice_data: Optional[str] = None,
    audio_format: Optional[str] = None,
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    context_ids: Optional[List[str]] = None
) -> AgentState:
    """Create initial state for workflow"""

    return AgentState(
        # Input
        input=input_text,
        mode=mode,  # type: ignore
        voice_data=voice_data,
        audio_format=audio_format,

        # Context
        context=[],
        context_ids=context_ids or [],
        session_id=session_id,
        conversation_id=conversation_id,
        user_id=user_id,
        user_metadata={},

        # Memory context (will be loaded by memory_service in intake_node)
        recent_messages=[],
        similar_past_conversations=[],
        user_preferences={},
        conversation_summary="",
        routing_metadata={},

        # Responses (will be filled during workflow)
        plume_response=None,
        mimir_response=None,
        discussion_history=[],

        # Output (will be set at end)
        final_output="",
        final_html=None,
        agent_used="",
        agents_involved=[],

        # Processing
        processing_steps=[],
        start_time=datetime.utcnow(),
        end_time=None,
        processing_time_ms=None,

        # Storage
        storage_status=None,
        note_id=None,
        should_save=True,  # Default to saving
        save_metadata={},

        # Error handling
        errors=[],
        warnings=[],
        retry_count=0,

        # Costs
        tokens_used=0,
        cost_eur=0.0,
        model_calls=[],

        # Search
        search_results=[],
        search_query=None,
        search_type=None,
        similarity_scores=[]
    )

def add_processing_step(state: AgentState, step: str) -> AgentState:
    """Add a processing step to the state"""
    state["processing_steps"].append(step)
    return state

def add_error(state: AgentState, error: str, context: Optional[Dict[str, Any]] = None) -> AgentState:
    """Add an error to the state"""
    error_entry = {
        "message": error,
        "timestamp": datetime.utcnow(),
        "context": context or {}
    }
    state["errors"].append(error_entry)
    return state

def add_warning(state: AgentState, warning: str) -> AgentState:
    """Add a warning to the state"""
    state["warnings"].append(warning)
    return state

def add_model_call(
    state: AgentState,
    model: str,
    tokens: int,
    cost: float,
    agent: str,
    duration_ms: float
) -> AgentState:
    """Record a model call in the state"""
    call_info = {
        "model": model,
        "tokens": tokens,
        "cost_eur": cost,
        "agent": agent,
        "duration_ms": duration_ms,
        "timestamp": datetime.utcnow()
    }

    state["model_calls"].append(call_info)
    state["tokens_used"] += tokens
    state["cost_eur"] += cost

    return state

def finalize_state(state: AgentState) -> AgentState:
    """Finalize the state at end of processing"""
    state["end_time"] = datetime.utcnow()

    if state["start_time"] and state["end_time"]:
        duration = state["end_time"] - state["start_time"]
        state["processing_time_ms"] = duration.total_seconds() * 1000

    # Generate UI-friendly metadata (human-readable vs technical)
    from utils.ui_message_formatter import get_metrics_summary
    state["ui_metadata"] = get_metrics_summary(state)

    return state

def get_state_summary(state: AgentState) -> Dict[str, Any]:
    """Get a summary of the current state for logging"""
    return {
        "input_length": len(state.get("input", "")),
        "mode": state.get("mode"),
        "agents_involved": state.get("agents_involved", []),
        "processing_steps": len(state.get("processing_steps", [])),
        "errors": len(state.get("errors", [])),
        "warnings": len(state.get("warnings", [])),
        "tokens_used": state.get("tokens_used", 0),
        "cost_eur": state.get("cost_eur", 0.0),
        "processing_time_ms": state.get("processing_time_ms"),
        "has_context": len(state.get("context", [])) > 0,
        "should_save": state.get("should_save", False)
    }