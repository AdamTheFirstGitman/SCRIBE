# 🎯 MISSION AGENT : Fix Tool Filtering in Chat UX

## 📋 CONTEXTE

**Projet :** SCRIBE - Système de gestion de connaissances avec agents IA (Plume + Mimir)
**Architecture :** Backend FastAPI + AutoGen v0.4 + LangGraph | Frontend Next.js 14.2.15 + TypeScript
**Déploiement :** Render.com (Backend + Frontend séparés)

**User ID :** king_001
**User Frustration Level :** 🔥🔥🔥 TRÈS ÉLEVÉ - "ça fait au moins 5 fois que tu me fais les mêmes erreurs"

---

## 🎯 OBJECTIF PRINCIPAL

**Faire disparaître les éléments techniques de l'interface utilisateur chat :**

❌ **Ce qui doit DISPARAÎTRE :**
```
[FunctionCall(id='toolu_01MY...', arguments='{"query": "...", ...}', name='search_knowledge')]
{'success': True, 'note_id': 'b38160c1-...', 'title': '...', 'created_at': '2025-10-14T...'}
[FunctionExecutionResult(content="{'success': True, ...}", name='search_knowledge', ...)]
```

✅ **Ce qui doit APPARAÎTRE à la place :**
```
🔍 Recherche dans les archives...
🌐 Exploration du web...
✍️ Note créée avec succès
📝 Note mise à jour
🔗 Recherche de contenus liés...
```

---

## 📊 HISTORIQUE DES TENTATIVES (5+ itérations)

### ✅ CE QUI MARCHE

1. **Backend filtering logic existe et fonctionne :**
   - `/backend/utils/tool_message_formatter.py` : Mapping déterministe tool → phrase UI
   - `format_tool_activity_for_ui()` : Remplace `[FunctionCall(...)]` par phrases avec emojis
   - `filter_for_ui()` : Filtrage keywords + condensing standard
   - Testé localement → FONCTIONNE

2. **Architecture agents opérationnelle :**
   - AutoGen v0.4 multi-agent (Plume + Mimir) discussion collaborative
   - LangGraph orchestrator avec StateGraph
   - SSE streaming temps réel (`/api/v1/chat/orchestrated/stream`)
   - Tools créés et fonctionnels : search_knowledge, web_search, create_note, update_note, get_related_content

3. **Frontend React components propres :**
   - `/frontend/components/chat/ChatMessage.tsx` : Affichage messages
   - `/frontend/app/page.tsx` : SSE handling
   - TypeScript types définis (`/frontend/lib/types.ts`)

### ❌ CE QUI NE MARCHE PAS (PROBLÈME RÉCURRENT)

**SYMPTÔME :**
- Les `[FunctionCall(...)]` et dicts Python `{'success': True, ...}` apparaissent TOUJOURS dans l'interface utilisateur
- Screenshot user montre messages bruts techniques visibles dans chat
- Pydantic validation errors sur `create_note` (arguments malformed)

**TENTATIVES ÉCHOUÉES :**

1. **Tentative 1-3 :** Filtrage backend HTML generation
   - Appliqué `format_tool_activity_for_ui()` dans génération HTML
   - Résultat : HTML contient parfois les filtres, parfois pas
   - Échec : Incompatibilité Tailwind backend/frontend, emojis cassent rendering

2. **Tentative 4 :** Render HTML backend directement en frontend
   - `dangerouslySetInnerHTML` avec HTML backend
   - Résultat : Rendering cassé, design incompatible
   - User feedback : "tu te fous de moi?" → retour fondamentaux demandé

3. **Tentative 5 :** Filtrage SSE messages (commit 74bd203)
   - Ajout `format_tool_activity_for_ui()` avant envoi SSE dans `orchestrator.py` line 620
   - Commit pushé, rebuild Render en cours
   - Résultat : **PAS ENCORE TESTÉ** (rebuild en cours pendant conversation)

### 🔍 DIAGNOSTIC ACTUEL

**Logs de production (14/10/2025 13:09) :**

```json
{
  "response": "{'success': True, 'note_id': 'b38160c1-6e76-4b91-9645-ed6785932301', ...}",
  "html": "<div>...[FunctionCall(id='toolu_01MY4kv4yJSDZ64rXLh9ReHz', ...)]...</div>",
  "agent_used": "discussion",
  "processing_time_ms": 29535,
  "timestamp": "2025-10-14T13:09:41.867326"
}
```

**Observations :**
1. ✅ Agents collaborent correctement (Plume + Mimir discussion)
2. ✅ Note créée avec succès (ID retourné)
3. ❌ `html` field contient `[FunctionCall(...)]` bruts
4. ❌ `response` field contient dict Python brut `{'success': True, ...}`
5. ⚠️ Pydantic validation error visible : `create_noteargs content Field required`

---

## 🔧 FICHIERS CRITIQUES À ANALYSER

### Backend (Python)

**`/backend/agents/orchestrator.py`** (CORE LOGIC)
- Line 618-632 : SSE message filtering (DERNIER FIX APPLIQUÉ)
- Line 26 : Import `format_tool_activity_for_ui`
- Line ~400-500 : HTML generation pour réponse finale
- Fonction `orchestrate_chat_v04()` : Point d'entrée principal

**`/backend/utils/tool_message_formatter.py`**
- `TOOL_DISPLAY_MAP` : Mapping tool names → phrases UI
- `format_tool_activity_for_ui()` : Regex-based replacement
- Patterns détectés : `[FunctionCall(...)`, `FunctionExecutionResult(...)`, dicts Python

**`/backend/utils/message_filter.py`**
- `filter_for_ui()` : Filtrage keywords + condensing
- Layer 2 filtering (après tool filtering)

**`/backend/routers/chat.py`**
- Endpoints : `/orchestrated`, `/orchestrated/stream`
- SSE streaming implementation

### Frontend (TypeScript)

**`/frontend/components/chat/ChatMessage.tsx`**
- Line 101-104 : Affichage message content (plain text only)
- Line 122-150 : Metadata display (ui_metadata support)
- Removed `dangerouslySetInnerHTML` (tentative 4 échec)

**`/frontend/app/page.tsx`**
- Line 95-127 : SSE event handling
- Line 143-156 : Response handling + message construction

**`/frontend/lib/types.ts`**
- `ChatMessage` interface : `content`, `metadata`, `ui_metadata`
- Removed `html` field (tentative 4 cleanup)

---

## 🐛 HYPOTHÈSES SUR LA CAUSE ROOT

### Hypothèse 1 : Deux Chemins Non-Filtrés (PLUS PROBABLE)

**Code paths produisant le HTML/response final :**

1. **Path SSE streaming** (`orchestrator.py` line 618-632)
   - Status : Fix appliqué (commit 74bd203) mais pas encore testé post-rebuild

2. **Path HTML generation finale** (`orchestrator.py` line ~400-500)
   - Status : PEUT-ÊTRE pas filtré correctement
   - Besoin vérifier si `format_tool_activity_for_ui()` appliqué avant génération HTML

3. **Path `response` field final** (JSON return)
   - Status : PROBABLEMENT pas filtré
   - Le `"response": "{'success': True, ...}"` suggère que le dict brut est retourné

**Action requise :**
→ Tracer TOUS les chemins qui construisent `html` et `response` fields
→ Appliquer `format_tool_activity_for_ui()` + `filter_for_ui()` sur TOUS les chemins

### Hypothèse 2 : Regex Patterns Incomplets

**`tool_message_formatter.py` patterns actuels :**
```python
r'\[FunctionCall\([^\]]+\)\]'
r'FunctionExecutionResult\([^\)]+\)'
r'\{[\'"]success[\'"]:\s*True[^\}]*\}'
```

**Possibilité :**
- Patterns ne matchent pas toutes les variations
- Nested dicts ou formats échappés non couverts
- Multi-line tool calls cassent le regex

**Action requise :**
→ Vérifier samples exacts des messages raw
→ Tester regex contre tous les formats observés

### Hypothèse 3 : Cache/Timing Issues

**Observations :**
- Commit 74bd203 pushé mais rebuild Render en cours pendant conversation
- Logs montrent timestamp `2025-10-14T13:09:41` (pendant discussion)
- User teste pendant que build n'est pas terminé

**Action requise :**
→ Attendre rebuild complet Render (5-10min post-push)
→ Clear browser cache + test avec message unique (éviter response cache)

### Hypothèse 4 : Pydantic Validation Breaking Tool Calls

**Error visible :** `create_noteargs content Field required`

**Possibilité :**
- AutoGen génère tool call avec arguments malformed
- Pydantic rejette, mais message brut quand même envoyé au frontend
- Error handling ne filtre pas les messages d'erreur

**Action requise :**
→ Vérifier structure tool call arguments AutoGen
→ Améliorer error handling pour cacher détails techniques même en cas d'erreur

---

## 🎯 STRATÉGIE RECOMMANDÉE

### Phase 1 : DIAGNOSTIC COMPLET (30min)

1. **Vérifier status rebuild Render**
   ```bash
   curl https://scribe-api-uj22.onrender.com/health/detailed
   # Check deployment timestamp
   ```

2. **Lire code orchestrator.py COMPLET**
   - Identifier TOUS les endroits où `html` et `response` sont construits
   - Vérifier si filtrage appliqué partout

3. **Tester regex patterns avec samples réels**
   ```python
   # Créer script Python test_regex.py avec samples exacts des logs
   import re
   sample = "[FunctionCall(id='toolu_01MY4kv4yJSDZ64rXLh9ReHz', arguments='{\"query\": \"communaut\\\\u00e9 \\\\u00e9gyptienne Al Masri Gaza\", \"limit\": 10}', name='search_knowledge')]"
   # Tester tous les patterns
   ```

4. **Tracer le flow complet d'un message**
   ```
   User input → orchestrate_chat_v04() → AutoGen discussion →
   Message construction → Filtering? → SSE send → Frontend display
   ```

### Phase 2 : FIX SYSTÉMATIQUE (1h)

**Option A : Centraliser Filtering (RECOMMANDÉ)**

Créer fonction unique `prepare_message_for_frontend()` qui :
1. Prend raw message (AutoGen output)
2. Applique `format_tool_activity_for_ui()` (Layer 1)
3. Applique `filter_for_ui()` (Layer 2)
4. Return message clean

Appeler cette fonction **partout** :
- Avant SSE send
- Avant HTML generation
- Avant JSON response construction

**Option B : Post-Processing Backend Response**

Dans `chat.py` endpoint, avant return :
```python
# Post-process TOUT ce qui sort
response["html"] = format_tool_activity_for_ui(response["html"], "")
response["response"] = format_tool_activity_for_ui(response["response"], "")
```

**Option C : Frontend Filtering (FALLBACK)**

Si backend infaisable, filtrer côté frontend :
```typescript
// ChatMessage.tsx
const cleanContent = (content: string) => {
  return content
    .replace(/\[FunctionCall\([^\]]+\)\]/g, '🔍 Traitement en cours...')
    .replace(/\{'success': True[^\}]*\}/g, '✅ Opération réussie')
}
```

### Phase 3 : VALIDATION (30min)

1. **Tests unitaires Python**
   ```python
   # test_tool_filtering.py
   def test_all_tool_patterns():
       samples = [
           "[FunctionCall(id='toolu_01MY...', ...)]",
           "FunctionExecutionResult(content=\"{'success': True, ...}\")",
           "{'success': True, 'note_id': '...'}",
       ]
       for sample in samples:
           cleaned = format_tool_activity_for_ui(sample, "mimir")
           assert "[FunctionCall" not in cleaned
           assert "{'success'" not in cleaned
   ```

2. **Test intégration complet**
   ```bash
   # Message unique pour éviter cache
   curl -X POST .../orchestrated \
     -d '{"message": "TEST_UNIQUE_$(date +%s)", "user_id": "king_001"}'
   # Vérifier response.html et response.response
   ```

3. **Test frontend live**
   - Message dans chat UI
   - Screenshot des messages agents
   - Vérifier AUCUN `[FunctionCall` ou `{'success'` visible

---

## 📝 DELIVERABLES ATTENDUS

1. **Code fix complet** avec filtering appliqué sur TOUS les chemins
2. **Tests Python** validant tous les patterns
3. **Documentation** : Où le filtering est appliqué (diagram si nécessaire)
4. **Screenshot** montrant chat UI propre (user-friendly phrases avec emojis)
5. **CR concis** : Root cause + fix + validation

---

## ⚠️ CONTRAINTES CRITIQUES

1. **NE PAS changer d'architecture** (pas de React Native, pas de refonte)
2. **NE PAS créer de nouveaux fichiers** sauf tests
3. **ÉDITER les fichiers existants** uniquement
4. **TESTER localement** avant commit
5. **COMMIT atomic** : 1 fix = 1 commit avec message clair
6. **User doit valider** avant continuer

---

## 💬 COMMUNICATION USER

**Ton :** Concis, technique, honnête sur les limitations
**Format :** Bullet points, pas de blabla
**Si échec :** Dire "Je ne sais pas" plutôt qu'inventer une solution non-testée
**Si succès :** Screenshot + "Testé et validé" + demander user de vérifier

---

## 🚨 RED FLAGS À ÉVITER

❌ "Je pense que ça devrait marcher" → TESTER avant dire ça
❌ Proposer solution sans avoir lu le code complet
❌ Faire 5 fixes successifs non-testés
❌ Ignorer les logs de production
❌ Blâmer le cache sans vérifier le code
❌ Proposer refonte complète au lieu de fix ciblé

---

**MISSION START : Diagnostic complet → Fix systématique → Validation stricte**

**SUCCESS CRITERIA : User dit "ça marche" avec screenshot propre**
