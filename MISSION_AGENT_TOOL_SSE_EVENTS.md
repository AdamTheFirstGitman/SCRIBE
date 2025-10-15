# MISSION: Émettre agent_action SSE depuis les tools directement

## 🎨 VISION & CONTEXTE (À LIRE AVANT DE CODER)

### Philosophie SCRIBE : Backend ≠ Frontend

Le backend et le frontend ne servent PAS le même objectif.

**Backend (agents, orchestration) :**
- Détails techniques nécessaires pour fonctionner
- Logs verbeux, tool calls, dicts Python, IDs
- Pour les développeurs et les agents

**Frontend (interface utilisateur) :**
- Informations pertinentes pour l'humain
- Langage naturel, notifications minimalistes
- Masquer la complexité technique
- WhatsApp-style : "Qu'est-ce qui se passe ?" pas "Comment ça marche ?"

### Objectif de cette mission

**User envoie :** "Créez une note sur Tokyo"

**Ce que le user DOIT voir :**
```
[Notification WhatsApp-style, centrée, pas de bulle]
Plume a créé une note... (dots animés)

[2s plus tard]
Plume a créé une note ✓

[Puis bulle de message]
Plume: ✅ Note créée sur Tokyo
```

**Ce que le user NE DOIT PAS voir :**
```
[FunctionCall(name='create_note', arguments='...')]
{'success': True, 'note_id': 'abc123', 'created_at': '2025-...'}
[... technical garbage ...]
```

### Architecture : 3 types d'éléments graphiques

1. **Messages** (bulles) - Agent parle, langage naturel
2. **Actions** (notifications) - Agent agit ← **C'EST CE QU'ON IMPLÉMENTE**
3. **Clickables** (ressources) - Liens vers notes/viz

**Ta mission = Faire apparaître les ACTIONS en temps réel pendant que les agents travaillent.**

**Pourquoi SSE ?** Pour que l'utilisateur voie **en direct** ce que les agents font, au lieu d'attendre 15s avec un loader qui tourne sans feedback.

---

## 🎯 OBJECTIF TECHNIQUE

Faire en sorte que **chaque tool** émette des events SSE `agent_action` au moment de son exécution :
- **START** : `status='running'` quand tool commence
- **END** : `status='completed'` quand tool termine

**Résultat attendu UI :**
```
[Notification centrée, pas de bulle]
Mimir recherche dans les archives...  (avec dots animés)
```
Puis après exécution :
```
Mimir recherche dans les archives ✓
```

---

## 📋 ANALYSE PRÉLIMINAIRE (déjà faite)

### Fichiers concernés

**1. `backend/agents/tools.py` (329 lignes)**
- Contient 5 tools async :
  - `search_knowledge(query, limit, similarity_threshold)` - Ligne 18-72
  - `web_search(query, max_results)` - Ligne 75-140
  - `get_related_content(note_id, limit)` - Ligne 143-185
  - `create_note(title, content, metadata)` - Ligne 188-249
  - `update_note(note_id, content, title, metadata)` - Ligne 252-310
- Assignments : `MIMIR_TOOLS` (ligne 318-322), `PLUME_TOOLS` (ligne 325-328)

**2. `backend/agents/autogen_agents.py`**
- Ligne 79 : `tools=PLUME_TOOLS` passé à `AssistantAgent`
- Ligne 118 : `tools=MIMIR_TOOLS` passé à `AssistantAgent`
- AutoGen appelle les tools **automatiquement**, sans paramètres custom

**3. `backend/agents/orchestrator.py`**
- Ligne 566 : `await autogen_discussion.group_chat.run(task=task_message)`
- Ligne 586-649 : Boucle qui traite messages et envoie SSE via `sse_queue`
- `sse_queue` disponible dans `discussion_node()` scope

### Contrainte technique identifiée

**❌ IMPOSSIBLE de passer `sse_queue` directement aux tools via AutoGen API**

AutoGen appelle `search_knowledge(query="...")` avec seulement les args définis dans la signature.

**✅ SOLUTION : Utiliser `contextvars` (Python 3.7+)**

Passer `sse_queue` via un contexte global accessible depuis n'importe quel async call.

---

## 🔧 PLAN D'ACTION DÉTAILLÉ

### ÉTAPE 1 : Créer module de contexte SSE

**Fichier à créer :** `backend/agents/sse_context.py`

```python
"""
Context manager pour SSE queue accessible depuis tools
Utilise contextvars pour async-safe context propagation
"""

from contextvars import ContextVar
from typing import Optional
import asyncio

# Context variable pour sse_queue (async-safe)
_sse_queue_context: ContextVar[Optional[asyncio.Queue]] = ContextVar('sse_queue', default=None)


def set_sse_queue(queue: Optional[asyncio.Queue]):
    """
    Set SSE queue in current async context
    À appeler dans orchestrator AVANT d'exécuter group chat
    """
    _sse_queue_context.set(queue)


def get_sse_queue() -> Optional[asyncio.Queue]:
    """
    Get SSE queue from current async context
    À appeler dans tools pour émettre events
    """
    return _sse_queue_context.get()


async def emit_agent_action(
    agent: str,
    tool: str,
    action_text: str,
    status: str
):
    """
    Helper pour émettre agent_action event depuis un tool

    Args:
        agent: 'plume' ou 'mimir'
        tool: nom du tool (ex: 'create_note')
        action_text: texte action (ex: 'a créé une note')
        status: 'running' ou 'completed'
    """
    queue = get_sse_queue()
    if queue:
        from datetime import datetime
        await queue.put({
            'type': 'agent_action',
            'agent': agent,
            'tool': tool,
            'action_text': action_text,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
```

**Dépendances :** Aucune (stdlib uniquement)

---

### ÉTAPE 2 : Instrumenter chaque tool

**Fichier à modifier :** `backend/agents/tools.py`

**Imports à ajouter (ligne 12, après logger) :**
```python
from agents.sse_context import emit_agent_action
```

**Pattern à appliquer à CHAQUE tool :**

```python
async def TOOL_NAME(...args):
    """Docstring..."""

    # DÉBUT TOOL - Emit START event
    await emit_agent_action(
        agent='mimir',  # ou 'plume' selon le tool
        tool='TOOL_NAME',
        action_text='ACTION_TEXT',  # Voir mapping ci-dessous
        status='running'
    )

    try:
        # ... code existant du tool ...

        result = {...}

        # FIN TOOL - Emit COMPLETE event
        await emit_agent_action(
            agent='mimir',  # ou 'plume'
            tool='TOOL_NAME',
            action_text='ACTION_TEXT',
            status='completed'
        )

        return result

    except Exception as e:
        # En cas d'erreur, émettre status='failed' (optionnel)
        await emit_agent_action(
            agent='mimir',
            tool='TOOL_NAME',
            action_text='ACTION_TEXT',
            status='failed'
        )
        # ... gestion erreur existante ...
```

**Mapping agent + action_text pour chaque tool :**

| Tool | Agent | action_text |
|------|-------|-------------|
| `search_knowledge` | `mimir` | `recherche dans les archives` |
| `web_search` | `mimir` | `recherche sur le web` |
| `get_related_content` | `mimir` | `explore les contenus liés` |
| `create_note` | `plume` | `a créé une note` |
| `update_note` | `plume` | `a mis à jour une note` |

**Exemple complet pour `create_note` :**

```python
async def create_note(
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Crée une nouvelle note dans les archives.
    [... docstring existante ...]
    """
    # DÉBUT TOOL
    await emit_agent_action(
        agent='plume',
        tool='create_note',
        action_text='a créé une note',
        status='running'
    )

    try:
        logger.info("Tool create_note called", title=title[:50])

        # Préparer les données de la note
        note_metadata = metadata or {}
        note_metadata["source"] = "plume_agent"

        note_data = {
            "title": title,
            "text_content": content,
            "metadata": note_metadata,
            "tags": metadata.get("tags", []) if metadata else []
        }

        # Créer la note
        note = await supabase_client.create_note(note_data)

        logger.info("Tool create_note completed", note_id=note.get("id"))

        # FIN TOOL - Emit success
        await emit_agent_action(
            agent='plume',
            tool='create_note',
            action_text='a créé une note',
            status='completed'
        )

        return {
            "success": True,
            "note_id": note.get("id"),
            "title": note.get("title"),
            "created_at": note.get("created_at")
        }
    except Exception as e:
        logger.error("Tool create_note failed", error=str(e))

        # Emit failed event (optionnel mais recommandé)
        await emit_agent_action(
            agent='plume',
            tool='create_note',
            action_text='a créé une note',
            status='failed'
        )

        return {
            "success": False,
            "error": str(e),
            "note_id": None
        }
```

**À RÉPÉTER pour les 5 tools.**

---

### ÉTAPE 3 : Set context dans orchestrator

**Fichier à modifier :** `backend/agents/orchestrator.py`

**Import à ajouter (ligne 26, après autres imports agents) :**
```python
from agents.sse_context import set_sse_queue
```

**Modification dans `discussion_node()` AVANT ligne 566 :**

```python
# AVANT cette ligne :
# result = await autogen_discussion.group_chat.run(task=task_message)

# AJOUTER :
# Set SSE queue in context pour que tools puissent émettre events
if sse_queue:
    set_sse_queue(sse_queue)

# Puis exécuter (ligne existante) :
result = await autogen_discussion.group_chat.run(task=task_message)
```

**Localisation exacte :**
- Ligne 564 : début boucle retry
- **INSÉRER avant ligne 566** (dans le try block)

---

### ÉTAPE 4 : Validation et tests

**Tests à faire :**

1. **Test local backend :**
```bash
cd backend
python3 -m pytest tests/ -v -k "test_" --tb=short
```

2. **Test SSE endpoint avec message déclenchant tools :**
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/orchestrated/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "Créez une note sur Marseille", "mode": "auto"}'
```

**Vérifier dans output SSE :**
```json
{"type": "agent_action", "agent": "plume", "tool": "create_note", "action_text": "a créé une note", "status": "running", ...}
```
Puis quelques secondes après :
```json
{"type": "agent_action", "agent": "plume", "tool": "create_note", "action_text": "a créé une note", "status": "completed", ...}
```

3. **Test frontend `/chat` :**
- Envoyer message : "Créez une note sur Berlin"
- **Vérifier UI affiche :** `Plume a créé une note` (notification centrée avec dots animés puis checkmark)

---

## 📦 LIVRABLES

### Fichiers à créer :
1. `backend/agents/sse_context.py` (~60 lignes)

### Fichiers à modifier :
1. `backend/agents/tools.py` :
   - Ajouter import `emit_agent_action` (ligne 12)
   - Instrumenter 5 tools avec emit START/COMPLETE (~10 lignes par tool)

2. `backend/agents/orchestrator.py` :
   - Ajouter import `set_sse_queue` (ligne 26)
   - Appeler `set_sse_queue(sse_queue)` avant group_chat.run (ligne 565)

### Tests :
- Tests unitaires existants doivent passer (emit_agent_action ne crash pas si sse_queue=None)
- Test SSE endpoint manuel
- Validation UI frontend

---

## ⚠️ POINTS D'ATTENTION

1. **emit_agent_action ne doit JAMAIS crasher** si `sse_queue` est None (déjà géré dans helper)

2. **Ordre des events SSE :**
   - `agent_action` status=running
   - `agent_action` status=completed
   - `agent_message` (le texte natural language de l'agent)

3. **Performance :** `emit_agent_action` est async et non-bloquant (queue.put est rapide)

4. **Error handling :** Si tool échoue, émettre `status='failed'` (optionnel mais améliore UX)

5. **Frontend déjà prêt :**
   - Composant `<AgentAction />` existe
   - Routing SSE `agent_action` → AgentAction implémenté
   - **Il suffit que backend émette les events**

---

## 🚀 ORDRE D'EXÉCUTION RECOMMANDÉ

1. Créer `sse_context.py` (base solide)
2. Tester `emit_agent_action` en standalone
3. Modifier `orchestrator.py` (set_sse_queue)
4. Instrumenter UN tool (ex: `create_note`) et tester
5. Si OK → instrumenter les 4 autres tools
6. Tests complets + validation UI

---

## 📚 RÉFÉRENCES

**Contextvars Python :**
- https://docs.python.org/3/library/contextvars.html
- Async-safe, pas besoin de threading.local
- Propagation automatique dans async calls

**Architecture SCRIBE :**
- Tools = fonctions appelées par AutoGen agents
- SSE queue = asyncio.Queue dans orchestrator
- Frontend AgentAction component prêt à recevoir events

---

**Bonne chance ! Cette approche est propre, fiable, et évite le parsing de messages AutoGen.**
