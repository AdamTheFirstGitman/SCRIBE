# 🚀 SCRIBE HANDOVER - PROMPT NOUVELLE SESSION

## 🎯 CONTEXTE PROJET

Tu prends la relève du développement de **SCRIBE**, un système de gestion de connaissances avec agents IA (Plume & Mimir). Le projet est **quasi-déployé** mais rencontre des **problèmes récurrents de deployment sur Render.com**.

## ⚠️ SITUATION ACTUELLE CRITIQUE

**Status :** Frontend no-deploy persistant malgré 15+ tentatives
**Problème :** "no-deploy" status sans logs, builds qui échouent silencieusement
**Déjà testé :** Next.js upgrade, imports relatifs, config Render, git cache reset, webpack fixes

## 🔥 PROBLÈMES RÉCURRENTS IDENTIFIÉS

1. **Node.js version conflicts** (local 23.11.0 vs .nvmrc 20.18.0)
2. **Next.js memory issues** (upgraded 14.0.3→14.2.15 pour fix OOM)
3. **Import alias @ failures** (remplacés par imports relatifs)
4. **Git cache case sensitivity** (Linux deploy vs local)
5. **Render config syntax** (yaml optimisé plusieurs fois)

## 📁 STRUCTURE PROJET

```
SCRIBE/
├── frontend/          # Next.js 14.2.15 PWA
│   ├── app/          # App Router (chat, upload, layout)
│   ├── components/   # UI components (imports relatifs)
│   ├── lib/          # Utils, API calls
│   ├── render.yaml   # Config deployment Render
│   └── package.json  # Node 20.18.0, Next 14.2.15
├── backend/          # FastAPI + agents
├── CLAUDE.md         # Doc projet optimisée
├── DEBUG.md          # Journal debug exhaustif
└── notes.md          # Notes condensées
```

## 🛠️ CONFIGURATION CRITIQUE

**Versions fixes :**
- Node.js: 20.18.0 (.nvmrc + package.json engines)
- Next.js: 14.2.15 (memory fixes Vercel)
- Imports: Chemins relatifs uniquement

**Render.yaml config :**
```yaml
services:
  - type: web
    rootDir: frontend
    buildCommand: npm ci && npm run build
    startCommand: npm start
    envVars:
      - key: PORT
        value: "10000"
      - key: HOSTNAME
        value: "0.0.0.0"
```

**Deploy hook :**
```bash
curl -X POST "https://api.render.com/deploy/srv-d3b7s9odl3ps73964ieg?key=_pf1X8o6lPA"
```

## 🎯 MISSION IMMÉDIATE

### ÉTAPE 1: DIAGNOSTIC SIMPLE
**Penser "out of the box"** - chercher des causes triviales :
- Syntaxe récente incompatible Node 18-20
- Packages manquants ou versions incompatibles
- Render.com limitations spécifiques
- Build size/memory limits
- File permissions ou paths malformés

### ÉTAPE 2: SOLUTIONS PRAGMATIQUES
- **Tests locaux d'abord** : npm run build doit marcher 100%
- **Simplification config** : enlever PWA temporairement si nécessaire
- **Alternative startCommand** : tester next start, node server.js, etc.
- **Monitoring logs** : utiliser build logs Render pour diagnostics

### ÉTAPE 3: PATTERN RECOGNITION
Observer dans DEBUG.md les **patterns qui ont marché** :
- Git cache reset après changes majeurs
- Version pinning strict (Node + Next.js)
- Imports relatifs plus fiables que alias
- Render rootDir configuration critique

## 📚 DOCUMENTATION DISPONIBLE

- **CLAUDE.md** : Config projet complète optimisée
- **DEBUG.md** : 15+ issues résolues avec solutions
- **notes.md** : Notes condensées essentielles
- **ARCHIVES/** : Docs détaillées agents (KodaF, Dako, etc.)

## 🔧 TECHNIQUES DE RÉFLEXION EFFICACES

### Smart Search Pattern
1. **WebSearch** problèmes spécifiques (Next.js + Render.com + version)
2. **Identifier patterns** dans community forums, GitHub issues
3. **Tester solutions simples** avant complex fixes
4. **Document succès** dans DEBUG.md pour future référence

### Debug Methodology
1. **One error at a time** - résoudre séquentiellement
2. **Local test first** - valider avant deploy
3. **Version control** - commit après chaque fix
4. **Pattern recognition** - réutiliser solutions qui marchent

### Out-of-the-box Thinking
- **Simplification** : enlever features complexes temporairement
- **Alternative approaches** : changer strategy si impasse
- **Community knowledge** : chercher solutions externes
- **Fresh perspective** : questionner assumptions de base

## ⚡ COMMANDES UTILES

```bash
# Build test local
cd frontend && npm run build

# Deploy trigger
curl -X POST "https://api.render.com/deploy/srv-d3b7s9odl3ps73964ieg?key=_pf1X8o6lPA"

# Git cache reset (si case sensitivity)
git rm -r --cached . && git add --all . && git commit -a -m "Fix cache"

# Clean build cache
rm -rf .next && npm run build
```

## 🎯 OBJECTIF FINAL

**Frontend SCRIBE accessible** à `https://scribe-frontend-qk6s.onrender.com`
**Backend SCRIBE déjà LIVE** à `https://scribe-api.onrender.com`

## 📝 NOTES IMPORTANTES

- **JAMAIS signer commits "Claude Code"** → Utiliser "Le King & Cloclo"
- **Toujours commit progress** même si solutions partielles
- **Documenter dans DEBUG.md** obstacles + solutions trouvées
- **Penser simple first** avant solutions complexes
- **User feedback important** : "pense out of the box", "trucs chiants qui passent à côté"

## 🚀 PRÊT POUR LA MISSION

Tu as maintenant **toutes les informations** pour:
1. Comprendre le contexte et problèmes récurrents
2. Appliquer les solutions documentées qui marchent
3. Investiguer avec techniques efficaces
4. Déployer frontend SCRIBE avec succès

**Good luck et que la force soit avec toi !** 🌟