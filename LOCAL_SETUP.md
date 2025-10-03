# SCRIBE - Setup Local pour Tests

## 🎯 Environnement Préparé

✅ **Backend :**
- Python venv créé avec Python 3.13
- Toutes les dépendances installées
- Script de lancement : `backend/run_local.sh`

✅ **Frontend :**
- Node modules déjà installés
- `.env.local` configuré pour backend local
- Script de lancement : `frontend/run_local.sh`

✅ **Database :**
- Schéma Supabase appliqué (`schema_v2_phase22.sql`)
- Tables : notes, conversations, embeddings, etc.
- Fonction search fulltext configurée

---

## 🚀 Lancer les Tests Locaux

### Terminal 1 - Backend

```bash
cd /Users/adamdahan/Documents/SCRIBE/backend
./run_local.sh
```

**Devrait afficher :**
```
🚀 Starting SCRIBE Backend...
✅ Environment ready
📡 Backend will run on: http://127.0.0.1:8000
📚 API Docs: http://127.0.0.1:8000/docs

INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**En cas d'erreur :**
- Vérifier que `.env` existe dans `backend/` avec toutes les clés (SUPABASE_URL, OPENAI_API_KEY, etc.)
- Si module manquant : `./venv/bin/pip install <module>`

### Terminal 2 - Frontend

```bash
cd /Users/adamdahan/Documents/SCRIBE/frontend
./run_local.sh
```

**Devrait afficher :**
```
🚀 Starting SCRIBE Frontend...
✅ Environment ready
🌐 Frontend will run on: http://localhost:3000
🔗 API Backend: http://localhost:8000

- Local:        http://localhost:3000
```

**En cas d'erreur :**
- Si port 3000 occupé : `kill -9 $(lsof -ti:3000)` puis relancer
- Si dépendances manquantes : `npm install`

---

## 🧪 Checklist Tests

Ouvrir : http://localhost:3000

### 1. ✅ Login
- Taper n'importe quel username/password
- Devrait rediriger vers chat

### 2. ✅ Chat Streaming
- Envoyer : "Bonjour"
- Observer : Messages Plume et/ou Mimir apparaissent en temps réel
- Vérifier : Pas d'erreur console

### 3. ✅ Archives - Upload Texte
- Aller : Archives
- Coller texte dans textarea
- Cliquer "Créer la note"
- Vérifier : Redirige vers /viz/[id] avec la note

### 4. ✅ Archives - Upload Audio
- Aller : Archives → Onglet "Audio"
- Upload fichier audio (mp3, wav, webm, etc.)
- Observer : "Transcription et traitement en cours..."
- Vérifier : Note créée avec transcription Whisper

### 5. ✅ Search Notes
- Aller : Archives
- Chercher : "test" (ou n'importe quel mot d'une note)
- Vérifier : Résultats affichés avec snippets

### 6. ✅ Viz - HTML Conversion
- Cliquer sur une note
- Toggle TEXT → HTML
- Observer : Conversion polling (2s interval, max 30s)
- Vérifier : Toast "Conversion HTML terminée"

### 7. ✅ Context Chat depuis Viz
- Dans viz, cliquer bouton chat (bottom-right)
- Vérifier : Redirige vers home avec banner "📎 Contexte: [titre note]"
- Envoyer message : Devrait inclure contexte note

### 8. ✅ Works - Conversations
- Aller : Works
- Vérifier : Liste des conversations
- Cliquer sur une conversation
- Vérifier : Messages chargés

### 9. ✅ Settings - Metrics
- Aller : Settings
- Vérifier : Métriques (total notes, conversations, tokens, coûts)
- Logout : Devrait rediriger vers login

---

## ❌ Erreurs Attendues (Normales)

### Upload Audio échoue
**Cause :** Clé OpenAI invalide ou crédit insuffisant
**Solution :** Vérifier `OPENAI_API_KEY` dans `backend/.env`

### Search retourne 0 résultats
**Cause :** Base de données vide (première utilisation)
**Solution :** Créer quelques notes d'abord, puis chercher

### CORS errors
**Cause :** Backend pas démarré ou mauvaise URL
**Solution :** Vérifier backend tourne sur `http://localhost:8000`

### Chat ne stream pas
**Cause :** AutoGen ou agents non configurés
**Solution :** Vérifier `CLAUDE_API_KEY` dans `backend/.env`

---

## 🐛 Debug Backend

**Logs détaillés :**
```bash
# Backend logs en temps réel
tail -f backend/*.log  # Si logs fichiers configurés
```

**Test API directement :**
```bash
# Health check
curl http://localhost:8000/health

# API docs interactive
open http://localhost:8000/docs
```

**Console Python :**
```bash
cd backend
./venv/bin/python
>>> from config import settings
>>> print(settings.SUPABASE_URL)
```

---

## 🐛 Debug Frontend

**Console Browser :**
- F12 → Console
- Vérifier erreurs réseau (Network tab)
- Vérifier API calls vers `http://localhost:8000`

**Variables environnement :**
```bash
cat frontend/.env.local
# Devrait afficher : NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Clear cache Next.js :**
```bash
cd frontend
rm -rf .next
npm run dev
```

---

## 📊 Status Attendu

**Backend :**
- ✅ Démarre sans erreur
- ✅ Health check accessible
- ✅ Logs montrent "Application startup complete"
- ✅ Pas d'erreur import modules

**Frontend :**
- ✅ Build réussit
- ✅ Accessible http://localhost:3000
- ✅ Pas d'erreur console au chargement
- ✅ Toast notifications fonctionnent (sonner)

**Database :**
- ✅ Tables créées (notes, conversations, embeddings, etc.)
- ✅ Fonction `search_notes_fulltext` existe
- ✅ Connexion Supabase OK

---

## 🚀 Prochaines Étapes Après Tests

Si tests locaux OK :
1. Commit changes
2. Push vers GitHub
3. Render redéploie automatiquement
4. Tester URLs production
5. Documenter dans CR final

Si tests échouent :
1. Noter erreurs exactes
2. Vérifier variables environnement
3. Tester endpoints un par un
4. Demander assistance si bloqué

---

**Setup créé le :** $(date)
**Python version :** 3.13.3
**Node version :** 20.18.0
**Next.js version :** 14.2.33
