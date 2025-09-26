# =� NOTES SCRIBE - CONDENS�ES

## <� PROJET STATUS

**SCRIBE** = Syst�me agents IA (Plume + Mimir) pour gestion connaissances
**Backend :**  LIVE `scribe-api.onrender.com`
**Frontend :** L no-deploy persistant `scribe-frontend-qk6s.onrender.com`

## � PROBL�MES R�CURRENTS

1. **Node.js version conflicts** (23.11.0 local vs 20.18.0 deploy)
2. **Next.js memory crashes** (14.0.3 OOM � 14.2.15 fixes)
3. **Import @ alias failures** � imports relatifs solution
4. **Git cache case sensitivity** � reset cache obligatoire
5. **Render config malformed** � yaml syntax critique

##  SOLUTIONS APPLIQU�ES

- **Node.js :** 20.18.0 fixe (.nvmrc + package.json)
- **Next.js :** 14.2.15 (memory fixes Vercel)
- **Imports :** Relatifs `../../components/ui/button`
- **Render.yaml :** rootDir: frontend + PORT=10000
- **Git cache :** `git rm -r --cached .` + recommit

## =' DEBUG TECHNIQUES

**Smart Search :** WebSearch + community patterns + GitHub issues
**One error at a time :** R�soudre s�quentiellement
**Local test first :** npm run build � deploy
**Document everything :** DEBUG.md exhaustif
**Think simple :** Out-of-the-box avant complex solutions

## =� DOCS ESSENTIELLES

- **CLAUDE.md :** Config projet optimis�e
- **DEBUG.md :** 15+ solutions d�taill�es
- **HANDOVER_PROMPT.md :** Guide nouvelle session
- **ARCHIVES/ :** Docs agents d�taill�es

## =� DEPLOY HOOK

```bash
curl -X POST "https://api.render.com/deploy/srv-d3b7s9odl3ps73964ieg?key=_pf1X8o6lPA"
```

## <� NEXT STEPS

1. **Diagnostic simple** : syntaxe, packages, limits Render
2. **Test local** : build success mandatory
3. **Deploy iterative** : commit � test � document
4. **Success pattern** : reproduce solutions qui marchent

---

*D�velopp� avec architecture multi-agents - Ready for handover*