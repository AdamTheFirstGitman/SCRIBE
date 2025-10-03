# 🎨 KODAF - Phase 2.2 : Frontend UX Restructure

**Agent :** KodaF (Frontend Specialist)
**Phase :** 2.2 - Phase 1 (Parallèle)
**Durée estimée :** 4-6 heures
**Status :** 🚧 À EXÉCUTER

---

## 🎯 OBJECTIF

Restructurer complètement l'architecture UX/UI du frontend selon la nouvelle vision utilisateur. Créer une application cohérente centrée sur le chat avec les agents, la gestion de notes et l'historique de conversations.

**Priorité :** Interface utilisable immédiatement, workflow fluide, design cohérent avec Phase 2.1.

---

## 📊 ARCHITECTURE ACTUELLE (Phase 2.1)

**Pages existantes :**
- `/` : Page d'accueil générique
- `/chat` : Interface chat avec sélection Plume/Mimir
- `/upload` : Upload de documents
- `/health` : Health check
- `/settings` : Settings basiques

**Composants existants :**
- Navigation (mobile + desktop)
- ThemeProvider (dark/light/system)
- Command Palette (Ctrl+K)
- Keyboard shortcuts
- OfflineStatus

**À CONSERVER :**
- ThemeProvider
- Navigation (mais restructurer les liens)
- shadcn/ui components
- Tailwind + framer-motion

**À REMPLACER/RESTRUCTURER :**
- Page d'accueil → Login + Chat vierge
- Page upload → Intégrer dans Archives
- Page chat → Simplifier (devient page Home après login)

---

## 🏗️ NOUVELLE ARCHITECTURE

### **Pages Principales**

#### 1. **`/login` - Page Login**
**Route :** `/login`
**Accessible :** Non authentifié uniquement

**Spécifications :**
- Design simple et épuré (pas de landing page marketing)
- Formulaire centré avec :
  - Input text "Identifiant" (valeur attendue : `King`)
  - Input password "Mot de passe" (valeur attendue : `Faire la diff`)
  - Bouton "Se connecter"
- Validation côté client simple
- Après login → localStorage : `{user_id: 'king_001', logged_in: true, expires: Date.now() + 30*24*3600*1000}`
- Redirection vers `/` (Home)

**Design :**
```tsx
<div className="min-h-screen flex items-center justify-center bg-gray-950">
  <Card className="w-full max-w-md">
    <CardHeader>
      <h1>SCRIBE - Plume & Mimir</h1>
      <p>Accès à votre espace de connaissances</p>
    </CardHeader>
    <CardContent>
      <form>
        <Input label="Identifiant" />
        <Input type="password" label="Mot de passe" />
        <Button>Se connecter</Button>
      </form>
    </CardContent>
  </Card>
</div>
```

---

#### 2. **`/` - Home (Chat Vierge)**
**Route :** `/`
**Accessible :** Authentifié uniquement
**Redirection :** Si non auth → `/login`

**Spécifications :**
- Page d'accueil = Chat directement utilisable
- Pas de messages de bienvenue pré-remplis
- Chat vierge, InputZone fixée en bas
- Navigation visible (accès Works, Archives, Settings)

**Layout :**
```tsx
<div className="min-h-screen flex flex-col">
  <Navigation /> {/* Déjà existant */}

  <main className="flex-1 overflow-y-auto pb-24">
    {/* Zone messages - vide au départ */}
    <div className="max-w-4xl mx-auto space-y-4 p-4">
      {messages.length === 0 && (
        <EmptyState
          icon={MessageSquare}
          title="Nouvelle conversation"
          description="Posez une question à Plume et Mimir"
        />
      )}
      {messages.map(msg => <ChatMessage key={msg.id} message={msg} />)}
    </div>
  </main>

  {/* Input Zone fixe en bas */}
  <InputZone fixed />
</div>
```

**Comportement :**
- Scroll automatique vers bas quand nouveau message
- InputZone toujours visible (position fixed bottom)
- Messages avec objets clickables (viz_link, web_link)

---

#### 3. **`/works` - Historique Conversations**
**Route :** `/works`
**Accessible :** Authentifié uniquement

**Spécifications :**
- Liste de toutes les conversations passées
- Chaque conversation = Card clickable avec :
  - **Titre** (gauche, gras) - généré par LLM ou "Conversation du [date]"
  - **Archives concernées** (ligne du dessous) - Liste titres notes séparés par virgule, "..." si déborde
  - **Date** (droite) - Format relatif : "Aujourd'hui", "Hier", "3 jours", "15 mars 2025"
- Cliquer sur card → ouvre chat avec historique complet (route `/works/{conversation_id}`)
- Ordre chronologique inverse (plus récent en haut)

**Design :**
```tsx
<div className="min-h-screen">
  <Navigation />

  <main className="max-w-4xl mx-auto p-4">
    <h1 className="text-2xl font-bold mb-6">Conversations</h1>

    <div className="space-y-3">
      {conversations.map(conv => (
        <Card
          key={conv.id}
          onClick={() => router.push(`/works/${conv.id}`)}
          className="cursor-pointer hover:border-plume-500/50 transition"
        >
          <CardContent className="p-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="font-semibold text-lg">{conv.title}</h3>
                <p className="text-sm text-gray-400 mt-1">
                  {conv.note_titles.slice(0, 3).join(', ')}
                  {conv.note_titles.length > 3 && '...'}
                </p>
              </div>
              <span className="text-sm text-gray-500 ml-4">
                {formatRelativeDate(conv.updated_at)}
              </span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  </main>
</div>
```

**Route conversation spécifique :**
`/works/[conversation_id]` → même layout que Home mais avec messages pré-chargés

---

#### 4. **`/archives` - Gestion Notes**
**Route :** `/archives`
**Accessible :** Authentifié uniquement

**Spécifications :**

**Section 1 : Recents (5 dernières notes)**
- Liste des 5 notes modifiées le plus récemment
- Format : Card clickable
  - **Titre** (gauche)
  - **"Last update: [date]"** ou **"Created on: [date]"** (droite)
- Cliquer → ouvre `/viz/{note_id}` en mode HTML
- Bouton "Voir tout" en bas → ouvre liste complète (route `/archives/all`)

**Section 2 : Recherche**
- Barre de recherche fulltext
- Placeholder : "Rechercher dans vos notes..."
- Recherche dans titre + contenu textuel
- Résultats en temps réel (debounced 300ms)

**Section 3 : Upload**
- Deux modes : **Texte** et **Audio**
- Toggle entre les deux modes
- **Informations contextuelles** peuvent être texte OU audio (micro/upload)

**Upload Texte :**
```tsx
<Card>
  <CardHeader>
    <h2>Créer une note</h2>
  </CardHeader>
  <CardContent>
    <Textarea
      placeholder="Collez votre texte ici..."
      rows={8}
    />

    {/* Context input - texte OU audio */}
    <div className="mt-4">
      <label className="text-sm text-gray-400">
        Informations contextuelles (optionnel)
      </label>
      <div className="flex gap-2 mt-2">
        <Textarea
          placeholder="Ajoutez du contexte..."
          rows={2}
          className="flex-1"
        />
        <div className="flex flex-col gap-2">
          {/* Micro pour context audio */}
          <Button
            variant="outline"
            size="icon"
            onClick={() => recordContextAudio()}
            title="Enregistrer contexte audio"
          >
            <Mic className="h-4 w-4" />
          </Button>
          {/* Upload fichier audio context */}
          <Button
            variant="outline"
            size="icon"
            onClick={() => uploadContextAudio()}
            title="Upload fichier audio contexte"
          >
            <Upload className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>

    <Button className="mt-4">Créer la note</Button>
  </CardContent>
</Card>
```

**Upload Audio :**
```tsx
<Card>
  <CardHeader>
    <h2>Créer note depuis audio</h2>
  </CardHeader>
  <CardContent>
    {/* Upload audio principal */}
    <div className="border-2 border-dashed rounded-lg p-8 text-center">
      <input
        type="file"
        accept="audio/*"
        onChange={handleAudioUpload}
        className="hidden"
        id="audio-upload"
      />
      <label htmlFor="audio-upload" className="cursor-pointer">
        <Upload className="h-8 w-8 mx-auto mb-2 text-gray-400" />
        <p className="text-sm">Cliquez ou glissez un fichier audio</p>
        <p className="text-xs text-gray-500 mt-1">
          Formats : mp3, wav, m4a, webm, ogg
        </p>
      </label>
    </div>

    {/* Context input - texte OU audio */}
    <div className="mt-4">
      <label className="text-sm text-gray-400">
        Informations contextuelles (optionnel)
      </label>
      <div className="flex gap-2 mt-2">
        <Textarea
          placeholder="Ajoutez du contexte..."
          rows={2}
          className="flex-1"
        />
        <div className="flex flex-col gap-2">
          {/* Micro pour context audio */}
          <Button
            variant="outline"
            size="icon"
            onClick={() => recordContextAudio()}
            title="Enregistrer contexte audio"
          >
            <Mic className="h-4 w-4" />
          </Button>
          {/* Upload fichier audio context */}
          <Button
            variant="outline"
            size="icon"
            onClick={() => uploadContextAudio()}
            title="Upload fichier audio contexte"
          >
            <Upload className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>

    <Button className="mt-4" disabled={!audioFile}>
      Créer la note
    </Button>

    {/* Loading state pendant transcription + traitement agents */}
    {isProcessing && (
      <div className="mt-4 flex items-center gap-2 text-sm text-gray-400">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Transcription et traitement en cours...</span>
      </div>
    )}
  </CardContent>
</Card>
```

**Workflow Upload Audio :**
1. User upload fichier audio principal + optionnel context (texte OU audio)
2. (Invisible) Transcription Whisper audio principal
3. (Invisible) Transcription Whisper context audio si présent
4. (Invisible) Envoi aux agents : "Crée une note basée sur : [transcription] + contexte: [context]"
5. (Invisible) Agents (Plume) structurent et créent note
6. User voit note créée + peut la visualiser

**Layout complet :**
```tsx
<div className="min-h-screen">
  <Navigation />

  <main className="max-w-4xl mx-auto p-4 space-y-6">
    {/* Section 1: Recents */}
    <section>
      <h2 className="text-xl font-bold mb-4">Notes récentes</h2>
      <div className="space-y-2">
        {recentNotes.map(note => (
          <Card key={note.id} onClick={() => router.push(`/viz/${note.id}`)}>
            <CardContent className="p-3 flex justify-between items-center">
              <span className="font-medium">{note.title}</span>
              <span className="text-sm text-gray-500">
                {note.updated_at > note.created_at
                  ? `Last update: ${formatDate(note.updated_at)}`
                  : `Created on: ${formatDate(note.created_at)}`
                }
              </span>
            </CardContent>
          </Card>
        ))}
      </div>
      <Button variant="outline" className="w-full mt-3">
        Voir tout
      </Button>
    </section>

    {/* Section 2: Search */}
    <section>
      <Input
        type="search"
        placeholder="Rechercher dans vos notes..."
        icon={Search}
        onChange={debouncedSearch}
      />
      {searchResults.length > 0 && (
        <div className="mt-3 space-y-2">
          {searchResults.map(note => (
            <Card key={note.id} onClick={() => router.push(`/viz/${note.id}`)}>
              <CardContent className="p-3">
                <h3 className="font-medium">{note.title}</h3>
                <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                  {note.snippet}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </section>

    {/* Section 3: Upload */}
    <section>
      <div className="flex gap-2 mb-4">
        <Button
          variant={uploadMode === 'text' ? 'default' : 'outline'}
          onClick={() => setUploadMode('text')}
        >
          Texte
        </Button>
        <Button
          variant={uploadMode === 'audio' ? 'default' : 'outline'}
          onClick={() => setUploadMode('audio')}
        >
          Audio
        </Button>
      </div>

      {uploadMode === 'text' ? <UploadTextForm /> : <UploadAudioForm />}
    </section>
  </main>
</div>
```

**Route liste complète :**
`/archives/all` → même design que Recents mais avec pagination/infinite scroll

---

#### 5. **`/viz/[note_id]` - Visualisation Note**
**Route :** `/viz/{note_id}`
**Accessible :** Authentifié uniquement

**Spécifications :**

**Header (sticky top) :**
```tsx
<div className="sticky top-0 bg-gray-900/95 backdrop-blur border-b border-gray-800 p-3 flex items-center justify-between z-10">
  {/* Gauche : Bouton retour */}
  <Button variant="ghost" size="icon" onClick={() => router.back()}>
    <ArrowLeft className="h-5 w-5" />
  </Button>

  {/* Centre : Titre note */}
  <h1 className="font-semibold truncate max-w-md">{note.title}</h1>

  {/* Droite : Actions */}
  <div className="flex items-center gap-2">
    {/* Toggle TEXT/HTML */}
    <div className="flex items-center bg-gray-800 rounded-lg p-1">
      <button
        className={viewMode === 'text' ? 'bg-gray-700' : ''}
        onClick={() => setViewMode('text')}
      >
        TEXT
      </button>
      <button
        className={viewMode === 'html' ? 'bg-gray-700' : ''}
        onClick={handleToggleHTML}
      >
        HTML
      </button>
    </div>

    {/* Refresh (si conversion en cours) */}
    {isConverting && (
      <Button variant="ghost" size="icon" disabled>
        <Loader2 className="h-4 w-4 animate-spin" />
      </Button>
    )}
  </div>
</div>
```

**Content :**
```tsx
<main className="max-w-4xl mx-auto p-6 pb-24">
  {viewMode === 'text' ? (
    <pre className="whitespace-pre-wrap font-mono text-sm">
      {note.text_content}
    </pre>
  ) : (
    <div
      className="prose prose-invert max-w-none"
      dangerouslySetInnerHTML={{__html: note.html_content}}
    />
  )}
</main>
```

**Bouton Chat (floating bottom-right) :**
```tsx
<Button
  size="icon"
  className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg"
  onClick={() => router.push(`/?context=note:${note.id}`)}
>
  <MessageSquare className="h-6 w-6" />
</Button>
```

**Comportement Toggle HTML :**
1. User clique sur "HTML"
2. Si `html_content` vide ou ancien → Lancer conversion
3. Afficher loader dans toggle + message "Conversion en cours..."
4. Requête async : `POST /notes/{id}/convert-html`
5. Polling ou WebSocket pour recevoir notification fin conversion
6. Une fois prêt → charger HTML et switcher vue
7. Toggle reste actif pendant conversion (non-bloquant)

---

### **Pages Secondaires**

#### 6. **`/settings` - Dashboard & Paramètres**
**Route :** `/settings`
**Accessible :** Authentifié uniquement

**Sections :**

**1. Metrics Dashboard**
```tsx
<section>
  <h2 className="text-xl font-bold mb-4">Statistiques</h2>
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
    <Card>
      <CardContent className="p-4 text-center">
        <p className="text-3xl font-bold text-plume-500">{metrics.total_notes}</p>
        <p className="text-sm text-gray-400 mt-1">Notes</p>
      </CardContent>
    </Card>

    <Card>
      <CardContent className="p-4 text-center">
        <p className="text-3xl font-bold text-mimir-500">{metrics.total_conversations}</p>
        <p className="text-sm text-gray-400 mt-1">Conversations</p>
      </CardContent>
    </Card>

    <Card>
      <CardContent className="p-4 text-center">
        <p className="text-3xl font-bold text-yellow-500">{metrics.total_tokens.toLocaleString()}</p>
        <p className="text-sm text-gray-400 mt-1">Tokens utilisés</p>
      </CardContent>
    </Card>

    <Card>
      <CardContent className="p-4 text-center">
        <p className="text-3xl font-bold text-green-500">{metrics.total_cost_eur.toFixed(2)} €</p>
        <p className="text-sm text-gray-400 mt-1">Coût total</p>
      </CardContent>
    </Card>
  </div>
</section>
```

**2. Préférences (déjà existant Phase 2.1)**
- Theme selector
- Keyboard shortcuts config

**3. Déconnexion**
```tsx
<section className="mt-8">
  <Button
    variant="destructive"
    onClick={handleLogout}
  >
    Se déconnecter
  </Button>
</section>
```

**Fonction logout :**
```ts
const handleLogout = () => {
  localStorage.removeItem('session')
  router.push('/login')
}
```

---

## 🧩 COMPOSANTS CLÉS

### **1. InputZone Component**

**Fichier :** `components/chat/InputZone.tsx`

**Spécifications :**
- Textarea auto-resize (min 44px, max 128px)
- Bouton Micro à droite sur la même ligne (clic = enregistrement direct, clic long/menu = upload fichier audio)
- Position fixed en bas quand prop `fixed={true}`
- Character counter si > 0 caractères
- Enter = send, Shift+Enter = nouvelle ligne

**Workflow Audio dans Chat :**
1. User clique micro → enregistrement direct OU upload fichier
2. Audio envoyé à backend dans `voice_data`
3. (Invisible) Transcription Whisper
4. (Invisible) Transcription devient `input_text` pour agents
5. User voit transcription + réponse agents

**Interface :**
```tsx
interface InputZoneProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  onVoiceRecord: () => void
  isRecording: boolean
  disabled?: boolean
  fixed?: boolean
  placeholder?: string
}

export function InputZone({
  value,
  onChange,
  onSend,
  onVoiceRecord,
  isRecording,
  disabled = false,
  fixed = false,
  placeholder = "Écrivez votre message..."
}: InputZoneProps) {
  return (
    <div className={cn(
      "bg-gray-900/95 backdrop-blur border-t border-gray-800 p-4",
      fixed && "fixed bottom-0 left-0 right-0 z-20"
    )}>
      <div className="max-w-4xl mx-auto flex items-end gap-2">
        {/* Textarea */}
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="flex-1 min-h-[44px] max-h-32 resize-none"
          disabled={disabled}
        />

        {/* Bouton Micro */}
        <Button
          size="icon"
          variant={isRecording ? "destructive" : "outline"}
          onClick={onVoiceRecord}
          disabled={disabled}
          className="flex-shrink-0"
        >
          {isRecording ? <MicOff /> : <Mic />}
        </Button>

        {/* Bouton Send */}
        <Button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="flex-shrink-0"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>

      {/* Character counter */}
      {value.length > 0 && (
        <p className="text-xs text-gray-500 text-right mt-2 max-w-4xl mx-auto">
          {value.length} caractères
        </p>
      )}
    </div>
  )
}
```

---

### **2. ChatMessage Component avec Objets Clickables**

**Fichier :** `components/chat/ChatMessage.tsx`

**Spécifications :**
- Afficher message user ou agent
- Parser `metadata.clickable_objects` si présent
- Render objets comme boutons/chips clickables sous le message

**Interface :**
```tsx
interface ClickableObject {
  type: 'viz_link' | 'web_link'
  note_id?: string
  title?: string
  url?: string
}

interface ChatMessageProps {
  message: {
    id: string
    role: 'user' | 'plume' | 'mimir'
    content: string
    timestamp: Date
    metadata?: {
      clickable_objects?: ClickableObject[]
      processing_time?: number
      tokens_used?: number
      cost_eur?: number
    }
  }
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const agentInfo = !isUser ? getAgentInfo(message.role) : null

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <Avatar />

      {/* Message bubble */}
      <div className="flex-1 max-w-[80%]">
        <Card>
          <CardContent className="p-3">
            {/* Message content */}
            <p className="text-sm whitespace-pre-wrap">
              {message.content}
            </p>

            {/* Clickable objects */}
            {message.metadata?.clickable_objects && (
              <div className="flex flex-wrap gap-2 mt-3">
                {message.metadata.clickable_objects.map((obj, idx) => (
                  <ClickableObjectButton key={idx} object={obj} />
                ))}
              </div>
            )}

            {/* Metadata (optionnel, pour debug) */}
            {message.metadata && (
              <div className="flex gap-3 text-xs text-gray-500 mt-2">
                {message.metadata.processing_time && (
                  <span>{message.metadata.processing_time}ms</span>
                )}
                {message.metadata.tokens_used && (
                  <span>{message.metadata.tokens_used} tokens</span>
                )}
                {message.metadata.cost_eur && (
                  <span>{message.metadata.cost_eur.toFixed(4)}€</span>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Timestamp */}
        <p className="text-xs text-gray-500 mt-1">
          {formatTime(message.timestamp)}
        </p>
      </div>
    </div>
  )
}
```

**ClickableObjectButton :**
```tsx
function ClickableObjectButton({ object }: { object: ClickableObject }) {
  const router = useRouter()

  const handleClick = () => {
    if (object.type === 'viz_link' && object.note_id) {
      router.push(`/viz/${object.note_id}`)
    } else if (object.type === 'web_link' && object.url) {
      window.open(object.url, '_blank')
    }
  }

  return (
    <Button
      size="sm"
      variant="outline"
      onClick={handleClick}
      className="gap-2"
    >
      {object.type === 'viz_link' ? (
        <>
          <FileText className="h-3 w-3" />
          {object.title || 'Voir la note'}
        </>
      ) : (
        <>
          <ExternalLink className="h-3 w-3" />
          {object.title || 'Lien externe'}
        </>
      )}
    </Button>
  )
}
```

---

### **3. Session Management Hook**

**Fichier :** `lib/hooks/useSession.ts`

```tsx
export function useSession() {
  const router = useRouter()
  const [session, setSession] = useState<{
    user_id: string
    logged_in: boolean
    expires: number
  } | null>(null)

  useEffect(() => {
    const stored = localStorage.getItem('session')
    if (stored) {
      const parsed = JSON.parse(stored)
      if (parsed.expires > Date.now()) {
        setSession(parsed)
      } else {
        // Session expirée
        localStorage.removeItem('session')
        router.push('/login')
      }
    }
  }, [])

  const login = (username: string, password: string): boolean => {
    if (username === 'King' && password === 'Faire la diff') {
      const newSession = {
        user_id: 'king_001',
        logged_in: true,
        expires: Date.now() + 30 * 24 * 3600 * 1000 // 30 jours
      }
      localStorage.setItem('session', JSON.stringify(newSession))
      setSession(newSession)
      return true
    }
    return false
  }

  const logout = () => {
    localStorage.removeItem('session')
    setSession(null)
    router.push('/login')
  }

  return { session, login, logout, isAuthenticated: !!session }
}
```

**Protection de routes :**
```tsx
// components/auth/ProtectedRoute.tsx
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated])

  if (!isAuthenticated) {
    return <Loader2 className="animate-spin" />
  }

  return <>{children}</>
}
```

---

### **4. API Client (Mockée temporairement)**

**Fichier :** `lib/api/mock.ts`

**Pour Phase 1, créer des mocks pour tester l'UI sans backend :**

```tsx
// Mock conversations
export async function getConversations(): Promise<Conversation[]> {
  return [
    {
      id: '1',
      title: 'Recherche sur le RAG',
      note_titles: ['RAG Architecture', 'Vector Embeddings', 'Semantic Search'],
      updated_at: new Date(),
      message_count: 12
    },
    // ... autres mocks
  ]
}

// Mock notes
export async function getRecentNotes(): Promise<Note[]> {
  return [
    {
      id: '1',
      title: 'RAG Architecture',
      text_content: 'Contenu de la note...',
      html_content: '<h1>RAG Architecture</h1>...',
      created_at: new Date(),
      updated_at: new Date()
    },
    // ... autres mocks
  ]
}

// Mock search
export async function searchNotes(query: string): Promise<Note[]> {
  // Filtrer notes mockées selon query
  return []
}

// Mock upload
export async function uploadText(text: string, context?: string): Promise<Note> {
  return {
    id: Date.now().toString(),
    title: 'Nouvelle note',
    text_content: text,
    html_content: '',
    created_at: new Date(),
    updated_at: new Date()
  }
}

export async function uploadAudio(file: File, context?: string): Promise<Note> {
  // Simuler upload + transcription
  await new Promise(resolve => setTimeout(resolve, 2000))
  return {
    id: Date.now().toString(),
    title: 'Transcription audio',
    text_content: 'Transcription simulée du fichier audio...',
    html_content: '',
    created_at: new Date(),
    updated_at: new Date()
  }
}

// Mock HTML conversion
export async function convertToHTML(noteId: string): Promise<string> {
  await new Promise(resolve => setTimeout(resolve, 1500))
  return '<h1>HTML converti</h1><p>Contenu de la note en HTML...</p>'
}

// Mock metrics
export async function getMetrics(): Promise<Metrics> {
  return {
    total_notes: 47,
    total_conversations: 23,
    total_tokens: 156432,
    total_cost_eur: 12.34
  }
}
```

**Note importante :** Ces mocks seront remplacés par les vrais appels API en Phase 2 (Integration).

---

## 📋 NAVIGATION RESTRUCTURÉE

**Fichier :** `components/layout/Navigation.tsx` (existant, à modifier)

**Liens à mettre à jour :**

**Mobile (bottom nav) :**
- Home (MessageSquare icon) → `/`
- Works (FolderOpen icon) → `/works`
- Archives (Archive icon) → `/archives`
- Settings (Settings icon) → `/settings`

**Desktop (top navbar) :**
- Logo "SCRIBE" → `/`
- Navigation links : Works | Archives | Settings
- User menu (dropdown) → Logout

---

## ✅ CHECKLIST DE TÂCHES

### **Phase Setup**
- [ ] Créer structure dossiers pages : `/login`, `/works`, `/archives`, `/viz`
- [ ] Créer fichier mocks : `lib/api/mock.ts`
- [ ] Créer hook session : `lib/hooks/useSession.ts`

### **Composants**
- [ ] Créer `InputZone.tsx` avec textarea + micro + send
- [ ] Modifier `ChatMessage.tsx` pour parser clickable_objects
- [ ] Créer `ClickableObjectButton.tsx`
- [ ] Créer `ProtectedRoute.tsx` pour auth guard
- [ ] Créer `EmptyState.tsx` pour états vides

### **Pages**
- [ ] Page `/login` avec formulaire simple
- [ ] Page `/` (Home) avec chat vierge + InputZone fixe
- [ ] Page `/works` avec liste conversations
- [ ] Page `/works/[id]` avec chat pré-chargé
- [ ] Page `/archives` avec 3 sections (recents, search, upload)
- [ ] Page `/archives/all` avec liste complète notes
- [ ] Page `/viz/[id]` avec toggle TEXT/HTML + loader
- [ ] Page `/settings` avec metrics dashboard

### **Navigation**
- [ ] Mettre à jour liens Navigation (mobile + desktop)
- [ ] Ajouter dropdown user menu avec logout
- [ ] Route guards sur toutes les pages protégées

### **Fonctionnalités**
- [ ] Login localStorage + redirection
- [ ] Logout clear localStorage
- [ ] Upload texte (mock)
- [ ] Upload audio (mock avec loader)
- [ ] Search notes (mock avec debounce)
- [ ] HTML conversion avec loader animé
- [ ] Format dates relatives (Aujourd'hui, Hier, etc.)

### **Tests UI**
- [ ] Navigation fluide entre pages
- [ ] InputZone fixed scroll correct
- [ ] Toggle HTML non-bloquant
- [ ] Objets clickables fonctionnels
- [ ] Responsive mobile/desktop
- [ ] Dark theme cohérent

### **Déploiement**
- [ ] Build production sans erreurs
- [ ] Tests lighthouse (Performance > 90)
- [ ] Vérifier toutes routes accessible
- [ ] Push vers Render

---

## 🎯 CRITÈRES DE SUCCÈS

**Interface :**
- ✅ Toutes les pages créées et navigables
- ✅ Design cohérent avec Phase 2.1 (dark theme, shadcn/ui)
- ✅ Responsive mobile-first

**Fonctionnalités :**
- ✅ Login/logout fonctionnel avec localStorage
- ✅ InputZone fixe avec bouton micro
- ✅ Objets clickables render correctement
- ✅ Upload texte + audio avec mocks
- ✅ Search notes avec debounce
- ✅ Toggle HTML avec loader

**Qualité Code :**
- ✅ TypeScript strict sans erreurs
- ✅ Components réutilisables
- ✅ Mocks bien structurés (faciles à remplacer Phase 2)

**Déploiement :**
- ✅ Build production réussi
- ✅ Déployé sur Render sans erreurs
- ✅ Application utilisable de bout en bout (avec mocks)

---

## 📝 NOTES IMPORTANTES

1. **Mocks temporaires :** Toutes les API calls sont mockées en Phase 1. Elles seront remplacées par de vrais appels en Phase 2 (Integration).

2. **Clickable Objects :** Le format exact sera défini par Koda (Backend). Pour l'instant, préparer l'UI pour recevoir `{type, note_id, title, url}`.

3. **Audio Upload :** L'upload audio montre un loader et simule 2s de traitement. Le vrai workflow (transcription Whisper) sera en Phase 2.

4. **HTML Conversion :** Le toggle lance une conversion async et affiche un loader. Le polling/WebSocket pour notification sera implémenté en Phase 2.

5. **Session Simple :** Pas de JWT/cookie complexe. localStorage suffit pour usage solo. Attention : pas ultra sécurisé mais acceptable pour MVP.

6. **AutoGen Discussion :** Les messages internes Plume ↔ Mimir seront visibles en Phase 2. Pour l'instant, juste préparer l'UI pour afficher plusieurs messages agents successifs.

---

**Document créé par :** Leo (Architecture)
**Pour agent :** KodaF (Frontend Specialist)
**Phase :** 2.2 Phase 1 (Parallèle)
**Date :** 30 septembre 2025
