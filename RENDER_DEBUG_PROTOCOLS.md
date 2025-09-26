# 🛠️ RENDER DEBUG PROTOCOLS - Dako's Field Guide

## 🎯 MISSION CONTEXT
**Frontend SCRIBE déployé avec succès après 20+ tentatives**
Documentation des patterns récurrents et solutions systematiques pour éviter les boucles d'erreurs.

---

## 📋 SYMPTÔMES CLASSIQUES & DIAGNOSTICS

### 🚨 SYMPTÔME 1: "Pas de logs de déploiement"
**Manifestation:** Push git → aucun log Render, service silencieux
**Causes possibles:**
- buildFilter paths incorrects
- Service Render cassé/bloqué
- Cache déploiement corrompu
- Changements ne touchent pas les paths surveillés

**PROTOCOLE DE RÉSOLUTION:**
1. **Vérifier buildFilter** dans render.yaml
   ```yaml
   buildFilter:
     paths:
     - frontend/**  # Vérifier chemin exact
   ```
2. **Forcer détection** avec changement critique (health endpoint, package.json)
3. **Si toujours pas de logs:** Service Render nécessite intervention

### 🚨 SYMPTÔME 2: "ReferenceError: navigator is not defined"
**Manifestation:** Build réussit localement, échoue sur Render avec erreurs SSR
**Cause:** Browser APIs utilisées pendant server-side rendering

**PROTOCOLE DE RÉSOLUTION:**
1. **Identifier tous les usages navigator:**
   ```bash
   grep -r "navigator" **/*.tsx **/*.ts
   ```
2. **Pattern SSR-safe obligatoire:**
   ```typescript
   // ❌ MAUVAIS - SSR crash
   const [isOnline, setIsOnline] = useState(navigator.onLine)

   // ✅ BON - SSR safe
   const [isOnline, setIsOnline] = useState(true)
   useEffect(() => {
     setIsOnline(navigator.onLine)
   }, [])
   ```
3. **Zones critiques à vérifier:**
   - Components dans layout.tsx (affectent toutes les pages)
   - useState avec browser APIs
   - Imports sans typeof checks

### 🚨 SYMPTÔME 3: "TypeScript not found"
**Manifestation:** Build dit "Please install typescript"
**Cause:** devDependencies pas installées en production

**PROTOCOLE DE RÉSOLUTION:**
1. **Déplacer TypeScript en dependencies:**
   ```json
   "dependencies": {
     "typescript": "^5.9.2"
   }
   ```
2. **Alternative - Variables env:**
   ```yaml
   envVars:
     - key: ESLINT_NO_DEV_ERRORS
       value: "true"
   ```

### 🚨 SYMPTÔME 4: "npm workspace conflicts"
**Manifestation:** Erreurs résolution dépendances, rootDir vs workspace
**Cause:** Monorepo config incompatible avec Render rootDir

**PROTOCOLE DE RÉSOLUTION:**
1. **Supprimer workspaces du root package.json**
2. **Générer package-lock.json autonome:**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```
3. **Commit package-lock.json local**

---

## 🧠 REFLEXES DE DEBUG SYSTÈME

### 🔍 PRINCIPE 1: "Comparaison Local vs Production"
**Quand:** Build local OK, Render KO
**Action:** Analyser différences environnement
- Node version (local vs Render)
- npm behavior (dev vs prod)
- Variables environnement
- Dépendances installées

### 🔍 PRINCIPE 2: "Pattern Recognition"
**Quand:** Même symptôme répété
**Action:** Chercher causes similaires
- "Pas de logs" = buildFilter ou détection
- "SSR errors" = Browser APIs mal utilisées
- "Module not found" = Dépendances mal placées

### 🔍 PRINCIPE 3: "Isolation Progressive"
**Quand:** Erreur complexe
**Action:** Simplifier jusqu'au minimum viable
- Remove next-pwa → basic Next.js
- Remove testing deps → core only
- Remove experimental config → stable config

### 🔍 PRINCIPE 4: "Configuration Cohérence"
**Quand:** Multiples services (frontend/backend)
**Action:** Vérifier alignement
- render.yaml paths vs structure réelle
- Environment variables consistency
- API URLs pointing correctly

---

## 📖 LEÇONS SPÉCIFIQUES SCRIBE

### ❌ ERREURS RÉCURRENTES À ÉVITER

1. **TypeScript double-install** dans buildCommand + devDeps
2. **Navigator usage** sans SSR protection
3. **buildFilter trop restrictif** rate les changements
4. **Workspace config** avec rootDir approach
5. **Dependencies vs devDependencies** confusion production

### ✅ BONNES PRATIQUES APPLIQUÉES

1. **Frontend autonome** (pas de workspace)
2. **SSR-safe patterns** systématiques
3. **Minimal Next.js config** pour éviter complexité
4. **Production dependencies** pour outils requis
5. **Health endpoints** pour monitoring

---

## 🚀 WORKFLOW DE DÉPLOIEMENT OPTIMISÉ

### Phase 1: Pre-Deploy Checks
```bash
# Local build test
npm run build

# Dependencies audit
npm ls | grep typescript

# SSR patterns check
grep -r "navigator\." **/*.tsx
```

### Phase 2: Deploy Strategy
1. **Commit par petites unités** (1 problème = 1 commit)
2. **Wait for logs** avant nouveau push
3. **Force detection** si pas de logs
4. **Debug systematic** selon protocoles

### Phase 3: Post-Deploy Validation
- Health check endpoints
- API connectivity
- Core functionalities

---

## 🎯 COACHING POINTS POUR DAKO

### 🧘 MINDSET CHANGES
- **"Pas de logs" ≠ "ça marche pas"** → Diagnostic buildFilter
- **"Ça marche local" ≠ "ça va marcher prod"** → Env differences matter
- **"Même erreur" = "Même pattern"** → Use protocols, not guessing

### 🛠️ TECHNICAL REFLEXES
1. **Browser APIs:** Toujours useEffect wrapper
2. **Dependencies:** Production needs vs dev needs
3. **Monorepo:** Workspace vs rootDir conflicts
4. **Render:** buildFilter paths critical

### 🔄 ITERATION STRATEGY
- **Small commits** avec diagnostic clear
- **Pattern recognition** avant trial/error
- **Environment awareness** systematic
- **Protocol application** over improvisation

---

> **RÉSULTAT:** Frontend SCRIBE déployé après protocoles appliqués
> **OBJECTIF:** Zero boucles d'erreurs sur futurs projets Render
>
> *"Debug smart, not hard"* - Dako 2024
