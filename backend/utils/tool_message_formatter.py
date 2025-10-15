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

    # Step 0: Detect and clean FRAGMENTS of tool calls (partial FunctionCall without prefix)
    # Patterns:
    # - name='tool_name', call_id='...', is_error=False)]
    # - [...truncated...], name='update_note')]
    # - Any text ending with name='tool')]
    fragment_patterns_step0 = [
        r'''(?:^|[,\s])name=['"]([a-z_]+)['"],\s*call_id=[^,\)]+(?:,\s*is_error=[^,\)]+)?[)\]]*''',  # Original
        r'''\[?\.\.\..*?\]?,?\s*name=['"]([a-z_]+)['"]\s*[)\]]+''',  # [...], name='tool')]
        r'''(?:.*?),\s*name=['"]([a-z_]+)['"]\s*[)\]]+$''',  # Anything ending with , name='tool')]
    ]

    for pattern in fragment_patterns_step0:
        matches = re.finditer(pattern, cleaned, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
        for match in matches:
            original = match.group(0)
            tool_name = match.group(1)

            if tool_name and tool_name in TOOL_DISPLAY_MAP:
                replacement = TOOL_DISPLAY_MAP[tool_name]
                cleaned = cleaned.replace(original, replacement)
            else:
                # Unknown tool or fragment, remove completely
                cleaned = cleaned.replace(original, '')

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
        r'\{\s*[\'"]note_id[\'"]\s*:[^\}]+\}',  # Match note_id dicts (avoid greedy)
        r'\{\s*[\'"]title[\'"]\s*:[^\}]+\}',    # Match title dicts (avoid greedy)
        r'\{\s*[\'"]content[\'"]\s*:.+?\}',
        r'\{\s*[\'"]created_at[\'"]\s*:[^\}]+\}',  # Match created_at timestamps
        r'\{\s*[\'"]confidence[\'"]\s*:[^\}]+\}',  # Match confidence scores
        # Catch remaining dicts with common structure
        r',?\s*\{[\'"][a-z_]+[\'"]\s*:.+?\}',
    ]

    for pattern in dict_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

    # Second pass: Remove leftover dict fragments like ], 'key': value}
    fragment_patterns = [
        r'\],?\s*[\'"][a-z_]+[\'"]\s*:[^\}]+\}',  # ], 'count': 2, 'confidence': 0.58}
        r',\s*[\'"][a-z_]+[\'"]\s*:[^\}]+\}',     # , 'count': 2}
        r'\]\s*,\s*[\'"][a-z_]+[\'"]\s*:[^\}]+\}', # Specific case from logs
    ]

    for pattern in fragment_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

    # Step 4: Clean up leftover artifacts
    # Remove leading/trailing commas, quotes, and whitespace
    cleaned = re.sub(r'^\s*[,"\'\s]+', '', cleaned)  # Leading artifacts
    cleaned = re.sub(r'[,"\'\s]+$', '', cleaned)     # Trailing artifacts
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Remove excessive newlines
    cleaned = re.sub(r'^["\',\s]+', '', cleaned)     # Clean start again after all replacements

    return cleaned.strip()


def extract_tool_activities(message_content: str, agent_name: str) -> List[Dict[str, Any]]:
    """
    Extract structured tool activity data from message
    Used to generate agent_action SSE events (WhatsApp-style notifications)

    Returns list of:
    {
        'agent': 'mimir',
        'tool': 'web_search',
        'status': 'running' | 'completed',
        'display': '🌐 Exploration du web...',
        'action_text': 'recherche sur le web'  # For "Mimir recherche sur le web"
    }
    """
    activities = []

    # Tool name to action verb mapping (for "Agent <action_verb>")
    TOOL_ACTION_VERBS = {
        'search_knowledge': 'recherche dans les archives',
        'web_search': 'recherche sur le web',
        'create_note': 'a créé une note',
        'update_note': 'a mis à jour une note',
        'get_related_content': 'explore les contenus liés',
    }

    # Find all tool calls (including fragments)
    patterns = [
        (r'\[?FunctionCall\([^)]+name=[\'"]([a-z_]+)[\'"][^)]*\)\]?', 'running'),
        (r'\[?FunctionExecutionResult\([^)]+name=[\'"]([a-z_]+)[\'"][^)]*\)\]?', 'completed'),
        (r'''(?:^|[,\s])name=['"]([a-z_]+)['"],\s*call_id=[^,\)]+''', 'running'),  # Fragments
    ]

    for pattern, status in patterns:
        matches = re.finditer(pattern, message_content, flags=re.DOTALL | re.IGNORECASE)
        for match in matches:
            tool_name = match.group(1)
            if tool_name in TOOL_DISPLAY_MAP:
                display = TOOL_DISPLAY_MAP[tool_name]
                if status == 'completed':
                    display = display.replace('...', '✓')

                # Avoid duplicates (same tool might be matched by multiple patterns)
                if not any(a['tool'] == tool_name and a['status'] == status for a in activities):
                    activities.append({
                        'agent': agent_name,
                        'tool': tool_name,
                        'status': status,
                        'display': display,
                        'action_text': TOOL_ACTION_VERBS.get(tool_name, f'utilise {tool_name}')
                    })

    return activities


def is_pure_tool_call(message_content: str) -> bool:
    """
    Check if message is ONLY a tool call (no human-readable content)
    Used to determine if we should send agent_action instead of agent_message

    Returns True if message contains ONLY:
    - FunctionCall/FunctionExecutionResult patterns
    - Python dicts
    - Technical artifacts

    Returns False if message contains natural language content
    """
    # Remove tool calls and dicts
    cleaned = format_tool_activity_for_ui(message_content, '')

    # If cleaned message is empty or very short, it was pure tool call
    cleaned_stripped = cleaned.strip()

    # Check if what remains is meaningful (more than just emoji or short artifact)
    if len(cleaned_stripped) == 0:
        return True

    # If only emojis/symbols remain
    if len(cleaned_stripped) < 5 and not any(c.isalpha() for c in cleaned_stripped):
        return True

    return False
