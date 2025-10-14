"""
Message Filtering Layer - Transform backend processing → frontend UX
Implements 2-layer architecture: complete backend processing + clean UI display
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

class MessageFilter:
    """
    Filter and transform backend messages for optimal frontend UX

    Philosophy:
    - Backend: Complete, detailed, logged
    - Frontend: Concise, user-friendly, WhatsApp-style
    """

    # Internal keywords to filter out from UI
    INTERNAL_KEYWORDS = [
        "reasoning:", "thinking:", "internal:", "debug:",
        "context_summary:", "tool_execution:", "processing_step:",
        "function_call:", "tool_params:", "raw_result:"
    ]

    # Tool call patterns that should be hidden
    TOOL_CALL_PATTERNS = [
        r'\[TOOL_START:.*?\]',
        r'\[TOOL_END:.*?\]',
        r'Tool params:.*?(?=\n|$)',  # Tool params line
        r'\{.*?"function":\s*".*?".*?\}',
        r'<tool_.*?>.*?</tool_.*?>',
        # Python dicts from tool returns (common patterns)
        r'\{\s*[\'"]success[\'"]\s*:\s*\w+.*?\}',
        r'\{\s*[\'"]results[\'"]\s*:\s*\[.*?\].*?\}',
        r'\{\s*[\'"]error[\'"]\s*:\s*.*?\}',
        r'\{\s*[\'"]count[\'"]\s*:\s*\d+.*?\}',
        r'\{\s*[\'"]note_id[\'"]\s*:\s*.*?\}',
    ]

    @classmethod
    def filter_agent_message(
        cls,
        agent_name: str,
        raw_message: str,
        message_type: str = "response"
    ) -> Dict[str, Any]:
        """
        Filter agent message for frontend display

        Args:
            agent_name: "plume" or "mimir"
            raw_message: Full backend message (may contain internal content)
            message_type: "response", "thinking", "tool_call", etc.

        Returns:
            Filtered message dict with UI-optimized content
        """

        # Step 1: Remove internal content blocks
        cleaned = cls._remove_internal_blocks(raw_message)

        # Step 2: Remove tool call syntax
        cleaned = cls._remove_tool_calls(cleaned)

        # Step 3: Condense if too long
        cleaned = cls._condense_message(cleaned, max_length=500)

        # Step 4: Extract action summary if present
        action_summary = cls._extract_action_summary(raw_message)

        return {
            "agent": agent_name,
            "content": cleaned.strip(),
            "action_summary": action_summary,
            "timestamp": datetime.now().isoformat(),
            "filtered": True
        }

    @classmethod
    def _remove_internal_blocks(cls, text: str) -> str:
        """Remove content marked as internal/debug"""

        # Remove lines/parts starting with internal keywords
        lines = text.split('\n')
        filtered_lines = []

        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            # Check if line starts with internal keyword
            starts_with_internal = any(line_lower.startswith(kw) for kw in cls.INTERNAL_KEYWORDS)

            if starts_with_internal:
                # Try to extract part AFTER keyword (same line)
                found_after = False
                for kw in cls.INTERNAL_KEYWORDS:
                    if line_lower.startswith(kw):
                        # Extract part after keyword
                        after_kw = line_stripped[len(kw):].strip()
                        if after_kw:
                            filtered_lines.append(after_kw)
                        found_after = True
                        break
                # If nothing after keyword, skip line entirely
                continue

            # If line contains internal keyword mid-sentence (not at start)
            has_internal_mid = False
            for kw in cls.INTERNAL_KEYWORDS:
                if kw in line_lower and not line_lower.startswith(kw):
                    # Find keyword position (case insensitive)
                    kw_pos = line_lower.find(kw)
                    # Extract part after keyword
                    after_kw = line_stripped[kw_pos + len(kw):].strip()
                    if after_kw:
                        filtered_lines.append(after_kw)
                    has_internal_mid = True
                    break

            if not has_internal_mid and not starts_with_internal:
                # Keep line as-is if no internal keywords
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    @classmethod
    def _remove_tool_calls(cls, text: str) -> str:
        """Remove tool call syntax from text"""

        cleaned = text
        for pattern in cls.TOOL_CALL_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)

        return cleaned

    @classmethod
    def _condense_message(cls, text: str, max_length: int = 500) -> str:
        """
        Condense long messages while preserving essential info

        Strategy: Keep first 300 chars + last 200 chars if exceeds limit
        """

        text = text.strip()

        if len(text) <= max_length:
            return text

        # Keep beginning and end, add ellipsis
        beginning = text[:300].rsplit(' ', 1)[0] if ' ' in text[:300] else text[:300]
        ending = text[-190:].split(' ', 1)[1] if ' ' in text[-190:] else text[-190:]

        return f"{beginning} [...] {ending}"

    @classmethod
    def _extract_action_summary(cls, raw_message: str) -> Optional[str]:
        """
        Extract action summary for tool activities

        Example: "J'ai recherché dans les archives et trouvé 5 résultats pertinents"
        """

        # Look for summary patterns
        summary_patterns = [
            r"(?:En résumé|Pour résumer|J'ai)\s*:\s*(.+?)(?:\n|$)",
            r"(?:Action effectuée|Résultat)\s*:\s*(.+?)(?:\n|$)",
        ]

        for pattern in summary_patterns:
            match = re.search(pattern, raw_message, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()

        return None


class ToolActivityFilter:
    """
    Filter tool activities for clean UI display
    Transforms detailed backend tool calls → user-friendly badges
    """

    # UI-friendly tool labels (French)
    TOOL_LABELS = {
        "search_knowledge": "🔍 Recherche archives",
        "web_search": "🌐 Recherche web",
        "get_related_content": "🔗 Contenus similaires",
        "create_note": "📝 Création note",
        "update_note": "✏️ Mise à jour note"
    }

    @classmethod
    def filter_tool_activity(
        cls,
        tool_name: str,
        tool_params: Dict[str, Any],
        tool_result: Optional[Dict[str, Any]] = None,
        status: str = "running"
    ) -> Dict[str, Any]:
        """
        Transform backend tool activity → UI-friendly representation

        Args:
            tool_name: Raw tool name (e.g., "search_knowledge")
            tool_params: Full tool parameters (may be verbose)
            tool_result: Tool execution result
            status: "running", "completed", "failed"

        Returns:
            Filtered activity for frontend display
        """

        return {
            "tool": tool_name,
            "label": cls.TOOL_LABELS.get(tool_name, tool_name),
            "status": status,
            "summary": cls._generate_tool_summary(tool_name, tool_params, tool_result),
            "timestamp": datetime.now().isoformat()
        }

    @classmethod
    def _generate_tool_summary(
        cls,
        tool_name: str,
        params: Dict[str, Any],
        result: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate concise summary of tool execution

        Examples:
        - search_knowledge → "5 résultats"
        - create_note → "Note créée"
        - web_search → "3 sources"
        """

        if tool_name == "search_knowledge":
            if result and "results_count" in result:
                count = result["results_count"]
                return f"{count} résultat{'s' if count > 1 else ''}"
            return "Recherche en cours..."

        elif tool_name == "web_search":
            if result and "sources_count" in result:
                count = result["sources_count"]
                return f"{count} source{'s' if count > 1 else ''}"
            return "Recherche en cours..."

        elif tool_name == "get_related_content":
            if result and "related_count" in result:
                count = result["related_count"]
                return f"{count} connexion{'s' if count > 1 else ''}"
            return "Analyse en cours..."

        elif tool_name == "create_note":
            if result and result.get("success"):
                return "Note créée"
            return "Création en cours..."

        elif tool_name == "update_note":
            if result and result.get("success"):
                return "Note mise à jour"
            return "Mise à jour en cours..."

        return "En cours..."


class ConversationStorageFilter:
    """
    Determine where to store conversation outcomes

    Rules:
    - Works (conversations table): ALL conversations with agents (chat history)
    - Archives (notes table): ONLY when create_note tool explicitly used

    Important: Works and Archives are SEPARATE spaces, no overlap
    - Works = Chat interface with agents (/chat)
    - Archives = Viz Page with consolidated notes (/archives, /viz/:id)
    """

    @classmethod
    def should_create_archive_note(cls, conversation_data: Dict[str, Any]) -> bool:
        """
        Determine if a note should be created in Archives

        Archives notes are ONLY created when:
        1. Agent explicitly used create_note tool (PRIMARY signal)
        2. User explicitly requested "crée une note" / "archive"

        NOT created for:
        - Regular chat conversations (go to Works only)
        - Questions/answers without explicit archiving
        - Tool searches (search_knowledge) without note creation
        """

        # Check if agents used create_note tool (PRIMARY signal)
        tools_used = conversation_data.get("tools_used", [])
        if "create_note" in tools_used:
            return True

        # Check for explicit archive intent from user
        user_input = conversation_data.get("user_input", "").lower()
        archive_keywords = ["crée une note", "créer une note", "archive", "sauvegarde"]

        if any(keyword in user_input for keyword in archive_keywords):
            return True

        return False


# Convenience functions for quick filtering

def filter_for_ui(agent_name: str, backend_message: str) -> Dict[str, Any]:
    """Quick filter backend message for UI display"""
    return MessageFilter.filter_agent_message(agent_name, backend_message)


def filter_tool_for_ui(tool_name: str, params: Dict, result: Optional[Dict] = None, status: str = "running") -> Dict[str, Any]:
    """Quick filter tool activity for UI display"""
    return ToolActivityFilter.filter_tool_activity(tool_name, params, result, status)


def should_create_archive_note(conversation_data: Dict[str, Any]) -> bool:
    """
    Quick check if conversation should create an Archive note

    Returns True ONLY if create_note tool was used or explicit user request

    Usage:
        if should_create_archive_note(data):
            # Create note in Archives (notes table)
            await supabase_client.create_note(...)

        # Always store conversation in Works (conversations table)
        await memory_service.store_message(...)
    """
    return ConversationStorageFilter.should_create_archive_note(conversation_data)
