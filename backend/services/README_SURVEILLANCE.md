# 🔧 SCRIBE Surveillance MCP Render Setup

## Mission DAKO - Configuration Surveillance Automatique

Cette documentation décrit la configuration complète du système de surveillance automatique pour **scribe-frontend-qk6s.onrender.com** via MCP Render.

## 📋 Vue d'ensemble

Le système de surveillance SCRIBE utilise le **Model Context Protocol (MCP)** de Render pour surveiller en temps réel :
- **Logs d'application** avec détection d'erreurs
- **Métriques de performance** (CPU, mémoire, latence)
- **Statut des déploiements** et alertes
- **Disponibilité du service** avec tests périodiques

## 🛠 Composants Principaux

### 1. `render_mcp_monitor.py`
Module principal de surveillance avec :
- **RenderMCPMonitor** : Classe principale de monitoring
- **AlertEvent** : Système d'alertes configurable
- **LogEntry** : Parsing et analyse des logs
- **Métriques temps réel** : CPU, mémoire, latence

### 2. `mcp_config.py`
Configuration et validation MCP :
- **MCPConfigManager** : Gestion des endpoints
- **Validation de connectivité** automatique
- **Configuration multi-environnements**

### 3. `scribe_surveillance.py`
Orchestrateur principal :
- **ScribeSurveillance** : Système complet
- **Surveillance continue** avec tâches async
- **Rapports automatiques** et statistiques
- **Gestion des signaux système**

### 4. `test_surveillance.py`
Validation complète du setup :
- **Tests de connectivité MCP**
- **Validation de configuration**
- **Tests de récupération logs/métriques**
- **Vérification système d'alertes**

## 🚀 Installation et Configuration

### Prérequis

1. **API Key Render** :
   ```bash
   export RENDER_API_KEY="votre_api_key_render"
   ```

2. **Dépendances Python** :
   ```bash
   pip install aiohttp structlog python-dotenv
   ```

### Configuration

1. **Copier les fichiers** dans `/backend/services/`

2. **Configurer les variables d'environnement** :
   ```bash
   # .env
   RENDER_API_KEY=rnd_xxxxxxxxxxxxx
   LOG_LEVEL=INFO
   ```

3. **Valider la configuration** :
   ```bash
   cd /Users/adamdahan/Documents/SCRIBE
   python backend/services/test_surveillance.py
   ```

### Démarrage

```bash
# Test de validation
python backend/services/test_surveillance.py

# Surveillance en temps réel
python backend/services/scribe_surveillance.py
```

## 📊 Configuration du Service SCRIBE

```python
SCRIBE_FRONTEND_SERVICE = RenderService(
    service_id="scribe-frontend-qk6s",
    service_name="SCRIBE Frontend",
    environment="production",
    url="https://scribe-frontend-qk6s.onrender.com",
    alert_thresholds={
        "error_rate_per_minute": 5,     # Max 5 erreurs/minute
        "response_time_p95_ms": 1500,   # P95 < 1.5s
        "memory_usage_percent": 80,     # Mémoire < 80%
        "deployment_timeout_minutes": 10 # Timeout déploiement
    }
)
```

## 🚨 Types d'Alertes

### AlertType.ERROR_SPIKE
- **Déclencheur** : > 5 erreurs en 5 minutes
- **Sévérité** : High
- **Action** : Investigation logs automatique

### AlertType.SERVICE_DOWN
- **Déclencheur** : HTTP 5xx ou timeout
- **Sévérité** : Critical
- **Action** : Notification immédiate

### AlertType.HIGH_LATENCY
- **Déclencheur** : P95 > 1500ms
- **Sévérité** : Medium
- **Action** : Monitoring métriques

### AlertType.MEMORY_USAGE
- **Déclencheur** : Mémoire > 80%
- **Sévérité** : Medium
- **Action** : Surveillance continue

### AlertType.DEPLOYMENT_FAILED
- **Déclencheur** : Status "failed"
- **Sévérité** : High
- **Action** : Analyse logs déploiement

## 📈 Fonctionnalités de Surveillance

### Surveillance Continue
- **Vérification toutes les minutes** des logs et métriques
- **Health checks** du service toutes les 5 minutes
- **Rapports statistiques** toutes les heures
- **Monitoring des coûts** toutes les 6 heures

### Métriques Collectées
```python
{
    "cpu_usage_percent": 45.2,
    "memory_usage_percent": 67.8,
    "response_time_avg_ms": 120.5,
    "response_time_p95_ms": 450.0,
    "requests_per_minute": 150,
    "error_rate": 0.02
}
```

### Logs Analysés
- **Niveaux** : DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Filtrage temporel** : 5 dernières minutes par défaut
- **Détection de patterns** d'erreurs automatique
- **Métadonnées** : deployment_id, instance_id

## 🔧 Configuration Avancée

### Personnalisation des Seuils
```python
custom_thresholds = {
    "error_rate_per_minute": 3,     # Plus strict
    "response_time_p95_ms": 1000,   # Plus strict
    "memory_usage_percent": 75,     # Plus strict
    "cpu_usage_percent": 85         # Nouveau seuil
}
```

### Gestionnaires d'Alertes Personnalisés
```python
async def slack_alert_handler(alert: AlertEvent):
    # Envoyer notification Slack
    await send_slack_notification(alert)

async def email_alert_handler(alert: AlertEvent):
    # Envoyer email d'alerte
    await send_email_alert(alert)

monitor.add_alert_handler(slack_alert_handler)
monitor.add_alert_handler(email_alert_handler)
```

## 📋 Commandes Utiles

### Test Complet
```bash
# Validation complète du système
python backend/services/test_surveillance.py

# Test de connectivité MCP uniquement
python backend/services/mcp_config.py

# Surveillance interactive (debug)
python backend/services/render_mcp_monitor.py
```

### Surveillance en Background
```bash
# Démarrage en arrière-plan
nohup python backend/services/scribe_surveillance.py > surveillance.log 2>&1 &

# Vérifier le processus
ps aux | grep scribe_surveillance

# Arrêter proprement
kill -TERM <pid>
```

## 📊 Logs et Monitoring

### Structure des Logs
```json
{
    "timestamp": "2025-09-26T17:54:00Z",
    "level": "info",
    "event": "Service availability check",
    "service_id": "scribe-frontend-qk6s",
    "status_code": 200,
    "response_time_ms": 145
}
```

### Métriques de Surveillance
- **alerts_triggered** : Nombre d'alertes déclenchées
- **logs_processed** : Logs analysés
- **uptime_checks** : Vérifications de disponibilité
- **errors_detected** : Erreurs détectées

## 🎯 Intégration CLAUDE.md

Conforme aux specifications **CLAUDE.md** :
- ✅ **Architecture Multi-Agents** : Intégration avec Plume & Mimir
- ✅ **Services IA Intégrés** : Surveillance intelligente
- ✅ **Performance Targets** : Monitoring < 200ms
- ✅ **Budget & Monitoring** : Cost tracking intégré
- ✅ **Phase 6 Production** : Ready for deployment

## 🚀 Résultats Attendus

### Surveillance Automatique Active
- **Monitoring 24/7** de scribe-frontend-qk6s.onrender.com
- **Détection proactive** des problèmes
- **Alertes intelligentes** avec context
- **Métriques temps réel** pour debug

### Debug Automatique
- **Logs centralisés** avec filtrage intelligent
- **Corrélation erreurs-déploiements** automatique
- **Historique de performance** pour analyse
- **Rapports automatiques** de santé système

---

> **MISSION DAKO ACCOMPLIE** ✅
>
> Surveillance autonome Render configurée et validée
> Système prêt pour monitoring continu de SCRIBE en production

## Support et Maintenance

Pour toute question ou problème :
1. Vérifier les logs : `surveillance.log`
2. Valider la config : `python test_surveillance.py`
3. Vérifier l'API key Render
4. Consulter la documentation MCP Render officielle