#!/usr/bin/env python3
"""
SCRIBE Surveillance Automatique - Mission DAKO
Integration complète du monitoring Render MCP pour scribe-frontend-qk6s.onrender.com
"""

import asyncio
import os
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
from pathlib import Path

# Import des modules SCRIBE
from backend.services.render_mcp_monitor import (
    RenderMCPMonitor,
    SCRIBE_FRONTEND_SERVICE,
    setup_scribe_monitoring,
    AlertEvent,
    AlertType
)
from backend.services.mcp_config import create_scribe_mcp_config, test_mcp_connectivity
from backend.utils.logger import get_logger, CostLogger

logger = get_logger("scribe_surveillance")
cost_logger = CostLogger()

class ScribeSurveillance:
    """Système de surveillance complet pour SCRIBE"""

    def __init__(self):
        self.monitor: RenderMCPMonitor = None
        self.running = False
        self.start_time: datetime = None
        self.stats = {
            "alerts_triggered": 0,
            "logs_processed": 0,
            "uptime_checks": 0,
            "errors_detected": 0
        }

    async def start(self):
        """Démarrer la surveillance complète"""
        logger.info("🔧 Starting SCRIBE Surveillance System")

        # 1. Vérifier la configuration
        api_key = os.getenv("RENDER_API_KEY")
        if not api_key:
            logger.error("RENDER_API_KEY environment variable required")
            sys.exit(1)

        # 2. Tester la connectivité MCP
        logger.info("Testing MCP connectivity...")
        connectivity_ok = await test_mcp_connectivity()
        if not connectivity_ok:
            logger.warning("MCP connectivity issues detected, proceeding anyway...")

        # 3. Configurer le monitoring
        self.monitor = await setup_scribe_monitoring(api_key)

        # 4. Ajouter des gestionnaires d'alertes personnalisés
        self.monitor.add_alert_handler(self._handle_critical_alert)
        self.monitor.add_alert_handler(self._log_alert_stats)

        # 5. Configurer les signaux système
        self._setup_signal_handlers()

        self.running = True
        self.start_time = datetime.now()

        logger.info(
            "🎯 SCRIBE Surveillance System Started",
            service="scribe-frontend-qk6s",
            start_time=self.start_time.isoformat()
        )

    async def run_surveillance(self):
        """Exécuter la surveillance complète"""
        if not self.monitor:
            raise RuntimeError("Surveillance not started")

        logger.info("🚀 Starting comprehensive surveillance...")

        # Créer les tâches de surveillance
        tasks = [
            # Surveillance principale des services
            asyncio.create_task(self.monitor.start_monitoring_all()),

            # Vérifications supplémentaires
            asyncio.create_task(self._periodic_health_check()),
            asyncio.create_task(self._periodic_stats_report()),
            asyncio.create_task(self._cost_monitoring())
        ]

        try:
            # Attendre que toutes les tâches se terminent
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error("Error in surveillance tasks", error=str(e))
        finally:
            await self.stop()

    async def stop(self):
        """Arrêter la surveillance"""
        self.running = False

        if self.monitor:
            await self.monitor.stop()

        uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)

        logger.info(
            "🛑 SCRIBE Surveillance Stopped",
            uptime_seconds=uptime.total_seconds(),
            stats=self.stats
        )

    async def _periodic_health_check(self):
        """Vérifications de santé périodiques"""
        while self.running:
            try:
                self.stats["uptime_checks"] += 1

                # Vérifier la disponibilité du service
                await self._check_service_availability()

                # Vérifier les métriques de performance
                await self._check_performance_metrics()

                # Attendre 5 minutes avant la prochaine vérification
                await asyncio.sleep(300)

            except Exception as e:
                logger.error("Error in health check", error=str(e))
                await asyncio.sleep(60)

    async def _check_service_availability(self):
        """Vérifier la disponibilité du service SCRIBE"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    SCRIBE_FRONTEND_SERVICE.url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status >= 500:
                        # Service indisponible
                        alert = AlertEvent(
                            alert_type=AlertType.SERVICE_DOWN,
                            service_id=SCRIBE_FRONTEND_SERVICE.service_id,
                            timestamp=datetime.now(),
                            severity="critical",
                            message=f"Service unavailable: HTTP {response.status}",
                            details={
                                "status_code": response.status,
                                "url": SCRIBE_FRONTEND_SERVICE.url,
                                "check_type": "availability"
                            }
                        )
                        await self.monitor._trigger_alert(alert)
                        self.stats["errors_detected"] += 1

                    logger.debug(
                        "Service availability check",
                        service_id=SCRIBE_FRONTEND_SERVICE.service_id,
                        status_code=response.status,
                        response_time_ms=(datetime.now().timestamp() * 1000) - (datetime.now().timestamp() * 1000)
                    )

        except Exception as e:
            logger.error(
                "Service availability check failed",
                service_id=SCRIBE_FRONTEND_SERVICE.service_id,
                error=str(e)
            )

    async def _check_performance_metrics(self):
        """Vérifier les métriques de performance"""
        try:
            metrics = await self.monitor.get_service_metrics(SCRIBE_FRONTEND_SERVICE.service_id)

            if metrics:
                # Analyser les métriques
                cpu_usage = metrics.get("cpu_usage_percent", 0)
                memory_usage = metrics.get("memory_usage_percent", 0)
                response_time = metrics.get("response_time_avg_ms", 0)

                logger.debug(
                    "Performance metrics",
                    service_id=SCRIBE_FRONTEND_SERVICE.service_id,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    response_time=response_time
                )

        except Exception as e:
            logger.error("Performance metrics check failed", error=str(e))

    async def _periodic_stats_report(self):
        """Rapport de statistiques périodique"""
        while self.running:
            try:
                # Attendre 1 heure
                await asyncio.sleep(3600)

                uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)

                logger.info(
                    "📊 Surveillance Statistics Report",
                    uptime_hours=uptime.total_seconds() / 3600,
                    stats=self.stats,
                    service=SCRIBE_FRONTEND_SERVICE.service_name
                )

            except Exception as e:
                logger.error("Error in stats report", error=str(e))

    async def _cost_monitoring(self):
        """Surveillance des coûts"""
        while self.running:
            try:
                # Attendre 6 heures
                await asyncio.sleep(21600)

                # Estimer les coûts de surveillance
                estimated_cost = self._calculate_surveillance_cost()

                cost_logger.log_token_usage(
                    service="render_mcp_surveillance",
                    model="render_api_calls",
                    tokens=self.stats.get("uptime_checks", 0),
                    cost=estimated_cost
                )

                if estimated_cost > 5.0:  # Budget alert à 5€
                    cost_logger.log_budget_alert(
                        alert_type="surveillance_cost",
                        current_cost=estimated_cost,
                        budget_limit=10.0
                    )

            except Exception as e:
                logger.error("Error in cost monitoring", error=str(e))

    def _calculate_surveillance_cost(self) -> float:
        """Calculer le coût estimé de la surveillance"""
        # Estimation basée sur le nombre d'appels API
        api_calls = self.stats.get("uptime_checks", 0)
        estimated_cost = api_calls * 0.001  # 0.1 centime par appel estimé
        return estimated_cost

    async def _handle_critical_alert(self, alert: AlertEvent):
        """Gestionnaire d'alertes critiques"""
        if alert.severity == "critical":
            logger.critical(
                f"🚨 CRITICAL ALERT: {alert.message}",
                alert_type=alert.alert_type.value,
                service_id=alert.service_id,
                details=alert.details
            )

            # Ici on peut ajouter :
            # - Notifications urgentes
            # - Auto-remediation
            # - Escalade

        self.stats["alerts_triggered"] += 1

    async def _log_alert_stats(self, alert: AlertEvent):
        """Logger les statistiques d'alertes"""
        self.stats["alerts_triggered"] += 1

        logger.info(
            "Alert statistics updated",
            alert_type=alert.alert_type.value,
            total_alerts=self.stats["alerts_triggered"],
            service_id=alert.service_id
        )

    def _setup_signal_handlers(self):
        """Configurer les gestionnaires de signaux système"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def run_scribe_surveillance():
    """Point d'entrée principal pour la surveillance SCRIBE"""
    surveillance = ScribeSurveillance()

    try:
        await surveillance.start()
        await surveillance.run_surveillance()
    except KeyboardInterrupt:
        logger.info("Surveillance interrupted by user")
    except Exception as e:
        logger.error("Fatal error in surveillance", error=str(e))
        raise
    finally:
        await surveillance.stop()

def main():
    """Point d'entrée du script"""
    print("🔧 MISSION DAKO - SCRIBE Surveillance Setup")
    print("=" * 60)
    print(f"🎯 Target: {SCRIBE_FRONTEND_SERVICE.service_name}")
    print(f"🌐 URL: {SCRIBE_FRONTEND_SERVICE.url}")
    print(f"🔍 Service ID: {SCRIBE_FRONTEND_SERVICE.service_id}")
    print("=" * 60)

    # Vérifier les prérequis
    if not os.getenv("RENDER_API_KEY"):
        print("❌ RENDER_API_KEY environment variable required")
        print("💡 Get your API key from: https://dashboard.render.com/account")
        sys.exit(1)

    print("🚀 Starting surveillance...")

    try:
        asyncio.run(run_scribe_surveillance())
    except KeyboardInterrupt:
        print("\n🛑 Surveillance stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()