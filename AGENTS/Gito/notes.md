# Notes Gito - Pense-Bête et Journal

## État Actuel
✅ **Phase 1 MVP** - Interface MCP Git basique opérationnelle
- Status, commit, branch, merge via MCP
- Communication Leo standardisée Dict[str, Any]
- Gestion erreurs basique

## Roadmap Évolution (voir notes.md racine)

### Phase 2 - Intelligence Git
- **Smart Commit Messages** : IA génère messages selon git diff
- **Conflict Resolution AI** : Assistant résolution conflits
- **Branch Strategy** : GitFlow/GitHub Flow conventions
- **Hooks Integration** : Pre-commit, pre-push automatisés

### Phase 3+ - Orchestration & Analytics
- Multi-repo, PR automation, CI/CD, metrics

## Déclencheurs Suggestions
**Patterns détection pour proposer évolutions :**
- `>5 commits/jour` → Smart Messages
- `conflicts detected` → AI Resolution
- `multiple branches active` → Branch Strategy
- `team > 2 devs` → Team Coordination

## Journal Développement
*[À remplir au fur et à mesure des améliorations]*

## Problèmes Connus
- MCP Git simulation (à remplacer par vrai MCP)
- Branch detection parfois `None`
- Error handling basique
- **GitHub CLI Auth** : One-time code manuel (D102-9F33, B3A6-1396)
  - Pourrait s'automatiser : recopie auto sur https://github.com/login/device
  - À surveiller si répétitif ou évolution IA prochaines

## Idées Futures
- **Automation GitHub Auth** : Selenium/puppeteer pour one-time codes
- Git hooks Python intégrés
- Analyse commits sémantique
- Backup automatique branches importantes
- Metrics dashboard Leo
- CLI auth flow detection et assistance contextuelle