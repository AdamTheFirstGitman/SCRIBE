"""
Tool Message Formatter - Convert technical tool calls to UI-friendly messages
Deterministic approach: Tool calls = structured events → fixed UI phrases
"""

import re
from typing import Dict, Any, Optional, List

# Mapping: tool name → UI display phrase
TOOL_DISPLAY_MAP = {
    'search_knowledge': '🔍 Recherche dans les archives...',
    'web_search': '🌐 Exploration du web...',
    'create_note': '✍️ Note créée avec succès',
    'update_note': '📝 Note mise à jour',
    'get_related_content': '🔗 Recherche de contenus liés...',
}

def detect_tool_name(text: str) -> Optional[str]:
    """
    Detect tool name from FunctionCall or FunctionExecutionResult

    Examples:
    - FunctionCall(name='search_knowledge', ...) → 'search_knowledge'
    - FunctionExecutionResult(name='web_search', ...) → 'web_search'
    """
    # Pattern: name='tool_name' or name="tool_name"
    match = re.search(r"name=['\"]([a-z_]+)['\"]", text)
    if match:
        return match.group(1)
    return None

def format_tool_activity_for_ui(message_content: str, agent_name: str = "") -> str:
    """
    Replace raw tool calls with UI-friendly fixed phrases

    Approach:
    1. Detect FunctionCall/FunctionExecutionResult patterns
    2. Extract tool name
    3. Replace with fixed phrase from TOOL_DISPLAY_MAP
    4. Remove leftover Python dicts

    Args:
        message_content: Raw message from AutoGen (may contain tool calls)
        agent_name: Agent who made the call (plume/mimir)

    Returns:
        Cleaned message with fixed UI phrases
    """
    cleaned = message_content

    # Step 1: Replace FunctionCall patterns
    function_call_pattern = r'\[?FunctionCall\([^)]+\)\]?'
    matches = re.finditer(function_call_pattern, cleaned, flags=re.DOTALL)

    for match in matches:
        original = match.group(0)
        tool_name = detect_tool_name(original)

        if tool_name and tool_name in TOOL_DISPLAY_MAP:
            replacement = TOOL_DISPLAY_MAP[tool_name]
            cleaned = cleaned.replace(original, replacement)
        else:
            # Unknown tool, remove completely
            cleaned = cleaned.replace(original, '')

    # Step 2: Replace FunctionExecutionResult patterns
    execution_result_pattern = r'\[?FunctionExecutionResult\([^)]+\)\]?'
    matches = re.finditer(execution_result_pattern, cleaned, flags=re.DOTALL)

    for match in matches:
        original = match.group(0)
        tool_name = detect_tool_name(original)

        if tool_name and tool_name in TOOL_DISPLAY_MAP:
            # For execution results, show completed status
            replacement = TOOL_DISPLAY_MAP[tool_name].replace('...', '✓')
            cleaned = cleaned.replace(original, replacement)
        else:
            # Unknown tool, remove completely
            cleaned = cleaned.replace(original, '')

    # Step 3: Remove Python dicts (aggressive cleaning)
    # First pass: Remove complete dicts
    dict_patterns = [
        r'\{\s*[\'"]success[\'"]\s*:.+?\}',
        r'\{\s*[\'"]results[\'"]\s*:.+?\}',
        r'\{\s*[\'"]error[\'"]\s*:.+?\}',
        r'\{\s*[\'"]count[\'"]\s*:.+?\}',
        r'\{\s*[\'"]note_id[\'"]\s*:.+?\}',
        r'\{\s*[\'"]title[\'"]\s*:.+?\}',
        r'\{\s*[\'"]content[\'"]\s*:.+?\}',
        # Catch remaining dicts with common structure
        r',?\s*\{[\'"][a-z_]+[\'"]\s*:.+?\}',
    ]

    for pattern in dict_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

    # Second pass: Remove leftover dict fragments like ], 'key': value}
    fragment_patterns = [
        r'\],?\s*[\'"][a-z_]+[\'"]\s*:.+?\}',  # ], 'count': 2, 'confidence': 0.58}
        r',\s*[\'"][a-z_]+[\'"]\s*:.+?\}',     # , 'count': 2}
    ]

    for pattern in fragment_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

    # Step 4: Clean up leftover artifacts
    # Remove leading/trailing commas and whitespace
    cleaned = re.sub(r'^\s*,\s*', '', cleaned)
    cleaned = re.sub(r',\s*$', '', cleaned)
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Remove excessive newlines

    return cleaned.strip()


def extract_tool_activities(message_content: str, agent_name: str) -> List[Dict[str, Any]]:
    """
    Extract structured tool activity data from message
    Useful for Phase 2 when we want separate tool_activities array

    Returns list of:
    {
        'agent': 'mimir',
        'tool': 'web_search',
        'status': 'completed',
        'display': '🌐 Exploration du web ✓'
    }
    """
    activities = []

    # Find all tool calls
    patterns = [
        (r'\[?FunctionCall\([^)]+name=[\'"]([a-z_]+)[\'"][^)]*\)\]?', 'running'),
        (r'\[?FunctionExecutionResult\([^)]+name=[\'"]([a-z_]+)[\'"][^)]*\)\]?', 'completed')
    ]

    for pattern, status in patterns:
        matches = re.finditer(pattern, message_content, flags=re.DOTALL)
        for match in matches:
            tool_name = match.group(1)
            if tool_name in TOOL_DISPLAY_MAP:
                display = TOOL_DISPLAY_MAP[tool_name]
                if status == 'completed':
                    display = display.replace('...', '✓')

                activities.append({
                    'agent': agent_name,
                    'tool': tool_name,
                    'status': status,
                    'display': display
                })

    return activities
