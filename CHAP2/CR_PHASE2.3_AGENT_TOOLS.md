# 🤖 PHASE 2.3 : ARCHITECTURE AGENT-CENTRIC AVEC TOOLS

**Date :** 1er octobre 2025
**Durée :** ~1h
**Statut :** ✅ COMPLÉTÉ (avec gaps identifiés)

---

## 🎯 OBJECTIF

Refactorer l'architecture d'orchestration pour que **les agents Plume et Mimir décident eux-mêmes** quand utiliser leurs outils (RAG, web search, etc.) au lieu que l'orchestrator fasse ces décisions.

**Principe :** Agent-centric vs orchestrator-centric

---

## ✅ RÉALISATIONS

### 1. **Création du système de Tools AutoGen**

**Fichier créé :** `backend/agents/tools.py`

```python
# Tool pour recherche RAG
async def search_knowledge(
    query: str,
    limit: int = 10,
    similarity_threshold: float = 0.75
) -> Dict[str, Any]:
    """
    Recherche dans la base de connaissances en utilisant RAG.

    Utilise cette fonction quand:
    - L'utilisateur demande explicitement une recherche
    - La question nécessite des informations archivées

    Ne PAS utiliser pour:
    - Salutations simples (bonjour, salut, etc.)
    - Questions générales ne nécessitant pas de contexte archivé
    """
```

**Configuration actuelle :**
- `MIMIR_TOOLS = [search_knowledge]` - Mimir peut chercher dans les archives
- `PLUME_TOOLS = []` - Plume n'a pas de tools pour l'instant

### 2. **Intégration Tools dans AutoGen Agents**

**Fichier modifié :** `backend/agents/autogen_agents.py`

**Changements :**
```python
# Import des tools
from agents.tools import MIMIR_TOOLS, PLUME_TOOLS

# Attachement aux agents
self.mimir_agent = AssistantAgent(
    name="Mimir",
    model_client=self.model_client,
    tools=MIMIR_TOOLS,  # ✅ Tools attachés
    system_message="""..."""
)

self.plume_agent = AssistantAgent(
    name="Plume",
    model_client=self.model_client,
    tools=PLUME_TOOLS,  # ✅ Tools attachés (vide pour l'instant)
    system_message="""..."""
)
```

**System prompts mis à jour :**
- Instructions explicites sur QUAND utiliser les tools
- Guidelines pour éviter les abus (pas de RAG pour "salut")

### 3. **Routing Auto → Discussion**

**Fichier modifié :** `backend/agents/orchestrator.py`

```python
# Mode "auto" route maintenant vers discussion
elif mode == "auto":
    state["agent_used"] = "discussion"
    state["routing_reason"] = "auto_discussion_with_tools"
    logger.info("Auto-routed to discussion (agents will decide with tools)")
    return state
```

**Impact :** Toutes les requêtes utilisateur passent par la discussion multi-agent où Plume et Mimir collaborent et décident ensemble.

### 4. **Fix Bug AgentLogger**

**Problème :** `'AgentLogger' object has no attribute 'error'`

**Solution :**
```python
# Avant (causait erreur)
from utils.logger import get_agent_logger
logger = get_agent_logger("autogen")
logger.error(...)  # ❌ AgentLogger n'a pas .error()

# Après (fixé)
from utils.logger import get_agent_logger, get_logger
agent_logger = get_agent_logger("autogen")  # Pour log_agent_start, etc.
logger = get_logger(__name__)  # Structlog pour .error(), .warning(), etc.
```

---

## 🧪 TESTS VALIDÉS

### Test 1: Salutation Simple ✅

**Input :** `"salut"`

**Résultat :**
- ✅ Agents Plume + Mimir ont répondu directement
- ✅ **AUCUN appel à `search_knowledge`**
- ✅ Discussion collaborative mais concise
- ⚠️ Réponse un peu longue (5 tours de discussion)

**Logs confirmés :**
```
Discussion completed, turns=5, final_response_length=...
# Aucune ligne "Tool search_knowledge called"
```

### Test 2: Recherche Explicite ✅

**Input :** `"recherche migration"`

**Résultat :**
- ✅ Mimir a **automatiquement appelé `search_knowledge`**
- ✅ Paramètres corrects: `{"query": "migration", "limit": 10, "similarity_threshold": 0.75}`
- ✅ 7 résultats retournés avec succès
- ✅ Agents ont synthétisé les résultats

**Logs confirmés :**
```json
{
  "type": "ToolCall",
  "tool_name": "search_knowledge",
  "result": "{'success': True, 'count': 7, 'query': 'migration'}"
}
```

**Conclusion :** L'architecture agent-centric fonctionne. Les agents décident intelligemment quand utiliser les tools.

---

## ⚠️ GAPS IDENTIFIÉS

### Tools Manquants pour MIMIR

Actuellement : `[search_knowledge]`

**Manquants :**
1. ❌ **`web_search`** - Recherche internet (Perplexity + Tavily)
   - Service existe: `services/rag_service.py` avec `_perplexity_search()` et `_tavily_search()`
   - Devrait être exposé comme tool pour recherches approfondies

2. ❌ **`get_related_content`** - Trouver contenus similaires
   - Service existe: `rag.py` avec `get_related_content()`
   - Utile pour explorer connexions entre concepts

### Tools Manquants pour PLUME

Actuellement : `[]`

**Manquants :**
1. ❌ **`create_note`** - Stocker dans les archives
   - Service existe: `storage.py` avec `create_note()`
   - **CRITIQUE** : Plume doit pouvoir écrire ses restitutions

2. ❌ **`update_note`** - Mettre à jour une note
   - Service existe: `storage.py` avec `update_note()`
   - Pour enrichir/corriger notes existantes

---

## 📊 ARCHITECTURE ACTUELLE

```
MODE AUTO → Discussion Multi-Agent
              ↓
        ┌─────────────┐
        │ Plume       │  Tools: []
        │ - Capture   │  (devrait avoir create_note)
        │ - Reformule │
        └──────┬──────┘
               │
               ↓ Collaboration
               │
        ┌──────┴──────┐
        │ Mimir       │  Tools: [search_knowledge]
        │ - Archive   │  (devrait avoir web_search, get_related_content)
        │ - Recherche │
        └─────────────┘
```

---

## 🚀 PROCHAINES ÉTAPES

### Priorité 1: Compléter les Tools

**Tâche :** Ajouter les 4 tools manquants dans `agents/tools.py`

```python
# MIMIR
async def web_search(query: str, max_results: int = 5) -> Dict[str, Any]
async def get_related_content(note_id: str, limit: int = 5) -> Dict[str, Any]

# PLUME
async def create_note(title: str, content: str, metadata: Dict = {}) -> Dict[str, Any]
async def update_note(note_id: str, content: str) -> Dict[str, Any]
```

**Mise à jour :**
```python
MIMIR_TOOLS = [search_knowledge, web_search, get_related_content]
PLUME_TOOLS = [create_note, update_note]
```

### Priorité 2: Affiner les Termination Conditions

**Problème :** La discussion peut être longue (5+ tours pour "salut")

**Solutions possibles :**
- Ajuster `MaxMessageTermination` (actuellement 10 max)
- Ajouter conditions de terminaison intelligentes
- Optimiser les prompts agents pour réponses plus concises

### Priorité 3: Tests End-to-End

**Scénarios à valider :**
1. ✅ Salutation → réponse directe
2. ✅ Recherche archives → `search_knowledge` appelé
3. ❌ Recherche internet → `web_search` appelé (à tester quand implémenté)
4. ❌ Capture note → `create_note` appelé (à tester quand implémenté)

---

## 📝 DOCUMENTATION ASSOCIÉE

- **Code :** `backend/agents/tools.py` (nouveau fichier)
- **Agents :** `backend/agents/autogen_agents.py` (tools attachés)
- **Orchestrator :** `backend/agents/orchestrator.py` (auto→discussion)
- **Config :** `backend/config.py` (token limits Plume=1000, Mimir=2000)

---

## 💡 LEÇONS APPRISES

1. **Architecture agent-centric** est plus flexible que orchestrator-centric
2. Les agents Claude sont capables de **décider intelligemment** quand utiliser les tools
3. Les **docstrings des tools** sont cruciales (agents les lisent pour décider)
4. AutoGen v0.4 gère bien les **tools asynchrones** Python
5. Importance de **logger distinctement** AgentLogger vs structlog logger

---

## ✅ VALIDATION FINALE

**Architecture fonctionnelle :** ✅
**Tests basiques passés :** ✅
**Tools complets :** ❌ (4 manquants identifiés)
**Production ready :** ⚠️ (nécessite complétion tools)

**Recommandation :** Compléter les 4 tools manquants avant déploiement production.

---

> **Phase 2.3 completée avec succès**
> Architecture agent-centric validée, gaps identifiés, roadmap claire pour complétion.
