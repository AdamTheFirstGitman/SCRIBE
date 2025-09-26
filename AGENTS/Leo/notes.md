# Notes Leo - Pense-Bête Architecte

## État Actuel
✅ **Sprint 1 MVP** - Leo operational avec capacités étendues
- Task decomposition (2-3 niveaux, max 20 tâches)
- Détection edges simples → délégation Koda
- Communication standardisée agents
- Architecture EMPYR discipline

## Agents Disponibles
- **Leo** : Architecte principal (moi)
- **Koda** : Codeur spécialisé Claude Code + patterns
- **Gito** : Git MCP, évolution roadmap notes.md

## Prochaines Étapes Sprint 2
**Selon roadmap.md - Sprint 2 Communication :**
- [ ] Prompts communs entre agents (standardisation)
- [ ] Executor simple (division prompts)
- [ ] Tests edge cases inter-agents

## Déclencheurs Actions
**Quand suggérer évolutions :**
- `Koda débordé` → Créer Koda spécialisés (Frontend, Backend)
- `Git complexe` → Suggérer roadmap Gito Phase 2+
- `Tests manquants` → Créer Tester Agent
- `Coordination difficile` → Activer Executor Agent

## Structure EMPYR Maintenue
- Folders agents : MAJUSCULE (Leo, Koda, Gito)
- Fichiers : snake_case + notes.md obligatoire
- XP.md capitalisation expérience
- JSON enrichi configuration

## Réflexions Architecture
- Golem fonctionne bien pour création agents
- Communication Dict[str, Any] standard efficace
- MCP pattern intéressant (Gito exemple)
- notes.md aide continuité développement

## Problèmes Identifiés
- Pas encore de venv setup automatique
- Communication inter-agents à standardiser
- Edge cases detection perfectible

## Visualisation Holographique - EN ATTENTE (26 sept 2025)

### Prototype Développé
- **Visualizer.py** : Outil complet dans TOOLS/, intégré Leo
- **Architecture temps réel** : Leo visualise ce qu'il conçoit (Mermaid)
- **Style futuriste** : Cyan/violet, translucide, coin bas-gauche
- **Commands** : "show architecture", mise à jour auto decomposition

### État Technique
✅ **Code fonctionnel** : visualizer.py + integration leo_agent.py
✅ **Styles CSS** : Effet hologramme avec blur + opacity
⚠️ **Affichage** : Problèmes overlay macOS (focus/bureau)

### Décision Report
**Focus priorité** : Agents autonomes Claude Code (Forge, PLUME/MIMIR)
**Report à** : Evolution full web app / application native
**Conservation** : Tout le code visualiseur prêt, bonnes idées UI future

**Note :** Excellent concept pour montrer pensée Leo en temps réel, reprendre lors phase UI avancée.