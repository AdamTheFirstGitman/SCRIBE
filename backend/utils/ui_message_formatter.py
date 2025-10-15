"""
UI Message Formatter - Backend technical info → User-friendly messages
Implements the principle: "Backend ≠ Frontend in terms of user relevance"
"""

from typing import Dict, Any, List, Optional

def format_context_info(context: List[Dict[str, Any]], short_term_messages: int = 0) -> str:
    """
    #6 Memory/Context humanisé

    Transform technical context retrieval → human-friendly message

    Backend sees:
    - Short-term: 3 messages from session_abc123
    - Long-term: 12 documents retrieved (RAG)
    - Checkpoint state_def456 restored

    User sees:
    💭 Je me rappelle de nos 3 derniers échanges
    └─ 12 notes liées trouvées dans vos archives
    """
    if not context and not short_term_messages:
        return ""

    parts = []

    if short_term_messages > 0:
        if short_term_messages == 1:
            parts.append(f"💭 Je me rappelle de notre dernier échange")
        else:
            parts.append(f"💭 Je me rappelle de nos {short_term_messages} derniers échanges")

    if context:
        count = len(context)
        if count == 1:
            parts.append(f"└─ 1 note liée trouvée dans vos archives")
        else:
            parts.append(f"└─ {count} notes liées trouvées dans vos archives")

    return "\n".join(parts)


def format_processing_time(ms: float, show_details: bool = False) -> str:
    """
    #4 Processing time simplifié

    Transform: "Processing: 25624ms, Tokens: 1928, Cost: 0.0798€"
    Into: "⏱️ Réponse en 26s" (with optional [Voir détails])
    """
    seconds = ms / 1000

    if seconds < 1:
        time_str = f"{int(ms)}ms"
    elif seconds < 60:
        time_str = f"{int(seconds)}s"
    else:
        minutes = int(seconds / 60)
        remaining_secs = int(seconds % 60)
        time_str = f"{minutes}min {remaining_secs}s"

    if show_details:
        return f"⏱️ Réponse en {time_str} [Voir détails ↓]"
    else:
        return f"⏱️ Réponse en {time_str}"


def format_rag_sources(context: List[Dict[str, Any]], collapsed: bool = True) -> str:
    """
    #1 RAG Context avec [Voir sources] expandable

    Transform technical RAG results with scores/embeddings
    Into: "🔍 5 documents trouvés [Voir sources ↓]"
    """
    if not context:
        return ""

    count = len(context)

    if collapsed:
        if count == 1:
            return "🔍 1 document trouvé dans les archives [Voir source ↓]"
        else:
            return f"🔍 {count} documents trouvés dans les archives [Voir sources ↓]"
    else:
        # Expanded version with source list
        lines = [f"🔍 {count} documents trouvés:"]
        for i, doc in enumerate(context[:5], 1):  # Limit to top 5
            title = doc.get('title', 'Document sans titre')
            score = doc.get('score', 0)
            lines.append(f"  {i}. {title} (pertinence: {score:.0%})")

        if count > 5:
            lines.append(f"  ... et {count - 5} autres")

        return "\n".join(lines)


def format_discussion_timeline(messages: List[Dict[str, Any]], collapsed: bool = True) -> str:
    """
    #5 Discussion history avec timeline

    Transform verbose agent dialogue
    Into: Timeline of actions (collapsed by default)

    Timeline:
    15:23 🧠 Recherche lancée
    15:24 ✅ 5 sources trouvées
    15:24 🖋️ Rédaction en cours
    15:25 ✅ Note créée
    """
    if not messages:
        return ""

    if collapsed:
        agent_count = len(set(m.get('agent', '') for m in messages))
        turn_count = len(messages)
        return f"💬 Discussion ({turn_count} échanges, {agent_count} agents) [Voir conversation ↓]"
    else:
        # Expanded timeline
        lines = ["💬 Timeline de la discussion:"]
        for msg in messages:
            agent = msg.get('agent', 'Unknown')
            content = msg.get('content', '')[:60]  # Truncate
            timestamp = msg.get('timestamp', '')[:5]  # HH:MM only

            icon = "🖋️" if agent.lower() == "plume" else "🧠"
            lines.append(f"{timestamp} {icon} {agent}: {content}...")

        return "\n".join(lines)


def format_error_message(error: str, technical_details: bool = False) -> str:
    """
    #3 (pour plus tard) Error handling user-friendly

    Transform: "SupabaseConnectionError: Connection timeout after 30s at line 142"
    Into: "⚠️ Problème de connexion aux archives"
    """
    # Map technical errors to user-friendly messages
    error_map = {
        'Supabase': '⚠️ Problème de connexion aux archives',
        'Connection': '⚠️ Problème de connexion',
        'Timeout': '⚠️ Le traitement prend trop de temps',
        'API': '⚠️ Service temporairement indisponible',
        'Token': '⚠️ Limite de traitement atteinte',
    }

    # Find matching error type
    for key, friendly_msg in error_map.items():
        if key.lower() in error.lower():
            if technical_details:
                return f"{friendly_msg}\n[Détails techniques ↓]\n{error}"
            else:
                return f"{friendly_msg}\n[Réessayer] [Détails ↓]"

    # Generic fallback
    if technical_details:
        return f"⚠️ Une erreur s'est produite\n{error}"
    else:
        return "⚠️ Une erreur s'est produite\n[Réessayer] [Détails ↓]"


def get_metrics_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metrics from state and format for UI

    Returns:
    {
        'processing_time': '26s',
        'context_info': '💭 3 échanges + 12 notes',
        'sources_found': '🔍 5 documents',
        'detailed_metrics': {  # For expandable details
            'tokens': 1928,
            'cost_eur': 0.0798,
            'processing_time_ms': 25624
        }
    }
    """
    processing_time_ms = state.get('processing_time_ms', 0)
    context = state.get('context', [])
    total_tokens = state.get('tokens_used', 0)
    total_cost = state.get('cost_eur', 0.0)

    return {
        'processing_time': format_processing_time(processing_time_ms, show_details=False),
        'context_info': format_context_info(context),
        'sources_found': format_rag_sources(context, collapsed=True),
        'detailed_metrics': {
            'tokens': total_tokens,
            'cost_eur': total_cost,
            'processing_time_ms': processing_time_ms
        }
    }
