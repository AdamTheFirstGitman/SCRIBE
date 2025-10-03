# 🎨 KodaF Frontend Audit - SCRIBE CHAP2

**Agent :** KodaF (Frontend Specialist)
**Mission :** Audit architecture frontend actuelle + Roadmap améliorations UX/UI
**Date :** 30 septembre 2025
**Context :** Chapitre 2 "Sur le Chantier" - Amélioration interface

---

## 📋 ARCHITECTURE FRONTEND ACTUELLE

### Structure Pages (Next.js 14 App Router)

```
frontend/app/
├── layout.tsx              # Layout racine (PWA + providers)
├── globals.css             # Styles globaux + Tailwind
│
├── chat/
│   └── page.tsx           # 💬 Interface Chat Agents
│
├── upload/
│   └── page.tsx           # 📤 Upload & Conversion Documents
│
└── health/
    └── route.ts           # 🏥 Health check endpoint
```

### Composants UI (shadcn/ui - Work CHAP1)

```
frontend/components/
├── ui/                     # shadcn/ui components professionnels
│   ├── button.tsx         # CVA variants (7 variants)
│   ├── card.tsx           # Layouts composition
│   ├── input.tsx          # Form controls
│   ├── textarea.tsx       # Auto-resize
│   ├── badge.tsx          # Status indicators
│   ├── label.tsx          # Form labels
│   └── switch.tsx         # Toggle switches
│
├── chat/
│   └── VoiceRecorder.tsx  # Recording vocal + transcription
│
├── pwa/
│   └── InstallPrompt.tsx  # Prompt installation PWA
│
├── OfflineStatus.tsx      # Indicator online/offline
└── providers.tsx          # Context providers globaux
```

---

## 📄 PAGES EXISTANTES - DÉTAILS

### 1. Root Layout (`layout.tsx`)

**Responsabilités :**
- Configuration PWA complète (manifest, service worker, meta tags)
- Providers globaux (Supabase, Toaster notifications)
- OfflineStatus indicator permanent
- PWAInstallPrompt component
- Skip to content link (accessibilité A11Y)
- Dark theme par défaut (`className="dark"`)
- Service Worker auto-registration (inline script)

**SEO & Meta :**
- Open Graph complet
- Twitter Cards
- Apple Web App meta tags
- Manifest.json reference
- Icons (favicon, apple-touch-icon)

**Fonts :**
- Inter (Google Fonts) avec preconnect

**Theme :**
- Dark mode uniquement (hardcoded)
- Palette : Plume Purple (#8B5CF6) + Mimir Blue (#3B82F6)
- Background : gray-950
- Text : gray-50

---

### 2. Chat Page (`/chat`)

**URL :** `/chat`

**Interface :**
```
┌─────────────────────────────────────┐
│  [Upload] [Settings]               │ ← Header buttons
├─────────────────────────────────────┤
│                                     │
│  🖋️ Plume: Message...              │ ← Message bubble agent
│                                     │
│          Message user 👤            │ ← Message bubble user
│                                     │
│  🧠 Mimir: Réponse...              │ ← Message bubble agent
│                                     │
├─────────────────────────────────────┤
│  [Plume] [Mimir]    ← Agent toggle │
│  ┌─────────────────────────────┐   │
│  │ Écris ton message...        │   │ ← Textarea input
│  └─────────────────────────────┘   │
│  [🎙️ Record] [📤 Send]            │ ← Action buttons
└─────────────────────────────────────┘
```

**Features :**
- Messages history (user + agents)
- Agent selection (Plume restitution / Mimir recherche)
- Voice recording (VoiceRecorder component)
- Text input (Textarea auto-resize)
- Loading states (spinner + "Agent réfléchit...")
- Auto-scroll to bottom
- Online/offline detection
- Links to Upload & Settings (in header)

**State Management :**
- `messages: ChatMessage[]` - Historique messages
- `selectedAgent: 'plume' | 'mimir'` - Agent actif
- `inputText: string` - Texte input
- `isRecording: boolean` - Recording status
- `isLoading: boolean` - Attente réponse agent
- `isOnline: boolean` - Network status

**Design :**
- Mobile-first responsive
- Message bubbles alignés (user right, agent left)
- Avatars agents (Feather icon Plume, Brain icon Mimir)
- Animations entrée messages (fade-in)
- Sticky input bottom

---

### 3. Upload Page (`/upload`)

**URL :** `/upload`

**Interface :**
```
┌─────────────────────────────────────┐
│  📤 Upload Documents                │ ← Header
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │  Drag & Drop Zone           │   │ ← Dropzone
│  │  ou clique pour sélectionner│   │
│  └─────────────────────────────┘   │
│                                     │
│  Fichiers uploadés:                 │
│  ┌─────────────────────────────┐   │
│  │ 📄 doc1.txt [Preview]       │   │ ← File list
│  │ 📄 doc2.md  [Preview]       │   │
│  └─────────────────────────────┘   │
│                                     │
│  Preview Document:                  │
│  ┌─────────────────────────────┐   │
│  │ [TEXT] [HTML] ← Toggle view │   │
│  │                             │   │
│  │ Contenu du document...      │   │ ← Preview pane
│  │                             │   │
│  └─────────────────────────────┘   │
│                                     │
│  Title: [_____________]             │ ← Custom fields
│  Tags:  [_____________]             │
│  [📤 Upload to Backend]            │ ← Action
└─────────────────────────────────────┘
```

**Features :**
- Drag & drop tactile (react-dropzone)
- Formats acceptés : txt, md, json
- File validation (size, type)
- Liste fichiers uploadés
- Preview document sélectionné
- **Toggle view TEXT ↔ HTML** (smart conversion)
- Conversion intelligent text-to-HTML :
  - Headers (# ## ###)
  - Links [text](url)
  - Lists (-, *, 1. 2.)
  - Code blocks
- Custom title & tags
- Metadata display (word count, char count, has_links, topics)
- Upload status (pending/processing/completed)
- Error handling

**State Management :**
- `uploadedFiles: File[]` - Files dropped/selected
- `processedDocs: ProcessedDocument[]` - Docs backend processed
- `selectedDoc: ProcessedDocument | null` - Doc preview
- `viewMode: 'text' | 'html'` - Toggle view
- `isUploading: boolean` - Upload status
- `customTitle/Tags: string` - Custom metadata

**Design :**
- Mobile-first responsive
- Drag active state (border highlight)
- File badges (status colors)
- Preview split view (metadata sidebar)
- Toggle smooth transition

---

### 4. Health Route (`/health`)

**URL :** `/health`
**Type :** API Route (Next.js)

**Response :**
```json
{
  "status": "ok",
  "timestamp": "2025-09-30T..."
}
```

---

## ✅ POINTS FORTS ACTUELS

### Design System (KodaF CHAP1)
- ✅ shadcn/ui components professionnels
- ✅ CVA variants system (consistency)
- ✅ Dark theme moderne
- ✅ Palette cohérente (Plume/Mimir colors)
- ✅ Animations natives CSS
- ✅ Mobile-first responsive
- ✅ TypeScript strict

### Fonctionnalités
- ✅ Chat agents fonctionnel
- ✅ Voice recording + transcription
- ✅ Upload documents avec preview
- ✅ Conversion text-to-HTML intelligente
- ✅ PWA complète (installable, offline)
- ✅ Service Worker active
- ✅ Network status detection

### Accessibilité
- ✅ Skip to content link
- ✅ Semantic HTML
- ✅ ARIA labels basiques
- ✅ Keyboard navigation partielle
- ✅ Focus states visibles

---

## 🚧 CE QUI MANQUE - DÉTAILS DÉVELOPPÉS

### 1. ❌ Navigation & Structure Globale

#### Page d'Accueil (`/`)
**Problème :** Pas de landing page, utilisateur ne sait pas où aller
**Besoin :**
- Landing page avec présentation Plume & Mimir
- Hero section avec value proposition
- CTA vers Chat ou Upload
- Onboarding visuel (screenshots/animations)
- OU redirect automatique vers `/chat` avec first-time onboarding

**Proposition :**
```
Option A: Landing Simple
- Hero: "Plume & Mimir - Gestion de connaissances IA"
- 2 cards: Plume (restitution) + Mimir (recherche)
- CTA: "Commencer" → /chat

Option B: Redirect + Onboarding
- `/` → redirect `/chat`
- First visit: Tour guidé (react-joyride)
- "Clique ici pour parler à Plume..."
```

---

#### Navigation Globale (Navbar/Sidebar)
**Problème :** Liens directs en dur dans pages, pas de navigation cohérente
**Besoin :**
- Navbar sticky top (desktop) OU Bottom navigation (mobile)
- Links: Home / Chat / Upload / Search / Settings
- Avatar utilisateur (futur multi-user)
- Notifications badge (optionnel)
- Theme toggle (dark/light)

**Proposition Mobile-First :**
```
Bottom Navigation (mobile):
┌─────────────────────────────────────┐
│         Content Page                │
│                                     │
├─────────────────────────────────────┤
│ [🏠] [💬] [📤] [🔍] [⚙️]          │ ← Bottom nav
└─────────────────────────────────────┘
    Home Chat Upload Search Settings

Navbar (desktop):
┌─────────────────────────────────────┐
│ 🖋️ Plume & Mimir  [💬][📤][🔍][⚙️]│ ← Top navbar
│                          [🌙] [@]   │   + theme + user
├─────────────────────────────────────┤
│         Content Page                │
│                                     │
└─────────────────────────────────────┘
```

**Composant à créer :**
- `components/layout/Navigation.tsx` (responsive)
- Active route highlight
- Smooth transitions
- Accessibility keyboard navigation

---

### 2. ❌ Page Settings (`/settings`)

**Problème :** Aucune configuration utilisateur possible
**Besoin :**
- Page settings complète
- Sections : Appearance / Agents / Notifications / Account

**Proposition Interface :**
```
Settings Page:
┌─────────────────────────────────────┐
│  ⚙️ Paramètres                      │
├─────────────────────────────────────┤
│  🎨 Apparence                       │
│  ├─ Theme: [Dark] [Light] [Auto]   │
│  ├─ Accent Color: [Plume] [Mimir]  │
│  └─ Font Size: [S] [M] [L]         │
│                                     │
│  🤖 Agents                          │
│  ├─ Agent par défaut: [Plume]      │
│  ├─ Auto-switch intelligent: [ON]  │
│  └─ Voice transcription: [ON]      │
│                                     │
│  🔔 Notifications                   │
│  ├─ Push notifications: [ON]       │
│  ├─ Sound effects: [OFF]           │
│  └─ Offline alerts: [ON]           │
│                                     │
│  👤 Compte (futur)                  │
│  ├─ Email: user@example.com        │
│  ├─ Préférences RAG                │
│  └─ Export données                 │
└─────────────────────────────────────┘
```

**Features Settings :**
- Theme toggle (dark/light/auto) avec persistence localStorage
- Agent par défaut (Plume/Mimir/Auto-detect)
- Voice settings (auto-transcribe, language)
- Notifications preferences
- Data export (conversations JSON)
- Clear cache button
- About section (version, credits)

**State Management :**
- Context Provider `SettingsContext`
- localStorage persistence
- Sync avec backend (futur)

---

### 3. ❌ Dark/Light Mode Toggle

**Problème :** Dark mode hardcoded, pas de choix utilisateur
**Besoin :**
- Theme provider avec toggle
- Persistence localStorage
- Smooth transition entre themes
- System preference detection (prefers-color-scheme)

**Implémentation :**
```typescript
// components/theme/ThemeProvider.tsx
type Theme = 'dark' | 'light' | 'system'

const ThemeContext = createContext<{
  theme: Theme
  setTheme: (theme: Theme) => void
}>()

// hooks/useTheme.ts
export function useTheme() {
  const { theme, setTheme } = useContext(ThemeContext)
  // Logic localStorage + system preference
}
```

**UI Toggle :**
- Icon: 🌙 (dark) / ☀️ (light) / 🖥️ (system)
- Position: Settings page + Navbar
- Animation transition smooth (0.3s ease)
- Variables CSS custom pour couleurs

**Palette Light Mode à définir :**
- Background: white / gray-50
- Text: gray-900
- Primary Plume: purple-600
- Primary Mimir: blue-600
- Cards: white avec border gray-200

---

### 4. ❌ Page Search Dédiée (`/search`)

**Problème :** Recherche uniquement via Mimir en chat, pas d'interface dédiée
**Besoin :**
- Page search standalone avec UX optimisée
- Filtres avancés (date, type, agent, tags)
- Résultats avec preview
- Historique recherches
- Suggestions auto-complete

**Proposition Interface :**
```
Search Page:
┌─────────────────────────────────────┐
│  🔍 Rechercher dans tes connaissances│
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │ 🔍 Recherche...       [🔍]  │   │ ← Search bar
│  └─────────────────────────────┘   │
│                                     │
│  Filtres: [Date▼] [Type▼] [Tags▼] │ ← Filters
│  Agent: [Tous] [Plume] [Mimir]     │
│                                     │
│  Résultats (45):                    │
│  ┌─────────────────────────────┐   │
│  │ 📄 Document title           │   │ ← Result card
│  │ Lorem ipsum excerpt...      │   │
│  │ Tags: [AI] [Notes]          │   │
│  │ 🖋️ Plume · 2 jours         │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 📄 Another doc...           │   │
│  └─────────────────────────────┘   │
│                                     │
│  [Load More]                        │
└─────────────────────────────────────┘
```

**Features Search :**
- Search bar avec debounce (300ms)
- Auto-complete suggestions (top queries)
- Filtres multiples :
  - Date range picker
  - Document type (note, doc, chat)
  - Tags multiselect
  - Agent source (Plume/Mimir)
  - Confidence score threshold
- Résultats :
  - Preview snippet (highlight keywords)
  - Metadata (date, agent, word count)
  - Click → full document view
- Pagination ou infinite scroll
- Historique recherches récentes
- Export résultats (CSV, JSON)

**State Management :**
- `searchQuery: string`
- `filters: SearchFilters`
- `results: SearchResult[]`
- `isSearching: boolean`
- `recentSearches: string[]` (localStorage)

**Backend Integration :**
- API: `POST /api/search/hybrid`
- RAG avancé (vector + fulltext + BM25)
- Mimir agent backend

---

### 5. ❌ Dashboard / Vue d'Ensemble (`/dashboard`)

**Problème :** Pas de vue d'ensemble activité utilisateur
**Besoin :**
- Dashboard avec statistiques et insights
- Vue agrégée conversations, documents, recherches
- Charts et visualisations

**Proposition Interface :**
```
Dashboard:
┌─────────────────────────────────────┐
│  📊 Tableau de bord                 │
├─────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌───────┐ │
│  │ 45      │ │ 12      │ │ 123   │ │ ← Stats cards
│  │ Messages│ │ Docs    │ │Searchs│ │
│  └─────────┘ └─────────┘ └───────┘ │
│                                     │
│  Activité récente:                  │
│  📈 [Chart conversations 7 jours]   │ ← Chart
│                                     │
│  Documents récents:                 │
│  ┌─────────────────────────────┐   │
│  │ 📄 Mon document.txt         │   │ ← Recent docs
│  │ 🖋️ Plume · Il y a 2h       │   │
│  └─────────────────────────────┘   │
│                                     │
│  Agents favoris:                    │
│  🖋️ Plume: 65% | 🧠 Mimir: 35%   │ ← Usage stats
│                                     │
│  [Voir toute l'activité →]         │
└─────────────────────────────────────┘
```

**Features Dashboard :**
- Stats cards (messages, docs, searches, tokens)
- Charts activité (recharts library)
  - Messages par jour (line chart)
  - Usage agents (pie chart)
  - Topics populaires (bar chart)
- Recent activity feed (derniers messages, uploads)
- Quick actions (New chat, Upload doc, Search)
- Shortcuts keyboard (Ctrl+K command palette)

**Agent Analytics (futur Agent Ava) :**
- Usage patterns détection
- Recommendations personnalisées
- Cost tracking (API tokens)

---

### 6. ❌ Micro-interactions & Animations

**Problème :** Animations basiques CSS, manque de fluidité
**Besoin :**
- Animations avancées avec framer-motion
- Transitions pages fluides
- Loading states sophistiqués
- Hover effects élégants

**Animations à Ajouter :**

**Page Transitions :**
```typescript
// app/template.tsx
import { motion } from 'framer-motion'

export default function Template({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  )
}
```

**Component Animations :**
- Message bubbles: slide-in + fade
- Cards: hover lift (scale + shadow)
- Buttons: press effect (scale 0.95)
- Dropzone: drag-over pulse
- Modal: backdrop blur + scale-in
- Toast notifications: slide-in from top

**Loading States :**
- Skeleton screens (composants)
- Spinner with agent avatar rotation
- Progress bars smooth (upload, processing)
- Shimmer effect (loading content)

**Gestures (mobile) :**
- Swipe to dismiss (messages, notifications)
- Pull to refresh (conversations list)
- Long press actions (message options)

---

### 7. ❌ Keyboard Shortcuts Système

**Problème :** Navigation souris/tactile uniquement
**Besoin :**
- Shortcuts clavier pour power users
- Command palette (Ctrl+K style)
- Accessibility keyboard navigation

**Shortcuts à Implémenter :**
```
Global:
- Ctrl+K       → Command palette
- Ctrl+/       → Toggle sidebar (futur)
- Ctrl+N       → New conversation
- Ctrl+U       → Upload document
- Ctrl+F       → Focus search
- Esc          → Close modal/dialog

Chat:
- Ctrl+1       → Switch to Plume
- Ctrl+2       → Switch to Mimir
- Ctrl+Enter   → Send message
- Alt+R        → Start/stop recording

Navigation:
- Ctrl+H       → Go Home
- Ctrl+Shift+C → Go Chat
- Ctrl+Shift+U → Go Upload
- Ctrl+Shift+S → Go Search
- Ctrl+,       → Open Settings
```

**Command Palette :**
```
┌─────────────────────────────────────┐
│  🔍 Rechercher action...            │ ← Input
├─────────────────────────────────────┤
│  💬 Nouvelle conversation    Ctrl+N │
│  📤 Upload document          Ctrl+U │
│  🔍 Rechercher              Ctrl+F  │
│  ⚙️ Paramètres              Ctrl+,  │
│  🤖 Parler à Plume          Ctrl+1  │
│  🧠 Parler à Mimir          Ctrl+2  │
│  🌙 Toggle theme                    │
└─────────────────────────────────────┘
```

**Library :**
- `cmdk` (Command palette Vercel style)
- `react-hotkeys-hook` (shortcuts)

---

### 8. ❌ Onboarding Interactif

**Problème :** Utilisateur nouveau perdu, pas d'explication
**Besoin :**
- Tour guidé première visite
- Tooltips contextuels
- Empty states informatifs

**Tour Guidé (react-joyride) :**
```
Step 1: "Bienvenue sur Plume & Mimir !"
Step 2: "Voici Plume, ton agent de restitution" (highlight agent toggle)
Step 3: "Tu peux parler ou écrire" (highlight input + mic)
Step 4: "Upload tes documents ici" (highlight upload button)
Step 5: "Configure tes préférences" (highlight settings)
```

**Empty States :**
```
Chat vide:
┌─────────────────────────────────────┐
│         🖋️ 🧠                       │
│                                     │
│  Commence une conversation          │
│  avec Plume ou Mimir                │
│                                     │
│  [Parler à Plume] [Parler à Mimir] │
└─────────────────────────────────────┘

Upload vide:
┌─────────────────────────────────────┐
│         📤                          │
│                                     │
│  Aucun document uploadé             │
│                                     │
│  Glisse-dépose ou clique pour       │
│  ajouter ton premier document       │
│                                     │
│  [Sélectionner fichier]             │
└─────────────────────────────────────┘
```

---

### 9. ❌ Responsive & Breakpoints

**Problème :** Mobile-first OK, mais optimisations desktop manquantes
**Besoin :**
- Layout adaptatif selon écran
- Sidebar desktop (collapsed mobile)
- Multi-column layouts (desktop)

**Breakpoints Tailwind :**
```css
sm:  640px  (mobile landscape, small tablets)
md:  768px  (tablets)
lg:  1024px (desktop)
xl:  1280px (large desktop)
2xl: 1536px (ultra-wide)
```

**Layouts Adaptatifs :**

**Chat Page Desktop :**
```
lg: breakpoint
┌─────────────────────────────────────┐
│ Sidebar     │   Chat Main           │
│ (collapsed) │                       │
│             │   Messages            │
│ [💬]        │   ...                 │
│ [📤]        │                       │
│ [🔍]        │   ──────────────      │
│ [⚙️]        │   Input + Actions     │
└─────────────────────────────────────┘

xl: breakpoint (sidebar expanded)
┌─────────────────────────────────────┐
│ Sidebar            │   Chat Main    │
│                    │                │
│ 🏠 Home            │   Messages     │
│ 💬 Chat            │   ...          │
│ 📤 Upload          │                │
│ 🔍 Search          │   ─────────    │
│ ⚙️ Settings        │   Input        │
└─────────────────────────────────────┘
```

**Upload Page Desktop :**
```
lg: breakpoint (split view)
┌─────────────────────────────────────┐
│ Upload Zone + List │   Preview      │
│                    │                │
│ [Drop zone]        │   Document     │
│                    │   content...   │
│ Files:             │                │
│ - doc1.txt         │   [TEXT][HTML] │
│ - doc2.md          │                │
└─────────────────────────────────────┘
```

---

### 10. ❌ Accessibility A11Y Complet

**Problème :** A11Y basique, pas conforme WCAG 2.1 AA
**Besoin :**
- ARIA labels complets
- Navigation clavier complète
- Screen reader support
- Color contrast audit

**Checklist WCAG 2.1 Level AA :**

**Perceivable :**
- [ ] Alt text images
- [ ] ARIA labels tous interactifs
- [ ] Color contrast 4.5:1 minimum (text)
- [ ] Color contrast 3:1 minimum (UI components)
- [ ] Captions vidéos (futur)

**Operable :**
- [ ] Keyboard navigation complète (Tab, Enter, Esc)
- [ ] Focus visible states (outline)
- [ ] No keyboard traps
- [ ] Skip links (✅ déjà présent)
- [ ] No time limits (ou controls)

**Understandable :**
- [ ] Labels explicites forms
- [ ] Error messages descriptifs
- [ ] Instructions claires
- [ ] Consistent navigation
- [ ] Predictable behavior

**Robust :**
- [ ] Valid HTML5
- [ ] ARIA roles corrects
- [ ] Compatible screen readers (NVDA, JAWS, VoiceOver)

**ARIA Patterns à Implémenter :**
```typescript
// Navigation
<nav role="navigation" aria-label="Navigation principale">
  <a href="/chat" aria-current="page">Chat</a>
</nav>

// Chat messages
<div role="log" aria-live="polite" aria-atomic="false">
  <div role="article" aria-label="Message de Plume">
    Content...
  </div>
</div>

// Form
<form role="search">
  <label htmlFor="search-input">Rechercher</label>
  <input
    id="search-input"
    type="search"
    aria-describedby="search-hint"
  />
  <span id="search-hint">
    Rechercher dans vos documents
  </span>
</form>

// Modal
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
>
  <h2 id="modal-title">Titre</h2>
  ...
</div>
```

---

## 📦 NOUVELLES DÉPENDANCES À AJOUTER

```json
{
  "dependencies": {
    "framer-motion": "^11.0.0",      // Animations avancées
    "cmdk": "^1.0.0",                 // Command palette
    "react-hotkeys-hook": "^4.5.0",   // Keyboard shortcuts
    "react-joyride": "^2.8.0",        // Tour guidé onboarding
    "recharts": "^2.12.0",            // Charts dashboard
    "date-fns": "^3.0.0",             // Date formatting
    "@radix-ui/react-dialog": "^1.0.5",     // Modal accessible
    "@radix-ui/react-dropdown-menu": "^2.0.6", // Dropdown menus
    "@radix-ui/react-select": "^2.0.0",     // Select accessible
    "@radix-ui/react-tabs": "^1.0.4",       // Tabs component
    "@radix-ui/react-tooltip": "^1.0.7"     // Tooltips
  }
}
```

---

## 🎯 PRIORITÉS CHAP2 - SUGGESTION

### Phase 2.1 : Quick Wins (Semaine 1-2)
**Priorité :** ⭐⭐⭐⭐⭐

1. **Navigation Globale**
   - Créer Bottom Navigation (mobile) + Navbar (desktop)
   - Links actifs entre pages
   - Component `Navigation.tsx`

2. **Dark/Light Mode Toggle**
   - ThemeProvider avec Context
   - Toggle UI (Settings + Navbar)
   - Persistence localStorage
   - Variables CSS light mode

3. **Page Settings Basique**
   - Route `/settings`
   - Section Appearance (theme toggle)
   - Section Agents (default agent)
   - About section

4. **Keyboard Shortcuts Essentiels**
   - Ctrl+K Command palette
   - Ctrl+N, Ctrl+U (navigation)
   - Shortcuts chat (Ctrl+1/2)

**Estimation :** 10 jours

---

### Phase 2.2 : UX Polish (Semaine 3-4)
**Priorité :** ⭐⭐⭐⭐

5. **Animations framer-motion**
   - Page transitions
   - Component animations (cards, buttons)
   - Loading states sophistiqués

6. **Page Landing/Dashboard**
   - Décider : Landing simple OU Dashboard
   - Stats cards + Recent activity
   - Quick actions

7. **Onboarding Interactif**
   - Tour guidé première visite (react-joyride)
   - Empty states informatifs
   - Tooltips contextuels

**Estimation :** 10 jours

---

### Phase 2.3 : Features Avancées (Semaine 5-6)
**Priorité :** ⭐⭐⭐

8. **Page Search Dédiée**
   - Route `/search`
   - Search bar + filters
   - Results avec preview
   - Historique recherches

9. **Accessibility A11Y Complet**
   - Audit WCAG 2.1 AA
   - ARIA labels complets
   - Screen reader tests
   - Color contrast fixes

10. **Responsive Desktop Optimizations**
    - Layouts adaptatifs (sidebar, split views)
    - Multi-column quand pertinent
    - Hover effects desktop

**Estimation :** 12 jours

---

## 📝 QUESTIONS À CLARIFIER

1. **Landing Page :** Landing simple OU redirect /chat avec onboarding ?
2. **Navigation :** Bottom nav mobile + Top navbar desktop OU sidebar toujours visible ?
3. **Dashboard :** Dashboard stats OU garder Chat comme page principale ?
4. **Multi-user :** Prévoir dès maintenant (avatar, account) OU phase future ?
5. **Palette Light Mode :** Valider couleurs Plume/Mimir en mode clair
6. **Charts Library :** recharts OU alternative (Victory, Nivo) ?
7. **Command Palette :** Style Vercel (cmdk) OU custom ?

---

## 🚀 LIVRABLE ATTENDU KODAF

**Format :**
- Plan détaillé phase par phase
- Mockups ou wireframes (optionnel mais apprécié)
- Liste composants à créer/modifier
- Dépendances à installer
- Estimation temps par feature
- Ordre d'implémentation recommandé

**Validation :**
- Review avec Leo (architecte principal)
- Alignment vision SCRIBE
- Faisabilité technique
- Priorités ajustées ensemble

---

**Document créé par :** Leo (Architecte Principal)
**Pour :** KodaF (Frontend Specialist)
**Date :** 30 septembre 2025
**Status :** 🚧 Audit CHAP2 - À discuter et planifier ensemble