#!/usr/bin/env python3
"""
Render MCP Monitor Service - Surveillance automatique des logs Render
Surveillance en temps réel pour scribe-frontend-qk6s.onrender.com
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import aiohttp
import structlog
from dataclasses import dataclass, asdict
from enum import Enum

# Import du logger configuré
from backend.utils.logger import get_logger, PerformanceLogger

logger = get_logger("render_mcp_monitor")
perf_logger = PerformanceLogger()

class LogLevel(Enum):
    """Niveaux de logs pour surveillance"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(Enum):
    """Types d'alertes pour monitoring"""
    ERROR_SPIKE = "error_spike"
    DEPLOYMENT_FAILED = "deployment_failed"
    SERVICE_DOWN = "service_down"
    HIGH_LATENCY = "high_latency"
    MEMORY_USAGE = "memory_usage"
    COST_THRESHOLD = "cost_threshold"

@dataclass
class RenderService:
    """Configuration d'un service Render à surveiller"""
    service_id: str
    service_name: str
    environment: str  # production, staging, etc.
    url: str
    alert_thresholds: Dict[str, Any]

@dataclass
class LogEntry:
    """Entrée de log standardisée"""
    timestamp: datetime
    level: LogLevel
    message: str
    service_id: str
    deployment_id: Optional[str] = None
    instance_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AlertEvent:
    """Événement d'alerte"""
    alert_type: AlertType
    service_id: str
    timestamp: datetime
    severity: str
    message: str
    details: Dict[str, Any]
    resolved: bool = False

class RenderMCPMonitor:
    """Surveillance automatique des services Render via MCP"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.mcp_endpoint = "https://mcp.render.com/mcp"
        self.session: Optional[aiohttp.ClientSession] = None
        self.monitoring_active = False
        self.services: Dict[str, RenderService] = {}
        self.alert_handlers: List[Callable[[AlertEvent], None]] = []

        # Configuration par défaut
        self.default_thresholds = {
            "error_rate_per_minute": 10,
            "response_time_p95_ms": 2000,
            "memory_usage_percent": 85,
            "deployment_timeout_minutes": 15
        }

    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.stop()

    async def start(self):
        """Démarrer le service de monitoring"""
        if self.session is None:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=30, connect=10)

            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "SCRIBE-Monitor/1.0"
                }
            )

        self.monitoring_active = True
        logger.info("Render MCP Monitor started", service="render_monitor")

    async def stop(self):
        """Arrêter le service de monitoring"""
        self.monitoring_active = False
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Render MCP Monitor stopped", service="render_monitor")

    def add_service(self, service: RenderService):
        """Ajouter un service à surveiller"""
        self.services[service.service_id] = service
        logger.info(
            "Service added to monitoring",
            service_id=service.service_id,
            service_name=service.service_name,
            environment=service.environment
        )

    def add_alert_handler(self, handler: Callable[[AlertEvent], None]):
        """Ajouter un gestionnaire d'alertes"""
        self.alert_handlers.append(handler)

    async def get_service_logs(
        self,
        service_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[LogLevel] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """Récupérer les logs d'un service"""
        if not self.session:
            raise RuntimeError("Monitor not started")

        # Préparer les paramètres de requête
        params = {
            "service_id": service_id,
            "limit": limit
        }

        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()
        if level:
            params["level"] = level.value

        try:
            start_ms = datetime.now().timestamp() * 1000

            # Simuler l'appel MCP (à remplacer par le vrai endpoint)
            async with self.session.get(
                f"{self.mcp_endpoint}/services/{service_id}/logs",
                params=params
            ) as response:
                duration_ms = datetime.now().timestamp() * 1000 - start_ms

                if response.status == 200:
                    data = await response.json()
                    logs = self._parse_logs(data.get("logs", []), service_id)

                    perf_logger.log_api_call(
                        service="render_mcp",
                        endpoint=f"logs/{service_id}",
                        duration_ms=duration_ms,
                        status_code=response.status,
                        logs_count=len(logs)
                    )

                    return logs
                else:
                    logger.error(
                        "Failed to fetch logs",
                        service_id=service_id,
                        status_code=response.status,
                        duration_ms=duration_ms
                    )
                    return []

        except Exception as e:
            logger.error(
                "Error fetching logs",
                service_id=service_id,
                error=str(e)
            )
            return []

    async def get_service_metrics(self, service_id: str) -> Dict[str, Any]:
        """Récupérer les métriques d'un service"""
        if not self.session:
            raise RuntimeError("Monitor not started")

        try:
            async with self.session.get(
                f"{self.mcp_endpoint}/services/{service_id}/metrics"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(
                        "Failed to fetch metrics",
                        service_id=service_id,
                        status_code=response.status
                    )
                    return {}
        except Exception as e:
            logger.error(
                "Error fetching metrics",
                service_id=service_id,
                error=str(e)
            )
            return {}

    async def check_deployment_status(self, service_id: str) -> Dict[str, Any]:
        """Vérifier le statut des déploiements"""
        if not self.session:
            raise RuntimeError("Monitor not started")

        try:
            async with self.session.get(
                f"{self.mcp_endpoint}/services/{service_id}/deployments"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(
                        "Failed to fetch deployments",
                        service_id=service_id,
                        status_code=response.status
                    )
                    return {}
        except Exception as e:
            logger.error(
                "Error fetching deployments",
                service_id=service_id,
                error=str(e)
            )
            return {}

    async def monitor_service(self, service_id: str):
        """Surveillance continue d'un service"""
        service = self.services.get(service_id)
        if not service:
            logger.error("Service not found for monitoring", service_id=service_id)
            return

        logger.info(
            "Starting service monitoring",
            service_id=service_id,
            service_name=service.service_name
        )

        while self.monitoring_active:
            try:
                # Récupérer les logs des 5 dernières minutes
                end_time = datetime.now()
                start_time = end_time - timedelta(minutes=5)

                logs = await self.get_service_logs(
                    service_id,
                    start_time=start_time,
                    end_time=end_time
                )

                # Analyser les logs pour détecter des anomalies
                await self._analyze_logs(service_id, logs)

                # Récupérer les métriques
                metrics = await self.get_service_metrics(service_id)
                await self._analyze_metrics(service_id, metrics)

                # Vérifier les déploiements
                deployments = await self.check_deployment_status(service_id)
                await self._analyze_deployments(service_id, deployments)

                # Attendre avant la prochaine vérification
                await asyncio.sleep(60)  # Vérification toutes les minutes

            except Exception as e:
                logger.error(
                    "Error in service monitoring loop",
                    service_id=service_id,
                    error=str(e)
                )
                await asyncio.sleep(30)  # Attendre plus longtemps en cas d'erreur

    async def start_monitoring_all(self):
        """Démarrer la surveillance de tous les services configurés"""
        tasks = []
        for service_id in self.services:
            task = asyncio.create_task(self.monitor_service(service_id))
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _parse_logs(self, raw_logs: List[Dict], service_id: str) -> List[LogEntry]:
        """Parser les logs bruts en objets LogEntry"""
        logs = []
        for raw_log in raw_logs:
            try:
                log_entry = LogEntry(
                    timestamp=datetime.fromisoformat(raw_log.get("timestamp", "")),
                    level=LogLevel(raw_log.get("level", "info")),
                    message=raw_log.get("message", ""),
                    service_id=service_id,
                    deployment_id=raw_log.get("deployment_id"),
                    instance_id=raw_log.get("instance_id"),
                    metadata=raw_log.get("metadata", {})
                )
                logs.append(log_entry)
            except Exception as e:
                logger.warning(
                    "Failed to parse log entry",
                    service_id=service_id,
                    error=str(e),
                    raw_log=raw_log
                )
        return logs

    async def _analyze_logs(self, service_id: str, logs: List[LogEntry]):
        """Analyser les logs pour détecter des anomalies"""
        service = self.services[service_id]
        error_threshold = service.alert_thresholds.get(
            "error_rate_per_minute",
            self.default_thresholds["error_rate_per_minute"]
        )

        # Compter les erreurs dans les 5 dernières minutes
        error_count = sum(1 for log in logs if log.level in [LogLevel.ERROR, LogLevel.CRITICAL])

        if error_count >= error_threshold:
            alert = AlertEvent(
                alert_type=AlertType.ERROR_SPIKE,
                service_id=service_id,
                timestamp=datetime.now(),
                severity="high",
                message=f"Error spike detected: {error_count} errors in 5 minutes",
                details={
                    "error_count": error_count,
                    "threshold": error_threshold,
                    "recent_errors": [
                        {"timestamp": log.timestamp.isoformat(), "message": log.message}
                        for log in logs
                        if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]
                    ][-5:]  # Dernières 5 erreurs
                }
            )
            await self._trigger_alert(alert)

    async def _analyze_metrics(self, service_id: str, metrics: Dict[str, Any]):
        """Analyser les métriques pour détecter des anomalies"""
        service = self.services[service_id]

        # Vérifier l'utilisation mémoire
        memory_usage = metrics.get("memory_usage_percent", 0)
        memory_threshold = service.alert_thresholds.get(
            "memory_usage_percent",
            self.default_thresholds["memory_usage_percent"]
        )

        if memory_usage >= memory_threshold:
            alert = AlertEvent(
                alert_type=AlertType.MEMORY_USAGE,
                service_id=service_id,
                timestamp=datetime.now(),
                severity="medium",
                message=f"High memory usage: {memory_usage}%",
                details={
                    "memory_usage_percent": memory_usage,
                    "threshold": memory_threshold,
                    "metrics": metrics
                }
            )
            await self._trigger_alert(alert)

        # Vérifier la latence
        response_time_p95 = metrics.get("response_time_p95_ms", 0)
        latency_threshold = service.alert_thresholds.get(
            "response_time_p95_ms",
            self.default_thresholds["response_time_p95_ms"]
        )

        if response_time_p95 >= latency_threshold:
            alert = AlertEvent(
                alert_type=AlertType.HIGH_LATENCY,
                service_id=service_id,
                timestamp=datetime.now(),
                severity="medium",
                message=f"High latency detected: {response_time_p95}ms P95",
                details={
                    "response_time_p95_ms": response_time_p95,
                    "threshold": latency_threshold,
                    "metrics": metrics
                }
            )
            await self._trigger_alert(alert)

    async def _analyze_deployments(self, service_id: str, deployments: Dict[str, Any]):
        """Analyser les déploiements pour détecter des échecs"""
        recent_deployments = deployments.get("deployments", [])

        for deployment in recent_deployments[:3]:  # 3 derniers déploiements
            status = deployment.get("status", "")
            created_at = datetime.fromisoformat(deployment.get("created_at", ""))

            # Vérifier les déploiements échoués
            if status == "failed":
                alert = AlertEvent(
                    alert_type=AlertType.DEPLOYMENT_FAILED,
                    service_id=service_id,
                    timestamp=datetime.now(),
                    severity="high",
                    message=f"Deployment failed at {created_at}",
                    details={
                        "deployment_id": deployment.get("id"),
                        "status": status,
                        "created_at": created_at.isoformat(),
                        "deployment": deployment
                    }
                )
                await self._trigger_alert(alert)

    async def _trigger_alert(self, alert: AlertEvent):
        """Déclencher une alerte"""
        logger.warning(
            "Alert triggered",
            alert_type=alert.alert_type.value,
            service_id=alert.service_id,
            severity=alert.severity,
            message=alert.message,
            details=alert.details
        )

        # Exécuter tous les gestionnaires d'alertes
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(
                    "Error in alert handler",
                    error=str(e),
                    alert_type=alert.alert_type.value
                )

# Configuration pour SCRIBE Frontend
SCRIBE_FRONTEND_SERVICE = RenderService(
    service_id="scribe-frontend-qk6s",
    service_name="SCRIBE Frontend",
    environment="production",
    url="https://scribe-frontend-qk6s.onrender.com",
    alert_thresholds={
        "error_rate_per_minute": 5,  # Plus strict pour la production
        "response_time_p95_ms": 1500,
        "memory_usage_percent": 80,
        "deployment_timeout_minutes": 10
    }
)

async def default_alert_handler(alert: AlertEvent):
    """Gestionnaire d'alertes par défaut"""
    logger.critical(
        f"🚨 ALERT: {alert.message}",
        alert_type=alert.alert_type.value,
        service_id=alert.service_id,
        severity=alert.severity,
        details=alert.details
    )

    # Ici on peut ajouter :
    # - Envoi d'emails
    # - Notifications Slack/Discord
    # - Webhooks
    # - Création de tickets

async def setup_scribe_monitoring(api_key: str) -> RenderMCPMonitor:
    """Configuration complète du monitoring SCRIBE"""
    monitor = RenderMCPMonitor(api_key)

    # Ajouter le service SCRIBE Frontend
    monitor.add_service(SCRIBE_FRONTEND_SERVICE)

    # Ajouter le gestionnaire d'alertes
    monitor.add_alert_handler(default_alert_handler)

    await monitor.start()

    logger.info(
        "SCRIBE monitoring configured",
        service="scribe-frontend-qk6s",
        environment="production"
    )

    return monitor

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    async def main():
        api_key = os.getenv("RENDER_API_KEY")
        if not api_key:
            print("RENDER_API_KEY environment variable required")
            return

        async with RenderMCPMonitor(api_key) as monitor:
            monitor.add_service(SCRIBE_FRONTEND_SERVICE)
            monitor.add_alert_handler(default_alert_handler)

            print("🔧 SCRIBE Render Monitoring Started")
            print(f"📊 Monitoring: {SCRIBE_FRONTEND_SERVICE.service_name}")
            print(f"🌐 URL: {SCRIBE_FRONTEND_SERVICE.url}")

            await monitor.start_monitoring_all()

    asyncio.run(main())