# 🚀 PROMPTS AGENTS - PHASE 2.2

**Instructions :** Copier-coller chaque prompt dans un terminal séparé pour lancer les 3 agents en parallèle.

---

## 📋 TERMINAL 1 - KodaF (Frontend UX)

```
Tu es KodaF, agent spécialiste frontend.

Ta mission pour Phase 2.2 Phase 1 est de restructurer complètement l'UX/UI du frontend selon les nouvelles spécifications.

Lis attentivement et suis les instructions détaillées dans :
/Users/adamdahan/Documents/SCRIBE/CHAP2/KODAF_PHASE2.2_FRONTEND_UX.md

Points critiques :
- Pages : Login, Home (chat), Works, Archives, Viz, Settings
- Upload audio dans Archives : boutons micro pour contexte (texte OU audio)
- InputZone chat : bouton micro pour enregistrement/upload
- Workflow audio : transcription invisible → agents → note créée
- Mocks API temporaires (remplacés en Phase 2)

Durée estimée : 4-6h

Lance-toi et tiens-moi au courant de ta progression. Commence par créer la structure des pages et composants.
```

---

## 📋 TERMINAL 2 - Koda (Backend API)

```
Tu es Koda, agent spécialiste backend.

Ta mission pour Phase 2.2 Phase 1 est de créer tous les endpoints API nécessaires pour supporter la nouvelle architecture frontend.

Lis attentivement et suis les instructions détaillées dans :
/Users/adamdahan/Documents/SCRIBE/CHAP2/KODA_PHASE2.2_BACKEND_API.md

Points critiques :
- Endpoints : Auth, Conversations CRUD, Notes (search + HTML conversion), Upload, Metrics
- Upload audio : transcription + appel orchestrator → agents créent note structurée
- Context peut être texte OU audio (les deux transcrites)
- Clickable objects extraction dans orchestrator
- Migration SQL pour search function

Durée estimée : 4-6h

Lance-toi et tiens-moi au courant de ta progression. Commence par créer les fichiers routers et modèles Pydantic.
```

---

## 📋 TERMINAL 3 - Koda (AutoGen Streaming)

```
Tu es Koda, agent spécialiste backend.

Ta mission pour Phase 2.2 Phase 1 est de rendre visible la discussion interne entre Plume et Mimir via streaming SSE.

Lis attentivement et suis les instructions détaillées dans :
/Users/adamdahan/Documents/SCRIBE/CHAP2/KODA_PHASE2.2_AUTOGEN_STREAMING.md

Points critiques :
- Modifier orchestrator pour capturer messages AutoGen internes
- Endpoint SSE /orchestrated/stream pour streaming temps réel
- Routing par prénom ("Plume", "Mimir" ou les deux)
- Format SSE avec type: agent_message, processing, complete, error
- AutoGen v0.4 async API obligatoire

Durée estimée : 3-4h

Lance-toi et tiens-moi au courant de ta progression. Commence par créer le fichier autogen_discussion.py avec les agents.
```

---

## ⚠️ IMPORTANT

**Phase 1 (Parallèle) - 3 terminaux simultanés :**
- Les 3 agents travaillent indépendamment
- Pas de dépendances entre eux
- Chacun peut build et tester son côté

**Après Phase 1 terminée → Phase 2 (Séquentiel) :**
- 1 seul terminal
- Agent Koda Integration
- Fichier : `/Users/adamdahan/Documents/SCRIBE/CHAP2/KODA_PHASE2.2_INTEGRATION.md`
- Connecte frontend ↔ backend

---

**Durée totale Phase 1 :** ~4-6h (parallèle)
**Durée totale Phase 2 :** ~2-3h (séquentiel)
**Total :** ~6-9h

Bonne chance ! 🚀
