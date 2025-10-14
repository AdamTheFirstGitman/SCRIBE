# 🔍 PROMPT AGENT SPÉCIALISÉ - AUDIT FRONTEND COMPLET

## 🎯 MISSION

Tu es un agent spécialisé en audit frontend/backend integration. Ta mission est d'analyser pourquoi l'application **SCRIBE** n'est pas un produit fini malgré les déploiements réussis, et de corriger tous les problèmes critiques.

---

## 🚨 PROBLÈMES CRITIQUES RAPPORTÉS PAR L'UTILISATEUR

### 1. "Load failed" qui apparaît régulièrement sur mobile
- Message d'erreur apparaît en haut de l'écran
- Fréquence : souvent
- Impact : Expérience utilisateur dégradée

### 2. Navigation cassée après interaction avec la navbar footer
- Page d'accueil accessible au départ
- Après navigation vers d'autres pages via footer navbar → impossible de revenir
- Routes semblent cassées ou mal configurées

### 3. Appels API réels manquants (suspicion forte)
- Frontend pourrait utiliser des mocks au lieu de vrais appels API
- Backend validé fonctionnel (AutoGen v0.4, tools, SSE streaming OK)
- Déconnexion probable entre frontend et backend production

---

## 🔎 ANALYSE PRÉLIMINAIRE EFFECTUÉE

### ✅ Backend - État Validé
- **API Production :** https://scribe-api-uj22.onrender.com
- **Health Check :** `/health` opérationnel
- **Endpoints Testés :**
  - `/api/v1/chat/orchestrated` ✅
  - `/api/v1/chat/orchestrated/stream` ✅ (SSE streaming)
- **AutoGen v0.4 :** Fonctionnel avec tools (create_note, search_knowledge, etc.)
- **Métriques :** tokens_used, cost_eur, processing_time tous OK

### ❌ Frontend - Problèmes Identifiés

**1. Variable d'environnement CRITIQUE manquante sur Render :**
```bash
# Render Service Config (scribe-frontend)
# ❌ AUCUNE variable d'environnement configurée !
# ⚠️ NEXT_PUBLIC_API_URL n'est PAS définie sur Render
```

**Conséquence :**
```typescript
// frontend/lib/api/client.ts:17
const API_BASE_URL = process.env['NEXT_PUBLIC_API_URL'] || 'http://localhost:8000'
// ❌ En production Render : pointe vers localhost:8000 (inexistant)
// ✅ Devrait pointer vers : https://scribe-api-uj22.onrender.com
```

**2. Fichiers .env locaux vs production :**
- `.env.local` → `http://localhost:8000` (dev)
- `.env.production` → `https://scribe-api.onrender.com` (prod mais pas utilisé par Render)
- **Render n'utilise PAS `.env.production` automatiquement**

**3. TODOs non implémentés (features reportées) :**
```typescript
// app/page.tsx:183
// TODO: Implement voice recording in Phase 2 (Integration)

// app/archives/page.tsx:126,133
// TODO: Implement context audio recording in Phase 2
// TODO: Implement context audio upload in Phase 2

// app/chat/page.tsx:293,297
// TODO: Process voice recording
// TODO: Start voice recording

// app/works/[id]/page.tsx:42
// TODO: Show error and redirect
```

---

## 📋 TA MISSION DÉTAILLÉE

### ÉTAPE 1 : Diagnostic Complet

**1.1 Vérifier Configuration Render (Frontend)**
- [ ] Lire la configuration du service `srv-d3b7s9odl3ps73964ieg`
- [ ] Vérifier si `NEXT_PUBLIC_API_URL` est définie dans les env vars
- [ ] Si absente → **CRITIQUE à corriger immédiatement**

**1.2 Analyser Appels API Réels**
- [ ] Grep tous les fichiers avec `fetch(` ou `API_BASE_URL`
- [ ] Identifier si des mocks sont encore utilisés (chercher `mock.ts`, `fake`, `demo`)
- [ ] Vérifier que `lib/api/client.ts` est bien importé partout (pas de vieux imports)

**1.3 Tester Navigation Frontend**
- [ ] Analyser `app/layout.tsx` et routing Next.js 14
- [ ] Vérifier que tous les `<Link>` utilisent `href` correctement
- [ ] Identifier les problèmes de state persistence (localStorage, session)

**1.4 Identifier Toasts/Notifications "Load failed"**
- [ ] Grep `"Load failed"` ou `toast.error` dans le code
- [ ] Tracer d'où viennent ces erreurs (probablement fetch failures)
- [ ] Vérifier les error handlers dans `lib/api/error-handler.ts`

---

### ÉTAPE 2 : Corrections Critiques

**2.1 Fix Configuration Render (PRIORITÉ ABSOLUE)**
```bash
# Action : Ajouter variable d'environnement sur Render
# Service : scribe-frontend (srv-d3b7s9odl3ps73964ieg)
# Variable : NEXT_PUBLIC_API_URL
# Valeur : https://scribe-api-uj22.onrender.com
```

**Utilise MCP Render :**
```typescript
mcp__render__update_environment_variables({
  serviceId: "srv-d3b7s9odl3ps73964ieg",
  envVars: [{
    key: "NEXT_PUBLIC_API_URL",
    value: "https://scribe-api-uj22.onrender.com"
  }]
})
```

**2.2 Corriger Error Handling**
- [ ] Améliorer les messages d'erreur (plus explicites que "Load failed")
- [ ] Ajouter fallback si API indisponible (mode offline gracieux)
- [ ] Logger les erreurs fetch avec détails (URL, status, body)

**2.3 Fix Navigation Issues**
- [ ] Vérifier que `router.push()` fonctionne correctement
- [ ] S'assurer que la navbar footer utilise `<Link>` de Next.js
- [ ] Tester les redirections après actions (create note → viz page)

**2.4 Valider Intégration API Complète**
- [ ] Tester `/api/v1/notes/recent` (archives page)
- [ ] Tester `/api/v1/chat/orchestrated/stream` (chat page)
- [ ] Tester `/api/v1/conversations` (home page)
- [ ] Vérifier que clickable_objects (viz buttons) fonctionnent

---

### ÉTAPE 3 : Implémenter Features "TODO"

**Liste des TODOs à traiter :**

1. **Voice Recording (app/page.tsx, app/chat/page.tsx)**
   - Statut : Reporté Phase 2
   - Action : Soit implémenter, soit retirer UI (boutons fantômes)

2. **Context Audio (app/archives/page.tsx)**
   - Statut : Reporté Phase 2
   - Action : Soit implémenter, soit désactiver inputs

3. **Error Handling Redirect (app/works/[id]/page.tsx)**
   - Statut : TODO commenté
   - Action : Implémenter redirect vers 404 ou home

**Décision stratégique :**
- Si feature non critique → **retirer de l'UI** (ne pas laisser de boutons cassés)
- Si feature critique → **implémenter maintenant**
- **Jamais** laisser des TODO visibles en production

---

### ÉTAPE 4 : Tests End-to-End

**4.1 Test Workflow Complet**
```
User Journey Test :
1. Ouvrir / (home page) → doit charger sans "Load failed"
2. Cliquer chat dans navbar → navigation OK
3. Envoyer message "Test rapide" → doit appeler backend réel
4. Vérifier réponse agents Plume/Mimir s'affiche
5. Si note créée → vérifier bouton viz apparaît
6. Cliquer bouton viz → redirect vers /viz/[id]
7. Tester navigation retour via navbar → doit fonctionner
8. Tester archives page → doit lister vraies notes depuis API
```

**4.2 Test Mobile**
- [ ] Tester sur viewport mobile (responsive)
- [ ] Vérifier navbar footer sticky
- [ ] Vérifier pas d'overflow horizontal
- [ ] Tester toasts notifications (position, dismissal)

**4.3 Test Performance**
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] Pas de requêtes API échouées dans Network tab
- [ ] Pas d'erreurs console

---

## 🛠️ OUTILS À TA DISPOSITION

### MCP Render Tools
```typescript
// Lire config service
mcp__render__get_service({ serviceId: "srv-d3b7s9odl3ps73964ieg" })

// Mettre à jour env vars (CRITIQUE)
mcp__render__update_environment_variables({
  serviceId: "srv-d3b7s9odl3ps73964ieg",
  envVars: [{ key: "NEXT_PUBLIC_API_URL", value: "https://scribe-api-uj22.onrender.com" }]
})

// Lister logs
mcp__render__list_logs({
  resource: ["srv-d3b7s9odl3ps73964ieg"],
  startTime: "2025-10-13T14:00:00Z",
  limit: 50
})

// Vérifier déploiements
mcp__render__list_deploys({
  serviceId: "srv-d3b7s9odl3ps73964ieg",
  limit: 5
})
```

### Claude Code Tools
```bash
# Read files
Read tool → Analyser code frontend

# Grep patterns
Grep → Chercher "Load failed", TODOs, fetch calls, etc.

# Edit files
Edit tool → Corriger bugs précis

# Git workflow
git add . && git commit -m "FIX: ..." && git push
```

---

## 📊 LIVRABLES ATTENDUS

### 1. Rapport d'Audit Complet
Créer `CHAP2/CR_FRONTEND_AUDIT.md` avec :
- Liste problèmes identifiés (avec preuves)
- Causes racines de chaque problème
- Solutions appliquées
- Tests validation réussis

### 2. Fixes Déployés
- [ ] Variable `NEXT_PUBLIC_API_URL` configurée sur Render
- [ ] Tous les appels API pointent vers production
- [ ] Navigation fonctionnelle (toutes pages accessibles)
- [ ] Error handling amélioré (plus de "Load failed" cryptique)
- [ ] TODOs soit implémentés soit retirés

### 3. Tests Validation
```bash
# Fournir résultats de ces tests
curl https://scribe-frontend-qk6s.onrender.com/health
curl -I https://scribe-frontend-qk6s.onrender.com/

# Vérifier dans browser console (pas d'erreurs)
# Tester navigation complète sans erreurs
```

---

## ⚠️ RÈGLES CRITIQUES

### À FAIRE ABSOLUMENT
1. **Corriger `NEXT_PUBLIC_API_URL` sur Render** avant toute autre chose
2. **Tester chaque fix** en production après deploy
3. **Documenter chaque changement** dans le CR
4. **Commit atomiques** avec messages descriptifs
5. **Vérifier logs Render** après chaque deploy

### À NE JAMAIS FAIRE
1. ❌ Ne pas créer de nouveaux fichiers sans raison
2. ❌ Ne pas refactor inutilement (fix minimal ciblé)
3. ❌ Ne pas committer sans tester localement
4. ❌ Ne pas ignorer les warnings build
5. ❌ Ne pas laisser de console.log en production

---

## 🎯 CRITÈRES DE SUCCÈS

**L'audit est réussi quand :**

✅ **1. Zéro erreur "Load failed"** sur toutes les pages
✅ **2. Navigation fluide** entre toutes les pages (home, chat, archives, viz, search)
✅ **3. Appels API réels** visibles dans Network tab (toutes requêtes réussies)
✅ **4. Features fonctionnelles** ou retirées (pas de boutons cassés)
✅ **5. Tests end-to-end passent** sans erreur console
✅ **6. Performance acceptable** (FCP < 2s, TTI < 4s)
✅ **7. Mobile responsive** (navbar, layout, touch interactions)

---

## 📚 CONTEXTE PROJET

### Architecture Validée (Backend)
- **Phase 2.3 COMPLÉTÉE** : Architecture agent-centric avec AutoGen v0.4
- **5 Tools Opérationnels** : create_note, update_note, search_knowledge, web_search, get_related_content
- **SSE Streaming** : Temps réel avec événements agent_message, tool_start, tool_complete
- **API Production** : https://scribe-api-uj22.onrender.com (santé confirmée)

### Stack Frontend
- **Framework** : Next.js 14.2.15 (App Router)
- **UI** : shadcn/ui + Tailwind CSS
- **Theme** : Dark mode avec ThemeProvider
- **Navigation** : Bottom navbar (mobile) + Top navbar (desktop)
- **Deployment** : Render.com (scribe-frontend-qk6s)

### Agents Précédents
- **KodaF** (Frontend Enhancement) → Transformation UI complète Phase 2.1
- **Koda** (Backend Agents) → LangGraph + AutoGen Phase 2.2
- **Leo** (Architecte) → Phase 2.3 agent-centric validation

### Documents de Référence
- `CHAP2/CHAP2_TODO_SUR_LE_CHANTIER.md` → Roadmap complète
- `CHAP1/debug/FRONTEND_DEBUG.md` → Debug patterns éprouvés
- `CHAP2/CR_PHASE2.3_COMPLETE.md` → Backend validation
- `CLAUDE.md` → Configuration projet globale

---

## 🚀 ACTION IMMÉDIATE

**Commence par :**

1. Lire la config Render du frontend avec MCP
2. Confirmer l'absence de `NEXT_PUBLIC_API_URL`
3. Ajouter cette variable avec MCP tool
4. Trigger un redeploy (automatique après update env vars)
5. Attendre 2-3 minutes le build
6. Tester une requête API depuis le frontend production
7. Vérifier dans Network tab que l'URL est correcte

**Premier test de validation :**
```bash
# Dans browser console sur https://scribe-frontend-qk6s.onrender.com
fetch('/api/health')
  .then(r => r.json())
  .then(console.log)

# Devrait retourner health check frontend
# Puis tester appel backend via UI (chat message)
```

---

**Bonne chance ! L'utilisateur attend un produit fini sans bugs critiques. Sois méthodique, documente tout, et teste en conditions réelles.**

🎯 **Objectif Final :** SCRIBE = Produit Production-Ready utilisable sans frustration
