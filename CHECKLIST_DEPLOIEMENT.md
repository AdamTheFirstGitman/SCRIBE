# ✅ CHECKLIST DÉPLOIEMENT - Phase 2.3

**Date :** 1er octobre 2025
**Statut Backend :** ✅ Healthy (local)
**Statut Frontend :** ✅ Running (local)

---

## 🚨 CRITIQUE (Bloquants déploiement)

### 1. **Initialiser Supabase Client au Startup** ❌

**Problème :**
```python
# Tests échouent avec: 'NoneType' object has no attribute 'table'
# supabase_client n'est pas initialisé au démarrage
```

**Solution :**
```python
# backend/main.py - Ajouter dans startup event:
await supabase_client.initialize()
```

**Fichier :** `backend/main.py:54` (après `orchestrator.initialize()`)

**Impact :** Tools `create_note` et `update_note` ne fonctionnent pas sans ça

---

### 2. **Appliquer Migration 004 (Hybrid Search)** ❌

**Migration :** `database/migrations/004_fix_hybrid_search.sql`

**Problème résolu :**
- SQL Error: "SELECT DISTINCT with ORDER BY expression not in select list"
- Code PostgreSQL: '42P10'

**Commande :**
```bash
# Option 1: Script Python
cd database && python apply_migration_004_psycopg2.py

# Option 2: psql direct
psql $DATABASE_URL -f database/migrations/004_fix_hybrid_search.sql
```

**Impact :** Hybrid search utilise fallback vector search sinon

---

## ⚠️ IMPORTANT (Recommandés avant production)

### 3. **Configurer API Keys Web Search** ⚠️

**Fichier :** `backend/.env`

```bash
# Actuellement commentées:
# PERPLEXITY_API_KEY=pplx-your-perplexity-key
# TAVILY_API_KEY=tvly-your-tavily-key

# À configurer pour tool web_search:
PERPLEXITY_API_KEY=pplx-xxxxx
TAVILY_API_KEY=tvly-xxxxx
```

**Impact :** Tool `web_search` échouera sans ces keys

**Optionnel :** Système fonctionne sans (agents utilisent seulement `search_knowledge`)

---

### 4. **Test End-to-End avec DB Connectée** ⚠️

**Script :**
```bash
source venv/bin/activate
python test_tools_integration.py
```

**Ce qui devrait passer après fix #1 :**
- ✅ Orchestrator Query (discussion)
- ✅ create_note (storage)
- ✅ update_note (storage)
- ✅ search_knowledge (avec résultats DB)

**Actuellement :**
- ❌ create_note fails (supabase_client not initialized)
- ❌ update_note fails (supabase_client not initialized)

---

### 5. **Mise à Jour CLAUDE.md** ⚠️

**Sections à mettre à jour :**

```markdown
## 🛠️ STRUCTURE AGENTS SCRIBE

### Agents Production (Architecture Agent-Centric avec Tools) ✅

AGENTS/
├── Plume/          # Agent restitution
│   └── Tools: [create_note, update_note] ✅ COMPLET
│
└── Mimir/          # Agent archiviste
    └── Tools: [search_knowledge, web_search, get_related_content] ✅ COMPLET

**Phase 2.3 complétée :** ✅ Tous les tools implémentés
- Tools complets (5/5)
- Tests unitaires (7/7 passés)
- Tests intégration (7/7 passés)
```

**Mettre à jour Status Phase 2.3 :**
```markdown
### 🤖 **Phase 2.3 - Agent Tools Architecture** ✅ TERMINÉE

**Date :** 1er octobre 2025
**Statut :** ✅ COMPLET - Architecture agent-centric opérationnelle

**Réalisations :**
- ✅ 4 nouveaux tools créés (web_search, get_related_content, create_note, update_note)
- ✅ PLUME_TOOLS = [create_note, update_note]
- ✅ MIMIR_TOOLS = [search_knowledge, web_search, get_related_content]
- ✅ Tests unitaires 7/7 passés
- ✅ Tests intégration 7/7 passés
- ✅ SSE streaming validé
- ✅ Discussion collaborative validée

**Détails :** `CHAP2/CR_PHASE2.3_COMPLETE.md`
```

---

## 📝 OPTIONNEL (Amélioration continue)

### 6. **Optimiser Termination Conditions AutoGen** 💡

**Problème :** Discussion peut être longue (5+ tours pour "salut")

**Solutions possibles :**
- Ajuster `MaxMessageTermination` (actuellement 10 max)
- Ajouter conditions de terminaison intelligentes
- Optimiser prompts agents pour réponses plus concises

**Impact :** Amélioration UX (réponses plus rapides)

---

### 7. **Activer Redis Cache Production** 💡

**Actuellement :** Cache en mémoire

**Amélioration :**
```bash
# .env
REDIS_URL=redis://your-redis-instance
```

**Impact :** Performance cache partagé entre instances

---

### 8. **Monitoring Production** 💡

**À configurer :**
- Sentry APM (error tracking)
- Prometheus metrics
- CloudFlare CDN

**Impact :** Observabilité production

---

## 🔄 WORKFLOW DÉPLOIEMENT

### **Étape 1 : Fixes Critiques Locaux**
```bash
cd /Users/adamdahan/Documents/SCRIBE/backend

# 1. Ajouter initialization supabase_client dans main.py
# 2. Appliquer migration 004
cd ../database
python apply_migration_004_psycopg2.py

# 3. Tester localement
cd ../backend
source venv/bin/activate
python test_tools_integration.py
```

### **Étape 2 : Tests Validation**
```bash
# Backend health check
curl http://localhost:8000/health

# Test discussion avec tools
curl -X POST http://localhost:8000/api/v1/chat/orchestrated \
  -H "Content-Type: application/json" \
  -d '{"message": "salut", "mode": "auto"}'

# Test SSE streaming
python test_sse_discussion.py
```

### **Étape 3 : Commit & Push**
```bash
git add -A
git commit -m "FEAT: Complete Agent-Centric Architecture with Tools (Phase 2.3)

- Add 4 new tools: web_search, get_related_content, create_note, update_note
- Fix rag_service.py imports and methods
- Add comprehensive tests (14/14 passed)
- Initialize supabase_client at startup
- Apply migration 004 (fix hybrid search)

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

### **Étape 4 : Déploiement Render**
1. Push déclenche auto-deploy backend + frontend
2. Appliquer migration 004 en production :
   ```bash
   # Depuis Render shell ou local avec prod DATABASE_URL
   psql $DATABASE_URL_PROD -f database/migrations/004_fix_hybrid_search.sql
   ```
3. Vérifier variables environnement Render :
   - ✅ SUPABASE_URL
   - ✅ SUPABASE_ANON_KEY
   - ✅ SUPABASE_SERVICE_KEY
   - ✅ CLAUDE_API_KEY
   - ✅ OPENAI_API_KEY
   - ⚠️ PERPLEXITY_API_KEY (optionnel)
   - ⚠️ TAVILY_API_KEY (optionnel)
4. Vérifier déploiement :
   ```bash
   curl https://scribe-api.onrender.com/health
   ```

---

## 📊 RÉSUMÉ STATUT

| Tâche | Priorité | Statut | Bloquant |
|-------|----------|--------|----------|
| Initialize supabase_client | 🚨 Critique | ❌ TODO | ✅ Oui |
| Appliquer migration 004 | 🚨 Critique | ❌ TODO | ✅ Oui |
| Configurer API keys web | ⚠️ Important | ❌ TODO | ❌ Non |
| Test E2E avec DB | ⚠️ Important | ❌ TODO | ❌ Non |
| Mise à jour CLAUDE.md | ⚠️ Important | ❌ TODO | ❌ Non |
| Optimiser termination | 💡 Optionnel | - | ❌ Non |
| Redis cache prod | 💡 Optionnel | - | ❌ Non |
| Monitoring prod | 💡 Optionnel | - | ❌ Non |

**Bloquants déploiement :** 2 tâches critiques

**Temps estimé :** 30-45 minutes (critiques + importants)

---

## ✅ VALIDATION FINALE

**Checklist avant push :**
- [ ] supabase_client initialized in main.py
- [ ] Migration 004 appliquée (local + test)
- [ ] test_tools_integration.py passe 7/7
- [ ] CLAUDE.md mis à jour
- [ ] Commit descriptif créé
- [ ] Push vers origin/main

**Checklist après déploiement :**
- [ ] Migration 004 appliquée en production
- [ ] Backend health check OK
- [ ] Frontend accessible
- [ ] Test discussion chat fonctionne
- [ ] SSE streaming fonctionne
- [ ] Logs Render sans erreurs

---

> **Phase 2.3 prête pour déploiement** après résolution des 2 bloquants critiques
